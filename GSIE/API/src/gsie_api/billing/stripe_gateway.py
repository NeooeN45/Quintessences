"""Passerelle Stripe Billing et traitement idempotent des webhooks."""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast
from uuid import UUID, uuid4

import stripe
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from gsie_api.core.config import get_settings
from gsie_api.infrastructure.models.billing import (
    BillingEventModel,
    EntitlementModel,
    PlanFeatureModel,
    PlanModel,
    SubscriptionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class StripeNotConfiguredError(RuntimeError):
    """Stripe n'est pas activé ou un paramètre obligatoire manque."""


class StripeWebhookError(ValueError):
    """Signature ou contenu du webhook Stripe invalide."""


class StripeBillingError(RuntimeError):
    """Erreur métier d'opération Stripe impossible à appliquer."""


class StripeBillingGateway:
    """Crée des Checkout Sessions sans jamais activer localement un abonnement."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def _configure(self) -> None:
        secret = self._settings.stripe_secret_key.get_secret_value().strip()
        if not self._settings.stripe_enabled or not secret:
            raise StripeNotConfiguredError("Stripe n'est pas configuré")
        stripe.api_key = secret

    def _price_id(self, plan_code: str) -> str:
        prices = {
            "geosylva_pro": self._settings.stripe_price_geosylva_pro_monthly,
            "quintessences_pro": self._settings.stripe_price_quintessences_pro_monthly,
        }
        price_id = prices.get(plan_code, "")
        if not price_id:
            raise StripeNotConfiguredError(f"Price Stripe absent pour {plan_code}")
        return price_id

    async def create_portal_session(self, customer_id: str) -> str:
        """Crée une session du portail client Stripe."""
        self._configure()

        def create() -> str:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=self._settings.stripe_portal_return_url,
            )
            return str(session.url)

        return await asyncio.to_thread(create)

    async def upgrade_subscription(
        self,
        subscription_id: str,
        target_plan_code: str,
    ) -> None:
        """Remplace le prix avec proratisation Stripe, sans doubler l'abonnement."""
        self._configure()
        price_id = self._price_id(target_plan_code)

        def upgrade() -> None:
            subscription = stripe.Subscription.retrieve(subscription_id)
            items = subscription.get("items", {}).get("data", [])
            if len(items) != 1:
                raise StripeBillingError("Abonnement Stripe ambigu")
            stripe.Subscription.modify(
                subscription_id,
                items=[{"id": items[0]["id"], "price": price_id}],
                proration_behavior="create_prorations",
                metadata={"plan_code": target_plan_code},
            )

        await asyncio.to_thread(upgrade)

    async def create_checkout_session(
        self,
        *,
        plan_code: str,
        owner_type: str,
        owner_id: UUID,
    ) -> str:
        """Retourne une URL Checkout ; le webhook fera foi pour l'activation."""
        self._configure()
        price_id = self._price_id(plan_code)
        metadata = {"owner_type": owner_type, "owner_id": str(owner_id), "plan_code": plan_code}

        def create() -> str:
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=self._settings.stripe_checkout_success_url,
                cancel_url=self._settings.stripe_checkout_cancel_url,
                client_reference_id=str(owner_id),
                metadata=metadata,
                subscription_data={"metadata": metadata},
            )
            return str(session.url)

        return await asyncio.to_thread(create)


class StripeWebhookProcessor:
    """Vérifie, déduplique et applique les événements Stripe utiles."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._settings = get_settings()

    def parse_event(self, payload: bytes, signature: str | None) -> stripe.Event:
        secret = self._settings.stripe_webhook_secret.get_secret_value().strip()
        if not self._settings.stripe_enabled or not secret or not signature:
            raise StripeWebhookError("Webhook Stripe non configuré")
        try:
            return cast(
                stripe.Event,
                stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
                    payload, signature, secret
                ),
            )
        except (ValueError, stripe.SignatureVerificationError) as exc:
            raise StripeWebhookError("Signature Stripe invalide") from exc

    async def process(self, event: stripe.Event) -> bool:
        """Retourne False si l'événement avait déjà été traité."""
        external_id = str(event.id)
        existing = await self._session.scalar(
            select(BillingEventModel.id).where(
                BillingEventModel.provider == "stripe",
                BillingEventModel.external_event_id == external_id,
            )
        )
        if existing is not None:
            return False

        payload = event.to_dict_recursive()
        event_model = BillingEventModel(
            id=uuid4(),
            provider="stripe",
            external_event_id=external_id,
            payload_hash=hashlib.sha256(
                json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest(),
            event_type=str(event.type),
            status="received",
        )
        self._session.add(event_model)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            return False

        if event.type == "checkout.session.completed":
            await self._handle_checkout_completed(payload)
        elif event.type in {
            "customer.subscription.updated",
            "customer.subscription.deleted",
        }:
            await self._handle_subscription_event(payload)
        elif event.type == "invoice.payment_failed":
            await self._mark_subscription_status(payload, "past_due")

        event_model.status = "processed"
        event_model.processed_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def _handle_checkout_completed(self, payload: dict[str, object]) -> None:
        subscription_id = str(payload.get("subscription", ""))
        if subscription_id:
            await self._upsert_subscription(subscription_id, payload)

    async def _handle_subscription_event(self, payload: dict[str, object]) -> None:
        subscription_id = str(payload.get("id", ""))
        if subscription_id:
            await self._upsert_subscription(subscription_id, payload)

    async def _mark_subscription_status(self, payload: dict[str, object], status: str) -> None:
        data = payload.get("subscription")
        if isinstance(data, str):
            await self._session.execute(
                update(SubscriptionModel)
                .where(SubscriptionModel.external_subscription_id == data)
                .values(status=status, updated_at=datetime.now(UTC))
            )

    async def _upsert_subscription(self, subscription_id: str, payload: dict[str, object]) -> None:
        metadata = payload.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        owner_type = str(metadata.get("owner_type", ""))
        owner_id_raw = str(metadata.get("owner_id", ""))
        plan_code = str(metadata.get("plan_code", ""))
        if owner_type not in {"account", "organisation"} or not plan_code:
            raise StripeWebhookError("Métadonnées Stripe d'abonnement incomplètes")
        try:
            owner_id = UUID(owner_id_raw)
        except ValueError as exc:
            raise StripeWebhookError("Propriétaire Stripe invalide") from exc

        plan = await self._session.scalar(select(PlanModel).where(PlanModel.code == plan_code))
        if plan is None:
            raise StripeWebhookError("Plan GSIE inconnu")
        existing = await self._session.scalar(
            select(SubscriptionModel).where(
                SubscriptionModel.external_subscription_id == subscription_id
            )
        )
        status = str(payload.get("status", "active"))
        valid_statuses = {"trialing", "active", "past_due", "canceled", "unpaid", "ended"}
        status = status if status in valid_statuses else "active"
        values = {
            "owner_type": owner_type,
            "account_id": owner_id if owner_type == "account" else None,
            "organisation_id": owner_id if owner_type == "organisation" else None,
            "plan_id": plan.id,
            "provider": "stripe",
            "external_subscription_id": subscription_id,
            "provider_customer_id": str(payload.get("customer"))
            if payload.get("customer")
            else None,
            "status": status,
            "cancel_at_period_end": bool(payload.get("cancel_at_period_end", False)),
            "updated_at": datetime.now(UTC),
        }
        if existing is None:
            subscription = SubscriptionModel(id=uuid4(), **values)
            self._session.add(subscription)
            await self._session.flush()
        else:
            subscription = existing
            for key, value in values.items():
                setattr(subscription, key, value)
            await self._session.flush()
        await self._refresh_entitlements(subscription, plan.id, owner_type, owner_id, status)

    async def _refresh_entitlements(
        self,
        subscription: SubscriptionModel,
        plan_id: UUID,
        owner_type: str,
        owner_id: UUID,
        status: str,
    ) -> None:
        await self._session.execute(
            update(EntitlementModel)
            .where(EntitlementModel.source_subscription_id == subscription.id)
            .values(status="revoked")
        )
        features = (
            (
                await self._session.execute(
                    select(PlanFeatureModel.feature_code).where(PlanFeatureModel.plan_id == plan_id)
                )
            )
            .scalars()
            .all()
        )
        for feature_code in features:
            subject_filter = [
                EntitlementModel.subject_type == owner_type,
                EntitlementModel.feature_code == feature_code,
            ]
            subject_filter.append(
                EntitlementModel.account_id == owner_id
                if owner_type == "account"
                else EntitlementModel.organisation_id == owner_id
            )
            entitlement = (
                await self._session.execute(
                    select(EntitlementModel).where(*subject_filter).with_for_update()
                )
            ).scalar_one_or_none()
            values = {
                "source_subscription_id": subscription.id,
                "status": "active" if status in {"active", "trialing"} else "revoked",
                "valid_until": None,
            }
            if entitlement is None:
                self._session.add(
                    EntitlementModel(
                        subject_type=owner_type,
                        account_id=owner_id if owner_type == "account" else None,
                        organisation_id=owner_id if owner_type == "organisation" else None,
                        feature_code=feature_code,
                        **values,
                    )
                )
            else:
                for key, value in values.items():
                    setattr(entitlement, key, value)
        await self._session.flush()

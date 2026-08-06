"""Service métier des plans et entitlements.

Aucun fournisseur de paiement n'est appelé ici. Stripe, Google Play et Apple
alimenteront ultérieurement les abonnements via des webhooks vérifiés, tandis
que ce service restera l'unique source des fonctionnalités effectivement
accordées.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol
from uuid import UUID, uuid4

from sqlalchemy import update

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from gsie_api.billing.store_gateways import VerifiedPurchase
    from gsie_api.infrastructure.models.billing import EntitlementModel, SubscriptionModel


@dataclass(frozen=True, slots=True)
class PlanRecord:
    code: str
    display_name: str
    product_scope: str
    monthly_amount_cents: int | None
    annual_amount_cents: int | None
    trial_days: int
    features: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EntitlementRecord:
    feature_code: str
    subject_type: str
    subject_id: UUID
    status: str
    valid_until: datetime | None


class BillingRepositoryProtocol(Protocol):
    async def list_public_plans(self) -> list[PlanRecord]: ...

    async def list_account_entitlements(self, account_id: UUID) -> list[EntitlementRecord]: ...

    async def list_organisation_entitlements(
        self, organisation_id: UUID
    ) -> list[EntitlementRecord]: ...

    async def ensure_free_account(self, account_id: UUID) -> None: ...

    async def apply_verified_purchase(
        self, owner_type: str, owner_id: UUID, purchase: VerifiedPurchase
    ) -> None: ...


class BillingService:
    """Expose le catalogue et calcule les droits effectifs du contexte."""

    def __init__(self, repository: BillingRepositoryProtocol) -> None:
        self._repository = repository

    async def list_public_plans(self) -> list[PlanRecord]:
        return await self._repository.list_public_plans()

    async def ensure_free_account(self, account_id: UUID) -> None:
        await self._repository.ensure_free_account(account_id)

    async def apply_verified_purchase(
        self, owner_type: str, owner_id: UUID, purchase: VerifiedPurchase
    ) -> None:
        await self._repository.apply_verified_purchase(owner_type, owner_id, purchase)

    async def get_effective_entitlements(
        self,
        account_id: UUID,
        organisation_id: UUID | None,
    ) -> list[EntitlementRecord]:
        account = await self._repository.list_account_entitlements(account_id)
        if organisation_id is None:
            return self._active(account)
        organisation = await self._repository.list_organisation_entitlements(organisation_id)
        return self._active([*account, *organisation])

    @staticmethod
    def _active(
        entitlements: list[EntitlementRecord],
    ) -> list[EntitlementRecord]:
        now = datetime.now(UTC)
        effective: dict[str, EntitlementRecord] = {}
        for entitlement in entitlements:
            if entitlement.status != "active":
                continue
            if entitlement.valid_until is not None and entitlement.valid_until <= now:
                continue
            effective[entitlement.feature_code] = entitlement
        return list(effective.values())


class SqlAlchemyBillingRepository:
    """Dépôt SQLAlchemy du catalogue public et des droits actifs."""

    def __init__(self, session: AsyncSession) -> None:
        from sqlalchemy import select

        from gsie_api.infrastructure.models.billing import (
            EntitlementModel,
            PlanFeatureModel,
            PlanModel,
            SubscriptionModel,
        )

        self._session = session
        self._select = select
        self._entitlement_model = EntitlementModel
        self._plan_feature_model = PlanFeatureModel
        self._plan_model = PlanModel
        self._subscription_model = SubscriptionModel

    async def list_public_plans(self) -> list[PlanRecord]:
        statement = (
            self._select(self._plan_model)
            .where(self._plan_model.is_public.is_(True), self._plan_model.status == "active")
            .order_by(self._plan_model.monthly_amount_cents.nulls_last(), self._plan_model.code)
        )
        plans = (await self._session.execute(statement)).scalars().all()
        result: list[PlanRecord] = []
        for plan in plans:
            features_stmt = self._select(self._plan_feature_model.feature_code).where(
                self._plan_feature_model.plan_id == plan.id
            )
            features = tuple((await self._session.execute(features_stmt)).scalars().all())
            result.append(
                PlanRecord(
                    code=plan.code,
                    display_name=plan.display_name,
                    product_scope=plan.product_scope,
                    monthly_amount_cents=plan.monthly_amount_cents,
                    annual_amount_cents=plan.annual_amount_cents,
                    trial_days=plan.trial_days,
                    features=features,
                )
            )
        return result

    async def list_account_entitlements(self, account_id: UUID) -> list[EntitlementRecord]:
        statement = self._select(self._entitlement_model).where(
            self._entitlement_model.account_id == account_id,
            self._entitlement_model.subject_type == "account",
        )
        models = (await self._session.execute(statement)).scalars().all()
        return [self._to_record(model, account_id) for model in models]

    async def list_organisation_entitlements(
        self, organisation_id: UUID
    ) -> list[EntitlementRecord]:
        statement = self._select(self._entitlement_model).where(
            self._entitlement_model.organisation_id == organisation_id,
            self._entitlement_model.subject_type == "organisation",
        )
        models = (await self._session.execute(statement)).scalars().all()
        return [self._to_record(model, organisation_id) for model in models]

    async def ensure_free_account(self, account_id: UUID) -> None:
        from datetime import UTC, datetime

        from gsie_api.infrastructure.models.billing import PlanModel, SubscriptionModel

        subscription_stmt = (
            self._select(SubscriptionModel.id)
            .where(
                SubscriptionModel.owner_type == "account",
                SubscriptionModel.account_id == account_id,
                SubscriptionModel.status.in_(("trialing", "active")),
            )
            .limit(1)
        )
        if (await self._session.execute(subscription_stmt)).scalar_one_or_none() is not None:
            return
        plan = (
            await self._session.execute(
                self._select(PlanModel).where(
                    PlanModel.code == "free", PlanModel.status == "active"
                )
            )
        ).scalar_one()
        subscription = SubscriptionModel(
            owner_type="account",
            account_id=account_id,
            plan_id=plan.id,
            provider="internal",
            status="active",
            current_period_start=datetime.now(UTC),
        )
        self._session.add(subscription)
        await self._session.flush()
        features_stmt = self._select(self._plan_feature_model.feature_code).where(
            self._plan_feature_model.plan_id == plan.id
        )
        for feature_code in (await self._session.execute(features_stmt)).scalars().all():
            self._session.add(
                self._entitlement_model(
                    subject_type="account",
                    account_id=account_id,
                    feature_code=feature_code,
                    source_subscription_id=subscription.id,
                    status="active",
                )
            )
        await self._session.flush()

    async def apply_verified_purchase(
        self,
        owner_type: str,
        owner_id: UUID,
        purchase: VerifiedPurchase,
    ) -> None:
        """Projette une preuve store dans subscription + entitlements."""
        if owner_type not in {"account", "organisation"}:
            raise ValueError("Propriétaire billing invalide")
        plan = (
            await self._session.execute(
                self._select(self._plan_model).where(
                    self._plan_model.code == purchase.plan_code,
                    self._plan_model.status == "active",
                )
            )
        ).scalar_one_or_none()
        if plan is None:
            raise ValueError("Plan store inconnu")
        subscription = (
            await self._session.execute(
                self._select(self._subscription_model).where(
                    self._subscription_model.provider == purchase.provider,
                    self._subscription_model.external_subscription_id
                    == purchase.external_transaction_id,
                )
            )
        ).scalar_one_or_none()
        values = {
            "owner_type": owner_type,
            "account_id": owner_id if owner_type == "account" else None,
            "organisation_id": owner_id if owner_type == "organisation" else None,
            "plan_id": plan.id,
            "provider": purchase.provider,
            "external_subscription_id": purchase.external_transaction_id,
            "status": purchase.status,
            "current_period_end": purchase.expires_at,
            "updated_at": datetime.now(UTC),
        }
        if subscription is None:
            subscription = self._subscription_model(id=uuid4(), **values)
            self._session.add(subscription)
            await self._session.flush()
        else:
            for key, value in values.items():
                setattr(subscription, key, value)
            await self._session.flush()
        await self._sync_entitlements(subscription, plan.id, owner_type, owner_id, purchase.status)

    async def _sync_entitlements(
        self,
        subscription: SubscriptionModel,
        plan_id: UUID,
        owner_type: str,
        owner_id: UUID,
        status: str,
    ) -> None:
        await self._session.execute(
            update(self._entitlement_model)
            .where(self._entitlement_model.source_subscription_id == subscription.id)
            .values(status="revoked")
        )
        features = (
            (
                await self._session.execute(
                    self._select(self._plan_feature_model.feature_code).where(
                        self._plan_feature_model.plan_id == plan_id
                    )
                )
            )
            .scalars()
            .all()
        )
        for feature_code in features:
            filters = [
                self._entitlement_model.subject_type == owner_type,
                self._entitlement_model.feature_code == feature_code,
            ]
            filters.append(
                self._entitlement_model.account_id == owner_id
                if owner_type == "account"
                else self._entitlement_model.organisation_id == owner_id
            )
            entitlement = (
                await self._session.execute(
                    self._select(self._entitlement_model).where(*filters).with_for_update()
                )
            ).scalar_one_or_none()
            values = {
                "source_subscription_id": subscription.id,
                "status": "active" if status == "active" else "revoked",
                "valid_until": subscription.current_period_end,
            }
            if entitlement is None:
                self._session.add(
                    self._entitlement_model(
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

    @staticmethod
    def _to_record(model: EntitlementModel, subject_id: UUID) -> EntitlementRecord:
        return EntitlementRecord(
            feature_code=model.feature_code,
            subject_type=model.subject_type,
            subject_id=subject_id,
            status=model.status,
            valid_until=model.valid_until,
        )

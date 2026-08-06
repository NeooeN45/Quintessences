"""Validation des achats Google Play et Apple App Store.

Les deux passerelles vérifient un achat auprès du fournisseur avant toute
activation locale. Elles ne connaissent pas les permissions métier : elles
retournent une preuve normalisée consommée par le service billing.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, cast

import httpx
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account

from gsie_api.core.config import get_settings


class StoreNotConfiguredError(RuntimeError):
    """La passerelle store n'est pas configurée."""


class StorePurchaseInvalidError(ValueError):
    """Le reçu ou token d'achat n'est pas valide."""


class AppleSignedVerifier(Protocol):
    def verify_and_decode_signed_transaction(self, value: str) -> Any: ...


@dataclass(frozen=True, slots=True)
class VerifiedPurchase:
    """Preuve normalisée d'un abonnement store vérifié côté serveur."""

    provider: str
    external_transaction_id: str
    external_product_id: str
    plan_code: str
    status: str
    expires_at: datetime | None


class GooglePlayPurchaseGateway:
    """Vérifie les abonnements via Google Play Developer API v3."""

    _SCOPE = "https://www.googleapis.com/auth/androidpublisher"
    _BASE_URL = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"

    def __init__(self) -> None:
        self._settings = get_settings()

    def _configure(self) -> None:
        settings = self._settings
        if not settings.google_play_enabled:
            raise StoreNotConfiguredError("Google Play est désactivé")
        if not settings.google_play_package_name:
            raise StoreNotConfiguredError("Package Google Play absent")
        if not settings.google_play_service_account_json_path:
            raise StoreNotConfiguredError("Compte de service Google Play absent")

    def _plan_code(self, product_id: str) -> str:
        mapping = {
            self._settings.google_play_product_geosylva_pro: "geosylva_pro",
            self._settings.google_play_product_quintessences_pro: "quintessences_pro",
        }
        plan_code = mapping.get(product_id)
        if not plan_code:
            raise StorePurchaseInvalidError("Produit Google Play inconnu")
        return plan_code

    async def verify_subscription(self, purchase_token: str) -> VerifiedPurchase:
        """Vérifie le token auprès de Google, sans jamais faire confiance au mobile."""
        self._configure()
        if not purchase_token.strip():
            raise StorePurchaseInvalidError("Token Google Play vide")
        access_token = await asyncio.to_thread(self._access_token)
        url = (
            f"{self._BASE_URL}/{self._settings.google_play_package_name}"
            f"/purchases/subscriptionsv2/tokens/{purchase_token}"
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.status_code != 200:
            raise StorePurchaseInvalidError("Achat Google Play non vérifié")
        payload = cast("dict[str, Any]", response.json())
        state = str(payload.get("subscriptionState", ""))
        status = self._status(state)
        line_items = payload.get("lineItems")
        if not isinstance(line_items, list) or not line_items:
            raise StorePurchaseInvalidError("Aucune ligne d'achat Google Play")
        line_item = line_items[0]
        if not isinstance(line_item, dict):
            raise StorePurchaseInvalidError("Ligne d'achat Google Play invalide")
        product_id = str(line_item.get("productId", ""))
        expiry = self._parse_expiry(line_item.get("expiryTime"))
        transaction_id = str(line_item.get("latestSuccessfulOrderId") or purchase_token)
        return VerifiedPurchase(
            provider="google_play",
            external_transaction_id=transaction_id,
            external_product_id=product_id,
            plan_code=self._plan_code(product_id),
            status=status,
            expires_at=expiry,
        )

    def _access_token(self) -> str:
        credentials = service_account.Credentials.from_service_account_file(  # type: ignore[no-untyped-call]
            self._settings.google_play_service_account_json_path,
            scopes=[self._SCOPE],
        )
        credentials.refresh(GoogleAuthRequest())
        if not credentials.token:
            raise StorePurchaseInvalidError("Google Play n'a pas fourni de jeton")
        return str(credentials.token)

    @staticmethod
    def _status(state: str) -> str:
        return {
            "SUBSCRIPTION_STATE_ACTIVE": "active",
            "SUBSCRIPTION_STATE_IN_GRACE_PERIOD": "past_due",
            "SUBSCRIPTION_STATE_CANCELED": "canceled",
            "SUBSCRIPTION_STATE_EXPIRED": "ended",
            "SUBSCRIPTION_STATE_ON_HOLD": "past_due",
            "SUBSCRIPTION_STATE_PAUSED": "canceled",
        }.get(state, "ended")

    @staticmethod
    def _parse_expiry(value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError as exc:
            raise StorePurchaseInvalidError("Expiration Google Play invalide") from exc


class ApplePurchaseGateway:
    """Vérifie les transactions avec la bibliothèque officielle Apple."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def verify_subscription(self, original_transaction_id: str) -> VerifiedPurchase:
        settings = self._settings
        if not settings.apple_store_enabled:
            raise StoreNotConfiguredError("Apple App Store est désactivé")
        if not original_transaction_id.strip():
            raise StorePurchaseInvalidError("Transaction Apple vide")
        required = (
            settings.apple_store_bundle_id,
            settings.apple_store_issuer_id,
            settings.apple_store_key_id,
            settings.apple_store_private_key_path,
            settings.apple_store_root_certificates_path,
        )
        if not all(required):
            raise StoreNotConfiguredError("Configuration Apple App Store incomplète")

        from appstoreserverlibrary.api_client import AsyncAppStoreServerAPIClient
        from appstoreserverlibrary.models.Environment import Environment
        from appstoreserverlibrary.signed_data_verifier import SignedDataVerifier

        environment = (
            Environment.PRODUCTION
            if settings.apple_store_environment == "production"
            else Environment.SANDBOX
        )
        private_key = Path(settings.apple_store_private_key_path).read_bytes()
        root_certificates = [
            Path(path).read_bytes() for path in settings.apple_store_root_certificates_path
        ]
        verifier = SignedDataVerifier(
            root_certificates,
            True,
            environment,
            settings.apple_store_bundle_id,
        )
        client = AsyncAppStoreServerAPIClient(
            private_key,
            settings.apple_store_key_id,
            settings.apple_store_issuer_id,
            settings.apple_store_bundle_id,
            environment,
        )
        try:
            response = await client.get_all_subscription_statuses(original_transaction_id)
            return self._to_purchase(response, verifier, original_transaction_id)
        except Exception as exc:
            raise StorePurchaseInvalidError("Achat Apple non vérifié") from exc
        finally:
            await client.async_close()  # type: ignore[no-untyped-call]

    def _to_purchase(
        self,
        response: object,
        verifier: AppleSignedVerifier,
        transaction_id: str,
    ) -> VerifiedPurchase:
        signed_items = getattr(response, "data", None) or []
        for item in signed_items:
            signed_transactions = getattr(item, "last_transactions", None) or []
            for signed in signed_transactions:
                signed_transaction = getattr(signed, "signed_transaction_info", None)
                if not signed_transaction:
                    continue
                decoded = verifier.verify_and_decode_signed_transaction(signed_transaction)
                product_id = str(decoded.product_id)
                plan_code = self._plan_code(product_id)
                expires_at = self._expiry_from_millis(decoded.expires_date)
                return VerifiedPurchase(
                    provider="apple",
                    external_transaction_id=str(decoded.transaction_id or transaction_id),
                    external_product_id=product_id,
                    plan_code=plan_code,
                    status=(
                        "active"
                        if expires_at is None or expires_at > datetime.now(UTC)
                        else "ended"
                    ),
                    expires_at=expires_at,
                )
        raise StorePurchaseInvalidError("Aucune transaction Apple active")

    def _plan_code(self, product_id: str) -> str:
        if product_id.endswith("geosylva_pro"):
            return "geosylva_pro"
        if product_id.endswith("quintessences_pro"):
            return "quintessences_pro"
        raise StorePurchaseInvalidError("Produit Apple inconnu")

    @staticmethod
    def _expiry_from_millis(value: object) -> datetime | None:
        if not isinstance(value, int):
            return None
        return datetime.fromtimestamp(value / 1000, tz=UTC)

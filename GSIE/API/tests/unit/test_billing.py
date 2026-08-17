"""Tests du module billing : catalogue, service, passerelles store et Stripe.

Convention : aucun réseau réel n'est joint. Les appels HTTP sortants (Google
Play) passent par ``respx`` ; les SDK tiers (Stripe, Apple, Google Auth) sont
monkeypatchés à leur point d'entrée. Les dépôts SQLAlchemy sont exercés avec
une session « scriptée » qui rejoue les résultats attendus dans l'ordre exact
des appels du code, afin de vérifier le comportement métier réel (valeurs
insérées/mises à jour, branches d'erreur) plutôt qu'un simple appel sans
assertion.
"""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import httpx
import pytest
import respx
import stripe
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from gsie_api.billing import router as router_module
from gsie_api.billing.service import (
    BillingService,
    EntitlementRecord,
    PlanRecord,
    SqlAlchemyBillingRepository,
)
from gsie_api.billing.store_gateways import (
    ApplePurchaseGateway,
    GooglePlayPurchaseGateway,
    StoreNotConfiguredError,
    StorePurchaseInvalidError,
    VerifiedPurchase,
)
from gsie_api.billing.stripe_gateway import (
    StripeBillingError,
    StripeBillingGateway,
    StripeNotConfiguredError,
    StripeWebhookError,
    StripeWebhookProcessor,
)
from gsie_api.core.auth import create_access_token
from gsie_api.core.config import get_settings

# ---------------------------------------------------------------------------
# Fixtures / doublures partagées
# ---------------------------------------------------------------------------


class FakeBillingRepository:
    async def list_public_plans(self) -> list[Any]:
        return []

    async def list_account_entitlements(self, account_id: UUID) -> list[EntitlementRecord]:
        return [
            EntitlementRecord("account.access", "account", account_id, "active", None),
            EntitlementRecord(
                "expired.feature",
                "account",
                account_id,
                "active",
                datetime.now(UTC) - timedelta(minutes=1),
            ),
        ]

    async def list_organisation_entitlements(
        self, organisation_id: UUID
    ) -> list[EntitlementRecord]:
        return [
            EntitlementRecord("enterprise.audit", "organisation", organisation_id, "active", None)
        ]

    async def ensure_free_account(self, account_id: UUID) -> None:
        return None


class RecordingResult:
    """Simule un ``Result`` SQLAlchemy pour ``.scalars().all()`` / ``.scalar_one[_or_none]()``."""

    def __init__(
        self,
        *,
        all_items: list[Any] | None = None,
        one: Any = None,
        one_or_none: Any = None,
    ) -> None:
        self._all_items = all_items or []
        self._one = one
        self._one_or_none = one_or_none

    def scalars(self) -> RecordingResult:
        return self

    def all(self) -> list[Any]:
        return self._all_items

    def scalar_one(self) -> Any:
        return self._one

    def scalar_one_or_none(self) -> Any:
        return self._one_or_none


class ScriptedSession:
    """Session AsyncSession factice rejouant des résultats dans l'ordre attendu.

    ``execute_results`` alimente ``execute()`` (utilisé par le dépôt billing) ;
    ``scalar_results`` alimente ``scalar()`` (utilisé par le processeur webhook
    Stripe, qui appelle directement ``session.scalar(select(...))``).
    """

    def __init__(
        self,
        execute_results: list[Any] | None = None,
        scalar_results: list[Any] | None = None,
    ) -> None:
        self._execute_results = deque(execute_results or [])
        self._scalar_results = deque(scalar_results or [])
        self.added: list[Any] = []
        self.executed_statements: list[Any] = []
        self.scalar_statements: list[Any] = []
        self.flush_count = 0
        self.committed = False
        self.rolled_back = False
        self.flush_side_effect: BaseException | None = None

    async def execute(self, statement: Any) -> Any:
        self.executed_statements.append(statement)
        if not self._execute_results:
            return RecordingResult()
        return self._execute_results.popleft()

    async def scalar(self, statement: Any) -> Any:
        self.scalar_statements.append(statement)
        return self._scalar_results.popleft()

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        self.flush_count += 1
        if self.flush_side_effect is not None:
            effect = self.flush_side_effect
            self.flush_side_effect = None
            raise effect

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


def _repo(session: ScriptedSession) -> SqlAlchemyBillingRepository:
    return SqlAlchemyBillingRepository(session)  # type: ignore[arg-type]


# ===========================================================================
# service.py — BillingService (logique pure, dépôt factice)
# ===========================================================================


async def test_should_filter_expired_entitlements_when_context_is_resolved() -> None:
    account_id = uuid4()
    organisation_id = uuid4()
    service = BillingService(FakeBillingRepository())

    entitlements = await service.get_effective_entitlements(account_id, organisation_id)

    assert {item.feature_code for item in entitlements} == {
        "account.access",
        "enterprise.audit",
    }


async def should_return_only_account_entitlements_when_no_organisation_is_active() -> None:
    """Sans organisation active, seules les entitlements du compte comptent."""
    account_id = uuid4()
    service = BillingService(FakeBillingRepository())

    entitlements = await service.get_effective_entitlements(account_id, None)

    assert {item.feature_code for item in entitlements} == {"account.access"}


async def should_delegate_public_plans_listing_to_the_repository() -> None:
    repository = AsyncMock()
    repository.list_public_plans.return_value = [
        PlanRecord("free", "Gratuit", "geosylva", None, None, 0, ("basic",))
    ]
    service = BillingService(repository)

    plans = await service.list_public_plans()

    assert plans[0].code == "free"
    repository.list_public_plans.assert_awaited_once()


async def should_delegate_ensure_free_account_to_the_repository() -> None:
    repository = AsyncMock()
    service = BillingService(repository)
    account_id = uuid4()

    await service.ensure_free_account(account_id)

    repository.ensure_free_account.assert_awaited_once_with(account_id)


async def should_delegate_apply_verified_purchase_to_the_repository() -> None:
    repository = AsyncMock()
    service = BillingService(repository)
    owner_id = uuid4()
    purchase = VerifiedPurchase("stripe", "sub_1", "prod_1", "geosylva_pro", "active", None)

    await service.apply_verified_purchase("account", owner_id, purchase)

    repository.apply_verified_purchase.assert_awaited_once_with("account", owner_id, purchase)


def should_drop_entitlement_when_status_is_not_active() -> None:
    """``_active`` élimine toute entitlement dont le statut n'est pas ``active``."""
    account_id = uuid4()
    revoked = EntitlementRecord("revoked.feature", "account", account_id, "revoked", None)

    active = BillingService._active([revoked])

    assert active == []


def should_keep_last_entitlement_when_feature_code_is_duplicated() -> None:
    """Le dernier enregistrement d'un ``feature_code`` gagne (dict d'agrégation)."""
    account_id = uuid4()
    first = EntitlementRecord("dup.feature", "account", account_id, "active", None)
    second = EntitlementRecord(
        "dup.feature", "account", account_id, "active", datetime.now(UTC) + timedelta(days=1)
    )

    active = BillingService._active([first, second])

    assert active == [second]


# ===========================================================================
# service.py — SqlAlchemyBillingRepository (session scriptée)
# ===========================================================================


async def should_list_public_plans_with_their_features() -> None:
    plan_a = SimpleNamespace(
        id=uuid4(),
        code="free",
        display_name="Gratuit",
        product_scope="geosylva",
        monthly_amount_cents=None,
        annual_amount_cents=None,
        trial_days=0,
    )
    plan_b = SimpleNamespace(
        id=uuid4(),
        code="pro",
        display_name="Pro",
        product_scope="geosylva",
        monthly_amount_cents=990,
        annual_amount_cents=9900,
        trial_days=14,
    )
    session = ScriptedSession(
        execute_results=[
            RecordingResult(all_items=[plan_a, plan_b]),
            RecordingResult(all_items=["basic"]),
            RecordingResult(all_items=["basic", "advanced"]),
        ]
    )

    plans = await _repo(session).list_public_plans()

    assert [p.code for p in plans] == ["free", "pro"]
    assert plans[0].features == ("basic",)
    assert plans[1].features == ("basic", "advanced")


async def should_map_account_entitlements_to_records() -> None:
    account_id = uuid4()
    model = SimpleNamespace(
        feature_code="account.access",
        subject_type="account",
        status="active",
        valid_until=None,
    )
    session = ScriptedSession(execute_results=[RecordingResult(all_items=[model])])

    records = await _repo(session).list_account_entitlements(account_id)

    assert records == [EntitlementRecord("account.access", "account", account_id, "active", None)]


async def should_map_organisation_entitlements_to_records() -> None:
    organisation_id = uuid4()
    model = SimpleNamespace(
        feature_code="enterprise.audit",
        subject_type="organisation",
        status="active",
        valid_until=None,
    )
    session = ScriptedSession(execute_results=[RecordingResult(all_items=[model])])

    records = await _repo(session).list_organisation_entitlements(organisation_id)

    assert records == [
        EntitlementRecord("enterprise.audit", "organisation", organisation_id, "active", None)
    ]


async def should_skip_free_account_creation_when_subscription_already_active() -> None:
    account_id = uuid4()
    session = ScriptedSession(execute_results=[RecordingResult(one_or_none=uuid4())])

    await _repo(session).ensure_free_account(account_id)

    assert session.added == []
    assert session.flush_count == 0


async def should_create_free_subscription_and_entitlements_when_none_exist() -> None:
    account_id = uuid4()
    plan = SimpleNamespace(id=uuid4(), code="free")
    session = ScriptedSession(
        execute_results=[
            RecordingResult(one_or_none=None),  # aucune souscription active
            RecordingResult(one=plan),  # plan gratuit
            RecordingResult(all_items=["account.access", "account.storage"]),
        ]
    )

    await _repo(session).ensure_free_account(account_id)

    subscriptions = [obj for obj in session.added if hasattr(obj, "plan_id")]
    entitlements = [obj for obj in session.added if hasattr(obj, "feature_code")]
    assert len(subscriptions) == 1
    assert subscriptions[0].account_id == account_id
    assert subscriptions[0].provider == "internal"
    assert {e.feature_code for e in entitlements} == {"account.access", "account.storage"}
    assert all(e.status == "active" for e in entitlements)
    assert session.flush_count == 2


async def should_reject_apply_verified_purchase_when_owner_type_is_invalid() -> None:
    session = ScriptedSession()
    purchase = VerifiedPurchase("stripe", "sub_1", "prod_1", "geosylva_pro", "active", None)

    with pytest.raises(ValueError, match="Propriétaire billing invalide"):
        await _repo(session).apply_verified_purchase("invalid", uuid4(), purchase)


async def should_reject_apply_verified_purchase_when_plan_is_unknown() -> None:
    session = ScriptedSession(execute_results=[RecordingResult(one_or_none=None)])
    purchase = VerifiedPurchase("stripe", "sub_1", "prod_1", "inexistant", "active", None)

    with pytest.raises(ValueError, match="Plan store inconnu"):
        await _repo(session).apply_verified_purchase("account", uuid4(), purchase)


async def should_create_subscription_and_active_entitlements_on_new_verified_purchase() -> None:
    owner_id = uuid4()
    plan = SimpleNamespace(id=uuid4(), code="geosylva_pro")
    purchase = VerifiedPurchase(
        "google_play", "order_1", "product_1", "geosylva_pro", "active", None
    )
    session = ScriptedSession(
        execute_results=[
            RecordingResult(one_or_none=plan),  # plan trouvé
            RecordingResult(one_or_none=None),  # pas de souscription existante
            RecordingResult(),  # update revoke (ignoré)
            RecordingResult(all_items=["geosylva.pro"]),  # features du plan
            RecordingResult(one_or_none=None),  # pas d'entitlement existant
        ]
    )

    await _repo(session).apply_verified_purchase("account", owner_id, purchase)

    subscriptions = [obj for obj in session.added if hasattr(obj, "plan_id")]
    entitlements = [obj for obj in session.added if hasattr(obj, "feature_code")]
    assert len(subscriptions) == 1
    assert subscriptions[0].account_id == owner_id
    assert subscriptions[0].provider == "google_play"
    assert subscriptions[0].external_subscription_id == "order_1"
    assert len(entitlements) == 1
    assert entitlements[0].status == "active"


async def should_update_existing_subscription_and_revoke_entitlements_on_ended_purchase() -> None:
    owner_id = uuid4()
    plan = SimpleNamespace(id=uuid4(), code="geosylva_pro")
    existing_subscription = SimpleNamespace(
        id=uuid4(),
        owner_type="account",
        account_id=owner_id,
        organisation_id=None,
        plan_id=uuid4(),
        provider="google_play",
        external_subscription_id="order_1",
        status="active",
        current_period_end=None,
        updated_at=None,
    )
    existing_entitlement = SimpleNamespace(
        source_subscription_id=None, status="active", valid_until=None
    )
    purchase = VerifiedPurchase(
        "google_play", "order_1", "product_1", "geosylva_pro", "ended", None
    )
    session = ScriptedSession(
        execute_results=[
            RecordingResult(one_or_none=plan),
            RecordingResult(one_or_none=existing_subscription),
            RecordingResult(),  # update revoke (ignoré)
            RecordingResult(all_items=["geosylva.pro"]),
            RecordingResult(one_or_none=existing_entitlement),
        ]
    )

    await _repo(session).apply_verified_purchase("account", owner_id, purchase)

    assert session.added == []  # aucune création, uniquement des mises à jour
    assert existing_subscription.status == "ended"
    assert existing_entitlement.status == "revoked"


# ===========================================================================
# store_gateways.py — GooglePlayPurchaseGateway
# ===========================================================================


def _configured_settings(monkeypatch: pytest.MonkeyPatch, **overrides: Any) -> Any:
    settings = get_settings()
    for key, value in overrides.items():
        setattr(settings, key, value)
    return settings


async def should_reject_google_play_verification_when_disabled() -> None:
    gateway = GooglePlayPurchaseGateway()
    gateway._settings.google_play_enabled = False

    with pytest.raises(StoreNotConfiguredError, match="Google Play est désactivé"):
        await gateway.verify_subscription("token")


async def should_reject_google_play_verification_when_package_name_missing() -> None:
    gateway = GooglePlayPurchaseGateway()
    gateway._settings.google_play_enabled = True
    gateway._settings.google_play_package_name = ""

    with pytest.raises(StoreNotConfiguredError, match="Package Google Play absent"):
        await gateway.verify_subscription("token")


async def should_reject_google_play_verification_when_service_account_missing() -> None:
    gateway = GooglePlayPurchaseGateway()
    gateway._settings.google_play_enabled = True
    gateway._settings.google_play_package_name = "fr.gsie.geosylva"
    gateway._settings.google_play_service_account_json_path = ""

    with pytest.raises(StoreNotConfiguredError, match="Compte de service Google Play absent"):
        await gateway.verify_subscription("token")


async def should_reject_google_play_verification_when_token_is_blank() -> None:
    gateway = GooglePlayPurchaseGateway()
    gateway._settings.google_play_enabled = True
    gateway._settings.google_play_package_name = "fr.gsie.geosylva"
    gateway._settings.google_play_service_account_json_path = "/tmp/sa.json"

    with pytest.raises(StorePurchaseInvalidError, match="Token Google Play vide"):
        await gateway.verify_subscription("   ")


def _ready_google_gateway(monkeypatch: pytest.MonkeyPatch) -> GooglePlayPurchaseGateway:
    gateway = GooglePlayPurchaseGateway()
    gateway._settings.google_play_enabled = True
    gateway._settings.google_play_package_name = "fr.gsie.geosylva"
    gateway._settings.google_play_service_account_json_path = "/tmp/sa.json"
    gateway._settings.google_play_product_geosylva_pro = "geosylva_pro_product"
    gateway._settings.google_play_product_quintessences_pro = "quintessences_pro_product"
    monkeypatch.setattr(gateway, "_access_token", lambda: "fake-access-token")
    return gateway


@respx.mock
async def should_reject_google_play_verification_when_http_status_is_not_200(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _ready_google_gateway(monkeypatch)
    respx.get(url__regex=r".*/purchases/subscriptionsv2/tokens/.*").mock(
        return_value=httpx.Response(404, json={})
    )

    with pytest.raises(StorePurchaseInvalidError, match="Achat Google Play non vérifié"):
        await gateway.verify_subscription("token-123")


@respx.mock
async def should_reject_google_play_verification_when_no_line_items(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _ready_google_gateway(monkeypatch)
    respx.get(url__regex=r".*/purchases/subscriptionsv2/tokens/.*").mock(
        return_value=httpx.Response(200, json={"subscriptionState": "SUBSCRIPTION_STATE_ACTIVE"})
    )

    with pytest.raises(StorePurchaseInvalidError, match="Aucune ligne d'achat Google Play"):
        await gateway.verify_subscription("token-123")


@respx.mock
async def should_reject_google_play_verification_when_line_item_is_not_a_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _ready_google_gateway(monkeypatch)
    respx.get(url__regex=r".*/purchases/subscriptionsv2/tokens/.*").mock(
        return_value=httpx.Response(
            200,
            json={"subscriptionState": "SUBSCRIPTION_STATE_ACTIVE", "lineItems": ["not-a-dict"]},
        )
    )

    with pytest.raises(StorePurchaseInvalidError, match="Ligne d'achat Google Play invalide"):
        await gateway.verify_subscription("token-123")


@respx.mock
async def should_reject_google_play_verification_when_product_id_is_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _ready_google_gateway(monkeypatch)
    respx.get(url__regex=r".*/purchases/subscriptionsv2/tokens/.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
                "lineItems": [{"productId": "produit-inconnu", "expiryTime": None}],
            },
        )
    )

    with pytest.raises(StorePurchaseInvalidError, match="Produit Google Play inconnu"):
        await gateway.verify_subscription("token-123")


@respx.mock
async def should_reject_google_play_verification_when_expiry_is_not_iso(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _ready_google_gateway(monkeypatch)
    respx.get(url__regex=r".*/purchases/subscriptionsv2/tokens/.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
                "lineItems": [
                    {
                        "productId": "geosylva_pro_product",
                        "expiryTime": "not-a-date",
                        "latestSuccessfulOrderId": "order_1",
                    }
                ],
            },
        )
    )

    with pytest.raises(StorePurchaseInvalidError, match="Expiration Google Play invalide"):
        await gateway.verify_subscription("token-123")


@respx.mock
async def should_verify_google_play_purchase_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _ready_google_gateway(monkeypatch)
    respx.get(url__regex=r".*/purchases/subscriptionsv2/tokens/.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "subscriptionState": "SUBSCRIPTION_STATE_IN_GRACE_PERIOD",
                "lineItems": [
                    {
                        "productId": "geosylva_pro_product",
                        "expiryTime": "2026-12-01T10:00:00Z",
                        "latestSuccessfulOrderId": "order_42",
                    }
                ],
            },
        )
    )

    purchase = await gateway.verify_subscription("token-123")

    assert purchase.provider == "google_play"
    assert purchase.plan_code == "geosylva_pro"
    assert purchase.status == "past_due"
    assert purchase.external_transaction_id == "order_42"
    assert purchase.expires_at == datetime(2026, 12, 1, 10, 0, tzinfo=UTC)


@respx.mock
async def should_fall_back_to_purchase_token_when_order_id_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _ready_google_gateway(monkeypatch)
    respx.get(url__regex=r".*/purchases/subscriptionsv2/tokens/.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "subscriptionState": "SUBSCRIPTION_STATE_CANCELED",
                "lineItems": [{"productId": "quintessences_pro_product", "expiryTime": None}],
            },
        )
    )

    purchase = await gateway.verify_subscription("token-999")

    assert purchase.external_transaction_id == "token-999"
    assert purchase.status == "canceled"
    assert purchase.expires_at is None


def should_produce_a_real_access_token_via_google_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exerce ``_access_token`` sans le mocker (chemin normalement inatteint ailleurs)."""
    gateway = GooglePlayPurchaseGateway()
    fake_credentials = SimpleNamespace(token="jeton-google", refresh=lambda request: None)
    monkeypatch.setattr(
        "gsie_api.billing.store_gateways.service_account.Credentials.from_service_account_file",
        lambda path, scopes: fake_credentials,
    )
    monkeypatch.setattr("gsie_api.billing.store_gateways.GoogleAuthRequest", lambda: object())

    token = gateway._access_token()

    assert token == "jeton-google"


def should_reject_access_token_when_google_returns_no_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = GooglePlayPurchaseGateway()
    fake_credentials = SimpleNamespace(token=None, refresh=lambda request: None)
    monkeypatch.setattr(
        "gsie_api.billing.store_gateways.service_account.Credentials.from_service_account_file",
        lambda path, scopes: fake_credentials,
    )
    monkeypatch.setattr("gsie_api.billing.store_gateways.GoogleAuthRequest", lambda: object())

    with pytest.raises(StorePurchaseInvalidError, match="Google Play n'a pas fourni de jeton"):
        gateway._access_token()


def should_map_unknown_google_play_subscription_state_to_ended() -> None:
    assert GooglePlayPurchaseGateway._status("SOMETHING_ELSE") == "ended"


def should_return_none_expiry_when_google_play_value_is_not_a_string() -> None:
    assert GooglePlayPurchaseGateway._parse_expiry(None) is None
    assert GooglePlayPurchaseGateway._parse_expiry(12345) is None


# ===========================================================================
# store_gateways.py — ApplePurchaseGateway
# ===========================================================================


async def should_reject_apple_verification_when_disabled() -> None:
    gateway = ApplePurchaseGateway()
    gateway._settings.apple_store_enabled = False

    with pytest.raises(StoreNotConfiguredError, match="Apple App Store est désactivé"):
        await gateway.verify_subscription("transaction-1")


async def should_reject_apple_verification_when_transaction_id_is_blank() -> None:
    gateway = ApplePurchaseGateway()
    gateway._settings.apple_store_enabled = True

    with pytest.raises(StorePurchaseInvalidError, match="Transaction Apple vide"):
        await gateway.verify_subscription("   ")


async def should_reject_apple_verification_when_configuration_is_incomplete() -> None:
    gateway = ApplePurchaseGateway()
    gateway._settings.apple_store_enabled = True
    gateway._settings.apple_store_bundle_id = ""
    gateway._settings.apple_store_issuer_id = ""
    gateway._settings.apple_store_key_id = ""
    gateway._settings.apple_store_private_key_path = ""
    gateway._settings.apple_store_root_certificates_path = []

    with pytest.raises(StoreNotConfiguredError, match="Configuration Apple App Store incomplète"):
        await gateway.verify_subscription("transaction-1")


def _ready_apple_gateway(tmp_path: Any) -> ApplePurchaseGateway:
    gateway = ApplePurchaseGateway()
    key_path = tmp_path / "key.p8"
    key_path.write_bytes(b"fake-private-key")
    cert_path = tmp_path / "root.cer"
    cert_path.write_bytes(b"fake-root-cert")
    gateway._settings.apple_store_enabled = True
    gateway._settings.apple_store_bundle_id = "fr.gsie.geosylva"
    gateway._settings.apple_store_issuer_id = "issuer-1"
    gateway._settings.apple_store_key_id = "key-1"
    gateway._settings.apple_store_private_key_path = str(key_path)
    gateway._settings.apple_store_root_certificates_path = [str(cert_path)]
    gateway._settings.apple_store_environment = "sandbox"
    return gateway


class _FakeAppleVerifier:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def verify_and_decode_signed_transaction(self, value: str) -> Any:
        return value


class _FakeAppleClient:
    instances: list[_FakeAppleClient] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.closed = False
        _FakeAppleClient.instances.append(self)

    async def get_all_subscription_statuses(self, original_transaction_id: str) -> Any:
        raise NotImplementedError

    async def async_close(self) -> None:
        self.closed = True


def _patch_apple_sdk(monkeypatch: pytest.MonkeyPatch, client_cls: type[_FakeAppleClient]) -> None:
    monkeypatch.setattr("appstoreserverlibrary.api_client.AsyncAppStoreServerAPIClient", client_cls)
    monkeypatch.setattr(
        "appstoreserverlibrary.signed_data_verifier.SignedDataVerifier", _FakeAppleVerifier
    )


async def should_wrap_apple_sdk_exception_into_invalid_purchase_error(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    gateway = _ready_apple_gateway(tmp_path)

    class BoomClient(_FakeAppleClient):
        async def get_all_subscription_statuses(self, original_transaction_id: str) -> Any:
            raise RuntimeError("panne réseau Apple")

    _patch_apple_sdk(monkeypatch, BoomClient)

    with pytest.raises(StorePurchaseInvalidError, match="Achat Apple non vérifié"):
        await gateway.verify_subscription("transaction-1")
    assert BoomClient.instances[-1].closed is True


async def should_reject_apple_verification_when_no_active_transaction_found(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    gateway = _ready_apple_gateway(tmp_path)

    class EmptyClient(_FakeAppleClient):
        async def get_all_subscription_statuses(self, original_transaction_id: str) -> Any:
            return SimpleNamespace(data=[])

    _patch_apple_sdk(monkeypatch, EmptyClient)

    # ``verify_subscription`` enveloppe toute exception SDK dans un message
    # générique ; on exerce donc directement ``_to_purchase`` pour vérifier
    # le message métier précis renvoyé quand aucune transaction n'est active.
    response = SimpleNamespace(data=[])
    with pytest.raises(StorePurchaseInvalidError, match="Aucune transaction Apple active"):
        gateway._to_purchase(response, _FakeAppleVerifier(), "transaction-1")

    with pytest.raises(StorePurchaseInvalidError, match="Achat Apple non vérifié"):
        await gateway.verify_subscription("transaction-1")


async def should_skip_items_without_signed_transaction_info(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    gateway = _ready_apple_gateway(tmp_path)

    class NoSignedTxClient(_FakeAppleClient):
        async def get_all_subscription_statuses(self, original_transaction_id: str) -> Any:
            item = SimpleNamespace(
                last_transactions=[SimpleNamespace(signed_transaction_info=None)]
            )
            return SimpleNamespace(data=[item])

    _patch_apple_sdk(monkeypatch, NoSignedTxClient)

    # Exerce directement ``_to_purchase`` : le ``continue`` sur l'item sans
    # ``signed_transaction_info`` (ligne 211-212) mène à la même erreur
    # métier, mais ``verify_subscription`` la ré-enveloppe (voir test ci-dessus).
    item = SimpleNamespace(last_transactions=[SimpleNamespace(signed_transaction_info=None)])
    response = SimpleNamespace(data=[item])
    with pytest.raises(StorePurchaseInvalidError, match="Aucune transaction Apple active"):
        gateway._to_purchase(response, _FakeAppleVerifier(), "transaction-1")


def _decoded_transaction(
    *, product_id: str, expires_date: int | None, transaction_id: str | None = "txn-1"
) -> SimpleNamespace:
    return SimpleNamespace(
        product_id=product_id, expires_date=expires_date, transaction_id=transaction_id
    )


async def should_verify_apple_purchase_successfully_when_still_active(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    gateway = _ready_apple_gateway(tmp_path)
    future_millis = int((datetime.now(UTC) + timedelta(days=30)).timestamp() * 1000)
    decoded = _decoded_transaction(product_id="com.gsie.geosylva_pro", expires_date=future_millis)

    class ActiveClient(_FakeAppleClient):
        async def get_all_subscription_statuses(self, original_transaction_id: str) -> Any:
            item = SimpleNamespace(
                last_transactions=[SimpleNamespace(signed_transaction_info="signed-blob")]
            )
            return SimpleNamespace(data=[item])

    class DecodingVerifier(_FakeAppleVerifier):
        def verify_and_decode_signed_transaction(self, value: str) -> Any:
            return decoded

    monkeypatch.setattr(
        "appstoreserverlibrary.api_client.AsyncAppStoreServerAPIClient", ActiveClient
    )
    monkeypatch.setattr(
        "appstoreserverlibrary.signed_data_verifier.SignedDataVerifier", DecodingVerifier
    )

    purchase = await gateway.verify_subscription("transaction-1")

    assert purchase.provider == "apple"
    assert purchase.plan_code == "geosylva_pro"
    assert purchase.status == "active"
    assert purchase.external_transaction_id == "txn-1"


async def should_mark_apple_purchase_ended_when_expiry_is_in_the_past(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    gateway = _ready_apple_gateway(tmp_path)
    past_millis = int((datetime.now(UTC) - timedelta(days=1)).timestamp() * 1000)
    decoded = _decoded_transaction(
        product_id="com.gsie.quintessences_pro", expires_date=past_millis, transaction_id=None
    )

    class ExpiredClient(_FakeAppleClient):
        async def get_all_subscription_statuses(self, original_transaction_id: str) -> Any:
            item = SimpleNamespace(
                last_transactions=[SimpleNamespace(signed_transaction_info="signed-blob")]
            )
            return SimpleNamespace(data=[item])

    class DecodingVerifier(_FakeAppleVerifier):
        def verify_and_decode_signed_transaction(self, value: str) -> Any:
            return decoded

    monkeypatch.setattr(
        "appstoreserverlibrary.api_client.AsyncAppStoreServerAPIClient", ExpiredClient
    )
    monkeypatch.setattr(
        "appstoreserverlibrary.signed_data_verifier.SignedDataVerifier", DecodingVerifier
    )

    purchase = await gateway.verify_subscription("transaction-fallback")

    assert purchase.status == "ended"
    assert purchase.plan_code == "quintessences_pro"
    # transaction_id absent côté décodé -> repli sur l'identifiant d'entrée
    assert purchase.external_transaction_id == "transaction-fallback"


def should_reject_unknown_apple_product_id() -> None:
    gateway = ApplePurchaseGateway()

    with pytest.raises(StorePurchaseInvalidError, match="Produit Apple inconnu"):
        gateway._plan_code("com.gsie.something_else")


def should_return_none_expiry_when_apple_millis_value_is_not_an_int() -> None:
    assert ApplePurchaseGateway._expiry_from_millis(None) is None
    assert ApplePurchaseGateway._expiry_from_millis("123") is None


# ===========================================================================
# stripe_gateway.py — StripeBillingGateway
# ===========================================================================


def should_reject_checkout_when_stripe_is_disabled() -> None:
    gateway = StripeBillingGateway()

    with pytest.raises(StripeNotConfiguredError, match="Stripe n'est pas configuré"):
        gateway._configure()


def should_reject_price_lookup_when_plan_has_no_configured_price() -> None:
    gateway = StripeBillingGateway()

    with pytest.raises(StripeNotConfiguredError, match="Price Stripe absent"):
        gateway._price_id("plan-inconnu")


def _enabled_stripe_settings(monkeypatch: pytest.MonkeyPatch) -> Any:
    from pydantic import SecretStr

    gateway = StripeBillingGateway()
    gateway._settings.stripe_enabled = True
    gateway._settings.stripe_secret_key = SecretStr("sk_test_123")
    gateway._settings.stripe_price_geosylva_pro_monthly = "price_geosylva"
    gateway._settings.stripe_price_quintessences_pro_monthly = "price_quintessences"
    gateway._settings.stripe_portal_return_url = "https://app.example/billing"
    gateway._settings.stripe_checkout_success_url = "https://app.example/success"
    gateway._settings.stripe_checkout_cancel_url = "https://app.example/cancel"
    return gateway


async def should_create_portal_session_successfully(monkeypatch: pytest.MonkeyPatch) -> None:
    gateway = _enabled_stripe_settings(monkeypatch)
    captured: dict[str, Any] = {}

    def fake_create(**kwargs: Any) -> Any:
        captured.update(kwargs)
        return SimpleNamespace(url="https://billing.stripe.com/session/abc")

    monkeypatch.setattr(stripe.billing_portal.Session, "create", staticmethod(fake_create))

    url = await gateway.create_portal_session("cus_123")

    assert url == "https://billing.stripe.com/session/abc"
    assert captured["customer"] == "cus_123"
    assert captured["return_url"] == "https://app.example/billing"


async def should_upgrade_subscription_successfully(monkeypatch: pytest.MonkeyPatch) -> None:
    gateway = _enabled_stripe_settings(monkeypatch)
    modify_calls: dict[str, Any] = {}

    monkeypatch.setattr(
        stripe.Subscription,
        "retrieve",
        staticmethod(lambda sub_id: {"items": {"data": [{"id": "si_1"}]}}),
    )

    def fake_modify(sub_id: str, **kwargs: Any) -> Any:
        modify_calls["sub_id"] = sub_id
        modify_calls.update(kwargs)
        return {}

    monkeypatch.setattr(stripe.Subscription, "modify", staticmethod(fake_modify))

    await gateway.upgrade_subscription("sub_123", "quintessences_pro")

    assert modify_calls["sub_id"] == "sub_123"
    assert modify_calls["items"] == [{"id": "si_1", "price": "price_quintessences"}]
    assert modify_calls["metadata"] == {"plan_code": "quintessences_pro"}


async def should_reject_upgrade_when_subscription_has_ambiguous_items(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _enabled_stripe_settings(monkeypatch)
    monkeypatch.setattr(
        stripe.Subscription,
        "retrieve",
        staticmethod(lambda sub_id: {"items": {"data": []}}),
    )

    with pytest.raises(StripeBillingError, match="Abonnement Stripe ambigu"):
        await gateway.upgrade_subscription("sub_123", "quintessences_pro")


async def should_create_checkout_session_successfully(monkeypatch: pytest.MonkeyPatch) -> None:
    gateway = _enabled_stripe_settings(monkeypatch)
    captured: dict[str, Any] = {}

    def fake_create(**kwargs: Any) -> Any:
        captured.update(kwargs)
        return SimpleNamespace(url="https://checkout.stripe.com/session/xyz")

    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(fake_create))
    owner_id = uuid4()

    url = await gateway.create_checkout_session(
        plan_code="geosylva_pro", owner_type="account", owner_id=owner_id
    )

    assert url == "https://checkout.stripe.com/session/xyz"
    assert captured["line_items"] == [{"price": "price_geosylva", "quantity": 1}]
    assert captured["client_reference_id"] == str(owner_id)
    assert captured["metadata"]["plan_code"] == "geosylva_pro"


# ===========================================================================
# stripe_gateway.py — StripeWebhookProcessor
# ===========================================================================


def should_build_webhook_processor_with_session_and_settings() -> None:
    session = ScriptedSession()

    processor = StripeWebhookProcessor(session)  # type: ignore[arg-type]

    assert processor._session is session
    assert processor._settings is not None


def should_reject_webhook_when_stripe_is_disabled() -> None:
    processor = StripeWebhookProcessor.__new__(StripeWebhookProcessor)
    processor._settings = get_settings()

    with pytest.raises(StripeWebhookError, match="Webhook Stripe non configuré"):
        processor.parse_event(b"{}", None)


def should_reject_webhook_when_signature_is_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    from pydantic import SecretStr

    processor = StripeWebhookProcessor.__new__(StripeWebhookProcessor)
    processor._settings = get_settings()
    processor._settings.stripe_enabled = True
    processor._settings.stripe_webhook_secret = SecretStr("whsec_test")

    def fake_construct_event(payload: bytes, signature: str, secret: str) -> Any:
        raise stripe.SignatureVerificationError("signature invalide", signature)

    monkeypatch.setattr(stripe.Webhook, "construct_event", staticmethod(fake_construct_event))

    with pytest.raises(StripeWebhookError, match="Signature Stripe invalide"):
        processor.parse_event(b"{}", "sig_123")


def should_parse_webhook_event_successfully(monkeypatch: pytest.MonkeyPatch) -> None:
    from pydantic import SecretStr

    processor = StripeWebhookProcessor.__new__(StripeWebhookProcessor)
    processor._settings = get_settings()
    processor._settings.stripe_enabled = True
    processor._settings.stripe_webhook_secret = SecretStr("whsec_test")
    fake_event = stripe.Event.construct_from({"id": "evt_1", "type": "ping"}, "sk_test")

    monkeypatch.setattr(
        stripe.Webhook, "construct_event", staticmethod(lambda payload, sig, secret: fake_event)
    )

    event = processor.parse_event(b"{}", "sig_123")

    assert event.id == "evt_1"


def _webhook_processor(session: ScriptedSession) -> StripeWebhookProcessor:
    processor = StripeWebhookProcessor.__new__(StripeWebhookProcessor)
    processor._session = session  # type: ignore[assignment]
    processor._settings = get_settings()
    return processor


def _stripe_event(payload: dict[str, Any]) -> stripe.Event:
    return stripe.Event.construct_from(payload, "sk_test")


async def should_skip_already_processed_webhook_event() -> None:
    session = ScriptedSession(scalar_results=[uuid4()])
    processor = _webhook_processor(session)
    event = _stripe_event({"id": "evt_dup", "type": "ping"})

    handled = await processor.process(event)

    assert handled is False
    assert session.added == []


async def should_treat_duplicate_billing_event_insert_as_already_processed() -> None:
    session = ScriptedSession(scalar_results=[None])
    session.flush_side_effect = IntegrityError("insert", {}, Exception("duplicate"))
    processor = _webhook_processor(session)
    event = _stripe_event({"id": "evt_race", "type": "ping"})

    handled = await processor.process(event)

    assert handled is False
    assert session.rolled_back is True


async def should_process_unhandled_event_type_and_mark_it_processed() -> None:
    session = ScriptedSession(scalar_results=[None])
    processor = _webhook_processor(session)
    event = _stripe_event({"id": "evt_ping", "type": "ping"})

    handled = await processor.process(event)

    assert handled is True
    event_models = [obj for obj in session.added if hasattr(obj, "event_type")]
    assert event_models[0].status == "processed"
    assert event_models[0].processed_at is not None


async def should_ignore_checkout_completed_event_without_subscription_id() -> None:
    session = ScriptedSession(scalar_results=[None])
    processor = _webhook_processor(session)
    event = _stripe_event({"id": "evt_checkout", "type": "checkout.session.completed"})

    handled = await processor.process(event)

    assert handled is True
    # Aucun appel supplémentaire déclenché par _upsert_subscription.
    subscriptions = [obj for obj in session.added if hasattr(obj, "plan_id")]
    assert subscriptions == []


async def should_ignore_subscription_event_without_id() -> None:
    session = ScriptedSession(scalar_results=[None])
    processor = _webhook_processor(session)
    event = _stripe_event({"id": "", "type": "customer.subscription.updated"})

    handled = await processor.process(event)

    assert handled is True


async def should_ignore_payment_failed_event_when_subscription_field_is_not_a_string() -> None:
    session = ScriptedSession(scalar_results=[None])
    processor = _webhook_processor(session)
    event = _stripe_event(
        {"id": "evt_invoice", "type": "invoice.payment_failed", "subscription": {"nested": True}}
    )

    handled = await processor.process(event)

    assert handled is True
    assert session.executed_statements == []  # aucun UPDATE émis
    assert len(session.scalar_statements) == 1  # seul le SELECT de dédup a eu lieu


async def should_mark_subscription_past_due_on_payment_failed_event() -> None:
    session = ScriptedSession(scalar_results=[None], execute_results=[RecordingResult()])
    processor = _webhook_processor(session)
    event = _stripe_event(
        {"id": "evt_invoice_2", "type": "invoice.payment_failed", "subscription": "sub_42"}
    )

    handled = await processor.process(event)

    assert handled is True
    assert len(session.executed_statements) == 1


async def should_reject_checkout_completed_when_metadata_is_incomplete() -> None:
    session = ScriptedSession(scalar_results=[None])
    processor = _webhook_processor(session)
    event = _stripe_event(
        {
            "id": "evt_checkout_bad",
            "type": "checkout.session.completed",
            "subscription": "sub_1",
            "metadata": {},
        }
    )

    with pytest.raises(StripeWebhookError, match="incomplètes"):
        await processor.process(event)


async def should_reject_subscription_event_when_owner_id_is_not_a_uuid() -> None:
    session = ScriptedSession(scalar_results=[None])
    processor = _webhook_processor(session)
    event = _stripe_event(
        {
            "id": "sub_bad_owner",
            "type": "customer.subscription.updated",
            "metadata": {
                "owner_type": "account",
                "owner_id": "not-a-uuid",
                "plan_code": "geosylva_pro",
            },
        }
    )

    with pytest.raises(StripeWebhookError, match="Propriétaire Stripe invalide"):
        await processor.process(event)


async def should_reject_checkout_completed_when_plan_is_unknown() -> None:
    owner_id = uuid4()
    session = ScriptedSession(
        scalar_results=[None, None],  # dédup event, puis plan introuvable
    )
    processor = _webhook_processor(session)
    event = _stripe_event(
        {
            "id": "evt_checkout_unknown_plan",
            "type": "checkout.session.completed",
            "subscription": "sub_2",
            "metadata": {
                "owner_type": "account",
                "owner_id": str(owner_id),
                "plan_code": "plan-inconnu",
            },
        }
    )

    with pytest.raises(StripeWebhookError, match="Plan GSIE inconnu"):
        await processor.process(event)


async def should_create_subscription_and_entitlements_on_checkout_completed() -> None:
    owner_id = uuid4()
    plan = SimpleNamespace(id=uuid4())
    session = ScriptedSession(
        scalar_results=[
            None,  # dédup event
            plan,  # plan trouvé
            None,  # aucune souscription existante
        ],
        execute_results=[
            RecordingResult(),  # revoke entitlements existantes (ignoré)
            RecordingResult(all_items=["geosylva.pro"]),  # features
            RecordingResult(one_or_none=None),  # entitlement inexistante -> création
        ],
    )
    processor = _webhook_processor(session)
    event = _stripe_event(
        {
            "id": "evt_checkout_ok",
            "type": "checkout.session.completed",
            "subscription": "sub_ok",
            "customer": "cus_42",
            "status": "active",
            "cancel_at_period_end": False,
            "metadata": {
                "owner_type": "account",
                "owner_id": str(owner_id),
                "plan_code": "geosylva_pro",
            },
        }
    )

    handled = await processor.process(event)

    assert handled is True
    subscriptions = [obj for obj in session.added if hasattr(obj, "plan_id")]
    entitlements = [obj for obj in session.added if hasattr(obj, "feature_code")]
    assert subscriptions[0].external_subscription_id == "sub_ok"
    assert subscriptions[0].provider_customer_id == "cus_42"
    assert entitlements[0].status == "active"


async def should_update_existing_subscription_and_revoke_entitlements_on_deletion() -> None:
    owner_id = uuid4()
    plan = SimpleNamespace(id=uuid4())
    existing_subscription = SimpleNamespace(
        id=uuid4(),
        owner_type="account",
        account_id=owner_id,
        organisation_id=None,
        plan_id=uuid4(),
        provider="stripe",
        external_subscription_id="sub_del",
        provider_customer_id=None,
        status="active",
        cancel_at_period_end=False,
        updated_at=None,
    )
    existing_entitlement = SimpleNamespace(
        source_subscription_id=None, status="active", valid_until=None
    )
    session = ScriptedSession(
        scalar_results=[None, plan, existing_subscription],
        execute_results=[
            RecordingResult(),
            RecordingResult(all_items=["geosylva.pro"]),
            RecordingResult(one_or_none=existing_entitlement),
        ],
    )
    processor = _webhook_processor(session)
    event = _stripe_event(
        {
            "id": "sub_del",
            "type": "customer.subscription.deleted",
            "status": "canceled",
            "metadata": {
                "owner_type": "account",
                "owner_id": str(owner_id),
                "plan_code": "geosylva_pro",
            },
        }
    )

    handled = await processor.process(event)

    assert handled is True
    subscriptions = [obj for obj in session.added if hasattr(obj, "plan_id")]
    entitlements = [obj for obj in session.added if hasattr(obj, "feature_code")]
    assert subscriptions == []  # mise à jour en place, pas de création
    assert entitlements == []
    assert existing_subscription.status == "canceled"
    # Statut ni "active" ni "trialing" -> l'entitlement existante est révoquée.
    assert existing_entitlement.status == "revoked"


async def should_default_subscription_status_to_active_when_not_in_enum() -> None:
    """Un statut Stripe inconnu retombe sur ``active`` (comportement documenté)."""
    owner_id = uuid4()
    plan = SimpleNamespace(id=uuid4())
    session = ScriptedSession(
        scalar_results=[None, plan, None],
        execute_results=[
            RecordingResult(),
            RecordingResult(all_items=["geosylva.pro"]),
            RecordingResult(one_or_none=None),
        ],
    )
    processor = _webhook_processor(session)
    event = _stripe_event(
        {
            "id": "sub_unknown_status",
            "type": "customer.subscription.updated",
            "status": "not-a-known-status",
            "metadata": {
                "owner_type": "account",
                "owner_id": str(owner_id),
                "plan_code": "geosylva_pro",
            },
        }
    )

    handled = await processor.process(event)

    assert handled is True
    subscriptions = [obj for obj in session.added if hasattr(obj, "plan_id")]
    entitlements = [obj for obj in session.added if hasattr(obj, "feature_code")]
    assert subscriptions[0].status == "active"
    assert entitlements[0].status == "active"


# ===========================================================================
# router.py — dépendances et fonctions internes
# ===========================================================================


async def should_build_billing_service_from_default_db_dependency() -> None:
    session = ScriptedSession()

    service = await router_module.get_billing_service(session)  # type: ignore[arg-type]

    assert isinstance(service, BillingService)


async def should_build_billing_service_from_scoped_db_dependency() -> None:
    session = ScriptedSession()

    service = await router_module.get_scoped_billing_service(session)  # type: ignore[arg-type]

    assert isinstance(service, BillingService)


def should_reject_account_id_extraction_when_subject_is_not_a_uuid() -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        router_module._account_id({"sub": "not-a-uuid"})

    assert exc_info.value.status_code == 401


# ===========================================================================
# router.py — contrat HTTP (TestClient + dépendances/gateways monkeypatchés)
# ===========================================================================


def _authorization(account_id: UUID) -> dict[str, str]:
    token = create_access_token(subject=str(account_id), claims={"roles": ["user"]})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def billing_app(mock_lifespan: object) -> Any:
    del mock_lifespan
    from gsie_api.app import create_app

    return create_app()


@pytest.fixture
def billing_client(billing_app: Any) -> Any:
    with TestClient(billing_app) as client:
        yield client


def should_list_public_plans_over_http(billing_app: Any, billing_client: Any) -> None:
    service = AsyncMock()
    service.list_public_plans.return_value = [
        PlanRecord("free", "Gratuit", "geosylva", None, None, 0, ("basic",))
    ]
    billing_app.dependency_overrides[router_module.get_billing_service] = lambda: service

    response = billing_client.get("/api/v1/billing/plans")

    assert response.status_code == 200
    assert response.json()["plans"][0]["code"] == "free"


def should_reject_checkout_for_non_account_owner(billing_app: Any, billing_client: Any) -> None:
    account_id = uuid4()

    response = billing_client.post(
        "/api/v1/billing/checkout",
        json={"plan_code": "geosylva_pro", "owner_type": "organisation"},
        headers=_authorization(account_id),
    )

    assert response.status_code == 501


def should_create_checkout_session_over_http(billing_app: Any, billing_client: Any) -> None:
    account_id = uuid4()

    class FakeGateway:
        async def create_checkout_session(
            self, *, plan_code: str, owner_type: str, owner_id: Any
        ) -> str:
            return "https://checkout.stripe.com/abc"

    billing_app.dependency_overrides = billing_app.dependency_overrides
    import gsie_api.billing.router as rm

    original = rm.StripeBillingGateway
    rm.StripeBillingGateway = FakeGateway
    try:
        response = billing_client.post(
            "/api/v1/billing/checkout",
            json={"plan_code": "geosylva_pro", "owner_type": "account"},
            headers=_authorization(account_id),
        )
    finally:
        rm.StripeBillingGateway = original

    assert response.status_code == 200
    assert response.json()["checkout_url"] == "https://checkout.stripe.com/abc"


def should_reject_checkout_session_when_stripe_not_configured_over_http(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()

    class FailingGateway:
        async def create_checkout_session(self, **kwargs: Any) -> str:
            raise StripeNotConfiguredError("Stripe désactivé")

    import gsie_api.billing.router as rm

    original = rm.StripeBillingGateway
    rm.StripeBillingGateway = FailingGateway
    try:
        response = billing_client.post(
            "/api/v1/billing/checkout",
            json={"plan_code": "geosylva_pro", "owner_type": "account"},
            headers=_authorization(account_id),
        )
    finally:
        rm.StripeBillingGateway = original

    assert response.status_code == 503


def should_reject_billing_portal_when_organisation_header_is_invalid(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    session = ScriptedSession()

    async def fake_get_db_resource() -> Any:
        yield session

    billing_app.dependency_overrides[router_module.get_db_resource] = fake_get_db_resource  # type: ignore[misc]

    response = billing_client.post(
        "/api/v1/billing/portal",
        headers={**_authorization(account_id), "X-Organisation-Id": "not-a-uuid"},
    )

    assert response.status_code == 400


def should_reject_billing_portal_when_no_active_stripe_customer(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    session = ScriptedSession(execute_results=[RecordingResult(one_or_none=None)])

    async def fake_get_db_resource() -> Any:
        yield session

    billing_app.dependency_overrides[router_module.get_db_resource] = fake_get_db_resource  # type: ignore[misc]

    response = billing_client.post(
        "/api/v1/billing/portal",
        headers=_authorization(account_id),
    )

    assert response.status_code == 404


def should_create_billing_portal_session_over_http(billing_app: Any, billing_client: Any) -> None:
    account_id = uuid4()
    subscription = SimpleNamespace(provider_customer_id="cus_123")
    session = ScriptedSession(execute_results=[RecordingResult(one_or_none=subscription)])

    async def fake_get_db_resource() -> Any:
        yield session

    billing_app.dependency_overrides[router_module.get_db_resource] = fake_get_db_resource  # type: ignore[misc]

    class FakeGateway:
        async def create_portal_session(self, customer_id: str) -> str:
            assert customer_id == "cus_123"
            return "https://billing.stripe.com/portal/xyz"

    import gsie_api.billing.router as rm

    original = rm.StripeBillingGateway
    rm.StripeBillingGateway = FakeGateway
    try:
        response = billing_client.post(
            "/api/v1/billing/portal",
            headers=_authorization(account_id),
        )
    finally:
        rm.StripeBillingGateway = original

    assert response.status_code == 200
    assert response.json()["checkout_url"] == "https://billing.stripe.com/portal/xyz"


def should_reject_billing_portal_when_stripe_not_configured_over_http(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    subscription = SimpleNamespace(provider_customer_id="cus_123")
    session = ScriptedSession(execute_results=[RecordingResult(one_or_none=subscription)])

    async def fake_get_db_resource() -> Any:
        yield session

    billing_app.dependency_overrides[router_module.get_db_resource] = fake_get_db_resource  # type: ignore[misc]

    class FailingGateway:
        async def create_portal_session(self, customer_id: str) -> str:
            raise StripeNotConfiguredError("Stripe désactivé")

    import gsie_api.billing.router as rm

    original = rm.StripeBillingGateway
    rm.StripeBillingGateway = FailingGateway
    try:
        response = billing_client.post(
            "/api/v1/billing/portal",
            headers=_authorization(account_id),
        )
    finally:
        rm.StripeBillingGateway = original

    assert response.status_code == 503


def should_reject_upgrade_when_no_active_individual_subscription(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    session = ScriptedSession(execute_results=[RecordingResult(one_or_none=None)])

    async def fake_get_db_resource() -> Any:
        yield session

    billing_app.dependency_overrides[router_module.get_db_resource] = fake_get_db_resource  # type: ignore[misc]

    response = billing_client.post(
        "/api/v1/billing/upgrade",
        json={"target_plan_code": "quintessences_pro"},
        headers=_authorization(account_id),
    )

    assert response.status_code == 404


def should_reject_upgrade_to_unsupported_plan(billing_app: Any, billing_client: Any) -> None:
    account_id = uuid4()
    subscription = SimpleNamespace(external_subscription_id="sub_123")
    session = ScriptedSession(execute_results=[RecordingResult(one_or_none=subscription)])

    async def fake_get_db_resource() -> Any:
        yield session

    billing_app.dependency_overrides[router_module.get_db_resource] = fake_get_db_resource  # type: ignore[misc]

    response = billing_client.post(
        "/api/v1/billing/upgrade",
        json={"target_plan_code": "plan-non-supporte"},
        headers=_authorization(account_id),
    )

    assert response.status_code == 400


def should_upgrade_subscription_successfully_over_http(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    subscription = SimpleNamespace(external_subscription_id="sub_123")
    session = ScriptedSession(execute_results=[RecordingResult(one_or_none=subscription)])

    async def fake_get_db_resource() -> Any:
        yield session

    billing_app.dependency_overrides[router_module.get_db_resource] = fake_get_db_resource  # type: ignore[misc]

    class FakeGateway:
        async def upgrade_subscription(self, subscription_id: str, target_plan_code: str) -> None:
            assert subscription_id == "sub_123"
            assert target_plan_code == "quintessences_pro"

    import gsie_api.billing.router as rm

    original = rm.StripeBillingGateway
    rm.StripeBillingGateway = FakeGateway
    try:
        response = billing_client.post(
            "/api/v1/billing/upgrade",
            json={"target_plan_code": "quintessences_pro"},
            headers=_authorization(account_id),
        )
    finally:
        rm.StripeBillingGateway = original

    assert response.status_code == 200
    assert response.json()["accepted"] is True


def should_reject_upgrade_when_stripe_billing_error_over_http(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    subscription = SimpleNamespace(external_subscription_id="sub_123")
    session = ScriptedSession(execute_results=[RecordingResult(one_or_none=subscription)])

    async def fake_get_db_resource() -> Any:
        yield session

    billing_app.dependency_overrides[router_module.get_db_resource] = fake_get_db_resource  # type: ignore[misc]

    class FailingGateway:
        async def upgrade_subscription(self, subscription_id: str, target_plan_code: str) -> None:
            raise StripeBillingError("Abonnement Stripe ambigu")

    import gsie_api.billing.router as rm

    original = rm.StripeBillingGateway
    rm.StripeBillingGateway = FailingGateway
    try:
        response = billing_client.post(
            "/api/v1/billing/upgrade",
            json={"target_plan_code": "quintessences_pro"},
            headers=_authorization(account_id),
        )
    finally:
        rm.StripeBillingGateway = original

    assert response.status_code == 503


def _fake_db_override(billing_app: Any, session: ScriptedSession) -> None:
    async def fake_get_db() -> Any:
        yield session

    billing_app.dependency_overrides[router_module.get_db] = fake_get_db  # type: ignore[misc]


def should_validate_google_play_purchase_successfully_over_http(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    plan = SimpleNamespace(id=uuid4(), code="geosylva_pro")
    # L'endpoint construit une vraie ``SqlAlchemyBillingRepository`` sur la
    # session (pas de dépendance injectable pour le service ici) : on script
    # donc la séquence réelle de ``apply_verified_purchase``.
    session = ScriptedSession(
        execute_results=[
            RecordingResult(one_or_none=plan),
            RecordingResult(one_or_none=None),
            RecordingResult(),
            RecordingResult(all_items=["geosylva.pro"]),
            RecordingResult(one_or_none=None),
        ]
    )
    _fake_db_override(billing_app, session)

    purchase = VerifiedPurchase(
        "google_play", "order_1", "product_1", "geosylva_pro", "active", None
    )

    class FakeGateway:
        async def verify_subscription(self, purchase_token: str) -> VerifiedPurchase:
            return purchase

    import gsie_api.billing.router as rm

    original = rm.GooglePlayPurchaseGateway
    rm.GooglePlayPurchaseGateway = FakeGateway
    try:
        response = billing_client.post(
            "/api/v1/billing/purchases/google-play",
            json={"purchase_token": "token-abc"},
            headers=_authorization(account_id),
        )
    finally:
        rm.GooglePlayPurchaseGateway = original

    assert response.status_code == 200
    assert response.json()["plan_code"] == "geosylva_pro"
    assert session.committed is True


def should_reject_google_play_purchase_when_store_not_configured_over_http(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    session = ScriptedSession()
    _fake_db_override(billing_app, session)

    class FailingGateway:
        async def verify_subscription(self, purchase_token: str) -> VerifiedPurchase:
            raise StoreNotConfiguredError("Google Play désactivé")

    import gsie_api.billing.router as rm

    original = rm.GooglePlayPurchaseGateway
    rm.GooglePlayPurchaseGateway = FailingGateway
    try:
        response = billing_client.post(
            "/api/v1/billing/purchases/google-play",
            json={"purchase_token": "token-abc"},
            headers=_authorization(account_id),
        )
    finally:
        rm.GooglePlayPurchaseGateway = original

    assert response.status_code == 503
    assert session.rolled_back is True


def should_reject_google_play_purchase_when_token_invalid_over_http(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    session = ScriptedSession()
    _fake_db_override(billing_app, session)

    class FailingGateway:
        async def verify_subscription(self, purchase_token: str) -> VerifiedPurchase:
            raise StorePurchaseInvalidError("Jeton invalide")

    import gsie_api.billing.router as rm

    original = rm.GooglePlayPurchaseGateway
    rm.GooglePlayPurchaseGateway = FailingGateway
    try:
        response = billing_client.post(
            "/api/v1/billing/purchases/google-play",
            json={"purchase_token": "token-abc"},
            headers=_authorization(account_id),
        )
    finally:
        rm.GooglePlayPurchaseGateway = original

    assert response.status_code == 400
    assert session.rolled_back is True
    assert session.executed_statements == []


def should_validate_apple_purchase_successfully_over_http(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    plan = SimpleNamespace(id=uuid4(), code="quintessences_pro")
    session = ScriptedSession(
        execute_results=[
            RecordingResult(one_or_none=plan),
            RecordingResult(one_or_none=None),
            RecordingResult(),
            RecordingResult(all_items=["quintessences.pro"]),
            RecordingResult(one_or_none=None),
        ]
    )
    _fake_db_override(billing_app, session)

    purchase = VerifiedPurchase("apple", "txn_1", "product_1", "quintessences_pro", "active", None)

    class FakeGateway:
        async def verify_subscription(self, original_transaction_id: str) -> VerifiedPurchase:
            return purchase

    import gsie_api.billing.router as rm

    original = rm.ApplePurchaseGateway
    rm.ApplePurchaseGateway = FakeGateway
    try:
        response = billing_client.post(
            "/api/v1/billing/purchases/apple",
            json={"purchase_token": "txn-abc"},
            headers=_authorization(account_id),
        )
    finally:
        rm.ApplePurchaseGateway = original

    assert response.status_code == 200
    assert response.json()["plan_code"] == "quintessences_pro"


def should_reject_apple_purchase_when_store_not_configured_over_http(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    session = ScriptedSession()
    _fake_db_override(billing_app, session)

    class FailingGateway:
        async def verify_subscription(self, original_transaction_id: str) -> VerifiedPurchase:
            raise StoreNotConfiguredError("Apple désactivé")

    import gsie_api.billing.router as rm

    original = rm.ApplePurchaseGateway
    rm.ApplePurchaseGateway = FailingGateway
    try:
        response = billing_client.post(
            "/api/v1/billing/purchases/apple",
            json={"purchase_token": "txn-abc"},
            headers=_authorization(account_id),
        )
    finally:
        rm.ApplePurchaseGateway = original

    assert response.status_code == 503


def should_reject_apple_purchase_when_token_invalid_over_http(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    session = ScriptedSession()
    _fake_db_override(billing_app, session)

    class FailingGateway:
        async def verify_subscription(self, original_transaction_id: str) -> VerifiedPurchase:
            raise StorePurchaseInvalidError("Transaction invalide")

    import gsie_api.billing.router as rm

    original = rm.ApplePurchaseGateway
    rm.ApplePurchaseGateway = FailingGateway
    try:
        response = billing_client.post(
            "/api/v1/billing/purchases/apple",
            json={"purchase_token": "txn-abc"},
            headers=_authorization(account_id),
        )
    finally:
        rm.ApplePurchaseGateway = original

    assert response.status_code == 400


def should_reject_stripe_webhook_when_invalid(billing_app: Any, billing_client: Any) -> None:
    session = ScriptedSession()
    _fake_db_override(billing_app, session)

    class FailingProcessor:
        def __init__(self, session: Any) -> None:
            pass

        def parse_event(self, payload: bytes, signature: str | None) -> Any:
            raise StripeWebhookError("Signature Stripe invalide")

    import gsie_api.billing.router as rm

    original = rm.StripeWebhookProcessor
    rm.StripeWebhookProcessor = FailingProcessor
    try:
        response = billing_client.post(
            "/api/v1/billing/webhooks/stripe",
            content=b"{}",
            headers={"Stripe-Signature": "sig_bad"},
        )
    finally:
        rm.StripeWebhookProcessor = original

    assert response.status_code == 400
    assert session.rolled_back is True


def should_accept_stripe_webhook_when_valid(billing_app: Any, billing_client: Any) -> None:
    session = ScriptedSession()
    _fake_db_override(billing_app, session)

    class WorkingProcessor:
        def __init__(self, session: Any) -> None:
            self.session = session

        def parse_event(self, payload: bytes, signature: str | None) -> Any:
            return "fake-event"

        async def process(self, event: Any) -> bool:
            assert event == "fake-event"
            return True

    import gsie_api.billing.router as rm

    original = rm.StripeWebhookProcessor
    rm.StripeWebhookProcessor = WorkingProcessor
    try:
        response = billing_client.post(
            "/api/v1/billing/webhooks/stripe",
            content=b"{}",
            headers={"Stripe-Signature": "sig_ok"},
        )
    finally:
        rm.StripeWebhookProcessor = original

    assert response.status_code == 204
    assert session.committed is True


def should_reject_billing_context_when_organisation_header_is_invalid(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    service = AsyncMock()
    billing_app.dependency_overrides[router_module.get_scoped_billing_service] = lambda: service

    response = billing_client.get(
        "/api/v1/billing/context",
        headers={**_authorization(account_id), "X-Organisation-Id": "not-a-uuid"},
    )

    assert response.status_code == 400


def should_return_billing_context_successfully_over_http(
    billing_app: Any, billing_client: Any
) -> None:
    account_id = uuid4()
    organisation_id = uuid4()
    service = AsyncMock()
    service.get_effective_entitlements.return_value = [
        EntitlementRecord("account.access", "account", account_id, "active", None)
    ]
    billing_app.dependency_overrides[router_module.get_scoped_billing_service] = lambda: service

    response = billing_client.get(
        "/api/v1/billing/context",
        headers={**_authorization(account_id), "X-Organisation-Id": str(organisation_id)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["features"] == ["account.access"]
    assert body["organisation_id"] == str(organisation_id)
    service.get_effective_entitlements.assert_awaited_once_with(account_id, organisation_id)

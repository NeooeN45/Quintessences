"""Couverture des branches de sécurité du socle d'identité DEC-000044."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.exc import IntegrityError

from gsie_api.app import create_app
from gsie_api.auth import google_nonces, identity_router
from gsie_api.auth.account_lifecycle import (
    AccountProfile,
    ActionCodeDelivery,
    EmailAlreadyUsedError,
    EmailChangeDelivery,
    InvalidActionCodeError,
    InvalidCurrentPasswordError,
    InvalidEmailChangeCodeError,
)
from gsie_api.auth.google_identity import (
    GoogleTokenVerifier,
    InvalidGoogleTokenError,
    _verify_with_google_library,
)
from gsie_api.auth.google_nonces import (
    MemoryGoogleNonceStore,
    RedisGoogleNonceStore,
    get_google_nonce_store,
)
from gsie_api.auth.identity import (
    AccountAlreadyExistsError,
    AuthenticatedAccount,
    GoogleIdentity,
    IdentityService,
    InvalidCredentialsError,
    LocalCredentialRecord,
    PasswordService,
    ProviderAlreadyLinkedError,
    ProviderNotConfiguredError,
)
from gsie_api.auth.identity_router import (
    get_account_lifecycle_service,
    get_identity_service,
    get_lockout_service,
    get_mfa_service,
    get_onboarding_billing_service,
    get_password_strength_service,
    get_personal_organisation_service,
    get_session_service,
)
from gsie_api.auth.lockout import AccountLockedError
from gsie_api.auth.mfa import (
    InvalidRecoveryCodeError,
    MfaAlreadyEnabledError,
    MfaNotEnabledError,
    MfaSetupResult,
)
from gsie_api.auth.oidc_generic import InvalidOidcTokenError
from gsie_api.auth.oidc_nonces import get_oidc_nonce_store
from gsie_api.auth.password_strength import (
    CompromisedPasswordError,
    PasswordStrengthReport,
    WeakPasswordError,
)
from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore, get_refresh_token_store
from gsie_api.auth.repository import SqlAlchemyIdentityRepository
from gsie_api.auth.sessions import SessionInfo, SessionService
from gsie_api.auth.transactional_email import get_transactional_email_sender
from gsie_api.billing.service import BillingService
from gsie_api.core.auth import (
    create_access_token,
    create_mfa_challenge_token,
    create_mfa_setup_token,
)
from gsie_api.infrastructure.database import get_db
from gsie_api.infrastructure.models.accounts import (
    IdentityActionTokenModel,
    IdentityProviderLinkModel,
    LocalCredentialModel,
    UserAccountModel,
)
from gsie_api.organisations.service import OrganisationService

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping


def _integrity_error() -> IntegrityError:
    return IntegrityError("INSERT", {}, Exception("unicité"))


def _result(
    *,
    first: object | None = None,
    scalar: object | None = None,
    scalars: tuple[object, ...] = (),
) -> MagicMock:
    result = MagicMock()
    result.first.return_value = first
    result.scalar_one_or_none.return_value = scalar
    result.scalars.return_value.all.return_value = list(scalars)
    return result


def _session() -> MagicMock:
    session = MagicMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.get = AsyncMock()
    return session


def _identity() -> GoogleIdentity:
    return GoogleIdentity(
        issuer="https://accounts.google.com",
        subject="sujet-google-stable",
        email="forestier@example.fr",
        display_name="Forestier",
    )


@pytest.fixture
def client_identite(mock_lifespan: object) -> Generator[TestClient, None, None]:
    del mock_lifespan
    app = create_app()
    refresh_store = MemoryRefreshTokenStore()
    nonce_store = MemoryGoogleNonceStore()
    app.dependency_overrides[get_refresh_token_store] = lambda: refresh_store
    app.dependency_overrides[get_google_nonce_store] = lambda: nonce_store
    app.dependency_overrides[get_identity_service] = lambda: AsyncMock()
    app.dependency_overrides[get_session_service] = lambda: AsyncMock()
    mfa_service = AsyncMock()
    mfa_service.is_enabled = AsyncMock(return_value=False)
    app.dependency_overrides[get_mfa_service] = lambda: mfa_service
    app.dependency_overrides[get_personal_organisation_service] = lambda: AsyncMock()
    app.dependency_overrides[get_onboarding_billing_service] = lambda: AsyncMock()
    db_session = MagicMock()
    db_session.execute = AsyncMock()
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        yield client


def _nonce(client: TestClient) -> str:
    response = client.post("/api/v1/auth/google/nonce")
    assert response.status_code == 201
    return str(response.json()["nonce"])


async def should_cover_password_rehash_and_invalid_hash_paths() -> None:
    passwords = PasswordService()
    assert passwords.needs_rehash("hash-invalide") is False

    account = AuthenticatedAccount(uuid4(), ("user",), "local")
    record = LocalCredentialRecord(account, uuid4(), "ancien-hash")
    repository = AsyncMock()
    repository.find_local_credentials = AsyncMock(return_value=record)
    repository.update_password_hash = AsyncMock()
    repository.mark_authenticated = AsyncMock()
    password_service = MagicMock(spec=PasswordService)
    password_service.verify.return_value = True
    password_service.needs_rehash.return_value = True
    password_service.hash.return_value = "nouveau-hash"
    service = IdentityService(repository, password_service)

    authenticated = await service.authenticate_local("forestier@example.fr", "mot-de-passe-long")

    assert authenticated == account
    repository.update_password_hash.assert_awaited_once_with(
        record.identity_link_id, "nouveau-hash"
    )


async def should_reject_inactive_google_account_and_unconfigured_verifier() -> None:
    identity = _identity()
    verifier = AsyncMock()
    verifier.is_configured = True
    verifier.verify = AsyncMock(return_value=identity)
    repository = AsyncMock()
    repository.find_provider_account = AsyncMock(
        return_value=AuthenticatedAccount(uuid4(), ("user",), "google", is_active=False)
    )
    service = IdentityService(repository, PasswordService(), verifier)

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate_google("jeton", "nonce")

    for absent in (None, SimpleNamespace(is_configured=False)):
        service = IdentityService(repository, PasswordService(), absent)  # type: ignore[arg-type]
        with pytest.raises(ProviderNotConfiguredError):
            await service.authenticate_google("jeton", "nonce")


async def should_handle_existing_google_link_for_same_or_other_account() -> None:
    identity = _identity()
    verifier = AsyncMock()
    verifier.is_configured = True
    verifier.verify = AsyncMock(return_value=identity)
    repository = AsyncMock()
    existing = AuthenticatedAccount(uuid4(), ("user",), "google")
    repository.find_provider_account = AsyncMock(return_value=existing)
    service = IdentityService(repository, PasswordService(), verifier)

    assert await service.link_google(existing.account_id, "jeton", "nonce") == existing
    with pytest.raises(ProviderAlreadyLinkedError):
        await service.link_google(uuid4(), "jeton", "nonce")


async def should_use_official_google_verifier_without_blocking_event_loop() -> None:
    claims = {"sub": "sujet"}
    with patch(
        "gsie_api.auth.google_identity.google_id_token.verify_oauth2_token",
        return_value=claims,
    ) as verify:
        assert await _verify_with_google_library("jeton", "audience") == claims
    assert verify.call_args.args[0] == "jeton"
    assert verify.call_args.args[2] == "audience"


async def should_try_all_google_audiences_and_reject_unknown_issuer() -> None:
    calls: list[str] = []

    async def verify_token(token: str, audience: str) -> Mapping[str, object]:
        del token
        calls.append(audience)
        if audience == "client-1":
            raise ValueError("mauvaise audience")
        return {
            "iss": "https://accounts.google.com",
            "sub": "sujet",
            "email": "forestier@example.fr",
            "email_verified": True,
            "nonce": "nonce-attendu",
        }

    verifier = GoogleTokenVerifier(("client-1", "client-2", "  "), verify_token)
    await verifier.verify("jeton", "nonce-attendu")
    assert calls == ["client-1", "client-2"]

    async def always_invalid(token: str, audience: str) -> Mapping[str, object]:
        del token, audience
        raise ValueError("invalide")

    with pytest.raises(InvalidGoogleTokenError, match="Jeton Google invalide"):
        await GoogleTokenVerifier(("client",), always_invalid).verify("jeton", "nonce")

    with pytest.raises(InvalidGoogleTokenError, match="Émetteur"):
        verifier._identity_from_claims(  # noqa: SLF001 - branche de contrat ciblée
            {
                "iss": "https://fournisseur.example",
                "sub": "sujet",
                "email": "forestier@example.fr",
                "email_verified": True,
                "nonce": "nonce",
            },
            "nonce",
        )


async def should_cover_memory_nonce_expiry_and_close() -> None:
    store = MemoryGoogleNonceStore(ttl_seconds=1)
    assert store.ttl_seconds == 1
    store._nonces["expire"] = 0  # noqa: SLF001 - horloge déterministe du test
    await store.create()
    assert "expire" not in store._nonces  # noqa: SLF001
    await store.close()
    assert store._nonces == {}  # noqa: SLF001


async def should_cover_redis_nonce_lifecycle() -> None:
    client = AsyncMock()
    client.set = AsyncMock(side_effect=[False, True])
    client.getdel = AsyncMock(side_effect=["active", None])
    client.aclose = AsyncMock()
    settings = SimpleNamespace(redis_socket_timeout=1.0, redis_connect_timeout=1.0)
    with (
        patch("gsie_api.auth.google_nonces.get_settings", return_value=settings),
        patch("gsie_api.auth.google_nonces.redis.from_url", return_value=client),
        patch("gsie_api.auth.google_nonces.secrets.token_urlsafe", side_effect=["a", "b"]),
    ):
        store = RedisGoogleNonceStore("redis://nonce", ttl_seconds=42)
        assert store.ttl_seconds == 42
        assert await store.create() == "b"
        assert await store.consume("b") is True
        assert await store.consume("absent") is False
        await store.close()
    client.aclose.assert_awaited_once()


async def should_refuse_redis_nonce_after_five_collisions() -> None:
    client = AsyncMock()
    client.set = AsyncMock(return_value=False)
    settings = SimpleNamespace(redis_socket_timeout=1.0, redis_connect_timeout=1.0)
    with (
        patch("gsie_api.auth.google_nonces.get_settings", return_value=settings),
        patch("gsie_api.auth.google_nonces.redis.from_url", return_value=client),
    ):
        store = RedisGoogleNonceStore("redis://nonce")
        with pytest.raises(RuntimeError, match="nonce Google unique"):
            await store.create()


async def should_build_and_close_configured_nonce_stores() -> None:
    get_google_nonce_store.cache_clear()
    memory_settings = SimpleNamespace(
        google_nonce_storage_url="memory://",
        refresh_token_storage_url="redis://refresh",
        google_nonce_expire_seconds=12,
    )
    with patch("gsie_api.auth.google_nonces.get_settings", return_value=memory_settings):
        store = get_google_nonce_store()
        assert isinstance(store, MemoryGoogleNonceStore)
        await google_nonces.close_google_nonce_store()

    redis_settings = SimpleNamespace(
        google_nonce_storage_url=None,
        refresh_token_storage_url="redis://refresh",
        google_nonce_expire_seconds=15,
    )
    redis_store = AsyncMock()
    with (
        patch("gsie_api.auth.google_nonces.get_settings", return_value=redis_settings),
        patch(
            "gsie_api.auth.google_nonces.RedisGoogleNonceStore",
            return_value=redis_store,
        ),
    ):
        assert get_google_nonce_store() is redis_store
        await google_nonces.close_google_nonce_store()
    redis_store.close.assert_awaited_once()


async def should_construct_default_identity_dependencies() -> None:
    session = _session()
    with patch(
        "gsie_api.auth.identity_router._settings.google_oauth_client_ids",
        ["client-web"],
    ):
        from gsie_api.auth import identity_router

        identity_router.get_password_service.cache_clear()
        identity_router.get_google_token_verifier.cache_clear()
        assert isinstance(identity_router.get_password_service(), PasswordService)
        assert identity_router.get_google_token_verifier().is_configured is True
        service = await get_identity_service(session)
        assert isinstance(service, IdentityService)


def should_cover_local_registration_http_errors(client_identite: TestClient) -> None:
    from gsie_api.auth import identity_router

    with patch.object(identity_router._settings, "auth_local_registration_enabled", False):
        response = client_identite.post(
            "/api/v1/auth/register",
            json={"email": "forestier@example.fr", "password": "mot-de-passe-long"},
        )
    assert response.status_code == 404

    service = AsyncMock()
    service.register_local = AsyncMock(side_effect=AccountAlreadyExistsError)
    client_identite.app.dependency_overrides[get_identity_service] = lambda: service
    response = client_identite.post(
        "/api/v1/auth/register",
        json={"email": "forestier@example.fr", "password": "mot-de-passe-long"},
    )
    assert response.status_code == 409


def should_cover_successful_local_login(client_identite: TestClient) -> None:
    account = AuthenticatedAccount(uuid4(), ("user",), "local")
    service = AsyncMock()
    service.authenticate_local = AsyncMock(return_value=account)
    client_identite.app.dependency_overrides[get_identity_service] = lambda: service
    response = client_identite.post(
        "/api/v1/auth/login/password",
        json={"email": "forestier@example.fr", "password": "mot-de-passe-long"},
    )
    assert response.status_code == 200


def should_require_mfa_setup_when_admin_account_has_no_second_factor(
    client_identite: TestClient,
) -> None:
    """Le rôle admin sans MFA ne reçoit jamais de token complet (ROADMAP —
    MFA administrateur). Il reçoit un jeton restreint utilisable uniquement
    sur /mfa/setup et /mfa/verify — jamais bloqué, jamais de token complet
    tant que le second facteur n'est pas actif."""
    account = AuthenticatedAccount(uuid4(), ("admin",), "local")
    service = AsyncMock()
    service.authenticate_local = AsyncMock(return_value=account)
    client_identite.app.dependency_overrides[get_identity_service] = lambda: service
    # mfa_service.is_enabled=False par défaut dans client_identite (ligne 136)

    response = client_identite.post(
        "/api/v1/auth/login/password",
        json={"email": "admin@example.fr", "password": "mot-de-passe-long"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mfa_setup_required"] is True
    assert "setup_token" in body
    assert "access_token" not in body


def should_issue_full_tokens_when_admin_account_already_has_mfa(
    client_identite: TestClient,
) -> None:
    """Témoin : un admin AVEC MFA actif suit le flux MFA normal existant
    (challenge puis /login/mfa) plutôt que le bootstrap — pas de régression
    sur le cas déjà couvert par ailleurs."""
    account = AuthenticatedAccount(uuid4(), ("admin",), "local")
    service = AsyncMock()
    service.authenticate_local = AsyncMock(return_value=account)
    client_identite.app.dependency_overrides[get_identity_service] = lambda: service
    mfa_service = AsyncMock()
    mfa_service.is_enabled = AsyncMock(return_value=True)
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service

    response = client_identite.post(
        "/api/v1/auth/login/password",
        json={"email": "admin@example.fr", "password": "mot-de-passe-long"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body.get("mfa_required") is True
    assert "challenge_token" in body
    assert "mfa_setup_required" not in body


def should_accept_mfa_bootstrap_token_on_setup_and_verify_endpoints(
    client_identite: TestClient,
) -> None:
    """Le jeton restreint émis par _issue_tokens pour un admin sans MFA doit
    fonctionner sur /mfa/setup et /mfa/verify — c'est tout son intérêt : sans
    ça, un admin sans MFA serait définitivement bloqué (pas de régression sur
    le bootstrap lui-même)."""
    account_id = uuid4()
    setup_token = create_mfa_setup_token(subject=str(account_id))
    headers = {"Authorization": f"Bearer {setup_token}"}

    mfa_service = AsyncMock()
    mfa_service.setup = AsyncMock(
        return_value=MfaSetupResult(
            secret="SECRET234",
            otpauth_uri="otpauth://totp/Quintessences:admin?secret=SECRET234",
            recovery_codes=("code-1", "code-2"),
        )
    )
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service

    setup_response = client_identite.post("/api/v1/auth/mfa/setup", headers=headers)
    assert setup_response.status_code == 201
    mfa_service.setup.assert_awaited_once_with(account_id)

    mfa_service.verify_totp = AsyncMock(return_value=True)
    verify_response = client_identite.post(
        "/api/v1/auth/mfa/verify",
        headers=headers,
        json={"code": "123456", "is_recovery_code": False},
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["enabled"] is True


def should_reject_mfa_bootstrap_token_on_unrelated_protected_route(
    client_identite: TestClient,
) -> None:
    """Le jeton restreint ne doit ouvrir AUCUNE autre route protégée — c'est
    la garantie centrale de l'obligation MFA admin. /me exige toujours
    get_current_user (type=access strict)."""
    setup_token = create_mfa_setup_token(subject=str(uuid4()))

    response = client_identite.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {setup_token}"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "error",
    [ProviderNotConfiguredError(), InvalidGoogleTokenError(), InvalidCredentialsError()],
)
def should_map_google_login_errors(client_identite: TestClient, error: Exception) -> None:
    service = AsyncMock()
    service.authenticate_google = AsyncMock(side_effect=error)
    client_identite.app.dependency_overrides[get_identity_service] = lambda: service
    response = client_identite.post(
        "/api/v1/auth/login/google",
        json={"id_token": "jeton-google", "nonce": _nonce(client_identite)},
    )
    assert response.status_code == (503 if isinstance(error, ProviderNotConfiguredError) else 401)


def should_reject_google_link_with_non_uuid_subject(client_identite: TestClient) -> None:
    token = create_access_token(subject="pas-un-uuid", claims={"roles": ["user"]})
    response = client_identite.post(
        "/api/v1/auth/link/google",
        headers={"Authorization": f"Bearer {token}"},
        json={"id_token": "jeton-google", "nonce": "n" * 32},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Session invalide"


@pytest.mark.parametrize(
    "error",
    [ProviderAlreadyLinkedError(), ProviderNotConfiguredError(), InvalidGoogleTokenError()],
)
def should_map_google_link_errors(client_identite: TestClient, error: Exception) -> None:
    account_id = uuid4()
    service = AsyncMock()
    service.link_google = AsyncMock(side_effect=error)
    client_identite.app.dependency_overrides[get_identity_service] = lambda: service
    token = create_access_token(subject=str(account_id), claims={"roles": ["user"]})
    response = client_identite.post(
        "/api/v1/auth/link/google",
        headers={"Authorization": f"Bearer {token}"},
        json={"id_token": "jeton-google", "nonce": _nonce(client_identite)},
    )
    expected = 409 if isinstance(error, ProviderAlreadyLinkedError) else 503
    if isinstance(error, InvalidGoogleTokenError):
        expected = 401
    assert response.status_code == expected


async def should_cover_local_repository_paths() -> None:
    session = _session()
    session.execute.return_value = _result(scalar=None)
    repository = SqlAlchemyIdentityRepository(session)
    assert (await repository.create_local_account("a@example.fr", "hash", None)).provider == (
        "local"
    )

    duplicate_session = _session()
    duplicate_session.execute.return_value = _result(scalar=uuid4())
    with pytest.raises(AccountAlreadyExistsError):
        await SqlAlchemyIdentityRepository(duplicate_session).create_local_account(
            "a@example.fr", "hash", None
        )

    conflict_session = _session()
    conflict_session.execute.return_value = _result(scalar=None)
    conflict_session.flush = AsyncMock(side_effect=[None, _integrity_error()])
    with pytest.raises(AccountAlreadyExistsError):
        await SqlAlchemyIdentityRepository(conflict_session).create_local_account(
            "a@example.fr", "hash", None
        )


async def should_cover_local_repository_reads_and_updates() -> None:
    account_id, link_id = uuid4(), uuid4()
    account = UserAccountModel(id=account_id, status="active")
    link = IdentityProviderLinkModel(
        id=link_id,
        account_id=account_id,
        provider="local",
        issuer="quintessences",
        subject="a@example.fr",
    )
    credential = LocalCredentialModel(identity_link_id=link_id, password_hash="hash")

    session = _session()
    session.execute = AsyncMock(
        side_effect=[
            _result(first=None),
            _result(first=(account, link, credential)),
            _result(scalars=("user",)),
        ]
    )
    repository = SqlAlchemyIdentityRepository(session)
    assert await repository.find_local_credentials("absent@example.fr") is None
    found = await repository.find_local_credentials("a@example.fr")
    assert found is not None and found.password_hash == "hash"

    session.get = AsyncMock(side_effect=[None, credential, None, link])
    with pytest.raises(InvalidCredentialsError):
        await repository.update_password_hash(uuid4(), "nouveau")
    await repository.update_password_hash(link_id, "nouveau")
    assert credential.password_hash == "nouveau"
    await repository.mark_authenticated(uuid4())
    await repository.mark_authenticated(link_id)
    assert link.last_authenticated_at is not None


async def should_cover_google_repository_paths() -> None:
    account_id, link_id = uuid4(), uuid4()
    account = UserAccountModel(id=account_id, status="active")
    link = IdentityProviderLinkModel(
        id=link_id,
        account_id=account_id,
        provider="google",
        issuer="https://accounts.google.com",
        subject="sujet",
    )

    session = _session()
    session.execute = AsyncMock(
        side_effect=[
            _result(first=None),
            _result(first=(account, link)),
            _result(scalars=("user",)),
        ]
    )
    repository = SqlAlchemyIdentityRepository(session)
    assert await repository.find_provider_account("google", link.issuer, link.subject) is None
    found = await repository.find_provider_account("google", link.issuer, link.subject)
    assert found is not None and found.account_id == account_id

    for scalar, expected in ((None, False), (account_id, True)):
        session.execute = AsyncMock(return_value=_result(scalar=scalar))
        assert await repository.has_account_with_verified_email("a@example.fr") is expected

    session.flush = AsyncMock()
    assert (await repository.create_google_account(_identity())).provider == "google"
    session.flush = AsyncMock(side_effect=[None, _integrity_error()])
    with pytest.raises(ProviderAlreadyLinkedError):
        await repository.create_google_account(_identity())


async def should_cover_google_repository_link_paths() -> None:
    identity = _identity()
    repository = SqlAlchemyIdentityRepository(_session())
    repository._session.get = AsyncMock(return_value=None)  # noqa: SLF001
    with pytest.raises(InvalidCredentialsError):
        await repository.link_google_identity(uuid4(), identity)

    account_id = uuid4()
    account = UserAccountModel(id=account_id, status="active")
    repository._session.get = AsyncMock(return_value=account)  # noqa: SLF001
    repository._session.execute = AsyncMock(return_value=_result(scalars=("user",)))  # noqa: SLF001
    linked = await repository.link_google_identity(account_id, identity)
    assert linked.provider == "google"

    repository._session.flush = AsyncMock(side_effect=_integrity_error())  # noqa: SLF001
    with pytest.raises(ProviderAlreadyLinkedError):
        await repository.link_google_identity(account_id, identity)

    account.status = "disabled"
    repository._session.flush = AsyncMock()  # noqa: SLF001
    with pytest.raises(InvalidCredentialsError):
        await repository.link_google_identity(account_id, identity)

    assert SqlAlchemyIdentityRepository._account(account, ("user",), "local").is_active is False


async def should_cover_account_profile_repository_paths() -> None:
    account_id = uuid4()
    account = UserAccountModel(id=account_id, status="active", display_name="Camille")
    local_link = IdentityProviderLinkModel(
        account_id=account_id,
        provider="local",
        issuer="quintessences",
        subject="forestier@example.fr",
        email_normalized="forestier@example.fr",
        email_verified=True,
    )
    google_link = IdentityProviderLinkModel(
        account_id=account_id,
        provider="google",
        issuer="https://accounts.google.com",
        subject="google-subject",
        email_normalized="google@example.fr",
        email_verified=True,
    )
    session = _session()
    session.get = AsyncMock(side_effect=[None, account, account])
    session.execute = AsyncMock(
        side_effect=[
            _result(scalars=(local_link, google_link)),
            _result(scalars=("user",)),
            _result(scalars=(google_link,)),
            _result(scalars=("user",)),
        ]
    )
    repository = SqlAlchemyIdentityRepository(session)

    assert await repository.get_profile(uuid4()) is None
    local_profile = await repository.get_profile(account_id)
    assert local_profile is not None
    assert local_profile.email == "forestier@example.fr"
    google_profile = await repository.get_profile(account_id)
    assert google_profile is not None
    assert google_profile.email == "google@example.fr"


async def should_cover_profile_update_and_local_lookup_repository_paths() -> None:
    account_id = uuid4()
    account = UserAccountModel(id=account_id, status="active")
    expected = AccountProfile(account_id, "Nouveau", None, False, (), ())
    session = _session()
    session.get = AsyncMock(side_effect=[None, account])
    session.execute = AsyncMock(return_value=_result(scalar=account_id))
    repository = SqlAlchemyIdentityRepository(session)
    repository.get_profile = AsyncMock(return_value=expected)  # type: ignore[method-assign]

    assert await repository.update_display_name(uuid4(), "Absent") is None
    assert await repository.update_display_name(account_id, "Nouveau") == expected
    assert account.display_name == "Nouveau"
    assert await repository.find_local_account_id("forestier@example.fr") == account_id


async def should_cover_action_code_repository_paths() -> None:
    account_id = uuid4()
    token_id = uuid4()
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    token = IdentityActionTokenModel(
        id=token_id,
        account_id=account_id,
        purpose="verify_email",
        code_hash="hash",
        expires_at=expires_at,
    )
    consumed = IdentityActionTokenModel(
        id=uuid4(),
        account_id=account_id,
        purpose="verify_email",
        code_hash="hash",
        expires_at=expires_at,
        consumed_at=datetime.now(UTC),
    )
    session = _session()
    repository = SqlAlchemyIdentityRepository(session)

    session.execute = AsyncMock(return_value=_result(scalar=None))
    assert (
        await repository.replace_action_code(
            account_id,
            "verify_email",
            "hash",
            expires_at,
        )
        is None
    )

    session.execute = AsyncMock(side_effect=[_result(scalar="forestier@example.fr"), _result()])
    assert (
        await repository.replace_action_code(
            account_id,
            "verify_email",
            "hash",
            expires_at,
        )
        == "forestier@example.fr"
    )
    session.add.assert_called_once()

    session.execute = AsyncMock(side_effect=[_result(scalar=None), _result(scalar=token)])
    assert await repository.get_active_action_code(account_id, "verify_email") is None
    action = await repository.get_active_action_code(account_id, "verify_email")
    assert action is not None and action.token_id == token_id

    session.get = AsyncMock(side_effect=[None, consumed, token])
    await repository.consume_action_code(uuid4())
    await repository.consume_action_code(consumed.id)
    await repository.consume_action_code(token_id)
    assert token.consumed_at is not None


async def should_cover_sensitive_account_mutations_repository_paths() -> None:
    account_id = uuid4()
    link_id = uuid4()
    credential = LocalCredentialModel(identity_link_id=link_id, password_hash="ancien")
    account = UserAccountModel(id=account_id, status="active", session_version=1)
    session = _session()
    repository = SqlAlchemyIdentityRepository(session)

    session.execute = AsyncMock(return_value=_result())
    await repository.mark_email_verified(account_id)

    session.execute = AsyncMock(side_effect=[_result(scalar=None), _result(scalar=credential)])
    session.get = AsyncMock(side_effect=[None, account])
    with pytest.raises(InvalidCredentialsError):
        await repository.update_local_password(account_id, "nouveau")
    await repository.update_local_password(account_id, "nouveau")
    assert credential.password_hash == "nouveau"
    assert account.session_version == 2

    session.execute = AsyncMock(side_effect=[_result(scalar=2), _result(scalar=None)])
    assert await repository.is_session_version_current(account_id, 2) is True
    assert await repository.is_session_version_current(account_id, 2) is False


# ============================================================================
# Compléments de couverture du 2026-08-07 — router identity_router.py
# ============================================================================


def _bearer(
    account_id: object | None = None, *, jti: str | None = None, **claims: object
) -> dict[str, str]:
    """Crée un header Authorization Bearer avec un token d'accès.

    Le paramètre ``jti`` force l'identifiant de session du token (claim JWT
    réservé) en patchant ``uuid4`` dans ``core.auth`` — ``create_access_token``
    refuse sinon les claims réservés.
    """
    extra_claims = {"roles": ["user"], **claims}
    if jti is not None:
        with patch(
            "gsie_api.core.auth.uuid4",
            return_value=type("FakeUUID", (), {"__str__": lambda self: jti})(),
        ):
            token = create_access_token(subject=str(account_id or uuid4()), claims=extra_claims)
    else:
        token = create_access_token(subject=str(account_id or uuid4()), claims=extra_claims)
    return {"Authorization": f"Bearer {token}"}


async def should_construct_session_organisation_and_billing_dependencies_directly() -> None:
    """Couvre les fabriques Depends jamais appelées quand elles sont surchargées."""
    session = _session()
    session_service = await get_session_service(session)
    assert isinstance(session_service, SessionService)
    organisation_service = await get_personal_organisation_service(session)
    assert isinstance(organisation_service, OrganisationService)
    billing_service = await get_onboarding_billing_service(session)
    assert isinstance(billing_service, BillingService)


@pytest.mark.parametrize(
    ("error", "expected_detail"),
    [
        (CompromisedPasswordError(), "PASSWORD_COMPROMISED"),
        (WeakPasswordError(score=1, minimum=3, suggestions=[]), "PASSWORD_TOO_WEAK"),
    ],
)
def should_reject_registration_when_password_strength_check_fails(
    client_identite: TestClient, error: Exception, expected_detail: str
) -> None:
    strength_service = AsyncMock()
    strength_service.validate = AsyncMock(side_effect=error)
    client_identite.app.dependency_overrides[get_password_strength_service] = (
        lambda: strength_service
    )
    response = client_identite.post(
        "/api/v1/auth/register",
        json={"email": "forestier@example.fr", "password": "mot-de-passe-long"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == expected_detail


def should_reject_local_login_when_turnstile_challenge_unresolved(
    client_identite: TestClient,
) -> None:
    with (
        patch.object(identity_router._settings, "turnstile_enabled", True),
        patch.object(identity_router._settings, "turnstile_secret_key", SecretStr("secret")),
    ):
        response = client_identite.post(
            "/api/v1/auth/login/password",
            json={
                "email": "forestier@example.fr",
                "password": "mot-de-passe-long",
                "turnstile_token": "",
            },
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Challenge anti-robot non résolu."


def should_lock_local_login_when_lockout_service_raises(client_identite: TestClient) -> None:
    lockout_service = AsyncMock()
    lockout_service.check_and_raise = AsyncMock(
        side_effect=AccountLockedError(remaining_seconds=42)
    )
    client_identite.app.dependency_overrides[get_lockout_service] = lambda: lockout_service
    response = client_identite.post(
        "/api/v1/auth/login/password",
        json={"email": "forestier@example.fr", "password": "mot-de-passe-long"},
    )
    assert response.status_code == 423
    assert response.json()["detail"] == "COMPTE_VERROUILLE"
    assert response.headers["Retry-After"] == "42"


def should_return_mfa_challenge_when_local_login_requires_second_factor(
    client_identite: TestClient,
) -> None:
    account = AuthenticatedAccount(uuid4(), ("user",), "local")
    service = AsyncMock()
    service.authenticate_local = AsyncMock(return_value=account)
    client_identite.app.dependency_overrides[get_identity_service] = lambda: service
    mfa_service = AsyncMock()
    mfa_service.is_enabled = AsyncMock(return_value=True)
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service
    response = client_identite.post(
        "/api/v1/auth/login/password",
        json={"email": "forestier@example.fr", "password": "mot-de-passe-long"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mfa_required"] is True
    assert body["challenge_token"]


def should_reject_mfa_completion_with_malformed_challenge_payload(
    client_identite: TestClient,
) -> None:
    # Le challenge ne porte pas la clé "login_key" attendue par l'endpoint.
    challenge_token = create_mfa_challenge_token(
        subject=str(uuid4()), claims={"session_version": 1}
    )
    response = client_identite.post(
        "/api/v1/auth/login/mfa",
        json={"challenge_token": challenge_token, "code": "123456"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Challenge MFA invalide"


def _mfa_challenge_token(login_key: str = "forestier@example.fr") -> str:
    return create_mfa_challenge_token(
        subject=str(uuid4()),
        claims={
            "auth_provider": "local",
            "session_version": 1,
            "roles": ["user"],
            "login_key": login_key,
        },
    )


@pytest.mark.parametrize("is_recovery", [False, True])
def should_reject_mfa_completion_with_invalid_code(
    client_identite: TestClient, is_recovery: bool
) -> None:
    mfa_service = AsyncMock()
    if is_recovery:
        mfa_service.verify_recovery_code = AsyncMock(side_effect=InvalidRecoveryCodeError)
    else:
        mfa_service.verify_totp = AsyncMock(return_value=False)
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service
    lockout_service = AsyncMock()
    client_identite.app.dependency_overrides[get_lockout_service] = lambda: lockout_service
    response = client_identite.post(
        "/api/v1/auth/login/mfa",
        json={
            "challenge_token": _mfa_challenge_token(),
            "code": "123456",
            "is_recovery_code": is_recovery,
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Code MFA invalide"
    lockout_service.record_failure.assert_awaited_once()


@pytest.mark.parametrize("is_recovery", [False, True])
def should_complete_mfa_login_and_issue_tokens(
    client_identite: TestClient, is_recovery: bool
) -> None:
    mfa_service = AsyncMock()
    mfa_service.verify_totp = AsyncMock(return_value=True)
    mfa_service.verify_recovery_code = AsyncMock(return_value=True)
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service
    lockout_service = AsyncMock()
    client_identite.app.dependency_overrides[get_lockout_service] = lambda: lockout_service
    response = client_identite.post(
        "/api/v1/auth/login/mfa",
        json={
            "challenge_token": _mfa_challenge_token(),
            "code": "123456",
            "is_recovery_code": is_recovery,
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    lockout_service.record_success.assert_awaited_once()


def should_reject_change_password_with_invalid_current_password(
    client_identite: TestClient,
) -> None:
    lifecycle = AsyncMock()
    lifecycle.change_password = AsyncMock(side_effect=InvalidCurrentPasswordError)
    client_identite.app.dependency_overrides[get_account_lifecycle_service] = lambda: lifecycle
    response = client_identite.post(
        "/api/v1/auth/password/change",
        headers=_bearer(),
        json={"current_password": "ancien-mdp", "new_password": "nouveau-mot-de-passe"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Mot de passe actuel invalide"


@pytest.mark.parametrize(
    "error", [CompromisedPasswordError(), WeakPasswordError(score=0, minimum=3, suggestions=[])]
)
def should_reject_change_password_when_new_password_too_weak(
    client_identite: TestClient, error: Exception
) -> None:
    strength_service = AsyncMock()
    strength_service.validate = AsyncMock(side_effect=error)
    client_identite.app.dependency_overrides[get_password_strength_service] = (
        lambda: strength_service
    )
    response = client_identite.post(
        "/api/v1/auth/password/change",
        headers=_bearer(),
        json={"current_password": "ancien-mdp", "new_password": "nouveau-mot-de-passe"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "PASSWORD_TOO_WEAK_OR_COMPROMISED"


def should_change_password_and_revoke_all_sessions(client_identite: TestClient) -> None:
    lifecycle = AsyncMock()
    lifecycle.change_password = AsyncMock(return_value=None)
    client_identite.app.dependency_overrides[get_account_lifecycle_service] = lambda: lifecycle
    session_service = AsyncMock()
    client_identite.app.dependency_overrides[get_session_service] = lambda: session_service
    response = client_identite.post(
        "/api/v1/auth/password/change",
        headers=_bearer(),
        json={"current_password": "ancien-mdp", "new_password": "nouveau-mot-de-passe"},
    )
    assert response.status_code == 200
    session_service.revoke_all_sessions.assert_awaited_once()


def should_export_current_account_data(client_identite: TestClient) -> None:
    with patch("gsie_api.auth.identity_router.AccountExportService") as export_cls:
        export_cls.return_value.export = AsyncMock(return_value={"account_id": "abc"})
        response = client_identite.get("/api/v1/auth/me/export", headers=_bearer())
    assert response.status_code == 200
    assert response.json() == {"account_id": "abc"}


def should_list_account_consents(client_identite: TestClient) -> None:
    row = SimpleNamespace(
        consent_type="terms",
        document_version="v1",
        accepted_at=datetime.now(UTC),
        revoked_at=None,
    )
    session = _session()
    session.execute.return_value = _result(scalars=(row,))
    client_identite.app.dependency_overrides[get_db] = lambda: session
    response = client_identite.get("/api/v1/auth/me/consents", headers=_bearer())
    assert response.status_code == 200
    consents = response.json()["consents"]
    assert consents[0]["consent_type"] == "terms"
    assert consents[0]["revoked_at"] is None


def should_accept_new_consent_and_supersede_previous_version(client_identite: TestClient) -> None:
    captured: dict[str, object] = {}
    session = _session()
    session.execute.return_value = _result()
    session.add = MagicMock(side_effect=lambda obj: captured.__setitem__("consent", obj))

    async def _flush() -> None:
        captured["consent"].accepted_at = datetime.now(UTC)  # type: ignore[union-attr]

    session.flush = AsyncMock(side_effect=_flush)
    client_identite.app.dependency_overrides[get_db] = lambda: session
    response = client_identite.post(
        "/api/v1/auth/me/consents",
        headers=_bearer(),
        json={"consent_type": "terms", "document_version": "v2"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["consent_type"] == "terms"
    assert body["document_version"] == "v2"
    assert body["revoked_at"] is None


def should_reject_revoke_consent_with_unknown_type(client_identite: TestClient) -> None:
    response = client_identite.delete("/api/v1/auth/me/consents/unknown-type", headers=_bearer())
    assert response.status_code == 400
    assert response.json()["detail"] == "Consentement invalide"


def should_revoke_known_consent_type(client_identite: TestClient) -> None:
    response = client_identite.delete("/api/v1/auth/me/consents/marketing", headers=_bearer())
    assert response.status_code == 200
    assert response.json()["completed"] is True


def should_reject_deletion_request_when_email_sender_unconfigured(
    client_identite: TestClient,
) -> None:
    email_sender = AsyncMock()
    email_sender.is_configured = False
    client_identite.app.dependency_overrides[get_transactional_email_sender] = lambda: email_sender
    response = client_identite.post(
        "/api/v1/auth/me/deletion/request",
        headers=_bearer(),
        json={"current_password": "mot-de-passe-actuel"},
    )
    assert response.status_code == 503


def should_reject_deletion_request_with_invalid_current_password(
    client_identite: TestClient,
) -> None:
    email_sender = AsyncMock()
    email_sender.is_configured = True
    client_identite.app.dependency_overrides[get_transactional_email_sender] = lambda: email_sender
    lifecycle = AsyncMock()
    lifecycle.request_account_deletion = AsyncMock(side_effect=InvalidCurrentPasswordError)
    client_identite.app.dependency_overrides[get_account_lifecycle_service] = lambda: lifecycle
    response = client_identite.post(
        "/api/v1/auth/me/deletion/request",
        headers=_bearer(),
        json={"current_password": "mot-de-passe-invalide"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Impossible de planifier la suppression du compte"


def should_fail_deletion_request_when_cancellation_email_unsent(
    client_identite: TestClient,
) -> None:
    email_sender = AsyncMock()
    email_sender.is_configured = True
    email_sender.send_deletion_cancellation_code = AsyncMock(return_value=False)
    client_identite.app.dependency_overrides[get_transactional_email_sender] = lambda: email_sender
    lifecycle = AsyncMock()
    lifecycle.request_account_deletion = AsyncMock(
        return_value=ActionCodeDelivery(email="forestier@example.fr", code="ABCD1234")
    )
    client_identite.app.dependency_overrides[get_account_lifecycle_service] = lambda: lifecycle
    response = client_identite.post(
        "/api/v1/auth/me/deletion/request",
        headers=_bearer(),
        json={"current_password": "mot-de-passe-actuel"},
    )
    assert response.status_code == 503


def should_accept_account_deletion_request(client_identite: TestClient) -> None:
    email_sender = AsyncMock()
    email_sender.is_configured = True
    email_sender.send_deletion_cancellation_code = AsyncMock(return_value=True)
    client_identite.app.dependency_overrides[get_transactional_email_sender] = lambda: email_sender
    lifecycle = AsyncMock()
    lifecycle.request_account_deletion = AsyncMock(
        return_value=ActionCodeDelivery(email="forestier@example.fr", code="ABCD1234")
    )
    client_identite.app.dependency_overrides[get_account_lifecycle_service] = lambda: lifecycle
    response = client_identite.post(
        "/api/v1/auth/me/deletion/request",
        headers=_bearer(),
        json={"current_password": "mot-de-passe-actuel"},
    )
    assert response.status_code == 202


def should_reject_cancel_deletion_with_invalid_code(client_identite: TestClient) -> None:
    lifecycle = AsyncMock()
    lifecycle.cancel_account_deletion = AsyncMock(side_effect=InvalidActionCodeError)
    client_identite.app.dependency_overrides[get_account_lifecycle_service] = lambda: lifecycle
    response = client_identite.post(
        "/api/v1/auth/deletion/cancel",
        json={"email": "forestier@example.fr", "code": "ABCD1234"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "CODE_INVALIDE_OU_EXPIRE"


def should_cancel_account_deletion(client_identite: TestClient) -> None:
    lifecycle = AsyncMock()
    lifecycle.cancel_account_deletion = AsyncMock(return_value=None)
    client_identite.app.dependency_overrides[get_account_lifecycle_service] = lambda: lifecycle
    response = client_identite.post(
        "/api/v1/auth/deletion/cancel",
        json={"email": "forestier@example.fr", "code": "ABCD1234"},
    )
    assert response.status_code == 200


def should_reject_email_change_request_when_sender_unconfigured(
    client_identite: TestClient,
) -> None:
    email_sender = AsyncMock()
    email_sender.is_configured = False
    client_identite.app.dependency_overrides[get_transactional_email_sender] = lambda: email_sender
    response = client_identite.post(
        "/api/v1/auth/email/change/request",
        headers=_bearer(),
        json={"current_password": "mot-de-passe-actuel", "new_email": "nouveau@example.fr"},
    )
    assert response.status_code == 503


@pytest.mark.parametrize("error", [InvalidCurrentPasswordError(), EmailAlreadyUsedError()])
def should_reject_email_change_request_on_invalid_password_or_used_email(
    client_identite: TestClient, error: Exception
) -> None:
    email_sender = AsyncMock()
    email_sender.is_configured = True
    client_identite.app.dependency_overrides[get_transactional_email_sender] = lambda: email_sender
    lifecycle = AsyncMock()
    lifecycle.request_email_change = AsyncMock(side_effect=error)
    client_identite.app.dependency_overrides[get_account_lifecycle_service] = lambda: lifecycle
    response = client_identite.post(
        "/api/v1/auth/email/change/request",
        headers=_bearer(),
        json={"current_password": "mot-de-passe-actuel", "new_email": "nouveau@example.fr"},
    )
    assert response.status_code == 400


def should_fail_email_change_request_when_delivery_unsent(client_identite: TestClient) -> None:
    email_sender = AsyncMock()
    email_sender.is_configured = True
    email_sender.send_email_change_code = AsyncMock(return_value=False)
    client_identite.app.dependency_overrides[get_transactional_email_sender] = lambda: email_sender
    lifecycle = AsyncMock()
    lifecycle.request_email_change = AsyncMock(
        return_value=EmailChangeDelivery(
            current_email="forestier@example.fr",
            current_code="AAAA1111",
            new_email="nouveau@example.fr",
            new_code="BBBB2222",
        )
    )
    client_identite.app.dependency_overrides[get_account_lifecycle_service] = lambda: lifecycle
    response = client_identite.post(
        "/api/v1/auth/email/change/request",
        headers=_bearer(),
        json={"current_password": "mot-de-passe-actuel", "new_email": "nouveau@example.fr"},
    )
    assert response.status_code == 503


def should_accept_email_change_request(client_identite: TestClient) -> None:
    email_sender = AsyncMock()
    email_sender.is_configured = True
    email_sender.send_email_change_code = AsyncMock(return_value=True)
    client_identite.app.dependency_overrides[get_transactional_email_sender] = lambda: email_sender
    lifecycle = AsyncMock()
    lifecycle.request_email_change = AsyncMock(
        return_value=EmailChangeDelivery(
            current_email="forestier@example.fr",
            current_code="AAAA1111",
            new_email="nouveau@example.fr",
            new_code="BBBB2222",
        )
    )
    client_identite.app.dependency_overrides[get_account_lifecycle_service] = lambda: lifecycle
    response = client_identite.post(
        "/api/v1/auth/email/change/request",
        headers=_bearer(),
        json={"current_password": "mot-de-passe-actuel", "new_email": "nouveau@example.fr"},
    )
    assert response.status_code == 202


def should_reject_confirm_email_change_with_invalid_code(client_identite: TestClient) -> None:
    lifecycle = AsyncMock()
    lifecycle.confirm_email_change = AsyncMock(side_effect=InvalidEmailChangeCodeError)
    client_identite.app.dependency_overrides[get_account_lifecycle_service] = lambda: lifecycle
    response = client_identite.post(
        "/api/v1/auth/email/change/confirm",
        headers=_bearer(),
        json={"channel": "current", "code": "ABCD1234"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "CODE_INVALIDE_OU_EXPIRE"


def should_confirm_email_change_and_revoke_sessions_when_both_sides_confirmed(
    client_identite: TestClient,
) -> None:
    profile = AccountProfile(uuid4(), "Forestier", "nouveau@example.fr", True, ("local",), ())
    lifecycle = AsyncMock()
    lifecycle.confirm_email_change = AsyncMock(return_value=(profile, True))
    client_identite.app.dependency_overrides[get_account_lifecycle_service] = lambda: lifecycle
    session_service = AsyncMock()
    client_identite.app.dependency_overrides[get_session_service] = lambda: session_service
    response = client_identite.post(
        "/api/v1/auth/email/change/confirm",
        headers=_bearer(),
        json={"channel": "new", "code": "ABCD1234"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "nouveau@example.fr"
    session_service.revoke_all_sessions.assert_awaited_once()


def should_confirm_email_change_without_revoking_when_second_side_pending(
    client_identite: TestClient,
) -> None:
    profile = AccountProfile(uuid4(), "Forestier", "forestier@example.fr", True, ("local",), ())
    lifecycle = AsyncMock()
    lifecycle.confirm_email_change = AsyncMock(return_value=(profile, False))
    client_identite.app.dependency_overrides[get_account_lifecycle_service] = lambda: lifecycle
    session_service = AsyncMock()
    client_identite.app.dependency_overrides[get_session_service] = lambda: session_service
    response = client_identite.post(
        "/api/v1/auth/email/change/confirm",
        headers=_bearer(),
        json={"channel": "current", "code": "ABCD1234"},
    )
    assert response.status_code == 200
    session_service.revoke_all_sessions.assert_not_awaited()


def should_reject_mfa_setup_when_already_enabled(client_identite: TestClient) -> None:
    mfa_service = AsyncMock()
    mfa_service.setup = AsyncMock(side_effect=MfaAlreadyEnabledError)
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service
    response = client_identite.post("/api/v1/auth/mfa/setup", headers=_bearer())
    assert response.status_code == 409
    assert response.json()["detail"] == "MFA_DEJA_ACTIVE"


def should_setup_mfa_and_return_recovery_codes(client_identite: TestClient) -> None:
    mfa_service = AsyncMock()
    mfa_service.setup = AsyncMock(
        return_value=MfaSetupResult(
            secret="SECRET", otpauth_uri="otpauth://totp/x", recovery_codes=("a1", "b2")
        )
    )
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service
    response = client_identite.post("/api/v1/auth/mfa/setup", headers=_bearer())
    assert response.status_code == 201
    body = response.json()
    assert body["secret"] == "SECRET"
    assert body["recovery_codes"] == ["a1", "b2"]


@pytest.mark.parametrize("is_recovery", [False, True])
def should_verify_mfa_successfully(client_identite: TestClient, is_recovery: bool) -> None:
    mfa_service = AsyncMock()
    mfa_service.verify_totp = AsyncMock(return_value=True)
    mfa_service.verify_recovery_code = AsyncMock(return_value=True)
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service
    response = client_identite.post(
        "/api/v1/auth/mfa/verify",
        headers=_bearer(),
        json={"code": "123456", "is_recovery_code": is_recovery},
    )
    assert response.status_code == 200
    assert response.json()["enabled"] is True


def should_reject_mfa_verification_with_invalid_totp_code(client_identite: TestClient) -> None:
    mfa_service = AsyncMock()
    mfa_service.verify_totp = AsyncMock(return_value=False)
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service
    response = client_identite.post(
        "/api/v1/auth/mfa/verify",
        headers=_bearer(),
        json={"code": "000000", "is_recovery_code": False},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "CODE_TOTP_INVALIDE"


def should_reject_mfa_verification_with_invalid_recovery_code(client_identite: TestClient) -> None:
    mfa_service = AsyncMock()
    mfa_service.verify_recovery_code = AsyncMock(side_effect=InvalidRecoveryCodeError)
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service
    response = client_identite.post(
        "/api/v1/auth/mfa/verify",
        headers=_bearer(),
        json={"code": "000000", "is_recovery_code": True},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "CODE_RECUPERATION_INVALIDE"


def should_reject_mfa_verification_when_not_enabled(client_identite: TestClient) -> None:
    mfa_service = AsyncMock()
    mfa_service.verify_totp = AsyncMock(side_effect=MfaNotEnabledError)
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service
    response = client_identite.post(
        "/api/v1/auth/mfa/verify",
        headers=_bearer(),
        json={"code": "000000", "is_recovery_code": False},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "MFA_NON_ACTIVE"


def should_reject_mfa_disable_when_not_enabled(client_identite: TestClient) -> None:
    mfa_service = AsyncMock()
    mfa_service.disable = AsyncMock(side_effect=MfaNotEnabledError)
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service
    response = client_identite.delete("/api/v1/auth/mfa", headers=_bearer())
    assert response.status_code == 404
    assert response.json()["detail"] == "MFA_NON_ACTIVE"


def should_disable_mfa_successfully(client_identite: TestClient) -> None:
    mfa_service = AsyncMock()
    mfa_service.disable = AsyncMock(return_value=None)
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service
    response = client_identite.delete("/api/v1/auth/mfa", headers=_bearer())
    assert response.status_code == 200
    assert response.json()["enabled"] is False


@pytest.mark.parametrize(("record", "expected"), [(None, False), (SimpleNamespace(), True)])
def should_report_mfa_status(client_identite: TestClient, record: object, expected: bool) -> None:
    mfa_service = AsyncMock()
    mfa_service._repository.get_active_secret = AsyncMock(return_value=record)  # noqa: SLF001
    client_identite.app.dependency_overrides[get_mfa_service] = lambda: mfa_service
    response = client_identite.get("/api/v1/auth/mfa/status", headers=_bearer())
    assert response.status_code == 200
    assert response.json()["enabled"] is expected


def should_list_active_sessions_with_current_flag(client_identite: TestClient) -> None:
    now = datetime.now(UTC)
    session_id = uuid4()
    info = SessionInfo(
        id=session_id,
        jti="jti-actuel",
        device_name="Pixel",
        user_agent="okhttp",
        ip_address="203.0.113.5",
        issued_at=now,
        last_seen_at=now,
        is_current=False,
    )
    session_service = AsyncMock()
    session_service.list_sessions = AsyncMock(return_value=[info])
    client_identite.app.dependency_overrides[get_session_service] = lambda: session_service
    response = client_identite.get("/api/v1/auth/sessions", headers=_bearer(jti="jti-actuel"))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["sessions"][0]["is_current"] is True


def should_revoke_all_sessions_except_current(client_identite: TestClient) -> None:
    session_service = AsyncMock()
    session_service.list_refresh_jtis = AsyncMock(return_value=["refresh-1", "refresh-2"])
    session_service.revoke_all_sessions = AsyncMock(return_value=2)
    client_identite.app.dependency_overrides[get_session_service] = lambda: session_service
    response = client_identite.delete("/api/v1/auth/sessions", headers=_bearer(jti="jti-actuel"))
    assert response.status_code == 200
    assert session_service.revoke_all_sessions.await_args.kwargs["except_jti"] == "jti-actuel"


def should_reject_session_revocation_with_non_uuid_id(client_identite: TestClient) -> None:
    response = client_identite.post(
        "/api/v1/auth/sessions/revoke",
        headers=_bearer(),
        json={"session_id": "pas-un-uuid"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "ID session invalide"


def should_reject_session_revocation_when_absent_or_already_revoked(
    client_identite: TestClient,
) -> None:
    session_service = AsyncMock()
    session_service.get_refresh_jti = AsyncMock(return_value=None)
    session_service.revoke_session = AsyncMock(return_value=False)
    client_identite.app.dependency_overrides[get_session_service] = lambda: session_service
    response = client_identite.post(
        "/api/v1/auth/sessions/revoke",
        headers=_bearer(),
        json={"session_id": str(uuid4())},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Session introuvable ou déjà révoquée"


def should_revoke_specific_session_and_its_refresh_token(client_identite: TestClient) -> None:
    session_service = AsyncMock()
    session_service.get_refresh_jti = AsyncMock(return_value="refresh-jti")
    session_service.revoke_session = AsyncMock(return_value=True)
    client_identite.app.dependency_overrides[get_session_service] = lambda: session_service
    response = client_identite.post(
        "/api/v1/auth/sessions/revoke",
        headers=_bearer(),
        json={"session_id": str(uuid4())},
    )
    assert response.status_code == 200


class _FakeOidcVerifier:
    def __init__(
        self,
        *,
        configured: bool = True,
        providers: tuple[str, ...] = ("keycloak",),
    ) -> None:
        self.is_configured = configured
        self._providers = providers
        self.build_authorization_url = MagicMock(
            return_value="https://auth.example.test/authorize?state=x"
        )
        self.verify = AsyncMock()

    def get_provider_names(self) -> list[str]:
        return list(self._providers)


def should_list_configured_oidc_providers(client_identite: TestClient) -> None:
    with patch(
        "gsie_api.auth.identity_router.get_generic_oidc_verifier",
        return_value=_FakeOidcVerifier(providers=("keycloak", "azure-ad")),
    ):
        response = client_identite.get("/api/v1/auth/oidc/providers")
    assert response.status_code == 200
    assert response.json()["providers"] == ["keycloak", "azure-ad"]


def should_reject_oidc_authorize_when_verifier_rejects_parameters(
    client_identite: TestClient,
) -> None:
    verifier = _FakeOidcVerifier()
    verifier.build_authorization_url = MagicMock(
        side_effect=InvalidOidcTokenError("redirect_uri OIDC non autorisée")
    )
    with patch("gsie_api.auth.identity_router.get_generic_oidc_verifier", return_value=verifier):
        response = client_identite.get(
            "/api/v1/auth/oidc/keycloak/authorize",
            params={
                "redirect_uri": "https://app.example.test/callback",
                "state": "s" * 20,
                "code_challenge": "c" * 43,
            },
        )
    assert response.status_code == 400


def should_build_oidc_authorization_url_and_return_nonce(client_identite: TestClient) -> None:
    verifier = _FakeOidcVerifier()
    with patch("gsie_api.auth.identity_router.get_generic_oidc_verifier", return_value=verifier):
        response = client_identite.get(
            "/api/v1/auth/oidc/keycloak/authorize",
            params={
                "redirect_uri": "https://app.example.test/callback",
                "state": "s" * 20,
                "code_challenge": "c" * 43,
                "client_id": "geosylva-android",
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "keycloak"
    assert body["nonce"]
    verifier.build_authorization_url.assert_called_once()


def should_reject_oidc_login_when_no_provider_configured(client_identite: TestClient) -> None:
    verifier = _FakeOidcVerifier(configured=False)
    with patch("gsie_api.auth.identity_router.get_generic_oidc_verifier", return_value=verifier):
        response = client_identite.post(
            "/api/v1/auth/login/oidc",
            json={
                "provider": "keycloak",
                "id_token": "jeton-oidc",
                "nonce": "n" * 32,
            },
        )
    assert response.status_code == 503


def should_reject_oidc_login_with_already_consumed_nonce(client_identite: TestClient) -> None:
    verifier = _FakeOidcVerifier()
    nonce_store = AsyncMock()
    nonce_store.consume = AsyncMock(return_value=False)
    client_identite.app.dependency_overrides[get_oidc_nonce_store] = lambda: nonce_store
    with patch("gsie_api.auth.identity_router.get_generic_oidc_verifier", return_value=verifier):
        response = client_identite.post(
            "/api/v1/auth/login/oidc",
            json={
                "provider": "keycloak",
                "id_token": "jeton-oidc",
                "nonce": "n" * 32,
            },
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Preuve OIDC invalide"


def should_reject_oidc_login_with_invalid_token(client_identite: TestClient) -> None:
    verifier = _FakeOidcVerifier()
    verifier.verify = AsyncMock(side_effect=InvalidOidcTokenError("jeton invalide"))
    nonce_store = AsyncMock()
    nonce_store.consume = AsyncMock(return_value=True)
    client_identite.app.dependency_overrides[get_oidc_nonce_store] = lambda: nonce_store
    with patch("gsie_api.auth.identity_router.get_generic_oidc_verifier", return_value=verifier):
        response = client_identite.post(
            "/api/v1/auth/login/oidc",
            json={
                "provider": "keycloak",
                "id_token": "jeton-oidc",
                "nonce": "n" * 32,
            },
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Preuve OIDC invalide"


def should_require_explicit_link_when_oidc_email_matches_existing_account(
    client_identite: TestClient,
) -> None:
    identity = GoogleIdentity(
        issuer="https://auth.example.test/realms/quintessences",
        subject="sujet-oidc",
        email="forestier@example.fr",
        display_name="Forestier",
    )
    verifier = _FakeOidcVerifier()
    verifier.verify = AsyncMock(return_value=identity)
    nonce_store = AsyncMock()
    nonce_store.consume = AsyncMock(return_value=True)
    client_identite.app.dependency_overrides[get_oidc_nonce_store] = lambda: nonce_store
    identity_service = AsyncMock()
    identity_service._repository.find_provider_account = AsyncMock(return_value=None)  # noqa: SLF001
    identity_service._repository.has_account_with_verified_email = AsyncMock(  # noqa: SLF001
        return_value=True
    )
    client_identite.app.dependency_overrides[get_identity_service] = lambda: identity_service
    with patch("gsie_api.auth.identity_router.get_generic_oidc_verifier", return_value=verifier):
        response = client_identite.post(
            "/api/v1/auth/login/oidc",
            json={
                "provider": "keycloak",
                "id_token": "jeton-oidc",
                "nonce": "n" * 32,
            },
        )
    assert response.status_code == 409
    assert response.json()["detail"] == "ACCOUNT_LINK_REQUIRED"


def should_create_oidc_account_on_first_login(client_identite: TestClient) -> None:
    identity = GoogleIdentity(
        issuer="https://auth.example.test/realms/quintessences",
        subject="sujet-oidc-nouveau",
        email="nouveau@example.fr",
        display_name="Nouveau",
    )
    verifier = _FakeOidcVerifier()
    verifier.verify = AsyncMock(return_value=identity)
    nonce_store = AsyncMock()
    nonce_store.consume = AsyncMock(return_value=True)
    client_identite.app.dependency_overrides[get_oidc_nonce_store] = lambda: nonce_store
    account = AuthenticatedAccount(uuid4(), ("user",), "keycloak")
    identity_service = AsyncMock()
    identity_service._repository.find_provider_account = AsyncMock(return_value=None)  # noqa: SLF001
    identity_service._repository.has_account_with_verified_email = AsyncMock(  # noqa: SLF001
        return_value=False
    )
    identity_service._repository.create_oidc_account = AsyncMock(return_value=account)  # noqa: SLF001
    client_identite.app.dependency_overrides[get_identity_service] = lambda: identity_service
    with patch("gsie_api.auth.identity_router.get_generic_oidc_verifier", return_value=verifier):
        response = client_identite.post(
            "/api/v1/auth/login/oidc",
            json={
                "provider": "keycloak",
                "id_token": "jeton-oidc",
                "nonce": "n" * 32,
            },
        )
    assert response.status_code == 200
    identity_service._repository.create_oidc_account.assert_awaited_once()  # noqa: SLF001


def should_login_existing_oidc_account_without_recreating_it(
    client_identite: TestClient,
) -> None:
    identity = GoogleIdentity(
        issuer="https://auth.example.test/realms/quintessences",
        subject="sujet-oidc-existant",
        email="existant@example.fr",
        display_name="Existant",
    )
    verifier = _FakeOidcVerifier()
    verifier.verify = AsyncMock(return_value=identity)
    nonce_store = AsyncMock()
    nonce_store.consume = AsyncMock(return_value=True)
    client_identite.app.dependency_overrides[get_oidc_nonce_store] = lambda: nonce_store
    account = AuthenticatedAccount(uuid4(), ("user",), "keycloak")
    identity_service = AsyncMock()
    identity_service._repository.find_provider_account = AsyncMock(return_value=account)  # noqa: SLF001
    client_identite.app.dependency_overrides[get_identity_service] = lambda: identity_service
    with patch("gsie_api.auth.identity_router.get_generic_oidc_verifier", return_value=verifier):
        response = client_identite.post(
            "/api/v1/auth/login/oidc",
            json={
                "provider": "keycloak",
                "id_token": "jeton-oidc",
                "nonce": "n" * 32,
            },
        )
    assert response.status_code == 200
    identity_service._repository.create_oidc_account.assert_not_awaited()  # noqa: SLF001


def should_reject_password_strength_check_without_password(client_identite: TestClient) -> None:
    response = client_identite.post("/api/v1/auth/password/strength", json={})
    assert response.status_code == 400
    assert response.json()["detail"] == "Mot de passe requis"


def should_report_password_strength_meeting_requirements(client_identite: TestClient) -> None:
    strength_service = AsyncMock()
    strength_service.check = AsyncMock(
        return_value=PasswordStrengthReport(
            zxcvbn_score=4,
            is_compromised=False,
            compromise_count=0,
            suggestions=(),
        )
    )
    client_identite.app.dependency_overrides[get_password_strength_service] = (
        lambda: strength_service
    )
    response = client_identite.post(
        "/api/v1/auth/password/strength", json={"password": "un-mot-de-passe-robuste"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meets_requirements"] is True
    assert body["zxcvbn_score"] == 4

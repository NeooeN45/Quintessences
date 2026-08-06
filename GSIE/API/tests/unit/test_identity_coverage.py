"""Couverture des branches de sécurité du socle d'identité DEC-000044."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from gsie_api.app import create_app
from gsie_api.auth import google_nonces
from gsie_api.auth.account_lifecycle import AccountProfile
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
    get_identity_service,
    get_mfa_service,
    get_onboarding_billing_service,
    get_personal_organisation_service,
    get_session_service,
)
from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore, get_refresh_token_store
from gsie_api.auth.repository import SqlAlchemyIdentityRepository
from gsie_api.core.auth import create_access_token
from gsie_api.infrastructure.database import get_db
from gsie_api.infrastructure.models.accounts import (
    IdentityActionTokenModel,
    IdentityProviderLinkModel,
    LocalCredentialModel,
    UserAccountModel,
)

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

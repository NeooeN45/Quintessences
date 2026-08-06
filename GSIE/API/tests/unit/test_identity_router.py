"""Contrats HTTP de l'identité Quintessences."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

import gsie_api.auth.identity_router as identity_router
from gsie_api.app import create_app
from gsie_api.auth.google_nonces import MemoryGoogleNonceStore, get_google_nonce_store
from gsie_api.auth.identity import (
    AccountLinkRequiredError,
    AuthenticatedAccount,
    InvalidCredentialsError,
)
from gsie_api.auth.identity_router import (
    get_identity_service,
    get_onboarding_billing_service,
    get_personal_organisation_service,
    get_session_service,
)
from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore, get_refresh_token_store
from gsie_api.core.auth import create_access_token, verify_token
from gsie_api.infrastructure.database import get_db

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def _reset_turnstile_settings() -> Generator[None, None, None]:
    """Isole la configuration Turnstile entre les tests."""
    previous_enabled = identity_router._settings.turnstile_enabled
    previous_secret = identity_router._settings.turnstile_secret_key
    identity_router._settings.turnstile_enabled = False
    identity_router._settings.turnstile_secret_key = SecretStr("")
    yield
    identity_router._settings.turnstile_enabled = previous_enabled
    identity_router._settings.turnstile_secret_key = previous_secret


@pytest.fixture
def client(mock_lifespan: object) -> Generator[TestClient, None, None]:
    del mock_lifespan
    app = create_app()
    refresh_store = MemoryRefreshTokenStore()
    nonce_store = MemoryGoogleNonceStore()
    session_service = AsyncMock()
    session_service.register_session = AsyncMock()
    personal_organisation_service = AsyncMock()
    billing_service = AsyncMock()
    db_session = MagicMock()
    db_session.execute = AsyncMock()
    db_session.flush = AsyncMock()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_personal_organisation_service] = (
        lambda: personal_organisation_service
    )
    app.dependency_overrides[get_onboarding_billing_service] = lambda: billing_service
    app.dependency_overrides[get_refresh_token_store] = lambda: refresh_store
    app.dependency_overrides[get_google_nonce_store] = lambda: nonce_store
    app.dependency_overrides[get_session_service] = lambda: session_service
    with TestClient(app) as test_client:
        yield test_client


def _account(provider: str = "local") -> AuthenticatedAccount:
    return AuthenticatedAccount(
        account_id=uuid4(),
        roles=("user",),
        provider=provider,
    )


def should_publish_local_google_and_enterprise_capabilities(client: TestClient) -> None:
    with patch(
        "gsie_api.auth.identity_router._settings.google_oauth_client_ids",
        ["web-client-id"],
    ):
        response = client.get("/api/v1/auth/providers")

    assert response.status_code == 200
    providers = {item["provider"]: item for item in response.json()["providers"]}
    assert providers["local"]["status"] == "available"
    assert providers["google"]["status"] == "available"
    assert providers["enterprise"]["status"] == "development"


def should_create_gsie_tokens_when_local_registration_succeeds(client: TestClient) -> None:
    account = _account()
    service = AsyncMock()
    service.register_local = AsyncMock(return_value=account)
    client.app.dependency_overrides[get_identity_service] = lambda: service

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "forestier@example.fr",
            "password": "mot-de-passe-long-et-unique",
            "display_name": "Forestier Test",
        },
    )

    assert response.status_code == 201
    payload = verify_token(response.json()["access_token"])
    assert payload["sub"] == str(account.account_id)
    assert payload["roles"] == ["user"]
    assert payload["auth_provider"] == "local"


def should_return_same_http_error_for_unknown_account_and_wrong_password(
    client: TestClient,
) -> None:
    service = AsyncMock()
    service.authenticate_local = AsyncMock(side_effect=InvalidCredentialsError)
    client.app.dependency_overrides[get_identity_service] = lambda: service

    response = client.post(
        "/api/v1/auth/login/password",
        json={
            "email": "forestier@example.fr",
            "password": "mot-de-passe-incorrect",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Identifiants invalides"


def should_issue_and_consume_google_nonce_before_login(client: TestClient) -> None:
    account = _account("google")
    service = AsyncMock()
    service.authenticate_google = AsyncMock(return_value=account)
    client.app.dependency_overrides[get_identity_service] = lambda: service

    nonce_response = client.post("/api/v1/auth/google/nonce")
    nonce = nonce_response.json()["nonce"]
    login_response = client.post(
        "/api/v1/auth/login/google",
        json={"id_token": "google-id-token", "nonce": nonce},
    )
    replay_response = client.post(
        "/api/v1/auth/login/google",
        json={"id_token": "google-id-token", "nonce": nonce},
    )

    assert nonce_response.status_code == 201
    assert login_response.status_code == 200
    assert replay_response.status_code == 401
    service.authenticate_google.assert_awaited_once_with("google-id-token", nonce)


def should_require_explicit_link_when_google_email_matches_existing_account(
    client: TestClient,
) -> None:
    service = AsyncMock()
    service.authenticate_google = AsyncMock(side_effect=AccountLinkRequiredError)
    client.app.dependency_overrides[get_identity_service] = lambda: service
    nonce_response = client.post("/api/v1/auth/google/nonce")

    response = client.post(
        "/api/v1/auth/login/google",
        json={
            "id_token": "google-id-token",
            "nonce": nonce_response.json()["nonce"],
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "ACCOUNT_LINK_REQUIRED"


def should_link_google_to_subject_of_current_gsie_session(client: TestClient) -> None:
    account = _account()
    service = AsyncMock()
    service.link_google = AsyncMock(return_value=account)
    client.app.dependency_overrides[get_identity_service] = lambda: service
    nonce_response = client.post("/api/v1/auth/google/nonce")
    token = create_access_token(subject=str(account.account_id), claims={"roles": ["user"]})

    response = client.post(
        "/api/v1/auth/link/google",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "id_token": "google-id-token",
            "nonce": nonce_response.json()["nonce"],
        },
    )

    assert response.status_code == 200
    called_account_id = service.link_google.await_args.kwargs["account_id"]
    assert isinstance(called_account_id, UUID)
    assert called_account_id == account.account_id


def test_should_build_pkce_authorization_url_for_registered_redirect() -> None:
    from gsie_api.auth.oidc_generic import GenericOidcVerifier, OidcProviderConfig

    verifier = GenericOidcVerifier(
        (
            OidcProviderConfig(
                name="keycloak",
                issuer="https://auth.example.test/realms/quintessences",
                client_ids=("geosylva-android",),
                jwks_url="https://auth.example.test/certs",
                authorization_url="https://auth.example.test/authorize",
                allowed_redirect_uris=("com.quintessences.geosylva:/oauth2redirect",),
            ),
        )
    )

    url = verifier.build_authorization_url(
        "keycloak",
        "com.quintessences.geosylva:/oauth2redirect",
        "state-value-123456",
        "a" * 43,
    )

    assert "code_challenge_method=S256" in url
    assert "response_type=code" in url
    assert "client_id=geosylva-android" in url

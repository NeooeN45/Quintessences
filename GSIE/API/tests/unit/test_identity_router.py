"""Contrats HTTP de l'identité Quintessences."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.auth.google_nonces import MemoryGoogleNonceStore, get_google_nonce_store
from gsie_api.auth.identity import (
    AccountLinkRequiredError,
    AuthenticatedAccount,
    InvalidCredentialsError,
)
from gsie_api.auth.identity_router import get_identity_service
from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore, get_refresh_token_store
from gsie_api.core.auth import create_access_token, verify_token

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def client(mock_lifespan: object) -> Generator[TestClient, None, None]:
    del mock_lifespan
    app = create_app()
    refresh_store = MemoryRefreshTokenStore()
    nonce_store = MemoryGoogleNonceStore()
    app.dependency_overrides[get_refresh_token_store] = lambda: refresh_store
    app.dependency_overrides[get_google_nonce_store] = lambda: nonce_store
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

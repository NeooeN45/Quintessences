"""Contrat HTTP du profil et de la récupération de compte."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.auth.account_lifecycle import (
    AccountLifecycleService,
    AccountNotFoundError,
    AccountProfile,
    ActionCodeDelivery,
    InvalidActionCodeError,
)
from gsie_api.auth.identity_router import get_account_lifecycle_service
from gsie_api.auth.transactional_email import get_transactional_email_sender
from gsie_api.core.auth import create_access_token

if TYPE_CHECKING:
    from collections.abc import Generator


class FakeEmailSender:
    is_configured = True

    def __init__(self) -> None:
        self.deliveries: list[tuple[str, str, str]] = []

    async def send_verification(self, email: str, code: str) -> bool:
        self.deliveries.append(("verify_email", email, code))
        return True

    async def send_password_reset(self, email: str, code: str) -> bool:
        self.deliveries.append(("reset_password", email, code))
        return True


@pytest.fixture
def lifecycle_client(mock_lifespan: object) -> Generator[tuple[TestClient, AsyncMock], None, None]:
    del mock_lifespan
    app = create_app()
    service = AsyncMock()
    app.dependency_overrides[get_account_lifecycle_service] = lambda: service
    app.dependency_overrides[get_transactional_email_sender] = FakeEmailSender
    with TestClient(app) as client:
        yield client, service


def _authorization(account_id: object) -> dict[str, str]:
    token = create_access_token(subject=str(account_id), claims={"roles": ["user"]})
    return {"Authorization": f"Bearer {token}"}


async def should_build_the_account_lifecycle_dependency_lazily() -> None:
    """La dépendance assemble le service dans la session de la requête."""
    service = await get_account_lifecycle_service(MagicMock())

    assert isinstance(service, AccountLifecycleService)


def should_return_current_account_profile_when_session_is_valid(
    lifecycle_client: tuple[TestClient, AsyncMock],
) -> None:
    client, service = lifecycle_client
    account_id = uuid4()
    service.get_profile.return_value = AccountProfile(
        account_id=account_id,
        display_name="Camille",
        email="forestier@example.fr",
        email_verified=True,
        providers=("local", "google"),
        roles=("user",),
    )

    response = client.get("/api/v1/auth/me", headers=_authorization(account_id))

    assert response.status_code == 200
    assert response.json()["display_name"] == "Camille"
    assert response.json()["email_verified"] is True


def should_return_same_accepted_response_when_reset_email_is_unknown(
    lifecycle_client: tuple[TestClient, AsyncMock],
) -> None:
    client, service = lifecycle_client
    service.request_password_reset.return_value = None

    response = client.post(
        "/api/v1/auth/password/reset/request",
        json={"email": "inconnu@example.fr"},
    )

    assert response.status_code == 202
    assert response.json() == {"accepted": True}


def should_return_generic_error_when_reset_code_is_invalid(
    lifecycle_client: tuple[TestClient, AsyncMock],
) -> None:
    client, service = lifecycle_client
    service.confirm_password_reset.side_effect = InvalidActionCodeError

    response = client.post(
        "/api/v1/auth/password/reset/confirm",
        json={
            "email": "forestier@example.fr",
            "code": "ABCD-EFGH",
            "new_password": "nouveau-mot-de-passe-solide",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "CODE_INVALIDE_OU_EXPIRE"


def should_update_display_name_without_changing_identity(
    lifecycle_client: tuple[TestClient, AsyncMock],
) -> None:
    client, service = lifecycle_client
    account_id = uuid4()
    service.update_profile.return_value = AccountProfile(
        account_id=account_id,
        display_name="Nouveau nom",
        email="forestier@example.fr",
        email_verified=False,
        providers=("local",),
        roles=("user",),
    )

    response = client.patch(
        "/api/v1/auth/me",
        headers=_authorization(account_id),
        json={"display_name": "Nouveau nom"},
    )

    assert response.status_code == 200
    assert response.json()["account_id"] == str(account_id)
    service.update_profile.assert_awaited_once_with(account_id, "Nouveau nom")


@pytest.mark.parametrize("method", ["get", "patch"])
def should_return_not_found_when_profile_disappears(
    lifecycle_client: tuple[TestClient, AsyncMock],
    method: str,
) -> None:
    client, service = lifecycle_client
    account_id = uuid4()
    if method == "get":
        service.get_profile.side_effect = AccountNotFoundError
        response = client.get("/api/v1/auth/me", headers=_authorization(account_id))
    else:
        service.update_profile.side_effect = AccountNotFoundError
        response = client.patch(
            "/api/v1/auth/me",
            headers=_authorization(account_id),
            json={"display_name": "Absent"},
        )
    assert response.status_code == 404


def should_reject_profile_with_non_uuid_subject(
    lifecycle_client: tuple[TestClient, AsyncMock],
) -> None:
    client, _service = lifecycle_client
    response = client.get("/api/v1/auth/me", headers=_authorization("non-uuid"))
    assert response.status_code == 401


def should_cover_email_verification_http_contract(
    lifecycle_client: tuple[TestClient, AsyncMock],
) -> None:
    client, service = lifecycle_client
    account_id = uuid4()
    headers = _authorization(account_id)
    sender = FakeEmailSender()
    client.app.dependency_overrides[get_transactional_email_sender] = lambda: sender

    sender.is_configured = False
    response = client.post("/api/v1/auth/email/verification/request", headers=headers)
    assert response.status_code == 503

    sender.is_configured = True
    service.request_email_verification.return_value = None
    response = client.post("/api/v1/auth/email/verification/request", headers=headers)
    assert response.status_code == 202

    delivery = ActionCodeDelivery("forestier@example.fr", "ABCD-EFGH")
    service.request_email_verification.return_value = delivery
    sender.send_verification = AsyncMock(return_value=False)  # type: ignore[method-assign]
    response = client.post("/api/v1/auth/email/verification/request", headers=headers)
    assert response.status_code == 503

    sender.send_verification = AsyncMock(return_value=True)  # type: ignore[method-assign]
    response = client.post("/api/v1/auth/email/verification/request", headers=headers)
    assert response.status_code == 202


def should_cover_email_verification_confirmation(
    lifecycle_client: tuple[TestClient, AsyncMock],
) -> None:
    client, service = lifecycle_client
    account_id = uuid4()
    headers = _authorization(account_id)
    profile = AccountProfile(
        account_id=account_id,
        display_name="Camille",
        email="forestier@example.fr",
        email_verified=True,
        providers=("local",),
        roles=("user",),
    )
    service.confirm_email_verification.return_value = profile

    response = client.post(
        "/api/v1/auth/email/verification/confirm",
        headers=headers,
        json={"code": "ABCD-EFGH"},
    )
    assert response.status_code == 200
    assert response.json()["email_verified"] is True

    service.confirm_email_verification.side_effect = InvalidActionCodeError
    response = client.post(
        "/api/v1/auth/email/verification/confirm",
        headers=headers,
        json={"code": "ABCD-EFGH"},
    )
    assert response.status_code == 400


def should_cover_password_reset_delivery_and_completion(
    lifecycle_client: tuple[TestClient, AsyncMock],
) -> None:
    client, service = lifecycle_client
    sender = FakeEmailSender()
    client.app.dependency_overrides[get_transactional_email_sender] = lambda: sender

    sender.is_configured = False
    response = client.post(
        "/api/v1/auth/password/reset/request",
        json={"email": "forestier@example.fr"},
    )
    assert response.status_code == 503

    sender.is_configured = True
    service.request_password_reset.return_value = ActionCodeDelivery(
        "forestier@example.fr",
        "ABCD-EFGH",
    )
    response = client.post(
        "/api/v1/auth/password/reset/request",
        json={"email": "forestier@example.fr"},
    )
    assert response.status_code == 202
    assert sender.deliveries[-1][0] == "reset_password"

    service.confirm_password_reset.side_effect = None
    response = client.post(
        "/api/v1/auth/password/reset/confirm",
        json={
            "email": "forestier@example.fr",
            "code": "ABCD-EFGH",
            "new_password": "nouveau-mot-de-passe-solide",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"completed": True}

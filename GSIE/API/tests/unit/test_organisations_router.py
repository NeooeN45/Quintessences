"""Contrat HTTP du router organisations (multi-tenant enterprise).

Le router est testé avec ``create_app()`` et un ``OrganisationService`` mocké
via ``dependency_overrides`` (aucune connexion DB réelle) — même pattern que
``tests/unit/test_account_lifecycle_router.py``. Couvre :
- la porte d'auth (401) et la conversion du ``sub`` JWT en UUID (401 si invalide),
- les codes de statut succès/erreur de chaque endpoint,
- le flux d'invitation par e-mail (503 si non configuré, 503 si envoi échoué).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from gsie_api.app import create_app
from gsie_api.auth.transactional_email import get_transactional_email_sender
from gsie_api.core.auth import create_access_token
from gsie_api.organisations.router import _map_error, get_organisation_service
from gsie_api.organisations.service import (
    AlreadyMemberError,
    InsufficientRoleError,
    InvitationDelivery,
    InvitationEmailMismatchError,
    InvitationInvalidError,
    InvitationRecord,
    LastOwnerError,
    MemberRecord,
    NotMemberError,
    OrganisationNotFoundError,
    OrganisationRecord,
    OrganisationService,
    SlugAlreadyTakenError,
    WorkspaceRecord,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from fastapi.testclient import TestClient

_PREFIX = "/api/v1/orgs"


class FakeEmailSender:
    """Faux expéditeur transactionnel — configurable par test."""

    is_configured = True

    def __init__(self) -> None:
        self.deliveries: list[tuple[str, str, str, str]] = []
        self.should_deliver = True

    async def send_organisation_invitation(
        self, *, email: str, organisation_name: str, invite_url: str, role: str
    ) -> bool:
        self.deliveries.append((email, organisation_name, invite_url, role))
        return self.should_deliver


class UnconfiguredEmailSender(FakeEmailSender):
    is_configured = False


@pytest.fixture
def app_and_service(
    mock_lifespan: object,
) -> Generator[tuple[TestClient, AsyncMock], None, None]:
    from fastapi.testclient import TestClient

    del mock_lifespan
    app = create_app()
    service = AsyncMock(spec=OrganisationService)
    app.dependency_overrides[get_organisation_service] = lambda: service
    app.dependency_overrides[get_transactional_email_sender] = FakeEmailSender
    with TestClient(app) as client:
        yield client, service
    app.dependency_overrides.clear()


def _auth(account_id: object | None = None) -> dict[str, str]:
    sub = str(account_id) if account_id is not None else str(uuid4())
    token = create_access_token(subject=sub, claims={"roles": ["user"]})
    return {"Authorization": f"Bearer {token}"}


def _org_record(**overrides: object) -> OrganisationRecord:
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "id": uuid4(),
        "slug": "onf",
        "display_name": "ONF",
        "status": "active",
        "created_by": uuid4(),
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    defaults.update(overrides)
    return OrganisationRecord(**defaults)  # type: ignore[arg-type]


def _ws_record(**overrides: object) -> WorkspaceRecord:
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "id": uuid4(),
        "organisation_id": uuid4(),
        "slug": "ws1",
        "display_name": "Workspace 1",
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    defaults.update(overrides)
    return WorkspaceRecord(**defaults)  # type: ignore[arg-type]


def _member_record(**overrides: object) -> MemberRecord:
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "organisation_id": uuid4(),
        "account_id": uuid4(),
        "role": "member",
        "invited_by": uuid4(),
        "joined_at": now,
        "revoked_at": None,
    }
    defaults.update(overrides)
    return MemberRecord(**defaults)  # type: ignore[arg-type]


def _invitation_record(**overrides: object) -> InvitationRecord:
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "id": uuid4(),
        "organisation_id": uuid4(),
        "email_normalized": "membre@example.fr",
        "role": "member",
        "invited_by": uuid4(),
        "token_hash": "hash",
        "expires_at": now + timedelta(hours=72),
        "accepted_at": None,
        "revoked_at": None,
    }
    defaults.update(overrides)
    return InvitationRecord(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Dependency directe — ligne 64 (assemblage paresseux du service)
# ---------------------------------------------------------------------------


async def should_build_the_organisation_service_dependency_lazily() -> None:
    """La dépendance assemble le service SQLAlchemy dans la session de requête."""
    service = await get_organisation_service(MagicMock())

    assert isinstance(service, OrganisationService)


def should_map_unrecognized_error_to_500() -> None:
    """``_map_error`` retombe sur 500 pour un type d'erreur non cartographié.

    Dans le router actuel, chaque appelant ne capture que les types déjà
    mappés (409/404/403) — cette branche défensive n'est donc jamais
    atteinte via une requête HTTP réelle. On la teste directement.
    """
    http_exc = _map_error(ValueError("erreur inattendue"))

    assert http_exc.status_code == 500
    assert http_exc.detail == "erreur inattendue"


# ---------------------------------------------------------------------------
# Porte d'auth — sub JWT invalide
# ---------------------------------------------------------------------------


def should_return_401_when_sub_claim_is_not_a_valid_uuid(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    """Un token valide dont le ``sub`` n'est pas un UUID retourne 401."""
    client, _service = app_and_service
    token = create_access_token(subject="not-a-uuid", claims={"roles": ["user"]})

    response = client.post(
        _PREFIX,
        json={"slug": "onf", "display_name": "ONF"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def should_return_401_when_create_organisation_without_token(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, _service = app_and_service
    response = client.post(_PREFIX, json={"slug": "onf", "display_name": "ONF"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /orgs — create_organisation
# ---------------------------------------------------------------------------


def should_return_201_when_create_organisation_succeeds(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    service.create_organisation.return_value = _org_record(slug="onf")

    response = client.post(_PREFIX, json={"slug": "onf", "display_name": "ONF"}, headers=_auth())

    assert response.status_code == 201
    assert response.json()["slug"] == "onf"


def should_return_409_when_create_organisation_slug_taken(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    service.create_organisation.side_effect = SlugAlreadyTakenError("onf")

    response = client.post(_PREFIX, json={"slug": "onf", "display_name": "ONF"}, headers=_auth())

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# GET /orgs — list_organisations
# ---------------------------------------------------------------------------


def should_return_200_when_list_organisations(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    service.list_organisations.return_value = ([_org_record()], 1)

    response = client.get(_PREFIX, headers=_auth())

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


# ---------------------------------------------------------------------------
# GET /orgs/{org_id} — get_organisation
# ---------------------------------------------------------------------------


def should_return_200_when_get_organisation_found(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org = _org_record()
    service.get_organisation.return_value = org

    response = client.get(f"{_PREFIX}/{org.id}", headers=_auth())

    assert response.status_code == 200
    assert response.json()["id"] == str(org.id)


def should_return_404_when_get_organisation_not_found(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    service.get_organisation.side_effect = OrganisationNotFoundError(str(org_id))

    response = client.get(f"{_PREFIX}/{org_id}", headers=_auth())

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /orgs/{org_id}/workspaces — create_workspace
# ---------------------------------------------------------------------------


def should_return_201_when_create_workspace_succeeds(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    service.create_workspace.return_value = _ws_record(organisation_id=org_id)

    response = client.post(
        f"{_PREFIX}/{org_id}/workspaces",
        json={"slug": "ws1", "display_name": "Workspace 1"},
        headers=_auth(),
    )

    assert response.status_code == 201
    assert response.json()["organisation_id"] == str(org_id)


def should_return_403_when_create_workspace_insufficient_role(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    service.create_workspace.side_effect = InsufficientRoleError("role manquant")

    response = client.post(
        f"{_PREFIX}/{org_id}/workspaces",
        json={"slug": "ws1", "display_name": "Workspace 1"},
        headers=_auth(),
    )

    assert response.status_code == 403


def should_return_409_when_create_workspace_slug_taken(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    service.create_workspace.side_effect = SlugAlreadyTakenError("ws1")

    response = client.post(
        f"{_PREFIX}/{org_id}/workspaces",
        json={"slug": "ws1", "display_name": "Workspace 1"},
        headers=_auth(),
    )

    assert response.status_code == 409


def should_return_404_when_create_workspace_organisation_not_found(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    service.create_workspace.side_effect = OrganisationNotFoundError(str(org_id))

    response = client.post(
        f"{_PREFIX}/{org_id}/workspaces",
        json={"slug": "ws1", "display_name": "Workspace 1"},
        headers=_auth(),
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /orgs/{org_id}/workspaces — list_workspaces
# ---------------------------------------------------------------------------


def should_return_200_when_list_workspaces(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    service.list_workspaces.return_value = ([_ws_record(organisation_id=org_id)], 1)

    response = client.get(f"{_PREFIX}/{org_id}/workspaces", headers=_auth())

    assert response.status_code == 200
    assert response.json()["total"] == 1


# ---------------------------------------------------------------------------
# POST /orgs/{org_id}/members — invite_member
# ---------------------------------------------------------------------------


def should_return_201_when_invite_member_succeeds(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    account_id = uuid4()
    service.invite_member.return_value = _member_record(
        organisation_id=org_id, account_id=account_id
    )

    response = client.post(
        f"{_PREFIX}/{org_id}/members",
        json={"account_id": str(account_id), "role": "member"},
        headers=_auth(),
    )

    assert response.status_code == 201
    assert response.json()["account_id"] == str(account_id)


def should_return_403_when_invite_member_insufficient_role(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    service.invite_member.side_effect = InsufficientRoleError("role manquant")

    response = client.post(
        f"{_PREFIX}/{org_id}/members",
        json={"account_id": str(uuid4()), "role": "member"},
        headers=_auth(),
    )

    assert response.status_code == 403


def should_return_409_when_invite_member_already_member(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    service.invite_member.side_effect = AlreadyMemberError("déjà membre")

    response = client.post(
        f"{_PREFIX}/{org_id}/members",
        json={"account_id": str(uuid4()), "role": "member"},
        headers=_auth(),
    )

    assert response.status_code == 409


def should_return_404_when_invite_member_organisation_not_found(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    service.invite_member.side_effect = OrganisationNotFoundError(str(org_id))

    response = client.post(
        f"{_PREFIX}/{org_id}/members",
        json={"account_id": str(uuid4()), "role": "member"},
        headers=_auth(),
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /orgs/{org_id}/invitations — create_email_invitation
# ---------------------------------------------------------------------------


def should_return_503_when_email_invitation_sender_not_configured(
    mock_lifespan: object,
) -> None:
    from fastapi.testclient import TestClient

    del mock_lifespan
    app = create_app()
    service = AsyncMock(spec=OrganisationService)
    app.dependency_overrides[get_organisation_service] = lambda: service
    app.dependency_overrides[get_transactional_email_sender] = UnconfiguredEmailSender
    org_id = uuid4()
    with TestClient(app) as client:
        response = client.post(
            f"{_PREFIX}/{org_id}/invitations",
            json={"email": "membre@example.fr", "role": "member"},
            headers=_auth(),
        )
    assert response.status_code == 503


def should_return_201_when_email_invitation_succeeds(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    org = _org_record(id=org_id, display_name="ONF")
    invitation = _invitation_record(organisation_id=org_id, email_normalized="membre@example.fr")
    service.get_organisation.return_value = org
    service.invite_by_email.return_value = InvitationDelivery(
        invitation=invitation, token="a-token-value"
    )

    response = client.post(
        f"{_PREFIX}/{org_id}/invitations",
        json={"email": "membre@example.fr", "role": "member"},
        headers=_auth(),
    )

    assert response.status_code == 201
    assert response.json()["email"] == "membre@example.fr"


def should_return_403_when_email_invitation_insufficient_role(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    service.get_organisation.return_value = _org_record(id=org_id)
    service.invite_by_email.side_effect = InsufficientRoleError("role manquant")

    response = client.post(
        f"{_PREFIX}/{org_id}/invitations",
        json={"email": "membre@example.fr", "role": "member"},
        headers=_auth(),
    )

    assert response.status_code == 403


def should_return_404_when_email_invitation_organisation_not_found(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    service.get_organisation.side_effect = OrganisationNotFoundError(str(org_id))

    response = client.post(
        f"{_PREFIX}/{org_id}/invitations",
        json={"email": "membre@example.fr", "role": "member"},
        headers=_auth(),
    )

    assert response.status_code == 404


def should_return_503_when_email_invitation_delivery_fails(
    mock_lifespan: object,
) -> None:
    from fastapi.testclient import TestClient

    del mock_lifespan
    app = create_app()
    service = AsyncMock(spec=OrganisationService)
    org_id = uuid4()
    org = _org_record(id=org_id, display_name="ONF")
    invitation = _invitation_record(organisation_id=org_id, email_normalized="membre@example.fr")
    service.get_organisation.return_value = org
    service.invite_by_email.return_value = InvitationDelivery(
        invitation=invitation, token="a-token-value"
    )
    app.dependency_overrides[get_organisation_service] = lambda: service
    failing_sender = FakeEmailSender()
    failing_sender.should_deliver = False
    app.dependency_overrides[get_transactional_email_sender] = lambda: failing_sender

    with TestClient(app) as client:
        response = client.post(
            f"{_PREFIX}/{org_id}/invitations",
            json={"email": "membre@example.fr", "role": "member"},
            headers=_auth(),
        )

    assert response.status_code == 503


# ---------------------------------------------------------------------------
# POST /orgs/invitations/accept — accept_email_invitation
# ---------------------------------------------------------------------------


def should_return_200_when_accept_invitation_succeeds(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    account_id = uuid4()
    service.accept_invitation.return_value = _member_record(account_id=account_id)

    response = client.post(
        f"{_PREFIX}/invitations/accept",
        json={"token": "a" * 32},
        headers=_auth(account_id),
    )

    assert response.status_code == 200
    assert response.json()["account_id"] == str(account_id)


def should_return_404_when_accept_invitation_invalid(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    service.accept_invitation.side_effect = InvitationInvalidError()

    response = client.post(
        f"{_PREFIX}/invitations/accept",
        json={"token": "a" * 32},
        headers=_auth(),
    )

    assert response.status_code == 404


def should_return_403_when_accept_invitation_email_mismatch(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    service.accept_invitation.side_effect = InvitationEmailMismatchError()

    response = client.post(
        f"{_PREFIX}/invitations/accept",
        json={"token": "a" * 32},
        headers=_auth(),
    )

    assert response.status_code == 403


def should_return_409_when_accept_invitation_already_member(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    service.accept_invitation.side_effect = AlreadyMemberError("déjà membre")

    response = client.post(
        f"{_PREFIX}/invitations/accept",
        json={"token": "a" * 32},
        headers=_auth(),
    )

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# GET /orgs/{org_id}/members — list_members
# ---------------------------------------------------------------------------


def should_return_200_when_list_members(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    service.list_members.return_value = ([_member_record(organisation_id=org_id)], 1)

    response = client.get(f"{_PREFIX}/{org_id}/members", headers=_auth())

    assert response.status_code == 200
    assert response.json()["total"] == 1


# ---------------------------------------------------------------------------
# DELETE /orgs/{org_id}/members/{account_id} — revoke_member
# ---------------------------------------------------------------------------


def should_return_200_when_revoke_member_succeeds(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    account_id = uuid4()
    service.revoke_member.return_value = _member_record(
        organisation_id=org_id, account_id=account_id, revoked_at=datetime.now(UTC)
    )

    response = client.delete(f"{_PREFIX}/{org_id}/members/{account_id}", headers=_auth())

    assert response.status_code == 200
    assert response.json()["revoked_at"] is not None


def should_return_403_when_revoke_member_insufficient_role(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    account_id = uuid4()
    service.revoke_member.side_effect = InsufficientRoleError("role manquant")

    response = client.delete(f"{_PREFIX}/{org_id}/members/{account_id}", headers=_auth())

    assert response.status_code == 403


def should_return_403_when_revoke_member_last_owner(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    account_id = uuid4()
    service.revoke_member.side_effect = LastOwnerError("dernier owner")

    response = client.delete(f"{_PREFIX}/{org_id}/members/{account_id}", headers=_auth())

    assert response.status_code == 403


def should_return_404_when_revoke_member_not_member(
    app_and_service: tuple[TestClient, AsyncMock],
) -> None:
    client, service = app_and_service
    org_id = uuid4()
    account_id = uuid4()
    service.revoke_member.side_effect = NotMemberError(str(account_id))

    response = client.delete(f"{_PREFIX}/{org_id}/members/{account_id}", headers=_auth())

    assert response.status_code == 404

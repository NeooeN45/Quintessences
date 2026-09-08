"""INV-003 — une resource soft-deleted ne réapparaît pas par le CRUD public."""

from collections.abc import AsyncGenerator
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.infrastructure.database import get_db
from gsie_api.resources.service import ResourceService
from tests.conftest import requires_docker

pytestmark = requires_docker


@pytest.fixture
def admin_headers() -> dict[str, str]:
    token = create_access_token(
        subject="soft-delete-auditor",
        claims={"roles": ["admin"]},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_soft_delete_disparait_du_get_de_la_liste_et_de_update(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    cree = await client.post(
        "/api/v1/resources",
        json={"type": "entity", "data": {"entity_subtype": "soft-delete-proof"}},
        headers=admin_headers,
    )
    assert cree.status_code == 201, cree.text
    resource_id = cree.json()["id"]

    supprime = await client.delete(
        f"/api/v1/resources/{resource_id}",
        params={"justification": "preuve INV-003"},
        headers=admin_headers,
    )
    assert supprime.status_code == 204, supprime.text

    relu = await client.get(
        f"/api/v1/resources/{resource_id}",
        headers=admin_headers,
    )
    assert relu.status_code == 404, relu.text

    liste = await client.get(
        "/api/v1/resources",
        params={"type": "entity", "size": 100},
        headers=admin_headers,
    )
    assert liste.status_code == 200, liste.text
    ids = {item["id"] for item in liste.json()["items"]}
    assert resource_id not in ids

    maj = await client.put(
        f"/api/v1/resources/{resource_id}",
        json={
            "data": {"entity_subtype": "ressuscitee"},
            "justification": "ne doit jamais réussir",
        },
        headers=admin_headers,
    )
    assert maj.status_code == 404, maj.text


@pytest.mark.asyncio
async def test_soft_delete_conserve_la_revision_finale(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_headers: dict[str, str],
) -> None:
    cree = await client.post(
        "/api/v1/resources",
        json={"type": "entity", "data": {"entity_subtype": "historique"}},
        headers=admin_headers,
    )
    assert cree.status_code == 201, cree.text
    resource_id = UUID(cree.json()["id"])

    supprime = await client.delete(
        f"/api/v1/resources/{resource_id}",
        params={"justification": "archivage terrain"},
        headers=admin_headers,
    )
    assert supprime.status_code == 204, supprime.text

    revisions = await ResourceService(db_session).list_revisions(resource_id)
    assert len(revisions) == 2
    assert revisions[0].version == 2
    assert revisions[0].justification == "[DELETED] archivage terrain"

"""Tests unitaires du service audit (domain layer).

Testé avec un dépôt mémoire — aucune dépendance SQLAlchemy ni FastAPI.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from gsie_api.audit.router import get_audit_service
from gsie_api.audit.service import AuditEntry, AuditService

# --- Fake repository ---


class FakeAuditRepository:
    """Dépôt mémoire pour tests unitaires du service audit."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    async def insert(self, entry: AuditEntry) -> AuditEntry:
        self._entries.append(entry)
        return entry

    async def list_entries(
        self,
        *,
        actor_id: UUID | None = None,
        resource_type: str | None = None,
        action: str | None = None,
        organisation_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditEntry], int]:
        filtered = self._entries
        if actor_id is not None:
            filtered = [e for e in filtered if e.actor_id == actor_id]
        if resource_type is not None:
            filtered = [e for e in filtered if e.resource_type == resource_type]
        if action is not None:
            filtered = [e for e in filtered if e.action == action]
        if organisation_id is not None:
            filtered = [e for e in filtered if e.organisation_id == organisation_id]
        return filtered[offset : offset + limit], len(filtered)


# --- Helpers ---


def _make_entry(**overrides: object) -> AuditEntry:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "timestamp": datetime.now(UTC),
        "actor_id": uuid4(),
        "actor_email": "test@example.com",
        "action": "create",
        "resource_type": "resource",
        "resource_id": "res-001",
        "ip_address": "127.0.0.1",
        "user_agent": "test-agent",
        "organisation_id": None,
        "workspace_id": None,
        "status_code": 201,
        "method": "POST",
        "path": "/api/v1/resources",
        "details": {},
        "trace_id": None,
    }
    defaults.update(overrides)
    return AuditEntry(**defaults)  # type: ignore[arg-type]


# --- Tests ---


@pytest.fixture()
def repo() -> FakeAuditRepository:
    return FakeAuditRepository()


@pytest.fixture()
def service(repo: FakeAuditRepository) -> AuditService:
    return AuditService(repo)


@pytest.mark.asyncio
async def test_log_inserts_entry(
    repo: FakeAuditRepository,
    service: AuditService,
) -> None:
    entry = _make_entry()

    result = await service.log(entry)

    assert result.id == entry.id
    assert len(repo._entries) == 1


@pytest.mark.asyncio
async def test_list_returns_all_entries(
    repo: FakeAuditRepository,
    service: AuditService,
) -> None:
    await service.log(_make_entry())
    await service.log(_make_entry())
    await service.log(_make_entry())

    entries, total = await service.list(page=1, size=10)

    assert total == 3
    assert len(entries) == 3


@pytest.mark.asyncio
async def test_list_filters_by_actor(
    repo: FakeAuditRepository,
    service: AuditService,
) -> None:
    actor1 = uuid4()
    actor2 = uuid4()
    await service.log(_make_entry(actor_id=actor1))
    await service.log(_make_entry(actor_id=actor1))
    await service.log(_make_entry(actor_id=actor2))

    entries, total = await service.list(actor_id=actor1, page=1, size=10)

    assert total == 2
    assert all(e.actor_id == actor1 for e in entries)


@pytest.mark.asyncio
async def test_list_filters_by_resource_type(
    repo: FakeAuditRepository,
    service: AuditService,
) -> None:
    await service.log(_make_entry(resource_type="resource"))
    await service.log(_make_entry(resource_type="organisation"))
    await service.log(_make_entry(resource_type="resource"))

    entries, total = await service.list(resource_type="resource", page=1, size=10)

    assert total == 2
    assert all(e.resource_type == "resource" for e in entries)


@pytest.mark.asyncio
async def test_list_filters_by_action(
    repo: FakeAuditRepository,
    service: AuditService,
) -> None:
    await service.log(_make_entry(action="create"))
    await service.log(_make_entry(action="delete"))
    await service.log(_make_entry(action="create"))

    entries, total = await service.list(action="create", page=1, size=10)

    assert total == 2
    assert all(e.action == "create" for e in entries)


@pytest.mark.asyncio
async def test_list_paginates(
    repo: FakeAuditRepository,
    service: AuditService,
) -> None:
    for _ in range(15):
        await service.log(_make_entry())

    page1, total1 = await service.list(page=1, size=10)
    page2, total2 = await service.list(page=2, size=10)

    assert total1 == 15
    assert len(page1) == 10
    assert total2 == 15
    assert len(page2) == 5


@pytest.mark.asyncio
async def test_list_filters_by_organisation(
    repo: FakeAuditRepository,
    service: AuditService,
) -> None:
    org1 = uuid4()
    org2 = uuid4()
    await service.log(_make_entry(organisation_id=org1))
    await service.log(_make_entry(organisation_id=org2))
    await service.log(_make_entry(organisation_id=org1))

    entries, total = await service.list(organisation_id=org1, page=1, size=10)

    assert total == 2
    assert all(e.organisation_id == org1 for e in entries)


@pytest.mark.asyncio
async def test_get_audit_service_dependency_returns_service() -> None:
    """La dépendance FastAPI doit retourner un AuditService encapsulant la session."""
    session = AsyncMock()
    service = await get_audit_service(session)  # type: ignore[arg-type]

    assert isinstance(service, AuditService)
    assert service._repository._session is session

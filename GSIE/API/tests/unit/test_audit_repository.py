"""Tests unitaires — SqlAlchemyAuditRepository (dépôt SQLAlchemy audit_log).

La session AsyncSession est mockée — pas de connexion DB réelle. Les
modèles ``AuditLogModel`` sont instanciés directement (SQLAlchemy ORM
permet la construction sans connexion).

Conventions (AGENTS.md API) : pytest-asyncio mode ``auto``, nommage
``should_[expected]_when_[condition]``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from gsie_api.audit.repository import SqlAlchemyAuditRepository
from gsie_api.audit.service import AuditEntry
from gsie_api.infrastructure.models.audit_log import AuditLogModel


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


def _make_model(**overrides: object) -> AuditLogModel:
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
    return AuditLogModel(**defaults)  # type: ignore[arg-type]


def _mock_session() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    return session


class TestInsert:
    async def should_add_model_and_flush_when_inserting_entry(self) -> None:
        session = _mock_session()
        repository = SqlAlchemyAuditRepository(session)
        entry = _make_entry()

        result = await repository.insert(entry)

        session.add.assert_called_once()
        added_model = session.add.call_args.args[0]
        assert isinstance(added_model, AuditLogModel)
        assert added_model.id == entry.id
        assert added_model.action == entry.action
        session.flush.assert_awaited_once()
        assert result.id == entry.id
        assert result.action == entry.action
        assert result.details == entry.details

    async def should_round_trip_optional_fields_when_none(self) -> None:
        session = _mock_session()
        repository = SqlAlchemyAuditRepository(session)
        entry = _make_entry(
            actor_id=None,
            actor_email=None,
            resource_id=None,
            ip_address=None,
            user_agent=None,
            organisation_id=None,
            workspace_id=None,
            status_code=None,
            method=None,
            path=None,
            trace_id=None,
        )

        result = await repository.insert(entry)

        assert result.actor_id is None
        assert result.organisation_id is None
        assert result.trace_id is None


class TestListEntries:
    async def should_apply_no_filters_by_default(self) -> None:
        session = _mock_session()
        session.scalar = AsyncMock(return_value=0)
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=execute_result)
        repository = SqlAlchemyAuditRepository(session)

        entries, total = await repository.list_entries()

        assert entries == []
        assert total == 0

    async def should_filter_by_actor_resource_action_and_organisation(self) -> None:
        session = _mock_session()
        session.scalar = AsyncMock(return_value=1)
        model = _make_model()
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = [model]
        session.execute = AsyncMock(return_value=execute_result)
        repository = SqlAlchemyAuditRepository(session)

        actor_id = uuid4()
        organisation_id = uuid4()

        entries, total = await repository.list_entries(
            actor_id=actor_id,
            resource_type="resource",
            action="create",
            organisation_id=organisation_id,
            offset=5,
            limit=10,
        )

        assert total == 1
        assert len(entries) == 1
        assert entries[0].id == model.id
        assert entries[0].details == {}
        session.scalar.assert_awaited_once()
        session.execute.assert_awaited_once()

    async def should_default_total_to_zero_when_scalar_returns_none(self) -> None:
        session = _mock_session()
        session.scalar = AsyncMock(return_value=None)
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=execute_result)
        repository = SqlAlchemyAuditRepository(session)

        _entries, total = await repository.list_entries()

        assert total == 0

    async def should_convert_model_details_to_plain_dict(self) -> None:
        session = _mock_session()
        session.scalar = AsyncMock(return_value=1)
        model = _make_model(details={"foo": "bar"})
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = [model]
        session.execute = AsyncMock(return_value=execute_result)
        repository = SqlAlchemyAuditRepository(session)

        entries, _total = await repository.list_entries()

        assert entries[0].details == {"foo": "bar"}
        assert type(entries[0].details) is dict

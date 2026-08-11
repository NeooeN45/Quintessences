"""Tests unitaires — SqlAlchemyGeoSylvaParcelRepository (dépôt sync GeoSylva).

La session AsyncSession est mockée — pas de connexion DB réelle
(voir tests/integration/test_geosylva_sync_repository.py pour la
persistance réelle et le cloisonnement inter-comptes).

Conventions (AGENTS.md API) : pytest-asyncio mode ``auto``, nommage
``should_[expected]_when_[condition]``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from gsie_api.infrastructure.models.sync import GeoSylvaParcelSyncModel
from gsie_api.sync.geosylva import GeoSylvaParcelRecord
from gsie_api.sync.repository import SqlAlchemyGeoSylvaParcelRepository


def _make_record(**overrides: object) -> GeoSylvaParcelRecord:
    now = datetime(2026, 8, 3, 10, 0, tzinfo=UTC)
    defaults: dict[str, object] = {
        "account_id": uuid4(),
        "client_id": "parcelle-1",
        "payload": {"name": "Parcelle test"},
        "client_updated_at": now,
        "version": 1,
        "last_operation_id": uuid4(),
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    defaults.update(overrides)
    return GeoSylvaParcelRecord(**defaults)  # type: ignore[arg-type]


def _make_model(**overrides: object) -> GeoSylvaParcelSyncModel:
    now = datetime(2026, 8, 3, 10, 0, tzinfo=UTC)
    defaults: dict[str, object] = {
        "account_id": uuid4(),
        "client_id": "parcelle-1",
        "payload": {"name": "Parcelle test"},
        "client_updated_at": now,
        "server_version": 1,
        "last_operation_id": uuid4(),
        "deleted_at": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return GeoSylvaParcelSyncModel(**defaults)  # type: ignore[arg-type]


def _mock_session() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    return session


class TestGetForUpdate:
    async def should_take_advisory_lock_then_return_none_when_absent(self) -> None:
        session = _mock_session()
        lock_result = MagicMock()
        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(side_effect=[lock_result, select_result])
        repository = SqlAlchemyGeoSylvaParcelRepository(session)

        record = await repository.get_for_update(uuid4(), "parcelle-1")

        assert record is None
        assert session.execute.await_count == 2
        lock_call = session.execute.await_args_list[0]
        assert "pg_advisory_xact_lock" in lock_call.args[0].text

    async def should_return_record_when_model_found(self) -> None:
        session = _mock_session()
        model = _make_model()
        lock_result = MagicMock()
        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = model
        session.execute = AsyncMock(side_effect=[lock_result, select_result])
        repository = SqlAlchemyGeoSylvaParcelRepository(session)

        record = await repository.get_for_update(model.account_id, model.client_id)

        assert record is not None
        assert record.account_id == model.account_id
        assert record.client_id == model.client_id
        assert record.version == model.server_version


class TestSave:
    async def should_insert_new_model_when_not_found(self) -> None:
        session = _mock_session()
        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=select_result)

        async def _refresh(model: GeoSylvaParcelSyncModel) -> None:
            del model

        session.refresh = AsyncMock(side_effect=_refresh)
        repository = SqlAlchemyGeoSylvaParcelRepository(session)
        record = _make_record()

        result = await repository.save(record)

        session.add.assert_called_once()
        added = session.add.call_args.args[0]
        assert added.account_id == record.account_id
        assert added.client_id == record.client_id
        session.flush.assert_awaited_once()
        session.refresh.assert_awaited_once()
        assert result.client_id == record.client_id
        assert result.version == record.version

    async def should_update_existing_model_when_found(self) -> None:
        session = _mock_session()
        existing = _make_model()
        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = existing
        session.execute = AsyncMock(return_value=select_result)
        session.refresh = AsyncMock()
        repository = SqlAlchemyGeoSylvaParcelRepository(session)
        record = _make_record(
            account_id=existing.account_id,
            client_id=existing.client_id,
            payload={"name": "Parcelle mise à jour"},
            version=2,
        )

        result = await repository.save(record)

        session.add.assert_not_called()
        assert existing.payload == {"name": "Parcelle mise à jour"}
        assert existing.server_version == 2
        session.flush.assert_awaited_once()
        assert result.version == 2


class TestListForAccount:
    async def should_return_records_and_total_count(self) -> None:
        session = _mock_session()
        session.scalar = AsyncMock(return_value=2)
        model = _make_model()
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = [model]
        session.execute = AsyncMock(return_value=execute_result)
        repository = SqlAlchemyGeoSylvaParcelRepository(session)

        records, total = await repository.list_for_account(model.account_id, offset=0, limit=50)

        assert total == 2
        assert len(records) == 1
        assert records[0].client_id == model.client_id

    async def should_default_total_to_zero_when_scalar_returns_none(self) -> None:
        session = _mock_session()
        session.scalar = AsyncMock(return_value=None)
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=execute_result)
        repository = SqlAlchemyGeoSylvaParcelRepository(session)

        records, total = await repository.list_for_account(uuid4(), offset=0, limit=50)

        assert records == []
        assert total == 0

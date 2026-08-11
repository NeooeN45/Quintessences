"""Règles métier de la synchronisation de parcelles GeoSylva."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from gsie_api.sync.geosylva import (
    GeoSylvaParcelMutation,
    GeoSylvaParcelRecord,
    GeoSylvaSyncConflictError,
    GeoSylvaSyncService,
)


class MemoryParcelRepository:
    """Double strict : chaque compte possède son propre espace de parcelles."""

    def __init__(self) -> None:
        self.records: dict[tuple[UUID, str], GeoSylvaParcelRecord] = {}

    async def get_for_update(self, account_id: UUID, client_id: str) -> GeoSylvaParcelRecord | None:
        return self.records.get((account_id, client_id))

    async def save(self, record: GeoSylvaParcelRecord) -> GeoSylvaParcelRecord:
        self.records[(record.account_id, record.client_id)] = record
        return record

    async def list_for_account(
        self,
        account_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[GeoSylvaParcelRecord], int]:
        records = [record for (owner, _), record in self.records.items() if owner == account_id]
        records.sort(key=lambda item: item.client_id)
        return records[offset : offset + limit], len(records)


def _mutation(*, operation_id: UUID | None = None, base_version: int | None = None):
    return GeoSylvaParcelMutation(
        operation_id=operation_id or uuid4(),
        base_version=base_version,
        client_updated_at=datetime(2026, 8, 3, 10, 0, tzinfo=UTC),
        payload={"name": "Parcelle test", "surface_ha": 12.5},
    )


async def should_create_then_replay_same_operation_without_incrementing_version() -> None:
    repository = MemoryParcelRepository()
    service = GeoSylvaSyncService(repository)
    account_id = uuid4()
    mutation = _mutation()

    first = await service.upsert(account_id, "parcelle-1", mutation)
    replay = await service.upsert(account_id, "parcelle-1", mutation)

    assert first.version == 1
    assert replay.version == 1
    assert replay.last_operation_id == mutation.operation_id


async def should_reject_stale_version_without_overwriting_server_payload() -> None:
    repository = MemoryParcelRepository()
    service = GeoSylvaSyncService(repository)
    account_id = uuid4()
    current = await service.upsert(account_id, "parcelle-1", _mutation())

    with pytest.raises(GeoSylvaSyncConflictError) as captured:
        await service.upsert(account_id, "parcelle-1", _mutation(base_version=None))

    assert captured.value.current.version == current.version
    assert captured.value.current.payload["name"] == "Parcelle test"


async def should_keep_tombstone_and_isolate_same_client_id_between_accounts() -> None:
    repository = MemoryParcelRepository()
    service = GeoSylvaSyncService(repository)
    account_a = uuid4()
    account_b = uuid4()
    record_a = await service.upsert(account_a, "parcelle-1", _mutation())
    await service.upsert(account_b, "parcelle-1", _mutation())

    deleted = await service.delete(
        account_a,
        "parcelle-1",
        operation_id=uuid4(),
        base_version=record_a.version,
        client_updated_at=datetime(2026, 8, 3, 11, 0, tzinfo=UTC),
    )
    rows_a, _ = await service.list(account_a, page=1, size=50)
    rows_b, _ = await service.list(account_b, page=1, size=50)

    assert deleted.deleted_at is not None
    assert deleted.version == 2
    assert rows_a[0].deleted_at is not None
    assert rows_b[0].deleted_at is None


async def should_reject_upsert_with_base_version_when_no_record_exists() -> None:
    repository = MemoryParcelRepository()
    service = GeoSylvaSyncService(repository)
    account_id = uuid4()

    with pytest.raises(GeoSylvaSyncConflictError) as captured:
        await service.upsert(account_id, "parcelle-1", _mutation(base_version=3))

    assert captured.value.current is None


async def should_apply_update_when_base_version_matches_current() -> None:
    repository = MemoryParcelRepository()
    service = GeoSylvaSyncService(repository)
    account_id = uuid4()
    current = await service.upsert(account_id, "parcelle-1", _mutation())

    updated = await service.upsert(
        account_id,
        "parcelle-1",
        GeoSylvaParcelMutation(
            operation_id=uuid4(),
            base_version=current.version,
            client_updated_at=datetime(2026, 8, 3, 11, 0, tzinfo=UTC),
            payload={"name": "Parcelle mise à jour"},
        ),
    )

    assert updated.version == current.version + 1
    assert updated.payload["name"] == "Parcelle mise à jour"


async def should_replay_delete_without_incrementing_version() -> None:
    repository = MemoryParcelRepository()
    service = GeoSylvaSyncService(repository)
    account_id = uuid4()
    current = await service.upsert(account_id, "parcelle-1", _mutation())
    operation_id = uuid4()

    first = await service.delete(
        account_id,
        "parcelle-1",
        operation_id=operation_id,
        base_version=current.version,
        client_updated_at=datetime(2026, 8, 3, 11, 0, tzinfo=UTC),
    )
    replay = await service.delete(
        account_id,
        "parcelle-1",
        operation_id=operation_id,
        base_version=current.version,
        client_updated_at=datetime(2026, 8, 3, 11, 0, tzinfo=UTC),
    )

    assert first.version == replay.version == 2
    assert replay.last_operation_id == operation_id


async def should_create_tombstone_when_deleting_absent_record_without_base_version() -> None:
    repository = MemoryParcelRepository()
    service = GeoSylvaSyncService(repository)
    account_id = uuid4()

    tombstone = await service.delete(
        account_id,
        "parcelle-inconnue",
        operation_id=uuid4(),
        base_version=None,
        client_updated_at=datetime(2026, 8, 3, 11, 0, tzinfo=UTC),
    )

    assert tombstone.deleted_at is not None
    assert tombstone.version == 1


async def should_reject_delete_with_base_version_when_no_record_exists() -> None:
    repository = MemoryParcelRepository()
    service = GeoSylvaSyncService(repository)
    account_id = uuid4()

    with pytest.raises(GeoSylvaSyncConflictError) as captured:
        await service.delete(
            account_id,
            "parcelle-inconnue",
            operation_id=uuid4(),
            base_version=2,
            client_updated_at=datetime(2026, 8, 3, 11, 0, tzinfo=UTC),
        )

    assert captured.value.current is None


async def should_reject_delete_when_base_version_mismatches_current() -> None:
    repository = MemoryParcelRepository()
    service = GeoSylvaSyncService(repository)
    account_id = uuid4()
    current = await service.upsert(account_id, "parcelle-1", _mutation())

    with pytest.raises(GeoSylvaSyncConflictError) as captured:
        await service.delete(
            account_id,
            "parcelle-1",
            operation_id=uuid4(),
            base_version=current.version + 5,
            client_updated_at=datetime(2026, 8, 3, 11, 0, tzinfo=UTC),
        )

    assert captured.value.current.version == current.version

"""Premières propriétés transversales — ticket #39, INV-004/005/008."""

import asyncio
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.resources.router import _extract_author_id
from gsie_api.resources.service import ResourceService
from gsie_api.sync.geosylva import (
    GeoSylvaParcelMutation,
    GeoSylvaParcelRecord,
    GeoSylvaSyncConflictError,
    GeoSylvaSyncService,
)


class MemoryParcelRepository:
    """Dépôt déterministe minimal pour éprouver les règles de sync sans I/O."""

    def __init__(self) -> None:
        self.rows: dict[tuple[UUID, str], GeoSylvaParcelRecord] = {}

    async def get_for_update(
        self,
        account_id: UUID,
        client_id: str,
    ) -> GeoSylvaParcelRecord | None:
        return self.rows.get((account_id, client_id))

    async def save(self, record: GeoSylvaParcelRecord) -> GeoSylvaParcelRecord:
        self.rows[(record.account_id, record.client_id)] = record
        return record

    async def list_for_account(
        self,
        account_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[GeoSylvaParcelRecord], int]:
        rows = [row for (owner, _), row in self.rows.items() if owner == account_id]
        return rows[offset : offset + limit], len(rows)


json_scalar = st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=50))
payloads = st.dictionaries(st.text(min_size=1, max_size=20), json_scalar, max_size=8)
client_ids = st.text(min_size=1, max_size=40).filter(lambda value: value.strip() != "")


@settings(max_examples=80, deadline=None)
@given(
    forbidden_value=json_scalar,
    safe_value=json_scalar,
)
def test_mass_assignment_ne_laisse_jamais_passer_deleted_at(
    forbidden_value: Any,
    safe_value: Any,
) -> None:
    service = ResourceService(cast(AsyncSession, None))
    filtered = service._filter_data(
        ResourceModel,
        {"deleted_at": forbidden_value, "metadata_json": {"value": safe_value}},
    )

    assert "deleted_at" not in filtered
    assert "metadata_json" in filtered


@settings(max_examples=80, deadline=None)
@given(subject=st.text(min_size=1, max_size=80))
def test_identite_auteur_est_deterministe(subject: str) -> None:
    first = _extract_author_id({"sub": subject})
    second = _extract_author_id({"sub": subject})

    assert first is not None
    assert first == second


@settings(max_examples=60, deadline=None)
@given(
    account_id=st.uuids(),
    operation_id=st.uuids(),
    client_id=client_ids,
    payload=payloads,
)
def test_replay_operation_geosylva_est_idempotent(
    account_id: UUID,
    operation_id: UUID,
    client_id: str,
    payload: dict[str, Any],
) -> None:
    async def scenario() -> tuple[GeoSylvaParcelRecord, GeoSylvaParcelRecord]:
        service = GeoSylvaSyncService(MemoryParcelRepository())
        mutation = GeoSylvaParcelMutation(
            operation_id=operation_id,
            base_version=None,
            client_updated_at=datetime(2026, 9, 8, 12, 0, tzinfo=UTC),
            payload=payload,
        )
        first = await service.upsert(account_id, client_id, mutation)
        second = await service.upsert(account_id, client_id, mutation)
        return first, second

    first, second = asyncio.run(scenario())
    assert second == first
    assert second.version == 1
    assert second.last_operation_id == operation_id


@settings(max_examples=60, deadline=None)
@given(
    account_id=st.uuids(),
    first_operation=st.uuids(),
    second_operation=st.uuids(),
    client_id=client_ids,
    payload=payloads,
    stale_version=st.integers(min_value=-100, max_value=100).filter(lambda value: value != 1),
)
def test_version_obsolete_geosylva_est_un_conflit_explicite(
    account_id: UUID,
    first_operation: UUID,
    second_operation: UUID,
    client_id: str,
    payload: dict[str, Any],
    stale_version: int,
) -> None:
    async def scenario() -> None:
        service = GeoSylvaSyncService(MemoryParcelRepository())
        current = await service.upsert(
            account_id,
            client_id,
            GeoSylvaParcelMutation(
                first_operation,
                None,
                datetime(2026, 9, 8, 12, 0, tzinfo=UTC),
                payload,
            ),
        )
        with pytest.raises(GeoSylvaSyncConflictError) as exc_info:
            await service.upsert(
                account_id,
                client_id,
                GeoSylvaParcelMutation(
                    second_operation,
                    stale_version,
                    datetime(2026, 9, 8, 12, 1, tzinfo=UTC),
                    payload,
                ),
            )
        assert exc_info.value.current == current

    asyncio.run(scenario())


@settings(max_examples=60, deadline=None)
@given(
    account_a=st.uuids(),
    account_b=st.uuids(),
    client_id=client_ids,
    payload_a=payloads,
    payload_b=payloads,
)
def test_meme_client_id_ne_melange_jamais_deux_comptes(
    account_a: UUID,
    account_b: UUID,
    client_id: str,
    payload_a: dict[str, Any],
    payload_b: dict[str, Any],
) -> None:
    if account_a == account_b:
        return

    async def scenario() -> tuple[GeoSylvaParcelRecord, GeoSylvaParcelRecord]:
        repo = MemoryParcelRepository()
        service = GeoSylvaSyncService(repo)
        now = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
        await service.upsert(
            account_a,
            client_id,
            GeoSylvaParcelMutation(UUID(int=1), None, now, payload_a),
        )
        await service.upsert(
            account_b,
            client_id,
            GeoSylvaParcelMutation(UUID(int=2), None, now, payload_b),
        )
        rows_a, _ = await service.list(account_a, page=1, size=10)
        rows_b, _ = await service.list(account_b, page=1, size=10)
        return rows_a[0], rows_b[0]

    row_a, row_b = asyncio.run(scenario())
    assert row_a.account_id == account_a
    assert row_b.account_id == account_b
    assert row_a.payload == payload_a
    assert row_b.payload == payload_b

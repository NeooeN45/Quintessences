"""Tests unitaires — GeoSylvaCubageRepository (dépôt de sync cubage).

La session AsyncSession est mockée — pas de connexion DB réelle. Les cas
couverts visent la déduplication par ``session_id`` : la PK est globale et un
renvoi avec une nouvelle ``Idempotency-Key`` ne doit produire ni 500 ni
doublon.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from gsie_api.geosylva.cubage_repository import (
    CubageIdempotencyConflictError,
    GeoSylvaCubageRepository,
)
from gsie_api.geosylva.cubage_schemas import (
    CUBAGE_REQUEST_SCHEMA_VERSION,
    CubageSyncRequest,
    canonical_cubage_fingerprint,
)
from gsie_api.infrastructure.models.geosylva_cubage import GeoSylvaCubageSessionModel

if TYPE_CHECKING:
    from collections.abc import Coroutine


def _request(account_id: UUID, session_id: UUID) -> CubageSyncRequest:
    payload = {
        "schema_version": CUBAGE_REQUEST_SCHEMA_VERSION,
        "session": {
            "session_id": str(session_id),
            "owner_account_id": str(account_id),
            "station_id": "parcelle-01",
            "geometry": {"type": "Point", "coordinates": [2.35, 48.85]},
            "purpose": "commercial",
            "created_at": "2026-08-31T10:00:00Z",
            "updated_at": "2026-08-31T10:05:00Z",
            "revision": 1,
            "sync_state": "LOCAL_CALCULATED",
            "session_fingerprint": "a" * 64,
        },
        "measurements": {
            "items": [{"id": "m1", "type": "diameter", "value": 40, "unit": "cm"}],
            "canonical_units": "SI",
            "measurements_fingerprint": "b" * 64,
        },
        "calculation": {
            "calculation_id": str(uuid4()),
            "engine": "geosylva.cubage",
            "engine_version": "3.1.0",
            "method_id": "LOG_HUBER",
            "method_version": "0.1.0",
            "parameters": {"length_m": 5, "diameter_mid_m": 0.4},
            "results": {"volume_m3": 0.6283185307},
            "units": {"volume": "m3_real"},
            "quality": {"status": "valid", "warnings": [], "uncertainty": {}},
            "basis": [],
            "inputs_fingerprint": "c" * 64,
            "result_fingerprint": "d" * 64,
            "calculated_at": "2026-08-31T10:05:00Z",
        },
        "client": {
            "application_id": "geosylva",
            "application_version": "3.1.0",
            "os_version": "Android",
            "locale": "fr-FR",
        },
    }
    return CubageSyncRequest.model_validate(payload)


def _result(value: object) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _mock_session() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.begin_nested = MagicMock()
    return session


def _call(
    repository: GeoSylvaCubageRepository,
    account_id: UUID,
    request: CubageSyncRequest,
) -> Coroutine[Any, Any, tuple[GeoSylvaCubageSessionModel, bool]]:
    return repository.create_or_get(
        account_id,
        request,
        idempotency_key=str(uuid4()),
        trace_id="trace-1",
        now=datetime(2026, 8, 31, 12, 0, tzinfo=UTC),
    )


async def should_replay_existing_record_when_session_resynced_with_new_key() -> None:
    account_id = uuid4()
    session_id = uuid4()
    request = _request(account_id, session_id)
    existing = GeoSylvaCubageSessionModel(
        session_id=session_id,
        account_id=account_id,
        request_fingerprint=canonical_cubage_fingerprint(request),
    )
    session = _mock_session()
    session.execute = AsyncMock(side_effect=[_result(None), _result(None)])
    session.get = AsyncMock(return_value=existing)

    model, created = await _call(GeoSylvaCubageRepository(session), account_id, request)

    assert model is existing
    assert created is False
    session.add.assert_not_called()


async def should_raise_conflict_when_session_resynced_with_different_payload() -> None:
    account_id = uuid4()
    session_id = uuid4()
    request = _request(account_id, session_id)
    existing = GeoSylvaCubageSessionModel(
        session_id=session_id,
        account_id=account_id,
        request_fingerprint="f" * 64,
    )
    session = _mock_session()
    session.execute = AsyncMock(side_effect=[_result(None), _result(None)])
    session.get = AsyncMock(return_value=existing)

    with pytest.raises(CubageIdempotencyConflictError, match="paquet différent"):
        await _call(GeoSylvaCubageRepository(session), account_id, request)


async def should_raise_conflict_when_session_belongs_to_another_account() -> None:
    account_id = uuid4()
    session_id = uuid4()
    request = _request(account_id, session_id)
    existing = GeoSylvaCubageSessionModel(
        session_id=session_id,
        account_id=uuid4(),
        request_fingerprint=canonical_cubage_fingerprint(request),
    )
    session = _mock_session()
    session.execute = AsyncMock(side_effect=[_result(None), _result(None)])
    session.get = AsyncMock(return_value=existing)

    with pytest.raises(CubageIdempotencyConflictError, match="déjà synchronisé"):
        await _call(GeoSylvaCubageRepository(session), account_id, request)


async def should_raise_conflict_when_insert_hits_a_unique_constraint() -> None:
    """Collision résiduelle : courses concurrentes ou session_id d'un autre
    compte invisible sous RLS — la contrainte DB reste l'arbitre final."""
    account_id = uuid4()
    request = _request(account_id, uuid4())
    session = _mock_session()
    session.execute = AsyncMock(side_effect=[_result(None), _result(None)])
    session.get = AsyncMock(return_value=None)
    session.flush = AsyncMock(
        side_effect=IntegrityError("INSERT INTO geosylva_cubage_session", {}, Exception("dup"))
    )

    with pytest.raises(CubageIdempotencyConflictError, match="déjà synchronisée"):
        await _call(GeoSylvaCubageRepository(session), account_id, request)

    session.begin_nested.assert_called_once()
    session.rollback.assert_not_called()

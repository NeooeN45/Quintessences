"""Contrat HTTP authentifié de la synchronisation cubage GeoSylva."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.geosylva.cubage_repository import CubageIdempotencyConflictError
from gsie_api.geosylva.cubage_schemas import (
    CUBAGE_REQUEST_SCHEMA_VERSION,
    CubageSessionResponse,
    CubageSyncRequest,
    CubageSyncResponse,
    CubageSyncStatus,
)
from gsie_api.geosylva.router import get_cubage_service

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def cubage_client(mock_lifespan: object) -> Generator[tuple[TestClient, AsyncMock], None, None]:
    del mock_lifespan
    app = create_app()
    service = AsyncMock()
    app.dependency_overrides[get_cubage_service] = lambda: service
    with TestClient(app) as client:
        yield client, service


def _authorization(account_id: object) -> dict[str, str]:
    token = create_access_token(subject=str(account_id), claims={"roles": ["user"]})
    return {"Authorization": f"Bearer {token}"}


def _payload(account_id: object) -> dict[str, object]:
    return {
        "schema_version": CUBAGE_REQUEST_SCHEMA_VERSION,
        "session": {
            "session_id": str(uuid4()),
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


def _sync_response(payload: CubageSyncRequest, *, trace_id: str = "trace-1") -> CubageSyncResponse:
    return CubageSyncResponse(
        session_id=payload.session.session_id,
        calculation_id=payload.calculation.calculation_id,
        status=CubageSyncStatus.synced,
        server_record_id=payload.session.session_id,
        server_verification_id=None,
        warnings=[],
        trace_id=trace_id,
    )


def should_sync_a_complete_session(cubage_client: tuple[TestClient, AsyncMock]) -> None:
    client, service = cubage_client
    account_id = uuid4()
    payload = _payload(account_id)
    idempotency_key = str(uuid4())
    request = CubageSyncRequest.model_validate(payload)
    service.synchronize.return_value = (_sync_response(request), True)

    response = client.post(
        "/api/v1/geosylva/cubage/sessions/sync",
        json=payload,
        headers={**_authorization(account_id), "Idempotency-Key": idempotency_key},
    )

    assert response.status_code == 200
    assert response.headers["Idempotency-Key"] == idempotency_key
    assert response.json()["status"] == "synced"
    service.synchronize.assert_awaited_once()


def should_return_403_when_packet_claims_another_owner(
    cubage_client: tuple[TestClient, AsyncMock],
) -> None:
    client, service = cubage_client
    payload = _payload(uuid4())  # owner_account_id différent du jeton

    response = client.post(
        "/api/v1/geosylva/cubage/sessions/sync",
        json=payload,
        headers={**_authorization(uuid4()), "Idempotency-Key": str(uuid4())},
    )

    assert response.status_code == 403
    service.synchronize.assert_not_awaited()


def should_return_409_when_idempotency_key_covers_a_different_packet(
    cubage_client: tuple[TestClient, AsyncMock],
) -> None:
    client, service = cubage_client
    account_id = uuid4()
    service.synchronize.side_effect = CubageIdempotencyConflictError("conflit")

    response = client.post(
        "/api/v1/geosylva/cubage/sessions/sync",
        json=_payload(account_id),
        headers={**_authorization(account_id), "Idempotency-Key": str(uuid4())},
    )

    assert response.status_code == 409


def should_return_session_when_owner_reads_it(
    cubage_client: tuple[TestClient, AsyncMock],
) -> None:
    client, service = cubage_client
    account_id = uuid4()
    request = CubageSyncRequest.model_validate(_payload(account_id))
    service.get_owned.return_value = CubageSessionResponse(
        session=request.session,
        measurements=request.measurements,
        calculation=request.calculation,
        trace_id="trace-1",
    )

    response = client.get(
        f"/api/v1/geosylva/cubage/sessions/{request.session.session_id}",
        headers=_authorization(account_id),
    )

    assert response.status_code == 200
    assert response.json()["session"]["session_id"] == str(request.session.session_id)


def should_return_404_when_session_is_absent_or_foreign(
    cubage_client: tuple[TestClient, AsyncMock],
) -> None:
    client, service = cubage_client
    service.get_owned.return_value = None

    response = client.get(
        f"/api/v1/geosylva/cubage/sessions/{uuid4()}",
        headers=_authorization(uuid4()),
    )

    assert response.status_code == 404


def should_require_authentication(cubage_client: tuple[TestClient, AsyncMock]) -> None:
    client, _service = cubage_client

    response = client.get(f"/api/v1/geosylva/cubage/sessions/{uuid4()}")

    assert response.status_code == 401

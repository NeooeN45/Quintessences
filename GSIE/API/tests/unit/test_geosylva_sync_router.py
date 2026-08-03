"""Contrat HTTP authentifié de la synchronisation GeoSylva."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.sync.geosylva import GeoSylvaParcelRecord, GeoSylvaSyncConflictError
from gsie_api.sync.router import get_geosylva_sync_service

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def sync_client(mock_lifespan: object) -> Generator[tuple[TestClient, AsyncMock], None, None]:
    del mock_lifespan
    app = create_app()
    service = AsyncMock()
    app.dependency_overrides[get_geosylva_sync_service] = lambda: service
    with TestClient(app) as client:
        yield client, service


def _authorization(account_id: object) -> dict[str, str]:
    token = create_access_token(subject=str(account_id), claims={"roles": ["user"]})
    return {"Authorization": f"Bearer {token}"}


def _record(account_id: object, *, version: int = 1) -> GeoSylvaParcelRecord:
    now = datetime(2026, 8, 3, 10, 0, tzinfo=UTC)
    return GeoSylvaParcelRecord(
        account_id=account_id,
        client_id="parcelle-1",
        payload={
            "name": "Parcelle test",
            "surface_ha": 12.5,
            "created_at_ms": 1_754_214_400_000,
            "updated_at_ms": 1_754_214_400_000,
        },
        client_updated_at=now,
        version=version,
        last_operation_id=uuid4(),
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


def should_require_access_token_and_derive_owner_from_jwt(
    sync_client: tuple[TestClient, AsyncMock],
) -> None:
    client, service = sync_client
    account_id = uuid4()
    service.upsert.return_value = _record(account_id)
    body = {
        "operation_id": str(uuid4()),
        "base_version": None,
        "client_updated_at": "2026-08-03T10:00:00Z",
        "parcel": {
            "name": "Parcelle test",
            "surface_ha": 12.5,
            "created_at_ms": 1_754_214_400_000,
            "updated_at_ms": 1_754_214_400_000,
        },
    }

    unauthorized = client.put("/api/v1/sync/geosylva/parcelles/parcelle-1", json=body)
    response = client.put(
        "/api/v1/sync/geosylva/parcelles/parcelle-1",
        headers=_authorization(account_id),
        json=body,
    )

    assert unauthorized.status_code == 401
    assert response.status_code == 200
    assert service.upsert.await_args.args[0] == account_id
    assert response.json()["server_version"] == 1


def should_return_current_snapshot_on_conflict(
    sync_client: tuple[TestClient, AsyncMock],
) -> None:
    client, service = sync_client
    account_id = uuid4()
    service.upsert.side_effect = GeoSylvaSyncConflictError(_record(account_id, version=4))

    response = client.put(
        "/api/v1/sync/geosylva/parcelles/parcelle-1",
        headers=_authorization(account_id),
        json={
            "operation_id": str(uuid4()),
            "base_version": 2,
            "client_updated_at": "2026-08-03T10:00:00Z",
            "parcel": {
                "name": "Version locale",
                "created_at_ms": 1_754_214_400_000,
                "updated_at_ms": 1_754_214_400_000,
            },
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "SYNC_VERSION_CONFLICT"
    assert response.json()["detail"]["current"]["server_version"] == 4


def should_reject_unknown_fields_and_naive_client_timestamp(
    sync_client: tuple[TestClient, AsyncMock],
) -> None:
    client, _service = sync_client
    headers = _authorization(uuid4())
    response = client.put(
        "/api/v1/sync/geosylva/parcelles/parcelle-1",
        headers=headers,
        json={
            "operation_id": str(uuid4()),
            "client_updated_at": "2026-08-03T10:00:00",
            "parcel": {
                "name": "Parcelle",
                "created_at_ms": 1_754_214_400_000,
                "updated_at_ms": 1_754_214_400_000,
                "champ_inconnu": "non",
            },
        },
    )

    assert response.status_code == 422

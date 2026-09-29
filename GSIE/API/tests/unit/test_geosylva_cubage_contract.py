"""Contrat V1 du cubage offline-first GeoSylva."""

from __future__ import annotations

from uuid import uuid4

import pytest

from gsie_api.geosylva.cubage_schemas import (
    CUBAGE_REQUEST_SCHEMA_VERSION,
    CubageSyncRequest,
    canonical_cubage_fingerprint,
)


def _payload() -> dict[str, object]:
    session_id = uuid4()
    calculation_id = uuid4()
    return {
        "schema_version": CUBAGE_REQUEST_SCHEMA_VERSION,
        "session": {
            "session_id": str(session_id),
            "owner_account_id": str(uuid4()),
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
            "calculation_id": str(calculation_id),
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


def should_accept_a_complete_local_calculation() -> None:
    request = CubageSyncRequest.model_validate(_payload())

    assert request.schema_version == CUBAGE_REQUEST_SCHEMA_VERSION
    assert request.session.sync_state == "LOCAL_CALCULATED"
    assert request.calculation.method_id == "LOG_HUBER"


def should_produce_the_same_fingerprint_when_json_order_changes() -> None:
    first_payload = _payload()
    first = CubageSyncRequest.model_validate(first_payload)
    second_payload = dict(first_payload)
    calculation = first_payload["calculation"]
    assert isinstance(calculation, dict)
    second_payload["calculation"] = dict(reversed(list(calculation.items())))
    second = CubageSyncRequest.model_validate(second_payload)

    assert canonical_cubage_fingerprint(first) == canonical_cubage_fingerprint(second)


def should_reject_an_invalid_fingerprint() -> None:
    payload = _payload()
    measurements = payload["measurements"]
    assert isinstance(measurements, dict)
    measurements["measurements_fingerprint"] = "invalid"

    with pytest.raises(ValueError, match="empreinte"):
        CubageSyncRequest.model_validate(payload)

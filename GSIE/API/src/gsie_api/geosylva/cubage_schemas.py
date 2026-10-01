"""Schémas V1 du cubage offline-first GeoSylva–GSIE."""

# ruff: noqa: TC003

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from gsie_api.geosylva.schemas import GeoSylvaModel

CUBAGE_REQUEST_SCHEMA_VERSION: Literal["geosylva.cubage.sync.request.v1"] = (
    "geosylva.cubage.sync.request.v1"
)
CUBAGE_RESPONSE_SCHEMA_VERSION: Literal["geosylva.cubage.sync.response.v1"] = (
    "geosylva.cubage.sync.response.v1"
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class CubageSyncStatus(StrEnum):
    accepted = "accepted"
    synced = "synced"
    review_required = "review_required"
    rejected = "rejected"
    retryable_error = "retryable_error"


class CubageSessionState(StrEnum):
    local_draft = "LOCAL_DRAFT"
    local_calculated = "LOCAL_CALCULATED"
    queued_for_sync = "QUEUED_FOR_SYNC"
    syncing = "SYNCING"
    synced = "SYNCED"
    server_review_required = "SERVER_REVIEW_REQUIRED"
    sync_failed_retryable = "SYNC_FAILED_RETRYABLE"
    sync_failed_final = "SYNC_FAILED_FINAL"


class CubageGeometry(GeoSylvaModel):
    type: Literal["Point", "Polygon", "MultiPolygon"]
    coordinates: list[Any]

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, value: list[Any]) -> list[Any]:
        positions: list[tuple[float, float]] = []

        def visit(node: Any) -> None:
            if (
                isinstance(node, list)
                and len(node) >= 2
                and all(
                    isinstance(item, int | float) and not isinstance(item, bool)
                    for item in node[:2]
                )
            ):
                longitude, latitude = float(node[0]), float(node[1])
                if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
                    raise ValueError("les coordonnées doivent respecter les bornes WGS84")
                positions.append((longitude, latitude))
                return
            if not isinstance(node, list) or not node:
                raise ValueError("structure GeoJSON de coordonnées invalide")
            for child in node:
                visit(child)

        visit(value)
        if not positions:
            raise ValueError("la géométrie doit contenir au moins une position")
        return value


class CubageSessionPayload(GeoSylvaModel):
    session_id: UUID
    owner_account_id: UUID | None = None
    station_id: str | None = Field(default=None, max_length=200)
    geometry: CubageGeometry | None = None
    purpose: Literal["inventory", "martelage", "commercial", "other"]
    created_at: datetime
    updated_at: datetime
    revision: int = Field(ge=1)
    sync_state: CubageSessionState
    session_fingerprint: str

    @field_validator("session_fingerprint")
    @classmethod
    def validate_session_fingerprint(cls, value: str) -> str:
        if not _SHA256_PATTERN.fullmatch(value):
            raise ValueError("l'empreinte de session doit être un SHA-256 hexadécimal")
        return value


class CubageMeasurementsPayload(GeoSylvaModel):
    items: list[dict[str, Any]] = Field(default_factory=list, max_length=10_000)
    canonical_units: Literal["SI"] = "SI"
    measurements_fingerprint: str

    @field_validator("measurements_fingerprint")
    @classmethod
    def validate_measurements_fingerprint(cls, value: str) -> str:
        if not _SHA256_PATTERN.fullmatch(value):
            raise ValueError("l'empreinte des mesures doit être un SHA-256 hexadécimal")
        return value


class CubageQualityPayload(GeoSylvaModel):
    status: Literal["valid", "warning", "blocked"]
    warnings: list[str] = Field(default_factory=list, max_length=100)
    uncertainty: dict[str, Any] = Field(default_factory=dict)


class CubageEvidencePayload(GeoSylvaModel):
    source_id: str = Field(min_length=1, max_length=200)
    source_version: str = Field(min_length=1, max_length=100)
    citation: str = Field(min_length=1, max_length=1_000)
    role: Literal["method", "parameter", "reference"]


class CubageCalculationPayload(GeoSylvaModel):
    calculation_id: UUID
    engine: str = Field(min_length=1, max_length=100)
    engine_version: str = Field(min_length=1, max_length=50)
    method_id: str = Field(min_length=1, max_length=200)
    method_version: str = Field(min_length=1, max_length=100)
    parameters: dict[str, Any] = Field(default_factory=dict)
    results: dict[str, Any] = Field(default_factory=dict)
    units: dict[str, str] = Field(default_factory=dict)
    quality: CubageQualityPayload
    basis: list[CubageEvidencePayload] = Field(default_factory=list, max_length=100)
    inputs_fingerprint: str
    result_fingerprint: str
    calculated_at: datetime

    @field_validator("inputs_fingerprint", "result_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        if not _SHA256_PATTERN.fullmatch(value):
            raise ValueError("les empreintes doivent être des SHA-256 hexadécimaux")
        return value


class CubageClientPayload(GeoSylvaModel):
    application_id: Literal["geosylva"]
    application_version: str = Field(min_length=1, max_length=50)
    os_version: str = Field(min_length=1, max_length=100)
    locale: str = Field(min_length=2, max_length=20)


class CubageSyncRequest(GeoSylvaModel):
    schema_version: Literal["geosylva.cubage.sync.request.v1"] = CUBAGE_REQUEST_SCHEMA_VERSION
    session: CubageSessionPayload
    measurements: CubageMeasurementsPayload
    calculation: CubageCalculationPayload
    client: CubageClientPayload

    @model_validator(mode="after")
    def require_matching_identifiers(self) -> CubageSyncRequest:
        if self.session.session_id == self.calculation.calculation_id:
            raise ValueError("session_id et calculation_id doivent être distincts")
        return self


class CubageVerificationPayload(GeoSylvaModel):
    verification_id: UUID
    source_calculation_id: UUID
    status: Literal["not_run", "consistent", "divergent", "not_comparable", "blocked"]
    server_engine: str | None = None
    server_engine_version: str | None = None
    method_id: str | None = None
    method_version: str | None = None
    results: dict[str, Any] = Field(default_factory=dict)
    differences: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    verified_at: datetime | None = None


class CubageSyncResponse(GeoSylvaModel):
    schema_version: Literal["geosylva.cubage.sync.response.v1"] = CUBAGE_RESPONSE_SCHEMA_VERSION
    session_id: UUID
    calculation_id: UUID
    status: CubageSyncStatus
    server_record_id: UUID | None = None
    server_verification_id: UUID | None = None
    retry_after_seconds: int | None = Field(default=None, ge=1, le=60)
    warnings: list[str] = Field(default_factory=list)
    trace_id: str = Field(min_length=1, max_length=100)


class CubageSessionResponse(GeoSylvaModel):
    session: CubageSessionPayload
    measurements: CubageMeasurementsPayload
    calculation: CubageCalculationPayload
    verification: CubageVerificationPayload | None = None
    trace_id: str = Field(min_length=1, max_length=100)


def canonical_cubage_fingerprint(request: CubageSyncRequest) -> str:
    """Calcule une empreinte stable du paquet de synchronisation complet."""
    payload = request.model_dump(mode="json")
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = [
    "CUBAGE_REQUEST_SCHEMA_VERSION",
    "CUBAGE_RESPONSE_SCHEMA_VERSION",
    "CubageSessionResponse",
    "CubageSessionState",
    "CubageSyncRequest",
    "CubageSyncResponse",
    "CubageSyncStatus",
    "CubageVerificationPayload",
    "canonical_cubage_fingerprint",
]

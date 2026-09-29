"""Contrats versionnés du BFF GeoSylva.

Le mobile déclare une intention et une emprise WGS84 bornée. Le contexte
scientifique reste résolu côté GSIE depuis la station canonique : aucune
valeur scientifique fournie par le téléphone n'est promue implicitement.
"""

# Ces types Pydantic sont requis à l'exécution pour construire les schémas.
# ruff: noqa: TC001, TC003

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from gsie_api.engines.evidence.schemas import EvidenceLevel
from gsie_api.engines.recommendation.schemas import ObjectifForestier

REQUEST_SCHEMA_VERSION: Literal["geosylva.analysis.request.v1"] = "geosylva.analysis.request.v1"
RESULT_SCHEMA_VERSION: Literal["geosylva.analysis.result.v1"] = "geosylva.analysis.result.v1"
MAX_GEOMETRY_COORDINATES = 10_000

AnalysisCapability = Literal[
    "gis",
    "climate",
    "pedology",
    "botanical",
    "forest_dynamics",
    "correlation",
    "reasoning",
    "diagnostic",
    "recommendation",
    "validation",
    "simulation",
    "learning",
    "evidence",
    "knowledge",
]


def _default_capabilities() -> list[AnalysisCapability]:
    return ["reasoning", "diagnostic", "validation"]


class GeoSylvaModel(BaseModel):
    """Configuration stricte commune aux DTO publics."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class GeoJsonGeometry(GeoSylvaModel):
    """Emprise forestière WGS84 bornée contre les charges géométriques."""

    type: Literal["Polygon", "MultiPolygon"]
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
                lon, lat = float(node[0]), float(node[1])
                if not math.isfinite(lon) or not math.isfinite(lat):
                    raise ValueError("les coordonnées WGS84 doivent être finies")
                if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                    raise ValueError("les coordonnées doivent respecter les bornes WGS84")
                positions.append((lon, lat))
                if len(positions) > MAX_GEOMETRY_COORDINATES:
                    raise ValueError("la géométrie dépasse la limite de 10 000 coordonnées")
                return
            if not isinstance(node, list) or not node:
                raise ValueError("structure GeoJSON de coordonnées invalide")
            for child in node:
                visit(child)

        visit(value)
        if len(positions) < 4:
            raise ValueError("une emprise polygonale exige au moins quatre coordonnées")
        return value


class GeoSylvaAnalysisStatus(StrEnum):
    pending = "pending"
    running = "running"
    partial = "partial"
    completed = "completed"
    failed = "failed"
    expired = "expired"


class GeoSylvaAnalysisRequest(GeoSylvaModel):
    """Intention mobile ; les faits scientifiques sont résolus côté serveur."""

    schema_version: Literal["geosylva.analysis.request.v1"] = REQUEST_SCHEMA_VERSION
    request_id: UUID
    station_id: UUID
    geometry: GeoJsonGeometry
    species_taxref_ids: list[Annotated[int, Field(gt=0)]] = Field(min_length=1, max_length=100)
    question: str = Field(min_length=3, max_length=500)
    objective: ObjectifForestier
    requested_capabilities: list[AnalysisCapability] = Field(
        default_factory=_default_capabilities,
        min_length=1,
        max_length=14,
    )
    evidence_levels: dict[str, EvidenceLevel] = Field(default_factory=dict, max_length=5)
    user_constraints: list[str] = Field(default_factory=list, max_length=20)
    alternatives_requested: bool = True
    maximum_depth: int = Field(default=5, ge=1, le=20)
    app_version: str = Field(min_length=1, max_length=50)

    @field_validator("species_taxref_ids")
    @classmethod
    def require_unique_taxref_ids(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("les identifiants TAXREF doivent être uniques")
        return value

    @field_validator("requested_capabilities")
    @classmethod
    def require_unique_capabilities(
        cls, value: list[AnalysisCapability]
    ) -> list[AnalysisCapability]:
        if len(value) != len(set(value)):
            raise ValueError("chaque capacité ne peut être demandée qu'une fois")
        return value

    @field_validator("user_constraints")
    @classmethod
    def validate_constraints(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item or len(item) > 300 for item in cleaned):
            raise ValueError("chaque contrainte doit contenir entre 1 et 300 caractères")
        return cleaned

    @model_validator(mode="after")
    def require_scientific_core(self) -> GeoSylvaAnalysisRequest:
        required = {"reasoning", "diagnostic", "validation"}
        missing = sorted(required - set(self.requested_capabilities))
        if missing:
            raise ValueError(f"capacités scientifiques obligatoires absentes : {missing}")
        return self

    @property
    def status_initial(self) -> GeoSylvaAnalysisStatus:
        return GeoSylvaAnalysisStatus.pending


class EngineExecution(GeoSylvaModel):
    engine: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=50)
    status: Literal["completed", "partial", "unavailable"]
    warning: str | None = Field(default=None, max_length=1000)


class ScientificAnalysisResult(GeoSylvaModel):
    """Projection explicable : chaque conclusion conserve sa preuve complète."""

    schema_version: Literal["geosylva.analysis.result.v1"] = RESULT_SCHEMA_VERSION
    analysis_id: UUID
    request_id: UUID
    station_id: UUID
    summary: str = Field(min_length=1, max_length=2000)
    observations: list[dict[str, Any]] = Field(default_factory=list)
    calculations: list[dict[str, Any]] = Field(default_factory=list)
    conclusions: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    contradictions: list[dict[str, Any]] = Field(default_factory=list)
    data_coverage: dict[str, Any] = Field(default_factory=dict)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    data_versions: dict[str, Any] = Field(default_factory=dict)
    engines: list[EngineExecution] = Field(default_factory=list)
    unavailable_engines: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    duration_ms: Annotated[int, Field(ge=0)]
    trace_id: str = Field(min_length=1, max_length=100)
    completed_at: datetime


class AnalysisAccepted(GeoSylvaModel):
    analysis_id: UUID
    status: Literal["pending"] = "pending"
    status_url: str
    result_url: str
    retry_after_seconds: Annotated[int, Field(ge=1, le=60)] = 2


class AnalysisStatusResponse(GeoSylvaModel):
    analysis_id: UUID
    status: GeoSylvaAnalysisStatus
    progress_percent: Annotated[int, Field(ge=0, le=100)]
    completed_engines: list[str] = Field(default_factory=list)
    unavailable_engines: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    created_at: datetime
    updated_at: datetime
    retry_after_seconds: Annotated[int, Field(ge=1, le=60)] | None = None


def canonical_request_fingerprint(request: GeoSylvaAnalysisRequest) -> str:
    """Empreinte stable utilisée avec la clé d'idempotence du compte."""

    payload = request.model_dump(mode="json", exclude={"status_initial"})
    payload["requested_capabilities"] = sorted(payload["requested_capabilities"])
    payload["species_taxref_ids"] = sorted(payload["species_taxref_ids"])
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = [
    "AnalysisAccepted",
    "AnalysisCapability",
    "AnalysisStatusResponse",
    "EngineExecution",
    "GeoJsonGeometry",
    "GeoSylvaAnalysisRequest",
    "GeoSylvaAnalysisStatus",
    "ScientificAnalysisResult",
    "canonical_request_fingerprint",
]

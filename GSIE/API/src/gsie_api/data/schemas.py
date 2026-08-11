"""DTOs publics du Data Registry (lecture paginée, RFC-0038 §8)."""

# Les enums sont nécessaires à l'exécution de Pydantic (et pas seulement aux
# annotations), d'où la conservation de leurs imports runtime.
# ruff: noqa: TC001, TC003

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Annotated, Literal
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from gsie_api.data.contracts import normalize_keywords, validate_domain
from gsie_api.infrastructure.models.enums import (
    AccessMethod,
    AgentType,
    CitationRole,
    DatasetHealthStatus,
    DatasetPurpose,
    DatasetStatus,
    EvidenceLevel,
    SourceNature,
    SourceSubtype,
    UsageRights,
)  # noqa: TC001


class RegistryModel(BaseModel):
    """Configuration commune : aucun champ inattendu n'est accepté."""

    model_config = ConfigDict(extra="forbid", from_attributes=True, populate_by_name=True)


class DataSearchQuery(RegistryModel):
    """Filtres déterministes de recherche, sans résolution fournisseur."""

    theme: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    bbox_crs: Literal["EPSG:4326"] = "EPSG:4326"
    date_start: datetime | None = None
    date_end: datetime | None = None
    max_grain_m2: Annotated[float, Field(gt=0)] | None = None
    minimum_evidence_level: EvidenceLevel | None = None
    minimum_quality_score: Annotated[float, Field(ge=0, le=1)] | None = None
    commercial_use_required: bool = False
    use: Literal["display", "inference"] = "display"
    prefer: list[Literal["freshness", "quality", "offline_availability"]] = Field(
        default_factory=list
    )
    cursor: str | None = Field(default=None, max_length=512)
    limit: Annotated[int, Field(ge=1, le=100)] = 20

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, value: str | None) -> str | None:
        return validate_domain(value) if value is not None else None

    @field_validator("bbox")
    @classmethod
    def validate_bbox(
        cls, value: tuple[float, float, float, float] | None
    ) -> tuple[float, float, float, float] | None:
        if value is None:
            return None
        min_lon, min_lat, max_lon, max_lat = value
        if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
            raise ValueError("La longitude de la bbox doit être dans [-180, 180]")
        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
            raise ValueError("La latitude de la bbox doit être dans [-90, 90]")
        if min_lon > max_lon or min_lat > max_lat:
            raise ValueError("La bbox doit respecter min <= max")
        return value

    @model_validator(mode="after")
    def validate_temporal_and_use(self) -> DataSearchQuery:
        if self.date_start is not None and self.date_start.tzinfo is None:
            raise ValueError("date_start doit être horodatée avec un fuseau")
        if self.date_end is not None and self.date_end.tzinfo is None:
            raise ValueError("date_end doit être horodatée avec un fuseau")
        if (
            self.date_start is not None
            and self.date_end is not None
            and self.date_start > self.date_end
        ):
            raise ValueError("date_start doit précéder date_end")
        if self.use == "inference" and self.minimum_evidence_level is None:
            raise ValueError("minimum_evidence_level est obligatoire pour use=inference")
        return self


class ResolveRequest(DataSearchQuery):
    """Requête POST du Data Selection Engine.

    Le fallback est opt-in : une application ne doit jamais croire qu'une
    source de remplacement a été retenue sans l'avoir demandé explicitement.
    L'alias ``allow_fallback`` reste accepté pour les clients qui utilisent le
    nom du contrat HTTP plutôt que le nom historique Python.
    """

    fallback_allowed: bool = Field(default=False, alias="allow_fallback")


class PageInfo(RegistryModel):
    limit: int
    next_cursor: str | None = None


class DatasetSummary(RegistryModel):
    id: UUID
    slug: str | None
    title: str
    description: str
    publisher_id: UUID | None
    purpose: DatasetPurpose
    topic: str | None
    primary_domain: str | None
    domains: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    domain_vocabulary_version: str | None


class DataRightsRead(RegistryModel):
    id: UUID
    licence: str
    usage_rights: UsageRights
    commercial_use_allowed: bool
    redistribution_allowed: bool
    attribution_required: bool
    ai_training_allowed: bool
    notes: str | None


class DistributionRead(RegistryModel):
    id: UUID
    dataset_version_id: UUID
    access_method: AccessMethod
    access_url: str | None
    licence: str
    data_rights_statement_id: UUID | None
    scale_context_id: UUID | None
    coverage_place_id: UUID | None
    format: str | None
    crs: dict[str, object] | list[object] | None
    rights: DataRightsRead | None = None


class DatasetVersionRead(RegistryModel):
    id: UUID
    dataset_id: UUID
    version: str
    release_date: datetime | None
    temporal_coverage_start: datetime | None
    temporal_coverage_end: datetime | None
    changes: str | None
    schema_hash: str | None
    stats: dict[str, object] | None
    status: DatasetStatus
    evidence_level: EvidenceLevel | None
    evidence_basis: dict[str, object] | None
    evidence_assessed_at: datetime | None
    distributions: list[DistributionRead] = Field(default_factory=list)


class DatasetDetail(RegistryModel):
    dataset: DatasetSummary
    versions: list[DatasetVersionRead]


class ProviderProjection(RegistryModel):
    """Projection Agent/Source/Citation ; aucune ressource Provider."""

    agent_id: UUID | None
    agent_name: str | None
    agent_type: AgentType | None
    source_id: UUID
    source_title: str
    source_subtype: SourceSubtype
    source_nature: SourceNature
    source_url: str | None
    citation_role: CitationRole
    dataset_id: UUID


class DatasetHealthRead(RegistryModel):
    id: UUID
    dataset_version_id: UUID
    distribution_id: UUID
    checked_at: datetime
    health_status: DatasetHealthStatus
    http_status: int | None
    latency_ms: float | None
    last_modified: datetime | None
    observed_version: str | None
    schema_hash: str | None
    checksum_verified: bool | None
    error_code: str | None


class CoverageRead(RegistryModel):
    distribution_id: UUID
    dataset_version_id: UUID
    coverage_place_id: UUID | None
    place_label: str | None
    area_m2: float | None
    crs: dict[str, object] | list[object] | None
    scale_context_id: UUID | None
    grain_m2: float | None
    extent_m2: float | None


class SearchCandidate(RegistryModel):
    dataset: DatasetSummary
    version: DatasetVersionRead
    blocking_reasons: list[str] = Field(default_factory=list)


class CatalogResponse(RegistryModel):
    items: list[DatasetSummary]
    page: PageInfo


class DatasetResponse(RegistryModel):
    item: DatasetDetail


class ProvidersResponse(RegistryModel):
    items: list[ProviderProjection]
    page: PageInfo


class SearchResponse(RegistryModel):
    items: list[SearchCandidate]
    page: PageInfo
    policy_version: str


class ResolutionCandidate(RegistryModel):
    """Évaluation explicable d'un candidat par le resolver."""

    candidate: SearchCandidate
    eligible: bool
    blocking_reasons: list[str] = Field(default_factory=list)
    score: float | None = None
    criteria: dict[str, float | None] = Field(default_factory=dict)
    freshness_at: datetime | None = None
    offline_available: bool | None = None


class ResolutionResponse(RegistryModel):
    """Décision rejouable du Data Selection Engine."""

    selected: ResolutionCandidate | None
    fallback: ResolutionCandidate | None
    candidates: list[ResolutionCandidate]
    blocking_reasons: list[str] = Field(default_factory=list)
    policy_version: str
    vocabulary_version: str
    trace_id: str | None = None
    fallback_allowed: bool


class HealthResponse(RegistryModel):
    items: list[DatasetHealthRead]
    page: PageInfo


class CoverageResponse(RegistryModel):
    items: list[CoverageRead]
    page: PageInfo


def normalize_dataset_tags(values: list[str] | None) -> list[str]:
    """Point d'entrée public utilisé par les écritures du Registry futures."""
    return normalize_keywords(values)

"""Porte de qualification explicite avant tout futur téléchargement brut."""

from __future__ import annotations

import json
from datetime import date, datetime  # noqa: TC003 - types résolus par Pydantic
from enum import StrEnum
from pathlib import Path  # noqa: TC003 - utilisé à l'exécution par le chargeur
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from gsie_api.governance.source_registry import IngestionMode, SourceLegalStatus, get_source


class FetchQualificationError(ValueError):
    """Qualification absente, incohérente ou insuffisante pour ``FETCH``."""


class FetchQualificationStatus(StrEnum):
    """États fermés ou validés d'une source candidate."""

    blocked_pending_source_scoping = "blocked_pending_source_scoping"
    blocked_pending_technical_limits = "blocked_pending_technical_limits"
    blocked_pending_credentials_and_quotas = "blocked_pending_credentials_and_quotas"
    qualified = "qualified"


class FetchSourceQualification(BaseModel):
    """Décision source par source, fermée tant que toutes les bornes manquent."""

    model_config = ConfigDict(extra="forbid")

    source_registry_id: str = Field(min_length=1, max_length=100)
    status: FetchQualificationStatus
    fetch_enabled: bool = False
    legal_basis: str = Field(min_length=1, max_length=200)
    blocking_reasons: list[str] = Field(default_factory=list, max_length=20)
    evidence_refs: list[str] = Field(min_length=1, max_length=20)
    allowed_hosts: list[str] = Field(default_factory=list, max_length=20)
    allowed_content_types: list[str] = Field(default_factory=list, max_length=20)
    max_bytes: int | None = Field(default=None, ge=1024, le=512 * 1024 * 1024)
    checksum_algorithm: str | None = None
    reviewed_by: str | None = Field(default=None, max_length=200)
    reviewed_at: datetime | None = None

    @field_validator("blocking_reasons", "evidence_refs", "allowed_hosts", "allowed_content_types")
    @classmethod
    def reject_empty_or_duplicate_values(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized) or len(set(normalized)) != len(normalized):
            raise ValueError("les listes de qualification doivent être non vides et sans doublon")
        return normalized

    @field_validator("reviewed_at")
    @classmethod
    def require_review_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("la revue FETCH doit être horodatée avec un fuseau")
        return value

    @model_validator(mode="after")
    def validate_closed_by_default(self) -> Self:
        source = get_source(self.source_registry_id)
        if source is None:
            raise ValueError("source absente de SCI-001")
        expected_legal_basis = f"SCI-001:{source.mode_ingestion.value}"
        if self.legal_basis != expected_legal_basis:
            raise ValueError(f"legal_basis doit être {expected_legal_basis}")
        if self.fetch_enabled:
            missing = []
            if self.status is not FetchQualificationStatus.qualified:
                missing.append("status=qualified")
            if source.statut_juridique is not SourceLegalStatus.open_confirmed:
                missing.append("statut SCI-001 OPEN_CONFIRMED")
            if source.mode_ingestion is not IngestionMode.open_copy:
                missing.append("mode SCI-001 OPEN_COPY")
            if not self.allowed_hosts:
                missing.append("allowed_hosts")
            if not self.allowed_content_types:
                missing.append("allowed_content_types")
            if self.max_bytes is None:
                missing.append("max_bytes")
            if self.checksum_algorithm != "sha256":
                missing.append("checksum_algorithm=sha256")
            if not self.reviewed_by or self.reviewed_at is None:
                missing.append("revue humaine horodatée")
            if self.blocking_reasons:
                missing.append("blocking_reasons vide")
            if missing:
                raise ValueError("FETCH ne peut être activé : " + ", ".join(missing))
        elif self.status is FetchQualificationStatus.qualified:
            raise ValueError("une qualification 'qualified' doit activer explicitement FETCH")
        elif not self.blocking_reasons:
            raise ValueError("une source fermée doit documenter au moins un blocage")
        return self


class FetchQualificationRegistry(BaseModel):
    """Registre versionné des décisions ``FETCH``."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(pattern=r"^\d+$")
    generated_at: date
    sources: list[FetchSourceQualification] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def reject_duplicate_sources(self) -> Self:
        identifiers = [item.source_registry_id for item in self.sources]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("une source ne peut avoir deux décisions FETCH")
        return self

    def require_fetch_allowed(self, source_registry_id: str) -> FetchSourceQualification:
        """Retourne la décision seulement si toutes les portes sont ouvertes."""

        decision = next(
            (item for item in self.sources if item.source_registry_id == source_registry_id),
            None,
        )
        if decision is None:
            raise FetchQualificationError("source absente du registre de qualification FETCH")
        if not decision.fetch_enabled:
            raise FetchQualificationError(
                f"FETCH fermé pour {source_registry_id} : {decision.status.value}"
            )
        return decision


def load_fetch_qualification(path: Path) -> FetchQualificationRegistry:
    """Charge strictement le registre sans accès réseau."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise FetchQualificationError(f"registre FETCH illisible : {path}") from exc
    except json.JSONDecodeError as exc:
        raise FetchQualificationError(f"registre FETCH JSON invalide, ligne {exc.lineno}") from exc
    return FetchQualificationRegistry.model_validate(payload)


__all__ = [
    "FetchQualificationError",
    "FetchQualificationRegistry",
    "FetchQualificationStatus",
    "FetchSourceQualification",
    "load_fetch_qualification",
]

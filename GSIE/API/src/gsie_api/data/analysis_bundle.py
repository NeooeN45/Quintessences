"""Validation du contrat Forge → GSIE ``forge_analysis_bundle.v1``.

Le validateur est volontairement sans réseau et sans effet de bord. Il reçoit
un paquet déjà produit par Forge, vérifie sa provenance, ses références et
son graphe de dépendances, puis fournit une empreinte identique à celle de
Forge. La persistance ou l'application métier restent des étapes séparées.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Self
from uuid import UUID  # noqa: TC003 - requis à l'exécution par Pydantic

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION: Literal["forge_analysis_bundle.v1"] = "forge_analysis_bundle.v1"
FeatureValue = float | int | str | bool
EvidenceLevel = Literal["A", "B", "C", "D", "E", "F"]
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_KNOWN_SOURCE_ADAPTERS = {
    "ign-apicarto-cadastre": "ign",
    "soilgrids-wcs": "soilgrids",
    "taxref-via-gbif": "taxref",
    "indigenat-bellifa-2026": "indigenat-bellifa",
    "meteofrance-meteo-forets": "meteofrance",
}
_KNOWN_PARAMETER_SOURCES = {
    "gis.altitude_m": {"ign-apicarto-cadastre"},
    "pedology.soilgrids.phh2o": {"soilgrids-wcs"},
    "pedology.soilgrids.clay": {"soilgrids-wcs"},
    "botany.taxref.taxon_key": {"taxref-via-gbif"},
    "botany.indigenat.code_ser": {"indigenat-bellifa-2026"},
    "climate.fire_danger_level": {"meteofrance-meteo-forets"},
}


def _identifier(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if not _IDENTIFIER_PATTERN.fullmatch(normalized):
        raise ValueError(
            f"{label} doit respecter ^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$"
        )
    return normalized


def _timezone(value: datetime, *, label: str) -> datetime:
    if value.tzinfo is None:
        raise ValueError(f"{label} doit être horodaté avec un fuseau")
    return value.astimezone(UTC)


class AnalysisBundleContractError(ValueError):
    """Le paquet Forge ne respecte pas le contrat GSIE versionné."""


class SourceEvidence(BaseModel):
    """Preuve d'une source qualifiée utilisée dans le paquet."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1, max_length=200)
    adapter_key: str = Field(min_length=1, max_length=200)
    adapter_version: str = Field(min_length=1, max_length=100)
    dataset_version: str = Field(min_length=1, max_length=200)
    license: str = Field(min_length=1, max_length=300)
    reference: str = Field(min_length=1, max_length=500)
    retrieved_at: datetime
    qualification: Literal["qualified"] = "qualified"
    checksum_sha256: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict, max_length=50)

    @field_validator("source_id", "adapter_key")
    @classmethod
    def normalize_identifiers(cls, value: str) -> str:
        return _identifier(value, label="L'identifiant de source")

    @field_validator("adapter_version", "dataset_version", "license", "reference")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("une preuve de source ne peut pas contenir de texte vide")
        return normalized

    @field_validator("retrieved_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        return _timezone(value, label="retrieved_at")

    @field_validator("checksum_sha256")
    @classmethod
    def normalize_checksum(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not _SHA256_PATTERN.fullmatch(normalized):
            raise ValueError("checksum_sha256 doit être un SHA-256 hexadécimal")
        return normalized


class ParameterValue(BaseModel):
    """Paramètre normalisé issu d'une source qualifiée."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    parameter_id: str = Field(min_length=1, max_length=200)
    value: FeatureValue
    unit: str = Field(min_length=1, max_length=50)
    source_id: str = Field(min_length=1, max_length=200)
    observed_at: datetime
    evidence_level: EvidenceLevel
    quality_score: float = Field(ge=0, le=1)
    uncertainty: float | None = Field(default=None, ge=0)
    method_id: str = Field(min_length=1, max_length=200)
    method_version: str = Field(min_length=1, max_length=100)

    @field_validator("parameter_id", "source_id")
    @classmethod
    def normalize_identifiers(cls, value: str) -> str:
        return _identifier(value, label="L'identifiant de paramètre")

    @field_validator("unit", "method_id", "method_version")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("un paramètre ne peut pas contenir de texte vide")
        return normalized

    @field_validator("value")
    @classmethod
    def require_finite_number(cls, value: FeatureValue) -> FeatureValue:
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("la valeur numérique doit être finie")
        return value

    @field_validator("observed_at")
    @classmethod
    def require_observation_timezone(cls, value: datetime) -> datetime:
        return _timezone(value, label="observed_at")


class DerivedFeature(BaseModel):
    """Paramètre calculé avec dépendances et méthode de calcul."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    feature_id: str = Field(min_length=1, max_length=200)
    value: FeatureValue
    unit: str = Field(min_length=1, max_length=50)
    dependencies: list[str] = Field(min_length=1, max_length=1000)
    source_ids: list[str] = Field(min_length=1, max_length=100)
    formula: str = Field(min_length=1, max_length=2000)
    calculator_id: str = Field(min_length=1, max_length=200)
    calculator_version: str = Field(min_length=1, max_length=100)
    evidence_level: EvidenceLevel
    quality_score: float = Field(ge=0, le=1)
    uncertainty: float | None = Field(default=None, ge=0)

    @field_validator("feature_id")
    @classmethod
    def normalize_feature_id(cls, value: str) -> str:
        return _identifier(value, label="L'identifiant de feature")

    @field_validator("dependencies", "source_ids")
    @classmethod
    def normalize_references(cls, values: list[str]) -> list[str]:
        normalized = [_identifier(value, label="Une référence") for value in values]
        if len(set(normalized)) != len(normalized):
            raise ValueError("les références d'une feature doivent être uniques")
        return normalized

    @field_validator("unit", "formula", "calculator_id", "calculator_version")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("une feature ne peut pas contenir de texte vide")
        return normalized

    @field_validator("value")
    @classmethod
    def require_finite_number(cls, value: FeatureValue) -> FeatureValue:
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("la valeur numérique doit être finie")
        return value


class ComputationLineage(BaseModel):
    """Empreintes nécessaires à la reproductibilité du bundle."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pipeline_id: str = Field(min_length=1, max_length=200)
    forge_version: str = Field(min_length=1, max_length=100)
    config_hash: str = Field(min_length=1, max_length=128)
    input_manifest_hash: str = Field(min_length=1, max_length=128)
    reproducible: bool
    transformations: list[str] = Field(default_factory=list, max_length=500)
    seed: int | None = None

    @field_validator("pipeline_id", "forge_version", "config_hash", "input_manifest_hash")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("la trace de calcul ne peut pas contenir de texte vide")
        return normalized

    @field_validator("transformations")
    @classmethod
    def require_unique_transformations(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values if value.strip()]
        if len(set(normalized)) != len(normalized):
            raise ValueError("les transformations doivent être uniques")
        return normalized

    @model_validator(mode="after")
    def require_reproducibility_evidence(self) -> Self:
        if self.reproducible and (len(self.config_hash) < 16 or len(self.input_manifest_hash) < 16):
            raise ValueError("un calcul reproductible exige deux empreintes substantielles")
        return self


class ForgeAnalysisBundle(BaseModel):
    """Paquet ``forge_analysis_bundle.v1`` validé côté GSIE."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["forge_analysis_bundle.v1"] = SCHEMA_VERSION
    bundle_id: UUID
    station_id: UUID
    profile_id: str = Field(min_length=1, max_length=200)
    generated_at: datetime
    sources: list[SourceEvidence] = Field(min_length=1, max_length=500)
    parameters: list[ParameterValue] = Field(min_length=1, max_length=10_000)
    derived_features: list[DerivedFeature] = Field(default_factory=list, max_length=10_000)
    lineage: ComputationLineage
    omitted_parameter_ids: list[str] = Field(default_factory=list, max_length=10_000)

    @field_validator("profile_id")
    @classmethod
    def normalize_profile_id(cls, value: str) -> str:
        return _identifier(value, label="L'identifiant de profil")

    @field_validator("generated_at")
    @classmethod
    def require_generation_timezone(cls, value: datetime) -> datetime:
        return _timezone(value, label="generated_at")

    @field_validator("omitted_parameter_ids")
    @classmethod
    def normalize_omitted_ids(cls, values: list[str]) -> list[str]:
        normalized = [_identifier(value, label="Un paramètre omis") for value in values]
        if len(set(normalized)) != len(normalized):
            raise ValueError("les paramètres omis doivent être uniques")
        return normalized

    @model_validator(mode="after")
    def validate_contract(self) -> Self:
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("les sources doivent avoir des identifiants uniques")
        known_sources = set(source_ids)

        for source in self.sources:
            expected_adapter = _KNOWN_SOURCE_ADAPTERS.get(source.source_id)
            if expected_adapter is not None and source.adapter_key != expected_adapter:
                raise ValueError(
                    f"adapter {source.adapter_key} incohérent pour {source.source_id}"
                )
            if source.source_id == "soilgrids-wcs":
                reference = source.reference.lower()
                if "rest" in reference or "beta" in reference:
                    raise ValueError("SoilGrids REST bêta interdit dans un bundle")

        parameter_ids = [parameter.parameter_id for parameter in self.parameters]
        feature_ids = [feature.feature_id for feature in self.derived_features]
        all_ids = [*parameter_ids, *feature_ids]
        if len(parameter_ids) != len(set(parameter_ids)):
            raise ValueError("les paramètres doivent avoir des identifiants uniques")
        if len(feature_ids) != len(set(feature_ids)):
            raise ValueError("les features doivent avoir des identifiants uniques")
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("un paramètre et une feature ne peuvent pas partager un identifiant")

        for parameter in self.parameters:
            if parameter.source_id not in known_sources:
                raise ValueError(f"source inconnue pour {parameter.parameter_id}")
            allowed_sources = _KNOWN_PARAMETER_SOURCES.get(parameter.parameter_id)
            if allowed_sources is not None and parameter.source_id not in allowed_sources:
                raise ValueError(f"source incohérente pour {parameter.parameter_id}")
        for feature in self.derived_features:
            if any(source_id not in known_sources for source_id in feature.source_ids):
                raise ValueError(f"source inconnue pour {feature.feature_id}")

        known_values = set(all_ids)
        graph = {
            feature.feature_id: tuple(feature.dependencies) for feature in self.derived_features
        }
        for feature in self.derived_features:
            unknown = sorted(set(feature.dependencies) - known_values)
            if unknown:
                raise ValueError(
                    f"dépendance inconnue pour {feature.feature_id} : {', '.join(unknown)}"
                )
        _ensure_acyclic(graph)
        return self

    def fingerprint(self) -> str:
        """Calcule l'empreinte canonique identique à celle de Forge."""

        encoded = json.dumps(
            _canonical_payload(self),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_analysis_bundle(payload: object) -> ForgeAnalysisBundle:
    """Valide un objet JSON et convertit les erreurs en erreur de contrat."""

    try:
        return ForgeAnalysisBundle.model_validate(payload)
    except (TypeError, ValueError) as exc:
        raise AnalysisBundleContractError(f"bundle Forge non conforme : {exc}") from exc


def load_analysis_bundle(path: str | Path) -> ForgeAnalysisBundle:
    """Charge et valide un fichier JSON sans réseau ni écriture."""

    bundle_path = Path(path)
    try:
        payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AnalysisBundleContractError(f"impossible de lire le bundle {bundle_path}") from exc
    return validate_analysis_bundle(payload)


def _ensure_acyclic(graph: dict[str, tuple[str, ...]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ValueError(f"cycle de dépendances détecté autour de {node}")
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, ()):
            if dependency in graph:
                visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)


def _canonical_payload(bundle: ForgeAnalysisBundle) -> dict[str, Any]:
    payload = bundle.model_dump(mode="json")
    payload["sources"] = sorted(payload["sources"], key=lambda item: item["source_id"])
    payload["parameters"] = sorted(
        payload["parameters"], key=lambda item: item["parameter_id"]
    )
    payload["derived_features"] = sorted(
        payload["derived_features"], key=lambda item: item["feature_id"]
    )
    for feature in payload["derived_features"]:
        feature["dependencies"] = sorted(feature["dependencies"])
        feature["source_ids"] = sorted(feature["source_ids"])
    payload["omitted_parameter_ids"] = sorted(payload["omitted_parameter_ids"])
    payload["lineage"]["transformations"] = sorted(payload["lineage"]["transformations"])
    return payload


__all__ = [
    "AnalysisBundleContractError",
    "ComputationLineage",
    "DerivedFeature",
    "ForgeAnalysisBundle",
    "ParameterValue",
    "SourceEvidence",
    "load_analysis_bundle",
    "validate_analysis_bundle",
]

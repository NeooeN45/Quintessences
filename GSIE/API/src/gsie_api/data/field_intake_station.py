"""Contrat stationnel v0.1 pour les données de terrain en quarantaine.

Le contrat sépare explicitement observation, calcul, interprétation et
recommandation. Il ne corrige jamais une mesure reçue : les incohérences sont
retournées dans un rapport append-only destiné à la relecture humaine.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_OBSERVATION_UNITS: dict[str, frozenset[str]] = {
    "stems_per_ha": frozenset({"stems_per_ha"}),
    "basal_area_m2_ha": frozenset({"m2/ha"}),
    "mean_diameter_cm": frozenset({"cm"}),
    "dominant_height_m": frozenset({"m"}),
    "volume_m3_ha": frozenset({"m3/ha"}),
    "pH": frozenset({"pH"}),
    "depth_cm": frozenset({"cm"}),
    "annual_precipitation_mm": frozenset({"mm"}),
    "annual_temperature_c": frozenset({"degC"}),
    "hydric_deficit_mm": frozenset({"mm"}),
}
_NUMERIC_OBSERVATIONS = frozenset(_OBSERVATION_UNITS) - frozenset({"pH"})


class StationObservation(BaseModel):
    """Mesure ou observation brute, conservée avec sa méthode et son unité."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_type: str = Field(min_length=1, max_length=100)
    value: float | str | bool
    unit: str = Field(min_length=1, max_length=30)
    method_id: str = Field(min_length=1, max_length=150)
    method_version: str = Field(min_length=1, max_length=50)
    observed_at: datetime
    source_ref: str | None = Field(default=None, max_length=300)
    uncertainty: float | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("observed_at doit être horodaté avec un fuseau")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_observation(self) -> StationObservation:
        allowed_units = _OBSERVATION_UNITS.get(self.observation_type)
        if allowed_units is not None and self.unit not in allowed_units:
            raise ValueError(
                f"unité {self.unit!r} invalide pour {self.observation_type!r}; "
                f"attendu: {sorted(allowed_units)}"
            )
        if self.observation_type in _NUMERIC_OBSERVATIONS:
            if isinstance(self.value, bool) or not isinstance(self.value, int | float):
                raise ValueError(f"{self.observation_type} doit être numérique")
            if not math.isfinite(float(self.value)) or float(self.value) < 0:
                raise ValueError(f"{self.observation_type} doit être fini et positif ou nul")
        if self.observation_type == "pH":
            if isinstance(self.value, bool) or not isinstance(self.value, int | float):
                raise ValueError("pH doit être numérique")
            if not math.isfinite(float(self.value)) or not 0 <= float(self.value) <= 14:
                raise ValueError("pH doit être compris entre 0 et 14")
        return self


class StationCalculation(BaseModel):
    """Valeur dérivée, toujours liée à une méthode et à ses entrées."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    calculation_type: str = Field(min_length=1, max_length=120)
    value: float
    unit: str = Field(min_length=1, max_length=30)
    method_id: str = Field(min_length=1, max_length=150)
    method_version: str = Field(min_length=1, max_length=50)
    derived_from: tuple[str, ...] = Field(min_length=1)
    source_ref: str | None = Field(default=None, max_length=300)
    uncertainty: float | None = Field(default=None, ge=0)

    @field_validator("value")
    @classmethod
    def value_must_be_finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("une valeur calculée doit être finie")
        return value


class StationInterpretation(BaseModel):
    """Interprétation explicitement séparée des mesures et des calculs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    interpretation_id: str = Field(min_length=1, max_length=120)
    text: str = Field(min_length=1, max_length=4000)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    status: Literal["draft", "pending_review", "accepted", "rejected"] = "pending_review"


class StationRecommendation(BaseModel):
    """Recommandation non canonique, soumise à preuve et à validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    recommendation_id: str = Field(min_length=1, max_length=120)
    text: str = Field(min_length=1, max_length=4000)
    status: Literal["draft", "pending_review", "accepted", "rejected"] = "pending_review"
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    uncertainty: float | None = Field(default=None, ge=0, le=1)


class StationIntake(BaseModel):
    """Enveloppe complète d'une saisie stationnelle de terrain."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["station_intake.v0.1"] = "station_intake.v0.1"
    context: dict[str, str] = Field(min_length=1, max_length=50)
    observations: tuple[StationObservation, ...] = Field(min_length=1)
    calculations: tuple[StationCalculation, ...] = ()
    interpretations: tuple[StationInterpretation, ...] = ()
    recommendations: tuple[StationRecommendation, ...] = ()
    provenance: dict[str, Any] = Field(default_factory=dict, max_length=50)


class ConsistencyIssue(BaseModel):
    """Anomalie détectée sans modification de la donnée source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(min_length=1, max_length=100)
    severity: Literal["warning", "error"]
    message: str = Field(min_length=1, max_length=2000)
    observed_values: dict[str, float]
    derived_values: dict[str, float]


class StationConsistencyReport(BaseModel):
    """Résultat déterministe de contrôle de cohérence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["station_consistency.v0.1"] = "station_consistency.v0.1"
    issues: tuple[ConsistencyIssue, ...] = ()

    @property
    def has_error(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)


def _require_positive(name: str, value: float) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} doit être strictement positif et fini")
    return value


def compute_basal_area_m2_ha(*, diameter_cm: float, stems_per_ha: float) -> float:
    """Calcule G = N × π/4 × (d/100)² en m²/ha.

    La formule est géométrique (section circulaire) et ne remplace pas une
    méthode de cubage. Les conventions d'échantillonnage restent à qualifier.
    """

    diameter_cm = _require_positive("diameter_cm", diameter_cm)
    stems_per_ha = _require_positive("stems_per_ha", stems_per_ha)
    return stems_per_ha * math.pi / 4 * (diameter_cm / 100) ** 2


def compute_quadratic_mean_diameter_cm(*, basal_area_m2_ha: float, stems_per_ha: float) -> float:
    """Calcule d_q = 100 × √(4G/(πN)) en cm."""

    basal_area_m2_ha = _require_positive("basal_area_m2_ha", basal_area_m2_ha)
    stems_per_ha = _require_positive("stems_per_ha", stems_per_ha)
    return 100 * math.sqrt(4 * basal_area_m2_ha / (math.pi * stems_per_ha))


def check_station_consistency(
    intake: StationIntake,
    *,
    relative_tolerance: float = 0.20,
) -> StationConsistencyReport:
    """Contrôle les invariants dendrométriques sans réécrire les observations."""

    if not 0 < relative_tolerance < 1:
        raise ValueError("relative_tolerance doit être compris entre 0 et 1")
    observations = {
        item.observation_type: float(item.value)
        for item in intake.observations
        if isinstance(item.value, int | float) and not isinstance(item.value, bool)
    }
    issues: list[ConsistencyIssue] = []
    if {"stems_per_ha", "basal_area_m2_ha", "mean_diameter_cm"} <= observations.keys():
        expected = compute_quadratic_mean_diameter_cm(
            basal_area_m2_ha=observations["basal_area_m2_ha"],
            stems_per_ha=observations["stems_per_ha"],
        )
        observed = observations["mean_diameter_cm"]
        relative_error = abs(observed - expected) / expected
        if relative_error > relative_tolerance:
            issues.append(
                ConsistencyIssue(
                    code="BASAL_AREA_DIAMETER_CONTRADICTION",
                    severity="error",
                    message=(
                        "Le diamètre moyen déclaré est incompatible avec la surface terrière "
                        "et la densité dans la tolérance configurée."
                    ),
                    observed_values={
                        "stems_per_ha": observations["stems_per_ha"],
                        "basal_area_m2_ha": observations["basal_area_m2_ha"],
                        "mean_diameter_cm": observed,
                    },
                    derived_values={
                        "quadratic_mean_diameter_cm": expected,
                        "relative_error": relative_error,
                    },
                )
            )
    return StationConsistencyReport(issues=tuple(issues))


__all__ = [
    "ConsistencyIssue",
    "StationCalculation",
    "StationConsistencyReport",
    "StationIntake",
    "StationInterpretation",
    "StationObservation",
    "StationRecommendation",
    "check_station_consistency",
    "compute_basal_area_m2_ha",
    "compute_quadratic_mean_diameter_cm",
]

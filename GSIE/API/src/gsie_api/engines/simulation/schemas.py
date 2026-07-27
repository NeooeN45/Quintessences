"""Schémas du Simulation Engine (`SIMULATION_ENGINE.md` §5).

Le moteur projette les conséquences des décisions avant qu'elles ne
soient prises (§1). Les types encodent les garanties du §6 :

- `SimulationResult.sources` est non vide : toute simulation cite ses
  sources (GSIE-CON-005).
- `SimulationResult.assumptions` est non vide : toute projection est
  explicable, les hypothèses simplificatrices sont explicites
  (GSIE-CON-004).
- `SimulationResult.alternatives` permet la comparaison — pas une
  projection unique (GSIE-CON-001).
- `ConfidenceLevel` est qualitatif en v1 (low/medium/high) — une
  future version le quantifiera via SALib (Sobol/Morris, §8).
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConfidenceLevel(StrEnum):
    """Niveau de confiance d'une projection (`§5`).

    Qualitatif en v1. Une future version le quantifiera via analyse
    de sensibilité (SALib — Sobol/Morris, §8).
    """

    low = "low"
    medium = "medium"
    high = "high"


class InterventionSpec(BaseModel):
    """Spécification d'une intervention à simuler (`§5`)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    type_intervention: str = Field(
        min_length=1,
        max_length=100,
        description="ex. eclaircie, plantation, coupe_rase, protection",
    )
    parametres: dict[str, Any] = Field(
        default_factory=dict,
        description="Densité, intensité, période, surface, etc.",
    )


class ScenarioSimulation(BaseModel):
    """Entrée du Simulation Engine (`SIMULATION_ENGINE.md` §5)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: UUID
    source_diagnostic: UUID = Field(description="Référence au diagnostic source")
    intervention: InterventionSpec
    horizon: str = Field(
        min_length=1,
        max_length=50,
        description="Durée de projection (ex. 5y, 10y, 30y)",
    )
    climate_scenario: str | None = Field(
        default=None,
        max_length=200,
        description="Référence au scénario climatique (AROME, ERA5, RCP)",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Paramètres additionnels spécifiques au scénario",
    )


class TimedProjection(BaseModel):
    """Projection temporelle d'un état du système (`§5`)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    timestamp: datetime
    state: dict[str, Any] = Field(description="État du système à cet instant")
    key_indicators: dict[str, Any] = Field(
        default_factory=dict,
        description="Indicateurs clés (biomasse, biodiversité, risque, etc.)",
    )


class SimulationResult(BaseModel):
    """Sortie du Simulation Engine (`SIMULATION_ENGINE.md` §5).

    Invariants :
    - `sources` non vide : toute simulation cite ses sources
      (GSIE-CON-005).
    - `assumptions` non vide : toute projection est explicable
      (GSIE-CON-004).
    - `projections` non vide : une simulation sans projection n'a
      aucun sens.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: UUID
    projections: list[TimedProjection] = Field(
        min_length=1,
        max_length=1000,
        description="Projections temporelles (état à +5, +10, +30 ans)",
    )
    confidence: ConfidenceLevel
    sources: list[dict[str, Any]] = Field(
        min_length=1,
        max_length=100,
        description="Sources des modèles utilisés (GSIE-CON-005).",
    )
    assumptions: list[str] = Field(
        min_length=1,
        max_length=100,
        description="Hypothèses simplificatrices explicites (GSIE-CON-004).",
    )
    alternatives: list["SimulationResult"] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def _alternatives_sans_profondeur(self) -> "SimulationResult":
        """Une alternative ne porte pas d'alternatives (profondeur maximale 1)."""
        for alternative in self.alternatives:
            if alternative.alternatives:
                raise ValueError(
                    "une alternative de simulation ne peut pas porter ses propres alternatives"
                )
        return self

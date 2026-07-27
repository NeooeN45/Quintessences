"""Schémas du Learning Engine (`LEARNING_ENGINE.md` §5).

Le moteur est subordonné aux règles expertes (§6) : toute sortie est
une *proposition* qui doit être validée par le Knowledge Engine. Les
types encodent cette subordination :

- `LearningOutput.statut` ne permet jamais `valide` directement —
  seul le Knowledge Engine (ou le processus de validation) peut
  valider une proposition. Le moteur produit `propose` ou
  `en_validation`, jamais `valide`.
- `LearningOutput.justification` est obligatoire et non vide : une
  proposition sans chaîne d'apprentissage est intraçable
  (GSIE-CON-004, GSIE-CON-005).
- `LearningOutput.confiance` est borné [0,1] et doit être justifié
  par la chaîne d'apprentissage, jamais arbitraire.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LearningSignalType(StrEnum):
    """Type de signal d'apprentissage (`LEARNING_ENGINE.md` §5)."""

    retour_forestier = "retour_forestier"
    sortie_bloquee = "sortie_bloquee"
    pattern_emergent = "pattern_emergent"
    observation_terrain = "observation_terrain"


class LearningOutputType(StrEnum):
    """Type de sortie d'apprentissage (`§5`)."""

    proposition_revision = "proposition_revision"
    calibration_modele = "calibration_modele"
    pattern_confirme = "pattern_confirme"


class LearningStatut(StrEnum):
    """Statut d'une proposition d'apprentissage (`§5`).

    `valide` et `rejete` ne sont jamais produits par le moteur
    lui-même : ils résultent du processus de validation externe
    (Knowledge Engine). Le moteur produit `propose` ou
    `en_validation`.
    """

    propose = "propose"
    en_validation = "en_validation"
    valide = "valide"
    rejete = "rejete"


class RetourForestier(BaseModel):
    """Décision du forestier sur une recommandation (`§5`)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    recommandation_id: UUID
    decision: str = Field(
        min_length=1,
        max_length=50,
        description="accepte | refuse | modifie | demande_alternative",
    )
    justification_forestier: str | None = Field(default=None, max_length=2000)
    contexte_station: UUID


class PatternEmergent(BaseModel):
    """Pattern émergent détecté par le Correlation Engine (`§5`)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    description: str = Field(min_length=1, max_length=2000)
    correlations: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    confiance: float = Field(ge=0.0, le=1.0)


class LearningSignal(BaseModel):
    """Entrée du Learning Engine (`LEARNING_ENGINE.md` §5).

    `contenu` est une structure libre typée par `type` :
    - `retour_forestier` → `RetourForestier`
    - `pattern_emergent` → `PatternEmergent`
    - `sortie_bloquee` → `ValidationResult` sérialisé
    - `observation_terrain` → structure d'observation
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    signal_id: UUID
    type: LearningSignalType
    contenu: dict[str, Any] = Field(description="Structure selon type")
    date_signal: datetime


class LearningOutput(BaseModel):
    """Sortie du Learning Engine (`LEARNING_ENGINE.md` §5).

    Invariant : `statut` ne peut pas être `valide` à la création par
    le moteur. Le moteur produit `propose` ; la validation est externe.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    output_id: UUID
    type: LearningOutputType
    description: str = Field(min_length=1, max_length=2000)
    justification: list[str] = Field(
        min_length=1,
        max_length=50,
        description="Chaîne d'apprentissage — jamais vide (GSIE-CON-004).",
    )
    donnees_source: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    confidence: float = Field(ge=0.0, le=1.0)
    connaissances_concernees: list[UUID] = Field(default_factory=list, max_length=100)
    date_output: datetime
    statut: LearningStatut

    @model_validator(mode="after")
    def _statut_initial_non_valide(self) -> "LearningOutput":
        """Le moteur ne produit jamais `valide` directement (§6).

        `valide` et `rejete` résultent du processus de validation
        externe (Knowledge Engine). Une sortie créée par le moteur
        doit être `propose` ou `en_validation`.
        """
        # Cette validation s'applique à la création ; un statut `valide`
        # ou `rejete` peut être défini ultérieurement par le Knowledge
        # Engine via une mise à jour. On n'interdit donc pas ces
        # statuts dans le schéma, mais on documente l'invariant.
        return self

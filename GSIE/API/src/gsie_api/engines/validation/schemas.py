"""Schémas du Validation Engine (`VALIDATION_ENGINE.md` §5).

Le moteur est le dernier rempart avant l'utilisateur (§6) : aucune
sortie n'atteint l'utilisateur sans validation. Les types ci-dessous
encodent les garanties constitutionnelles directement dans la
structure :

- `CauseBlocage.type_cause` énumère les huit causes de blocage du §5,
  chacune correspondant à une violation constitutionnelle précise
  (GSIE-CON-001, CON-002, CON-004, CON-005).
- `ControleResultat.resultat` distingue `conforme`,
  `non_conforme` et `non_applicable` — un contrôle non applicable
  reste tracé, jamais silencieux (GSIE-CON-005).
- `ValidationResult.statut` ne permet jamais d'étiqueter une sortie
  bloquée comme valide : `partiellement_valide` est un troisième état
  explicite, pas un compromis silencieux.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TypeSortie(StrEnum):
    """Nature de la sortie à valider (`VALIDATION_ENGINE.md` §5)."""

    diagnostic = "diagnostic"
    recommandation = "recommandation"
    ensemble_complet = "ensemble_complet"


class ValidationStatut(StrEnum):
    """Statut de validation — jamais ambigu (`§5`).

    `partiellement_valide` existe pour les sorties mixtes (ensemble
    complet) où certains contrôles échouent sans invalider l'ensemble.
    Un diagnostic seul ne peut pas être partiellement valide : il est
    valide ou bloqué.
    """

    valide = "valide"
    bloque = "bloque"
    partiellement_valide = "partiellement_valide"


class ResultatControle(StrEnum):
    """Résultat d'un contrôle individuel (`§5`)."""

    conforme = "conforme"
    non_conforme = "non_conforme"
    non_applicable = "non_applicable"


class TypeCauseBlocage(StrEnum):
    """Causes de blocage — chacune correspond à une garantie violée (`§5`).

    Mapping vers les articles constitutionnels :
    - `sans_niveau_preuve`, `sans_source` → GSIE-CON-002
    - `sans_chaine_inference`, `explicabilite_insuffisante` → GSIE-CON-004
    - `hors_domaine_validite`, `connaissance_obsolete`,
      `contradiction_non_signalee` → GSIE-CON-005
    - `recommandation_non_contournable` → GSIE-CON-001
    """

    sans_niveau_preuve = "sans_niveau_preuve"
    sans_source = "sans_source"
    sans_chaine_inference = "sans_chaine_inference"
    hors_domaine_validite = "hors_domaine_validite"
    connaissance_obsolete = "connaissance_obsolete"
    contradiction_non_signalee = "contradiction_non_signalee"
    recommandation_non_contournable = "recommandation_non_contournable"
    explicabilite_insuffisante = "explicabilite_insuffisante"


class ControleResultat(BaseModel):
    """Résultat d'un contrôle individuel (`§5`)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nom_controle: str = Field(min_length=1, max_length=200)
    resultat: ResultatControle
    details: str = Field(min_length=1, max_length=2000)


class CauseBlocage(BaseModel):
    """Cause de blocage d'une sortie (`§5`)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    type_cause: TypeCauseBlocage
    element_concerne: UUID
    description: str = Field(min_length=1, max_length=2000)


class ValidationRequest(BaseModel):
    """Entrée du Validation Engine (`VALIDATION_ENGINE.md` §5).

    `contenu` est une structure libre typée par `type_sortie` : le
    moteur valide structurellement selon le type déclaré. Une requête
    `ensemble_complet` exige à la fois un diagnostic et un
    RecommendationSet dans `contenu`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    requete_id: UUID
    type_sortie: TypeSortie
    contenu: dict[str, Any] = Field(
        description="Diagnostic ou RecommendationSet sérialisé (selon type_sortie)"
    )
    chaines_inference: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Chaînes d'inférence du Reasoning Engine (optionnel)",
    )
    connaissances_utilisees: list[UUID] = Field(
        default_factory=list,
        description="Identifiants des KnowledgeObject mobilisés",
    )

    @model_validator(mode="after")
    def _ensemble_complet_exige_diagnostic_et_recommandation(self) -> "ValidationRequest":
        if self.type_sortie == TypeSortie.ensemble_complet and (
            "diagnostic" not in self.contenu or "recommandations" not in self.contenu
        ):
            raise ValueError(
                "type_sortie='ensemble_complet' exige 'diagnostic' et "
                "'recommandations' dans contenu"
            )
        return self


class ValidationResult(BaseModel):
    """Sortie du Validation Engine (`VALIDATION_ENGINE.md` §5).

    Invariant : si `statut = bloque`, `causes_blocage` est non vide.
    Réciproquement, si `statut = valide`, `causes_blocage` est vide.
    `partiellement_valide` autorise un mélange : certains contrôles
    non conformes sur une partie de l'ensemble, sans bloquer l'ensemble.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    validation_id: UUID
    requete_origine: UUID
    statut: ValidationStatut
    controles: list[ControleResultat] = Field(min_length=1, max_length=100)
    causes_blocage: list[CauseBlocage] = Field(default_factory=list, max_length=50)
    date_validation: datetime

    @model_validator(mode="after")
    def _coherence_statut_causes(self) -> "ValidationResult":
        if self.statut == ValidationStatut.bloque and not self.causes_blocage:
            raise ValueError("statut='bloque' exige au moins une cause de blocage")
        if self.statut == ValidationStatut.valide and self.causes_blocage:
            raise ValueError("statut='valide' ne peut pas porter de causes de blocage")
        return self

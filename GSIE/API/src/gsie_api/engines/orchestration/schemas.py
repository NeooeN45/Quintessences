"""Contrat de l'orchestration — un appel pour toute la chaîne.

    Reasoning → Diagnostic → Recommendation → Validation

L'orchestration **ne décide de rien**. Elle branche la sortie d'un moteur sur
l'entrée du suivant, comme `pipeline.py` le fait déjà pour Evidence → Knowledge,
et respecte la même règle : aucune logique métier ajoutée (`GSIE-CON-007`).

Deux informations que la chaîne exige ne peuvent donc pas être déduites ici :

* la **qualification** de chaque conclusion — rôle et domaine. Le Diagnostic
  Engine le dit de lui-même : « Le contrat §5 suppose que le moteur sait classer
  une conclusion. Il ne le sait pas et ne doit pas le deviner. »
* l'**état global** du peuplement, déclaré et sourcé comme n'importe quelle
  affirmation : « Déduire "dépérissement" d'un ensemble de contraintes exigerait
  une fonction de score que le moteur ne possède pas et ne peut pas inventer. »

Les deux sont donc déclarés par l'appelant. Difficulté : une qualification
désigne une conclusion, et les conclusions n'existent qu'**après** l'inférence.
L'appelant déclare par conséquent ses qualifications **par identifiant de
règle** — il connaît les règles qu'il soumet — et l'orchestration fait le lien
via `conclusion_id_pour`, la dérivation que le Reasoning Engine utilise
lui-même. Aucune correspondance approchée, aucun rapprochement par ressemblance
de texte.

Une règle qui produit une conclusion sans qualification déclarée fait refuser
l'appel, en nommant la règle. Choisir un rôle par défaut reviendrait à classer
une conclusion à la place du forestier.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from gsie_api.engines.diagnostic.schemas import (
    Diagnostic,
    DomaineElement,
    DomaineRisque,
    EtatGlobalDeclare,
    Probabilite,
    RoleDiagnostic,
    TypeDiagnostic,
)
from gsie_api.engines.reasoning.schemas import (
    InferenceResult,
    ReasoningRequest,
    RegleInference,
    StationContexte,
)
from gsie_api.engines.recommendation.schemas import ObjectifForestier, RecommendationSet
from gsie_api.engines.validation.schemas import ValidationResult

__all__ = [
    "AnalyseComplete",
    "AnalyseRequest",
    "QualificationParRegle",
]


class QualificationParRegle(BaseModel):
    """Rôle et domaine à donner à la conclusion issue d'une règle.

    Reprend `QualificationConclusion` sans son `conclusion_id` : l'appelant ne
    peut pas le connaître avant l'inférence. Les mêmes champs, les mêmes règles
    de cohérence — un risque sans probabilité ni horizon n'est pas un risque.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    identifiant_regle: str = Field(
        min_length=1,
        max_length=200,
        description="Identifiant de la règle soumise, tel qu'il figure dans `regles`",
    )
    role: RoleDiagnostic
    domaine_element: DomaineElement | None = Field(
        default=None, description="Obligatoire pour une contrainte ou un atout"
    )
    domaine_risque: DomaineRisque | None = Field(
        default=None, description="Obligatoire pour un risque"
    )
    probabilite: Probabilite | None = Field(default=None, description="Obligatoire pour un risque")
    horizon: str | None = Field(
        default=None, max_length=100, description="Obligatoire pour un risque"
    )


class AnalyseRequest(BaseModel):
    """Entrée unique de la chaîne complète.

    Rassemble ce que les quatre moteurs exigent, sans rien y ajouter. Les
    champs dont un moteur a besoin et qu'aucun autre ne produit — les
    qualifications, l'état global — sont déclarés ici parce qu'ils ne se
    déduisent pas.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    requete_id: UUID
    station_id: UUID
    contexte: StationContexte
    regles: list[RegleInference] = Field(
        min_length=1,
        description=(
            "Règles d'inférence, chacune avec sa source et son niveau de preuve. "
            "Fournies dans la requête en v1, comme pour le Reasoning Engine "
            "appelé seul ; une version ultérieure les récupérera du Knowledge "
            "Engine à partir du territoire."
        ),
    )
    qualifications: list[QualificationParRegle] = Field(
        min_length=1,
        description=(
            "Une par règle susceptible de conclure. Une conclusion sans "
            "qualification déclarée fait refuser l'appel — la classer d'office "
            "reviendrait à décider à la place du forestier (`GSIE-CON-001`)."
        ),
    )
    etat_global: EtatGlobalDeclare = Field(
        description=(
            "Déclaré et sourcé. Le Diagnostic Engine ne le déduit pas des "
            "contraintes : cela exigerait une fonction de score qu'il n'a pas."
        )
    )
    type_diagnostic: TypeDiagnostic = TypeDiagnostic.stationnel
    question: str = Field(
        min_length=1,
        max_length=500,
        description="Question posée au raisonnement, reprise telle quelle",
    )
    objectif_forestier: ObjectifForestier
    alternatives_demandees: bool = True
    profondeur_max: int = Field(default=5, ge=1, le=20)

    def vers_requete_raisonnement(self) -> ReasoningRequest:
        """Extrait la requête du premier maillon, sans rien transformer."""
        return ReasoningRequest(
            requete_id=self.requete_id,
            station_id=self.station_id,
            contexte=self.contexte,
            question=self.question,
            regles=list(self.regles),
            profondeur_max=self.profondeur_max,
        )


class AnalyseComplete(BaseModel):
    """Sortie de la chaîne — chaque étape reste lisible séparément.

    Les quatre sorties intermédiaires sont retournées, et non seulement la
    dernière. Un forestier à qui l'on présenterait la seule recommandation ne
    pourrait ni voir le raisonnement qui la fonde, ni le diagnostic qu'elle
    invoque, ni ce que la validation a contrôlé : `GSIE-CON-004` exige que la
    sortie soit explicable, et une explication qu'il faut redemander en
    plusieurs appels n'en est pas tout à fait une.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    requete_origine: UUID
    inference: InferenceResult
    diagnostic: Diagnostic
    recommandations: RecommendationSet
    validation: ValidationResult

    @property
    def resume(self) -> dict[str, Any]:
        """Vue courte pour la journalisation — jamais pour l'affichage."""
        return {
            "n_conclusions": len(self.inference.conclusions),
            "etat_global": self.diagnostic.etat_global.value,
            "plancher": self.diagnostic.evidence_level_plancher.value,
            "n_recommandations": len(self.recommandations.recommandations),
            "statut_validation": self.validation.statut.value,
        }

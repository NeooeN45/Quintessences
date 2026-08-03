"""Orchestration de la chaîne complète — branchement, jamais décision.

    Reasoning → Diagnostic → Recommendation → Validation

Ce module n'ajoute aucune logique métier (`GSIE-CON-007`). Il reprend le
précédent de `pipeline.py`, qui « ne fait que connecter les sorties de l'un aux
entrées de l'autre » pour Evidence → Knowledge.

Pourquoi il existe : aucun endpoint ne couvrait la chaîne, et les conversions
entre moteurs vivaient dans `validation_pipeline.py` sans être exposées. Un
client — l'application GeoSylva — devait donc enchaîner cinq appels et
reproduire ces conversions de son côté, chaque passage de main étant un point
de rupture que rien ne surveillait.

Ce que ce module refuse de faire, et qui est l'essentiel :

* il ne qualifie aucune conclusion — l'appelant le déclare, par règle ;
* il ne déduit aucun état global — l'appelant le déclare et le source ;
* il ne comble aucun manque par une valeur par défaut. Une conclusion sans
  qualification déclarée fait refuser l'appel, en nommant la règle.

Choisir un rôle par défaut serait classer une conclusion à la place du
forestier, et le conseil sylvicole qui en découlerait citerait une chaîne
complète — invisible (`ADR-009`, `GSIE-CON-001`).
"""

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.engines.diagnostic.engine import DiagnosticEngine
from gsie_api.engines.diagnostic.schemas import (
    DiagnosticRequest,
    QualificationConclusion,
)
from gsie_api.engines.orchestration.schemas import AnalyseComplete, AnalyseRequest
from gsie_api.engines.reasoning.engine import ReasoningEngine, conclusion_id_pour
from gsie_api.engines.reasoning.schemas import Conclusion
from gsie_api.engines.recommendation.engine import RecommendationEngine
from gsie_api.engines.recommendation.schemas import RecommendationRequest
from gsie_api.engines.validation.engine import ValidationEngine
from gsie_api.engines.validation_pipeline import ensemble_complet_to_validation_request

logger = get_logger("gsie_api.orchestration")

__all__ = ["AnalyseImpossibleError", "OrchestrationEngine"]


class AnalyseImpossibleError(Exception):
    """La chaîne ne peut pas se dérouler avec ce qui a été déclaré.

    Distincte des erreurs des moteurs : elle signale un manque dans la requête,
    que l'appelant peut corriger. Le message nomme toujours ce qui manque —
    « analyse impossible » sans motif obligerait à deviner.
    """


class OrchestrationEngine:
    """Enchaîne les quatre moteurs sur une session partagée.

    La session est unique pour toute la chaîne : le diagnostic est persisté par
    son moteur, puis relu par le Recommendation Engine. Deux sessions
    distinctes feraient échouer cette relecture sur un diagnostic pourtant
    écrit — ce qui se lirait comme un diagnostic introuvable.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def version() -> str:
        """Version de l'orchestration."""
        return "0.1.0"

    async def analyser(self, requete: AnalyseRequest, maintenant: datetime) -> AnalyseComplete:
        """Déroule la chaîne complète et retourne chaque étape.

        `maintenant` est une entrée et non une lecture d'horloge : le Reasoning
        Engine et le Diagnostic Engine l'exigent tous deux pour rester
        déterministes, et une horloge lue ici les rendrait intestables.

        Raises:
            AnalyseImpossibleError: si le raisonnement ne conclut rien, ou si
                une conclusion n'a pas de qualification déclarée.
            ReasoningEngineError, DiagnosticEngineError, RecommendationEngineError:
                remontées telles quelles — l'orchestration ne les traduit pas,
                et une erreur du Diagnostic Engine doit se lire comme telle.
        """
        inference = await ReasoningEngine(self._session).infer(
            requete.vers_requete_raisonnement(), maintenant
        )
        if not inference.conclusions:
            raise AnalyseImpossibleError(
                "le raisonnement n'a produit aucune conclusion : aucune règle "
                "fournie ne s'applique au contexte déclaré. Un diagnostic sans "
                "conclusion serait vide, et une recommandation ne reposerait sur "
                "rien"
            )

        qualifications = self._qualifier(requete, inference.conclusions)

        diagnostic = await DiagnosticEngine(self._session).diagnostiquer(
            DiagnosticRequest(
                requete_id=requete.requete_id,
                station_id=requete.station_id,
                conclusions=list(inference.conclusions),
                qualifications=qualifications,
                etat_global=requete.etat_global,
                contexte=requete.contexte,
                type_diagnostic=requete.type_diagnostic,
            ),
            maintenant,
        )

        recommandations = await RecommendationEngine(self._session).recommend(
            RecommendationRequest(
                requete_id=requete.requete_id,
                diagnostic_id=diagnostic.diagnostic_id,
                objectif_forestier=requete.objectif_forestier,
                alternatives_demandees=requete.alternatives_demandees,
            )
        )

        validation = await ValidationEngine().validate(
            ensemble_complet_to_validation_request(
                diagnostic, recommandations, list(inference.conclusions)
            )
        )

        resultat = AnalyseComplete(
            requete_origine=requete.requete_id,
            inference=inference,
            diagnostic=diagnostic,
            recommandations=recommandations,
            validation=validation,
        )
        logger.info(
            "analyse_complete",
            requete_id=str(requete.requete_id),
            **resultat.resume,
        )
        return resultat

    def _qualifier(
        self, requete: AnalyseRequest, conclusions: list[Conclusion]
    ) -> list[QualificationConclusion]:
        """Rattache chaque conclusion à la qualification déclarée pour sa règle.

        Le rattachement passe par `conclusion_id_pour`, la dérivation que le
        Reasoning Engine emploie lui-même. Rapprocher par ressemblance d'énoncé
        serait fragile — deux règles peuvent conclure la même chose — et une
        erreur de rapprochement classerait une conclusion sous un rôle qui n'est
        pas le sien, sans que rien ne le signale.

        Une conclusion sans qualification déclarée fait refuser l'appel. Le
        Diagnostic Engine exige de toute façon la bijection ; refuser ici permet
        de nommer la **règle** fautive, que l'appelant connaît, plutôt qu'un
        identifiant de conclusion qu'il n'a jamais vu.
        """
        par_conclusion: dict[UUID, QualificationConclusion] = {}
        for declaree in requete.qualifications:
            identifiant = conclusion_id_pour(requete.requete_id, declaree.identifiant_regle)
            par_conclusion[identifiant] = QualificationConclusion(
                conclusion_id=identifiant,
                role=declaree.role,
                domaine_element=declaree.domaine_element,
                domaine_risque=declaree.domaine_risque,
                probabilite=declaree.probabilite,
                horizon=declaree.horizon,
            )

        # Les regles dont une conclusion est sortie mais qu'aucune
        # qualification ne couvre. On les renomme par leur identifiant de
        # regle : c'est ce que l'appelant a ecrit.
        regles_par_conclusion = {
            conclusion_id_pour(requete.requete_id, regle.identifiant): regle.identifiant
            for regle in requete.regles
        }
        manquantes = [
            regles_par_conclusion.get(conclusion.conclusion_id, str(conclusion.conclusion_id))
            for conclusion in conclusions
            if conclusion.conclusion_id not in par_conclusion
        ]
        if manquantes:
            raise AnalyseImpossibleError(
                "conclusion(s) sans qualification déclarée, pour la ou les "
                f"règles : {', '.join(sorted(manquantes))}. Déclarez leur rôle "
                "et leur domaine — le moteur ne classe pas une conclusion à "
                "votre place (GSIE-CON-001)"
            )

        return [par_conclusion[conclusion.conclusion_id] for conclusion in conclusions]

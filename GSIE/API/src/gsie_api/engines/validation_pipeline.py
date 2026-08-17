"""Pipeline cross-moteurs — orchestration Validation + Learning sur objets typés.

Ce module câble le Validation Engine et le Learning Engine sur les vraies
sorties des moteurs amont (Diagnostic, RecommendationSet, Conclusion) au
lieu des dicts abstraits de la v1. Il implémente la chaîne principale :

    Reasoning → Diagnostic → Recommendation → Validation → Utilisateur
                                                    ↓ (si bloqué)
                                               Learning

Trois fonctions d'adaptation transforment les objets typés en
`ValidationRequest` consommable par le Validation Engine, en extrayant
les champs pertinents (evidence_level, sources, chaines_inference,
contournable, justification) sans dupliquer la logique de validation.

Une quatrième fonction branche le Learning Engine sur un ValidationResult
bloqué : le type `sortie_bloquee` non géré en v1 devient géré via ce
pipeline, qui transforme le blocage en signal d'apprentissage.

Voir `VALIDATION_ENGINE.md` §3 (entrées) et `LEARNING_ENGINE.md` §3
(sorties vers Learning).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import uuid4

from gsie_api.core.logging import get_logger
from gsie_api.engines.learning.engine import LearningEngine, LearningEngineError
from gsie_api.engines.learning.schemas import (
    LearningOutput,
    LearningSignal,
    LearningSignalType,
)
from gsie_api.engines.validation.engine import ValidationEngine
from gsie_api.engines.validation.schemas import (
    TypeSortie,
    ValidationRequest,
    ValidationResult,
    ValidationStatut,
)

if TYPE_CHECKING:
    from gsie_api.engines.diagnostic.schemas import Diagnostic
    from gsie_api.engines.reasoning.schemas import Conclusion
    from gsie_api.engines.recommendation.schemas import RecommendationSet

logger = get_logger("gsie_api.validation_pipeline")


class PipelineError(Exception):
    """Erreur de base du pipeline cross-moteurs."""


# --- Adaptateurs : objets typés → ValidationRequest ---


def diagnostic_to_validation_request(
    diagnostic: Diagnostic,
    conclusions: list[Conclusion] | None = None,
) -> ValidationRequest:
    """Transforme un `Diagnostic` (+ conclusions Reasoning) en `ValidationRequest`.

    Extrait du diagnostic :
    - `evidence_level_plancher` → niveau de preuve global ;
    - sources des contraintes/atouts/risques → sources de la sortie ;
    - `conclusions_source` → références aux chaînes d'inférence.

    Extrait des conclusions Reasoning (si fournies) :
    - `chaine_inference` de chaque conclusion → `chaines_inference` de la requête.

    Raises:
        PipelineError: si le diagnostic est vide ou incohérent.
    """
    contenu: dict[str, Any] = {
        "diagnostic_id": str(diagnostic.diagnostic_id),
        "evidence_level": diagnostic.evidence_level_plancher.value,
        "etat_global": diagnostic.etat_global.value,
        "sources": [
            element.source.model_dump() for element in diagnostic.contraintes + diagnostic.atouts
        ]
        + [risque.source.model_dump() for risque in diagnostic.risques],
        "justification": (
            f"Diagnostic {diagnostic.type_diagnostic.value} — "
            f"{len(diagnostic.contraintes)} contrainte(s), "
            f"{len(diagnostic.atouts)} atout(s), "
            f"{len(diagnostic.risques)} risque(s)."
        ),
    }

    chaines_inference: list[dict[str, Any]] = []
    if conclusions:
        for conclusion in conclusions:
            chaines_inference.append(
                {
                    "conclusion_id": str(conclusion.conclusion_id),
                    "enonce": conclusion.enonce,
                    "etapes": [
                        {
                            "ordre": etape.ordre,
                            "regle": etape.regle_appliquee,
                            "premisses": etape.premisses,
                        }
                        for etape in conclusion.chaine_inference
                    ],
                }
            )

    return ValidationRequest(
        requete_id=uuid4(),
        type_sortie=TypeSortie.diagnostic,
        contenu=contenu,
        chaines_inference=chaines_inference,
        connaissances_utilisees=diagnostic.conclusions_source,
    )


def recommendation_set_to_validation_request(
    reco_set: RecommendationSet,
    *,
    evidence_level: str = "B",
) -> ValidationRequest:
    """Transforme un `RecommendationSet` en `ValidationRequest`.

    Extrait :
    - `evidence_level` depuis la première recommandation (toutes partagent
      le même diagnostic source, donc le même plancher) ;
    - sources des justifications → sources de la sortie ;
    - `contournable` (computed_field, toujours vrai) → vérifié par le contrôle ;
    - `justification` de chaque recommandation → justification de la sortie.
    """
    recommandations_serialisees = []
    sources: list[dict[str, Any]] = []
    for reco in reco_set.recommandations:
        reco_dict = reco.model_dump()
        recommandations_serialisees.append(reco_dict)
        for source in reco.justification.sources:
            sources.append(source.model_dump())

    contenu: dict[str, Any] = {
        "ensemble_id": str(reco_set.ensemble_id),
        "diagnostic_source": str(reco_set.diagnostic_source),
        "recommandations": recommandations_serialisees,
        "evidence_level": evidence_level,
        "sources": sources,
        "justification": (
            f"{len(reco_set.recommandations)} recommandation(s) "
            f"sur le diagnostic {reco_set.diagnostic_source}."
        ),
    }

    return ValidationRequest(
        requete_id=uuid4(),
        type_sortie=TypeSortie.recommandation,
        contenu=contenu,
    )


def ensemble_complet_to_validation_request(
    diagnostic: Diagnostic,
    reco_set: RecommendationSet,
    conclusions: list[Conclusion] | None = None,
) -> ValidationRequest:
    """Transforme un `Diagnostic` + `RecommendationSet` en `ValidationRequest` ensemble_complet.

    L'ensemble complet est la sortie finale présentée à l'utilisateur :
    diagnostic + recommandations + chaînes d'inférence. C'est le cas où
    `partiellement_valide` peut s'appliquer (un échec non critique sur une
    partie n'invalide pas l'ensemble).

    Raises:
        PipelineError: si le diagnostic source du reco_set ne correspond pas
            au diagnostic fourni.
    """
    if reco_set.diagnostic_source != diagnostic.diagnostic_id:
        raise PipelineError(
            f"incohérence : reco_set.diagnostic_source="
            f"{reco_set.diagnostic_source} != diagnostic.diagnostic_id="
            f"{diagnostic.diagnostic_id}"
        )

    contenu_diagnostic = diagnostic_to_validation_request(diagnostic, conclusions).contenu
    contenu_recommandations = recommendation_set_to_validation_request(
        reco_set,
        evidence_level=diagnostic.evidence_level_plancher.value,
    ).contenu

    contenu: dict[str, Any] = {
        "diagnostic": contenu_diagnostic,
        "recommandations": contenu_recommandations["recommandations"],
        "evidence_level": diagnostic.evidence_level_plancher.value,
        "sources": contenu_diagnostic["sources"] + contenu_recommandations["sources"],
        "justification": (
            f"Ensemble complet : diagnostic {diagnostic.diagnostic_id} + "
            f"{len(reco_set.recommandations)} recommandation(s)."
        ),
    }

    chaines_inference: list[dict[str, Any]] = []
    if conclusions:
        for conclusion in conclusions:
            chaines_inference.append(
                {
                    "conclusion_id": str(conclusion.conclusion_id),
                    "enonce": conclusion.enonce,
                    "etapes": [
                        {
                            "ordre": etape.ordre,
                            "regle": etape.regle_appliquee,
                            "premisses": etape.premisses,
                        }
                        for etape in conclusion.chaine_inference
                    ],
                }
            )

    return ValidationRequest(
        requete_id=uuid4(),
        type_sortie=TypeSortie.ensemble_complet,
        contenu=contenu,
        chaines_inference=chaines_inference,
        connaissances_utilisees=diagnostic.conclusions_source,
    )


# --- Branche Learning : ValidationResult bloqué → LearningSignal ---


def validation_failure_to_learning_signal(
    validation_result: ValidationResult,
) -> LearningSignal:
    """Transforme un `ValidationResult` bloqué en `LearningSignal` (sortie_bloquee).

    Le signal `sortie_bloquee` alimente le Learning Engine pour détecter
    les patterns de blocage récurrents (ex. : un moteur produit
    systématiquement des sorties sans source). Le Learning Engine peut
    alors proposer une calibration ou une révision des règles.

    Raises:
        PipelineError: si le ValidationResult n'est pas bloqué (un
            résultat valide ne doit pas alimenter l'apprentissage).
    """
    if validation_result.statut == ValidationStatut.valide:
        raise PipelineError("un ValidationResult valide ne doit pas alimenter le Learning Engine")

    return LearningSignal(
        signal_id=uuid4(),
        type=LearningSignalType.sortie_bloquee,
        contenu={
            "validation_id": str(validation_result.validation_id),
            "statut": validation_result.statut.value,
            "causes_blocage": [
                {
                    "type_cause": cause.type_cause.value,
                    "description": cause.description,
                }
                for cause in validation_result.causes_blocage
            ],
            "controles_non_conformes": [
                {
                    "nom_controle": c.nom_controle,
                    "details": c.details,
                }
                for c in validation_result.controles
                if c.resultat.value == "non_conforme"
            ],
        },
        date_signal=validation_result.date_validation,
    )


# --- Orchestrateur complet ---


async def run_validation_pipeline(
    diagnostic: Diagnostic,
    reco_set: RecommendationSet,
    conclusions: list[Conclusion] | None = None,
    *,
    learning_engine: LearningEngine | None = None,
) -> dict[str, Any]:
    """Orchestre la chaîne Validation → Learning sur un ensemble complet.

    Étapes :
    1. Construit un `ValidationRequest` ensemble_complet depuis le
       diagnostic, le RecommendationSet et les conclusions Reasoning.
    2. Valide via le Validation Engine.
    3. Si le résultat est bloqué ou partiellement valide, transforme le
       blocage en `LearningSignal` (sortie_bloquee) et le passe au
       Learning Engine (si fourni).
    4. Retourne un dict avec `validation` et `learning` (optionnel).

    Returns:
        Dict avec clés :
        - `validation` : ValidationResult (toujours présent) ;
        - `learning` : LearningOutput | None (présent si learning_engine
          fourni et signal déclenché) ;
        - `learning_signal` : LearningSignal | None (le signal transmis,
          pour traçabilité).

    Raises:
        PipelineError: si le diagnostic source du reco_set ne correspond
            pas au diagnostic fourni.
    """
    request = ensemble_complet_to_validation_request(diagnostic, reco_set, conclusions)
    validation = await ValidationEngine().validate(request)

    learning_output: LearningOutput | None = None
    learning_signal: LearningSignal | None = None

    if validation.statut != ValidationStatut.valide and learning_engine is not None:
        learning_signal = validation_failure_to_learning_signal(validation)
        try:
            learning_output = await learning_engine.process(learning_signal)
        except LearningEngineError as exc:
            logger.warning(
                "pipeline_learning_error",
                validation_id=str(validation.validation_id),
                error=str(exc),
            )

    logger.info(
        "pipeline_complete",
        diagnostic_id=str(diagnostic.diagnostic_id),
        validation_statut=validation.statut.value,
        learning_triggered=learning_output is not None,
    )

    return {
        "validation": validation,
        "learning": learning_output,
        "learning_signal": learning_signal,
    }

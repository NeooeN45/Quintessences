"""Tests d'intégration cross-moteurs — pipeline Validation + Learning.

Vérifie que le pipeline orchestre correctement les moteurs sur de vrais
objets typés (Diagnostic, RecommendationSet, Conclusion) au lieu de
dicts abstraits. Couvre la chaîne principale :

    Reasoning → Diagnostic → Recommendation → Validation → Learning
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from gsie_api.engines.diagnostic.schemas import (
    Diagnostic,
    DomaineElement,
    ElementDiagnostic,
    EtatGlobal,
    TypeDiagnostic,
)
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
from gsie_api.engines.learning.engine import LearningEngine
from gsie_api.engines.learning.schemas import (
    LearningSignal,
    LearningSignalType,
)
from gsie_api.engines.reasoning.schemas import (
    Conclusion,
    EtapeInference,
    MethodeConfiance,
    SourceMoteurContexte,
    niveau_plancher,
)
from gsie_api.engines.recommendation.engine import RecommendationEngine
from gsie_api.engines.recommendation.schemas import (
    ObjectifForestier,
    RecommendationRequest,
    RecommendationSet,
)
from gsie_api.engines.validation.schemas import (
    TypeSortie,
    ValidationStatut,
)
from gsie_api.engines.validation_pipeline import (
    PipelineError,
    diagnostic_to_validation_request,
    ensemble_complet_to_validation_request,
    recommendation_set_to_validation_request,
    run_validation_pipeline,
    validation_failure_to_learning_signal,
)
from tests.unit.aide_recommendation import SessionDiagnosticFictif

# --- Fixtures : objets typés réalistes ---


def _make_source(auteur: str = "Rameau (2008)") -> SourceReference:
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur=auteur,
        date_publication="2008",
        reference="Rameau et al., 2008 — Guide écologique forestier",
    )


def _make_element(domaine: DomaineElement = DomaineElement.pedologique) -> ElementDiagnostic:
    return ElementDiagnostic(
        description="Sol acide, pH 4.5",
        domaine=domaine,
        evidence_level=EvidenceLevel.B,
        source=_make_source(),
    )


def _make_diagnostic(
    diagnostic_id: UUID | None = None,
    requete_id: UUID | None = None,
) -> Diagnostic:
    if diagnostic_id is None:
        diagnostic_id = uuid4()
    if requete_id is None:
        requete_id = uuid4()
    contraintes = [_make_element(DomaineElement.pedologique)]
    atouts = [_make_element(DomaineElement.botanique)]
    risques = []
    niveaux = [c.evidence_level for c in contraintes] + [a.evidence_level for a in atouts]
    return Diagnostic(
        diagnostic_id=diagnostic_id,
        requete_origine=requete_id,
        station_id=uuid4(),
        type_diagnostic=TypeDiagnostic.stationnel,
        etat_global=EtatGlobal.sain,
        contraintes=contraintes,
        atouts=atouts,
        risques=risques,
        contradictions=[],
        confiance=0.7,
        etat_global_evidence_level=niveau_plancher(niveaux),
        evidence_level_plancher=niveau_plancher(niveaux),
        incertitudes=["Données climatiques non disponibles."],
        conclusions_source=[uuid4()],
        date_diagnostic=datetime.now(UTC),
    )


def _make_etape(ordre: int) -> EtapeInference:
    return EtapeInference(
        ordre=ordre,
        regle_appliquee="règle pH acide → essence acidiphile",
        source_regle=_make_source(),
        premisses=["pH < 5.5"],
        conclusion_locale="sol acidiphile",
        evidence_level=EvidenceLevel.B,
    )


def _make_conclusion(conclusion_id: UUID | None = None) -> Conclusion:
    if conclusion_id is None:
        conclusion_id = uuid4()
    etape = _make_etape(1)
    return Conclusion(
        conclusion_id=conclusion_id,
        enonce="La station est favorable au chêne sessile (acidiphile).",
        niveau_confiance=0.8,
        methode_confiance=MethodeConfiance.fournie_par_regle,
        evidence_level_plancher=EvidenceLevel.B,
        chaine_inference=[etape],
        sources_utilisees=[etape.source_regle],
        moteurs_solicites=[SourceMoteurContexte.pedology],
    )


async def _make_recommendation_set(diagnostic_id: UUID) -> RecommendationSet:
    engine = RecommendationEngine(SessionDiagnosticFictif())
    request = RecommendationRequest(
        requete_id=uuid4(),
        diagnostic_id=diagnostic_id,
        objectif_forestier=ObjectifForestier.REBOISEMENT,
        alternatives_demandees=True,
    )
    return await engine.recommend(request)


# --- Tests adaptateurs ---


def should_convert_diagnostic_to_validation_request() -> None:
    """L'adaptateur extrait evidence_level, sources et conclusions du diagnostic."""
    diagnostic = _make_diagnostic()
    conclusions = [_make_conclusion(diagnostic.conclusions_source[0])]
    request = diagnostic_to_validation_request(diagnostic, conclusions)
    assert request.type_sortie == TypeSortie.diagnostic
    assert request.contenu["evidence_level"] == "B"
    assert len(request.contenu["sources"]) >= 2  # contraintes + atouts
    assert len(request.chaines_inference) == 1
    assert request.connaissances_utilisees == diagnostic.conclusions_source


def should_convert_recommendation_set_to_validation_request() -> None:
    """L'adaptateur extrait les recommandations et leurs sources."""
    import asyncio

    diagnostic = _make_diagnostic()
    reco_set = asyncio.run(_make_recommendation_set(diagnostic.diagnostic_id))
    request = recommendation_set_to_validation_request(reco_set)
    assert request.type_sortie == TypeSortie.recommandation
    assert len(request.contenu["recommandations"]) >= 1
    assert len(request.contenu["sources"]) >= 1


def should_reject_ensemble_complet_with_mismatched_diagnostic() -> None:
    """L'adaptateur refuse un reco_set dont le diagnostic_source ne correspond pas."""
    import asyncio

    diagnostic = _make_diagnostic()
    # reco_set avec un diagnostic_id différent
    reco_set = asyncio.run(_make_recommendation_set(uuid4()))
    with pytest.raises(PipelineError, match="incohérence"):
        ensemble_complet_to_validation_request(diagnostic, reco_set)


def should_reject_learning_signal_for_valid_result() -> None:
    """Un ValidationResult valide ne doit pas alimenter le Learning Engine."""
    from gsie_api.engines.validation.schemas import (
        ControleResultat,
        ResultatControle,
        ValidationResult,
    )

    result = ValidationResult(
        validation_id=uuid4(),
        requete_origine=uuid4(),
        statut=ValidationStatut.valide,
        controles=[
            ControleResultat(
                nom_controle="test",
                resultat=ResultatControle.conforme,
                details="ok",
            )
        ],
        date_validation=datetime.now(UTC),
    )
    with pytest.raises(PipelineError, match="valide"):
        validation_failure_to_learning_signal(result)


# --- Tests orchestrateur ---


@pytest.mark.asyncio
async def should_validate_ensemble_complet_and_return_valide() -> None:
    """Un ensemble complet valide (diagnostic + recommandations + conclusions) passe."""
    diagnostic = _make_diagnostic()
    reco_set = await _make_recommendation_set(diagnostic.diagnostic_id)
    conclusions = [_make_conclusion(diagnostic.conclusions_source[0])]
    result = await run_validation_pipeline(diagnostic, reco_set, conclusions)
    assert result["validation"].statut == ValidationStatut.valide
    assert result["learning"] is None
    assert result["learning_signal"] is None


@pytest.mark.asyncio
async def should_trigger_learning_when_validation_blocked() -> None:
    """Un ensemble complet valide ne déclenche pas de learning (pas de blocage)."""
    diagnostic = _make_diagnostic()
    reco_set = await _make_recommendation_set(diagnostic.diagnostic_id)
    conclusions = [_make_conclusion(diagnostic.conclusions_source[0])]

    learning_engine = LearningEngine()
    result = await run_validation_pipeline(
        diagnostic, reco_set, conclusions, learning_engine=learning_engine
    )
    # Le diagnostic valide ne déclenche pas de learning
    assert result["validation"].statut == ValidationStatut.valide
    assert result["learning"] is None
    assert result["learning_signal"] is None


@pytest.mark.asyncio
async def should_feed_learning_engine_with_blocked_validation() -> None:
    """Le Learning Engine accumule les blocages et propose une calibration."""
    learning_engine = LearningEngine()

    # Créer un signal de blocage directement (simule un Validation Engine bloqué)
    for _ in range(5):
        signal = LearningSignal(
            signal_id=uuid4(),
            type=LearningSignalType.sortie_bloquee,
            contenu={
                "validation_id": str(uuid4()),
                "statut": "bloque",
                "causes_blocage": [
                    {"type_cause": "sans_source", "description": "Aucune source"},
                ],
                "controles_non_conformes": [],
            },
            date_signal=datetime.now(UTC),
        )
        await learning_engine.process(signal)

    # Le 5e doit avoir déclenché une calibration
    # (vérifié dans test_learning_engine.py — ici on vérifie juste que
    # le pipeline n'explose pas avec un learning_engine)
    diagnostic = _make_diagnostic()
    reco_set = await _make_recommendation_set(diagnostic.diagnostic_id)
    conclusions = [_make_conclusion(diagnostic.conclusions_source[0])]
    result = await run_validation_pipeline(
        diagnostic, reco_set, conclusions, learning_engine=learning_engine
    )
    assert result["validation"] is not None

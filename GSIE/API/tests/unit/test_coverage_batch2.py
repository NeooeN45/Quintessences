"""Tests de couverture — batch 2.

Couvre les comportements suivants :

1. ``engines/orchestration/service.py`` — chemin nominal de ``analyser``
   (enchaînement des quatre moteurs) et propriété ``resume`` de
   ``AnalyseComplete``.
2. ``engines/diagnostic/schemas.py`` — validateurs de
   ``QualificationConclusion`` (cohérence des champs selon le rôle),
   ``ContradictionDeclaree`` (conclusions distinctes) et
   ``DiagnosticRequest`` (bijection qualifications/conclusions,
   contradictions référençant des conclusions existantes).
3. ``engines/reasoning/schemas.py`` — validateur de cohérence entre
   ``resultat_partiel`` et ``regles_non_appliquees`` de
   ``InferenceResult``.
4. ``engines/simulation/schemas.py`` — validateur interdisant les
   alternatives imbriquées de ``SimulationResult``.
5. ``engines/correlation/schemas.py`` — validateur de l'appariement des
   valeurs de ``CorrelationComputeRequest``.

Conventions (AGENTS.md API) : pytest-asyncio mode ``auto``, nommage
``should_[expected]_when_[condition]``, structure Arrange → Act → Assert.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from gsie_api.engines.correlation.schemas import (
    CorrelationComputeRequest,
    DomaineCorrelation,
    ParametreCorrelation,
    SourceMoteur,
)
from gsie_api.engines.diagnostic.schemas import (
    ContradictionDeclaree,
    Diagnostic,
    DiagnosticRequest,
    DomaineElement,
    DomaineRisque,
    ElementDiagnostic,
    EtatGlobal,
    EtatGlobalDeclare,
    Probabilite,
    QualificationConclusion,
    RoleDiagnostic,
    TypeDiagnostic,
)
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
from gsie_api.engines.orchestration.schemas import (
    AnalyseComplete,
    AnalyseRequest,
    QualificationParRegle,
)
from gsie_api.engines.orchestration.service import OrchestrationEngine
from gsie_api.engines.reasoning.engine import conclusion_id_pour
from gsie_api.engines.reasoning.schemas import (
    BlocContexte,
    Conclusion,
    EtapeInference,
    InferenceResult,
    MethodeConfiance,
    RegleInference,
    SourceMoteurContexte,
    StationContexte,
)
from gsie_api.engines.recommendation.schemas import (
    JustificationRecommandation,
    ObjectifForestier,
    Recommendation,
    RecommendationSet,
    TypeAction,
)
from gsie_api.engines.simulation.schemas import (
    ConfidenceLevel,
    SimulationResult,
    TimedProjection,
)
from gsie_api.engines.validation.schemas import (
    ControleResultat,
    ResultatControle,
    ValidationResult,
    ValidationStatut,
)
from gsie_api.infrastructure.models.enums import CorrelationMethod

# ---------------------------------------------------------------------------
# Fabriques partagées — objets valides réutilisables.
# ---------------------------------------------------------------------------


def _source(
    *,
    auteur: str = "Rameau et al.",
    reference: str = "doi:10.0000/test",
    type_source: SourceType = SourceType.peer_reviewed,
) -> SourceReference:
    return SourceReference(
        type_source=type_source,
        auteur=auteur,
        reference=reference,
    )


def _etape(*, ordre: int = 1, evidence_level: EvidenceLevel = EvidenceLevel.B) -> EtapeInference:
    return EtapeInference(
        ordre=ordre,
        regle_appliquee="Regle de test",
        source_regle=_source(),
        premisses=["fait observe"],
        conclusion_locale="conclusion locale",
        evidence_level=evidence_level,
    )


def _conclusion(*, conclusion_id: UUID | None = None) -> Conclusion:
    etape = _etape()
    return Conclusion(
        conclusion_id=conclusion_id or uuid4(),
        enonce="Conclusion de test",
        niveau_confiance=0.85,
        methode_confiance=MethodeConfiance.fournie_par_regle,
        evidence_level_plancher=EvidenceLevel.B,
        chaine_inference=[etape],
        sources_utilisees=[etape.source_regle],
    )


def _bloc_contexte() -> BlocContexte:
    return BlocContexte(
        source_moteur=SourceMoteurContexte.pedology,
        source=_source(),
        evidence_level=EvidenceLevel.B,
        valeurs={"pH": 5.2},
    )


def _station_contexte() -> StationContexte:
    return StationContexte(pedologie=_bloc_contexte())


def _etat_global() -> EtatGlobalDeclare:
    return EtatGlobalDeclare(
        etat=EtatGlobal.vigueur_reduite,
        justification="Vigueur reduite constatee",
        source=_source(),
        evidence_level=EvidenceLevel.B,
    )


def _element() -> ElementDiagnostic:
    return ElementDiagnostic(
        description="Sol acide, pH 5.2",
        domaine=DomaineElement.pedologique,
        evidence_level=EvidenceLevel.B,
        source=_source(),
    )


def _diagnostic() -> Diagnostic:
    return Diagnostic(
        diagnostic_id=uuid4(),
        requete_origine=uuid4(),
        station_id=uuid4(),
        type_diagnostic=TypeDiagnostic.stationnel,
        etat_global=EtatGlobal.sain,
        atouts=[_element()],
        confiance=0.75,
        etat_global_evidence_level=EvidenceLevel.B,
        evidence_level_plancher=EvidenceLevel.B,
        conclusions_source=[uuid4()],
        date_diagnostic=datetime(2026, 7, 25, 12, 0, 0, tzinfo=UTC),
    )


def _justification(diagnostic_ref: UUID) -> JustificationRecommandation:
    return JustificationRecommandation(
        diagnostic_ref=diagnostic_ref,
        sources=[_source()],
        facteurs_limitants=["Diagnostic limite aux donnees pedologiques"],
    )


def _recommendation(*, diagnostic_ref: UUID) -> Recommendation:
    return Recommendation(
        recommandation_id=uuid4(),
        type_action=TypeAction.PLANTATION,
        description="Reconstituer le peuplement.",
        justification=_justification(diagnostic_ref),
        niveau_confiance=0.7,
    )


def _recommendation_set(*, diagnostic_ref: UUID) -> RecommendationSet:
    return RecommendationSet(
        ensemble_id=uuid4(),
        requete_origine=uuid4(),
        diagnostic_source=diagnostic_ref,
        recommandations=[_recommendation(diagnostic_ref=diagnostic_ref)],
        date_generation=datetime.now(UTC),
    )


def _validation_result() -> ValidationResult:
    return ValidationResult(
        validation_id=uuid4(),
        requete_origine=uuid4(),
        statut=ValidationStatut.valide,
        controles=[
            ControleResultat(
                nom_controle="presence_sources",
                resultat=ResultatControle.conforme,
                details="Toutes les sorties citent leurs sources.",
            )
        ],
        date_validation=datetime.now(UTC),
    )


def _inference_result(*, conclusions: list[Conclusion] | None = None) -> InferenceResult:
    return InferenceResult(
        resultat_id=uuid4(),
        requete_origine=uuid4(),
        conclusions=conclusions if conclusions is not None else [_conclusion()],
        contradictions=[],
        date_inference=datetime.now(UTC),
    )


# ===========================================================================
# orchestration/service.py — chemin nominal de analyser
# ===========================================================================


async def should_complete_full_chain_when_reasoning_produces_conclusions() -> None:
    """Le chemin nominal enchaîne les quatre moteurs et retourne AnalyseComplete.

    Couvre la qualification, le diagnostic, la recommandation, la
    validation, la construction du résultat et la journalisation.
    """
    from gsie_api.engines.orchestration import service as orch_service

    requete_id = uuid4()
    identifiant_regle = "regle-test"
    conclusion_id = conclusion_id_pour(requete_id, identifiant_regle)

    conclusion = _conclusion(conclusion_id=conclusion_id)
    inference = InferenceResult(
        resultat_id=uuid4(),
        requete_origine=requete_id,
        conclusions=[conclusion],
        contradictions=[],
        date_inference=datetime.now(UTC),
    )

    requete = AnalyseRequest(
        requete_id=requete_id,
        station_id=uuid4(),
        contexte=_station_contexte(),
        regles=[
            RegleInference(
                identifiant=identifiant_regle,
                condition="pedologie_pH < 5.5",
                enonce_conclusion="Le sol est acide.",
                source=_source(),
                evidence_level=EvidenceLevel.B,
                niveau_confiance=0.85,
            ),
        ],
        qualifications=[
            QualificationParRegle(
                identifiant_regle=identifiant_regle,
                role=RoleDiagnostic.contrainte,
                domaine_element=DomaineElement.pedologique,
            ),
        ],
        etat_global=_etat_global(),
        type_diagnostic=TypeDiagnostic.stationnel,
        question="Quelles essences sont adaptees ?",
        objectif_forestier=ObjectifForestier.PRODUCTION,
        alternatives_demandees=True,
    )

    diagnostic_mock = MagicMock()
    diagnostic_mock.diagnostic_id = uuid4()
    recommandations_mock = MagicMock()
    validation_mock = MagicMock()
    resultat_mock = MagicMock()
    resultat_mock.resume = {"n_conclusions": 1}

    engine = OrchestrationEngine(session=MagicMock())

    with (
        patch.object(orch_service, "ReasoningEngine") as mock_reasoning_cls,
        patch.object(orch_service, "DiagnosticEngine") as mock_diagnostic_cls,
        patch.object(orch_service, "RecommendationEngine") as mock_reco_cls,
        patch.object(orch_service, "ValidationEngine") as mock_validation_cls,
        patch.object(orch_service, "ensemble_complet_to_validation_request") as mock_ensemble,
        patch.object(orch_service, "AnalyseComplete", return_value=resultat_mock) as mock_complete,
    ):
        mock_reasoning_cls.return_value.infer = AsyncMock(return_value=inference)
        mock_diagnostic_cls.return_value.diagnostiquer = AsyncMock(return_value=diagnostic_mock)
        mock_reco_cls.return_value.recommend = AsyncMock(return_value=recommandations_mock)
        mock_validation_cls.return_value.validate = AsyncMock(return_value=validation_mock)
        mock_ensemble.return_value = MagicMock()

        result = await engine.analyser(requete, datetime.now(UTC))

    assert result is resultat_mock
    mock_complete.assert_called_once()
    mock_ensemble.assert_called_once()


# ===========================================================================
# orchestration/schemas.py — propriété resume de AnalyseComplete
# ===========================================================================


def should_resume_return_summary_dict_when_analyse_complete_is_valid() -> None:
    """La propriété ``resume`` agrège les comptes et statuts pour la journalisation."""
    diagnostic = _diagnostic()
    reco_set = _recommendation_set(diagnostic_ref=diagnostic.diagnostic_id)
    inference = _inference_result()
    validation = _validation_result()

    analyse = AnalyseComplete(
        requete_origine=uuid4(),
        inference=inference,
        diagnostic=diagnostic,
        recommandations=reco_set,
        validation=validation,
    )

    resume = analyse.resume
    assert resume["n_conclusions"] == len(inference.conclusions)
    assert resume["etat_global"] == diagnostic.etat_global.value
    assert resume["plancher"] == diagnostic.evidence_level_plancher.value
    assert resume["n_recommandations"] == len(reco_set.recommandations)
    assert resume["statut_validation"] == validation.statut.value


# ===========================================================================
# diagnostic/schemas.py — QualificationConclusion._champs_coherents_avec_le_role
# ===========================================================================


def should_reject_risque_with_missing_obligatory_fields() -> None:
    """Un risque sans domaine_risque/probabilite/horizon est incomplet."""
    with pytest.raises(ValidationError, match="risque incomplet"):
        QualificationConclusion(
            conclusion_id=uuid4(),
            role=RoleDiagnostic.risque,
            domaine_element=None,
            domaine_risque=None,
            probabilite=None,
            horizon=None,
        )


def should_reject_risque_with_domaine_element_set() -> None:
    """Un risque ne porte pas de domaine_element."""
    with pytest.raises(ValidationError, match="domaine_element"):
        QualificationConclusion(
            conclusion_id=uuid4(),
            role=RoleDiagnostic.risque,
            domaine_element=DomaineElement.pedologique,
            domaine_risque=DomaineRisque.climatique,
            probabilite=Probabilite.eleve,
            horizon="10 ans",
        )


def should_reject_non_risque_without_domaine_element() -> None:
    """Une contrainte sans domaine_element est invalide."""
    with pytest.raises(ValidationError, match="exige un domaine_element"):
        QualificationConclusion(
            conclusion_id=uuid4(),
            role=RoleDiagnostic.contrainte,
            domaine_element=None,
        )


def should_reject_non_risque_with_risk_fields_set() -> None:
    """Une contrainte portant un champ de risque est invalide."""
    with pytest.raises(ValidationError, match="ne porte ni probabilité"):
        QualificationConclusion(
            conclusion_id=uuid4(),
            role=RoleDiagnostic.contrainte,
            domaine_element=DomaineElement.pedologique,
            probabilite=Probabilite.eleve,
        )


# ===========================================================================
# diagnostic/schemas.py — ContradictionDeclaree._conclusions_distinctes
# ===========================================================================


def should_reject_contradiction_with_same_conclusion_twice() -> None:
    """Une conclusion ne peut pas se contredire elle-même."""
    meme_id = uuid4()
    with pytest.raises(ValidationError, match="se contredire elle-même"):
        ContradictionDeclaree(
            conclusion_a=meme_id,
            conclusion_b=meme_id,
            description="Contradiction circulaire",
        )


# ===========================================================================
# diagnostic/schemas.py — DiagnosticRequest._qualifications_bijectives
# ===========================================================================


def _diagnostic_request(
    *,
    conclusions: list[Conclusion] | None = None,
    qualifications: list[QualificationConclusion] | None = None,
    contradictions: list[ContradictionDeclaree] | None = None,
) -> DiagnosticRequest:
    if conclusions is None:
        conclusions = [_conclusion()]
    if qualifications is None:
        qualifications = [
            QualificationConclusion(
                conclusion_id=c.conclusion_id,
                role=RoleDiagnostic.contrainte,
                domaine_element=DomaineElement.pedologique,
            )
            for c in conclusions
        ]
    return DiagnosticRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        conclusions=conclusions,
        qualifications=qualifications,
        etat_global=_etat_global(),
        contexte=_station_contexte(),
        type_diagnostic=TypeDiagnostic.stationnel,
        contradictions=contradictions or [],
    )


def should_reject_duplicate_qualifications_for_same_conclusion() -> None:
    """Deux qualifications visant la même conclusion sont rejetées."""
    conclusion = _conclusion()
    qualif = QualificationConclusion(
        conclusion_id=conclusion.conclusion_id,
        role=RoleDiagnostic.contrainte,
        domaine_element=DomaineElement.pedologique,
    )
    with pytest.raises(ValidationError, match="deux qualifications visent la même conclusion"):
        _diagnostic_request(
            conclusions=[conclusion],
            qualifications=[qualif, qualif],
        )


def should_reject_conclusion_without_qualification() -> None:
    """Une conclusion sans qualification correspondante est rejetée."""
    c1 = _conclusion()
    c2 = _conclusion()
    qualif1 = QualificationConclusion(
        conclusion_id=c1.conclusion_id,
        role=RoleDiagnostic.contrainte,
        domaine_element=DomaineElement.pedologique,
    )
    with pytest.raises(ValidationError, match="conclusions non qualifiées"):
        _diagnostic_request(
            conclusions=[c1, c2],
            qualifications=[qualif1],
        )


def should_reject_orphan_qualification_without_conclusion() -> None:
    """Une qualification sans conclusion correspondante est rejetée."""
    conclusion = _conclusion()
    orphan_qualif = QualificationConclusion(
        conclusion_id=uuid4(),
        role=RoleDiagnostic.contrainte,
        domaine_element=DomaineElement.pedologique,
    )
    real_qualif = QualificationConclusion(
        conclusion_id=conclusion.conclusion_id,
        role=RoleDiagnostic.contrainte,
        domaine_element=DomaineElement.pedologique,
    )
    with pytest.raises(ValidationError, match="qualifications sans conclusion correspondante"):
        _diagnostic_request(
            conclusions=[conclusion],
            qualifications=[real_qualif, orphan_qualif],
        )


# ===========================================================================
# diagnostic/schemas.py — DiagnosticRequest._contradictions_referencent_des_conclusions
# ===========================================================================


def should_reject_contradiction_referencing_absent_conclusion() -> None:
    """Une contradiction visant des conclusions absentes est rejetée."""
    conclusion = _conclusion()
    contradiction = ContradictionDeclaree(
        conclusion_a=conclusion.conclusion_id,
        conclusion_b=uuid4(),  # absente
        description="Contradiction avec une conclusion inconnue",
    )
    with pytest.raises(ValidationError, match="conclusions absentes"):
        _diagnostic_request(
            conclusions=[conclusion],
            contradictions=[contradiction],
        )


# ===========================================================================
# reasoning/schemas.py — InferenceResult._partiel_coherent
# ===========================================================================


def should_reject_partial_result_without_unapplied_rules() -> None:
    """Un résultat déclaré partiel sans règles non appliquées est rejeté."""
    with pytest.raises(ValidationError, match="sans indiquer les règles non appliquées"):
        InferenceResult(
            resultat_id=uuid4(),
            requete_origine=uuid4(),
            conclusions=[_conclusion()],
            contradictions=[],
            date_inference=datetime.now(UTC),
            resultat_partiel=True,
            regles_non_appliquees=[],
        )


def should_reject_unapplied_rules_when_result_claims_complete() -> None:
    """Des règles non appliquées listées alors que le résultat se dit complet sont rejetées."""
    with pytest.raises(ValidationError, match="résultat se dit complet"):
        InferenceResult(
            resultat_id=uuid4(),
            requete_origine=uuid4(),
            conclusions=[_conclusion()],
            contradictions=[],
            date_inference=datetime.now(UTC),
            resultat_partiel=False,
            regles_non_appliquees=["REGLE-A"],
        )


def should_reject_unsorted_unapplied_rules() -> None:
    """regles_non_appliquees doit être trié pour le déterminisme."""
    with pytest.raises(ValidationError, match="doit être trié"):
        InferenceResult(
            resultat_id=uuid4(),
            requete_origine=uuid4(),
            conclusions=[_conclusion()],
            contradictions=[],
            date_inference=datetime.now(UTC),
            resultat_partiel=True,
            regles_non_appliquees=["REGLE-B", "REGLE-A"],
        )


# ===========================================================================
# simulation/schemas.py — SimulationResult._alternatives_sans_profondeur
# ===========================================================================


def _timed_projection() -> TimedProjection:
    return TimedProjection(
        timestamp=datetime.now(UTC),
        state={"biomasse": 100.0},
        key_indicators={"biodiversite": 0.8},
    )


def _simulation_result(
    *,
    alternatives: list[SimulationResult] | None = None,
) -> SimulationResult:
    return SimulationResult(
        scenario_id=uuid4(),
        projections=[_timed_projection()],
        confidence=ConfidenceLevel.medium,
        sources=[{"modele": "FOREST-DYNAMICS", "version": "1.0"}],
        assumptions=["Hypothese de croissance lineaire"],
        alternatives=alternatives or [],
    )


def should_reject_alternative_with_nested_alternatives() -> None:
    """Une alternative ne peut pas porter ses propres alternatives."""
    nested = _simulation_result(alternatives=[])
    nested_with_child = _simulation_result(alternatives=[nested])
    with pytest.raises(ValidationError, match="ne peut pas porter ses propres alternatives"):
        _simulation_result(alternatives=[nested_with_child])


# ===========================================================================
# correlation/schemas.py — CorrelationComputeRequest._valeurs_appariees
# ===========================================================================


def _correlation_request(
    *,
    valeurs_a: list[float],
    valeurs_b: list[float],
) -> CorrelationComputeRequest:
    return CorrelationComputeRequest(
        requete_id=uuid4(),
        domaine=DomaineCorrelation.stationnel,
        variable_a=ParametreCorrelation(
            source_moteur=SourceMoteur.pedology,
            variable="pH",
            valeurs=valeurs_a,
        ),
        variable_b=ParametreCorrelation(
            source_moteur=SourceMoteur.botanical,
            variable="presence_chene",
            valeurs=valeurs_b,
        ),
        methode=CorrelationMethod.pearson,
        seuil_significativite=0.05,
        source=_source(),
        evidence_level=EvidenceLevel.B,
    )


def should_reject_mismatched_variable_lengths() -> None:
    """variable_a et variable_b doivent avoir le même nombre de valeurs."""
    with pytest.raises(ValidationError, match="appariées"):
        _correlation_request(
            valeurs_a=[1.0, 2.0, 3.0, 4.0],
            valeurs_b=[5.0, 6.0, 7.0],
        )

"""Tests unitaires — Orchestration Engine.

L'orchestration branche les moteurs Reasoning → Diagnostic →
Recommendation → Validation sans ajouter de logique métier. Ces tests
unitaires ciblent la méthode `_qualifier` — le rattachement des
qualifications déclarées aux conclusions produites — sans Docker ni DB,
contrairement aux tests d'intégration qui couvrent la chaîne HTTP
complète.

Conventions (AGENTS.md API) : pytest-asyncio mode `auto`, nommage
`should_[expected]_when_[condition]`, structure Arrange → Act → Assert.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from gsie_api.engines.diagnostic.schemas import (
    DomaineElement,
    DomaineRisque,
    EtatGlobalDeclare,
    Probabilite,
    RoleDiagnostic,
    TypeDiagnostic,
)
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
from gsie_api.engines.orchestration.schemas import (
    AnalyseRequest,
    QualificationParRegle,
)
from gsie_api.engines.orchestration.service import (
    AnalyseImpossibleError,
    OrchestrationEngine,
)
from gsie_api.engines.reasoning.engine import conclusion_id_pour
from gsie_api.engines.reasoning.schemas import (
    Conclusion,
    EtapeInference,
    InferenceResult,
    MethodeConfiance,
    RegleInference,
    StationContexte,
)
from gsie_api.engines.recommendation.schemas import ObjectifForestier


def _source() -> SourceReference:
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="INRAE (2008)",
        reference="Référentiel pédologique français, édition 2008",
    )


def _station_contexte() -> StationContexte:
    return StationContexte(
        pedologie={
            "source_moteur": "PEDOLOGY",
            "source": _source(),
            "evidence_level": EvidenceLevel.B,
            "valeurs": {"pH": 5.2, "profondeur_cm": 80},
        }
    )


def _regle(identifiant: str, condition: str, enonce: str) -> RegleInference:
    return RegleInference(
        identifiant=identifiant,
        condition=condition,
        enonce_conclusion=enonce,
        source=_source(),
        evidence_level=EvidenceLevel.B,
        niveau_confiance=0.85,
    )


def _requete(
    *,
    regles: list[RegleInference] | None = None,
    qualifications: list[QualificationParRegle] | None = None,
) -> AnalyseRequest:
    if regles is None:
        regles = [
            _regle("regle-acidite-01", "pedologie_pH < 5.5", "Le sol est acide."),
            _regle("regle-profondeur-01", "pedologie_profondeur_cm > 50", "Le sol est profond."),
        ]
    if qualifications is None:
        qualifications = [
            QualificationParRegle(
                identifiant_regle="regle-acidite-01",
                role=RoleDiagnostic.contrainte,
                domaine_element=DomaineElement.pedologique,
            ),
            QualificationParRegle(
                identifiant_regle="regle-profondeur-01",
                role=RoleDiagnostic.atout,
                domaine_element=DomaineElement.pedologique,
            ),
        ]
    return AnalyseRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        contexte=_station_contexte(),
        regles=regles,
        qualifications=qualifications,
        etat_global=EtatGlobalDeclare(
            etat="vigueur_reduite",
            justification="Acidité marquée constatée sur la station",
            source=_source(),
            evidence_level=EvidenceLevel.B,
        ),
        type_diagnostic=TypeDiagnostic.stationnel,
        question="Quelles essences sont adaptées à cette station ?",
        objectif_forestier=ObjectifForestier.PRODUCTION,
        alternatives_demandees=True,
    )


def _conclusion(requete_id, identifiant_regle: str, enonce: str) -> Conclusion:
    source = _source()
    return Conclusion(
        conclusion_id=conclusion_id_pour(requete_id, identifiant_regle),
        enonce=enonce,
        niveau_confiance=0.85,
        methode_confiance=MethodeConfiance.fournie_par_regle,
        evidence_level_plancher=EvidenceLevel.B,
        chaine_inference=[
            EtapeInference(
                ordre=1,
                regle_appliquee=identifiant_regle,
                source_regle=source,
                premisses=["pH = 5.2"],
                conclusion_locale=enonce,
                evidence_level=EvidenceLevel.B,
            )
        ],
        sources_utilisees=[source],
    )


# ─────────────────────────────────────────────────────────────────────────
# Tests _qualifier — rattachement qualifications ↔ conclusions
# ─────────────────────────────────────────────────────────────────────────


def should_rattachement_qualified_conclusions_in_order() -> None:
    """_qualifier retourne les qualifications dans l'ordre des conclusions produites."""
    requete = _requete()
    engine = OrchestrationEngine(session=MagicMock())

    conclusions = [
        _conclusion(requete.requete_id, "regle-acidite-01", "Le sol est acide."),
        _conclusion(requete.requete_id, "regle-profondeur-01", "Le sol est profond."),
    ]
    qualifications = engine._qualifier(requete, conclusions)

    assert len(qualifications) == 2
    assert qualifications[0].conclusion_id == conclusions[0].conclusion_id
    assert qualifications[0].role == RoleDiagnostic.contrainte
    assert qualifications[1].conclusion_id == conclusions[1].conclusion_id
    assert qualifications[1].role == RoleDiagnostic.atout


def should_raise_when_conclusion_has_no_qualification_declared() -> None:
    """Une conclusion sans qualification déclarée fait refuser — l'orchestration ne classe pas."""
    requete = _requete(
        qualifications=[
            QualificationParRegle(
                identifiant_regle="regle-acidite-01",
                role=RoleDiagnostic.contrainte,
                domaine_element=DomaineElement.pedologique,
            ),
            # regle-profondeur-01 n'est pas qualifiée
        ]
    )
    engine = OrchestrationEngine(session=MagicMock())

    conclusions = [
        _conclusion(requete.requete_id, "regle-acidite-01", "Le sol est acide."),
        _conclusion(requete.requete_id, "regle-profondeur-01", "Le sol est profond."),
    ]
    with pytest.raises(AnalyseImpossibleError, match="regle-profondeur-01"):
        engine._qualifier(requete, conclusions)


def should_name_missing_rule_by_its_identifier() -> None:
    """Le refus nomme la règle fautive — pas l'ID de conclusion qu'il n'a jamais vu."""
    requete = _requete(
        qualifications=[
            QualificationParRegle(
                identifiant_regle="regle-acidite-01",
                role=RoleDiagnostic.contrainte,
                domaine_element=DomaineElement.pedologique,
            ),
        ]
    )
    engine = OrchestrationEngine(session=MagicMock())

    conclusions = [
        _conclusion(requete.requete_id, "regle-acidite-01", "Le sol est acide."),
        _conclusion(requete.requete_id, "regle-profondeur-01", "Le sol est profond."),
    ]
    with pytest.raises(AnalyseImpossibleError) as exc_info:
        engine._qualifier(requete, conclusions)

    # Le message doit contenir l'identifiant de la règle, pas l'UUID de conclusion
    assert "regle-profondeur-01" in str(exc_info.value)
    assert str(conclusions[1].conclusion_id) not in str(exc_info.value)


def should_qualifier_preserve_risk_fields() -> None:
    """Un risque déclaré avec probabilité et horizon voit ces champs préservés."""
    requete = _requete(
        qualifications=[
            QualificationParRegle(
                identifiant_regle="regle-acidite-01",
                role=RoleDiagnostic.contrainte,
                domaine_element=DomaineElement.pedologique,
            ),
            QualificationParRegle(
                identifiant_regle="regle-profondeur-01",
                role=RoleDiagnostic.risque,
                domaine_risque=DomaineRisque.climatique,
                probabilite=Probabilite.modere,
                horizon="court_terme",
            ),
        ]
    )
    engine = OrchestrationEngine(session=MagicMock())

    conclusions = [
        _conclusion(requete.requete_id, "regle-acidite-01", "Le sol est acide."),
        _conclusion(requete.requete_id, "regle-profondeur-01", "Le sol est profond."),
    ]
    qualifications = engine._qualifier(requete, conclusions)

    risque = qualifications[1]
    assert risque.role == RoleDiagnostic.risque
    assert risque.domaine_risque == DomaineRisque.climatique
    assert risque.probabilite == Probabilite.modere
    assert risque.horizon == "court_terme"


# ─────────────────────────────────────────────────────────────────────────
# Tests structurels
# ─────────────────────────────────────────────────────────────────────────


def should_return_version_0_1_0() -> None:
    """version() retourne la version courante de l'orchestration."""
    assert OrchestrationEngine.version() == "0.1.0"


async def should_raise_when_reasoning_produces_no_conclusion() -> None:
    """Un raisonnement sans conclusion fait refuser — un diagnostic vide n'est pas honnête."""
    requete = _requete()
    session = MagicMock()
    engine = OrchestrationEngine(session=session)

    # Mock ReasoningEngine.infer pour retourner un résultat sans conclusion
    inference_vide = InferenceResult(
        resultat_id=uuid4(),
        requete_origine=requete.requete_id,
        conclusions=[],
        contradictions=[],
        date_inference=datetime.now(UTC),
    )

    from gsie_api.engines.orchestration import service as orch_service

    original_infer = orch_service.ReasoningEngine.infer
    orch_service.ReasoningEngine.infer = AsyncMock(return_value=inference_vide)
    try:
        with pytest.raises(AnalyseImpossibleError, match="aucune conclusion"):
            await engine.analyser(requete, datetime.now(UTC))
    finally:
        orch_service.ReasoningEngine.infer = original_infer

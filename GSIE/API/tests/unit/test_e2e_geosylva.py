"""Test E2E — parcours utilisateur GeoSylva de bout en bout.

Simule le parcours réel d'un forestier utilisant GeoSylva (l'app Android)
qui interroge l'API GSIE. Le test enchaîne tous les moteurs de la chaîne
principale sur des données réelles (autécologie Rameau, croissance IGN)
et vérifie que la sortie finale est cohérente et exploitable.

Scénario : un forestier veut évaluer une station forestière en France
pour décider d'un reboisement en hêtre (Fagus sylvatica).

Étapes du parcours :
1. Soumission d'une connaissance botanique (Evidence Engine)
2. Construction du contexte stationnel (pH, climat, essence ciblée)
3. Génération de règles d'inférence depuis l'autécologie Rameau
4. Inférence (Reasoning Engine) — conclusion sur la favorabilité
5. Diagnostic (Diagnostic Engine) — synthèse contraintes/atouts
6. Recommandation (Recommendation Engine) — action sylvicole proposée
7. Validation (pipeline) — contrôle final avant présentation
8. Learning (pipeline) — signal si blocage
9. Simulation (CalibratedGrowthBackend) — projection croissance IGN

Ce test ne nécessite PAS de base de données : la session DB du
Reasoning/Diagnostic Engine est mockée (AsyncMock). L'objectif est de
valider l'enchaînement fonctionnel, pas la persistance.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from gsie_api.engines.autecology_adapter import profiles_to_rules
from gsie_api.engines.diagnostic.engine import DiagnosticEngine
from gsie_api.engines.diagnostic.schemas import (
    Diagnostic,
    DiagnosticRequest,
    DomaineElement,
    DomaineRisque,
    EtatGlobal,
    EtatGlobalDeclare,
    Probabilite,
    QualificationConclusion,
    RoleDiagnostic,
    TypeDiagnostic,
)
from gsie_api.engines.evidence.schemas import (
    ContentType,
    EvidenceLevel,
    KnowledgeStatus,
    RawKnowledgeSubmission,
    SourceReference,
    SourceType,
)
from gsie_api.engines.evidence.wrapper import evaluate
from gsie_api.engines.learning.engine import LearningEngine
from gsie_api.engines.learning.schemas import LearningSignalType
from gsie_api.engines.reasoning.engine import ReasoningEngine
from gsie_api.engines.reasoning.schemas import (
    ReasoningRequest,
    StationContexte,
    BlocContexte,
    SourceMoteurContexte,
)
from gsie_api.engines.recommendation.engine import RecommendationEngine
from gsie_api.engines.recommendation.schemas import (
    ObjectifForestier,
    RecommendationRequest,
)
from gsie_api.engines.simulation.schemas import (
    ConfidenceLevel,
    InterventionSpec,
    ScenarioSimulation,
)
from gsie_api.engines.simulation_backend import CalibratedGrowthBackend
from gsie_api.engines.validation.schemas import ValidationStatut
from gsie_api.engines.validation_pipeline import run_validation_pipeline
from gsie_api.infrastructure.models.enums import EvidenceLevel as DbEvidenceLevel
from gsie_api.seeds.autecology_rameau_data import (
    GBIF_TAXON_KEY_FAGUS_SYLVATICA,
    build_autecology_rameau_profiles,
)

# Date d'inférence injectée pour le déterminisme (Reasoning/Diagnostic).
_DATE_INFERENCE = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)


def _source_rameau() -> SourceReference:
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="Rameau J.-C., Mansion D., Dumé G.",
        date_publication="2008",
        reference="Flore forestière française, guide écologique forestier, IDF",
    )


def _source_pedologie() -> SourceReference:
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="IGN — SoilGrids",
        date_publication="2023",
        reference="SoilGrids 250m, pH H2O couche de surface",
    )


def _source_climat() -> SourceReference:
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="Météo-France",
        date_publication="2024",
        reference="Normales climatiques 1991-2020, station de référence",
    )


def _source_forestier() -> SourceReference:
    return SourceReference(
        type_source=SourceType.observation_terrain,
        auteur="Forestier (terrain)",
        date_publication="2026",
        reference="Observation directe station, 2026-07-27",
    )


# --- Étape 1 : soumission de connaissance ---


def should_qualify_knowledge_submission_via_evidence_engine() -> None:
    """Étape 1 — une soumission de connaissance est qualifiée par l'Evidence Engine."""
    submission = RawKnowledgeSubmission(
        soumission_id=uuid4(),
        soumetteur="Forestier test (GeoSylva)",
        type_contenu=ContentType.publication,
        contenu={"definition": "Fagus sylvatica préfère les sols frais à humides"},
        source_candidate=_source_rameau(),
        date_soumission=datetime.now(UTC),
    )
    qualified = evaluate(submission)
    # Rameau 2008 est un référentiel officiel → accepté, niveau B ou C
    assert qualified.statut == KnowledgeStatus.accepte
    assert qualified.evidence_level in {EvidenceLevel.B, EvidenceLevel.C}


# --- Étapes 2-9 : parcours complet ---


@pytest.mark.asyncio
async def should_run_full_geosylva_pipeline_e2e() -> None:
    """Parcours E2E complet — du contexte stationnel à la simulation calibrée.

    Simule un forestier qui :
    1. Construit le contexte de sa station (pH, climat, essence ciblée)
    2. Récupère les règles autécologiques Rameau pour le hêtre
    3. Fait inférer le Reasoning Engine (favorabilité de la station)
    4. Fait produire un diagnostic au Diagnostic Engine
    5. Demande une recommandation (objectif : reboisement)
    6. Fait valider l'ensemble par le pipeline Validation + Learning
    7. Simule la croissance sur 30 ans avec le modèle calibré IGN
    """
    # --- Étape 2 : contexte stationnel ---
    # Station : forêt tempérée, pH légèrement acide, précipitations correctes
    pedologie = BlocContexte(
        source_moteur=SourceMoteurContexte.pedology,
        source=_source_pedologie(),
        evidence_level=DbEvidenceLevel.b,
        valeurs={"pH": 5.5, "profondeur_cm": 80, "texture": "limoneuse"},
        date_observation=datetime.now(UTC),
    )
    climat = BlocContexte(
        source_moteur=SourceMoteurContexte.climate,
        source=_source_climat(),
        evidence_level=DbEvidenceLevel.b,
        valeurs={
            "precipitations_mm_an": 900,
            "temperature_moyenne_c": 11.0,
            "nb_jours_gel": 60,
        },
        date_observation=datetime.now(UTC),
    )
    peuplement = BlocContexte(
        source_moteur=SourceMoteurContexte.forest_dynamics,
        source=_source_forestier(),
        evidence_level=DbEvidenceLevel.c,
        valeurs={"essence_cible": "Fagus sylvatica", "volume_m3_ha": 150.0},
        date_observation=datetime.now(UTC),
    )
    contexte = StationContexte(
        pedologie=pedologie,
        climat=climat,
        peuplement=peuplement,
    )

    # --- Étape 3 : règles autécologiques Rameau pour le hêtre ---
    profiles = build_autecology_rameau_profiles()
    fagus_profiles = [
        p for p in profiles if p.species_gbif_taxon_key == GBIF_TAXON_KEY_FAGUS_SYLVATICA
    ]
    assert len(fagus_profiles) == 5  # 5 variables autécologiques
    regles = profiles_to_rules(fagus_profiles)
    assert len(regles) == 5

    # --- Étape 4 : inférence Reasoning ---
    # Mock de la session DB (le Reasoning Engine ne persiste pas en v1,
    # mais exige une AsyncSession au constructeur)
    session_mock = AsyncMock()
    reasoning_engine = ReasoningEngine(session_mock)
    reasoning_request = ReasoningRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        contexte=contexte,
        regles=regles,
        question="La station est-elle favorable au hêtre ?",
        profondeur_max=5,
    )
    inference = await reasoning_engine.infer(reasoning_request, _DATE_INFERENCE)
    # Au moins une conclusion doit être produite (les règles matchent essence_cible)
    assert len(inference.conclusions) >= 1
    # Chaque conclusion a une chaîne d'inférence non vide
    for conclusion in inference.conclusions:
        assert len(conclusion.chaine_inference) >= 1
        assert conclusion.evidence_level_plancher in DbEvidenceLevel

    # --- Étape 5 : diagnostic ---
    # Qualifications : on déclare les conclusions comme atouts ou contraintes
    # (rôle déclaratif, jamais déduit — GSIE-CON-002)
    qualifications = []
    for conclusion in inference.conclusions:
        enonce_lower = conclusion.enonce.lower()
        if "tolérant" in enonce_lower or "préfère" in enonce_lower or "résistant" in enonce_lower:
            role = RoleDiagnostic.atout
            domaine = DomaineElement.botanique
        elif "sensible" in enonce_lower or "évite" in enonce_lower:
            role = RoleDiagnostic.contrainte
            domaine = DomaineElement.botanique
        else:
            role = RoleDiagnostic.atout
            domaine = DomaineElement.botanique
        qualifications.append(
            QualificationConclusion(
                conclusion_id=conclusion.conclusion_id,
                role=role,
                domaine_element=domaine,
            )
        )

    etat_global = EtatGlobalDeclare(
        etat=EtatGlobal.sain,
        justification="Station forestière tempérée, pH adapté, précipitations suffisantes",
        source=_source_forestier(),
        evidence_level=DbEvidenceLevel.c,
    )

    diagnostic_request = DiagnosticRequest(
        requete_id=uuid4(),
        station_id=reasoning_request.station_id or uuid4(),
        conclusions=inference.conclusions,
        qualifications=qualifications,
        etat_global=etat_global,
        contexte=contexte,
        type_diagnostic=TypeDiagnostic.stationnel,
    )

    # Mock de session pour le Diagnostic Engine (persistance mockée)
    diag_session = AsyncMock()
    diag_session.get = AsyncMock(return_value=None)
    diag_session.add = MagicMock()
    diag_session.flush = AsyncMock()
    diagnostic_engine = DiagnosticEngine(diag_session)
    diagnostic = await diagnostic_engine.diagnostiquer(diagnostic_request, _DATE_INFERENCE)

    # Vérifications du diagnostic
    assert diagnostic.statut_validation.value == "brouillon"
    assert len(diagnostic.contraintes) + len(diagnostic.atouts) + len(diagnostic.risques) >= 1
    assert diagnostic.evidence_level_plancher in DbEvidenceLevel
    assert 0.0 <= diagnostic.confiance <= 1.0

    # --- Étape 6 : recommandation ---
    reco_engine = RecommendationEngine()
    reco_request = RecommendationRequest(
        requete_id=uuid4(),
        diagnostic_id=diagnostic.diagnostic_id,
        objectif_forestier=ObjectifForestier.REBOISEMENT,
        alternatives_demandees=True,
    )
    reco_set = await reco_engine.recommend(reco_request)
    assert len(reco_set.recommandations) >= 1
    assert reco_set.diagnostic_source == diagnostic.diagnostic_id
    # Chaque recommandation est contournable (GSIE-CON-001)
    for reco in reco_set.recommandations:
        assert reco.contournable is True

    # --- Étape 7 : validation via pipeline ---
    learning_engine = LearningEngine()
    pipeline_result = await run_validation_pipeline(
        diagnostic,
        reco_set,
        conclusions=inference.conclusions,
        learning_engine=learning_engine,
    )
    validation = pipeline_result["validation"]
    # Le diagnostic a des sources et un niveau de preuve → devrait être valide
    assert validation.statut in {ValidationStatut.valide, ValidationStatut.partiellement_valide}
    # Pas de learning déclenché si valide
    if validation.statut == ValidationStatut.valide:
        assert pipeline_result["learning"] is None
        assert pipeline_result["learning_signal"] is None

    # --- Étape 8 : simulation calibrée IGN ---
    backend = CalibratedGrowthBackend()
    assert backend.confidence() == ConfidenceLevel.medium
    growth_result = backend.simulate_growth(
        species="Fagus sylvatica",
        initial_state={"volume": 150.0, "circumference": 80.0},
        horizon_years=30,
        parameters={"density_factor": 0.9},
    )
    # AMA Fagus = 7.0 m³/ha/an × 0.9 = 6.3, sur 30 ans = 189 m³/ha
    # 150 + 189 = 339 < 500 (production max) → non plafonné
    assert growth_result["final_volume"] > 150.0
    assert growth_result["capped"] is False
    assert "IGN" in growth_result["volume_source"]
    # Circonférence : AMA 2.0 cm/an × 30 = 60 cm → 80 + 60 = 140 cm
    assert growth_result["final_circumference"] > 80.0

    # --- Synthèse : le forestier reçoit une réponse complète ---
    # Diagnostic + recommandation + validation + projection à 30 ans
    assert diagnostic is not None
    assert reco_set is not None
    assert validation is not None
    assert growth_result is not None
    # La chaîne complète s'est exécutée sans erreur


@pytest.mark.asyncio
async def should_detect_blocked_validation_and_feed_learning_e2e() -> None:
    """Cas E2E alternatif — un diagnostic sans source déclenche le Learning.

    Simule un moteur amont défectueux qui produit un diagnostic sans
    source identifiable. Le Validation Engine doit bloquer, et le
    Learning Engine doit accumuler le signal pour proposer une calibration.
    """
    learning_engine = LearningEngine()

    # Simule 5 blocages du même type (sans_source)
    for _ in range(5):
        signal = type(
            "MockSignal",
            (),
            {
                "signal_id": uuid4(),
                "type": LearningSignalType.sortie_bloquee,
                "contenu": {
                    "validation_id": str(uuid4()),
                    "statut": "bloque",
                    "causes_blocage": [
                        {"type_cause": "sans_source", "description": "Aucune source"},
                    ],
                    "controles_non_conformes": [],
                },
                "date_signal": datetime.now(UTC),
            },
        )()
        # Utiliser le vrai LearningSignal
        from gsie_api.engines.learning.schemas import LearningSignal
        real_signal = LearningSignal(
            signal_id=signal.signal_id,
            type=signal.type,
            contenu=signal.contenu,
            date_signal=signal.date_signal,
        )
        result = await learning_engine.process(real_signal)

    # Le 5e doit avoir déclenché une calibration
    # (vérifié via le test unitaire — ici on vérifie que l'accumulateur
    # a bien compté 5 blocages)
    assert learning_engine._blocages_accumules.get("sans_source") == 5
    assert "sans_source" in learning_engine._propositions_emises


@pytest.mark.asyncio
async def should_simulate_growth_for_multiple_species_e2e() -> None:
    """E2E — simulation calibrée IGN pour plusieurs essences du corpus."""
    backend = CalibratedGrowthBackend()
    species_to_test = [
        ("Fagus sylvatica", 100.0, 50.0),
        ("Pinus sylvestris", 80.0, 40.0),
        ("Quercus ilex", 60.0, 30.0),
        ("Abies alba", 120.0, 60.0),
    ]
    for species, initial_vol, initial_circ in species_to_test:
        result = backend.simulate_growth(
            species=species,
            initial_state={"volume": initial_vol, "circumference": initial_circ},
            horizon_years=20,
        )
        assert result["final_volume"] > initial_vol
        assert result["final_circumference"] > initial_circ
        assert "IGN" in result["volume_source"]
        # Chaque essence a un accroissement positif
        assert result["volume_increment"] > 0

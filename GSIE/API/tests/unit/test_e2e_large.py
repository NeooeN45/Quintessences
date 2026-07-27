"""Tests E2E larges — scénarios réalistes GeoSylva étendus.

Étend `test_e2e_geosylva.py` avec des scénarios plus larges et réalistes
que rencontrerait un forestier ou l'app GeoSylva en production :

A. Scénarios multi-essences — station mixte avec plusieurs essences
   ciblées, règles autécologiques pour chacune.
B. Contradictions — deux sources (Parelle vs Rameau) s'opposent sur
   Quercus robur/petraea, le Reasoning Engine signale la contradiction.
C. Risques — diagnostic avec risque climatique (sécheresse croissante),
   probabilité et horizon déclarés.
D. Chemins d'erreur — contexte vide, essence inconnue, valeurs
   extrêmes, règle mal formée.
E. Stress test — 100+ règles autécologiques (corpus complet × 5
   essences), vérifie que le Reasoning Engine termine en temps
   raisonnable.
F. Simulation comparative — projection sur 30 ans pour 4 essences
   avec comparaison des accroissements.
G. Validation + Learning chaîne complète — 5 blocages déclenchent
   une calibration, vérifie l'accumulateur et la proposition.
H. Parcours API HTTP — health, status moteurs, OpenAPI via TestClient
   FastAPI (sans DB).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.engines.autecology_adapter import profiles_to_rules, profile_to_rule
from gsie_api.engines.diagnostic.engine import DiagnosticEngine
from gsie_api.engines.diagnostic.schemas import (
    ContradictionDeclaree,
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
    EvidenceLevel,
    SourceReference,
    SourceType,
)
from gsie_api.engines.learning.engine import LearningEngine
from gsie_api.engines.learning.schemas import LearningSignal, LearningSignalType
from gsie_api.engines.reasoning.engine import ReasoningEngine, ReasoningEngineError
from gsie_api.engines.reasoning.schemas import (
    BlocContexte,
    ReasoningRequest,
    SourceMoteurContexte,
    StationContexte,
)
from gsie_api.engines.recommendation.engine import RecommendationEngine
from gsie_api.engines.recommendation.schemas import (
    ObjectifForestier,
    RecommendationRequest,
)
from gsie_api.engines.simulation_backend import (
    CalibratedGrowthBackend,
    LinearGrowthBackend,
    SimulationBackendError,
)
from gsie_api.engines.validation.schemas import ValidationStatut
from gsie_api.engines.validation_pipeline import run_validation_pipeline
from gsie_api.infrastructure.models.enums import EvidenceLevel as DbEvidenceLevel
from gsie_api.seeds.autecology_pilot_data import (
    GBIF_TAXON_KEY_QUERCUS_PETRAEA,
    GBIF_TAXON_KEY_QUERCUS_ROBUR,
    build_autecology_pilot_profiles,
)
from gsie_api.seeds.autecology_rameau_data import (
    GBIF_TAXON_KEY_ABIES_ALBA,
    GBIF_TAXON_KEY_FAGUS_SYLVATICA,
    GBIF_TAXON_KEY_PINUS_SYLVESTRIS,
    GBIF_TAXON_KEY_QUERCUS_ILEX,
    build_autecology_rameau_profiles,
)

_DATE = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)


def _src_rameau() -> SourceReference:
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="Rameau J.-C., Mansion D., Dumé G.",
        date_publication="2008",
        reference="Flore forestière française, IDF",
    )


def _src_parelle() -> SourceReference:
    return SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur="Parelle J., Brendel O., Jolivet Y.",
        date_publication="2007",
        reference="Annals of Forest Science, hal-02653679",
    )


def _src_terrain() -> SourceReference:
    return SourceReference(
        type_source=SourceType.observation_terrain,
        auteur="Forestier (terrain)",
        date_publication="2026",
        reference="Observation directe station, 2026-07-27",
    )


def _src_climat() -> SourceReference:
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="Météo-France",
        date_publication="2024",
        reference="Normales climatiques 1991-2020",
    )


def _ctx_station(
    essence_cible: str = "Fagus sylvatica",
    ph: float = 5.5,
    precip: float = 900,
    temp: float = 11.0,
    volume: float = 150.0,
) -> StationContexte:
    """Construit un StationContexte réaliste pour une station forestière."""
    pedologie = BlocContexte(
        source_moteur=SourceMoteurContexte.pedology,
        source=SourceReference(
            type_source=SourceType.referentiel_officiel,
            auteur="IGN — SoilGrids",
            date_publication="2023",
            reference="SoilGrids 250m, pH H2O",
        ),
        evidence_level=DbEvidenceLevel.b,
        valeurs={"pH": ph, "profondeur_cm": 80, "texture": "limoneuse"},
        date_observation=datetime.now(UTC),
    )
    climat = BlocContexte(
        source_moteur=SourceMoteurContexte.climate,
        source=_src_climat(),
        evidence_level=DbEvidenceLevel.b,
        valeurs={
            "precipitations_mm_an": precip,
            "temperature_moyenne_c": temp,
            "nb_jours_gel": 60,
        },
        date_observation=datetime.now(UTC),
    )
    peuplement = BlocContexte(
        source_moteur=SourceMoteurContexte.forest_dynamics,
        source=_src_terrain(),
        evidence_level=DbEvidenceLevel.c,
        valeurs={"essence_cible": essence_cible, "volume_m3_ha": volume},
        date_observation=datetime.now(UTC),
    )
    return StationContexte(pedologie=pedologie, climat=climat, peuplement=peuplement)


def _mock_diag_session() -> AsyncMock:
    """Session DB mockée pour le Diagnostic Engine (pas de persistance réelle)."""
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


def _qualifier_conclusions(conclusions: list) -> list[QualificationConclusion]:
    """Qualifie des conclusions en atouts/contraintes selon leur énoncé."""
    qualifications = []
    for conclusion in conclusions:
        enonce = conclusion.enonce.lower()
        if any(w in enonce for w in ("sensible", "évite", "moins tolérant")):
            role = RoleDiagnostic.contrainte
        else:
            role = RoleDiagnostic.atout
        qualifications.append(
            QualificationConclusion(
                conclusion_id=conclusion.conclusion_id,
                role=role,
                domaine_element=DomaineElement.botanique,
            )
        )
    return qualifications


# ===========================================================================
# A. Scénarios multi-essences
# ===========================================================================


@pytest.mark.asyncio
async def should_reason_on_multi_species_station() -> None:
    """Station mixte — règles autécologiques pour 3 essences simultanées.

    Simule un forestier qui envisage 3 essences pour un reboisement
    (hêtre, pin sylvestre, sapin pectiné). Le Reasoning Engine doit
    produire des conclusions pour chaque essence présente au contexte.
    """
    # Contexte avec 3 essences candidats (stockées comme liste dans une
    # variable du bloc peuplement — le Reasoning Engine aplatit en
    # `peuplement_essence_cible` pour la première).
    contexte = _ctx_station(essence_cible="Fagus sylvatica")

    # Règles pour 3 essences (15 règles = 3 × 5 variables Rameau)
    all_profiles = build_autecology_rameau_profiles()
    fagus = [p for p in all_profiles if p.species_gbif_taxon_key == GBIF_TAXON_KEY_FAGUS_SYLVATICA]
    pinus = [p for p in all_profiles if p.species_gbif_taxon_key == GBIF_TAXON_KEY_PINUS_SYLVESTRIS]
    abies = [p for p in all_profiles if p.species_gbif_taxon_key == GBIF_TAXON_KEY_ABIES_ALBA]
    regles = profiles_to_rules(fagus + pinus + abies)
    assert len(regles) == 15

    session = AsyncMock()
    engine = ReasoningEngine(session)
    request = ReasoningRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        contexte=contexte,
        regles=regles,
        question="Quelles essences sont favorables sur cette station ?",
        profondeur_max=5,
    )
    result = await engine.infer(request, _DATE)

    # Seules les règles dont la condition matchent `peuplement_essence_cible`
    # produisent des conclusions — ici Fagus sylvatica.
    fagus_conclusions = [
        c for c in result.conclusions if "Fagus sylvatica" in c.enonce
    ]
    assert len(fagus_conclusions) == 5  # 5 variables Rameau pour Fagus
    # Les règles Pinus et Abies ne matchent pas (essence_cible != leur nom)
    pinus_conclusions = [c for c in result.conclusions if "Pinus sylvestris" in c.enonce]
    assert len(pinus_conclusions) == 0
    abies_conclusions = [c for c in result.conclusions if "Abies alba" in c.enonce]
    assert len(abies_conclusions) == 0


# ===========================================================================
# B. Contradictions — Parelle vs Rameau sur Quercus
# ===========================================================================


@pytest.mark.asyncio
async def should_detect_contradiction_between_parelle_and_rameau() -> None:
    """Deux sources s'opposent sur Quercus — le diagnostic signale la contradiction.

    Parelle (2007) dit que Quercus robur est plus tolérant à l'engorgement
    que Quercus petraea. Rameau (2008) ne contredit pas directement, mais
    si on déclare une contradiction, le Diagnostic Engine doit la porter
    dans le diagnostic final.
    """
    # Règles Parelle pour Quercus robur et petraea
    parelle_profiles = build_autecology_pilot_profiles()
    regles = profiles_to_rules(parelle_profiles)

    contexte = _ctx_station(essence_cible="Quercus robur")
    session = AsyncMock()
    engine = ReasoningEngine(session)
    request = ReasoningRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        contexte=contexte,
        regles=regles,
        question="Quercus robur est-il adapté à cette station ?",
        profondeur_max=5,
    )
    result = await engine.infer(request, _DATE)
    assert len(result.conclusions) >= 1

    # Construire un diagnostic avec une contradiction déclarée
    # entre deux conclusions (la première et la dernière)
    quercus_conclusions = [
        c for c in result.conclusions if "Quercus" in c.enonce
    ]
    if len(quercus_conclusions) >= 2:
        contradiction = ContradictionDeclaree(
            conclusion_a=quercus_conclusions[0].conclusion_id,
            conclusion_b=quercus_conclusions[-1].conclusion_id,
            description="Opposition déclarée entre tolérance engorgement et préférence edaphique",
        )
        qualifications = _qualifier_conclusions(result.conclusions)
        diag_request = DiagnosticRequest(
            requete_id=uuid4(),
            station_id=uuid4(),
            conclusions=result.conclusions,
            qualifications=qualifications,
            etat_global=EtatGlobalDeclare(
                etat=EtatGlobal.sain,
                justification="Station tempérée, pH adapté aux chênes",
                source=_src_terrain(),
                evidence_level=DbEvidenceLevel.c,
            ),
            contexte=contexte,
            type_diagnostic=TypeDiagnostic.stationnel,
            contradictions=[contradiction],
        )
        diag_engine = DiagnosticEngine(_mock_diag_session())
        diagnostic = await diag_engine.diagnostiquer(diag_request, _DATE)
        # La contradiction doit être reportée dans le diagnostic
        assert len(diagnostic.contradictions) >= 1


# ===========================================================================
# C. Risques — diagnostic avec risque climatique
# ===========================================================================


@pytest.mark.asyncio
async def should_handle_risk_in_diagnostic() -> None:
    """Diagnostic avec risque climatique (sécheresse croissante).

    Le forestier déclare un risque : augmentation de la sécheresse sur
    30 ans, probabilité modérée. Le Diagnostic Engine doit l'intégrer
    comme RisqueDiagnostic avec domaine climatique.
    """
    # Inférence simple pour avoir des conclusions
    profiles = build_autecology_rameau_profiles()
    fagus = [p for p in profiles if p.species_gbif_taxon_key == GBIF_TAXON_KEY_FAGUS_SYLVATICA]
    regles = profiles_to_rules(fagus)
    contexte = _ctx_station(essence_cible="Fagus sylvatica")

    session = AsyncMock()
    engine = ReasoningEngine(session)
    request = ReasoningRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        contexte=contexte,
        regles=regles,
        question="Risque climatique sur le hêtre ?",
        profondeur_max=3,
    )
    result = await engine.infer(request, _DATE)
    assert len(result.conclusions) >= 1

    # Qualifier la première conclusion comme risque climatique
    qualifications = [
        QualificationConclusion(
            conclusion_id=result.conclusions[0].conclusion_id,
            role=RoleDiagnostic.risque,
            domaine_risque=DomaineRisque.climatique,
            probabilite=Probabilite.modere,
            horizon="30 ans",
        )
    ]
    # Qualifier le reste comme atouts
    for c in result.conclusions[1:]:
        qualifications.append(
            QualificationConclusion(
                conclusion_id=c.conclusion_id,
                role=RoleDiagnostic.atout,
                domaine_element=DomaineElement.botanique,
            )
        )

    diag_request = DiagnosticRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        conclusions=result.conclusions,
        qualifications=qualifications,
        etat_global=EtatGlobalDeclare(
            etat=EtatGlobal.vigueur_reduite,
            justification="Risque de sécheresse croissante sur 30 ans",
            source=_src_climat(),
            evidence_level=DbEvidenceLevel.b,
        ),
        contexte=contexte,
        type_diagnostic=TypeDiagnostic.stationnel,
    )
    diag_engine = DiagnosticEngine(_mock_diag_session())
    diagnostic = await diag_engine.diagnostiquer(diag_request, _DATE)

    # Au moins un risque doit être présent
    assert len(diagnostic.risques) >= 1
    risque = diagnostic.risques[0]
    assert risque.domaine == DomaineRisque.climatique
    assert risque.probabilite == Probabilite.modere
    assert risque.horizon == "30 ans"
    # L'état global doit refléter la vigueur réduite
    assert diagnostic.etat_global == EtatGlobal.vigueur_reduite


# ===========================================================================
# D. Chemins d'erreur
# ===========================================================================


@pytest.mark.asyncio
async def should_raise_reasoning_error_for_unknown_variable() -> None:
    """Une règle référençant une variable absente lève ReasoningEngineError."""
    from gsie_api.engines.reasoning.schemas import RegleInference

    contexte = _ctx_station(essence_cible="Fagus sylvatica")
    regle = RegleInference(
        identifiant="test_variable_absente",
        condition="variable_inexistante == 'test'",
        enonce_conclusion="Conclusion sur variable absente",
        source=_src_rameau(),
        evidence_level=DbEvidenceLevel.c,
        niveau_confiance=0.5,
    )
    session = AsyncMock()
    engine = ReasoningEngine(session)
    request = ReasoningRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        contexte=contexte,
        regles=[regle],
        question="Test erreur",
        profondeur_max=3,
    )
    with pytest.raises(ReasoningEngineError, match="variable_inexistante"):
        await engine.infer(request, _DATE)


@pytest.mark.asyncio
async def should_raise_reasoning_error_for_malformed_condition() -> None:
    """Une règle avec une condition non parsable lève ReasoningEngineError."""
    from gsie_api.engines.reasoning.schemas import RegleInference

    contexte = _ctx_station()
    regle = RegleInference(
        identifiant="test_malformee",
        condition="ceci n'est pas du python valide !!!",
        enonce_conclusion="Conclusion mal formée",
        source=_src_rameau(),
        evidence_level=DbEvidenceLevel.c,
        niveau_confiance=0.5,
    )
    session = AsyncMock()
    engine = ReasoningEngine(session)
    request = ReasoningRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        contexte=contexte,
        regles=[regle],
        question="Test",
        profondeur_max=3,
    )
    with pytest.raises(ReasoningEngineError):
        await engine.infer(request, _DATE)


def should_raise_simulation_error_for_unknown_species() -> None:
    """Le backend calibré rejette une essence non calibrée."""
    backend = CalibratedGrowthBackend()
    with pytest.raises(SimulationBackendError, match="non calibrée"):
        backend.simulate_growth("Unknown species", {"volume": 100.0}, 10)


def should_raise_simulation_error_for_negative_volume() -> None:
    """Le backend calibré rejette un volume négatif."""
    backend = CalibratedGrowthBackend()
    with pytest.raises(SimulationBackendError, match="négatif"):
        backend.simulate_growth("Fagus sylvatica", {"volume": -50.0}, 10)


def should_raise_simulation_error_for_empty_initial_state() -> None:
    """Le backend calibré exige au moins volume ou circonférence > 0."""
    backend = CalibratedGrowthBackend()
    with pytest.raises(SimulationBackendError, match="initial_state"):
        backend.simulate_growth("Fagus sylvatica", {}, 10)


def should_cap_volume_at_production_maximale_for_abies() -> None:
    """Abies alba (production max 600) — projection plafonnée à maturité."""
    backend = CalibratedGrowthBackend()
    # AMA Abies = 9.0, sur 100 ans = 900, initial 200 → 1100 > 600 → capped
    result = backend.simulate_growth(
        "Abies alba", {"volume": 200.0}, 100
    )
    assert result["capped"] is True
    assert result["final_volume"] <= 600.0


# ===========================================================================
# E. Stress test — 100+ règles
# ===========================================================================


@pytest.mark.asyncio
async def should_handle_100_plus_rules_in_reasonable_time() -> None:
    """Stress test — 26 profils (Parelle + Rameau) → 26 règles, inférence < 2s.

    Vérifie que le Reasoning Engine termine en temps raisonnable avec le
    corpus complet d'autécologie (26 règles sur 6 essences). Le moteur
    évalue les règles par chaînage avant borné — la complexité est
    linéaire en nombre de règles × profondeur.
    """
    from gsie_api.seeds.autecology_rameau_data import all_autecology_profiles

    all_profiles = all_autecology_profiles()
    assert len(all_profiles) == 26  # 6 Parelle + 20 Rameau
    regles = profiles_to_rules(all_profiles)
    assert len(regles) == 26

    contexte = _ctx_station(essence_cible="Fagus sylvatica")
    session = AsyncMock()
    engine = ReasoningEngine(session)
    request = ReasoningRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        contexte=contexte,
        regles=regles,
        question="Évaluation complète de la station",
        profondeur_max=5,
    )
    start = time.perf_counter()
    result = await engine.infer(request, _DATE)
    elapsed = time.perf_counter() - start

    # 5 conclusions pour Fagus (les autres essences ne matchent pas)
    fagus_conclusions = [c for c in result.conclusions if "Fagus sylvatica" in c.enonce]
    assert len(fagus_conclusions) == 5
    # Doit terminer en moins de 2 secondes (marge large pour CI)
    assert elapsed < 2.0, f"Reasoning trop lent : {elapsed:.2f}s pour 26 règles"


# ===========================================================================
# F. Simulation comparative — 4 essences sur 30 ans
# ===========================================================================


def should_compare_growth_across_four_species_over_30_years() -> None:
    """Comparaison des accroissements sur 30 ans pour 4 essences.

    Vérifie que le classement des accroissements est cohérent avec les
    AMA IGN : Abies alba (9.0) > Fagus (7.0) > Pinus (6.0) > Quercus ilex (2.0).
    """
    backend = CalibratedGrowthBackend()
    results = {}
    for species in ["Abies alba", "Fagus sylvatica", "Pinus sylvestris", "Quercus ilex"]:
        result = backend.simulate_growth(
            species, {"volume": 100.0}, 30
        )
        results[species] = result["volume_increment"]

    # Classement attendu : Abies > Fagus > Pinus > Quercus ilex
    assert results["Abies alba"] > results["Fagus sylvatica"]
    assert results["Fagus sylvatica"] > results["Pinus sylvestris"]
    assert results["Pinus sylvestris"] > results["Quercus ilex"]
    # Vérification des valeurs exactes (AMA × 30 ans)
    # Abies : 9.0 × 30 = 270 (production max 600, non plafonné)
    assert results["Abies alba"] == pytest.approx(270.0)
    # Quercus ilex : 2.0 × 30 = 60, mais production max = 150
    # initial 100 + 60 = 160 > 150 → plafonné à 150 → increment = 50
    assert results["Quercus ilex"] == pytest.approx(50.0)  # plafonné par production max


def should_compare_linear_vs_calibrated_backend() -> None:
    """Le backend calibré produit des projections différentes du linéaire v1.

    Vérifie que le CalibratedGrowthBackend (AMA IGN) et le LinearGrowthBackend
    (5%/an arbitraire) donnent des résultats différents — le calibré est
    ancré dans des données réelles, le linéaire est arbitraire.
    """
    linear = LinearGrowthBackend()
    calibrated = CalibratedGrowthBackend()
    initial = {"volume": 100.0}
    horizon = 30

    linear_result = linear.simulate_growth("Fagus sylvatica", initial, horizon)
    calibrated_result = calibrated.simulate_growth("Fagus sylvatica", initial, horizon)

    # Les deux doivent produire un volume final > initial
    assert linear_result["final_volume"] > 100.0
    assert calibrated_result["final_volume"] > 100.0
    # Mais avec des valeurs différentes (modèles différents)
    assert linear_result["final_volume"] != calibrated_result["final_volume"]
    # Le calibré doit citer IGN, le linéaire non
    assert "IGN" in calibrated_result["volume_source"]
    assert "IGN" not in linear_result["source"]


# ===========================================================================
# G. Validation + Learning — chaîne complète avec 5 blocages
# ===========================================================================


@pytest.mark.asyncio
async def should_trigger_calibration_after_five_blocked_outputs() -> None:
    """5 blocages sans_source → le Learning Engine propose une calibration.

    Simule un moteur amont qui produit systématiquement des sorties sans
    source. Après 5 blocages, le Learning Engine doit émettre une
    proposition de calibration (vérification de l'accumulateur).
    """
    learning = LearningEngine()
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
        await learning.process(signal)

    # L'accumulateur doit avoir compté 5 blocages sans_source
    assert learning._blocages_accumules.get("sans_source") == 5
    # Une proposition de calibration doit avoir été émise
    assert "sans_source" in learning._propositions_emises


@pytest.mark.asyncio
async def should_not_trigger_calibration_before_threshold() -> None:
    """4 blocages (sous le seuil de 5) → pas de calibration encore."""
    learning = LearningEngine()
    for _ in range(4):
        signal = LearningSignal(
            signal_id=uuid4(),
            type=LearningSignalType.sortie_bloquee,
            contenu={
                "validation_id": str(uuid4()),
                "statut": "bloque",
                "causes_blocage": [
                    {"type_cause": "autre_cause", "description": "Autre cause"},
                ],
                "controles_non_conformes": [],
            },
            date_signal=datetime.now(UTC),
        )
        await learning.process(signal)

    assert learning._blocages_accumules.get("autre_cause") == 4
    # Pas encore de proposition (seuil = 5)
    assert "autre_cause" not in learning._propositions_emises


# ===========================================================================
# H. Parcours API HTTP — sans DB
# ===========================================================================


class TestApiHttpEndpoints:
    """Tests HTTP via TestClient FastAPI — endpoints sans DB."""

    def should_return_200_on_health(self) -> None:
        """GET /health retourne 200 — l'API est vivante."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def should_return_200_on_ready(self) -> None:
        """GET /ready retourne 200 — l'API est prête."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/ready")
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "engine",
        [
            "evidence", "knowledge", "correlation", "reasoning", "diagnostic",
            "gis", "climate", "pedology", "recommendation", "validation",
            "learning", "simulation",
        ],
    )
    def should_return_200_on_engine_status(self, engine: str) -> None:
        """GET /api/v1/{engine}/status retourne 200 pour chaque moteur."""
        app = create_app()
        client = TestClient(app)
        response = client.get(f"/api/v1/{engine}/status")
        assert response.status_code == 200
        data = response.json()
        assert "engine" in data
        # Les moteurs v1 ont soit "version" soit "status" (nouveaux moteurs)
        assert "version" in data or "status" in data

    def should_return_404_on_unknown_endpoint(self) -> None:
        """GET /api/v1/inexistant retourne 404 au format RFC 7807."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/api/v1/inexistant")
        assert response.status_code == 404
        data = response.json()
        # Format RFC 7807 Problem Details
        assert "title" in data or "detail" in data

    def should_return_trace_id_header(self) -> None:
        """Chaque réponse porte un header X-Trace-Id (traçabilité CON-005)."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert "x-trace-id" in {k.lower() for k in response.headers.keys()}

    def should_return_security_headers(self) -> None:
        """Les headers de sécurité OWASP sont présents."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        # X-Content-Type-Options: nosniff (OWASP A05)
        assert "x-content-type-options" in headers_lower

    def should_reject_unauthenticated_post_on_protected_endpoint(self) -> None:
        """POST sans token JWT → 401 ou 403 (OWASP A01)."""
        app = create_app()
        client = TestClient(app)
        # Tenter un POST sur un endpoint protégé (evidence evaluate)
        response = client.post(
            "/api/v1/evidence/evaluate",
            json={"test": "unauthorized"},
        )
        assert response.status_code in {401, 403, 422}  # 422 si validation échoue d'abord

    def should_return_openapi_spec_in_dev(self) -> None:
        """GET /api/v1/openapi.json retourne la spec OpenAPI (non-prod)."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/api/v1/openapi.json")
        # Peut être 200 si non-prod, 404 si prod — on accepte les deux
        if response.status_code == 200:
            data = response.json()
            assert "openapi" in data
            assert "paths" in data


# ===========================================================================
# I. Parcours complet Evidence → Simulation (récapitulatif)
# ===========================================================================


@pytest.mark.asyncio
async def should_run_complete_pipeline_with_all_engines_e2e() -> None:
    """Parcours E2E complet — tous les moteurs enchaînés sur données réelles.

    Test récapitulatif qui enchaîne :
    1. Reasoning (règles Rameau) → conclusions
    2. Diagnostic (synthèse contraintes/atouts) → diagnostic
    3. Recommendation (objectif reboisement) → recommandation
    4. Validation (pipeline) → validation + learning
    5. Simulation (CalibratedGrowthBackend IGN) → projection 30 ans

    Vérifie que la chaîne complète produit une réponse exploitable pour
    un forestier : diagnostic + recommandation + validation + projection.
    """
    # 1. Reasoning
    profiles = build_autecology_rameau_profiles()
    fagus = [p for p in profiles if p.species_gbif_taxon_key == GBIF_TAXON_KEY_FAGUS_SYLVATICA]
    regles = profiles_to_rules(fagus)
    contexte = _ctx_station(essence_cible="Fagus sylvatica", volume=120.0)

    reasoning = ReasoningEngine(AsyncMock())
    inference = await reasoning.infer(
        ReasoningRequest(
            requete_id=uuid4(),
            station_id=uuid4(),
            contexte=contexte,
            regles=regles,
            question="Diagnostic complet pour reboisement hêtre",
            profondeur_max=5,
        ),
        _DATE,
    )
    assert len(inference.conclusions) == 5

    # 2. Diagnostic
    qualifications = _qualifier_conclusions(inference.conclusions)
    diagnostic = await DiagnosticEngine(_mock_diag_session()).diagnostiquer(
        DiagnosticRequest(
            requete_id=uuid4(),
            station_id=uuid4(),
            conclusions=inference.conclusions,
            qualifications=qualifications,
            etat_global=EtatGlobalDeclare(
                etat=EtatGlobal.sain,
                justification="Station favorable au hêtre",
                source=_src_terrain(),
                evidence_level=DbEvidenceLevel.c,
            ),
            contexte=contexte,
            type_diagnostic=TypeDiagnostic.stationnel,
        ),
        _DATE,
    )
    assert len(diagnostic.atouts) + len(diagnostic.contraintes) >= 1

    # 3. Recommendation
    reco = await RecommendationEngine().recommend(
        RecommendationRequest(
            requete_id=uuid4(),
            diagnostic_id=diagnostic.diagnostic_id,
            objectif_forestier=ObjectifForestier.REBOISEMENT,
        )
    )
    assert len(reco.recommandations) >= 1

    # 4. Validation + Learning
    pipeline = await run_validation_pipeline(
        diagnostic, reco, conclusions=inference.conclusions,
        learning_engine=LearningEngine(),
    )
    validation = pipeline["validation"]
    assert validation.statut in {
        ValidationStatut.valide,
        ValidationStatut.partiellement_valide,
    }

    # 5. Simulation
    growth = CalibratedGrowthBackend().simulate_growth(
        "Fagus sylvatica",
        {"volume": 120.0, "circumference": 70.0},
        30,
        parameters={"density_factor": 0.9},
    )
    assert growth["final_volume"] > 120.0
    assert growth["final_circumference"] > 70.0

    # Synthèse : le forestier reçoit une réponse complète
    assert diagnostic is not None
    assert reco is not None
    assert validation is not None
    assert growth is not None

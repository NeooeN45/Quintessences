"""Tests unitaires — Learning Engine.

Vérifie la détection de patterns de refus et le traitement des
patterns émergents, avec subordination aux règles expertes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from gsie_api.engines.learning.engine import LearningEngine
from gsie_api.engines.learning.schemas import (
    LearningOutput,
    LearningOutputType,
    LearningSignal,
    LearningSignalType,
    LearningStatut,
)


def _make_retour_signal(decision: str = "refuse", contexte: uuid4 | None = None) -> LearningSignal:
    return LearningSignal(
        signal_id=uuid4(),
        type=LearningSignalType.retour_forestier,
        contenu={
            "recommandation_id": str(uuid4()),
            "decision": decision,
            "contexte_station": str(contexte or uuid4()),
        },
        date_signal=datetime.now(UTC),
    )


def _make_pattern_signal(
    confiance: float = 0.8, description: str = "Pattern test"
) -> LearningSignal:
    return LearningSignal(
        signal_id=uuid4(),
        type=LearningSignalType.pattern_emergent,
        contenu={
            "description": description,
            "correlations": [],
            "confiance": confiance,
        },
        date_signal=datetime.now(UTC),
    )


@pytest.fixture
def engine() -> LearningEngine:
    return LearningEngine()


# --- Tests retour forestier ---


@pytest.mark.asyncio
async def should_return_none_when_single_refus(engine: LearningEngine) -> None:
    """Un refus isolé ne déclenche pas de proposition (sur-réaction évitée)."""
    signal = _make_retour_signal()
    result = await engine.process(signal)
    assert result is None


@pytest.mark.asyncio
async def should_return_proposition_when_threshold_refus_reached(engine: LearningEngine) -> None:
    """5 refus sur le même contexte déclenchent une proposition de révision."""
    contexte = uuid4()
    for _ in range(5):
        signal = _make_retour_signal(contexte=contexte)
        result = await engine.process(signal)
    # Le 5e refus déclenche la proposition
    assert result is not None
    assert result.type == LearningOutputType.proposition_revision
    assert result.statut == LearningStatut.propose
    assert len(result.justification) >= 1
    assert 0.5 <= result.confidence <= 0.95


@pytest.mark.asyncio
async def should_not_propose_for_accepte_decisions() -> None:
    """Les décisions 'accepte' n'accumulent pas de pattern de refus."""
    engine = LearningEngine()
    contexte = uuid4()
    for _ in range(10):
        signal = _make_retour_signal(decision="accepte", contexte=contexte)
        result = await engine.process(signal)
    assert result is None


# --- Tests pattern émergent ---


@pytest.mark.asyncio
async def should_return_pattern_confirme_when_high_confidence(engine: LearningEngine) -> None:
    """Un pattern émergent avec confiance >= 0.7 produit une proposition confirmée."""
    signal = _make_pattern_signal(confiance=0.85)
    result = await engine.process(signal)
    assert result is not None
    assert result.type == LearningOutputType.pattern_confirme
    assert result.statut == LearningStatut.propose
    assert result.confidence == 0.85


@pytest.mark.asyncio
async def should_return_none_when_low_confidence_pattern(engine: LearningEngine) -> None:
    """Un pattern émergent avec confiance < 0.7 est ignoré."""
    signal = _make_pattern_signal(confiance=0.5)
    result = await engine.process(signal)
    assert result is None


# --- Tests sortie bloquée (Validation Engine → Learning) ---


@pytest.mark.asyncio
async def should_accumulate_sortie_bloquee_and_propose_calibration(engine: LearningEngine) -> None:
    """5 blocages du même type déclenchent une calibration proposée."""
    contenu = {
        "validation_id": str(uuid4()),
        "statut": "bloque",
        "causes_blocage": [
            {"type_cause": "sans_source", "description": "Aucune source"},
        ],
        "controles_non_conformes": [
            {"nom_controle": "presence_source", "details": "ko"},
        ],
    }
    for _ in range(5):
        signal = LearningSignal(
            signal_id=uuid4(),
            type=LearningSignalType.sortie_bloquee,
            contenu=contenu,
            date_signal=datetime.now(UTC),
        )
        result = await engine.process(signal)
    # Le 5e blocage déclenche la proposition
    assert result is not None
    assert result.type == LearningOutputType.calibration_modele
    assert result.statut == LearningStatut.propose


@pytest.mark.asyncio
async def should_return_none_when_sortie_bloquee_without_causes(engine: LearningEngine) -> None:
    """Un signal sortie_bloquee sans cause est ignoré."""
    signal = LearningSignal(
        signal_id=uuid4(),
        type=LearningSignalType.sortie_bloquee,
        contenu={"causes_blocage": []},
        date_signal=datetime.now(UTC),
    )
    result = await engine.process(signal)
    assert result is None


@pytest.mark.asyncio
async def should_not_reissue_proposition_for_same_cause(engine: LearningEngine) -> None:
    """Une proposition n'est émise qu'une fois par type de cause."""
    contenu = {
        "validation_id": str(uuid4()),
        "statut": "bloque",
        "causes_blocage": [
            {"type_cause": "sans_source", "description": "Aucune source"},
        ],
        "controles_non_conformes": [],
    }
    signal = LearningSignal(
        signal_id=uuid4(),
        type=LearningSignalType.sortie_bloquee,
        contenu=contenu,
        date_signal=datetime.now(UTC),
    )
    # 5 blocages → proposition
    for _ in range(5):
        await engine.process(signal)
    # 5 blocages supplémentaires → pas de nouvelle proposition
    result = await engine.process(signal)
    assert result is None


@pytest.mark.asyncio
async def should_raise_for_observation_terrain_in_v1(engine: LearningEngine) -> None:
    """Le type observation_terrain n'est pas géré en v1."""
    signal = LearningSignal(
        signal_id=uuid4(),
        type=LearningSignalType.observation_terrain,
        contenu={},
        date_signal=datetime.now(UTC),
    )
    with pytest.raises(Exception, match="non géré en v1"):
        await engine.process(signal)


# --- Tests invariants schéma ---


def should_require_justification_non_vide() -> None:
    """Le schéma rejette une proposition sans justification."""
    with pytest.raises(ValueError, match="justification"):
        LearningOutput(
            output_id=uuid4(),
            type=LearningOutputType.proposition_revision,
            description="Test",
            justification=[],  # vide — interdit
            confidence=0.5,
            date_output=datetime.now(UTC),
            statut=LearningStatut.propose,
        )


def should_require_confidence_in_range() -> None:
    """Le schéma rejette une confiance hors [0, 1]."""
    with pytest.raises(ValueError):
        LearningOutput(
            output_id=uuid4(),
            type=LearningOutputType.proposition_revision,
            description="Test",
            justification=["test"],
            confidence=1.5,  # hors plage
            date_output=datetime.now(UTC),
            statut=LearningStatut.propose,
        )


# ===========================================================================
# Couverture complémentaire — lignes 100, 111-112
# ===========================================================================


async def should_raise_for_unknown_signal_type(engine: LearningEngine) -> None:
    """Un type de signal inconnu doit lever LearningEngineError (garde défensive)."""
    # Tous les types de LearningSignalType sont gérés en v1.
    # La ligne 100 est une garde défensive — on la teste en mockant
    # les vérifications pour qu'aucune ne matche.
    from unittest.mock import patch

    signal = LearningSignal(
        signal_id=uuid4(),
        type=LearningSignalType.sortie_bloquee,
        contenu={},
        date_signal=datetime.now(UTC),
    )

    # Patch les 4 vérifications pour qu'aucune ne matche → ligne 100
    with (
        patch("gsie_api.engines.learning.engine.LearningSignalType") as mock_type,
    ):
        mock_type.retour_forestier = "fake_retour"
        mock_type.pattern_emergent = "fake_pattern"
        mock_type.sortie_bloquee = "fake_sortie"
        mock_type.observation_terrain = "fake_obs"
        # signal.type vaut toujours "sortie_bloquee" (StrEnum),
        # mais les comparaisons ne matchent plus → ligne 100

        with pytest.raises(Exception, match="Type de signal inconnu"):
            await engine.process(signal)


async def should_raise_when_retour_forestier_content_invalid(engine: LearningEngine) -> None:
    """Un retour_forestier avec contenu invalide doit lever LearningEngineError."""
    signal = LearningSignal(
        signal_id=uuid4(),
        type=LearningSignalType.retour_forestier,
        contenu={"champ_inattendu": "valeur"},  # manque les champs requis
        date_signal=datetime.now(UTC),
    )
    with pytest.raises(Exception, match="Contenu de retour_forestier invalide"):
        await engine.process(signal)


# --- Tests version() ---


def should_return_version_string() -> None:
    """version() retourne la version du moteur."""
    assert LearningEngine.version() == "0.1.0"


# --- Tests isolation de contexte ---


@pytest.mark.asyncio
async def should_not_cross_context_signals(engine: LearningEngine) -> None:
    """Les refus sur un contexte A ne déclenchent pas de proposition sur le contexte B."""
    contexte_a = uuid4()
    contexte_b = uuid4()
    # 4 refus sur A (sous le seuil)
    for _ in range(4):
        signal = _make_retour_signal(contexte=contexte_a)
        result = await engine.process(signal)
        assert result is None
    # 1 refus sur B — ne doit pas déclencher (A a 4, B a 1)
    signal_b = _make_retour_signal(contexte=contexte_b)
    result = await engine.process(signal_b)
    assert result is None, (
        "un refus sur B ne doit pas déclencher de proposition : "
        "les signaux de A ne doivent pas compter pour B"
    )


@pytest.mark.asyncio
async def should_trigger_exactly_at_threshold(engine: LearningEngine) -> None:
    """Le 5e refus déclenche, pas le 4e."""
    contexte = uuid4()
    for i in range(4):
        result = await engine.process(_make_retour_signal(contexte=contexte))
        assert result is None, f"le {i+1}e refus ne doit pas déclencher"
    # 5e refus → déclenche
    result = await engine.process(_make_retour_signal(contexte=contexte))
    assert result is not None, "le 5e refus doit déclencher la proposition"


@pytest.mark.asyncio
async def should_isolate_state_between_instances() -> None:
    """Deux instances distinctes ne partagent pas leur cache interne."""
    engine_a = LearningEngine()
    engine_b = LearningEngine()
    contexte = uuid4()
    # 4 refus sur engine_a
    for _ in range(4):
        await engine_a.process(_make_retour_signal(contexte=contexte))
    # 1 refus sur engine_b — ne doit pas déclencher
    result = await engine_b.process(_make_retour_signal(contexte=contexte))
    assert result is None, (
        "engine_b ne doit pas partager l'état de engine_a : "
        "les caches d'accumulation sont par instance"
    )

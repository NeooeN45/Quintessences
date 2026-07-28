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

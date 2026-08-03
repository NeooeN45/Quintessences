"""Tests d'intégration — Learning Engine sur PostgreSQL réel.

Le moteur est stateless en v1 : il ne persiste rien et n'accepte pas de
session DB. Ces tests valident néanmoins son comportement avec une vraie
session PostgreSQL active (via testcontainers), pour préparer la v2 où
les propositions seront persistées pour audit (LEARNING_ENGINE.md §6).

Le cache en mémoire (`_signaux_accumules`, `_blocages_accumules`) est
par-instance : chaque test instancie son propre moteur pour isoler
l'accumulation des signaux.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest

from gsie_api.engines.learning.engine import LearningEngine, LearningEngineError
from gsie_api.engines.learning.schemas import (
    LearningOutput,
    LearningOutputType,
    LearningSignal,
    LearningSignalType,
    LearningStatut,
)
from tests.conftest import requires_docker

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = requires_docker

_SEUIL_PATTERN_REFUS = 5


def _retour_forestier(
    decision: str = "refuse",
    contexte: UUID | None = None,
) -> LearningSignal:
    """Construit un signal `retour_forestier` avec un contexte station fixe."""
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


def _pattern_emergent(confiance: float, description: str = "Pattern test") -> LearningSignal:
    """Construit un signal `pattern_emergent` avec une confiance donnée."""
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


def _sortie_bloquee(type_cause: str = "sans_source") -> LearningSignal:
    """Construit un signal `sortie_bloquee` avec une cause de blocage."""
    return LearningSignal(
        signal_id=uuid4(),
        type=LearningSignalType.sortie_bloquee,
        contenu={
            "validation_id": str(uuid4()),
            "statut": "bloque",
            "causes_blocage": [
                {"type_cause": type_cause, "description": "Aucune source"},
            ],
            "controles_non_conformes": [],
        },
        date_signal=datetime.now(UTC),
    )


async def should_return_none_when_isolated_refus_below_threshold(
    db_session: AsyncSession,
) -> None:
    """Un refus isolé (sous le seuil) est accumulé sans déclencher de proposition."""
    engine = LearningEngine()
    signal = _retour_forestier()

    result = await engine.process(signal)

    assert result is None


async def should_return_proposition_revision_when_five_refus_accumulated_on_same_contexte(
    db_session: AsyncSession,
) -> None:
    """5 refus sur le même contexte station déclenchent une `proposition_revision`."""
    engine = LearningEngine()
    contexte = uuid4()
    result: LearningOutput | None = None
    for _ in range(_SEUIL_PATTERN_REFUS):
        result = await engine.process(_retour_forestier(contexte=contexte))

    assert result is not None
    assert result.type == LearningOutputType.proposition_revision
    assert result.statut == LearningStatut.propose
    assert len(result.justification) >= 1
    assert 0.5 <= result.confidence <= 0.95


async def should_return_none_when_accepte_decisions_do_not_accumulate_refus(
    db_session: AsyncSession,
) -> None:
    """Les décisions 'accepte' n'accumulent pas de pattern de refus, même au-delà du seuil."""
    engine = LearningEngine()
    contexte = uuid4()
    result: LearningOutput | None = None
    for _ in range(_SEUIL_PATTERN_REFUS + 5):
        result = await engine.process(_retour_forestier(decision="accepte", contexte=contexte))

    assert result is None


async def should_return_pattern_confirme_when_pattern_emergent_confiance_above_seuil(
    db_session: AsyncSession,
) -> None:
    """Un pattern émergent avec confiance >= 0.7 produit une proposition `pattern_confirme`."""
    engine = LearningEngine()
    signal = _pattern_emergent(confiance=0.85, description="Hêtre refusé en plaine")

    result = await engine.process(signal)

    assert result is not None
    assert result.type == LearningOutputType.pattern_confirme
    assert result.statut == LearningStatut.propose
    assert result.confidence == 0.85
    assert len(result.justification) >= 1


async def should_return_none_when_pattern_emergent_confiance_below_seuil(
    db_session: AsyncSession,
) -> None:
    """Un pattern émergent avec confiance < 0.7 est ignoré (trop faible)."""
    engine = LearningEngine()
    signal = _pattern_emergent(confiance=0.5)

    result = await engine.process(signal)

    assert result is None


async def should_return_calibration_modele_when_sortie_bloquee_reaches_seuil(
    db_session: AsyncSession,
) -> None:
    """5 blocages du même type de cause déclenchent une `calibration_modele`."""
    engine = LearningEngine()
    signal = _sortie_bloquee(type_cause="sans_source")
    result: LearningOutput | None = None
    for _ in range(_SEUIL_PATTERN_REFUS):
        result = await engine.process(signal)

    assert result is not None
    assert result.type == LearningOutputType.calibration_modele
    assert result.statut == LearningStatut.propose
    assert 0.5 <= result.confidence <= 0.95
    assert len(result.justification) >= 1


async def should_return_none_when_sortie_bloquee_without_causes(
    db_session: AsyncSession,
) -> None:
    """Un signal `sortie_bloquee` sans cause de blocage est ignoré."""
    engine = LearningEngine()
    signal = LearningSignal(
        signal_id=uuid4(),
        type=LearningSignalType.sortie_bloquee,
        contenu={"causes_blocage": []},
        date_signal=datetime.now(UTC),
    )

    result = await engine.process(signal)

    assert result is None


async def should_raise_learning_engine_error_when_observation_terrain_in_v1(
    db_session: AsyncSession,
) -> None:
    """Le type `observation_terrain` n'est pas géré en v1 — lève `LearningEngineError`."""
    engine = LearningEngine()
    signal = LearningSignal(
        signal_id=uuid4(),
        type=LearningSignalType.observation_terrain,
        contenu={},
        date_signal=datetime.now(UTC),
    )

    with pytest.raises(LearningEngineError, match="non géré en v1"):
        await engine.process(signal)

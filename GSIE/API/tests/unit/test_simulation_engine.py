"""Tests unitaires — Simulation Engine.

Vérifie la génération de projections temporelles, le parsing d'horizon
et les invariants du schéma (sources, assumptions non vides).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from gsie_api.engines.simulation.engine import SimulationEngine, SimulationEngineError
from gsie_api.engines.simulation.schemas import (
    ConfidenceLevel,
    InterventionSpec,
    ScenarioSimulation,
    SimulationResult,
    TimedProjection,
)


def _make_scenario(
    horizon: str = "30y",
    intervention_type: str = "eclaircie",
    parametres: dict | None = None,
) -> ScenarioSimulation:
    return ScenarioSimulation(
        scenario_id=uuid4(),
        source_diagnostic=uuid4(),
        intervention=InterventionSpec(
            type_intervention=intervention_type,
            parametres=parametres or {"intensite": "25", "densite": 1000},
        ),
        horizon=horizon,
    )


@pytest.fixture
def engine() -> SimulationEngine:
    return SimulationEngine()


# --- Tests simulation ---

@pytest.mark.asyncio
async def should_generate_projections_for_standard_horizon(engine: SimulationEngine) -> None:
    """Un horizon 30y génère des projections à 5, 10 et 30 ans."""
    scenario = _make_scenario(horizon="30y")
    result = await engine.simulate(scenario)
    assert len(result.projections) == 3
    horizons = [p.key_indicators.get("horizon_annees") for p in result.projections]
    assert sorted(horizons) == [5, 10, 30]


@pytest.mark.asyncio
async def should_generate_projection_for_custom_horizon(engine: SimulationEngine) -> None:
    """Un horizon 15y génère les pas standards <= 15 + une projection à 15 ans."""
    scenario = _make_scenario(horizon="15y")
    result = await engine.simulate(scenario)
    horizons = [p.key_indicators.get("horizon_annees") for p in result.projections]
    assert 5 in horizons and 10 in horizons and 15 in horizons
    assert 30 not in horizons  # 30 > 15


@pytest.mark.asyncio
async def should_return_low_confidence_in_v1(engine: SimulationEngine) -> None:
    """Le modèle v1 est explicitement marqué confidence=low."""
    scenario = _make_scenario()
    result = await engine.simulate(scenario)
    assert result.confidence == ConfidenceLevel.low


@pytest.mark.asyncio
async def should_include_sources_and_assumptions(engine: SimulationEngine) -> None:
    """Toute simulation cite ses sources et hypothèses (GSIE-CON-004, CON-005)."""
    scenario = _make_scenario()
    result = await engine.simulate(scenario)
    assert len(result.sources) >= 1
    assert len(result.assumptions) >= 1


@pytest.mark.asyncio
async def should_compute_biomasse_growth(engine: SimulationEngine) -> None:
    """La biomasse croît avec l'horizon (modèle linéaire v1)."""
    scenario = _make_scenario(horizon="30y")
    result = await engine.simulate(scenario)
    biomasses = [p.key_indicators.get("biomasse_t_ha") for p in result.projections]
    # La biomasse doit croître avec le temps
    assert biomasses[0] < biomasses[-1]


# --- Tests parsing horizon ---

@pytest.mark.asyncio
async def should_parse_horizon_with_y_suffix(engine: SimulationEngine) -> None:
    """L'horizon '10y' est parsé comme 10 ans."""
    scenario = _make_scenario(horizon="10y")
    result = await engine.simulate(scenario)
    assert any(p.key_indicators.get("horizon_annees") == 10 for p in result.projections)


@pytest.mark.asyncio
async def should_parse_horizon_without_y_suffix(engine: SimulationEngine) -> None:
    """L'horizon '10' (sans suffixe) est parsé comme 10 ans."""
    scenario = _make_scenario(horizon="10")
    result = await engine.simulate(scenario)
    assert any(p.key_indicators.get("horizon_annees") == 10 for p in result.projections)


@pytest.mark.asyncio
async def should_raise_for_invalid_horizon(engine: SimulationEngine) -> None:
    """Un horizon non numérique lève une erreur."""
    scenario = _make_scenario(horizon="abc")
    with pytest.raises(SimulationEngineError, match="Horizon invalide"):
        await engine.simulate(scenario)


@pytest.mark.asyncio
async def should_raise_for_negative_horizon(engine: SimulationEngine) -> None:
    """Un horizon négatif lève une erreur."""
    scenario = _make_scenario(horizon="-5y")
    with pytest.raises(SimulationEngineError, match="hors plage"):
        await engine.simulate(scenario)


@pytest.mark.asyncio
async def should_raise_for_excessive_horizon(engine: SimulationEngine) -> None:
    """Un horizon > 200 ans lève une erreur."""
    scenario = _make_scenario(horizon="500y")
    with pytest.raises(SimulationEngineError, match="hors plage"):
        await engine.simulate(scenario)


# --- Tests invariants schéma ---

def should_reject_simulation_result_without_sources() -> None:
    """Le schéma rejette un résultat sans sources (GSIE-CON-005)."""
    with pytest.raises(ValueError, match="sources"):
        SimulationResult(
            scenario_id=uuid4(),
            projections=[
                TimedProjection(
                    timestamp=datetime.now(UTC),
                    state={},
                    key_indicators={},
                )
            ],
            confidence=ConfidenceLevel.low,
            sources=[],  # vide — interdit
            assumptions=["test"],
        )


def should_reject_simulation_result_without_assumptions() -> None:
    """Le schéma rejette un résultat sans hypothèses (GSIE-CON-004)."""
    with pytest.raises(ValueError, match="assumptions"):
        SimulationResult(
            scenario_id=uuid4(),
            projections=[
                TimedProjection(
                    timestamp=datetime.now(UTC),
                    state={},
                    key_indicators={},
                )
            ],
            confidence=ConfidenceLevel.low,
            sources=[{"auteur": "test"}],
            assumptions=[],  # vide — interdit
        )


def should_reject_simulation_result_without_projections() -> None:
    """Le schéma rejette un résultat sans projections."""
    with pytest.raises(ValueError, match="projections"):
        SimulationResult(
            scenario_id=uuid4(),
            projections=[],  # vide — interdit
            confidence=ConfidenceLevel.low,
            sources=[{"auteur": "test"}],
            assumptions=["test"],
        )

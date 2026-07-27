"""Simulation Engine — simulation de scénarios d'évolution et d'intervention.

Voir `GSIE/ENGINES/SIMULATION_ENGINE/SIMULATION_ENGINE.md`.

Le moteur projette les conséquences des décisions avant qu'elles ne
soient prises. La simulation ne décide pas — elle projette, le
forestier/COS choisit (GSIE-CON-001).
"""

from gsie_api.engines.simulation.engine import SimulationEngine, SimulationEngineError
from gsie_api.engines.simulation.schemas import (
    ConfidenceLevel,
    InterventionSpec,
    ScenarioSimulation,
    SimulationResult,
    TimedProjection,
)

__all__ = [
    "ConfidenceLevel",
    "InterventionSpec",
    "ScenarioSimulation",
    "SimulationEngine",
    "SimulationEngineError",
    "SimulationResult",
    "TimedProjection",
]

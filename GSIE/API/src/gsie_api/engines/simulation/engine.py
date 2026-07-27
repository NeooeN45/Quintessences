"""Simulation Engine — simulation de scénarios d'évolution et d'intervention.

Responsabilité (SIMULATION_ENGINE.md §1) : simuler des scénarios
d'évolution et d'intervention à partir de l'état courant du système
(forêt, feu, climat) pour projeter les conséquences des décisions
avant qu'elles ne soient prises.

La simulation ne décide pas — elle projette des conséquences, le
forestier/COS choisit (GSIE-CON-001, §6).

Périmètre v1 :
- Projection déterministe simple basée sur les paramètres de
  l'intervention et l'horizon demandé. Pas de couplage à CAPSIS,
  iLand, LANDIS-II ou ForeFire en v1 (ces intégrations sont
  documentées §8 comme pistes pour une version ultérieure).
- Les projections sont des extrapolations linéaires des indicateurs
  clés (biomasse, densité) — explicitement marquées comme
  `confidence=low` pour refléter la simplicité du modèle.
- Les sources citées sont les modèles de croissance du Forest
  Dynamics Engine (référence abstraite en v1).
- Les hypothèses simplificatrices sont explicites (GSIE-CON-004).

Une future version intégrera :
- CAPSIS/iLand/LANDIS-II pour les modèles de croissance calibrés ;
- ForeFire pour les scénarios incendie (Ignis) ;
- SALib pour la quantification d'incertitude (Sobol/Morris) ;
- Le couplage au Centre de Commandement Unreal Engine 5.8 pour la
  visualisation.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from gsie_api.core.logging import get_logger
from gsie_api.engines.simulation.schemas import (
    ConfidenceLevel,
    InterventionSpec,
    ScenarioSimulation,
    SimulationResult,
    TimedProjection,
)

logger = get_logger("gsie_api.simulation.engine")

# Source abstraite pour le modèle de croissance en v1.
# Une future version référencera le Forest Dynamics Engine réel.
# Version 0.1.0 — modèle v1, sourcé par ADR-009 (valeurs traçables).
_V1_SOURCE = {
    "type_source": "referentiel_officiel",
    "auteur": "GSIE Forest Dynamics Engine (v1 — modèle linéaire)",
    "reference": "FOREST_DYNAMICS_ENGINE.md §5 — modèle de croissance (ADR-009)",
    "version_source": "0.1.0",
}

# Hypothèses simplificatrices du modèle v1 — explicites (GSIE-CON-004).
_V1_ASSUMPTIONS = [
    "Modèle linéaire : accroissement constant sur l'horizon de projection.",
    "Pas de mortalité ni perturbation modélisées en v1.",
    "Pas de couplage au scénario climatique — conditions stationnaires.",
    "Confiance 'low' : modèle simplifié, à remplacer par CAPSIS/iLand en v2.",
]

# Pas de projection temporelle (en années) pour les horizons standards.
_PROJECTION_STEPS = [5, 10, 30]


class SimulationEngineError(Exception):
    """Erreur de base du Simulation Engine."""


class SimulationEngine:
    """Moteur de simulation — stateless en v1.

    Le moteur ne persiste pas les résultats en v1 : chaque simulation
    est indépendante et retournée à l'appelant. Une future version
    pourra persister les résultats pour comparaison et alimentation
    du Learning Engine (§3 — écarts simulation/réalité).
    """

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    async def simulate(self, scenario: ScenarioSimulation) -> SimulationResult:
        """Simule un scénario d'intervention et projette les conséquences.

        Raises:
            SimulationEngineError: si l'horizon n'est pas parsable ou
                si l'intervention est invalide.
        """
        horizon_years = self._parse_horizon(scenario.horizon)
        projections = self._generate_projections(scenario, horizon_years)

        logger.info(
            "simulation_complete",
            scenario_id=str(scenario.scenario_id),
            intervention=scenario.intervention.type_intervention,
            horizon=scenario.horizon,
            n_projections=len(projections),
        )

        return SimulationResult(
            scenario_id=scenario.scenario_id,
            projections=projections,
            confidence=ConfidenceLevel.low,
            sources=[_V1_SOURCE],
            assumptions=_V1_ASSUMPTIONS,
        )

    def _parse_horizon(self, horizon: str) -> int:
        """Parse un horizon de projection en années.

        Accepte les formats : "5y", "10y", "30y", "5", "10".
        """
        horizon_clean = horizon.strip().lower().removesuffix("y")
        try:
            years = int(horizon_clean)
        except ValueError as exc:
            raise SimulationEngineError(
                f"Horizon invalide '{horizon}' — format attendu : '5y', '10y', '30y'"
            ) from exc
        if years <= 0 or years > 200:
            raise SimulationEngineError(
                f"Horizon {years} hors plage valide (1-200 ans)"
            )
        return years

    def _generate_projections(
        self, scenario: ScenarioSimulation, horizon_years: int
    ) -> list[TimedProjection]:
        """Génère les projections temporelles pour le scénario.

        Modèle v1 : extrapolation linéaire des indicateurs clés à
        partir des paramètres de l'intervention. Les projections sont
        générées aux pas standards (5, 10, 30 ans) dans la limite de
        l'horizon demandé.
        """
        now = datetime.now(UTC)
        intervention = scenario.intervention

        # Indicateurs initiaux dérivés des paramètres d'intervention
        # En v1, valeurs par défaut — une future version les récupérera
        # du diagnostic source et du Forest Dynamics Engine.
        biomasse_initiale = 100.0  # t/ha — valeur abstraite v1
        densite_initiale = float(
            intervention.parametres.get("densite", 1000)
        )

        # Taux d'accroissement annuel — modèle linéaire v1
        # Une future version utilisera un modèle de croissance calibré
        taux_accroissement = 0.02  # 2%/an — valeur abstraite v1

        projections: list[TimedProjection] = []
        for step in _PROJECTION_STEPS:
            if step > horizon_years:
                continue
            timestamp = now + timedelta(days=365 * step)
            biomasse = biomasse_initiale * ((1 + taux_accroissement) ** step)
            key_indicators = {
                "biomasse_t_ha": round(biomasse, 2),
                "densite_t_ha": round(densite_initiale, 0),
                "horizon_annees": step,
                "intervention": intervention.type_intervention,
            }
            projections.append(
                TimedProjection(
                    timestamp=timestamp,
                    state={
                        "intervention_appliquee": intervention.type_intervention,
                        "parametres": intervention.parametres,
                    },
                    key_indicators=key_indicators,
                )
            )

        # Toujours inclure la projection à l'horizon exact si non standard
        if horizon_years not in _PROJECTION_STEPS:
            timestamp = now + timedelta(days=365 * horizon_years)
            biomasse = biomasse_initiale * ((1 + taux_accroissement) ** horizon_years)
            projections.append(
                TimedProjection(
                    timestamp=timestamp,
                    state={
                        "intervention_appliquee": intervention.type_intervention,
                        "parametres": intervention.parametres,
                    },
                    key_indicators={
                        "biomasse_t_ha": round(biomasse, 2),
                        "densite_t_ha": round(densite_initiale, 0),
                        "horizon_annees": horizon_years,
                        "intervention": intervention.type_intervention,
                    },
                )
            )

        return sorted(projections, key=lambda p: p.timestamp)

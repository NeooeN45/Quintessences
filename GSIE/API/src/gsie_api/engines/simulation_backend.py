"""Backend de simulation — interface strategy pour modèles de croissance.

Architecture en strategy pattern qui permet de brancher différents
backends de simulation sans modifier le Simulation Engine :

- `LinearGrowthBackend` : modèle linéaire v1 (par défaut, confidence=low) ;
- `CalibratedGrowthBackend` : modèle calibré IGN (confidence=medium) ;
- `CapsisBackend` (futur) : wrapper CAPSIS via subprocess Java
  (non implémenté en v1, lève `NotImplementedError`).

Le Simulation Engine délègue la projection à un backend injecté. En v1
calibrée, on utilise `CalibratedGrowthBackend` qui s'appuie sur
`growth_models.py` (données IGN publiques). Une future version pourra
injecter `CapsisBackend` pour des projections calibrées INRAE/AMAP.

Voir `SIMULATION_ENGINE.md` §8 (pistes v2) et `FOREST_DYNAMICS_ENGINE.md`
pour le couplage avec le Forest Dynamics Engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from gsie_api.engines.growth_models import (
    GrowthModelError,
    project_circumference,
    project_volume,
)
from gsie_api.engines.simulation.schemas import ConfidenceLevel


class SimulationBackendError(Exception):
    """Erreur de base d'un backend de simulation."""


class GrowthBackend(ABC):
    """Interface abstraite d'un backend de simulation de croissance.

    Un backend projette l'état d'un peuplement sur un horizon donné.
    Le contrat est volontairement minimal : `simulate_growth` prend un
    état initial et un horizon, retourne un dict d'indicateurs projetés.
    """

    @abstractmethod
    def confidence(self) -> ConfidenceLevel:
        """Niveau de confiance du backend (low/medium/high)."""

    @abstractmethod
    def sources(self) -> list[str]:
        """Sources citées par le backend (GSIE-CON-005)."""

    @abstractmethod
    def assumptions(self) -> list[str]:
        """Hypothèses simplificatrices du backend (GSIE-CON-004)."""

    @abstractmethod
    def simulate_growth(
        self,
        species: str,
        initial_state: dict[str, float],
        horizon_years: int,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Projette l'état d'un peuplement mono-spécifique sur l'horizon.

        Args:
            species: nom scientifique de l'essence.
            initial_state: état initial (clés attendues : `volume`,
                `circumference` — optionnel).
            horizon_years: horizon de projection en années.
            parameters: paramètres additionnels (ex. `density_factor`).

        Returns:
            Dict avec les indicateurs projetés (volume, circonférence,
            accroissements, source, capped, etc.).

        Raises:
            SimulationBackendError: si l'essence n'est pas calibrée ou
                si les paramètres sont invalides.
        """


class LinearGrowthBackend(GrowthBackend):
    """Backend v1 — modèle linéaire arbitraire (confidence=low).

    Conservé pour compatibilité avec le v1 existant. Ne pas utiliser en
    production : préférez `CalibratedGrowthBackend`.
    """

    def confidence(self) -> ConfidenceLevel:
        return ConfidenceLevel.low

    def sources(self) -> list[str]:
        return ["FOREST_DYNAMICS_ENGINE.md §5 — modèle de croissance (ADR-009)"]

    def assumptions(self) -> list[str]:
        return [
            "Modèle linéaire : accroissement constant sur l'horizon.",
            "Pas de mortalité ni perturbation modélisées.",
            "Pas de couplage au scénario climatique — conditions stationnaires.",
            "Confiance 'low' : modèle simplifié, à remplacer par CAPSIS/iLand.",
        ]

    def simulate_growth(
        self,
        species: str,
        initial_state: dict[str, float],
        horizon_years: int,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        initial_volume = initial_state.get("volume", 0.0)
        # Taux d'accroissement arbitraire v1 (5% par an) : aucune source ne le
        # fonde, il ne depend pas de l'essence, et il ne vaut que pour comparer
        # des ordres de grandeur.
        annual_rate = 0.05
        projected = initial_volume * (1 + annual_rate) ** horizon_years
        return {
            "final_volume": projected,
            "increment": projected - initial_volume,
            "annual_increment": initial_volume * annual_rate,
            "species": species,
            # `sources()` renvoyait seule une reference documentaire — dont
            # ADR-009, le garde-fou anti-invention. Un consommateur qui ne lit
            # que cette charge utile prenait donc un taux invente pour une
            # valeur sourcee. `assumptions()` portait l'aveu, mais rien
            # n'obligeait a le lire : il accompagne desormais le resultat.
            "source": self.sources()[0],
            "taux_annuel_arbitraire": annual_rate,
            "avertissement": (
                "Taux d'accroissement arbitraire, non sourcé et indépendant de "
                "l'essence. Modèle de comparaison d'ordres de grandeur, pas de "
                "prévision. Pour une projection fondée, utiliser "
                "CalibratedGrowthBackend (accroissements IGN par essence)."
            ),
            "capped": False,
        }


class CalibratedGrowthBackend(GrowthBackend):
    """Backend v1 calibré — modèle IGN (confidence=medium).

    S'appuie sur `growth_models.py` (accroissements moyens annuels IGN
    par essence). Amélioration majeure par rapport à `LinearGrowthBackend` :
    les accroissements sont calibrés sur des données réelles publiées,
    pas arbitraires.
    """

    def confidence(self) -> ConfidenceLevel:
        return ConfidenceLevel.medium

    def sources(self) -> list[str]:
        return [
            "IGN — Inventaire Forestier National, résultats d'inventaire (2023), "
            "inventaire-forestier.ign.fr"
        ]

    def assumptions(self) -> list[str]:
        return [
            "AMA constant sur l'horizon (hypothèse stationnaire).",
            "Pas de mortalité ni perturbation modélisées en v1.",
            "Pas de compétition inter-essences (modèle mono-spécifique).",
            "Pas de couplage au scénario climatique — conditions stationnaires.",
            "AMA = moyenne France métropolitaine, à affiner par région forestière.",
            "Confiance 'medium' : modèle calibré sur données IGN réelles.",
        ]

    def simulate_growth(
        self,
        species: str,
        initial_state: dict[str, float],
        horizon_years: int,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = parameters or {}
        density_factor = float(params.get("density_factor", 1.0))
        initial_volume = initial_state.get("volume", 0.0)
        initial_circumference = initial_state.get("circumference", 0.0)

        result: dict[str, Any] = {"species": species}

        if initial_volume > 0 or "volume" in initial_state:
            try:
                vol_projection = project_volume(
                    species, initial_volume, horizon_years, density_factor=density_factor
                )
                result.update(
                    {
                        "final_volume": vol_projection["final_volume"],
                        "volume_increment": vol_projection["increment"],
                        "annual_volume_increment": vol_projection["annual_increment"],
                        "capped": vol_projection["capped"],
                        "volume_source": vol_projection["source"],
                    }
                )
            except GrowthModelError as exc:
                raise SimulationBackendError(str(exc)) from exc

        if initial_circumference > 0 or "circumference" in initial_state:
            try:
                circ_projection = project_circumference(
                    species, initial_circumference, horizon_years
                )
                result.update(
                    {
                        "final_circumference": circ_projection["final_circumference"],
                        "circumference_increment": circ_projection["increment"],
                        "circumference_source": circ_projection["source"],
                    }
                )
            except GrowthModelError as exc:
                raise SimulationBackendError(str(exc)) from exc

        if not result.get("final_volume") and not result.get("final_circumference"):
            raise SimulationBackendError(
                "initial_state doit contenir 'volume' ou 'circumference' > 0"
            )

        return result


class CapsisBackend(GrowthBackend):
    """Backend futur — wrapper CAPSIS via subprocess Java (non implémenté).

    CAPSIS (Computer-Aided Projection of Strategies in Silviculture) est
    une plateforme Java open source (INRAE/AMAP/CIRAD) fédérant des
    dizaines de modules de croissance calibrés sur des essences
    européennes (Dufour-Kowalski et al., 2012).

    Implémentation future :
    1. Installer CAPSIS (Java 11+ requis) sur le serveur de simulation ;
    2. Lancer un module CAPSIS via `subprocess.run(["java", "-jar",
       "capsis.jar", ...])` avec un fichier de configuration généré ;
    3. Parser la sortie CAPSIS (CSV/JSON) pour alimenter les
       `TimedProjection` du Simulation Engine.

    En v1, ce backend lève `NotImplementedError` pour signaler qu'il
    n'est pas encore disponible — l'architecture est en place pour
    permettre son branchement sans modifier le Simulation Engine.
    """

    def confidence(self) -> ConfidenceLevel:
        return ConfidenceLevel.high  # CAPSIS = modules calibrés INRAE

    def sources(self) -> list[str]:
        return [
            "Dufour-Kowalski S., Courbaud B., Dreyfus P., Meredieu C., "
            "de Coligny F. (2012), « Capsis: an open software framework "
            "and platform for forest growth modelling », Annals of Forest "
            "Science 69:221-233"
        ]

    def assumptions(self) -> list[str]:
        return [
            "Module CAPSIS calibré sur données INRAE (essence + région).",
            "Modèle individu-centré ou peuplement selon le module sélectionné.",
            "Nécessite installation Java 11+ et CAPSIS sur le serveur.",
            "Confiance 'high' : modules calibrés et validés scientifiquement.",
        ]

    def simulate_growth(
        self,
        species: str,
        initial_state: dict[str, float],
        horizon_years: int,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError(
            "CapsisBackend non implémenté en v1 — "
            "utiliser CalibratedGrowthBackend (modèle IGN) ou LinearGrowthBackend (v1). "
            "Voir SIMULATION_ENGINE.md §8 pour la feuille de route v2."
        )

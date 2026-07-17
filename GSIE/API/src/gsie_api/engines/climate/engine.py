"""Climate Engine — observations météorologiques réelles, sourcées et vérifiables.

Périmètre v1 (voir docstring schemas.py) : dernière observation SYNOP
réelle (Météo-France, data.gouv.fr, licence ouverte 2.0, aucune clé
requise) pour une station donnée. Pas de projection climatique
(DRIAS/RCP) — nécessitera l'API portail Météo-France (clé requise).

Conversions d'unités (vérifiées sur un échantillon réel, station 07510
Bordeaux-Mérignac, 2026-07-16T21:00Z : t=297.15K -> 24.0°C,
pmer=101690 Pa -> 1016.9 hPa) :
- Température : Kelvin -> Celsius (- 273.15)
- Pression : Pa -> hPa (/ 100)
- Humidité, vent, précipitations : déjà dans l'unité cible (%, °, m/s, mm)

Garantie : un champ vide dans le CSV SYNOP (paramètre non mesuré à
cette station) reste `None` dans le résultat, jamais remplacé par une
valeur par défaut (ADR-007).
"""

from datetime import datetime

from gsie_api.core.logging import get_logger
from gsie_api.engines.climate.schemas import ClimateQuery, ObservationClimatique
from gsie_api.engines.climate.synop_client import SynopClient, SynopClientError
from gsie_api.engines.evidence.schemas import SourceReference, SourceType

logger = get_logger("gsie_api.climate.engine")

# Constante physique exacte : le zéro Celsius vaut 273.15 K par définition
# de l'échelle Celsius adossée au kelvin — BIPM (2019), Système
# international d'unités, 9e édition, §2.3.1. Valeur définie, pas mesurée.
_KELVIN_TO_CELSIUS = 273.15

_SYNOP_SOURCE = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="Météo-France",
    reference=(
        "Données d'observation SYNOP (data.gouv.fr, licence ouverte 2.0) — "
        "meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/OBS/SYNOP/"
    ),
)


def _parse_float(raw: dict[str, str], key: str) -> float | None:
    """Parse un champ CSV optionnel — chaîne vide ou absente -> None (jamais 0.0 par défaut)."""
    value = raw.get(key, "").strip()
    if not value:
        return None
    return float(value)


class ClimateEngineError(Exception):
    """Erreur de base du Climate Engine."""


class ClimateEngine:
    """Moteur Climate — pas de persistance en v1 (observation ponctuelle, non versionnée)."""

    def __init__(self, synop_client: SynopClient | None = None) -> None:
        self._synop_client = synop_client or SynopClient()

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    async def query(self, request: ClimateQuery) -> ObservationClimatique | None:
        """Récupère la dernière observation réelle d'une station SYNOP.

        Returns:
            None si la station est introuvable dans les données de
            l'année courante — jamais une observation approximée
            (ADR-007).

        Raises:
            ClimateEngineError: si les données SYNOP sont indisponibles.
        """
        try:
            raw = await self._synop_client.get_latest_observation(request.station_id)
        except SynopClientError as exc:
            raise ClimateEngineError(str(exc)) from exc

        if raw is None:
            logger.info("climate_station_not_found", station_id=request.station_id)
            return None

        temperature_k = _parse_float(raw, "t")
        pression_pa = _parse_float(raw, "pmer")

        observation = ObservationClimatique(
            requete_id=request.requete_id,
            station_id=request.station_id,
            nom_station=raw["name"],
            latitude=float(raw["lat"]),
            longitude=float(raw["lon"]),
            date_observation=datetime.fromisoformat(raw["validity_time"].replace("Z", "+00:00")),
            temperature_c=temperature_k - _KELVIN_TO_CELSIUS if temperature_k is not None else None,
            humidite_pct=_parse_float(raw, "u"),
            pression_hpa=pression_pa / 100.0 if pression_pa is not None else None,
            vent_direction_deg=_parse_float(raw, "dd"),
            vent_vitesse_ms=_parse_float(raw, "ff"),
            precipitations_1h_mm=_parse_float(raw, "rr1"),
            source=_SYNOP_SOURCE,
        )

        logger.info(
            "climate_observation_retrieved",
            station_id=request.station_id,
            date_observation=observation.date_observation.isoformat(),
        )

        return observation

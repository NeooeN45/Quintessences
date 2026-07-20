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

import csv
import io
from datetime import datetime
from typing import Any
from uuid import uuid4

from gsie_api.core.logging import get_logger
from gsie_api.engines.climate.arome_client import AromeClient, AromeClientError
from gsie_api.engines.climate.arome_grib_decoder import (
    AromeGribDecodeError,
    extract_nearest_temperature_celsius,
)
from gsie_api.engines.climate.dpclim_client import DPClimClient, DPClimClientError
from gsie_api.engines.climate.meteofrance_client import MeteoFranceClient, MeteoFranceClientError
from gsie_api.engines.climate.paquet_observation_client import (
    PaquetObservationClient,
    PaquetObservationClientError,
)
from gsie_api.engines.climate.schemas import (
    AromeTemperatureQuery,
    AromeTemperatureResult,
    ClimateQuery,
    ClimatologieQuotidienneQuery,
    DangerFeuxDepartement,
    ObservationClimatique,
    ObservationClimatologiqueQuotidienne,
    ObservationHoraireDepartement,
    VigilanceBulletin,
    VigilanceDomaine,
    VigilancePhenomene,
)
from gsie_api.engines.climate.synop_client import SynopClient, SynopClientError
from gsie_api.engines.climate.vigilance_client import VigilanceClient, VigilanceClientError
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

_METEO_FORETS_SOURCE = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="Météo-France",
    reference=(
        "API Météo des forêts (portail-api.meteofrance.fr, "
        "DonneesPubliquesMeteoForets v1) — danger de feux de forêt J+1/J+2"
    ),
)

_VIGILANCE_SOURCE = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="Météo-France",
    reference=(
        "API Bulletin Vigilance (portail-api.meteofrance.fr, "
        "DonneesPubliquesVigilance v1) — carte de vigilance en cours"
    ),
)

def _arome_source(run_modele: str) -> SourceReference:
    """Construit la SourceReference AROME — le run utilisé varie par requête."""
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="Météo-France",
        reference=(
            "Modèle AROME France (portail-api.meteofrance.fr, API WCS "
            f"MF-NWP-HIGHRES-AROME-001-FRANCE-WCS) — run {run_modele}"
        ),
    )


_PAQUET_OBSERVATION_SOURCE = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="Météo-France",
    reference=(
        "API Package Observations (portail-api.meteofrance.fr, "
        "DonneesPubliquesPaquetObservation v2) — observations horaires 24h/département"
    ),
)

_DPCLIM_SOURCE = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="Météo-France",
    reference=(
        "API Données Climatologiques (portail-api.meteofrance.fr, "
        "DonneesPubliquesClimatologie v1, DPClim) — produit quotidien par station"
    ),
)


def _parse_float(raw: dict[str, str], key: str) -> float | None:
    """Parse un champ CSV optionnel — chaîne vide ou absente -> None (jamais 0.0 par défaut)."""
    value = raw.get(key, "").strip()
    if not value:
        return None
    return float(value)


def _parse_french_float(raw: dict[str, str], key: str) -> float | None:
    """Parse un nombre décimal DPClim (virgule française) — vide/absent -> None."""
    value = raw.get(key, "").strip()
    if not value:
        return None
    return float(value.replace(",", "."))


class ClimateEngineError(Exception):
    """Erreur de base du Climate Engine."""


class ClimateEngine:
    """Moteur Climate — pas de persistance en v1 (observation ponctuelle, non versionnée)."""

    def __init__(
        self,
        synop_client: SynopClient | None = None,
        meteofrance_client: MeteoFranceClient | None = None,
        dpclim_client: DPClimClient | None = None,
        vigilance_client: VigilanceClient | None = None,
        paquet_observation_client: PaquetObservationClient | None = None,
        arome_client: AromeClient | None = None,
    ) -> None:
        self._synop_client = synop_client or SynopClient()
        self._meteofrance_client = meteofrance_client or MeteoFranceClient()
        self._dpclim_client = dpclim_client or DPClimClient()
        self._vigilance_client = vigilance_client or VigilanceClient()
        self._paquet_observation_client = (
            paquet_observation_client or PaquetObservationClient()
        )
        self._arome_client = arome_client or AromeClient()

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

    async def get_danger_feux(self) -> list[DangerFeuxDepartement]:
        """Récupère le niveau de danger de feux de forêt réel, tous départements.

        Raises:
            ClimateEngineError: si l'API Météo des forêts est indisponible
                ou la clé absente — jamais un niveau approximé (ADR-007).
        """
        try:
            rows = await self._meteofrance_client.get_danger_feux_departements()
        except MeteoFranceClientError as exc:
            raise ClimateEngineError(str(exc)) from exc

        resultats = [
            DangerFeuxDepartement(
                dep_code=row["dep_code"],
                dep_nom=row["dep_nom"],
                niveau_j1=int(row["niveau_j1"]),
                niveau_j2=int(row["niveau_j2"]),
                reference_time=datetime.fromisoformat(
                    row["reference_time"].replace("Z", "+00:00")
                ),
                source=_METEO_FORETS_SOURCE,
            )
            for row in rows
        ]

        logger.info("climate_danger_feux_retrieved", nb_departements=len(resultats))

        return resultats

    async def list_stations_climatologie(self, id_departement: str) -> list[dict[str, Any]]:
        """Liste réelle des stations DPClim d'un département (id_station 8 chiffres).

        Raises:
            ClimateEngineError: si l'API DPClim est indisponible ou la clé absente.
        """
        try:
            return await self._dpclim_client.list_stations(id_departement)
        except DPClimClientError as exc:
            raise ClimateEngineError(str(exc)) from exc

    async def get_climatologie_quotidienne(
        self, request: ClimatologieQuotidienneQuery
    ) -> list[ObservationClimatologiqueQuotidienne]:
        """Récupère les données climatologiques quotidiennes réelles d'une station DPClim.

        Le jeu de colonnes CSV varie selon la station (voir schemas.py) —
        chaque ligne conserve toutes ses colonnes brutes dans
        `valeurs_brutes`, en plus des champs pratiques typés (RR/TN/TX/TM).

        Raises:
            ClimateEngineError: clé absente, échec réseau, ou commande
                jamais prête (station sans donnée sur la période, ou
                délai dépassé) — jamais une donnée approximée (ADR-007).
        """
        try:
            csv_text = await self._dpclim_client.get_donnees_quotidiennes(
                request.id_station,
                request.date_deb_periode.strftime("%Y-%m-%dT%H:%M:%SZ"),
                request.date_fin_periode.strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
        except DPClimClientError as exc:
            raise ClimateEngineError(str(exc)) from exc

        reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")
        resultats = [
            ObservationClimatologiqueQuotidienne(
                requete_id=request.requete_id,
                id_station=row["POSTE"],
                date=datetime.strptime(row["DATE"], "%Y%m%d").date(),
                rr_mm=_parse_french_float(row, "RR"),
                tn_c=_parse_french_float(row, "TN"),
                tx_c=_parse_french_float(row, "TX"),
                tm_c=_parse_french_float(row, "TM"),
                valeurs_brutes={k: (v if v else None) for k, v in row.items()},
                source=_DPCLIM_SOURCE,
            )
            for row in reader
        ]

        logger.info(
            "climate_climatologie_quotidienne_retrieved",
            id_station=request.id_station,
            nb_lignes=len(resultats),
        )

        return resultats

    async def get_vigilance(self) -> list[VigilanceBulletin]:
        """Récupère la carte de vigilance réelle en cours (échéances J et J+1).

        Raises:
            ClimateEngineError: si l'API Vigilance est indisponible ou
                la clé absente — jamais un niveau approximé (ADR-007).
        """
        try:
            data = await self._vigilance_client.get_carte_vigilance()
        except VigilanceClientError as exc:
            raise ClimateEngineError(str(exc)) from exc

        update_time = datetime.fromisoformat(
            data["product"]["update_time"].replace("Z", "+00:00")
        )

        bulletins = [
            VigilanceBulletin(
                requete_id=uuid4(),
                echeance=period["echeance"],
                update_time=update_time,
                domaines=[
                    VigilanceDomaine(
                        domain_id=domaine["domain_id"],
                        max_color_id=domaine["max_color_id"],
                        phenomenes=[
                            VigilancePhenomene(
                                phenomenon_id=item["phenomenon_id"],
                                color_id=item["phenomenon_max_color_id"],
                            )
                            for item in domaine.get("phenomenon_items", [])
                        ],
                    )
                    for domaine in period.get("timelaps", {}).get("domain_ids", [])
                ],
                source=_VIGILANCE_SOURCE,
            )
            for period in data["product"]["periods"]
        ]

        logger.info("climate_vigilance_retrieved", nb_echeances=len(bulletins))

        return bulletins

    async def get_observations_horaires(
        self, id_departement: str
    ) -> list[ObservationHoraireDepartement]:
        """Récupère les observations horaires réelles des 24h, toutes stations d'un département.

        Raises:
            ClimateEngineError: si l'API Package Observations est
                indisponible ou la clé absente — jamais une observation
                approximée (ADR-007).
        """
        try:
            rows = await self._paquet_observation_client.get_observations_horaires(
                id_departement
            )
        except PaquetObservationClientError as exc:
            raise ClimateEngineError(str(exc)) from exc

        resultats = []
        for row in rows:
            temperature_k = _parse_float(row, "t")
            pression_pa = _parse_float(row, "pmer")
            resultats.append(
                ObservationHoraireDepartement(
                    geo_id_insee=row["geo_id_insee"],
                    latitude=float(row["lat"]),
                    longitude=float(row["lon"]),
                    date_observation=datetime.fromisoformat(
                        row["validity_time"].replace("Z", "+00:00")
                    ),
                    temperature_c=(
                        temperature_k - _KELVIN_TO_CELSIUS
                        if temperature_k is not None
                        else None
                    ),
                    humidite_pct=_parse_float(row, "u"),
                    pression_hpa=pression_pa / 100.0 if pression_pa is not None else None,
                    vent_direction_deg=_parse_float(row, "dd"),
                    vent_vitesse_ms=_parse_float(row, "ff"),
                    precipitations_1h_mm=_parse_float(row, "rr1"),
                    source=_PAQUET_OBSERVATION_SOURCE,
                )
            )

        logger.info(
            "climate_observations_horaires_retrieved",
            id_departement=id_departement,
            nb_observations=len(resultats),
        )

        return resultats

    async def get_temperature_arome(
        self, request: AromeTemperatureQuery
    ) -> AromeTemperatureResult:
        """Récupère la température 2 m réelle du modèle AROME (décodage GRIB2 réel).

        Utilise le run de modèle le plus récent réellement publié pour
        ce paramètre — l'échéance demandée doit être couverte par ce
        run (typiquement les prochaines ~17h), sinon l'API Météo-France
        rejette la requête explicitement (voir AromeClientError).

        Raises:
            ClimateEngineError: clé absente, échec réseau, échéance
                hors du run disponible, ou GRIB2 non décodable —
                jamais une température approximée (ADR-007).
        """
        try:
            run_modele = await self._arome_client.get_latest_temperature_2m_run()
            grib_bytes = await self._arome_client.get_temperature_2m_grib(
                run_modele, request.latitude, request.longitude, request.echeance
            )
        except AromeClientError as exc:
            raise ClimateEngineError(str(exc)) from exc

        try:
            temperature_c = extract_nearest_temperature_celsius(
                grib_bytes, request.latitude, request.longitude
            )
        except AromeGribDecodeError as exc:
            raise ClimateEngineError(str(exc)) from exc

        logger.info(
            "climate_arome_temperature_retrieved",
            run_modele=run_modele,
            latitude=request.latitude,
            longitude=request.longitude,
        )

        return AromeTemperatureResult(
            requete_id=request.requete_id,
            latitude=request.latitude,
            longitude=request.longitude,
            echeance=request.echeance,
            temperature_c=temperature_c,
            run_modele=run_modele,
            source=_arome_source(run_modele),
        )

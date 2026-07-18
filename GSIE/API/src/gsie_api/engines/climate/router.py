"""Engine Climate — observations météorologiques réelles, sourcées et vérifiables.

Périmètre v1 : dernière observation SYNOP (Météo-France, aucune clé
requise) — voir docstring engine.py. Pas de projection climatique
(DRIAS/RCP), qui nécessitera la clé du portail API Météo-France.

Endpoints :
- GET  /climate/status   — statut du moteur
- GET  /climate/version  — version et backend
- POST /climate/query     — dernière observation réelle d'une station
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from gsie_api.core.auth import get_current_user
from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError
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
)
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/climate", tags=["climate"])

_climate_limiter = Limiter(key_func=get_remote_address)


@router.get("/status", response_model=EngineStatusResponse)
async def climate_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Climate."""
    return EngineStatusResponse(
        engine="climate",
        status="active",
        planned_week=7,
        language="python",
    )


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur Climate",
)
async def climate_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=ClimateEngine.version(),
        backend="synop",
    )


@router.post(
    "/query",
    response_model=ObservationClimatique | None,
    status_code=status.HTTP_200_OK,
    summary="Récupérer la dernière observation réelle d'une station SYNOP",
    description=(
        "Interroge les données d'observation SYNOP Météo-France (aucune "
        "clé requise) pour la dernière observation d'une station donnée. "
        "Retourne null si la station est introuvable — jamais une "
        "observation approximée (ADR-007)."
    ),
)
@_climate_limiter.limit("20/minute")
async def climate_query(
    request_body: ClimateQuery,
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> ObservationClimatique | None:
    """Récupère la dernière observation d'une station SYNOP.

    Raises:
        502: Si les données SYNOP sont indisponibles.
    """
    try:
        return await ClimateEngine().query(request_body)
    except ClimateEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/danger-feux",
    response_model=list[DangerFeuxDepartement],
    status_code=status.HTTP_200_OK,
    summary="Niveau de danger de feux de forêt réel, tous départements (J+1/J+2)",
    description=(
        "Interroge l'API Météo des forêts (portail-api.meteofrance.fr, "
        "clé de compte requise) pour le niveau de danger de feux de forêt "
        "réel de chaque département français, aujourd'hui+1 et +2."
    ),
)
@_climate_limiter.limit("20/minute")
async def climate_danger_feux(
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> list[DangerFeuxDepartement]:
    """Récupère le niveau de danger de feux de forêt réel, tous départements.

    Raises:
        502: Si l'API Météo des forêts est indisponible ou la clé absente.
    """
    try:
        return await ClimateEngine().get_danger_feux()
    except ClimateEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/climatologie-stations",
    response_model=list[dict],
    status_code=status.HTTP_200_OK,
    summary="Liste réelle des stations DPClim d'un département",
    description=(
        "Interroge l'API Données Climatologiques (DPClim) pour la liste "
        "des stations d'un département — nécessaire pour obtenir "
        "l'id_station à 8 chiffres requis par /climatologie-quotidienne."
    ),
)
@_climate_limiter.limit("20/minute")
async def climate_climatologie_stations(
    request: Request,
    id_departement: str,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> list[dict]:
    """Récupère la liste réelle des stations DPClim d'un département.

    Raises:
        502: Si l'API DPClim est indisponible ou la clé absente.
    """
    try:
        return await ClimateEngine().list_stations_climatologie(id_departement)
    except ClimateEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/climatologie-quotidienne",
    response_model=list[ObservationClimatologiqueQuotidienne],
    status_code=status.HTTP_200_OK,
    summary="Données climatologiques quotidiennes réelles d'une station DPClim",
    description=(
        "Interroge l'API Données Climatologiques (DPClim, clé de compte "
        "requise) pour une station et une période données. Flux "
        "asynchrone côté Météo-France (commande + polling) — la réponse "
        "peut prendre plusieurs secondes. Retourne une liste vide si la "
        "station n'a aucune donnée sur la période — jamais une valeur "
        "approximée (ADR-007)."
    ),
)
@_climate_limiter.limit("5/minute")
async def climate_climatologie_quotidienne(
    request_body: ClimatologieQuotidienneQuery,
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> list[ObservationClimatologiqueQuotidienne]:
    """Récupère les données climatologiques quotidiennes réelles d'une station.

    Raises:
        502: Si l'API DPClim est indisponible, la clé absente, ou la
            commande n'est jamais prête (station sans donnée sur la
            période, ou délai de traitement dépassé).
    """
    try:
        return await ClimateEngine().get_climatologie_quotidienne(request_body)
    except ClimateEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/vigilance",
    response_model=list[VigilanceBulletin],
    status_code=status.HTTP_200_OK,
    summary="Carte de vigilance réelle en cours (échéances J et J+1)",
    description=(
        "Interroge l'API Bulletin Vigilance (portail-api.meteofrance.fr, "
        "clé de compte requise) pour le niveau de vigilance réel de "
        "chaque domaine (département/zone), aujourd'hui et J+1."
    ),
)
@_climate_limiter.limit("20/minute")
async def climate_vigilance(
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> list[VigilanceBulletin]:
    """Récupère la carte de vigilance réelle en cours.

    Raises:
        502: Si l'API Vigilance est indisponible ou la clé absente.
    """
    try:
        return await ClimateEngine().get_vigilance()
    except ClimateEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/observations-horaires",
    response_model=list[ObservationHoraireDepartement],
    status_code=status.HTTP_200_OK,
    summary="Observations horaires réelles des 24h, toutes stations d'un département",
    description=(
        "Interroge l'API Package Observations (portail-api.meteofrance.fr, "
        "clé de compte requise) pour les observations horaires réelles "
        "des 24 dernières heures, toutes stations d'un département."
    ),
)
@_climate_limiter.limit("20/minute")
async def climate_observations_horaires(
    request: Request,
    id_departement: str,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> list[ObservationHoraireDepartement]:
    """Récupère les observations horaires réelles des 24h d'un département.

    Raises:
        502: Si l'API Package Observations est indisponible ou la clé absente.
    """
    try:
        return await ClimateEngine().get_observations_horaires(id_departement)
    except ClimateEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/arome-temperature",
    response_model=AromeTemperatureResult,
    status_code=status.HTTP_200_OK,
    summary="Température 2 m réelle du modèle AROME (décodage GRIB2)",
    description=(
        "Interroge l'API WCS du modèle AROME (portail-api.meteofrance.fr, "
        "clé de compte requise) pour la température à 2 m sur le run de "
        "modèle le plus récent. L'échéance demandée doit être couverte "
        "par ce run (typiquement les prochaines ~17h)."
    ),
)
@_climate_limiter.limit("10/minute")
async def climate_arome_temperature(
    request_body: AromeTemperatureQuery,
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> AromeTemperatureResult:
    """Récupère la température 2 m réelle du modèle AROME.

    Raises:
        502: Si l'API AROME est indisponible, la clé absente, l'échéance
            hors du run disponible, ou le GRIB2 non décodable.
    """
    try:
        return await ClimateEngine().get_temperature_arome(request_body)
    except ClimateEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

"""Engine GIS — données géospatiales de référence, sourcées et vérifiables.

Responsabilité : fournir des données géospatiales réelles (parcelles
cadastrales, altitude) avec traçabilité de la source (GIS_ENGINE.md).
Périmètre v1 : cadastre (API Carto IGN) et altitude (API de calcul
altimétrique IGN) — voir docstring engine.py pour le détail.

Endpoints :
- GET  /gis/status              — statut du moteur
- GET  /gis/version              — version et backend
- POST /gis/cadastre/parcelle    — récupère et persiste une parcelle cadastrale
- POST /gis/altitude              — récupère l'altitude d'un point
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.rbac import EngineReadUser, EngineWriteUser
from gsie_api.engines.gis.engine import GISEngine, GISEngineError
from gsie_api.engines.gis.ign_client import IGNClientError
from gsie_api.engines.gis.schemas import (
    AltitudeRequest,
    GeoData,
    ParcelleCadastraleRequest,
    StationCharacteristics,
)
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/gis", tags=["gis"])

_gis_limiter = Limiter(key_func=get_remote_address)

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/status", response_model=EngineStatusResponse)
async def gis_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur GIS."""
    return EngineStatusResponse(
        engine="gis",
        status="active",
        planned_week=5,
        language="python",
    )


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur GIS",
)
async def gis_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=GISEngine.version(),
        backend="postgis",
    )


@router.post(
    "/cadastre/parcelle",
    response_model=GeoData | None,
    status_code=status.HTTP_200_OK,
    summary="Récupérer une parcelle cadastrale réelle (API Carto IGN)",
    description=(
        "Interroge l'API Carto — module Cadastre de l'IGN pour une parcelle "
        "unique (code INSEE + section + numéro), persiste sa géométrie "
        "(Lambert-93) comme resource `place`, et retourne les données "
        "sourcées. Retourne null si aucune parcelle ne correspond — jamais "
        "de géométrie approximée (ADR-007)."
    ),
)
@_gis_limiter.limit("30/minute")
async def gis_cadastre_parcelle(
    request_body: ParcelleCadastraleRequest,
    request: Request,
    session: DbSession,
    _user: EngineWriteUser,
) -> GeoData | None:
    """Récupère et persiste une parcelle cadastrale.

    Raises:
        502: Si l'API Carto IGN est indisponible.
    """
    try:
        return await GISEngine(session).get_parcelle_cadastre(request_body)
    except IGNClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/altitude",
    response_model=StationCharacteristics,
    status_code=status.HTTP_200_OK,
    summary="Récupérer l'altitude réelle d'un point (API IGN)",
    description=(
        "Interroge l'API de calcul altimétrique de l'IGN (RGE ALTI) pour "
        "un point WGS 84. Aucune valeur par défaut en cas d'échec (ADR-007)."
    ),
)
@_gis_limiter.limit("60/minute")
async def gis_altitude(
    request_body: AltitudeRequest,
    request: Request,
    session: DbSession,
    _user: EngineReadUser,
) -> StationCharacteristics:
    """Récupère l'altitude d'un point.

    Raises:
        502: Si l'API altimétrique IGN est indisponible.
    """
    try:
        return await GISEngine(session).get_altitude(request_body)
    except GISEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

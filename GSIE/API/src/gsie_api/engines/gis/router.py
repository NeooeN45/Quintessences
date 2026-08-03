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

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.limiter import limiter as _limiter
from gsie_api.core.rbac import EngineReadUser, EngineWriteUser
from gsie_api.engines.gis.engine import GISEngine, GISEngineError
from gsie_api.engines.gis.ign_client import IGNClientError
from gsie_api.engines.gis.schemas import (
    AltitudeRequest,
    GeoData,
    ListeDossiersResponse,
    ListeFichiersResponse,
    ListeRessourcesResponse,
    ParcelleCadastraleRequest,
    StationCharacteristics,
)
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/gis", tags=["gis"])

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
        "de géométrie approximée (ADR-009)."
    ),
)
@_limiter.limit("30/minute")
async def gis_cadastre_parcelle(
    request_body: ParcelleCadastraleRequest,
    request: Request,
    response: Response,
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
        "un point WGS 84. Aucune valeur par défaut en cas d'échec (ADR-009)."
    ),
)
@_limiter.limit("60/minute")
async def gis_altitude(
    request_body: AltitudeRequest,
    request: Request,
    response: Response,
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


# --- API de téléchargement Géoplateforme IGN ---
# GetCapabilities / GetResource / GetSubResource / Download


@router.get(
    "/telechargement/ressources",
    response_model=ListeRessourcesResponse,
    summary="Lister les ressources téléchargeables (GetCapabilities IGN)",
    description=(
        "Interroge l'API de téléchargement de la Géoplateforme IGN pour "
        "lister les produits disponibles (BD Forêt, BD TOPO Express, "
        "ADMIN-EXPRESS-COG, LiDAR HD, etc.). Résultats paginés."
    ),
)
@_limiter.limit("10/minute")
async def gis_telechargement_ressources(
    request: Request,
    response: Response,
    session: DbSession,
    _user: EngineReadUser,
    page: int = 1,
    limit: int = 50,
    zone: str | None = None,
    format: str | None = None,
) -> ListeRessourcesResponse:
    """Liste les ressources téléchargeables (GetCapabilities).

    Raises:
        502: Si l'API de téléchargement IGN est indisponible.
    """
    try:
        return await GISEngine(session).lister_ressources_telechargement(
            page=page, limit=limit, zone=zone, format=format
        )
    except GISEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/telechargement/ressources/{resource_name}",
    response_model=ListeDossiersResponse,
    summary="Lister les dossiers d'une ressource (GetResource IGN)",
    description=(
        "Liste les jeux de données d'un produit IGN (ex. ADMIN-EXPRESS-COG). "
        "Chaque dossier correspond à une édition millésimée."
    ),
)
@_limiter.limit("10/minute")
async def gis_telechargement_dossiers(
    resource_name: str,
    request: Request,
    response: Response,
    session: DbSession,
    _user: EngineReadUser,
    page: int = 1,
    limit: int = 50,
    zone: str | None = None,
    format: str | None = None,
) -> ListeDossiersResponse:
    """Liste les dossiers d'une ressource (GetResource).

    Raises:
        502: Si l'API de téléchargement IGN est indisponible.
    """
    try:
        return await GISEngine(session).lister_dossiers_telechargement(
            resource_name, page=page, limit=limit, zone=zone, format=format
        )
    except GISEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/telechargement/ressources/{resource_name}/{subresource_name}",
    response_model=ListeFichiersResponse,
    summary="Lister les fichiers d'un dossier (GetSubResource IGN)",
    description="Liste les fichiers téléchargeables d'un dossier de ressource IGN.",
)
@_limiter.limit("10/minute")
async def gis_telechargement_fichiers(
    resource_name: str,
    subresource_name: str,
    request: Request,
    response: Response,
    session: DbSession,
    _user: EngineReadUser,
    page: int = 1,
    limit: int = 50,
) -> ListeFichiersResponse:
    """Liste les fichiers d'un dossier (GetSubResource).

    Raises:
        502: Si l'API de téléchargement IGN est indisponible.
    """
    try:
        return await GISEngine(session).lister_fichiers_telechargement(
            resource_name, subresource_name, page=page, limit=limit
        )
    except GISEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/telechargement/telecharger/{resource_name}/{subresource_name}/{file_name:path}",
    summary="Télécharger un fichier (Download IGN)",
    description=(
        "Télécharge un fichier binaire depuis l'API de téléchargement "
        "Géoplateforme IGN. Retourne le contenu binaire (ex. .7z, .shp)."
    ),
)
@_limiter.limit("5/minute")
async def gis_telechargement_download(
    resource_name: str,
    subresource_name: str,
    file_name: str,
    request: Request,
    response: Response,
    session: DbSession,
    _user: EngineWriteUser,
) -> Response:
    """Télécharge un fichier binaire (Download).

    Raises:
        502: Si l'API de téléchargement IGN est indisponible.
    """
    try:
        content = await GISEngine(session).telecharger_fichier(
            resource_name, subresource_name, file_name
        )
    except GISEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return Response(content=content, media_type="application/octet-stream")

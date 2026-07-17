"""Engine Pedology — propriétés de sol, sourcées et vérifiables.

Responsabilité : fournir les caractéristiques pédologiques (pH,
texture) pour un point donné, sans jamais inventer de seuil
(PEDOLOGY_ENGINE.md). Périmètre v1 : SoilGrids (ISRIC) — voir
docstring engine.py.

Endpoints :
- GET  /pedology/status   — statut du moteur
- GET  /pedology/version  — version et backend
- POST /pedology/query     — propriétés de sol réelles pour un point
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from gsie_api.core.auth import get_current_user
from gsie_api.engines.pedology.engine import PedologyEngine, PedologyEngineError
from gsie_api.engines.pedology.schemas import PedologyData, PedologyQuery
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/pedology", tags=["pedology"])

_pedology_limiter = Limiter(key_func=get_remote_address)


@router.get("/status", response_model=EngineStatusResponse)
async def pedology_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Pedology."""
    return EngineStatusResponse(
        engine="pedology",
        status="active",
        planned_week=8,
        language="python",
    )


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur Pedology",
)
async def pedology_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=PedologyEngine.version(),
        backend="soilgrids",
    )


@router.post(
    "/query",
    response_model=PedologyData,
    status_code=status.HTTP_200_OK,
    summary="Récupérer les propriétés de sol réelles d'un point (SoilGrids)",
    description=(
        "Interroge SoilGrids (ISRIC) pour le pH et la texture (argile, "
        "sable, limon) à un point et une profondeur donnés. Les propriétés "
        "sans donnée disponible sont omises, jamais approximées (ADR-007)."
    ),
)
@_pedology_limiter.limit("30/minute")
async def pedology_query(
    request_body: PedologyQuery,
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> PedologyData:
    """Récupère les propriétés de sol d'un point.

    Raises:
        502: Si l'API SoilGrids est indisponible.
    """
    try:
        return await PedologyEngine().query(request_body)
    except PedologyEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

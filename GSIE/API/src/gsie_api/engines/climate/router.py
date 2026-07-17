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
from gsie_api.engines.climate.schemas import ClimateQuery, ObservationClimatique
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

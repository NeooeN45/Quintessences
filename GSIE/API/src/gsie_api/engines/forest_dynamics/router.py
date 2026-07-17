"""Engine Forest Dynamics — dendrométrie géométrique, sourcée et vérifiable.

Responsabilité : calculer les caractéristiques dendrométriques d'un
peuplement à partir de son état mesuré (FOREST_DYNAMICS_ENGINE.md).
Périmètre v1 : surface terrière uniquement (identité géométrique) —
pas de projection de croissance (voir docstring engine.py, ADR-007).

Endpoints :
- GET  /forest-dynamics/status   — statut du moteur
- GET  /forest-dynamics/version  — version et backend
- POST /forest-dynamics/dendrometrics — calcule la surface terrière
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from gsie_api.core.auth import get_current_user
from gsie_api.engines.forest_dynamics.engine import ForestDynamicsEngine
from gsie_api.engines.forest_dynamics.schemas import DendrometricRequest, DendrometricResult
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/forest-dynamics", tags=["forest-dynamics"])

_forest_dynamics_limiter = Limiter(key_func=get_remote_address)


@router.get("/status", response_model=EngineStatusResponse)
async def forest_dynamics_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Forest Dynamics."""
    return EngineStatusResponse(
        engine="forest_dynamics",
        status="active",
        planned_week=10,
        language="python",
    )


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur Forest Dynamics",
)
async def forest_dynamics_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=ForestDynamicsEngine.version(),
        backend="geometrie",
    )


@router.post(
    "/dendrometrics",
    response_model=DendrometricResult,
    status_code=status.HTTP_200_OK,
    summary="Calculer la surface terrière d'un peuplement",
    description=(
        "Calcule la surface terrière (G = π/4 × D² × N) à partir d'un état "
        "de peuplement mesuré. Aucune projection de croissance ni volume "
        "approché en v1 — ces calculs exigent des coefficients empiriques "
        "sourcés (modèle ONF-FFN/CAPSIS ou calibration IFN) non encore "
        "disponibles de façon vérifiée (ADR-007)."
    ),
)
@_forest_dynamics_limiter.limit("60/minute")
async def forest_dynamics_dendrometrics(
    request_body: DendrometricRequest,
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> DendrometricResult:
    """Calcule les caractéristiques dendrométriques géométriques d'un peuplement."""
    return ForestDynamicsEngine().compute_dendrometrics(request_body)

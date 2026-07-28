"""Engine Simulation — simulation de scénarios d'évolution et d'intervention.

Responsabilité : simuler des scénarios d'évolution et d'intervention à
partir de l'état courant du système (forêt, feu, climat) pour projeter
les conséquences des décisions avant qu'elles ne soient prises
(SIMULATION_ENGINE.md §1). La simulation ne décide pas — elle projette,
le forestier/COS choisit (GSIE-CON-001).

Endpoints :
- GET  /simulation/status   — statut du moteur
- GET  /simulation/version   — version et backend
- POST /simulation/run       — simule un scénario d'intervention
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.limiter import limiter as _limiter
from gsie_api.core.rbac import EngineWriteUser
from gsie_api.engines.simulation.engine import SimulationEngine, SimulationEngineError
from gsie_api.engines.simulation.schemas import ScenarioSimulation, SimulationResult
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/simulation", tags=["simulation"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/status", response_model=EngineStatusResponse)
async def simulation_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Simulation."""
    return EngineStatusResponse(
        engine="simulation",
        status="active",
        planned_week=15,
        language="python",
    )


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur Simulation",
)
async def simulation_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=SimulationEngine.version(),
        backend="python",
    )


@router.post(
    "/run",
    response_model=SimulationResult,
    status_code=status.HTTP_200_OK,
    summary="Simuler un scénario d'intervention",
    description=(
        "Projette les conséquences d'une intervention sur un horizon donné. "
        "Les projections sont explications (hypothèses explicites, GSIE-CON-004), "
        "sourcées (GSIE-CON-005) et comparatives (alternatives, GSIE-CON-001). "
        "La simulation ne décide pas — elle projette, le forestier/COS choisit."
    ),
)
@_limiter.limit("10/minute")
async def simulation_run(
    request_body: ScenarioSimulation,
    request: Request,
    response: Response,
    session: DbSession,
    _user: EngineWriteUser,
) -> SimulationResult:
    """Simule un scénario d'intervention.

    Raises:
        400: Si l'horizon ou l'intervention est invalide.
    """
    try:
        return await SimulationEngine().simulate(request_body)
    except SimulationEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

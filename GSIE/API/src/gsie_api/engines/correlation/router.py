"""Engine Correlation — détection et quantification de corrélations statistiques.

Responsabilité : croiser des variables issues de sources hétérogènes
pour produire des corrélations sourcées et statistiquement justifiées,
consommées par Reasoning/Diagnostic/Forest Dynamics/Learning
(CORRELATION_ENGINE.md §3). Ne produit aucune recommandation.

Endpoints :
- GET  /correlation/status   — statut du moteur
- GET  /correlation/version  — version et backend
- POST /correlation/compute  — calcule et persiste une corrélation
- GET  /correlation/stats    — statistiques des corrélations persistées
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.auth import get_current_user
from gsie_api.engines.correlation.engine import CorrelationEngine, CorrelationEngineError
from gsie_api.engines.correlation.schemas import CorrelationComputeRequest, CorrelationResult
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/correlation", tags=["correlation"])

_compute_limiter = Limiter(key_func=get_remote_address)

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/status", response_model=EngineStatusResponse)
async def correlation_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Correlation."""
    return EngineStatusResponse(
        engine="correlation",
        status="active",
        planned_week=9,
        language="python",
    )


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur Correlation",
)
async def correlation_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=CorrelationEngine.version(),
        backend="postgresql",
    )


@router.post(
    "/compute",
    response_model=CorrelationResult,
    status_code=status.HTTP_201_CREATED,
    summary="Calculer une corrélation entre deux variables",
    description=(
        "Calcule le coefficient de corrélation (pearson/spearman/kendall), sa "
        "p-valeur et sa force, entre deux variables fournies avec leurs valeurs "
        "observées appariées. Persiste le résultat comme ressource « correlation » "
        "du graphe v6.2 (CON-002 — toute corrélation est sourcée et justifiée)."
    ),
)
@_compute_limiter.limit("30/minute")
async def correlation_compute(
    request_body: CorrelationComputeRequest,
    request: Request,
    session: DbSession,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> CorrelationResult:
    """Calcule et persiste une corrélation.

    Raises:
        400: Si la méthode demandée n'est pas calculable par ce moteur.
    """
    try:
        return await CorrelationEngine(session).compute(request_body)
    except CorrelationEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/stats",
    summary="Statistiques des corrélations persistées",
)
async def correlation_stats(
    request: Request,
    session: DbSession,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, int]:
    """Retourne le nombre de corrélations persistées, par méthode."""
    return await CorrelationEngine(session).stats()

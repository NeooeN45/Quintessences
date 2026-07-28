"""Engine Learning — amélioration continue des modèles et calibrations.

Responsabilité : améliorer les modèles et calibrations de GSIE à partir
des données terrain validées et des retours d'expérience du forestier,
en restant subordonné aux règles expertes (LEARNING_ENGINE.md §1).
L'IA assiste, elle ne décide pas (GSIE-CON-001) : toute proposition
doit être validée par le Knowledge Engine.

Endpoints :
- GET  /learning/status   — statut du moteur
- GET  /learning/version   — version et backend
- POST /learning/process   — traite un signal d'apprentissage
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.limiter import limiter as _limiter
from gsie_api.core.rbac import EngineWriteUser
from gsie_api.engines.learning.engine import LearningEngine, LearningEngineError
from gsie_api.engines.learning.schemas import LearningOutput, LearningSignal
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/learning", tags=["learning"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/status", response_model=EngineStatusResponse)
async def learning_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Learning."""
    return EngineStatusResponse(
        engine="learning",
        status="active",
        planned_week=14,
        language="python",
    )


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur Learning",
)
async def learning_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=LearningEngine.version(),
        backend="python",
    )


@router.post(
    "/process",
    response_model=LearningOutput,
    status_code=status.HTTP_200_OK,
    summary="Traiter un signal d'apprentissage",
    description=(
        "Traite un signal (retour forestier, pattern émergent, sortie bloquée, "
        "observation terrain) et retourne une proposition d'apprentissage si le "
        "signal déclenche une révision. Les propositions ne sont jamais "
        "appliquées automatiquement — elles doivent être validées par le "
        "Knowledge Engine (GSIE-CON-001, LEARNING_ENGINE.md §6)."
    ),
)
@_limiter.limit("30/minute")
async def learning_process(
    request_body: LearningSignal,
    request: Request,
    response: Response,
    session: DbSession,
    _user: EngineWriteUser,
) -> LearningOutput:
    """Traite un signal d'apprentissage.

    Raises:
        400: Si le type de signal n'est pas géré en v1 ou si le contenu est invalide.
        204: Si le signal est accumulé sans déclencher de proposition (retourné
            comme 200 avec corps `null` — voir schéma).
    """
    try:
        output = await LearningEngine().process(request_body)
    except LearningEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if output is None:
        # Signal accumulé sans proposition — retourner un 204 No Content
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Signal accumulé sans déclencher de proposition.",
        )
    return output

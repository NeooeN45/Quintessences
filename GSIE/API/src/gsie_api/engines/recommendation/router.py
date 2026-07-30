"""Engine Recommendation — propositions sylvicoles justifiées et contournables.

Responsabilité : produire des recommandations sylvicoles contournables
à partir des diagnostics et des simulations, en proposant
systématiquement des alternatives justifiées et en documentant les
refus du forestier (RECOMMENDATION_ENGINE.md §1). GSIE recommande, le
forestier décide (GSIE-CON-001).

Endpoints :
- GET  /recommendation/status    — statut du moteur
- GET  /recommendation/version    — version et backend
- POST /recommendation/recommend  — génère un ensemble de recommandations
- POST /recommendation/decision   — enregistre la décision du forestier
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.limiter import limiter as _limiter
from gsie_api.core.rbac import EngineWriteUser
from gsie_api.engines.recommendation.engine import (
    RecommendationEngine,
    RecommendationEngineError,
)
from gsie_api.engines.recommendation.schemas import (
    ForestierDecision,
    RecommendationRequest,
    RecommendationSet,
)
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.resources.router import _extract_author_id
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/recommendation", tags=["recommendation"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/status", response_model=EngineStatusResponse)
async def recommendation_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Recommendation."""
    return EngineStatusResponse(
        engine="recommendation",
        status="active",
        planned_week=12,
        language="python",
    )


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur Recommendation",
)
async def recommendation_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=RecommendationEngine.version(),
        backend="python",
    )


@router.post(
    "/recommend",
    response_model=RecommendationSet,
    status_code=status.HTTP_200_OK,
    summary="Générer un ensemble de recommandations sylvicoles",
    description=(
        "Produit des recommandations contournables à partir d'un diagnostic. "
        "Plusieurs alternatives sont systématiquement proposées (principe fondateur). "
        "Chaque recommandation est justifiée par le diagnostic, les connaissances "
        "et les règles sous-jacentes (GSIE-CON-004). Aucune recommandation n'est "
        "étiquetée comme « décision » — GSIE recommande, le forestier décide "
        "(GSIE-CON-001)."
    ),
)
@_limiter.limit("20/minute")
async def recommendation_recommend(
    request_body: RecommendationRequest,
    request: Request,
    response: Response,
    session: DbSession,
    _user: EngineWriteUser,
) -> RecommendationSet:
    """Génère un ensemble de recommandations.

    Raises:
        400: Si la requête est invalide.
    """
    try:
        return await RecommendationEngine(session).recommend(request_body)
    except RecommendationEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/decision",
    status_code=status.HTTP_200_OK,
    summary="Enregistrer la décision du forestier sur une recommandation",
    description=(
        "Trace la décision du forestier (accepte, refuse, modifie, demande "
        "alternative) pour traçabilité (GSIE-CON-005) et alimentation du "
        "Learning Engine. Le forestier n'a pas à se justifier (GSIE-CON-001)."
    ),
)
@_limiter.limit("30/minute")
async def recommendation_decision(
    decision: ForestierDecision,
    request: Request,
    response: Response,
    session: DbSession,
    user: EngineWriteUser,
) -> dict[str, str]:
    """Enregistre la décision du forestier, attribuée à son auteur.

    L'identité de l'appelant était ignorée (`_user`). Une décision anonyme
    satisfait mal `GSIE-CON-005` : savoir qu'une recommandation a été refusée
    sans savoir par qui rend la trace difficile à relire, et impossible à
    contester. La dérivation est celle de `resources/router.py` — le sujet JWT
    peut être un nom d'utilisateur, `uuid5` le rend déterministe.

    Raises:
        400: Si la décision est invalide ou si la recommandation est introuvable.
    """
    try:
        return await RecommendationEngine(session).record_decision(
            decision, forestier_id=_extract_author_id(user)
        )
    except RecommendationEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

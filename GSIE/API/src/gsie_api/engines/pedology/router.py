"""Engine Pedology — propriétés de sol, sourcées et vérifiables.

Responsabilité : fournir les caractéristiques pédologiques (pH,
texture) pour un point donné, sans jamais inventer de seuil
(PEDOLOGY_ENGINE.md). Périmètre v1 : SoilGrids (ISRIC) — voir
docstring engine.py.

Endpoints :
- GET  /pedology/status            — statut du moteur
- GET  /pedology/version           — version et backend
- POST /pedology/query             — propriétés de sol réelles pour un point (transitoire)
- POST /pedology/query-and-ingest  — idem, puis fait entrer le résultat dans le
  Knowledge Engine via EvidenceKnowledgePipeline (Gate 5 — maillon amont)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.limiter import limiter as _limiter
from gsie_api.core.rbac import EngineReadUser, EngineWriteUser
from gsie_api.engines.knowledge.engine import KnowledgeEngine
from gsie_api.engines.pedology.engine import PedologyEngine, PedologyEngineError
from gsie_api.engines.pedology.schemas import (
    PedologyData,
    PedologyIngestResponse,
    PedologyQuery,
)
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/pedology", tags=["pedology"])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


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
        "sans donnée disponible sont omises, jamais approximées (ADR-009)."
    ),
)
@_limiter.limit("30/minute")
async def pedology_query(
    request_body: PedologyQuery,
    request: Request,
    response: Response,
    _user: EngineReadUser,
) -> PedologyData:
    """Récupère les propriétés de sol d'un point.

    Raises:
        502: Si l'API SoilGrids est indisponible.
    """
    try:
        return await PedologyEngine().query(request_body)
    except PedologyEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/query-and-ingest",
    response_model=PedologyIngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Propriétés de sol d'un point, ingérées dans le Knowledge Engine",
    description=(
        "Interroge SoilGrids comme /query, puis fait passer chaque "
        "caractéristique par l'Evidence Engine et l'ingère dans le "
        "Knowledge Engine si acceptée (Gate 5 — maillon amont "
        "ingestion→Evidence→Knowledge, ROADMAP.md). Contrairement à "
        "/query, le résultat devient une connaissance sourcée, "
        "versionnée et réutilisable par les autres moteurs, pas une "
        "valeur transitoire."
    ),
)
@_limiter.limit("10/minute")
async def pedology_query_and_ingest(
    request_body: PedologyQuery,
    request: Request,
    response: Response,
    session: DbSession,
    _user: EngineWriteUser,
) -> PedologyIngestResponse:
    """Récupère les propriétés de sol d'un point et les ingère.

    Raises:
        502: Si l'API SoilGrids est indisponible.

    Note : `EvidenceKnowledgePipeline.process()` capture déjà
    `KnowledgeEngineError` en interne et le rapporte comme un résultat
    « refused » par caractéristique (voir `PedologyIngestResult.raison`)
    plutôt que de le laisser remonter — ce n'est donc jamais une erreur
    HTTP ici, uniquement dans le corps de la réponse.
    """
    try:
        return await PedologyEngine().query_and_ingest(request_body, KnowledgeEngine(session))
    except PedologyEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

"""Engine Knowledge — centralisation et versionnement des connaissances.

Responsabilité : centraliser, structurer et versionner les connaissances
scientifiques qualifiées dans un graphe interrogeable (KNOWLEDGE_ENGINE.md).

Source unique de vérité pour tous les moteurs de raisonnement.
Aucune logique d'inférence — le moteur stocke et fournit (CON-007).
Versionnement complet (CON-010) — aucune connaissance supprimée silencieusement.

Endpoints :
- GET  /knowledge/status   — statut du moteur
- GET  /knowledge/version   — version et backend
- POST /knowledge/ingest    — ingère une connaissance qualifiée (depuis Evidence)
- POST /knowledge/query     — interroge le graphe de connaissances
- POST /knowledge/revise    — révise une connaissance existante (CON-010)
- GET  /knowledge/stats     — statistiques du graphe
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from gsie_api.core.auth import get_current_user
from gsie_api.engines.knowledge.engine import (
    KnowledgeEngine,
    KnowledgeEngineError,
    KnowledgeNotFoundError,
)
from gsie_api.engines.knowledge.schemas import (
    KnowledgeIngestRequest,
    KnowledgeObject,
    KnowledgeQuery,
    KnowledgeQueryResult,
    KnowledgeRevisionRequest,
)
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# Rate limiter pour les endpoints POST
_ingest_limiter = Limiter(key_func=get_remote_address)
_query_limiter = Limiter(key_func=get_remote_address)

# Instance singleton du moteur (Vague 1 — stockage en mémoire)
_engine = KnowledgeEngine()


@router.get("/status", response_model=EngineStatusResponse)
async def knowledge_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Knowledge."""
    return EngineStatusResponse(
        engine="knowledge",
        status="active",
        planned_week=3,
        language="python",
    )


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur Knowledge",
)
async def knowledge_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=KnowledgeEngine.version(),
        backend="python-in-memory",
    )


@router.post(
    "/ingest",
    response_model=KnowledgeObject,
    status_code=status.HTTP_201_CREATED,
    summary="Ingérer une connaissance qualifiée dans le graphe",
    description=(
        "Ingère une connaissance qualifiée (statut « accepte » depuis l'Evidence Engine) "
        "dans le graphe de connaissances. La connaissance reçoit la version 1 et "
        "son historique est initialisé vide. "
        "Les connaissances en quarantaine ou refusées sont rejetées (CON-001)."
    ),
)
@_ingest_limiter.limit("30/minute")
async def knowledge_ingest(
    request_body: KnowledgeIngestRequest,
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> KnowledgeObject:
    """Ingère une connaissance dans le graphe.

    Raises:
        400: Si la connaissance existe déjà ou si le statut n'est pas « accepte ».
    """
    try:
        return _engine.ingest(request_body)
    except KnowledgeEngineError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/query",
    response_model=KnowledgeQueryResult,
    status_code=status.HTTP_200_OK,
    summary="Interroger le graphe de connaissances",
    description=(
        "Interroge le graphe selon un type de requête (par_concept, par_relation, "
        "par_domaine, par_essence, par_station) avec filtres optionnels et "
        "filtre par niveau de preuve minimum. Les résultats sont paginés."
    ),
)
@_query_limiter.limit("60/minute")
async def knowledge_query(
    query: KnowledgeQuery,
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> KnowledgeQueryResult:
    """Interroge le graphe de connaissances."""
    return _engine.query(query)


@router.post(
    "/revise",
    response_model=KnowledgeObject,
    status_code=status.HTTP_200_OK,
    summary="Réviser une connaissance existante (CON-010)",
    description=(
        "Révise une connaissance en archivant l'ancienne version dans l'historique "
        "et en créant une nouvelle version. La connaissance n'est jamais supprimée "
        "silencieusement (CON-010). Au moins un champ modifié est requis."
    ),
)
@_ingest_limiter.limit("30/minute")
async def knowledge_revise(
    revision: KnowledgeRevisionRequest,
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> KnowledgeObject:
    """Révise une connaissance existante.

    Raises:
        404: Si la connaissance n'existe pas.
        400: Si aucun champ n'est modifié.
    """
    from fastapi import HTTPException

    try:
        return _engine.revise(revision)
    except KnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except KnowledgeEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/stats",
    summary="Statistiques du graphe de connaissances",
)
async def knowledge_stats(
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, int]:
    """Retourne les statistiques du graphe (nombre d'objets par type)."""
    return _engine.stats()

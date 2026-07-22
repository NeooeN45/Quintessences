"""Engine Botanical — taxonomie et nomenclature, sourcées et vérifiables.

Responsabilité : résoudre une essence vers son taxon (GBIF Backbone
Taxonomy), résoudre les synonymes vers le taxon accepté
(BOTANICAL_ENGINE.md). Périmètre v1 : taxonomie/nomenclature
uniquement — pas d'autécologie (voir docstring engine.py).

Endpoints :
- GET  /botanical/status   — statut du moteur
- GET  /botanical/version  — version et backend
- POST /botanical/query     — résout une essence vers son taxon GBIF
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.rbac import EngineReadUser, EngineWriteUser
from gsie_api.engines.botanical.engine import BotanicalEngine, BotanicalEngineError
from gsie_api.engines.botanical.schemas import (
    BotanicalData,
    BotanicalQuery,
    IndigenatQuery,
    IndigenatResult,
    TaxrefQuery,
    TaxrefResult,
)
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/botanical", tags=["botanical"])

_botanical_limiter = Limiter(key_func=get_remote_address)

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/status", response_model=EngineStatusResponse)
async def botanical_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Botanical."""
    return EngineStatusResponse(
        engine="botanical",
        status="active",
        planned_week=9,
        language="python",
    )


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur Botanical",
)
async def botanical_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=BotanicalEngine.version(),
        backend="postgresql",
    )


@router.post(
    "/query",
    response_model=BotanicalData,
    status_code=status.HTTP_200_OK,
    summary="Résoudre une essence vers son taxon GBIF",
    description=(
        "Résout un nom scientifique vers son taxon accepté (GBIF Backbone "
        "Taxonomy), en résolvant les synonymes. Persiste le taxon comme "
        "resource `entity` (dédupliqué par clé GBIF). Retourne une liste "
        "vide si aucune correspondance — jamais de taxon inventé (ADR-007)."
    ),
)
@_botanical_limiter.limit("30/minute")
async def botanical_query(
    request_body: BotanicalQuery,
    request: Request,
    session: DbSession,
    _user: EngineWriteUser,
) -> BotanicalData:
    """Résout une essence vers son taxon GBIF.

    Raises:
        502: Si l'API GBIF est indisponible.
    """
    try:
        return await BotanicalEngine(session).query(request_body)
    except BotanicalEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/indigenat",
    response_model=IndigenatResult | None,
    status_code=status.HTTP_200_OK,
    summary="Statut d'indigénat réel d'une essence pour une sylvoécorégion",
    description=(
        "Interroge le dataset réel Bellifa et al. (2026, DOI "
        "10.57745/DHJHGS) pour le statut d'indigénat d'une essence "
        "(France + sylvoécorégion). Retourne null si le taxon ou le "
        "code SER est introuvable — jamais un statut approximé (ADR-007)."
    ),
)
@_botanical_limiter.limit("30/minute")
async def botanical_indigenat(
    request_body: IndigenatQuery,
    request: Request,
    session: DbSession,
    _user: EngineReadUser,
) -> IndigenatResult | None:
    """Récupère le statut d'indigénat réel d'une essence.

    Raises:
        502: Si le dataset local d'indigénat est introuvable.
        400: Si une valeur de statut inattendue est rencontrée dans le dataset.
    """
    try:
        return BotanicalEngine(session).get_indigenat(request_body)
    except BotanicalEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/taxref",
    response_model=TaxrefResult | None,
    status_code=status.HTTP_200_OK,
    summary="Résout un nom scientifique vers son entrée TAXREF réelle (SCI-003)",
    description=(
        "Interroge le référentiel taxonomique TAXREF (miroir GBIF, "
        "infrastructure MNHN directe dégradée). Retourne null si aucune "
        "entrée ne correspond — jamais un cd_nom inventé (ADR-007)."
    ),
)
@_botanical_limiter.limit("30/minute")
async def botanical_taxref(
    request_body: TaxrefQuery,
    request: Request,
    session: DbSession,
    _user: EngineReadUser,
) -> TaxrefResult | None:
    """Résout un nom scientifique vers son entrée TAXREF réelle.

    Raises:
        502: Si le miroir GBIF de TAXREF est indisponible.
    """
    try:
        return await BotanicalEngine(session).resolve_taxref(request_body)
    except BotanicalEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

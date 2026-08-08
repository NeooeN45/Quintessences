"""Engine Botanical — taxonomie et nomenclature, sourcées et vérifiables.

Responsabilité : résoudre une essence vers son taxon (GBIF Backbone
Taxonomy), résoudre les synonymes vers le taxon accepté
(BOTANICAL_ENGINE.md). Périmètre v1 : taxonomie/nomenclature
uniquement — pas d'autécologie (voir docstring engine.py).

Endpoints :
- GET  /botanical/status              — statut du moteur
- GET  /botanical/version             — version et backend
- POST /botanical/query                — résout une essence vers son taxon GBIF
- POST /botanical/identify             — identifie une plante par image (PlantNet, RFC-0031)
- POST /botanical/identify-and-ingest  — idem, puis fait entrer les candidats dans le
  Knowledge Engine via EvidenceKnowledgePipeline (Gate 5 — maillon amont)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.limiter import limiter as _limiter
from gsie_api.core.rbac import EngineReadUser, EngineWriteUser
from gsie_api.engines.botanical.engine import (
    BotanicalEngine,
    BotanicalEngineError,
    parse_plantnet_results,
)
from gsie_api.engines.botanical.plantnet_client import PlantNetClient, PlantNetClientError
from gsie_api.engines.botanical.schemas import (
    BotanicalData,
    BotanicalQuery,
    IndigenatQuery,
    IndigenatResult,
    PlantNetIdentificationResponse,
    PlantNetIngestResponse,
    TaxrefQuery,
    TaxrefResult,
)
from gsie_api.engines.knowledge.engine import KnowledgeEngine
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/botanical", tags=["botanical"])

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
        "vide si aucune correspondance — jamais de taxon inventé (ADR-009)."
    ),
)
@_limiter.limit("30/minute")
async def botanical_query(
    request_body: BotanicalQuery,
    request: Request,
    response: Response,
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
        "code SER est introuvable — jamais un statut approximé (ADR-009)."
    ),
)
@_limiter.limit("30/minute")
async def botanical_indigenat(
    request_body: IndigenatQuery,
    request: Request,
    response: Response,
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
        "entrée ne correspond — jamais un cd_nom inventé (ADR-009)."
    ),
)
@_limiter.limit("30/minute")
async def botanical_taxref(
    request_body: TaxrefQuery,
    request: Request,
    response: Response,
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


@router.post(
    "/identify",
    response_model=PlantNetIdentificationResponse | None,
    status_code=status.HTTP_200_OK,
    summary="Identifier une plante par image (API PlantNet, RFC-0031 action 8)",
    description=(
        "Soumet une image (JPG/PNG) à l'API PlantNet pour identification. "
        "78 810 espèces identifiables. Retourne la meilleure correspondance "
        "et les résultats classés par score de confiance. Retourne null si "
        "aucune identification n'est possible — jamais d'espèce inventée (ADR-009)."
    ),
)
@_limiter.limit("10/minute")
async def botanical_identify(
    request: Request,
    response: Response,
    file: Annotated[UploadFile, File(description="Image de la plante (JPG ou PNG)")],
    _user: EngineReadUser,
) -> PlantNetIdentificationResponse | None:
    """Identifie une plante à partir d'une image via l'API PlantNet.

    Raises:
        502: Si l'API PlantNet est indisponible ou la clé API manquante.
        400: Si le fichier est vide ou dans un format non supporté.
    """
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Fichier image vide")
    if file.content_type and file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté : {file.content_type}. JPG ou PNG requis.",
        )
    try:
        data = await PlantNetClient().identify(
            image_bytes,
            filename=file.filename or "image.jpg",
        )
    except PlantNetClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if data is None:
        return None
    return PlantNetIdentificationResponse(
        best_match=data.get("bestMatch"),
        results=parse_plantnet_results(data),
    )


@router.post(
    "/identify-and-ingest",
    response_model=PlantNetIngestResponse | None,
    status_code=status.HTTP_200_OK,
    summary="Identifier une plante par image, candidats ingérés dans le Knowledge Engine",
    description=(
        "Identifie une plante comme /identify, puis fait passer chaque "
        "espèce candidate par l'Evidence Engine et l'ingère dans le "
        "Knowledge Engine (Gate 5 — maillon amont ingestion→Evidence→"
        "Knowledge, ROADMAP.md). Une identification par image plafonne à "
        "evidence_level=D (quarantaine, validation humaine requise, "
        "CON-001) — contrairement à SoilGrids, ce n'est jamais ingéré "
        "automatiquement."
    ),
)
@_limiter.limit("10/minute")
async def botanical_identify_and_ingest(
    request: Request,
    response: Response,
    file: Annotated[UploadFile, File(description="Image de la plante (JPG ou PNG)")],
    session: DbSession,
    _user: EngineWriteUser,
) -> PlantNetIngestResponse | None:
    """Identifie une plante par image et ingère les candidats.

    Raises:
        502: Si l'API PlantNet est indisponible ou la clé API manquante.
        400: Si le fichier est vide ou dans un format non supporté.
    """
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Fichier image vide")
    if file.content_type and file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté : {file.content_type}. JPG ou PNG requis.",
        )
    try:
        return await BotanicalEngine(session).identify_and_ingest(
            image_bytes,
            filename=file.filename or "image.jpg",
            knowledge_engine=KnowledgeEngine(session),
        )
    except BotanicalEngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

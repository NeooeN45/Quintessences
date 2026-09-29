"""BFF sécurisé et propriétaire consommé par l'application GeoSylva."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.auth import get_current_user
from gsie_api.core.limiter import limiter
from gsie_api.data.service import DataRegistryService
from gsie_api.geosylva.repository import (
    AnalysisIdempotencyConflictError,
    GeoSylvaAnalysisRepository,
)
from gsie_api.geosylva.schemas import (
    AnalysisAccepted,
    AnalysisStatusResponse,
    GeoSylvaAnalysisRequest,
    ScientificAnalysisResult,
)
from gsie_api.geosylva.service import GeoSylvaAnalysisService
from gsie_api.infrastructure.database import get_db
from gsie_api.infrastructure.models.enums import DatasetStatus

router = APIRouter(prefix="/geosylva", tags=["geosylva-bff"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]


def _account_id(current_user: dict[str, Any]) -> UUID:
    try:
        return UUID(str(current_user.get("sub", "")))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session nominative invalide"
        ) from None


def _trace_id(request: Request) -> str:
    value = getattr(request.state, "trace_id", None)
    return str(value or request.headers.get("X-Trace-Id") or "n/a")


@router.post(
    "/analyses",
    response_model=AnalysisAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Créer une analyse scientifique asynchrone",
)
@limiter.limit("10/minute")
async def create_analysis(
    body: GeoSylvaAnalysisRequest,
    request: Request,
    response: Response,
    session: DbSession,
    current_user: CurrentUser,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=36, max_length=36)],
) -> AnalysisAccepted:
    if idempotency_key != str(body.request_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key doit être égal à request_id",
        )
    try:
        job, _created = await GeoSylvaAnalysisService(session).submit(
            _account_id(current_user),
            body,
            now=datetime.now(UTC),
            trace_id=_trace_id(request),
        )
        await session.commit()
    except AnalysisIdempotencyConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    base = f"/api/v1/geosylva/analyses/{job.id}"
    response.headers["Location"] = base
    response.headers["Retry-After"] = "2"
    response.headers["Idempotency-Key"] = str(body.request_id)
    return AnalysisAccepted(
        analysis_id=job.id,
        status_url=base,
        result_url=f"{base}/result",
    )


@router.get("/analyses/{analysis_id}", response_model=AnalysisStatusResponse)
@limiter.limit("60/minute")
async def get_analysis_status(
    analysis_id: UUID,
    request: Request,
    response: Response,
    session: DbSession,
    current_user: CurrentUser,
) -> AnalysisStatusResponse:
    job = await GeoSylvaAnalysisRepository(session).get_owned(
        analysis_id, _account_id(current_user)
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analyse introuvable")
    retry = 2 if job.status in {"pending", "running"} else None
    if retry is not None:
        response.headers["Retry-After"] = str(retry)
    return AnalysisStatusResponse(
        analysis_id=job.id,
        status=job.status,
        progress_percent=job.progress_percent,
        completed_engines=list(job.completed_engines),
        unavailable_engines=list(job.unavailable_engines),
        warnings=list(job.warnings),
        error_code=job.error_code,
        created_at=job.created_at,
        updated_at=job.updated_at,
        retry_after_seconds=retry,
    )


@router.get("/analyses/{analysis_id}/result", response_model=ScientificAnalysisResult)
@limiter.limit("30/minute")
async def get_analysis_result(
    analysis_id: UUID,
    request: Request,
    response: Response,
    session: DbSession,
    current_user: CurrentUser,
) -> ScientificAnalysisResult:
    job = await GeoSylvaAnalysisRepository(session).get_owned(
        analysis_id, _account_id(current_user)
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analyse introuvable")
    if job.result_payload is None:
        if job.status in {"pending", "running"}:
            response.headers["Retry-After"] = "2"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Résultat non disponible"
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="L'analyse n'a produit aucun résultat scientifique publiable",
        )
    return ScientificAnalysisResult.model_validate(job.result_payload)


@router.get("/resources")
@limiter.limit("60/minute")
async def list_resources(
    request: Request,
    response: Response,
    session: DbSession,
    _current_user: CurrentUser,
    cursor: Annotated[str | None, Query(max_length=512)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    domain: Annotated[str | None, Query(max_length=100)] = None,
) -> dict[str, Any]:
    result = await DataRegistryService(session).catalog(
        cursor=cursor,
        limit=limit,
        status=DatasetStatus.production,
        domain=domain,
    )
    return result.model_dump(mode="json")


@router.get("/resources/{dataset_id}")
@limiter.limit("60/minute")
async def get_resource(
    dataset_id: UUID,
    request: Request,
    response: Response,
    session: DbSession,
    _current_user: CurrentUser,
) -> dict[str, Any]:
    result = await DataRegistryService(session).dataset(dataset_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ressource introuvable")
    versions = [
        version for version in result.item.versions if version.status is DatasetStatus.production
    ]
    if not versions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ressource introuvable")
    payload = result.model_dump(mode="json")
    payload["item"]["versions"] = [version.model_dump(mode="json") for version in versions]
    return payload


__all__ = ["router"]

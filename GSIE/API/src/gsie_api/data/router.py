"""Routes authentifiées du Data Registry RFC-0038 (lecture Phase 2)."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Annotated, Any
from uuid import UUID  # noqa: TC003

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.auth import get_current_user
from gsie_api.core.config import get_settings
from gsie_api.core.limiter import limiter
from gsie_api.core.rbac import can_access_resource, check_permission
from gsie_api.data.schemas import (
    CatalogResponse,
    CoverageResponse,
    DataSearchQuery,
    DatasetResponse,
    HealthResponse,
    ProvidersResponse,
    ResolutionResponse,
    ResolveRequest,
    SearchResponse,
)
from gsie_api.data.service import DataRegistryService, RegistryContractError
from gsie_api.infrastructure.database import get_db_resource
from gsie_api.infrastructure.models.enums import (  # noqa: TC001
    DatasetHealthStatus,
    DatasetStatus,
    EvidenceLevel,
)

router = APIRouter(prefix="/data", tags=["data-registry"])
_settings = get_settings()

CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db_resource)]


def _contract_http_error(exc: RegistryContractError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"code": exc.code, "message": str(exc)},
    )


def _read_permission(user: dict[str, Any]) -> None:
    check_permission(user, "dataset", "read")


@router.get(
    "/catalog",
    response_model=CatalogResponse,
    summary="Catalogue paginé des datasets GSIE",
)
@limiter.limit(_settings.rate_limit_default)
async def catalog(
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DbSession,
    cursor: str | None = Query(None, max_length=512),
    limit: int = Query(20, ge=1, le=100),
    status_filter: DatasetStatus | None = Query(None, alias="status"),  # noqa: B008
    domain: str | None = Query(None, max_length=100),
    publisher_id: UUID | None = Query(None),  # noqa: B008
) -> CatalogResponse:
    _read_permission(user)
    try:
        return await DataRegistryService(session).catalog(
            cursor=cursor,
            limit=limit,
            status=status_filter,
            domain=domain,
            publisher_id=publisher_id,
        )
    except RegistryContractError as exc:
        raise _contract_http_error(exc) from exc


@router.get(
    "/datasets/{dataset_id}",
    response_model=DatasetResponse,
    summary="Détail d'un dataset et de ses versions",
)
@limiter.limit(_settings.rate_limit_default)
async def dataset(
    dataset_id: UUID,
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DbSession,
) -> DatasetResponse:
    _read_permission(user)
    item = await DataRegistryService(session).dataset(dataset_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "dataset_id": str(dataset_id)},
        )
    return item


@router.get(
    "/providers",
    response_model=ProvidersResponse,
    summary="Projection paginée Agent/Source/Citation",
)
@limiter.limit(_settings.rate_limit_default)
async def providers(
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DbSession,
    dataset_id: UUID | None = Query(None),  # noqa: B008
    cursor: str | None = Query(None, max_length=512),
    limit: int = Query(20, ge=1, le=100),
) -> ProvidersResponse:
    _read_permission(user)
    return await DataRegistryService(session).providers(
        cursor=cursor,
        limit=limit,
        dataset_id=dataset_id,
        include_agent=can_access_resource(user, "agent", "read"),
    )


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Recherche catalogue déterministe (sans resolver)",
)
@limiter.limit(_settings.rate_limit_default)
async def search(
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DbSession,
    theme: str | None = Query(None, max_length=100),
    bbox: list[float] | None = Query(None, description="min_lon,min_lat,max_lon,max_lat"),  # noqa: B008
    date_start: datetime | None = Query(None),  # noqa: B008
    date_end: datetime | None = Query(None),  # noqa: B008
    max_grain_m2: float | None = Query(None, gt=0),
    minimum_evidence_level: EvidenceLevel | None = Query(None),  # noqa: B008
    minimum_quality_score: float | None = Query(None, ge=0, le=1),
    commercial_use_required: bool = Query(False),
    use: str = Query("display", pattern="^(display|inference)$"),
    prefer: list[str] | None = Query(None),  # noqa: B008
    cursor: str | None = Query(None, max_length=512),
    limit: int = Query(20, ge=1, le=100),
) -> SearchResponse:
    _read_permission(user)
    if bbox is not None and len(bbox) != 4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "BBOX_INVALID", "message": "bbox attend quatre coordonnées"},
        )
    try:
        query = DataSearchQuery(
            theme=theme,
            bbox=tuple(bbox) if bbox is not None else None,
            date_start=date_start,
            date_end=date_end,
            max_grain_m2=max_grain_m2,
            minimum_evidence_level=minimum_evidence_level,
            minimum_quality_score=minimum_quality_score,
            commercial_use_required=commercial_use_required,
            use=use,
            prefer=prefer or [],
            cursor=cursor,
            limit=limit,
        )
        return await DataRegistryService(session).search(query)
    except RegistryContractError as exc:
        raise _contract_http_error(exc) from exc


@router.post(
    "/resolve",
    response_model=ResolutionResponse,
    summary="Sélection déterministe d'un dataset avec décision explicable",
)
@limiter.limit(_settings.rate_limit_default)
async def resolve(
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DbSession,
    payload: ResolveRequest,
) -> ResolutionResponse:
    """Applique la politique Registry avant tout classement ou fallback."""

    _read_permission(user)
    try:
        return await DataRegistryService(session).resolve(
            payload,
            trace_id=request.headers.get("X-Trace-Id"),
        )
    except RegistryContractError as exc:
        raise _contract_http_error(exc) from exc


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Historique de santé par distribution",
)
@limiter.limit(_settings.rate_limit_default)
async def health(
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DbSession,
    health_status: DatasetHealthStatus | None = Query(None),  # noqa: B008
    dataset_version_id: UUID | None = Query(None),  # noqa: B008
    distribution_id: UUID | None = Query(None),  # noqa: B008
    cursor: str | None = Query(None, max_length=512),
    limit: int = Query(20, ge=1, le=100),
) -> HealthResponse:
    _read_permission(user)
    try:
        return await DataRegistryService(session).health(
            cursor=cursor,
            limit=limit,
            health_status=health_status,
            dataset_version_id=dataset_version_id,
            distribution_id=distribution_id,
        )
    except RegistryContractError as exc:
        raise _contract_http_error(exc) from exc


@router.get(
    "/coverage",
    response_model=CoverageResponse,
    summary="Emprises, CRS et grains natifs par distribution",
)
@limiter.limit(_settings.rate_limit_default)
async def coverage(
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DbSession,
    cursor: str | None = Query(None, max_length=512),
    limit: int = Query(20, ge=1, le=100),
) -> CoverageResponse:
    _read_permission(user)
    try:
        return await DataRegistryService(session).coverage(cursor=cursor, limit=limit)
    except RegistryContractError as exc:
        raise _contract_http_error(exc) from exc

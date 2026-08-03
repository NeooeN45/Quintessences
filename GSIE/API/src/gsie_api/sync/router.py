"""API privée de synchronisation GeoSylva, isolée par compte et par RLS."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.auth import get_current_user
from gsie_api.core.limiter import limiter
from gsie_api.core.logging import get_logger
from gsie_api.infrastructure.database import get_db_rls
from gsie_api.sync.geosylva import (
    GeoSylvaParcelMutation,
    GeoSylvaParcelRecord,
    GeoSylvaSyncConflictError,
    GeoSylvaSyncService,
)
from gsie_api.sync.repository import SqlAlchemyGeoSylvaParcelRepository
from gsie_api.sync.schemas import (
    GeoSylvaClientId,
    GeoSylvaDeleteRequest,
    GeoSylvaParcelPage,
    GeoSylvaParcelPayload,
    GeoSylvaParcelResponse,
    GeoSylvaUpsertRequest,
)

router = APIRouter(prefix="/sync/geosylva", tags=["sync-geosylva"])
logger = get_logger("gsie_api.sync.geosylva")


async def get_geosylva_sync_service(
    session: Annotated[AsyncSession, Depends(get_db_rls)],
) -> GeoSylvaSyncService:
    return GeoSylvaSyncService(SqlAlchemyGeoSylvaParcelRepository(session))


def _account_id(current_user: dict[str, object]) -> UUID:
    try:
        return UUID(str(current_user.get("sub", "")))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide"
        ) from None


def _response(record: GeoSylvaParcelRecord) -> GeoSylvaParcelResponse:
    parcel = None
    if record.deleted_at is None:
        parcel = GeoSylvaParcelPayload.model_validate(record.payload)
    return GeoSylvaParcelResponse(
        client_id=record.client_id,
        status="deleted" if record.deleted_at is not None else "active",
        server_version=record.version,
        client_updated_at=record.client_updated_at,
        server_updated_at=record.updated_at,
        parcel=parcel,
    )


def _raise_conflict(error: GeoSylvaSyncConflictError) -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "SYNC_VERSION_CONFLICT",
            "current": _response(error.current).model_dump(mode="json") if error.current else None,
        },
    ) from None


@router.put("/parcelles/{client_id}", response_model=GeoSylvaParcelResponse)
@limiter.limit("120/minute")
async def upsert_parcel(
    request: Request,
    response: Response,
    client_id: GeoSylvaClientId,
    mutation: GeoSylvaUpsertRequest,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[GeoSylvaSyncService, Depends(get_geosylva_sync_service)],
) -> GeoSylvaParcelResponse:
    del request, response
    account_id = _account_id(current_user)
    try:
        record = await service.upsert(
            account_id,
            client_id,
            GeoSylvaParcelMutation(
                operation_id=mutation.operation_id,
                base_version=mutation.base_version,
                client_updated_at=mutation.client_updated_at,
                payload=mutation.parcel.model_dump(mode="json"),
            ),
        )
    except GeoSylvaSyncConflictError as error:
        _raise_conflict(error)
    logger.info(
        "geosylva_parcel_synchronized",
        account_id=str(account_id),
        client_id=client_id,
        server_version=record.version,
    )
    return _response(record)


@router.delete("/parcelles/{client_id}", response_model=GeoSylvaParcelResponse)
@limiter.limit("120/minute")
async def delete_parcel(
    request: Request,
    response: Response,
    client_id: GeoSylvaClientId,
    deletion: GeoSylvaDeleteRequest,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[GeoSylvaSyncService, Depends(get_geosylva_sync_service)],
) -> GeoSylvaParcelResponse:
    del request, response
    account_id = _account_id(current_user)
    try:
        record = await service.delete(
            account_id,
            client_id,
            operation_id=deletion.operation_id,
            base_version=deletion.base_version,
            client_updated_at=deletion.client_updated_at,
        )
    except GeoSylvaSyncConflictError as error:
        _raise_conflict(error)
    logger.info(
        "geosylva_parcel_deleted",
        account_id=str(account_id),
        client_id=client_id,
        server_version=record.version,
    )
    return _response(record)


@router.get("/parcelles", response_model=GeoSylvaParcelPage)
@limiter.limit("60/minute")
async def list_parcels(
    request: Request,
    response: Response,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[GeoSylvaSyncService, Depends(get_geosylva_sync_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> GeoSylvaParcelPage:
    del request, response
    records, total = await service.list(_account_id(current_user), page=page, size=size)
    return GeoSylvaParcelPage(
        items=[_response(record) for record in records],
        page=page,
        size=size,
        total=total,
    )

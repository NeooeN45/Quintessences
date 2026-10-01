"""Service de synchronisation des sessions de cubage GeoSylva."""

# ruff: noqa: TC001, TC002, TC003

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.geosylva.cubage_repository import GeoSylvaCubageRepository
from gsie_api.geosylva.cubage_schemas import (
    CubageSessionResponse,
    CubageSyncRequest,
    CubageSyncResponse,
    CubageSyncStatus,
)
from gsie_api.infrastructure.models.geosylva_cubage import GeoSylvaCubageSessionModel


class GeoSylvaCubageService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = GeoSylvaCubageRepository(session)

    async def synchronize(
        self,
        account_id: UUID,
        request: CubageSyncRequest,
        *,
        idempotency_key: str,
        trace_id: str,
        now: datetime,
    ) -> tuple[CubageSyncResponse, bool]:
        model, created = await self._repository.create_or_get(
            account_id,
            request,
            idempotency_key=idempotency_key,
            trace_id=trace_id,
            now=now,
        )
        return self._response(model, trace_id), created

    async def get_owned(
        self, session_id: UUID, account_id: UUID, *, trace_id: str
    ) -> CubageSessionResponse | None:
        model = await self._repository.get_owned(session_id, account_id)
        if model is None:
            return None
        request = CubageSyncRequest.model_validate(model.request_payload)
        return CubageSessionResponse(
            session=request.session,
            measurements=request.measurements,
            calculation=request.calculation,
            verification=None,
            trace_id=trace_id,
        )

    @staticmethod
    def _response(model: GeoSylvaCubageSessionModel, trace_id: str) -> CubageSyncResponse:
        return CubageSyncResponse(
            session_id=model.session_id,
            calculation_id=model.calculation_id,
            status=CubageSyncStatus(model.status),
            server_record_id=model.session_id,
            server_verification_id=None,
            warnings=list(model.warnings),
            trace_id=trace_id,
        )


__all__ = ["GeoSylvaCubageService"]

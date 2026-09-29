"""Repository de persistance des sessions de cubage GeoSylva."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.geosylva.cubage_schemas import (
    CubageSyncRequest,
    canonical_cubage_fingerprint,
)
from gsie_api.infrastructure.models.geosylva_cubage import GeoSylvaCubageSessionModel


class CubageIdempotencyConflictError(ValueError):
    """Une clé d'idempotence désigne deux paquets différents."""


class GeoSylvaCubageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_or_get(
        self,
        account_id: UUID,
        request: CubageSyncRequest,
        *,
        idempotency_key: str,
        trace_id: str,
        now: datetime,
    ) -> tuple[GeoSylvaCubageSessionModel, bool]:
        fingerprint = canonical_cubage_fingerprint(request)
        await self._lock(account_id, idempotency_key)
        existing = await self._find_by_key(account_id, idempotency_key)
        if existing is not None:
            self._ensure_same_payload(existing, fingerprint)
            return existing, False
        model = GeoSylvaCubageSessionModel(
            session_id=request.session.session_id,
            account_id=account_id,
            calculation_id=request.calculation.calculation_id,
            idempotency_key=idempotency_key,
            session_fingerprint=request.session.session_fingerprint,
            measurements_fingerprint=request.measurements.measurements_fingerprint,
            inputs_fingerprint=request.calculation.inputs_fingerprint,
            result_fingerprint=request.calculation.result_fingerprint,
            request_fingerprint=fingerprint,
            status="synced",
            request_payload=request.model_dump(mode="json"),
            warnings=list(request.calculation.quality.warnings),
            trace_id=trace_id,
            created_at=now,
            updated_at=now,
        )
        self._session.add(model)
        await self._session.flush()
        return model, True

    async def get_owned(
        self, session_id: UUID, account_id: UUID
    ) -> GeoSylvaCubageSessionModel | None:
        statement = select(GeoSylvaCubageSessionModel).where(
            GeoSylvaCubageSessionModel.session_id == session_id,
            GeoSylvaCubageSessionModel.account_id == account_id,
        )
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def _find_by_key(
        self, account_id: UUID, idempotency_key: str
    ) -> GeoSylvaCubageSessionModel | None:
        statement = select(GeoSylvaCubageSessionModel).where(
            GeoSylvaCubageSessionModel.account_id == account_id,
            GeoSylvaCubageSessionModel.idempotency_key == idempotency_key,
        )
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def _lock(self, account_id: UUID, idempotency_key: str) -> None:
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
            {"lock_key": f"geosylva-cubage:{account_id}:{idempotency_key}"},
        )

    @staticmethod
    def _ensure_same_payload(
        existing: GeoSylvaCubageSessionModel, fingerprint: str
    ) -> None:
        if existing.request_fingerprint != fingerprint:
            raise CubageIdempotencyConflictError(
                "La clé d'idempotence existe déjà avec un paquet différent"
            )


__all__ = ["CubageIdempotencyConflictError", "GeoSylvaCubageRepository"]

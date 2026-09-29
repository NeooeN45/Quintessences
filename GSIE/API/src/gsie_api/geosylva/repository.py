"""Repository SQL des jobs GeoSylva, avec propriété et reprise concurrente."""

# ruff: noqa: TC002, TC003

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.geosylva.schemas import GeoSylvaAnalysisRequest, canonical_request_fingerprint
from gsie_api.infrastructure.models.geosylva_analysis import GeoSylvaAnalysisJobModel


class AnalysisIdempotencyConflictError(ValueError):
    """La même clé de compte désigne une demande au contenu différent."""


class GeoSylvaAnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_or_get(
        self,
        account_id: UUID,
        request: GeoSylvaAnalysisRequest,
        *,
        now: datetime,
        trace_id: str,
    ) -> tuple[GeoSylvaAnalysisJobModel, bool]:
        fingerprint = canonical_request_fingerprint(request)
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
            {"lock_key": f"geosylva-analysis:{account_id}:{request.request_id}"},
        )
        statement = select(GeoSylvaAnalysisJobModel).where(
            GeoSylvaAnalysisJobModel.account_id == account_id,
            GeoSylvaAnalysisJobModel.request_id == request.request_id,
        )
        existing = (await self._session.execute(statement)).scalar_one_or_none()
        if existing is not None:
            if existing.request_fingerprint != fingerprint:
                raise AnalysisIdempotencyConflictError(
                    "La clé d'idempotence existe déjà avec une demande différente"
                )
            return existing, False
        job = GeoSylvaAnalysisJobModel(
            account_id=account_id,
            request_id=request.request_id,
            request_fingerprint=fingerprint,
            station_id=request.station_id,
            request_payload=request.model_dump(mode="json"),
            status="pending",
            progress_percent=0,
            trace_id=trace_id,
            next_attempt_at=now,
            expires_at=now + timedelta(days=30),
        )
        self._session.add(job)
        await self._session.flush()
        return job, True

    async def get_owned(
        self, analysis_id: UUID, account_id: UUID
    ) -> GeoSylvaAnalysisJobModel | None:
        statement = select(GeoSylvaAnalysisJobModel).where(
            GeoSylvaAnalysisJobModel.id == analysis_id,
            GeoSylvaAnalysisJobModel.account_id == account_id,
        )
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def get(self, analysis_id: UUID) -> GeoSylvaAnalysisJobModel | None:
        return await self._session.get(GeoSylvaAnalysisJobModel, analysis_id)

    async def claim_next(self, *, now: datetime) -> GeoSylvaAnalysisJobModel | None:
        statement = (
            select(GeoSylvaAnalysisJobModel)
            .where(
                GeoSylvaAnalysisJobModel.expires_at > now,
                GeoSylvaAnalysisJobModel.next_attempt_at <= now,
                or_(
                    GeoSylvaAnalysisJobModel.status == "pending",
                    (
                        (GeoSylvaAnalysisJobModel.status == "running")
                        & (GeoSylvaAnalysisJobModel.lease_expires_at < now)
                    ),
                ),
            )
            .order_by(GeoSylvaAnalysisJobModel.next_attempt_at, GeoSylvaAnalysisJobModel.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        job = (await self._session.execute(statement)).scalar_one_or_none()
        if job is None:
            return None
        job.status = "running"
        job.progress_percent = max(job.progress_percent, 5)
        job.started_at = job.started_at or now
        job.lease_expires_at = now + timedelta(minutes=10)
        job.attempt_count += 1
        await self._session.flush()
        return job


__all__ = ["AnalysisIdempotencyConflictError", "GeoSylvaAnalysisRepository"]

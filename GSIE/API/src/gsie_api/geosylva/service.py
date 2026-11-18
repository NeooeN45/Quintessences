"""Soumission et exécution serveur des analyses GeoSylva."""

# ruff: noqa: TC001, TC002, TC003

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.orchestration.preparation import StationPreparationService
from gsie_api.engines.orchestration.schemas import AnalyseRequest
from gsie_api.engines.orchestration.service import OrchestrationEngine
from gsie_api.engines.validation.schemas import ValidationStatut
from gsie_api.geosylva.publication import build_scientific_result
from gsie_api.geosylva.repository import GeoSylvaAnalysisRepository
from gsie_api.geosylva.schemas import GeoSylvaAnalysisRequest
from gsie_api.infrastructure.models.geosylva_analysis import GeoSylvaAnalysisJobModel


class GeoSylvaAnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = GeoSylvaAnalysisRepository(session)

    async def submit(
        self,
        account_id: UUID,
        request: GeoSylvaAnalysisRequest,
        *,
        now: datetime,
        trace_id: str,
    ) -> tuple[GeoSylvaAnalysisJobModel, bool]:
        return await self._repository.create_or_get(account_id, request, now=now, trace_id=trace_id)

    async def execute(self, job: GeoSylvaAnalysisJobModel, *, now: datetime) -> None:
        request = GeoSylvaAnalysisRequest.model_validate(job.request_payload)
        preparation = await StationPreparationService(self._session).prepare(
            request.station_id,
            niveaux_declares=dict(request.evidence_levels),
        )
        job.preparation_snapshot = preparation.rapport.model_dump(mode="json")
        job.progress_percent = 35
        await self._session.flush()

        analysis_request = AnalyseRequest(
            requete_id=request.request_id,
            station_id=request.station_id,
            contexte=preparation.contexte,
            regles=preparation.regles,
            qualifications=preparation.qualifications,
            etat_global=preparation.etat_global,
            question=request.question,
            objectif_forestier=request.objective,
            alternatives_demandees=request.alternatives_requested,
            profondeur_max=request.maximum_depth,
        )
        result = await OrchestrationEngine(self._session).analyser_idempotente(
            analysis_request, now
        )
        completed_at = datetime.now(UTC)
        public = build_scientific_result(
            result,
            preparation.rapport,
            requested_capabilities=list(request.requested_capabilities),
            started_at=job.started_at or now,
            completed_at=completed_at,
            trace_id=job.trace_id,
        )
        job.result_payload = public.model_dump(mode="json")
        job.analysis_run_id = result.analyse_id
        job.completed_engines = [
            engine.engine for engine in public.engines if engine.status == "completed"
        ]
        job.unavailable_engines = list(public.unavailable_engines)
        job.warnings = list(public.warnings)
        job.progress_percent = 100
        job.completed_at = completed_at
        job.lease_expires_at = None
        if result.validation.statut is ValidationStatut.bloque:
            job.status = "failed"
            job.error_code = "SCIENTIFIC_VALIDATION_BLOCKED"
            job.error_detail = "La validation scientifique a bloqué la publication complète"
        elif public.unavailable_engines or (
            result.validation.statut is ValidationStatut.partiellement_valide
        ):
            job.status = "partial"
        else:
            job.status = "completed"
        await self._session.flush()

    async def mark_failure(
        self,
        job: GeoSylvaAnalysisJobModel,
        *,
        error_code: str,
        public_detail: str,
        now: datetime,
        retryable: bool,
    ) -> None:
        if retryable and job.attempt_count < 3:
            job.status = "pending"
            job.next_attempt_at = now + timedelta(seconds=2**job.attempt_count)
            job.lease_expires_at = None
            job.error_code = error_code
            return
        job.status = "failed"
        job.progress_percent = 100
        job.error_code = error_code[:100]
        job.error_detail = public_detail[:2000]
        job.completed_at = now
        job.lease_expires_at = None


__all__ = ["GeoSylvaAnalysisService"]

"""Worker durable des analyses GeoSylva."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime

from gsie_api.core.logging import get_logger, setup_logging
from gsie_api.engines.orchestration.hydration import HydratationVideError, StationIntrouvableError
from gsie_api.engines.orchestration.preparation import PreparationError
from gsie_api.geosylva.repository import GeoSylvaAnalysisRepository
from gsie_api.geosylva.service import GeoSylvaAnalysisService
from gsie_api.infrastructure.database import async_session_factory
from gsie_api.outbox_health import write_worker_heartbeat

logger = get_logger("gsie_api.geosylva.worker")


async def process_next() -> bool:
    """Réserve puis traite un job ; le bail permet sa reprise après un crash."""

    async with async_session_factory() as claim_session:
        job = await GeoSylvaAnalysisRepository(claim_session).claim_next(now=datetime.now(UTC))
        if job is None:
            await claim_session.commit()
            return False
        analysis_id = job.id
        await claim_session.commit()

    async with async_session_factory() as session:
        repository = GeoSylvaAnalysisRepository(session)
        claimed = await repository.get(analysis_id)
        if claimed is None:
            return False
        service = GeoSylvaAnalysisService(session)
        try:
            await service.execute(claimed, now=claimed.started_at or datetime.now(UTC))
        except (StationIntrouvableError, HydratationVideError, PreparationError) as exc:
            await service.mark_failure(
                claimed,
                error_code=type(exc).__name__,
                public_detail=str(exc),
                now=datetime.now(UTC),
                retryable=False,
            )
        except Exception as exc:
            logger.error(
                "geosylva_analysis_failed",
                analysis_id=str(analysis_id),
                error_type=type(exc).__name__,
            )
            await service.mark_failure(
                claimed,
                error_code=type(exc).__name__,
                public_detail="Échec technique temporaire de l'analyse",
                now=datetime.now(UTC),
                retryable=True,
            )
        await session.commit()
        return True


async def run() -> None:
    setup_logging("INFO", "worker")
    while True:
        processed = await process_next()
        write_worker_heartbeat(os.getenv("GSIE_GEOSYLVA_WORKER_HEALTHCHECK_PATH"))
        if not processed:
            await asyncio.sleep(1.0)


if __name__ == "__main__":
    asyncio.run(run())

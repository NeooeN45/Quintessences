"""Worker de livraison transactionnelle des événements outbox (ADR-005)."""

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger, setup_logging
from gsie_api.infrastructure.database import async_session_factory
from gsie_api.infrastructure.models.outbox import OutboxEvent
from gsie_api.websocket.manager import manager as ws_manager

Publisher = Callable[[str, dict[str, Any]], Awaitable[None]]

logger = get_logger("gsie_api.outbox_worker")
_settings = get_settings()


async def _publish_to_redis(channel: str, payload: dict[str, Any]) -> None:
    """Publie via Redis et échoue si le fan-out distribué est indisponible."""
    await ws_manager.broadcast_event(channel, payload, require_redis=True)


async def deliver_outbox_batch(
    session: AsyncSession,
    *,
    publisher: Publisher = _publish_to_redis,
    batch_size: int | None = None,
) -> int:
    """Livre un lot avec verrouillage concurrent et sémantique au moins une fois."""
    limit = batch_size or _settings.outbox_batch_size
    statement = (
        select(OutboxEvent)
        .where(OutboxEvent.status == "pending")
        .order_by(OutboxEvent.created_at, OutboxEvent.id)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    events = (await session.execute(statement)).scalars().all()
    delivered = 0

    for event in events:
        try:
            await publisher(event.aggregate_type, event.payload)
        except Exception as exc:
            logger.warning(
                "outbox_publish_failed",
                event_id=str(event.id),
                event_type=event.event_type,
                error_type=type(exc).__name__,
            )
            continue
        event.status = "published"
        event.published_at = datetime.now(UTC)
        delivered += 1

    await session.commit()
    return delivered


async def run_worker() -> None:
    """Traite continuellement l'outbox jusqu'à l'arrêt du processus."""
    setup_logging(_settings.log_level, _settings.environment)
    logger.info("outbox_worker_started")

    try:
        while True:
            delivered = 0
            async with async_session_factory() as session:
                try:
                    delivered = await deliver_outbox_batch(session)
                except asyncio.CancelledError:
                    await session.rollback()
                    raise
                except Exception:
                    await session.rollback()
                    logger.exception("outbox_batch_failed")
            if delivered == 0:
                await asyncio.sleep(_settings.outbox_poll_interval_seconds)
    finally:
        await ws_manager.shutdown()
        logger.info("outbox_worker_stopped")


def main() -> None:
    """Point d'entrée du service Docker outbox-worker."""
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run_worker())


if __name__ == "__main__":
    main()

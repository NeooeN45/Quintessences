"""Worker de finalisation des suppressions de comptes arrivées à échéance.

Le worker n'expose aucune route HTTP. La purge bornée et idempotente est
exécutée par la fonction PostgreSQL installée par la migration 20260826_0055.
Le verrouillage ``FOR UPDATE SKIP LOCKED`` dans cette fonction permet de
lancer plusieurs instances sans traiter deux fois le même compte.
"""

from __future__ import annotations

import asyncio
import contextlib
import sys

from sqlalchemy import text

from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger, setup_logging
from gsie_api.infrastructure.database import async_session_factory
from gsie_api.outbox_health import write_worker_heartbeat

_settings = get_settings()
logger = get_logger("gsie_api.account_deletion_worker")


async def finalize_due_accounts(batch_size: int | None = None) -> int:
    """Finalise un lot de comptes échus et retourne le nombre traité."""
    limit = batch_size or _settings.account_deletion_batch_size
    async with async_session_factory() as session:
        try:
            result = await session.execute(
                text(
                    "SELECT gsie_rgpd_identites.finalize_due_account_deletions(:batch_size)"
                ),
                {"batch_size": limit},
            )
            processed = int(result.scalar_one() or 0)
            await session.commit()
        except BaseException:
            await session.rollback()
            raise
    return processed


async def run_once() -> int:
    """Exécute un cycle et écrit la sonde après commit réussi."""
    processed = await finalize_due_accounts()
    write_worker_heartbeat(_settings.account_deletion_healthcheck_path)
    logger.info("account_deletion_cycle_succeeded", processed=processed)
    return processed


async def run_worker() -> None:
    """Traite les comptes échus jusqu'à l'arrêt du processus."""
    setup_logging(_settings.log_level, _settings.environment)
    if not _settings.account_deletion_worker_enabled:
        logger.info("account_deletion_worker_disabled")
        return

    logger.info(
        "account_deletion_worker_started",
        batch_size=_settings.account_deletion_batch_size,
        poll_interval_seconds=_settings.account_deletion_poll_interval_seconds,
    )
    try:
        while True:
            try:
                processed = await run_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("account_deletion_cycle_failed")
                processed = 0
            if processed < _settings.account_deletion_batch_size:
                await asyncio.sleep(_settings.account_deletion_poll_interval_seconds)
    finally:
        logger.info("account_deletion_worker_stopped")


def main() -> None:
    """Point d'entrée Docker ; ``--once`` sert à une recette opérée."""
    with contextlib.suppress(KeyboardInterrupt):
        if "--once" in sys.argv[1:]:
            asyncio.run(run_once())
        else:
            asyncio.run(run_worker())


if __name__ == "__main__":
    main()

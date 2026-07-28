"""Worker de livraison transactionnelle des événements outbox (ADR-005).

Garanties tenues par ce module :

- **au moins une fois** — un événement n'est marqué `published` qu'après le
  retour du publisher, dans la même transaction ; une panne entre les deux
  rejoue l'événement avec le **même** `event_id`, jamais un nouveau ;
- **pas de boucle serrée** — un échec repousse `next_attempt_at` selon un
  backoff exponentiel borné et bruité ; le worker ne resélectionne que les
  événements arrivés à échéance ;
- **pas de famine** — un événement empoisonné sort de la fenêtre de lot dès
  son premier échec, puis part en lettre morte après `outbox_max_attempts`
  tentatives ; les événements sains continuent de progresser ;
- **pas de fuite** — seul un code d'erreur normalisé est persisté, jamais un
  message ni une traceback : ils peuvent contenir une URL Redis avec mot de
  passe.
"""

import asyncio
import contextlib
import random
import re
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from prometheus_client import Counter, Gauge
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger, setup_logging
from gsie_api.infrastructure.database import async_session_factory
from gsie_api.infrastructure.models.outbox import (
    OUTBOX_STATUS_DEAD_LETTER,
    OUTBOX_STATUS_PENDING,
    OUTBOX_STATUS_PUBLISHED,
    OutboxEvent,
)
from gsie_api.websocket.manager import manager as ws_manager

Publisher = Callable[[str, dict[str, Any]], Awaitable[None]]
Clock = Callable[[], datetime]
Jitter = Callable[[], float]

logger = get_logger("gsie_api.outbox_worker")
_settings = get_settings()

# Codes d'erreur : identifiants courts et stables, jamais de contenu libre.
_ERROR_CODE_PATTERN = re.compile(r"[^A-Za-z0-9_]")
_ERROR_CODE_MAX_LENGTH = 100

# --- Métriques Prometheus -----------------------------------------------------

OUTBOX_PUBLISHED = Counter(
    "gsie_outbox_events_published_total",
    "Événements d'outbox publiés avec succès.",
    ["aggregate_type"],
)
OUTBOX_FAILURES = Counter(
    "gsie_outbox_publish_failures_total",
    "Échecs de publication d'un événement d'outbox.",
    ["error_code"],
)
OUTBOX_DEAD_LETTERED = Counter(
    "gsie_outbox_dead_lettered_total",
    "Événements basculés en lettre morte après épuisement des tentatives.",
    ["error_code"],
)
OUTBOX_REQUEUED = Counter(
    "gsie_outbox_requeued_total",
    "Événements en lettre morte remis en file par une opération contrôlée.",
)
OUTBOX_PENDING_GAUGE = Gauge(
    "gsie_outbox_pending_events",
    "Événements d'outbox en attente de publication.",
)
OUTBOX_DUE_GAUGE = Gauge(
    "gsie_outbox_due_events",
    "Événements d'outbox en attente et arrivés à échéance.",
)
OUTBOX_DEAD_LETTER_GAUGE = Gauge(
    "gsie_outbox_dead_letter_events",
    "Événements d'outbox en lettre morte, en attente d'arbitrage humain.",
)
OUTBOX_OLDEST_PENDING_AGE = Gauge(
    "gsie_outbox_oldest_pending_age_seconds",
    "Âge du plus ancien événement d'outbox non publié, en secondes.",
)


@dataclass(frozen=True)
class RetryPolicy:
    """Politique de reprise — backoff exponentiel borné avec bruit.

    Le bruit est soustractif : le délai reste dans
    ``[base_delay * (1 - jitter_ratio), base_delay]``. Il ne peut donc jamais
    dépasser le plafond, et un `jitter_ratio` nul rend la politique
    entièrement déterministe — c'est ce qui la rend testable sans horloge
    réelle ni tirage aléatoire.
    """

    max_attempts: int
    base_seconds: float
    max_seconds: float
    jitter_ratio: float

    @classmethod
    def from_settings(cls) -> "RetryPolicy":
        return cls(
            max_attempts=_settings.outbox_max_attempts,
            base_seconds=_settings.outbox_retry_base_seconds,
            max_seconds=_settings.outbox_retry_max_seconds,
            jitter_ratio=_settings.outbox_retry_jitter_ratio,
        )

    def delay_seconds(self, attempt: int, jitter: float = 0.0) -> float:
        """Délai avant la tentative suivante, après `attempt` échecs.

        Args:
            attempt: nombre de tentatives déjà consommées (>= 1).
            jitter: tirage dans [0, 1) — 0 donne le délai maximal du palier.
        """
        exponent = max(attempt - 1, 0)
        # 2**exponent explose vite : on borne l'exposant avant de multiplier
        # pour ne pas calculer un flottant inutilement énorme.
        if exponent > 32:
            base_delay = self.max_seconds
        else:
            base_delay = min(self.base_seconds * (2**exponent), self.max_seconds)
        return base_delay * (1.0 - self.jitter_ratio * jitter)

    def is_exhausted(self, attempt: int) -> bool:
        """Vrai si `attempt` tentatives épuisent le quota."""
        return attempt >= self.max_attempts


@dataclass(frozen=True)
class OutboxStats:
    """Photographie de l'outbox, pour les métriques et l'exploitation."""

    pending: int
    due: int
    dead_letter: int
    oldest_pending_age_seconds: float


def _code_erreur(exc: BaseException) -> str:
    """Réduit une exception à un code stable et anodin.

    Seul le **nom de la classe** est retenu. Le message est écarté par
    construction : il transporte régulièrement l'URL du broker, donc son mot
    de passe (`redis://:motdepasse@...`).
    """
    code = _ERROR_CODE_PATTERN.sub("_", type(exc).__name__)
    return code[:_ERROR_CODE_MAX_LENGTH] or "UnknownError"


async def _publish_to_redis(channel: str, payload: dict[str, Any]) -> None:
    """Publie via Redis et échoue si le fan-out distribué est indisponible."""
    await ws_manager.broadcast_event(channel, payload, require_redis=True)


def _echec(
    event: OutboxEvent,
    exc: BaseException,
    *,
    policy: RetryPolicy,
    moment: datetime,
    jitter: Jitter,
) -> None:
    """Comptabilise un échec : backoff, ou bascule en lettre morte."""
    code = _code_erreur(exc)
    event.attempt_count += 1
    event.last_error_code = code
    OUTBOX_FAILURES.labels(error_code=code).inc()

    if policy.is_exhausted(event.attempt_count):
        event.status = OUTBOX_STATUS_DEAD_LETTER
        event.dead_lettered_at = moment
        OUTBOX_DEAD_LETTERED.labels(error_code=code).inc()
        logger.error(
            "outbox_event_dead_lettered",
            event_id=str(event.id),
            event_type=event.event_type,
            attempt_count=event.attempt_count,
            error_code=code,
        )
        return

    delai = policy.delay_seconds(event.attempt_count, jitter())
    event.next_attempt_at = moment + timedelta(seconds=delai)
    logger.warning(
        "outbox_publish_failed",
        event_id=str(event.id),
        event_type=event.event_type,
        attempt_count=event.attempt_count,
        retry_in_seconds=round(delai, 3),
        error_code=code,
    )


def _select_due_events_statement(limit: int, maintenant: datetime) -> Any:
    """Construit la requête des événements `pending` arrivés à échéance.

    Verrous ignorés (`SKIP LOCKED`) : deux workers concurrents ne traitent
    jamais le même événement, et aucun ne bloque sur l'autre.
    """
    return (
        select(OutboxEvent)
        .where(
            OutboxEvent.status == OUTBOX_STATUS_PENDING,
            OutboxEvent.next_attempt_at <= maintenant,
        )
        .order_by(OutboxEvent.next_attempt_at, OutboxEvent.created_at, OutboxEvent.id)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )


def _marquer_publie(event: OutboxEvent, moment: datetime) -> None:
    """Comptabilise une publication réussie : statut, horodatage, métrique."""
    event.status = OUTBOX_STATUS_PUBLISHED
    event.published_at = moment
    event.attempt_count += 1
    OUTBOX_PUBLISHED.labels(aggregate_type=event.aggregate_type).inc()


async def _deliver_single_event(
    event: OutboxEvent,
    *,
    publisher: Publisher,
    policy: RetryPolicy,
    moment: datetime,
    jitter: Jitter,
) -> bool:
    """Livre un événement unique. Retourne True s'il a été publié."""
    try:
        await publisher(event.aggregate_type, event.payload)
    except Exception as exc:
        _echec(event, exc, policy=policy, moment=moment, jitter=jitter)
        return False
    _marquer_publie(event, moment)
    return True


async def deliver_outbox_batch(
    session: AsyncSession,
    *,
    publisher: Publisher = _publish_to_redis,
    batch_size: int | None = None,
    policy: RetryPolicy | None = None,
    clock: Clock | None = None,
    jitter: Jitter | None = None,
) -> int:
    """Livre un lot avec verrouillage concurrent et sémantique au moins une fois.

    Ne sélectionne que les événements `pending` **arrivés à échéance**, verrous
    ignorés (`SKIP LOCKED`) : deux workers concurrents ne traitent jamais le
    même événement, et aucun ne bloque sur l'autre.

    Returns:
        Nombre d'événements effectivement publiés.
    """
    limit = batch_size or _settings.outbox_batch_size
    politique = policy or RetryPolicy.from_settings()
    maintenant = (clock or _maintenant)()
    tirage = jitter or random.random

    statement = _select_due_events_statement(limit, maintenant)
    events = (await session.execute(statement)).scalars().all()

    delivered = 0
    for event in events:
        if await _deliver_single_event(
            event, publisher=publisher, policy=politique, moment=maintenant, jitter=tirage
        ):
            delivered += 1

    await session.commit()
    return delivered


async def collect_outbox_stats(
    session: AsyncSession,
    *,
    clock: Clock | None = None,
) -> OutboxStats:
    """Agrège l'état de l'outbox et met à jour les jauges Prometheus."""
    maintenant = (clock or _maintenant)()
    resultat = (
        await session.execute(
            select(
                func.count().filter(OutboxEvent.status == OUTBOX_STATUS_PENDING),
                func.count().filter(
                    OutboxEvent.status == OUTBOX_STATUS_PENDING,
                    OutboxEvent.next_attempt_at <= maintenant,
                ),
                func.count().filter(OutboxEvent.status == OUTBOX_STATUS_DEAD_LETTER),
                func.min(OutboxEvent.created_at).filter(
                    OutboxEvent.status != OUTBOX_STATUS_PUBLISHED
                ),
            ).select_from(OutboxEvent)
        )
    ).one()

    pending, due, dead_letter, plus_ancien = resultat
    age = 0.0
    if plus_ancien is not None:
        # SQLite restitue des datetimes naïfs : on les rattache à UTC plutôt
        # que de laisser la soustraction lever.
        reference = (
            plus_ancien if plus_ancien.tzinfo is not None else plus_ancien.replace(tzinfo=UTC)
        )
        age = max((maintenant - reference).total_seconds(), 0.0)

    stats = OutboxStats(
        pending=int(pending or 0),
        due=int(due or 0),
        dead_letter=int(dead_letter or 0),
        oldest_pending_age_seconds=age,
    )
    OUTBOX_PENDING_GAUGE.set(stats.pending)
    OUTBOX_DUE_GAUGE.set(stats.due)
    OUTBOX_DEAD_LETTER_GAUGE.set(stats.dead_letter)
    OUTBOX_OLDEST_PENDING_AGE.set(stats.oldest_pending_age_seconds)
    return stats


def _valider_requete_requeue(
    event_ids: Sequence[UUID] | None, limit: int | None, reason: str
) -> None:
    """Rejette une demande de ré-enfilement mal formée (fail fast)."""
    if event_ids is None and limit is None:
        raise ValueError(
            "Ré-enfilement refusé : préciser event_ids ou limit "
            "(un ré-enfilement massif implicite masquerait la cause)"
        )
    if not reason.strip():
        raise ValueError("Ré-enfilement refusé : reason est obligatoire (traçabilité CON-010)")


def _select_dead_letters_statement(event_ids: Sequence[UUID] | None, limit: int | None) -> Any:
    """Construit la requête des événements en lettre morte à ré-enfiler."""
    statement = select(OutboxEvent).where(OutboxEvent.status == OUTBOX_STATUS_DEAD_LETTER)
    if event_ids is not None:
        statement = statement.where(OutboxEvent.id.in_(list(event_ids)))
    statement = statement.order_by(OutboxEvent.created_at, OutboxEvent.id)
    if limit is not None:
        statement = statement.limit(limit)
    return statement.with_for_update(skip_locked=True)


def _reset_for_retry(event: OutboxEvent, moment: datetime) -> None:
    """Remet un événement en lettre morte à l'état `pending`, prêt à rejouer."""
    event.status = OUTBOX_STATUS_PENDING
    event.attempt_count = 0
    event.next_attempt_at = moment
    event.dead_lettered_at = None


def _log_requeue_outcome(events: Sequence[OutboxEvent], reason: str) -> None:
    """Journalise et comptabilise un ré-enfilement effectif (traçabilité CON-010)."""
    if not events:
        return
    OUTBOX_REQUEUED.inc(len(events))
    logger.info(
        "outbox_dead_letters_requeued",
        count=len(events),
        reason=reason,
        event_ids=[str(event.id) for event in events],
    )


async def requeue_dead_letters(
    session: AsyncSession,
    *,
    event_ids: Sequence[UUID] | None = None,
    limit: int | None = None,
    reason: str,
    clock: Clock | None = None,
) -> int:
    """Remet en file des événements en lettre morte — opération contrôlée.

    Le ré-enfilement est délibérément non automatique : une lettre morte
    signale une cause qui n'a pas disparu d'elle-même. L'appelant doit donc
    désigner explicitement les événements (`event_ids`) ou accepter un
    plafond (`limit`), et motiver l'opération (`reason`), qui est journalisée.

    `id` est conservé : un consommateur ayant déjà vu l'événement avant la
    panne le dédupliquera sur ce même `event_id`.

    Returns:
        Nombre d'événements remis en file.
    """
    _valider_requete_requeue(event_ids, limit, reason)
    if event_ids is not None and not event_ids:
        return 0

    maintenant = (clock or _maintenant)()
    statement = _select_dead_letters_statement(event_ids, limit)
    events = (await session.execute(statement)).scalars().all()

    for event in events:
        _reset_for_retry(event, maintenant)
    await session.commit()

    _log_requeue_outcome(events, reason)
    return len(events)


def _maintenant() -> datetime:
    """Horloge par défaut — isolée pour être remplaçable dans les tests."""
    return datetime.now(UTC)


async def run_worker() -> None:
    """Traite continuellement l'outbox jusqu'à l'arrêt du processus."""
    setup_logging(_settings.log_level, _settings.environment)
    policy = RetryPolicy.from_settings()
    logger.info(
        "outbox_worker_started",
        batch_size=_settings.outbox_batch_size,
        max_attempts=policy.max_attempts,
        retry_base_seconds=policy.base_seconds,
        retry_max_seconds=policy.max_seconds,
    )

    try:
        while True:
            delivered = 0
            async with async_session_factory() as session:
                try:
                    delivered = await deliver_outbox_batch(session, policy=policy)
                    if delivered == 0:
                        # Moment creux : on rafraîchit les jauges sans peser
                        # sur le débit quand un arriéré est en cours de purge.
                        await collect_outbox_stats(session)
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

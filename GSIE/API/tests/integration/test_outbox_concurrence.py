"""Contrat d'intégration de l'outbox sur PostgreSQL réel.

Ce que SQLite ne peut pas prouver : `FOR UPDATE SKIP LOCKED`. Deux workers
concurrents doivent se partager la file sans jamais publier deux fois le même
événement, et sans qu'aucun ne se bloque sur l'autre. Les tests ci-dessous
exigent donc une vraie base PostgreSQL.
"""

import asyncio
from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from gsie_api.infrastructure.models.outbox import (
    OUTBOX_STATUS_DEAD_LETTER,
    OUTBOX_STATUS_PENDING,
    OUTBOX_STATUS_PUBLISHED,
    OutboxEvent,
)
from gsie_api.outbox_worker import (
    RetryPolicy,
    collect_outbox_stats,
    deliver_outbox_batch,
    requeue_dead_letters,
)
from tests.conftest import requires_docker

pytestmark = requires_docker

_MAINTENANT = datetime(2026, 7, 26, 12, 0, 0, tzinfo=UTC)
_POLITIQUE = RetryPolicy(max_attempts=3, base_seconds=2.0, max_seconds=60.0, jitter_ratio=0.0)


def _horloge(moment: datetime) -> Callable[[], datetime]:
    """Horloge figée sur un instant — capture la valeur, pas la variable.

    Une lambda définie dans une boucle capturerait la variable et lirait sa
    dernière valeur : tous les appels partageraient alors le même instant.
    """
    return lambda: moment


@pytest.fixture
async def fabrique_session(postgres_url: str) -> AsyncGenerator[Any, None]:
    """Fabrique de sessions sur une table `outbox_event` isolée et vierge."""
    engine = create_async_engine(postgres_url, pool_pre_ping=True)
    table = OutboxEvent.__table__

    async with engine.begin() as conn:
        await conn.run_sync(table.drop, checkfirst=True)
        await conn.run_sync(table.create)

    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(table.drop, checkfirst=True)
    await engine.dispose()


def _evenement(*, aggregate_type: str = "entity", decalage_secondes: int = 0) -> OutboxEvent:
    identifiant = uuid4()
    moment = _MAINTENANT + timedelta(seconds=decalage_secondes)
    return OutboxEvent(
        id=identifiant,
        aggregate_id=uuid4(),
        aggregate_type=aggregate_type,
        event_type="resource.created",
        payload={"event_id": str(identifiant), "data": {}},
        created_at=moment,
        status=OUTBOX_STATUS_PENDING,
        attempt_count=0,
        next_attempt_at=_MAINTENANT,
    )


async def _semer(fabrique: Any, evenements: list[OutboxEvent]) -> None:
    async with fabrique() as session:
        session.add_all(evenements)
        await session.commit()


class TestConcurrenceSkipLocked:
    """Deux workers se partagent la file sans double marquage."""

    @pytest.mark.asyncio
    async def test_should_not_publish_same_event_twice(self, fabrique_session: Any) -> None:
        await _semer(fabrique_session, [_evenement(decalage_secondes=i) for i in range(20)])
        publies: list[str] = []
        depart = asyncio.Event()

        async def worker() -> int:
            async with fabrique_session() as session:

                async def publier(canal: str, payload: dict[str, Any]) -> None:
                    publies.append(payload["event_id"])

                await depart.wait()
                return await deliver_outbox_batch(
                    session,
                    publisher=publier,
                    batch_size=20,
                    policy=_POLITIQUE,
                    clock=lambda: _MAINTENANT,
                )

        taches = [asyncio.create_task(worker()) for _ in range(2)]
        await asyncio.sleep(0)
        depart.set()
        livres = await asyncio.gather(*taches)

        # Chaque événement est publié une fois exactement : SKIP LOCKED a
        # partagé la file au lieu de la dupliquer.
        assert sum(livres) == 20
        assert len(publies) == 20
        assert len(set(publies)) == 20

        async with fabrique_session() as session:
            statuts = (await session.execute(select(OutboxEvent.status))).scalars().all()
        assert set(statuts) == {OUTBOX_STATUS_PUBLISHED}

    @pytest.mark.asyncio
    async def test_should_not_block_second_worker_on_locked_rows(
        self, fabrique_session: Any
    ) -> None:
        """Le second worker saute les lignes verrouillées au lieu d'attendre."""
        await _semer(fabrique_session, [_evenement(decalage_secondes=i) for i in range(4)])

        async with fabrique_session() as premier:
            verrouilles = (
                (
                    await premier.execute(
                        select(OutboxEvent)
                        .where(OutboxEvent.status == OUTBOX_STATUS_PENDING)
                        .order_by(OutboxEvent.created_at)
                        .limit(2)
                        .with_for_update(skip_locked=True)
                    )
                )
                .scalars()
                .all()
            )
            assert len(verrouilles) == 2

            async with fabrique_session() as second:
                livres = await asyncio.wait_for(
                    deliver_outbox_batch(
                        second,
                        publisher=AsyncMock(),
                        batch_size=10,
                        policy=_POLITIQUE,
                        clock=lambda: _MAINTENANT,
                    ),
                    timeout=10,
                )

            await premier.rollback()

        # Les 2 lignes verrouillées ont été sautées, les 2 autres publiées.
        assert livres == 2


class TestPoisonEtLettreMortePostgres:
    """Un événement empoisonné ne retient pas la file sur PostgreSQL."""

    @pytest.mark.asyncio
    async def test_should_drain_healthy_events_while_poison_backs_off(
        self, fabrique_session: Any
    ) -> None:
        poison = _evenement(aggregate_type="poison", decalage_secondes=-10)
        sains = [_evenement(decalage_secondes=i) for i in range(3)]
        await _semer(fabrique_session, [poison, *sains])

        async def publier(canal: str, payload: dict[str, Any]) -> None:
            if canal == "poison":
                raise RuntimeError("payload irrecevable")

        # Lot de taille 1 : sans échéance, le poison monopoliserait la file.
        livres = 0
        async with fabrique_session() as session:
            for _ in range(4):
                livres += await deliver_outbox_batch(
                    session,
                    publisher=publier,
                    batch_size=1,
                    policy=_POLITIQUE,
                    clock=lambda: _MAINTENANT,
                )

        assert livres == 3
        async with fabrique_session() as session:
            restant = (
                await session.execute(
                    select(OutboxEvent).where(OutboxEvent.aggregate_type == "poison")
                )
            ).scalar_one()
            publies = (
                (
                    await session.execute(
                        select(OutboxEvent).where(OutboxEvent.status == OUTBOX_STATUS_PUBLISHED)
                    )
                )
                .scalars()
                .all()
            )
        assert restant.status == OUTBOX_STATUS_PENDING
        assert restant.attempt_count == 1
        assert len(publies) == 3

    @pytest.mark.asyncio
    async def test_should_dead_letter_then_requeue_with_same_id(
        self, fabrique_session: Any
    ) -> None:
        poison = _evenement(aggregate_type="poison")
        identifiant = poison.id
        await _semer(fabrique_session, [poison])

        async def publier_ko(canal: str, payload: dict[str, Any]) -> None:
            raise ConnectionError("redis://:secret@interne:6379 injoignable")

        moment = _MAINTENANT
        async with fabrique_session() as session:
            for _ in range(_POLITIQUE.max_attempts):
                await deliver_outbox_batch(
                    session, publisher=publier_ko, policy=_POLITIQUE, clock=_horloge(moment)
                )
                moment += timedelta(seconds=_POLITIQUE.max_seconds)

            stats = await collect_outbox_stats(session, clock=lambda: moment)
            mort = (await session.execute(select(OutboxEvent))).scalar_one()

        assert stats.dead_letter == 1
        assert stats.pending == 0
        assert mort.status == OUTBOX_STATUS_DEAD_LETTER
        # Le code d'erreur est un identifiant de classe, pas le message.
        assert mort.last_error_code == "ConnectionError"
        assert "secret" not in str(mort.last_error_code)

        publies: list[str] = []

        async def publier_ok(canal: str, payload: dict[str, Any]) -> None:
            publies.append(payload["event_id"])

        async with fabrique_session() as session:
            remis = await requeue_dead_letters(
                session,
                event_ids=[identifiant],
                reason="incident redis clos",
                clock=lambda: moment,
            )
            livres = await deliver_outbox_batch(
                session, publisher=publier_ok, policy=_POLITIQUE, clock=lambda: moment
            )

        assert remis == 1
        assert livres == 1
        # Rejeu sous le même identifiant : le consommateur peut dédupliquer.
        assert publies == [str(identifiant)]

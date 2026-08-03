"""Tests unitaires — reprise sur échec de l'outbox (backoff, lettre morte).

Horloge et bruit sont injectés : aucun test n'attend, aucun test ne dépend
d'un tirage aléatoire. Ce qui est vérifié ici, ce n'est pas « le worker
retente », c'est qu'il retente **plus tard**, un nombre **borné** de fois, et
qu'un événement empoisonné n'empêche jamais les autres de sortir.
"""

from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.schema import DefaultClause

from gsie_api import outbox_health
from gsie_api.infrastructure.models.outbox import (
    OUTBOX_STATUS_DEAD_LETTER,
    OUTBOX_STATUS_PENDING,
    OUTBOX_STATUS_PUBLISHED,
    OutboxEvent,
)
from gsie_api.outbox_health import worker_heartbeat_is_fresh, write_worker_heartbeat
from gsie_api.outbox_worker import (
    RetryPolicy,
    collect_outbox_stats,
    deliver_outbox_batch,
    requeue_dead_letters,
)

_MAINTENANT = datetime(2026, 7, 26, 12, 0, 0, tzinfo=UTC)

# Politique déterministe : bruit nul, seuil bas pour atteindre la lettre morte
# sans dérouler huit tentatives dans chaque test.
_POLITIQUE = RetryPolicy(
    max_attempts=3,
    base_seconds=2.0,
    max_seconds=60.0,
    jitter_ratio=0.0,
)


def _horloge(moment: datetime) -> Callable[[], datetime]:
    """Horloge figée sur un instant — capture la valeur, pas la variable.

    Une lambda définie dans une boucle capturerait la variable et lirait sa
    dernière valeur : tous les appels partageraient alors le même instant.
    """
    return lambda: moment


@compiles(JSONB, "sqlite")
def _jsonb_to_sqlite(element: Any, compiler: Any, **kw: Any) -> str:
    return "JSON"


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Session SQLite in-memory ne portant que la table `outbox_event`."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    table = OutboxEvent.__table__
    remplaces: list[tuple[Any, Any]] = []
    for col in table.columns:
        if (
            col.server_default is not None
            and str(getattr(col.server_default, "arg", "")) == "now()"
        ):
            remplaces.append((col, col.server_default))
            col.server_default = DefaultClause("CURRENT_TIMESTAMP")

    async with engine.begin() as conn:
        await conn.run_sync(table.create)

    fabrique = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with fabrique() as ouverte:
        yield ouverte

    for col, original in remplaces:
        col.server_default = original
    await engine.dispose()


def _evenement(
    *,
    aggregate_type: str = "entity",
    cree_a: datetime | None = None,
    echeance: datetime | None = None,
) -> OutboxEvent:
    """Construit un événement en attente, échéance déjà atteinte par défaut."""
    identifiant = uuid4()
    moment = cree_a or _MAINTENANT
    return OutboxEvent(
        id=identifiant,
        aggregate_id=uuid4(),
        aggregate_type=aggregate_type,
        event_type="resource.created",
        payload={"event_id": str(identifiant), "data": {}},
        created_at=moment,
        status=OUTBOX_STATUS_PENDING,
        attempt_count=0,
        next_attempt_at=echeance or moment,
    )


async def _relire(session: AsyncSession, event_id: UUID) -> OutboxEvent:
    """Relit un événement depuis la base, sans expirer les autres objets.

    `expire_all()` ferait basculer les objets voisins en chargement paresseux,
    donc en E/S synchrone au milieu d'un test asynchrone.
    """
    resultat = await session.execute(
        select(OutboxEvent)
        .where(OutboxEvent.id == event_id)
        .execution_options(populate_existing=True)
    )
    return resultat.scalar_one()


def _en_utc(moment: datetime | None) -> datetime | None:
    """SQLite restitue des datetimes naïfs : on les rattache à UTC."""
    if moment is None:
        return None
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


class TestBackoff:
    """Le backoff est exponentiel, borné, et déterministe à bruit nul."""

    def test_should_double_delay_at_each_attempt(self) -> None:
        assert _POLITIQUE.delay_seconds(1) == 2.0
        assert _POLITIQUE.delay_seconds(2) == 4.0
        assert _POLITIQUE.delay_seconds(3) == 8.0

    def test_should_cap_delay_at_max(self) -> None:
        assert _POLITIQUE.delay_seconds(20) == 60.0
        # Un compteur aberrant ne doit pas produire un flottant infini.
        assert _POLITIQUE.delay_seconds(10_000) == 60.0

    def test_should_keep_jitter_inside_bounds(self) -> None:
        bruitee = RetryPolicy(
            max_attempts=5, base_seconds=10.0, max_seconds=100.0, jitter_ratio=0.5
        )
        # Le bruit est soustractif : jamais au-dessus du palier, jamais négatif.
        assert bruitee.delay_seconds(1, jitter=0.0) == 10.0
        assert bruitee.delay_seconds(1, jitter=1.0) == 5.0
        assert bruitee.delay_seconds(1, jitter=0.5) == 7.5

    def test_should_never_exceed_cap_even_with_jitter(self) -> None:
        bruitee = RetryPolicy(max_attempts=5, base_seconds=10.0, max_seconds=12.0, jitter_ratio=1.0)
        for tirage in (0.0, 0.25, 0.5, 0.75, 0.999):
            delai = bruitee.delay_seconds(9, jitter=tirage)
            assert 0.0 <= delai <= 12.0


class TestSanteWorker:
    """Le healthcheck reflète un cycle réussi, pas un port HTTP absent."""

    def test_should_write_an_atomic_fresh_heartbeat(self, tmp_path: Path) -> None:
        heartbeat = tmp_path / "worker.heartbeat"

        write_worker_heartbeat(str(heartbeat))

        assert heartbeat.is_file()
        assert not heartbeat.with_suffix(".heartbeat.tmp").exists()
        assert worker_heartbeat_is_fresh(
            str(heartbeat),
            max_age_seconds=30,
            now_epoch=heartbeat.stat().st_mtime + 29,
        )

    def test_should_reject_missing_or_stale_heartbeat(self, tmp_path: Path) -> None:
        heartbeat = tmp_path / "worker.heartbeat"
        assert not worker_heartbeat_is_fresh(str(heartbeat), max_age_seconds=30)

        write_worker_heartbeat(str(heartbeat))
        assert not worker_heartbeat_is_fresh(
            str(heartbeat),
            max_age_seconds=30,
            now_epoch=heartbeat.stat().st_mtime + 31,
        )

    @pytest.mark.parametrize(("fresh", "exit_code"), [(True, 0), (False, 1)])
    def test_should_expose_lightweight_healthcheck_as_process_exit_code(
        self,
        fresh: bool,
        exit_code: int,
    ) -> None:
        with (
            patch("gsie_api.outbox_health.worker_heartbeat_is_fresh", return_value=fresh),
            pytest.raises(SystemExit) as raised,
        ):
            outbox_health.main()

        assert raised.value.code == exit_code

    @pytest.mark.parametrize("maximum", ["0", "301", "nan", "infinite"])
    def test_should_reject_invalid_maximum_age_from_environment(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        maximum: str,
    ) -> None:
        heartbeat = tmp_path / "worker.heartbeat"
        write_worker_heartbeat(str(heartbeat))
        monkeypatch.setenv("GSIE_OUTBOX_HEALTHCHECK_PATH", str(heartbeat))
        monkeypatch.setenv("GSIE_OUTBOX_HEALTHCHECK_MAX_AGE_SECONDS", maximum)

        assert not worker_heartbeat_is_fresh()


class TestEcheance:
    """Un échec repousse l'échéance — pas de boucle de retry serrée."""

    @pytest.mark.asyncio
    async def test_should_postpone_next_attempt_after_failure(self, session: AsyncSession) -> None:
        evenement = _evenement()
        session.add(evenement)
        await session.commit()

        delivered = await deliver_outbox_batch(
            session,
            publisher=AsyncMock(side_effect=RuntimeError("redis indisponible")),
            policy=_POLITIQUE,
            clock=lambda: _MAINTENANT,
        )

        relu = await _relire(session, evenement.id)
        assert delivered == 0
        assert relu.status == OUTBOX_STATUS_PENDING
        assert relu.attempt_count == 1
        echeance = _en_utc(relu.next_attempt_at)
        assert echeance is not None
        assert echeance == _MAINTENANT + timedelta(seconds=_POLITIQUE.base_seconds)
        assert relu.published_at is None

    @pytest.mark.asyncio
    async def test_should_not_reselect_event_before_due_date(self, session: AsyncSession) -> None:
        """Immédiatement après un échec, l'événement n'est plus éligible."""
        evenement = _evenement()
        session.add(evenement)
        await session.commit()
        publisher = AsyncMock(side_effect=RuntimeError("panne"))

        await deliver_outbox_batch(
            session, publisher=publisher, policy=_POLITIQUE, clock=lambda: _MAINTENANT
        )
        await deliver_outbox_batch(
            session, publisher=publisher, policy=_POLITIQUE, clock=lambda: _MAINTENANT
        )

        # Une seule tentative consommée malgré deux passages du worker.
        relu = await _relire(session, evenement.id)
        assert publisher.await_count == 1
        assert relu.attempt_count == 1

    @pytest.mark.asyncio
    async def test_should_reselect_event_once_due(self, session: AsyncSession) -> None:
        evenement = _evenement()
        session.add(evenement)
        await session.commit()
        publisher = AsyncMock(side_effect=RuntimeError("panne"))

        await deliver_outbox_batch(
            session, publisher=publisher, policy=_POLITIQUE, clock=lambda: _MAINTENANT
        )
        plus_tard = _MAINTENANT + timedelta(seconds=10)
        await deliver_outbox_batch(
            session, publisher=publisher, policy=_POLITIQUE, clock=lambda: plus_tard
        )

        relu = await _relire(session, evenement.id)
        assert publisher.await_count == 2
        assert relu.attempt_count == 2


class TestPoisonEvent:
    """Un événement empoisonné n'affame jamais les événements sains."""

    @pytest.mark.asyncio
    async def test_should_deliver_healthy_event_despite_poison_in_same_batch(
        self, session: AsyncSession
    ) -> None:
        poison = _evenement(aggregate_type="poison")
        sain = _evenement(aggregate_type="entity")
        id_poison, id_sain = poison.id, sain.id
        session.add_all([poison, sain])
        await session.commit()

        async def publier(canal: str, payload: dict[str, Any]) -> None:
            if canal == "poison":
                raise RuntimeError("payload irrecevable")

        delivered = await deliver_outbox_batch(
            session, publisher=publier, policy=_POLITIQUE, clock=lambda: _MAINTENANT
        )

        assert delivered == 1
        assert (await _relire(session, id_sain)).status == OUTBOX_STATUS_PUBLISHED
        assert (await _relire(session, id_poison)).status == OUTBOX_STATUS_PENDING

    @pytest.mark.asyncio
    async def test_should_let_later_events_progress_while_poison_waits(
        self, session: AsyncSession
    ) -> None:
        """Avec un lot de taille 1, le poison ne bloque pas la tête de file.

        C'est le scénario de famine : avant l'échéance, l'événement en échec
        était resélectionné en boucle et le lot ne contenait jamais rien
        d'autre.
        """
        poison = _evenement(aggregate_type="poison", cree_a=_MAINTENANT)
        # Créé juste après, mais déjà éligible : c'est bien la position dans la
        # file, et non l'échéance, qui le mettait en second.
        suivant = _evenement(
            aggregate_type="entity",
            cree_a=_MAINTENANT + timedelta(seconds=1),
            echeance=_MAINTENANT,
        )
        id_suivant = suivant.id
        session.add_all([poison, suivant])
        await session.commit()

        async def publier(canal: str, payload: dict[str, Any]) -> None:
            if canal == "poison":
                raise RuntimeError("payload irrecevable")

        # 1er passage : le poison occupe le lot unique et échoue.
        assert (
            await deliver_outbox_batch(
                session,
                publisher=publier,
                batch_size=1,
                policy=_POLITIQUE,
                clock=lambda: _MAINTENANT,
            )
            == 0
        )
        # 2e passage, même instant : le poison n'est plus à échéance, le lot
        # revient à l'événement sain.
        assert (
            await deliver_outbox_batch(
                session,
                publisher=publier,
                batch_size=1,
                policy=_POLITIQUE,
                clock=lambda: _MAINTENANT,
            )
            == 1
        )

        assert (await _relire(session, id_suivant)).status == OUTBOX_STATUS_PUBLISHED


class TestDeadLetter:
    """Après N échecs, l'événement sort de la file au lieu d'y tourner."""

    @pytest.mark.asyncio
    async def test_should_dead_letter_after_max_attempts(self, session: AsyncSession) -> None:
        evenement = _evenement()
        session.add(evenement)
        await session.commit()
        publisher = AsyncMock(side_effect=RuntimeError("panne permanente"))

        moment = _MAINTENANT
        for _ in range(_POLITIQUE.max_attempts):
            await deliver_outbox_batch(
                session, publisher=publisher, policy=_POLITIQUE, clock=_horloge(moment)
            )
            moment += timedelta(seconds=_POLITIQUE.max_seconds)

        relu = await _relire(session, evenement.id)
        assert relu.status == OUTBOX_STATUS_DEAD_LETTER
        assert relu.attempt_count == _POLITIQUE.max_attempts
        assert relu.dead_lettered_at is not None
        assert relu.published_at is None

    @pytest.mark.asyncio
    async def test_should_stop_selecting_dead_lettered_event(self, session: AsyncSession) -> None:
        evenement = _evenement()
        session.add(evenement)
        await session.commit()
        publisher = AsyncMock(side_effect=RuntimeError("panne permanente"))

        moment = _MAINTENANT
        for _ in range(_POLITIQUE.max_attempts):
            await deliver_outbox_batch(
                session, publisher=publisher, policy=_POLITIQUE, clock=_horloge(moment)
            )
            moment += timedelta(seconds=_POLITIQUE.max_seconds)
        tentatives_avant = publisher.await_count

        tres_tard = moment + timedelta(days=365)
        await deliver_outbox_batch(
            session, publisher=publisher, policy=_POLITIQUE, clock=lambda: tres_tard
        )

        assert publisher.await_count == tentatives_avant

    @pytest.mark.asyncio
    async def test_should_not_block_healthy_events_once_dead_lettered(
        self, session: AsyncSession
    ) -> None:
        poison = _evenement(aggregate_type="poison")
        session.add(poison)
        await session.commit()

        async def publier(canal: str, payload: dict[str, Any]) -> None:
            if canal == "poison":
                raise RuntimeError("payload irrecevable")

        moment = _MAINTENANT
        for _ in range(_POLITIQUE.max_attempts):
            await deliver_outbox_batch(
                session, publisher=publier, batch_size=1, policy=_POLITIQUE, clock=_horloge(moment)
            )
            moment += timedelta(seconds=_POLITIQUE.max_seconds)

        sain = _evenement(aggregate_type="entity", cree_a=moment, echeance=moment)
        session.add(sain)
        await session.commit()
        id_sain = sain.id
        delivered = await deliver_outbox_batch(
            session,
            publisher=publier,
            batch_size=1,
            policy=_POLITIQUE,
            clock=_horloge(moment),
        )

        assert delivered == 1
        assert (await _relire(session, id_sain)).status == OUTBOX_STATUS_PUBLISHED


class TestConfidentialiteDesErreurs:
    """Le journal d'échec ne doit jamais devenir une fuite de secret."""

    @pytest.mark.asyncio
    async def test_should_store_error_class_only(self, session: AsyncSession) -> None:
        evenement = _evenement()
        session.add(evenement)
        await session.commit()
        secret = "redis://:MotDePasseTresSecret@redis.interne:6379/0"

        await deliver_outbox_batch(
            session,
            publisher=AsyncMock(side_effect=ConnectionError(f"echec sur {secret}")),
            policy=_POLITIQUE,
            clock=lambda: _MAINTENANT,
        )

        relu = await _relire(session, evenement.id)
        assert relu.last_error_code == "ConnectionError"
        assert "MotDePasseTresSecret" not in str(relu.last_error_code)
        assert "redis://" not in str(relu.last_error_code)

    @pytest.mark.asyncio
    async def test_should_bound_and_normalise_error_code(self, session: AsyncSession) -> None:
        """Un nom de classe exotique reste un identifiant court et inerte."""

        classe = type("Erreur" + "X" * 500, (RuntimeError,), {})
        evenement = _evenement()
        session.add(evenement)
        await session.commit()

        await deliver_outbox_batch(
            session,
            publisher=AsyncMock(side_effect=classe("peu importe")),
            policy=_POLITIQUE,
            clock=lambda: _MAINTENANT,
        )

        relu = await _relire(session, evenement.id)
        assert relu.last_error_code is not None
        assert len(relu.last_error_code) <= 100
        assert relu.last_error_code.replace("_", "").isalnum()


class TestAuMoinsUneFois:
    """Une panne entre publication et commit rejoue le même événement."""

    @pytest.mark.asyncio
    async def test_should_replay_with_same_event_id_after_crash_before_commit(
        self, session: AsyncSession
    ) -> None:
        evenement = _evenement()
        identifiant = evenement.id
        session.add(evenement)
        await session.commit()

        publies: list[str] = []

        async def publier(canal: str, payload: dict[str, Any]) -> None:
            publies.append(payload["event_id"])

        # Panne simulée : le publisher a réussi, le commit n'a jamais eu lieu.
        with (
            patch.object(session, "commit", side_effect=RuntimeError("panne processus")),
            pytest.raises(RuntimeError, match="panne processus"),
        ):
            await deliver_outbox_batch(
                session, publisher=publier, policy=_POLITIQUE, clock=lambda: _MAINTENANT
            )
        await session.rollback()

        # Le worker redémarre : l'événement est toujours en attente.
        relu = await _relire(session, identifiant)
        assert relu.status == OUTBOX_STATUS_PENDING

        delivered = await deliver_outbox_batch(
            session, publisher=publier, policy=_POLITIQUE, clock=lambda: _MAINTENANT
        )

        assert delivered == 1
        # Deux livraisons, un seul identifiant : le consommateur peut dédupliquer.
        assert publies == [str(identifiant), str(identifiant)]
        assert (await _relire(session, identifiant)).id == identifiant


class TestReenfilement:
    """Le ré-enfilement est explicite, motivé et conserve l'identifiant."""

    @staticmethod
    async def _mettre_en_lettre_morte(session: AsyncSession) -> OutboxEvent:
        evenement = _evenement()
        session.add(evenement)
        await session.commit()
        publisher = AsyncMock(side_effect=RuntimeError("panne"))
        moment = _MAINTENANT
        for _ in range(_POLITIQUE.max_attempts):
            await deliver_outbox_batch(
                session, publisher=publisher, policy=_POLITIQUE, clock=_horloge(moment)
            )
            moment += timedelta(seconds=_POLITIQUE.max_seconds)
        return evenement

    @pytest.mark.asyncio
    async def test_should_refuse_unbounded_requeue(self, session: AsyncSession) -> None:
        """Sans périmètre explicite, le ré-enfilement est refusé."""
        with pytest.raises(ValueError, match="event_ids ou limit"):
            await requeue_dead_letters(session, reason="incident redis resolu")

    @pytest.mark.asyncio
    async def test_should_refuse_requeue_without_reason(self, session: AsyncSession) -> None:
        with pytest.raises(ValueError, match="reason"):
            await requeue_dead_letters(session, limit=10, reason="   ")

    @pytest.mark.asyncio
    async def test_should_requeue_and_republish_with_same_id(self, session: AsyncSession) -> None:
        evenement = await self._mettre_en_lettre_morte(session)
        identifiant = evenement.id

        remis = await requeue_dead_letters(
            session,
            event_ids=[identifiant],
            reason="incident redis resolu — DEC a tracer",
            clock=lambda: _MAINTENANT,
        )

        relu = await _relire(session, identifiant)
        assert remis == 1
        assert relu.status == OUTBOX_STATUS_PENDING
        assert relu.attempt_count == 0
        assert relu.dead_lettered_at is None

        publies: list[str] = []

        async def publier(canal: str, payload: dict[str, Any]) -> None:
            publies.append(payload["event_id"])

        delivered = await deliver_outbox_batch(
            session, publisher=publier, policy=_POLITIQUE, clock=lambda: _MAINTENANT
        )

        assert delivered == 1
        assert publies == [str(identifiant)]

    @pytest.mark.asyncio
    async def test_should_ignore_events_outside_dead_letter(self, session: AsyncSession) -> None:
        """Un événement encore en attente n'est pas « ré-enfilé » par erreur."""
        en_attente = _evenement()
        session.add(en_attente)
        await session.commit()

        remis = await requeue_dead_letters(
            session, event_ids=[en_attente.id], reason="verification de perimetre"
        )

        assert remis == 0
        assert (await _relire(session, en_attente.id)).attempt_count == 0


class TestMetriques:
    """Les compteurs d'exploitation reflètent l'état réel de la file."""

    @pytest.mark.asyncio
    async def test_should_report_pending_due_and_dead_letter(self, session: AsyncSession) -> None:
        a_echeance = _evenement()
        plus_tard = _evenement(echeance=_MAINTENANT + timedelta(hours=1))
        session.add_all([a_echeance, plus_tard])
        await session.commit()

        stats = await collect_outbox_stats(session, clock=lambda: _MAINTENANT)

        assert stats.pending == 2
        assert stats.due == 1
        assert stats.dead_letter == 0

    @pytest.mark.asyncio
    async def test_should_report_dead_letter_count_and_backlog_age(
        self, session: AsyncSession
    ) -> None:
        ancien = _evenement(cree_a=_MAINTENANT - timedelta(minutes=30))
        session.add(ancien)
        await session.commit()
        publisher = AsyncMock(side_effect=RuntimeError("panne"))
        moment = _MAINTENANT
        for _ in range(_POLITIQUE.max_attempts):
            await deliver_outbox_batch(
                session, publisher=publisher, policy=_POLITIQUE, clock=_horloge(moment)
            )
            moment += timedelta(seconds=_POLITIQUE.max_seconds)

        stats = await collect_outbox_stats(session, clock=lambda: _MAINTENANT)

        assert stats.dead_letter == 1
        assert stats.pending == 0
        # L'événement non publié compte toujours dans l'arriéré observé.
        assert stats.oldest_pending_age_seconds == pytest.approx(1800.0, abs=1.0)

    @pytest.mark.asyncio
    async def test_should_report_empty_outbox(self, session: AsyncSession) -> None:
        stats = await collect_outbox_stats(session, clock=lambda: _MAINTENANT)

        assert stats.pending == 0
        assert stats.due == 0
        assert stats.dead_letter == 0
        assert stats.oldest_pending_age_seconds == 0.0

    @pytest.mark.asyncio
    async def test_should_exclude_published_events_from_backlog(
        self, session: AsyncSession
    ) -> None:
        evenement = _evenement(cree_a=_MAINTENANT - timedelta(days=1))
        session.add(evenement)
        await session.commit()

        await deliver_outbox_batch(
            session, publisher=AsyncMock(), policy=_POLITIQUE, clock=lambda: _MAINTENANT
        )
        stats = await collect_outbox_stats(session, clock=lambda: _MAINTENANT)

        assert stats.pending == 0
        assert stats.oldest_pending_age_seconds == 0.0


class TestSelectionDuLot:
    """L'ordre de service reste chronologique à échéance égale."""

    @pytest.mark.asyncio
    async def test_should_serve_oldest_due_event_first(self, session: AsyncSession) -> None:
        recent = _evenement(aggregate_type="recent", cree_a=_MAINTENANT)
        ancien = _evenement(aggregate_type="ancien", cree_a=_MAINTENANT - timedelta(minutes=5))
        ancien.next_attempt_at = _MAINTENANT - timedelta(minutes=5)
        session.add_all([recent, ancien])
        await session.commit()

        canaux: list[str] = []

        async def publier(canal: str, payload: dict[str, Any]) -> None:
            canaux.append(canal)

        await deliver_outbox_batch(
            session, publisher=publier, batch_size=1, policy=_POLITIQUE, clock=lambda: _MAINTENANT
        )

        assert canaux == ["ancien"]

    @pytest.mark.asyncio
    async def test_should_leave_future_events_untouched(self, session: AsyncSession) -> None:
        futur = _evenement(echeance=_MAINTENANT + timedelta(minutes=10))
        session.add(futur)
        await session.commit()
        publisher = AsyncMock()

        delivered = await deliver_outbox_batch(
            session, publisher=publisher, policy=_POLITIQUE, clock=lambda: _MAINTENANT
        )

        assert delivered == 0
        publisher.assert_not_awaited()
        assert (await _relire(session, futur.id)).attempt_count == 0

    @pytest.mark.asyncio
    async def test_should_keep_pending_events_after_partial_batch(
        self, session: AsyncSession
    ) -> None:
        evenements = [_evenement() for _ in range(3)]
        session.add_all(evenements)
        await session.commit()

        delivered = await deliver_outbox_batch(
            session,
            publisher=AsyncMock(),
            batch_size=2,
            policy=_POLITIQUE,
            clock=lambda: _MAINTENANT,
        )
        restants = (
            (
                await session.execute(
                    select(OutboxEvent).where(OutboxEvent.status == OUTBOX_STATUS_PENDING)
                )
            )
            .scalars()
            .all()
        )

        assert delivered == 2
        assert len(restants) == 1

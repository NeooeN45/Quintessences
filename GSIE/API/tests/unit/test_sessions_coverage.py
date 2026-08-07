"""Couverture résiduelle de auth/sessions.py.

``SqlAlchemySessionRepository`` n'était exercé nulle part avec une vraie
session SQLAlchemy (les tests existants passent par ``FakeSessionRepository``
au niveau de ``SessionService``) — d'où la quasi-totalité des lignes
manquantes. On utilise ici la fixture SQLite ``identity_sqlite_session``
(voir tests/conftest.py) pour exécuter le SQL réel sans dépendre de Docker.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from gsie_api.auth.sessions import SessionService, SqlAlchemySessionRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def should_create_session_and_truncate_long_user_agent(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    account_id = uuid4()
    long_user_agent = "Mozilla/5.0 " + ("x" * 600)

    info = await repository.create_session(
        account_id=account_id,
        jti="jti-1",
        refresh_jti="refresh-1",
        device_name="Chrome sur Windows",
        user_agent=long_user_agent,
        ip_address="127.0.0.1",
    )

    assert info.jti == "jti-1"
    assert info.device_name == "Chrome sur Windows"
    assert info.user_agent is not None
    assert len(info.user_agent) == 500


async def should_create_session_with_no_user_agent(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)

    info = await repository.create_session(
        account_id=uuid4(),
        jti="jti-1",
        refresh_jti=None,
        device_name=None,
        user_agent=None,
        ip_address=None,
    )

    assert info.user_agent is None


async def should_list_only_active_sessions_ordered_by_last_seen(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    account_id = uuid4()
    first = await repository.create_session(account_id, "jti-1", "r-1", None, None, None)
    second = await repository.create_session(account_id, "jti-2", "r-2", None, None, None)
    await repository.revoke_session(account_id, first.id)

    sessions = await repository.list_active_sessions(account_id)

    assert [info.id for info in sessions] == [second.id]


async def should_rotate_session_jti_and_refresh_jti(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    account_id = uuid4()
    await repository.create_session(account_id, "jti-1", "r-1", None, None, None)

    rotated = await repository.rotate_session("jti-1", "jti-2", "r-2")

    assert rotated is True
    sessions = await repository.list_active_sessions(account_id)
    assert sessions[0].jti == "jti-2"


async def should_fail_to_rotate_unknown_session(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)

    assert await repository.rotate_session("absent", "jti-2", "r-2") is False


async def should_get_refresh_jti_for_own_session_only(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    account_id = uuid4()
    other_account_id = uuid4()
    info = await repository.create_session(account_id, "jti-1", "refresh-1", None, None, None)

    assert await repository.get_refresh_jti(account_id, info.id) == "refresh-1"
    assert await repository.get_refresh_jti(other_account_id, info.id) is None
    assert await repository.get_refresh_jti(account_id, uuid4()) is None


async def should_list_refresh_jtis_excluding_current_and_null(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    account_id = uuid4()
    await repository.create_session(account_id, "jti-1", "refresh-1", None, None, None)
    await repository.create_session(account_id, "jti-2", "refresh-2", None, None, None)
    # Une session sans refresh_jti (ex. access token seul) ne doit jamais apparaître.
    await repository.create_session(account_id, "jti-3", None, None, None, None)

    jtis = await repository.list_refresh_jtis(account_id, except_jti="jti-1")

    assert sorted(jtis) == ["refresh-2"]


async def should_list_all_refresh_jtis_without_exclusion(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    account_id = uuid4()
    await repository.create_session(account_id, "jti-1", "refresh-1", None, None, None)
    await repository.create_session(account_id, "jti-2", "refresh-2", None, None, None)

    jtis = await repository.list_refresh_jtis(account_id)

    assert sorted(jtis) == ["refresh-1", "refresh-2"]


async def should_revoke_session_once(identity_sqlite_session: AsyncSession) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    account_id = uuid4()
    info = await repository.create_session(account_id, "jti-1", "r-1", None, None, None)

    assert await repository.revoke_session(account_id, info.id) is True
    assert await repository.revoke_session(account_id, info.id) is False


async def should_not_revoke_session_of_another_account(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    account_id = uuid4()
    info = await repository.create_session(account_id, "jti-1", "r-1", None, None, None)

    assert await repository.revoke_session(uuid4(), info.id) is False


async def should_revoke_all_sessions_except_current(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    account_id = uuid4()
    await repository.create_session(account_id, "jti-1", "r-1", None, None, None)
    await repository.create_session(account_id, "jti-2", "r-2", None, None, None)

    count = await repository.revoke_all_sessions(account_id, except_jti="jti-1")

    assert count == 1
    remaining = await repository.list_active_sessions(account_id)
    assert [info.jti for info in remaining] == ["jti-1"]


async def should_revoke_all_sessions_without_exclusion(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    account_id = uuid4()
    await repository.create_session(account_id, "jti-1", "r-1", None, None, None)
    await repository.create_session(account_id, "jti-2", "r-2", None, None, None)

    count = await repository.revoke_all_sessions(account_id)

    assert count == 2
    assert await repository.list_active_sessions(account_id) == []


async def should_revoke_by_jti(identity_sqlite_session: AsyncSession) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    account_id = uuid4()
    await repository.create_session(account_id, "jti-1", "r-1", None, None, None)

    assert await repository.revoke_by_jti("jti-1") is True
    assert await repository.revoke_by_jti("jti-1") is False
    assert await repository.revoke_by_jti("absent") is False


async def should_touch_session_and_update_last_seen(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    account_id = uuid4()
    info = await repository.create_session(account_id, "jti-1", "r-1", None, None, None)
    original_last_seen = info.last_seen_at

    await repository.touch_session("jti-1")

    refreshed = await repository.list_active_sessions(account_id)
    assert refreshed[0].last_seen_at >= original_last_seen


# ---------------------------------------------------------------------------
# SessionService — délégation non couverte (rotate_session, get_refresh_jti,
# list_refresh_jtis, revoke_by_jti)
# ---------------------------------------------------------------------------


async def should_delegate_rotate_session_to_repository(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    service = SessionService(repository)
    account_id = uuid4()
    await repository.create_session(account_id, "jti-1", "r-1", None, None, None)

    assert await service.rotate_session("jti-1", "jti-2", "r-2") is True


async def should_delegate_get_refresh_jti_to_repository(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    service = SessionService(repository)
    account_id = uuid4()
    info = await repository.create_session(account_id, "jti-1", "refresh-1", None, None, None)

    assert await service.get_refresh_jti(account_id, info.id) == "refresh-1"


async def should_delegate_list_refresh_jtis_to_repository(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    service = SessionService(repository)
    account_id = uuid4()
    await repository.create_session(account_id, "jti-1", "refresh-1", None, None, None)

    assert await service.list_refresh_jtis(account_id) == ["refresh-1"]


async def should_delegate_revoke_by_jti_to_repository(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemySessionRepository(identity_sqlite_session)
    service = SessionService(repository)
    account_id = uuid4()
    await repository.create_session(account_id, "jti-1", "r-1", None, None, None)

    assert await service.revoke_by_jti("jti-1") is True

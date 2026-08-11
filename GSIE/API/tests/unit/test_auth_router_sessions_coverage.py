"""Couverture résiduelle de auth/router.py — sessions actives et Turnstile.

Complète tests/unit/test_auth_coverage.py et test_auth_hardening.py sur les
branches encore non exercées :
- ``get_session_service`` (dépendance FastAPI)
- ``_revoke_account_sessions`` / ``_rotate_active_session`` (helpers DB)
- la révocation en cascade après réutilisation d'un refresh token *lié à une
  session active* (``session_jti`` présent dans les claims)
- l'échec de rotation de session active pendant /auth/refresh
- POST /auth/turnstile/verify
"""

from __future__ import annotations

from collections.abc import Generator  # noqa: TC003
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.auth import router as auth_router
from gsie_api.auth.sessions import SessionService, SqlAlchemySessionRepository

auth_router._settings.auth_dev_login_enabled = True
auth_router._settings.auth_dev_password = "changeme"


@pytest.fixture
def client(mock_lifespan: object) -> Generator[TestClient, None, None]:
    with TestClient(create_app()) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# get_session_service — ligne 52
# ---------------------------------------------------------------------------


async def should_build_session_service_from_db_session() -> None:
    fake_session = MagicMock()

    service = await auth_router.get_session_service(fake_session)

    assert isinstance(service, SessionService)
    assert isinstance(service._repository, SqlAlchemySessionRepository)
    assert service._repository._session is fake_session


# ---------------------------------------------------------------------------
# _revoke_account_sessions — lignes 62-77
# ---------------------------------------------------------------------------


async def should_do_nothing_when_subject_is_not_a_uuid() -> None:
    store = AsyncMock()

    await auth_router._revoke_account_sessions("not-a-uuid", store)

    store.revoke.assert_not_called()


async def should_revoke_all_sessions_and_their_refresh_tokens() -> None:
    account_id = uuid4()
    store = AsyncMock()
    session = MagicMock()
    session.commit = AsyncMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=None)
    fake_repo = MagicMock()
    fake_repo.list_refresh_jtis = AsyncMock(return_value=["refresh-a", "refresh-b"])
    fake_repo.revoke_all_sessions = AsyncMock(return_value=2)

    with (
        patch.object(
            auth_router.database_infrastructure,
            "async_session_factory",
            return_value=context,
        ),
        patch.object(auth_router, "SqlAlchemySessionRepository", return_value=fake_repo),
    ):
        await auth_router._revoke_account_sessions(str(account_id), store)

    fake_repo.list_refresh_jtis.assert_awaited_once_with(account_id, None)
    fake_repo.revoke_all_sessions.assert_awaited_once_with(account_id, None)
    session.commit.assert_awaited_once()
    assert store.revoke.await_count == 2
    store.revoke.assert_any_await("refresh-a")
    store.revoke.assert_any_await("refresh-b")


# ---------------------------------------------------------------------------
# _rotate_active_session — lignes 80-90
# ---------------------------------------------------------------------------


async def should_rotate_active_session_and_commit() -> None:
    session = MagicMock()
    session.commit = AsyncMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=None)
    fake_repo = MagicMock()
    fake_repo.rotate_session = AsyncMock(return_value=True)

    with (
        patch.object(
            auth_router.database_infrastructure,
            "async_session_factory",
            return_value=context,
        ),
        patch.object(auth_router, "SqlAlchemySessionRepository", return_value=fake_repo),
    ):
        result = await auth_router._rotate_active_session("current", "new", "new-refresh")

    assert result is True
    fake_repo.rotate_session.assert_awaited_once_with("current", "new", "new-refresh")
    session.commit.assert_awaited_once()


async def should_report_false_when_active_session_rotation_finds_nothing() -> None:
    session = MagicMock()
    session.commit = AsyncMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=None)
    fake_repo = MagicMock()
    fake_repo.rotate_session = AsyncMock(return_value=False)

    with (
        patch.object(
            auth_router.database_infrastructure,
            "async_session_factory",
            return_value=context,
        ),
        patch.object(auth_router, "SqlAlchemySessionRepository", return_value=fake_repo),
    ):
        result = await auth_router._rotate_active_session("current", "new", "new-refresh")

    assert result is False


# ---------------------------------------------------------------------------
# /auth/refresh — révocation en cascade sur réutilisation avec session_jti
# (ligne 330) et échec de rotation de session active (lignes 341-349)
# ---------------------------------------------------------------------------


def should_revoke_account_sessions_when_reused_token_had_a_session_jti(
    client: TestClient,
) -> None:
    from gsie_api.auth.router import get_refresh_token_store as _get_store
    from gsie_api.core.auth import create_refresh_token

    token = create_refresh_token(
        subject=str(auth_router.DEV_USER_ID),
        claims={"roles": ["admin"], "session_jti": "current-session-jti"},
    )
    mock_store = AsyncMock()
    mock_store.rotate = AsyncMock(return_value=False)
    revoke_mock = AsyncMock()
    client.app.dependency_overrides[_get_store] = lambda: mock_store
    try:
        with patch.object(auth_router, "_revoke_account_sessions", revoke_mock):
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
    finally:
        client.app.dependency_overrides.pop(_get_store, None)

    assert response.status_code == 401
    revoke_mock.assert_awaited_once_with(str(auth_router.DEV_USER_ID), mock_store)


def should_not_revoke_account_sessions_when_reused_token_has_no_session_jti(
    client: TestClient,
) -> None:
    """Sans session_jti (ex. token émis avant la fonctionnalité), pas de cascade."""
    from gsie_api.auth.router import get_refresh_token_store as _get_store
    from gsie_api.core.auth import create_refresh_token

    token = create_refresh_token(
        subject=str(auth_router.DEV_USER_ID),
        claims={"roles": ["admin"]},
    )
    mock_store = AsyncMock()
    mock_store.rotate = AsyncMock(return_value=False)
    revoke_mock = AsyncMock()
    client.app.dependency_overrides[_get_store] = lambda: mock_store
    try:
        with patch.object(auth_router, "_revoke_account_sessions", revoke_mock):
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
    finally:
        client.app.dependency_overrides.pop(_get_store, None)

    assert response.status_code == 401
    revoke_mock.assert_not_awaited()


def should_return_401_when_active_session_rotation_fails(client: TestClient) -> None:
    from gsie_api.auth.router import get_refresh_token_store as _get_store
    from gsie_api.core.auth import create_refresh_token

    token = create_refresh_token(
        subject=str(auth_router.DEV_USER_ID),
        claims={"roles": ["admin"], "session_jti": "current-session-jti"},
    )
    mock_store = AsyncMock()
    mock_store.rotate = AsyncMock(return_value=True)
    mock_store.revoke = AsyncMock()
    client.app.dependency_overrides[_get_store] = lambda: mock_store
    try:
        with patch.object(auth_router, "_rotate_active_session", AsyncMock(return_value=False)):
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
    finally:
        client.app.dependency_overrides.pop(_get_store, None)

    assert response.status_code == 401
    assert response.json()["detail"] == "Session révoquée"
    mock_store.revoke.assert_awaited_once()


# ---------------------------------------------------------------------------
# POST /auth/turnstile/verify — lignes 437-447
# ---------------------------------------------------------------------------


def should_return_valid_true_when_turnstile_verification_succeeds(client: TestClient) -> None:
    with patch.object(auth_router.TurnstileClient, "verify", AsyncMock(return_value=True)):
        response = client.post(
            "/api/v1/auth/turnstile/verify",
            json={"token": "un-jeton-turnstile"},
        )

    assert response.status_code == 200
    assert response.json() == {"valid": True}


def should_return_valid_false_when_turnstile_verification_fails(client: TestClient) -> None:
    with patch.object(auth_router.TurnstileClient, "verify", AsyncMock(return_value=False)):
        response = client.post(
            "/api/v1/auth/turnstile/verify",
            json={"token": "un-jeton-invalide"},
        )

    assert response.status_code == 200
    assert response.json() == {"valid": False}

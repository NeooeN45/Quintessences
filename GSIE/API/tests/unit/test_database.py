"""Tests unitaires — base de données (infrastructure/database.py)."""

import contextlib
from unittest.mock import AsyncMock, MagicMock

import pytest

from gsie_api.core.config import Settings
from gsie_api.infrastructure.database import (
    _build_engine_kwargs,
    get_db,
    get_db_rls,
    set_rls_context,
)


def should_include_basic_kwargs_when_building_engine():
    """_build_engine_kwargs doit inclure echo, pool_size, max_overflow, pool_pre_ping."""
    settings = Settings(
        db_echo=True,
        db_pool_size=10,
        db_max_overflow=5,
        db_pgbouncer_mode=False,
        db_ssl_mode="disable",
    )
    kwargs = _build_engine_kwargs(settings)
    assert kwargs["echo"] is True
    assert kwargs["pool_size"] == 10
    assert kwargs["max_overflow"] == 5
    assert kwargs["pool_pre_ping"] is True
    assert "connect_args" not in kwargs


def should_disable_prepared_statements_when_pgbouncer_mode():
    """_build_engine_kwargs doit désactiver les prepared statements en mode PgBouncer."""
    settings = Settings(db_pgbouncer_mode=True, db_ssl_mode="disable")
    kwargs = _build_engine_kwargs(settings)
    assert "connect_args" in kwargs
    assert kwargs["connect_args"]["statement_cache_size"] == 0
    assert kwargs["connect_args"]["prepared_statement_cache_size"] == 0


def should_not_include_connect_args_when_no_pgbouncer():
    """_build_engine_kwargs ne doit pas inclure connect_args sans PgBouncer ni TLS."""
    settings = Settings(db_pgbouncer_mode=False, db_ssl_mode="disable")
    kwargs = _build_engine_kwargs(settings)
    assert "connect_args" not in kwargs


def should_include_ssl_connect_arg_by_default():
    """_build_engine_kwargs doit activer TLS (mode 'prefer') par défaut."""
    settings = Settings(db_pgbouncer_mode=False)
    kwargs = _build_engine_kwargs(settings)
    assert kwargs["connect_args"]["ssl"] == "prefer"


def should_include_ssl_require_in_production_mode():
    """_build_engine_kwargs doit propager db_ssl_mode='require' vers asyncpg."""
    settings = Settings(db_ssl_mode="require")
    kwargs = _build_engine_kwargs(settings)
    assert kwargs["connect_args"]["ssl"] == "require"


def should_combine_pgbouncer_and_ssl_connect_args():
    """_build_engine_kwargs doit combiner PgBouncer et TLS dans connect_args."""
    settings = Settings(db_pgbouncer_mode=True, db_ssl_mode="require")
    kwargs = _build_engine_kwargs(settings)
    assert kwargs["connect_args"]["statement_cache_size"] == 0
    assert kwargs["connect_args"]["ssl"] == "require"


@pytest.mark.asyncio
async def should_rollback_when_exception_raised():
    """get_db doit rollback en cas d'exception pendant la session."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock(side_effect=Exception("DB error"))
    mock_session.rollback = AsyncMock()

    # Mock du context manager async : async_session_factory() doit retourner
    # un objet qui supporte __aenter__ et __aexit__
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_factory = MagicMock(return_value=mock_ctx)

    import gsie_api.infrastructure.database as db_module

    original_factory = db_module.async_session_factory
    db_module.async_session_factory = mock_factory

    try:
        gen = get_db()
        await gen.__anext__()  # yield session
        with contextlib.suppress(Exception):
            await gen.__anext__()  # commit → exception → rollback
        mock_session.rollback.assert_called_once()
    finally:
        db_module.async_session_factory = original_factory


@pytest.mark.asyncio
async def should_set_rls_context_with_user_id_and_roles():
    """set_rls_context doit exécuter SET LOCAL avec user_id et roles."""
    mock_session = AsyncMock()
    await set_rls_context(mock_session, "user-uuid-123", "admin,researcher")
    assert mock_session.execute.call_count == 2
    # Premier appel : SET LOCAL app.current_user_id
    first_call = mock_session.execute.call_args_list[0]
    assert "app.current_user_id" in first_call.args[0].text
    assert first_call.args[1]["uid"] == "user-uuid-123"
    # Second appel : SET LOCAL app.current_user_roles
    second_call = mock_session.execute.call_args_list[1]
    assert "app.current_user_roles" in second_call.args[0].text
    assert second_call.args[1]["roles"] == "admin,researcher"


@pytest.mark.asyncio
async def should_set_rls_context_with_empty_roles_when_no_roles():
    """set_rls_context doit gérer le cas où l'utilisateur n'a pas de rôles."""
    mock_session = AsyncMock()
    await set_rls_context(mock_session, "user-uuid-456", "")
    assert mock_session.execute.call_count == 2
    second_call = mock_session.execute.call_args_list[1]
    assert second_call.args[1]["roles"] == ""


@pytest.mark.asyncio
async def should_inject_rls_context_when_get_db_rls_yields_session():
    """get_db_rls doit injecter le contexte RLS avant de fournir la session."""
    mock_session = AsyncMock()
    mock_session.begin = MagicMock(return_value=AsyncMock())
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_factory = MagicMock(return_value=mock_ctx)

    import gsie_api.infrastructure.database as db_module

    original_factory = db_module.async_session_factory
    db_module.async_session_factory = mock_factory

    try:
        user = {"sub": "user-uuid-789", "roles": ["admin", "dpo"]}
        gen = get_db_rls(user=user)
        session = await gen.__anext__()
        # set_rls_context doit avoir été appelé (2 execute)
        assert mock_session.execute.call_count == 2
        # Vérifier que l'user_id et les rôles sont bien injectés
        first_call = mock_session.execute.call_args_list[0]
        assert first_call.args[1]["uid"] == "user-uuid-789"
        second_call = mock_session.execute.call_args_list[1]
        assert second_call.args[1]["roles"] == "admin,dpo"
        assert session is mock_session
        with contextlib.suppress(StopAsyncIteration):
            await gen.__anext__()
    finally:
        db_module.async_session_factory = original_factory


@pytest.mark.asyncio
async def should_use_empty_string_when_sub_missing_in_get_db_rls():
    """get_db_rls doit gérer l'absence de 'sub' dans le payload JWT."""
    mock_session = AsyncMock()
    mock_session.begin = MagicMock(return_value=AsyncMock())
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_factory = MagicMock(return_value=mock_ctx)

    import gsie_api.infrastructure.database as db_module

    original_factory = db_module.async_session_factory
    db_module.async_session_factory = mock_factory

    try:
        user = {}  # Pas de sub, pas de roles
        gen = get_db_rls(user=user)
        await gen.__anext__()
        first_call = mock_session.execute.call_args_list[0]
        assert first_call.args[1]["uid"] == ""
        with contextlib.suppress(StopAsyncIteration):
            await gen.__anext__()
    finally:
        db_module.async_session_factory = original_factory

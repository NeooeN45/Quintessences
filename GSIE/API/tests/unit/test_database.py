"""Tests unitaires — base de données (infrastructure/database.py)."""

import contextlib
from unittest.mock import AsyncMock, MagicMock

import pytest

from gsie_api.core.config import Settings
from gsie_api.infrastructure.database import _build_engine_kwargs, get_db


def should_include_basic_kwargs_when_building_engine():
    """_build_engine_kwargs doit inclure echo, pool_size, max_overflow, pool_pre_ping."""
    settings = Settings(
        db_echo=True,
        db_pool_size=10,
        db_max_overflow=5,
        db_pgbouncer_mode=False,
    )
    kwargs = _build_engine_kwargs(settings)
    assert kwargs["echo"] is True
    assert kwargs["pool_size"] == 10
    assert kwargs["max_overflow"] == 5
    assert kwargs["pool_pre_ping"] is True
    assert "connect_args" not in kwargs


def should_disable_prepared_statements_when_pgbouncer_mode():
    """_build_engine_kwargs doit désactiver les prepared statements en mode PgBouncer."""
    settings = Settings(db_pgbouncer_mode=True)
    kwargs = _build_engine_kwargs(settings)
    assert "connect_args" in kwargs
    assert kwargs["connect_args"]["statement_cache_size"] == 0
    assert kwargs["connect_args"]["prepared_statement_cache_size"] == 0


def should_not_include_connect_args_when_no_pgbouncer():
    """_build_engine_kwargs ne doit pas inclure connect_args sans PgBouncer."""
    settings = Settings(db_pgbouncer_mode=False)
    kwargs = _build_engine_kwargs(settings)
    assert "connect_args" not in kwargs


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

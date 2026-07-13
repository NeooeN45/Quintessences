"""Base de données — SQLAlchemy 2.0 async + asyncpg (DEC-000019).

Configuration PgBouncer :
- statement_cache_size=0 côté asyncpg quand db_pgbouncer_mode=True
- Connexion directe dédiée pour LISTEN/NOTIFY (bypass pooler)
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from gsie_api.core.config import get_settings

_settings = get_settings()

# Engine principal — mode PgBouncer : désactive prepared statements
_engine_kwargs: dict = {
    "echo": _settings.db_echo,
    "pool_size": _settings.db_pool_size,
    "max_overflow": _settings.db_max_overflow,
    "pool_pre_ping": True,
}

if _settings.db_pgbouncer_mode:
    # Ajustement P0 DEC-000019 : statement_cache_size=0 pour PgBouncer transaction
    _engine_kwargs["connect_args"] = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    }

engine = create_async_engine(_settings.database_url, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Requis pour async (global_rules)
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency FastAPI — fournit une session DB par requête.

    Rollback automatique en cas d'exception (global_rules connection leaks).
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

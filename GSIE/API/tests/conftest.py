"""Fixtures partagées — base PostgreSQL/PostGIS réelle via testcontainers.

Centralise ce qui était dupliqué dans tests/integration/test_database.py,
pour que les autres suites (Knowledge Engine, pipeline) puissent réutiliser
la même base de test sans relancer un conteneur Docker par fichier.
"""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from gsie_api.infrastructure.models import Base


def _docker_available() -> bool:
    """Vérifie si Docker est disponible sans lever d'exception."""
    try:
        import docker

        docker.from_env().version()
        return True
    except Exception:
        return False


DOCKER_AVAILABLE = _docker_available()

requires_docker = pytest.mark.skipif(
    not DOCKER_AVAILABLE,
    reason="Docker is not available (testcontainers requires Docker)",
)


@pytest.fixture(scope="session")
def postgres_url() -> AsyncGenerator[str, None]:
    """Lance un conteneur PostgreSQL/PostGIS (une fois par session de tests)."""
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer(
        image="postgis/postgis:16-3.4",
        driver="asyncpg",
        username="gsie",
        password="gsie_test",
        dbname="gsie_test",
    ) as postgres:
        yield postgres.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")


@pytest.fixture
async def db_session(postgres_url: str) -> AsyncGenerator[AsyncSession, None]:
    """Session DB sur PostgreSQL/PostGIS réel — schéma créé puis nettoyé par test."""
    engine = create_async_engine(postgres_url, pool_pre_ping=True)

    # postgis_tiger_geocoder (activé par défaut sur l'image postgis/postgis) crée
    # une table `place` qui entre en conflit avec notre PlaceModel.
    async with engine.begin() as conn:
        await conn.execute(text("DROP EXTENSION IF EXISTS postgis_tiger_geocoder CASCADE"))
        await conn.execute(text("DROP EXTENSION IF EXISTS postgis_topology CASCADE"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

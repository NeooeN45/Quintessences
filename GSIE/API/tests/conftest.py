"""Fixtures partagées — base PostgreSQL/PostGIS réelle via testcontainers.

Centralise ce qui était dupliqué dans tests/integration/test_database.py,
pour que les autres suites (Knowledge Engine, pipeline) puissent réutiliser
la même base de test sans relancer un conteneur Docker par fichier.
"""

from collections.abc import AsyncGenerator, Sequence
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from gsie_api.infrastructure.models import Base

# Fichiers dont les tests dépendent d'un état de concurrence réel (verrous
# PostgreSQL `FOR UPDATE SKIP LOCKED`) et ne doivent jamais tourner en
# parallèle avec un autre test du même fichier. On ne modifie pas le fichier
# de test lui-même : le marquage se fait ici, à la collecte.
_FICHIERS_SERIAL = ("test_outbox_concurrence.py",)


def pytest_collection_modifyitems(items: Sequence[Any]) -> None:
    """Marque `serial` et regroupe sur un seul worker xdist les tests listés
    dans `_FICHIERS_SERIAL`, afin qu'ils ne soient jamais répartis sur des
    workers différents ni exécutés concurremment entre eux."""
    for item in items:
        if item.fspath.basename in _FICHIERS_SERIAL:
            item.add_marker(pytest.mark.serial)
            item.add_marker(pytest.mark.xdist_group(name="outbox_concurrence"))


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

    # `create_all` ne cree pas les schemas : depuis `20260728_0011`, les donnees
    # personnelles vivent hors de `public` et leurs tables echoueraient a se
    # creer. On declare donc les schemas que le registre reference.
    async with engine.begin() as conn:
        for schema in sorted(
            {table.schema for table in Base.metadata.tables.values() if table.schema}
        ):
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

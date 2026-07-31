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
    """Lance un conteneur PostgreSQL/PostGIS (une fois par session de tests).

    L'image `postgis/postgis:16-3.4` n'inclut pas pgvector. On l'installe
    à la volée via apt (le dépôt PGDG est déjà configuré par l'image de
    base postgres:16) avant de créer l'extension.

    L'installation dépend du réseau : sans elle, `CREATE EXTENSION vector`
    échoue plus loin, dans `db_session`, sur un message qui ne dit pas que
    la cause est un apt muet. On vérifie donc le code de sortie ici et on
    remonte la sortie d'apt telle quelle — un diagnostic à sa cause coûte
    moins cher qu'un diagnostic à trois fixtures de distance.
    """
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer(
        image="postgis/postgis:16-3.4",
        driver="asyncpg",
        username="gsie",
        password="gsie_test",
        dbname="gsie_test",
    ) as postgres:
        # Installer pgvector dans le conteneur (le dépôt PGDG est présent).
        container = postgres.get_wrapped_container()
        code, sorties = container.exec_run(
            ["sh", "-c", "apt-get update -qq && apt-get install -y -qq postgresql-16-pgvector"],
            demux=True,
        )
        if code != 0:
            # `demux=True` renvoie le couple (stdout, stderr), chacun pouvant
            # être None si le flux est resté vide.
            flux = b"\n".join(f for f in (sorties or (None, None)) if f)
            raise RuntimeError(
                "Installation de pgvector échouée dans le conteneur de test "
                f"(code {code}). Vérifier l'accès réseau au dépôt PGDG.\n"
                f"{flux.decode('utf-8', errors='replace')}"
            )
        yield postgres.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")


@pytest.fixture
async def db_session(postgres_url: str) -> AsyncGenerator[AsyncSession, None]:
    """Session DB sur PostgreSQL/PostGIS réel — schéma créé puis nettoyé par test."""
    engine = create_async_engine(postgres_url, pool_pre_ping=True)

    # postgis_tiger_geocoder (activé par défaut sur l'image postgis/postgis) crée
    # une table `place` qui entre en conflit avec notre PlaceModel.
    # pgvector est installé à la volée dans le fixture postgres_url (ci-dessus).
    async with engine.begin() as conn:
        await conn.execute(text("DROP EXTENSION IF EXISTS postgis_tiger_geocoder CASCADE"))
        await conn.execute(text("DROP EXTENSION IF EXISTS postgis_topology CASCADE"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

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

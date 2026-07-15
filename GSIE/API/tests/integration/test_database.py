"""Tests d'intégration — base PostgreSQL + Redis via testcontainers.

Ces tests nécessitent Docker. Ils sont ignorés si Docker n'est pas accessible.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from gsie_api.infrastructure.redis_client import get_redis


def _docker_available() -> bool:
    """Vérifie si Docker est disponible sans lever d'exception."""
    try:
        import docker

        docker.from_env().version()
        return True
    except Exception:
        return False


DOCKER_AVAILABLE = _docker_available()

pytestmark = pytest.mark.skipif(
    not DOCKER_AVAILABLE,
    reason="Docker is not available (testcontainers requires Docker)",
)


@pytest.fixture(scope="module")
def postgres_url():
    """Lance un conteneur PostgreSQL/PostGIS et retourne l'URL asyncpg."""
    with PostgresContainer(
        image="postgis/postgis:16-3.4",
        driver="asyncpg",
        username="gsie",
        password="gsie_test",
        dbname="gsie_test",
    ) as postgres:
        # asyncpg URL : remplace le driver de la URL fournie par testcontainers
        url = postgres.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
        yield url


@pytest.fixture(scope="module")
def redis_url():
    """Lance un conteneur Redis et retourne son URL."""
    with RedisContainer(image="redis:7-alpine") as redis:
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(6379)
        yield f"redis://{host}:{port}/0"


@pytest.mark.asyncio
async def should_connect_to_postgres_and_verify_postgis(postgres_url: str):
    """La connexion PostgreSQL + PostGIS fonctionne."""
    engine = create_async_engine(postgres_url, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT PostGIS_Full_Version()"))
            version = result.scalar_one()
            assert version is not None
            assert "postgis" in version.lower()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def should_connect_to_redis_and_ping(redis_url: str):
    """La connexion Redis fonctionne."""
    import redis.asyncio as redis

    # Patch temporaire du pool pour pointer vers le conteneur de test
    original_pool = None
    try:
        from gsie_api.infrastructure import redis_client as redis_module

        original_pool = redis_module.redis_pool
        redis_module.redis_pool = redis.ConnectionPool.from_url(
            redis_url,
            decode_responses=True,
        )
        client = await get_redis()
        pong = await client.ping()
        assert pong is True
    finally:
        if original_pool is not None:
            redis_module.redis_pool = original_pool
        # Ferme le client de test s'il existe
        if "client" in locals():
            await client.aclose()

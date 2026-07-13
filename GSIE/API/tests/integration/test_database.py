"""Tests d'intégration — base PostgreSQL + Redis via testcontainers.

Ces tests nécessitent Docker pour lancer les conteneurs de test.
Skip si Docker n'est pas disponible.
"""

import pytest

pytestmark = pytest.mark.skipif(
    True,  # Activé quand Docker est disponible — passer à False pour run
    reason="Tests d'intégration nécessitent Docker (testcontainers)",
)


@pytest.mark.asyncio
async def test_database_connection():
    """Test : la connexion à PostgreSQL + PostGIS fonctionne."""
    # TODO semaine 1 : testcontainers + asyncpg + SELECT PostGIS_Version()


@pytest.mark.asyncio
async def test_redis_connection():
    """Test : la connexion à Redis fonctionne."""
    # TODO semaine 1 : testcontainers + redis-py + PING

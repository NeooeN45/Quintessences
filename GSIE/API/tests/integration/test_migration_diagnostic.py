"""Test d'intégration — réversibilité de la migration 0013.

Une migration dont le `downgrade` n'a jamais été exécuté est un rollback
supposé, pas un rollback disponible : on ne le découvre faux qu'au moment
où l'on en a besoin. Ce test exécute réellement le cycle
`upgrade → downgrade → upgrade` sur une base PostgreSQL/PostGIS neuve et
vérifie ce que chaque sens laisse derrière lui.

`DEC-000031` a durci cette zone (garde-fous de migration, `0005`
irréversible) : le test s'exécute sur un conteneur jetable, jamais sur une
base existante, et ne touche à aucun garde-fou. Il pilote Alembic
directement, sans passer par le point d'entrée applicatif gardé par
`GSIE_RUN_MIGRATIONS_ON_STARTUP`.
"""

import asyncio
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.conftest import requires_docker

pytestmark = requires_docker

_ENUMS_0013 = ("diagnostic_type", "diagnostic_global_state", "diagnostic_validation_status")


@pytest.fixture(scope="module")
def base_vierge(monkeypatch_module: Any) -> Generator[str, None, None]:
    """Conteneur PostgreSQL/PostGIS dédié, sans aucun schéma préexistant.

    Distinct de la base partagée des autres suites : celle-ci crée ses
    tables par `metadata.create_all`, ce qui court-circuiterait justement
    ce que la migration doit prouver.

    `alembic/env.py` lit l'URL depuis la configuration applicative, pas
    depuis l'objet `Config` : c'est donc la variable d'environnement qui
    est positionnée, avant tout appel à Alembic.
    """
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer(
        image="postgis/postgis:16-3.4",
        driver="asyncpg",
        username="gsie",
        password="gsie_test",
        dbname="gsie_migration",
    ) as postgres:
        url = postgres.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
        asyncio.run(_preparer_postgis(url))
        monkeypatch_module.setenv("GSIE_DATABASE_URL", url)
        from gsie_api.core.config import get_settings

        get_settings.cache_clear()
        yield url
        get_settings.cache_clear()


@pytest.fixture(scope="module")
def monkeypatch_module() -> Generator[pytest.MonkeyPatch, None, None]:
    """`monkeypatch` est function-scoped ; le conteneur vit à l'échelle du module."""
    patch = pytest.MonkeyPatch()
    yield patch
    patch.undo()


async def _preparer_postgis(url: str) -> None:
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.execute(text("DROP EXTENSION IF EXISTS postgis_tiger_geocoder CASCADE"))
        await conn.execute(text("DROP EXTENSION IF EXISTS postgis_topology CASCADE"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    await engine.dispose()


async def _interroger(url: str, requete: str, **params: Any) -> Any:
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            return (await conn.execute(text(requete), params)).scalar()
    finally:
        await engine.dispose()


def _table_existe(url: str, nom: str) -> bool:
    return bool(
        asyncio.run(_interroger(url, "SELECT to_regclass(:nom) IS NOT NULL", nom=f"public.{nom}"))
    )


def _compte_enums(url: str, noms: tuple[str, ...]) -> int:
    return int(
        asyncio.run(
            _interroger(
                url,
                "SELECT count(*) FROM pg_type WHERE typname = ANY(:noms)",
                noms=list(noms),
            )
        )
    )


def _alembic_config() -> Any:
    from alembic.config import Config

    return Config("alembic.ini")


class TestMigration0013Reversible:
    """Le cycle upgrade → downgrade → upgrade doit être réellement jouable."""

    def test_cycle_complet(self, base_vierge: str) -> None:
        """Rend impossible : un `downgrade` écrit mais inexécutable.

        Vérifie aussi que le retour arrière ne laisse ni table `diagnostic`,
        ni enums orphelins, ni lignes `resource` sans corps — une resource
        citable dont le contenu a disparu serait un diagnostic illisible et
        pourtant référençable.
        """
        from alembic import command

        config = _alembic_config()

        command.upgrade(config, "head")
        assert _table_existe(base_vierge, "diagnostic")
        assert _compte_enums(base_vierge, _ENUMS_0013) == len(_ENUMS_0013)

        command.downgrade(config, "0012")
        assert not _table_existe(base_vierge, "diagnostic")
        assert _compte_enums(base_vierge, _ENUMS_0013) == 0
        # `evidence_level` préexiste à 0013 et sert à d'autres tables : le
        # downgrade ne doit surtout pas l'emporter avec lui.
        assert _compte_enums(base_vierge, ("evidence_level",)) == 1
        assert (
            asyncio.run(
                _interroger(base_vierge, "SELECT count(*) FROM resource WHERE type = 'diagnostic'")
            )
            == 0
        )

        command.upgrade(config, "head")
        assert _table_existe(base_vierge, "diagnostic")
        assert _compte_enums(base_vierge, _ENUMS_0013) == len(_ENUMS_0013)

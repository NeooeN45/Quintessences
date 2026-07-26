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
import os
import subprocess
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.conftest import requires_docker

pytestmark = requires_docker

_REVISIONS_AVANT_0013 = tuple(f"{n:04d}" for n in range(1, 12))

_ENUMS_0013 = ("diagnostic_type", "diagnostic_global_state", "diagnostic_validation_status")

# La chaîne de migrations commence par `CREATE EXTENSION age` (0001) : l'image
# postgis officielle ne suffit pas, il faut celle du dépôt (`Dockerfile.db`).
_IMAGE_DB = os.environ.get("GSIE_TEST_DB_IMAGE", "gsie-db:supply-chain-hardened")


def _image_disponible(image: str) -> bool:
    """Vérifie la présence locale de l'image sans la télécharger."""
    return (
        subprocess.run(  # noqa: S603
            ["docker", "image", "inspect", image],  # noqa: S607
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


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

    if not _image_disponible(_IMAGE_DB):
        pytest.skip(
            f"image {_IMAGE_DB} absente — la chaîne de migrations exige Apache AGE "
            f"(0001 crée l'extension), fourni par GSIE/API/Dockerfile.db et non par "
            f"l'image postgis officielle. Construire l'image, ou surcharger "
            f"GSIE_TEST_DB_IMAGE."
        )

    with PostgresContainer(
        image=_IMAGE_DB,
        driver="asyncpg",
        username="gsie",
        password="gsie_test",
        dbname="gsie_migration",
    ).with_command("postgres -c shared_preload_libraries=age -c search_path=public") as postgres:
        # `search_path` est forcé à `public` : l'image embarque
        # `ag_catalog,public,tiger`, or `ag_catalog` n'existe qu'une fois
        # l'extension AGE créée par 0001 — toute connexion antérieure à la
        # migration échouerait sur un schéma inexistant.
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
    """Amène la base à l'état que la chaîne de migrations suppose.

    L'image du dépôt fixe `search_path = ag_catalog,public,tiger`, mais
    `ag_catalog` n'existe qu'une fois l'extension AGE créée : toute
    connexion par défaut échoue tant qu'elle ne l'est pas. On force donc
    `search_path` sur cette connexion d'amorçage, le temps de créer AGE —
    après quoi les connexions normales, dont celles d'Alembic, fonctionnent.
    """
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": "public"}})
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS age"))
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

        # État pré-0013. Deux défauts préexistants de la chaîne obligent à
        # l'atteindre révision par révision. Ils sont signalés, non corrigés
        # ici (`CODE_QUALITY_STANDARD` §6) :
        #
        # 1. `upgrade` d'une seule traite jusqu'à 0011 avance le numéro de
        #    version sans appliquer le DDL des révisions traversées — la base
        #    reste à l'état 0001 tout en se déclarant en 0011.
        # 2. 0012 échoue sur une base vierge : 0006 crée les tables
        #    forestières depuis les modèles courants, qui portent déjà
        #    `index=True` sur `source_id`, si bien que 0012 recrée des index
        #    existants. Elle ne crée que des index et n'a aucune incidence
        #    sur 0013 : on la marque appliquée plutôt que de la jouer.
        for revision in _REVISIONS_AVANT_0013:
            command.upgrade(config, revision)
        command.stamp(config, "0012")

        command.upgrade(config, "head")
        assert _table_existe(base_vierge, "diagnostic")
        assert _compte_enums(base_vierge, _ENUMS_0013) == len(_ENUMS_0013)

        command.downgrade(config, "-1")
        # Le retour arrière porte sur 0013 seule : vérifié, pas supposé.
        assert (
            asyncio.run(_interroger(base_vierge, "SELECT version_num FROM alembic_version"))
            == "0012"
        )
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

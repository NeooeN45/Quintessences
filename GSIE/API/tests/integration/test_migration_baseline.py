"""Contrat d'intégration de la baseline Alembic GSIE v6.2.

Le test part d'une base PostgreSQL 16 réellement vierge, applique la baseline en
une seule commande, contrôle sa parité avec le registre SQLAlchemy courant,
exécute le retour à ``base`` puis rejoue l'upgrade. Aucun ``stamp`` ne peut
masquer une révision incomplète.
"""

import asyncio
import os
import subprocess
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from gsie_api.infrastructure.models import Base
from tests.conftest import requires_docker

pytestmark = requires_docker

_REVISION = "20260726_0001"
# Tête courante de la lignée : la baseline reste la base, les révisions
# suivantes s'empilent dessus.
_HEAD = "20260726_0002"
_GRAPH = "gsie_knowledge_graph"
_IMAGE_DB = os.environ.get("GSIE_TEST_DB_IMAGE", "gsie-db:supply-chain-hardened")
_REQUIRE_IMAGE = os.environ.get("GSIE_REQUIRE_MIGRATION_IMAGE", "false").lower() == "true"
_SYSTEM_TABLES = frozenset({"alembic_version", "spatial_ref_sys"})
_LEGACY_TABLES = frozenset(
    {
        "knowledge_mots_cles",
        "knowledge_domaines_validite",
        "knowledge_conflits",
        "knowledge_relations",
        "knowledge_history",
        "knowledge_objects",
        "ecosystem_groupes_ecologiques",
        "ecosystem_stations",
        "ecosystem_habitats",
        "botanical_essences",
        "botanical_genres",
        "botanical_familles",
    }
)
_EXPECTED_TABLES = frozenset(Base.metadata.tables)
# Colonnes apportées par la révision de reprise sur échec de l'outbox.
_OUTBOX_RETRY_COLUMNS = frozenset(
    {"attempt_count", "next_attempt_at", "last_error_code", "dead_lettered_at"}
)
_INDEX_ECHEANCE = "ix_outbox_status_next_attempt"
_EXPECTED_SOURCE_ID_INDEXES = frozenset(
    index.name
    for table in Base.metadata.tables.values()
    for index in table.indexes
    if index.name is not None and any(column.name == "source_id" for column in index.columns)
)


def _image_disponible(image: str) -> bool:
    return (
        subprocess.run(  # noqa: S603
            ["docker", "image", "inspect", image],  # noqa: S607
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


async def _nettoyer_extensions_preinstallees(url: str) -> None:
    """Neutralise les extensions PostGIS ajoutées par l'image de test."""
    engine = create_async_engine(
        url,
        connect_args={"server_settings": {"search_path": "public"}},
    )
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS age"))
            await conn.execute(text("DROP EXTENSION IF EXISTS postgis_tiger_geocoder CASCADE"))
            await conn.execute(text("DROP EXTENSION IF EXISTS postgis_topology CASCADE"))
            await conn.execute(text("DROP EXTENSION IF EXISTS postgis CASCADE"))
    finally:
        await engine.dispose()


@pytest.fixture(scope="module")
def monkeypatch_module() -> Generator[pytest.MonkeyPatch, None, None]:
    patch = pytest.MonkeyPatch()
    yield patch
    patch.undo()


@pytest.fixture(scope="module")
def base_vierge(monkeypatch_module: pytest.MonkeyPatch) -> Generator[str, None, None]:
    """Fournit une base sans schéma applicatif ni extension PostGIS."""
    from testcontainers.postgres import PostgresContainer

    if not _image_disponible(_IMAGE_DB):
        message = (
            f"image {_IMAGE_DB} absente ; construire GSIE/API/Dockerfile.db "
            "avant le test de migration"
        )
        if _REQUIRE_IMAGE:
            pytest.fail(message)
        pytest.skip(message)

    with PostgresContainer(
        image=_IMAGE_DB,
        driver="asyncpg",
        username="gsie",
        password="gsie_test",
        dbname="gsie_migration",
    ).with_command("postgres -c shared_preload_libraries=age -c search_path=public") as postgres:
        url = postgres.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
        asyncio.run(_nettoyer_extensions_preinstallees(url))
        monkeypatch_module.setenv("GSIE_DATABASE_URL", url)
        from gsie_api.core.config import get_settings

        get_settings.cache_clear()
        yield url
        get_settings.cache_clear()


async def _valeurs(url: str, requete: str, **params: Any) -> list[Any]:
    engine = create_async_engine(
        url,
        connect_args={"server_settings": {"search_path": "public"}},
    )
    try:
        async with engine.connect() as conn:
            resultat = await conn.execute(text(requete), params)
            return list(resultat.scalars())
    finally:
        await engine.dispose()


def _public_tables(url: str) -> frozenset[str]:
    return frozenset(
        asyncio.run(
            _valeurs(
                url,
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'",
            )
        )
    )


def _enum_names(url: str) -> frozenset[str]:
    return frozenset(
        asyncio.run(
            _valeurs(
                url,
                """
                SELECT t.typname
                FROM pg_type AS t
                JOIN pg_namespace AS n ON n.oid = t.typnamespace
                WHERE n.nspname = 'public' AND t.typtype = 'e'
                """,
            )
        )
    )


def _extension_names(url: str) -> frozenset[str]:
    return frozenset(asyncio.run(_valeurs(url, "SELECT extname FROM pg_extension")))


def _source_id_indexes(url: str) -> frozenset[str]:
    return frozenset(
        asyncio.run(
            _valeurs(
                url,
                """
                SELECT DISTINCT index_class.relname
                FROM pg_index AS i
                JOIN pg_class AS table_class ON table_class.oid = i.indrelid
                JOIN pg_class AS index_class ON index_class.oid = i.indexrelid
                JOIN pg_namespace AS n ON n.oid = table_class.relnamespace
                JOIN pg_attribute AS a
                  ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE n.nspname = 'public' AND a.attname = 'source_id'
                """,
            )
        )
    )


def _version(url: str) -> str | None:
    valeurs = asyncio.run(_valeurs(url, "SELECT version_num FROM alembic_version"))
    return str(valeurs[0]) if valeurs else None


def _colonnes(url: str, table: str) -> frozenset[str]:
    return frozenset(
        asyncio.run(
            _valeurs(
                url,
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :table
                """,
                table=table,
            )
        )
    )


def _index_de_table(url: str, table: str) -> frozenset[str]:
    return frozenset(
        asyncio.run(
            _valeurs(
                url,
                "SELECT indexname FROM pg_indexes "
                "WHERE schemaname = 'public' AND tablename = :table",
                table=table,
            )
        )
    )


def _graph_existe(url: str) -> bool:
    valeurs = asyncio.run(
        _valeurs(
            url,
            "SELECT EXISTS (SELECT 1 FROM ag_catalog.ag_graph WHERE name = :nom)",
            nom=_GRAPH,
        )
    )
    return bool(valeurs[0])


def _alembic_config() -> Any:
    from alembic.config import Config

    return Config("alembic.ini")


def _verifier_schema_courant(url: str) -> None:
    tables = _public_tables(url)
    assert tables - _SYSTEM_TABLES == _EXPECTED_TABLES
    assert tables.isdisjoint(_LEGACY_TABLES)
    assert _source_id_indexes(url) == _EXPECTED_SOURCE_ID_INDEXES
    assert {"postgis", "age"} <= _extension_names(url)
    assert _enum_names(url)
    assert _graph_existe(url)


class TestBaselineGSIEV62:
    """La baseline est autonome, exacte et réversible sur une base jetable."""

    def test_upgrade_downgrade_upgrade(self, base_vierge: str) -> None:
        from alembic import command

        config = _alembic_config()

        command.upgrade(config, "head")
        assert _version(base_vierge) == _HEAD
        _verifier_schema_courant(base_vierge)
        command.check(config)

        enums_apres_upgrade = _enum_names(base_vierge)
        command.downgrade(config, "base")
        assert _version(base_vierge) is None
        assert _public_tables(base_vierge) - _SYSTEM_TABLES == frozenset()
        assert _enum_names(base_vierge).isdisjoint(enums_apres_upgrade)
        assert not _graph_existe(base_vierge)
        assert {"postgis", "age"} <= _extension_names(base_vierge)

        command.upgrade(config, "head")
        assert _version(base_vierge) == _HEAD
        _verifier_schema_courant(base_vierge)

    def test_revision_outbox_reversible_sur_la_baseline(self, base_vierge: str) -> None:
        """La révision d'outbox se pose, se retire et se repose sans dérive.

        On redescend jusqu'à la baseline seule — pas jusqu'à `base` — pour
        vérifier que le `downgrade` de la révision est bien écrit, et non
        simplement masqué par la suppression de toute la table.
        """
        from alembic import command

        config = _alembic_config()
        command.upgrade(config, "head")

        assert _colonnes(base_vierge, "outbox_event") >= _OUTBOX_RETRY_COLUMNS
        assert _INDEX_ECHEANCE in _index_de_table(base_vierge, "outbox_event")

        command.downgrade(config, _REVISION)
        assert _version(base_vierge) == _REVISION
        colonnes_baseline = _colonnes(base_vierge, "outbox_event")
        assert colonnes_baseline.isdisjoint(_OUTBOX_RETRY_COLUMNS)
        # La table et son contenu historique survivent au retour arrière.
        assert "payload" in colonnes_baseline
        assert _INDEX_ECHEANCE not in _index_de_table(base_vierge, "outbox_event")

        command.upgrade(config, "head")
        assert _version(base_vierge) == _HEAD
        assert _colonnes(base_vierge, "outbox_event") >= _OUTBOX_RETRY_COLUMNS
        # Contrôle de dérive : le registre SQLAlchemy et la base coïncident.
        command.check(config)
        _verifier_schema_courant(base_vierge)

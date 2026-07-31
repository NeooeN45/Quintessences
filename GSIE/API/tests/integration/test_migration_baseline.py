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
# suivantes s'empilent dessus. Mise à jour après DEC-000037 (3 migrations
# additives 20260727_0003 à 0005).
_HEAD = "20260728_0019"
_GRAPH = "gsie_knowledge_graph"
# Doit correspondre a l image construite par la CI (.github/workflows/ci.yml,
# job python-integration). Une divergence faisait echouer le job en dur,
# GSIE_REQUIRE_MIGRATION_IMAGE valant "true" en integration continue.
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
# Schemas où vivent les tables du métamodèle. Dérivé du registre pour rester
# générique : chaque nouveau schéma de domaine (RFC-0029) est inclus
# automatiquement, sans qu'il faille modifier cette liste à la main.
_SCHEMAS_METAMODELE = frozenset(table.schema or "public" for table in Base.metadata.tables.values())
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
    """Tables applicatives, qualifiees par leur schema quand il n'est pas `public`.

    Les donnees personnelles vivent hors de `public` depuis `20260728_0011`,
    et les schemas de domaine depuis `20260728_0013` (RFC-0029). Ne lire que
    `public` ferait paraitre ces tables disparues.

    La liste des schemas est derivee du registre SQLAlchemy (`_SCHEMAS_METAMODELE`) :
    chaque nouveau schema de domaine est inclus automatiquement, sans qu'il
    faille modifier cette fonction a la main.

    La qualification suit la convention de `Base.metadata.tables` : une table de
    `public` est nommee nue, une table d'un autre schema est prefixee. Le
    controle verifie donc que chaque table est **la ou le registre la
    declare** — invariant plus fort que « tout dans public », et le seul qui
    detecte qu'une table sensible aurait ete rapatriee par megarde.
    """
    lignes = asyncio.run(
        _valeurs(
            url,
            """
            SELECT CASE WHEN schemaname = 'public' THEN tablename
                        ELSE schemaname || '.' || tablename END
            FROM pg_tables
            WHERE schemaname = ANY(:schemas)
            """,
            schemas=list(_SCHEMAS_METAMODELE),
        )
    )
    return frozenset(lignes)


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
                WHERE n.nspname = ANY(:schemas) AND a.attname = 'source_id'
                """,
                schemas=list(_SCHEMAS_METAMODELE),
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


# Aucun ecart tolere : le registre SQLAlchemy et la base migree doivent
# coincider exactement sur les tables du metamodele. Tout ajout ici doit etre
# justifie — un ecart tolere est un ecart que plus personne ne regarde.
_DIFFS_TOLERES: frozenset[tuple[str, str]] = frozenset()


def _aplatir_diffs(diffs: list[Any]) -> list[Any]:
    """Deplie les diffs groupes par alembic.

    `compare_metadata` ne rend pas une liste plate : les modifications d'une
    meme colonne (`modify_nullable`, `modify_type`, `modify_comment`) arrivent
    regroupees dans une sous-liste. Les traiter comme un diff simple faisait
    echouer le controle sur `TypeError: unhashable type` — donc le controle
    de derive ne controlait plus rien.
    """
    plats: list[Any] = []
    for diff in diffs:
        if isinstance(diff, list):
            plats.extend(diff)
        else:
            plats.append(diff)
    return plats


def _decrire_diff(diff: Any) -> tuple[str, str, str]:
    """Reduit un diff alembic a (operation, table concernee, libelle).

    Les diffs n'ont pas tous la meme forme : `add_table` porte un objet
    `Table`, `add_index` un `Index`, `add_column` un triplet
    (schema, table, Column), et les `modify_*` portent
    (schema, table, colonne, ...). Lire le message textuel ne voyait que les
    deux premieres formes — une derive `modify_nullable` ou `modify_type`
    passait donc inapercue.

    La table est extraite separement du libelle : c'est elle qui dit si le
    diff releve du metamodele ou d'une extension PostGIS.
    """
    operation = diff[0]
    if operation in {"add_table", "remove_table"}:
        return operation, diff[1].name, diff[1].name
    if operation in {"add_index", "remove_index"}:
        return operation, diff[1].table.name, diff[1].name
    if operation in {"add_column", "remove_column"}:
        return operation, diff[2], f"{diff[2]}.{diff[3].name}"
    if operation in {"add_constraint", "remove_constraint", "add_fk", "remove_fk"}:
        table = getattr(getattr(diff[1], "table", None), "name", "?")
        return operation, table, str(getattr(diff[1], "name", diff[1]))
    if operation.startswith("modify_"):
        return operation, diff[2], f"{diff[2]}.{diff[3]}"
    return operation, "?", str(diff[1:])


async def _comparer_registre_et_base(url: str) -> list[Any]:
    """Compare le registre SQLAlchemy a la base, via l'API structuree d'alembic."""
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": "public"}})
    try:
        async with engine.connect() as conn:
            return await conn.run_sync(
                lambda sync_conn: compare_metadata(
                    MigrationContext.configure(
                        sync_conn,
                        # `include_schemas` est indispensable depuis que les
                        # donnees personnelles vivent hors de `public`
                        # (`20260728_0011`). Sans lui, la reflexion se limite au
                        # `search_path` et les quatre tables RGPD paraissent
                        # disparues : le controle echouerait en signalant une
                        # derive qui n'existe pas, et masquerait les vraies.
                        opts={"include_schemas": True},
                    ),
                    Base.metadata,
                )
            )
    finally:
        await engine.dispose()


def _verifier_absence_de_derive(url: str) -> None:
    """Echoue sur toute derive schema/modele autre que celles tolerees.

    L'ancienne version interceptait la detection d'alembic et se contentait
    de verifier l'absence de cinq mots-cles dans le message : une derive
    `modify_nullable` ou `modify_type` passait donc inapercue. On raisonne
    desormais par liste blanche sur des diffs structures — tout ce qui n'est
    pas explicitement tolere fait echouer.

    Les tables installees par les extensions PostGIS (`tiger`, `topology`)
    sont ecartees : elles n'appartiennent pas au metamodele et noieraient
    toute vraie derive sous des dizaines de `remove_table`.
    """
    # Seules les tables du metamodele sont comparees. Une table absente du
    # registre releve d'une extension (PostGIS `tiger`, `topology`,
    # `spatial_ref_sys`) : la signaler noierait toute vraie derive.
    notres = {
        (operation, libelle)
        for operation, table, libelle in (
            _decrire_diff(diff)
            for diff in _aplatir_diffs(asyncio.run(_comparer_registre_et_base(url)))
        )
        if table in Base.metadata.tables
    }

    inattendus = notres - _DIFFS_TOLERES
    assert not inattendus, (
        "Derive entre le registre SQLAlchemy et la base migree : "
        f"{sorted(inattendus)}. Ajouter une revision Alembic, ou inscrire "
        "l'ecart dans _DIFFS_TOLERES en justifiant pourquoi il est faux."
    )


class TestBaselineGSIEV62:
    """La baseline est autonome, exacte et réversible sur une base jetable."""

    def test_upgrade_downgrade_upgrade(self, base_vierge: str) -> None:
        from alembic import command

        config = _alembic_config()

        command.upgrade(config, "head")
        assert _version(base_vierge) == _HEAD
        _verifier_schema_courant(base_vierge)
        _verifier_absence_de_derive(base_vierge)

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
        _verifier_absence_de_derive(base_vierge)
        _verifier_schema_courant(base_vierge)

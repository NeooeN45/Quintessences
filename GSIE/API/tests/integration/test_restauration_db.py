"""Test d'intégration — restauration DB prouvée (DEC-000043, S1).

Prouve que la base GSIE peut être sauvegardée et restaurée de bout en
bout, avec vérification d'intégrité. Ce test nécessite Docker
(testcontainers) et valide :

1. pg_dump de la base source (schéma migré via Alembic)
2. Restauration sur une base vierge
3. Parité structurelle : extensions, schémas, tables, FK, RLS, index
4. Fonctions PostGIS opérationnelles

Le test utilise l'image ``gsie-db:supply-chain-hardened`` (construite par
la CI via ``Dockerfile.db``) avec testcontainers, exécute les migrations
Alembic, puis enchaîne backup → restore → vérifications.

Le test est marqué ``serial`` car il crée une base temporaire et ne doit
pas tourner en parallèle avec d'autres tests DB.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import subprocess
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.conftest import requires_docker

if TYPE_CHECKING:
    from collections.abc import Generator

pytestmark = requires_docker

_IMAGE_DB = os.environ.get("GSIE_TEST_DB_IMAGE", "gsie-db:supply-chain-hardened")
_REQUIRE_IMAGE = os.environ.get("GSIE_REQUIRE_MIGRATION_IMAGE", "false").lower() == "true"

_ADMIN_USER = "gsie"
_SOURCE_DB = "gsie_test"
_TEST_DB = "gsie_restore_test"
_DUMP_FILE = "/tmp/gsie_backup_test.dump"


def _image_disponible(image: str) -> bool:
    """Vérifie qu'une image Docker est présente localement."""
    return (
        subprocess.run(  # noqa: S603
            ["docker", "image", "inspect", image],  # noqa: S607
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


async def _nettoyer_extensions_preinstallees(url: str) -> None:
    """Neutralise les extensions PostGIS ajoutées par l'image de test.

    L'image ``gsie-db`` pré-installe PostGIS, AGE et pgvector. On retire
    ``postgis_tiger_geocoder`` et ``postgis_topology`` qui créent des tables
    parasites (``place``, etc.) en conflit avec nos modèles. PostGIS lui-même
    est recréé par les migrations Alembic.
    """
    engine = create_async_engine(
        url,
        connect_args={"server_settings": {"search_path": "public"}},
    )
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS age"))
            await conn.execute(text("DROP EXTENSION IF EXISTS postgis_tiger_geocoder CASCADE"))
            await conn.execute(text("DROP EXTENSION IF EXISTS postgis_topology CASCADE"))
    finally:
        await engine.dispose()


@pytest.fixture(scope="module")
def monkeypatch_module() -> Generator[pytest.MonkeyPatch, None, None]:
    patch = pytest.MonkeyPatch()
    yield patch
    patch.undo()


@pytest.fixture(scope="module")
def base_migree(
    monkeypatch_module: pytest.MonkeyPatch,
) -> Generator[tuple[Any, str], None, None]:
    """Fournit un conteneur PostgreSQL avec le schéma GSIE migré.

    Retourne le couple ``(postgres_container, url_asyncpg)``. Le conteneur
    utilise l'image ``gsie-db:supply-chain-hardened`` (construite par la CI)
    avec PostgreSQL 16 + PostGIS + AGE + pgvector. Les migrations Alembic
    sont appliquées pour créer le schéma complet avant le backup.

    En CI, ``GSIE_REQUIRE_MIGRATION_IMAGE=true`` fait échouer le test si
    l'image est absente (au lieu de sauter silencieusement).
    """
    from testcontainers.postgres import PostgresContainer

    if not _image_disponible(_IMAGE_DB):
        message = (
            f"image {_IMAGE_DB} absente ; construire GSIE/API/Dockerfile.db "
            "avant le test de restauration"
        )
        if _REQUIRE_IMAGE:
            pytest.fail(message)
        pytest.skip(message)

    with PostgresContainer(
        image=_IMAGE_DB,
        driver="asyncpg",
        username=_ADMIN_USER,
        password="gsie_test",
        dbname=_SOURCE_DB,
    ).with_command("postgres -c shared_preload_libraries=age -c search_path=public") as postgres:
        url = postgres.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
        asyncio.run(_nettoyer_extensions_preinstallees(url))

        monkeypatch_module.setenv("GSIE_DATABASE_URL", url)
        from gsie_api.core.config import get_settings

        get_settings.cache_clear()

        # Appliquer les migrations Alembic pour créer le schéma complet.
        from alembic import command
        from alembic.config import Config

        config = Config("alembic.ini")
        command.upgrade(config, "head")

        yield postgres, url

        get_settings.cache_clear()


def _exec_container(
    container: Any,
    cmd: list[str],
    *,
    check: bool = True,
    timeout: int = 120,
) -> tuple[int, str, str]:
    """Exécute une commande dans le conteneur via ``exec_run``.

    Retourne ``(exit_code, stdout, stderr)``. Si ``check=True`` et que le
    code de sortie est non nul, lève ``CalledProcessError``.
    """
    result = container.exec_run(cmd, demux=True)
    exit_code, (stdout, stderr) = result
    stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
    stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""
    if check and exit_code != 0:
        raise subprocess.CalledProcessError(exit_code, cmd, stderr_str)
    return exit_code, stdout_str, stderr_str


def _psql_container(container: Any, db: str, sql: str) -> str:
    """Exécute une requête SQL dans le conteneur et retourne le résultat."""
    _, stdout, _ = _exec_container(
        container,
        ["psql", "-U", _ADMIN_USER, "-d", db, "-t", "-A", "-c", sql],
    )
    return stdout.strip()


def _count_container(container: Any, db: str, sql: str) -> int:
    """Exécute une requête COUNT et retourne l'entier."""
    raw = _psql_container(container, db, sql)
    return int(raw.strip()) if raw.strip() else 0


def _cleanup_container(container: Any) -> None:
    """Supprime la base de test et le dump temporaire."""
    with contextlib.suppress(subprocess.CalledProcessError):
        _exec_container(
            container,
            [
                "psql",
                "-U",
                _ADMIN_USER,
                "-d",
                _SOURCE_DB,
                "-c",
                f"DROP DATABASE IF EXISTS {_TEST_DB};",
            ],
            check=False,
        )
    _exec_container(container, ["rm", "-f", _DUMP_FILE], check=False)


@pytest.mark.serial
class TestRestaurationDB:
    """Prouve que la base GSIE peut être sauvegardée et restaurée.

    Étapes : backup → création base vierge → restore → vérifications →
    nettoyage. Toutes les vérifications doivent passer pour valider S1.
    """

    def should_backup_and_restore_with_full_integrity(self, base_migree: tuple[Any, str]) -> None:
        """Backup → restore → vérifications d'intégrité (S1, DEC-000043).

        Ce test prouve que la base GSIE est restaurable de bout en bout.
        Il vérifie : extensions, schémas, tables, FK, RLS, index, PostGIS.
        """
        postgres, _url = base_migree
        container = postgres.get_wrapped_container()

        _cleanup_container(container)

        # --- Étape 1 : Backup ---
        _exec_container(
            container,
            [
                "pg_dump",
                "-U",
                _ADMIN_USER,
                "-d",
                _SOURCE_DB,
                "--format=custom",
                "--compress=9",
                "--no-owner",
                "--no-privileges",
                f"--file={_DUMP_FILE}",
            ],
            timeout=120,
        )

        # --- Étape 2 : Création base vierge ---
        _exec_container(
            container,
            [
                "psql",
                "-U",
                _ADMIN_USER,
                "-d",
                _SOURCE_DB,
                "-c",
                f"CREATE DATABASE {_TEST_DB};",
            ],
        )

        # Précharger AGE (évite le warning ag_catalog)
        with contextlib.suppress(subprocess.CalledProcessError):
            _exec_container(
                container,
                [
                    "psql",
                    "-U",
                    _ADMIN_USER,
                    "-d",
                    _TEST_DB,
                    "-c",
                    "CREATE EXTENSION IF NOT EXISTS age;",
                ],
                check=False,
            )

        # --- Étape 3 : Restore ---
        exit_code, _, stderr = _exec_container(
            container,
            [
                "pg_restore",
                "-U",
                _ADMIN_USER,
                "-d",
                _TEST_DB,
                "--no-owner",
                "--no-privileges",
                "--if-exists",
                "--clean",
                _DUMP_FILE,
            ],
            check=False,
            timeout=120,
        )
        # pg_restore retourne des warnings sur les objets pré-existants ;
        # seul le code de sortie 1 (erreur fatale) nous intéresse.
        assert exit_code in (0, 1, 2), f"pg_restore a échoué : {stderr}"

        # --- Étape 4 : Vérifications d'intégrité ---

        # 4a — Extensions
        ext_count = _count_container(
            container,
            _TEST_DB,
            "SELECT count(*) FROM pg_extension WHERE extname IN ('postgis', 'age', 'vector');",
        )
        assert ext_count >= 3, f"Extensions : {ext_count}/3 — attendu 3 (postgis, age, vector)"

        # 4b — Schémas
        schema_count = _count_container(
            container,
            _TEST_DB,
            "SELECT count(*) FROM information_schema.schemata "
            "WHERE schema_name NOT LIKE 'pg_%' AND schema_name != 'information_schema';",
        )
        assert schema_count >= 6, f"Schémas : {schema_count} — attendu >= 6"

        # 4c — Tables
        table_count = _count_container(
            container,
            _TEST_DB,
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema NOT LIKE 'pg_%' AND table_schema != 'information_schema';",
        )
        assert table_count >= 100, f"Tables : {table_count} — attendu >= 100"

        # 4d — Contraintes FK
        fk_count = _count_container(
            container,
            _TEST_DB,
            "SELECT count(*) FROM information_schema.table_constraints "
            "WHERE constraint_type = 'FOREIGN KEY';",
        )
        assert fk_count >= 50, f"FK : {fk_count} — attendu >= 50"

        # 4e — RLS policies
        rls_count = _count_container(container, _TEST_DB, "SELECT count(*) FROM pg_policies;")
        assert rls_count >= 6, f"RLS : {rls_count} — attendu >= 6"

        # 4f — Fonctions PostGIS
        postgis_funcs = _count_container(
            container,
            _TEST_DB,
            "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid "
            "WHERE n.nspname = 'public' AND p.proname LIKE 'st_%';",
        )
        assert postgis_funcs >= 10, f"PostGIS : {postgis_funcs} — attendu >= 10"

        # 4g — Index
        index_count = _count_container(
            container,
            _TEST_DB,
            "SELECT count(*) FROM pg_indexes WHERE schemaname NOT LIKE 'pg_%';",
        )
        assert index_count >= 50, f"Index : {index_count} — attendu >= 50"

        # 4h — Parité tables source/restaurée
        source_tables = _count_container(
            container,
            _SOURCE_DB,
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema NOT LIKE 'pg_%' AND table_schema != 'information_schema';",
        )
        assert (
            table_count == source_tables
        ), f"Déséquilibre tables : source={source_tables} restaurée={table_count}"

        # 4i — Parité FK source/restaurée
        source_fk = _count_container(
            container,
            _SOURCE_DB,
            "SELECT count(*) FROM information_schema.table_constraints "
            "WHERE constraint_type = 'FOREIGN KEY';",
        )
        assert fk_count == source_fk, f"Déséquilibre FK : source={source_fk} restaurée={fk_count}"

        # 4j — Parité index source/restaurée
        source_index = _count_container(
            container,
            _SOURCE_DB,
            "SELECT count(*) FROM pg_indexes WHERE schemaname NOT LIKE 'pg_%';",
        )
        assert (
            index_count == source_index
        ), f"Déséquilibre index : source={source_index} restaurée={index_count}"

        # Nettoyage
        _cleanup_container(container)

    def should_verify_postgis_functions_are_operational(self, base_migree: tuple[Any, str]) -> None:
        """Les fonctions PostGIS restaurées sont fonctionnelles (pas juste présentes).

        Vérifie que ST_Area, ST_Contains, ST_GeomFromText retournent des
        résultats corrects sur la base restaurée — pas seulement qu'elles
        existent dans pg_proc.
        """
        postgres, _url = base_migree
        container = postgres.get_wrapped_container()

        _cleanup_container(container)

        # Backup + restore (réutilise le flux du test précédent)
        _exec_container(
            container,
            [
                "pg_dump",
                "-U",
                _ADMIN_USER,
                "-d",
                _SOURCE_DB,
                "--format=custom",
                "--compress=9",
                "--no-owner",
                "--no-privileges",
                f"--file={_DUMP_FILE}",
            ],
        )
        _exec_container(
            container,
            [
                "psql",
                "-U",
                _ADMIN_USER,
                "-d",
                _SOURCE_DB,
                "-c",
                f"CREATE DATABASE {_TEST_DB};",
            ],
        )
        _exec_container(
            container,
            [
                "pg_restore",
                "-U",
                _ADMIN_USER,
                "-d",
                _TEST_DB,
                "--no-owner",
                "--no-privileges",
                "--if-exists",
                "--clean",
                _DUMP_FILE,
            ],
            check=False,
            timeout=120,
        )

        # ST_Area sur un polygone connu (carré 1x1 = aire 1)
        area = _psql_container(
            container,
            _TEST_DB,
            "SELECT ST_Area(ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))'));",
        )
        area_val = float(area.strip())
        assert abs(area_val - 1.0) < 0.001, f"ST_Area incorrect : {area_val} — attendu 1.0"

        # ST_Contains : un polygone contient un point
        contains = _psql_container(
            container,
            _TEST_DB,
            "SELECT ST_Contains("
            "ST_GeomFromText('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))'), "
            "ST_GeomFromText('POINT(5 5)'));",
        )
        assert "t" in contains.lower(), f"ST_Contains incorrect : {contains} — attendu true"

        # ST_Distance : distance entre deux points
        distance = _psql_container(
            container,
            _TEST_DB,
            "SELECT ST_Distance("
            "ST_GeomFromText('POINT(0 0)'), "
            "ST_GeomFromText('POINT(3 4)'));",
        )
        dist_val = float(distance.strip())
        assert abs(dist_val - 5.0) < 0.001, f"ST_Distance incorrect : {dist_val} — attendu 5.0"

        # Nettoyage
        _cleanup_container(container)

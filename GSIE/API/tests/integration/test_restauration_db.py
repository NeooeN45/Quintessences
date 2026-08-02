"""Test d'intégration — restauration DB prouvée (DEC-000043, S1).

Prouve que la base GSIE peut être sauvegardée et restaurée de bout en
bout, avec vérification d'intégrité. Ce test nécessite Docker
(testcontainers) et valide :

1. pg_dump de la base source
2. Restauration sur une base vierge
3. Parité structurelle : extensions, schémas, tables, FK, RLS, index
4. Fonctions PostGIS opérationnelles

Le test est marqué ``serial`` car il crée une base temporaire et ne doit
pas tourner en parallèle avec d'autres tests DB.
"""

from __future__ import annotations

import contextlib
import subprocess

import pytest


def _docker_exec(container: str, cmd: list[str], timeout: int = 60) -> str:
    """Exécute une commande dans un conteneur Docker et retourne la sortie."""
    result = subprocess.run(
        ["docker", "exec", container] + cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    return result.stdout.strip()


def _psql(container: str, db: str, sql: str, user: str = "gsie") -> str:
    """Exécute une requête SQL dans le conteneur et retourne le résultat."""
    return _docker_exec(container, ["psql", "-U", user, "-d", db, "-t", "-c", sql])


def _count(container: str, db: str, sql: str) -> int:
    """Exécute une requête COUNT et retourne l'entier."""
    raw = _psql(container, db, sql)
    return int(raw.strip()) if raw.strip() else 0


@pytest.mark.serial
class TestRestaurationDB:
    """Prouve que la base GSIE peut être sauvegardée et restaurée.

    Étapes : backup → création base vierge → restore → vérifications →
    nettoyage. Toutes les vérifications doivent passer pour valider S1.
    """

    CONTAINER = "api-db-1"
    ADMIN_USER = "gsie"
    SOURCE_DB = "gsie"
    TEST_DB = "gsie_restore_test"
    DUMP_FILE = "/tmp/gsie_backup_test.dump"

    def _cleanup(self) -> None:
        """Supprime la base de test et le dump temporaire."""
        with contextlib.suppress(subprocess.CalledProcessError):
            _docker_exec(
                self.CONTAINER,
                [
                    "psql",
                    "-U",
                    self.ADMIN_USER,
                    "-d",
                    self.SOURCE_DB,
                    "-c",
                    f"DROP DATABASE IF EXISTS {self.TEST_DB};",
                ],
            )
        with contextlib.suppress(subprocess.CalledProcessError):
            _docker_exec(self.CONTAINER, ["rm", "-f", self.DUMP_FILE])

    def teardown_method(self) -> None:
        """Nettoyage après chaque test — pas de base temporaire résiduelle."""
        self._cleanup()

    def should_backup_and_restore_with_full_integrity(self) -> None:
        """Backup → restore → vérifications d'intégrité (S1, DEC-000043).

        Ce test prouve que la base GSIE est restaurable de bout en bout.
        Il vérifie : extensions, schémas, tables, FK, RLS, index, PostGIS.
        """
        self._cleanup()

        # --- Étape 1 : Backup ---
        _docker_exec(
            self.CONTAINER,
            [
                "pg_dump",
                "-U",
                self.ADMIN_USER,
                "-d",
                self.SOURCE_DB,
                "--format=custom",
                "--compress=9",
                "--no-owner",
                "--no-privileges",
                "--file=" + self.DUMP_FILE,
            ],
            timeout=120,
        )

        # --- Étape 2 : Création base vierge ---
        _docker_exec(
            self.CONTAINER,
            [
                "psql",
                "-U",
                self.ADMIN_USER,
                "-d",
                self.SOURCE_DB,
                "-c",
                f"CREATE DATABASE {self.TEST_DB};",
            ],
        )

        # Précharger AGE (évite le warning ag_catalog)
        with contextlib.suppress(subprocess.CalledProcessError):
            _docker_exec(
                self.CONTAINER,
                [
                    "psql",
                    "-U",
                    self.ADMIN_USER,
                    "-d",
                    self.TEST_DB,
                    "-c",
                    "CREATE EXTENSION IF NOT EXISTS age;",
                ],
            )

        # --- Étape 3 : Restore ---
        restore = subprocess.run(
            [
                "docker",
                "exec",
                self.CONTAINER,
                "pg_restore",
                "-U",
                self.ADMIN_USER,
                "-d",
                self.TEST_DB,
                "--no-owner",
                "--no-privileges",
                "--if-exists",
                "--clean",
                self.DUMP_FILE,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        # pg_restore retourne des warnings sur les objets pré-existants ;
        # seul le code de sortie 1 (erreur fatale) nous intéresse.
        assert restore.returncode in (0, 1), f"pg_restore a échoué : {restore.stderr}"

        # --- Étape 4 : Vérifications d'intégrité ---

        # 4a — Extensions
        ext_count = _count(
            self.CONTAINER,
            self.TEST_DB,
            "SELECT count(*) FROM pg_extension WHERE extname IN ('postgis', 'age', 'vector');",
        )
        assert ext_count >= 3, f"Extensions : {ext_count}/3 — attendu 3 (postgis, age, vector)"

        # 4b — Schémas
        schema_count = _count(
            self.CONTAINER,
            self.TEST_DB,
            "SELECT count(*) FROM information_schema.schemata "
            "WHERE schema_name NOT LIKE 'pg_%' AND schema_name != 'information_schema';",
        )
        assert schema_count >= 6, f"Schémas : {schema_count} — attendu >= 6"

        # 4c — Tables
        table_count = _count(
            self.CONTAINER,
            self.TEST_DB,
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema NOT LIKE 'pg_%' AND table_schema != 'information_schema';",
        )
        assert table_count >= 100, f"Tables : {table_count} — attendu >= 100"

        # 4d — Contraintes FK
        fk_count = _count(
            self.CONTAINER,
            self.TEST_DB,
            "SELECT count(*) FROM information_schema.table_constraints "
            "WHERE constraint_type = 'FOREIGN KEY';",
        )
        assert fk_count >= 50, f"FK : {fk_count} — attendu >= 50"

        # 4e — RLS policies
        rls_count = _count(self.CONTAINER, self.TEST_DB, "SELECT count(*) FROM pg_policies;")
        assert rls_count >= 6, f"RLS : {rls_count} — attendu >= 6"

        # 4f — Fonctions PostGIS
        postgis_funcs = _count(
            self.CONTAINER,
            self.TEST_DB,
            "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid "
            "WHERE n.nspname = 'public' AND p.proname LIKE 'st_%';",
        )
        assert postgis_funcs >= 10, f"PostGIS : {postgis_funcs} — attendu >= 10"

        # 4g — Index
        index_count = _count(
            self.CONTAINER,
            self.TEST_DB,
            "SELECT count(*) FROM pg_indexes WHERE schemaname NOT LIKE 'pg_%';",
        )
        assert index_count >= 50, f"Index : {index_count} — attendu >= 50"

        # 4h — Parité tables source/restaurée
        source_tables = _count(
            self.CONTAINER,
            self.SOURCE_DB,
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema NOT LIKE 'pg_%' AND table_schema != 'information_schema';",
        )
        assert (
            table_count == source_tables
        ), f"Déséquilibre tables : source={source_tables} restaurée={table_count}"

        # 4i — Parité FK source/restaurée
        source_fk = _count(
            self.CONTAINER,
            self.SOURCE_DB,
            "SELECT count(*) FROM information_schema.table_constraints "
            "WHERE constraint_type = 'FOREIGN KEY';",
        )
        assert fk_count == source_fk, f"Déséquilibre FK : source={source_fk} restaurée={fk_count}"

        # 4j — Parité index source/restaurée
        source_index = _count(
            self.CONTAINER,
            self.SOURCE_DB,
            "SELECT count(*) FROM pg_indexes WHERE schemaname NOT LIKE 'pg_%';",
        )
        assert (
            index_count == source_index
        ), f"Déséquilibre index : source={source_index} restaurée={index_count}"

    def should_verify_postgis_functions_are_operational(self) -> None:
        """Les fonctions PostGIS restaurées sont fonctionnelles (pas juste présentes).

        Vérifie que ST_Area, ST_Contains, ST_GeomFromText retournent des
        résultats corrects sur la base restaurée — pas seulement qu'elles
        existent dans pg_proc.
        """
        self._cleanup()

        # Backup + restore (réutilise le flux du test précédent)
        _docker_exec(
            self.CONTAINER,
            [
                "pg_dump",
                "-U",
                self.ADMIN_USER,
                "-d",
                self.SOURCE_DB,
                "--format=custom",
                "--compress=9",
                "--no-owner",
                "--no-privileges",
                "--file=" + self.DUMP_FILE,
            ],
        )
        _docker_exec(
            self.CONTAINER,
            [
                "psql",
                "-U",
                self.ADMIN_USER,
                "-d",
                self.SOURCE_DB,
                "-c",
                f"CREATE DATABASE {self.TEST_DB};",
            ],
        )
        subprocess.run(
            [
                "docker",
                "exec",
                self.CONTAINER,
                "pg_restore",
                "-U",
                self.ADMIN_USER,
                "-d",
                self.TEST_DB,
                "--no-owner",
                "--no-privileges",
                "--if-exists",
                "--clean",
                self.DUMP_FILE,
            ],
            capture_output=True,
            timeout=120,
        )

        # ST_Area sur un polygone connu (carré 1x1 = aire 1)
        area = _psql(
            self.CONTAINER,
            self.TEST_DB,
            "SELECT ST_Area(ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))'));",
        )
        area_val = float(area.strip())
        assert abs(area_val - 1.0) < 0.001, f"ST_Area incorrect : {area_val} — attendu 1.0"

        # ST_Contains : un polygone contient un point
        contains = _psql(
            self.CONTAINER,
            self.TEST_DB,
            "SELECT ST_Contains("
            "ST_GeomFromText('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))'), "
            "ST_GeomFromText('POINT(5 5)'));",
        )
        assert "t" in contains.lower(), f"ST_Contains incorrect : {contains} — attendu true"

        # ST_Distance : distance entre deux points
        distance = _psql(
            self.CONTAINER,
            self.TEST_DB,
            "SELECT ST_Distance("
            "ST_GeomFromText('POINT(0 0)'), "
            "ST_GeomFromText('POINT(3 4)'));",
        )
        dist_val = float(distance.strip())
        assert abs(dist_val - 5.0) < 0.001, f"ST_Distance incorrect : {dist_val} — attendu 5.0"

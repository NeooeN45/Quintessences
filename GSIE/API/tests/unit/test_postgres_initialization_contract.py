"""Contrats statiques de l'initialisation PostgreSQL conteneurisée."""

import re
from pathlib import Path

COMPOSE_PATH = Path(__file__).resolve().parents[2] / "docker-compose.yml"
INIT_DIRECTORY = Path(__file__).resolve().parents[2] / "docker" / "init"
HA_WORKFLOW_PATH = Path(__file__).resolve().parents[4] / ".github" / "workflows" / "ha-linux.yml"


def test_should_keep_public_schema_first_during_fresh_initdb() -> None:
    """Les extensions initdb doivent pouvoir être créées avant Apache AGE."""
    compose = COMPOSE_PATH.read_text(encoding="utf-8")
    match = re.search(r"^\s+- search_path=([^\r\n]+)$", compose, re.MULTILINE)

    assert match is not None
    assert match.group(1).split(",", maxsplit=1)[0] == "public"


def test_should_install_age_before_other_extensions_during_fresh_initdb() -> None:
    """AGE doit créer ``ag_catalog`` avant les extensions suivantes."""
    scripts = sorted(INIT_DIRECTORY.glob("*.sql"))

    assert scripts[0].name == "00-apache-age.sql"
    assert "CREATE EXTENSION IF NOT EXISTS age" in scripts[0].read_text(encoding="utf-8")
    for script in scripts:
        assert "SET search_path = public, pg_catalog" in script.read_text(encoding="utf-8")


def test_should_create_pgbackrest_stanza_before_first_wal_archive() -> None:
    """Le dépôt WAL doit être prêt avant l'arrêt du serveur initdb temporaire."""
    script = INIT_DIRECTORY / "05-pgbackrest-stanza.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")
    assert "SHOW archive_mode" in content
    assert "return 0 2>/dev/null || exit 0" in content
    assert "pgbackrest --stanza=gsie stanza-create" in content
    assert "pgbackrest --stanza=gsie check" in content


def test_should_preserve_base_platform_logs_when_ha_initialization_fails() -> None:
    """Un échec pré-HA doit laisser les journaux PostgreSQL dans l'artefact."""
    workflow = HA_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "tests/perf/results/ha-linux-platform.log" in workflow
    assert "GSIE/API/tests/perf/results/ha-linux-*.log" in workflow


def test_should_pin_the_ha_artifact_action_to_an_immutable_revision() -> None:
    """La preuve HA ne doit pas dépendre d'un tag GitHub Actions mutable."""
    workflow = HA_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "actions/upload-artifact@v4" not in workflow
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in workflow

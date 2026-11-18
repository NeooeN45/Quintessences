"""Contrat de la lignée unique d'intake et génération SQL hors ligne.

GSIE-PROMPT-0034 retire le contrat de compatibilité B/0060 ; les anciennes
bases de développement concernées relèvent de la procédure de recréation.
"""

import re
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

_RACINE_API = Path(__file__).resolve().parents[2]
_INTAKE = "20260823_0051"
_HEAD = "20260929_0059"
_REVISIONS_RETIREES = {"20260908_0051", "20261116_0060"}


def _configuration(buffer: StringIO | None = None) -> Config:
    configuration = Config(str(_RACINE_API / "alembic.ini"), output_buffer=buffer)
    configuration.set_main_option("script_location", str(_RACINE_API / "alembic"))
    return configuration


def _sql_hors_ligne(direction: str, intervalle: str) -> str:
    buffer = StringIO()
    with patch(
        "sqlalchemy.ext.asyncio.async_engine_from_config",
        side_effect=AssertionError("La génération SQL hors ligne ne doit ouvrir aucune connexion"),
    ):
        getattr(command, direction)(_configuration(buffer), intervalle, sql=True)
    return buffer.getvalue()


def should_keep_one_intake_creation_on_a_single_linear_lineage() -> None:
    script = ScriptDirectory.from_config(_configuration())

    assert script.get_heads() == [_HEAD]
    assert script.get_bases() == ["20260726_0001"]
    assert script.get_revision(_INTAKE).down_revision == "20260815_0050"
    assert script.get_revision("20260826_0052").down_revision == _INTAKE
    assert script.get_revision(_HEAD).down_revision == "20260929_0058"
    revisions = list(script.walk_revisions())
    identifiants = [revision.revision for revision in revisions]
    assert identifiants[0] == _HEAD
    assert identifiants[-1] == "20260726_0001"
    assert {_INTAKE, _HEAD} <= set(identifiants)
    assert set(identifiants).isdisjoint(_REVISIONS_RETIREES)
    assert len(identifiants) == len(set(identifiants))
    for revision in revisions:
        assert revision.down_revision is None or isinstance(revision.down_revision, str)
        assert revision.dependencies is None


@pytest.mark.parametrize(
    ("direction", "intervalle"),
    [("upgrade", "base:head"), ("downgrade", "head:base")],
)
def should_render_the_complete_lineage_without_a_database_connection(
    direction: str,
    intervalle: str,
) -> None:
    sql = _sql_hors_ligne(direction, intervalle)

    assert "BEGIN;" in sql
    assert "COMMIT;" in sql
    assert _HEAD in sql
    assert not any(revision in sql for revision in _REVISIONS_RETIREES)
    if direction == "upgrade":
        assert len(re.findall(r"CREATE TABLE (?:public\.)?field_intake\s*\(", sql)) == 1
        assert "uq_field_intake_application_event" in sql
        assert "ck_field_intake_status" in sql
        assert "CHECK (status IN ('quarantined', 'accepted', 'rejected'))" in " ".join(sql.split())
        for index in (
            "ix_field_intake_submitted_by",
            "ix_field_intake_target_resource_id",
            "ix_field_intake_submitted_by_received",
            "ix_field_intake_status_received",
        ):
            assert len(re.findall(rf"CREATE INDEX {index}\s", sql)) == 1
    else:
        assert len(re.findall(r"DROP TABLE (?:public\.)?field_intake\s*;", sql)) == 1
        assert "DROP TABLE alembic_version;" in sql


def should_keep_the_duplicate_alias_guard_in_generated_sql_before_the_unique_index() -> None:
    sql = _sql_hors_ligne("upgrade", "20260801_0026:20260801_0027")
    normalise = " ".join(sql.upper().split())

    assert "DO " in normalise
    assert "RAISE EXCEPTION" in normalise
    assert "GROUP BY NAMESPACE, EXTERNAL_ID" in normalise
    assert re.search(r"HAVING (?:PG_CATALOG\.)?COUNT\(\*\) > 1", normalise)
    assert "IDX_ENTITY_ALIAS_NS_EXTID" in normalise
    assert normalise.index("RAISE EXCEPTION") < normalise.index("CREATE UNIQUE INDEX")

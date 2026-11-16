"""Les deux identifiants d'intake restent accessibles sans tête concurrente."""

from pathlib import Path
from runpy import run_path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from alembic import op
from alembic.config import Config
from alembic.script import ScriptDirectory

_RACINE_API = Path(__file__).resolve().parents[2]
_FEAT_0051 = "20260823_0051"
_MAIN_0051 = "20260908_0051"
_HEAD = "20261116_0060"


def should_retain_both_historical_intake_revisions_on_a_single_linear_lineage() -> None:
    configuration = Config(str(_RACINE_API / "alembic.ini"))
    configuration.set_main_option("script_location", str(_RACINE_API / "alembic"))
    script = ScriptDirectory.from_config(configuration)

    assert script.get_heads() == [_HEAD]
    assert script.get_bases() == ["20260726_0001"]
    assert script.get_revision(_FEAT_0051).down_revision == "20260815_0050"
    assert script.get_revision(_MAIN_0051).down_revision == _FEAT_0051
    assert script.get_revision("20260826_0052").down_revision == _MAIN_0051
    assert script.get_revision(_HEAD).down_revision == "20260929_0059"

    revisions = list(script.walk_revisions())
    identifiants = [revision.revision for revision in revisions]
    assert identifiants[0] == _HEAD
    assert identifiants[-1] == "20260726_0001"
    assert {_FEAT_0051, _MAIN_0051, "20260929_0059"} <= set(identifiants)
    assert len(identifiants) == len(set(identifiants))
    for revision in revisions:
        assert revision.down_revision is None or isinstance(revision.down_revision, str)
        assert revision.dependencies is None


@pytest.mark.parametrize(
    "nom_revision",
    ["20260908_0051_field_intake.py", "20261116_0060_reconciliation_field_intake.py"],
)
def should_refuse_offline_reconciliation_before_opening_a_database_connection(
    monkeypatch: pytest.MonkeyPatch,
    nom_revision: str,
) -> None:
    revision = run_path(str(_RACINE_API / "alembic" / "versions" / nom_revision))
    connexion = Mock()
    monkeypatch.setattr(op, "get_context", lambda: SimpleNamespace(as_sql=True))
    monkeypatch.setattr(op, "get_bind", connexion)

    with pytest.raises(RuntimeError, match=r"public\.field_intake.*hors ligne"):
        revision["upgrade"]()

    connexion.assert_not_called()


def should_refuse_schema_verification_on_a_non_postgresql_connection() -> None:
    helper = run_path(str(_RACINE_API / "alembic" / "compatibility" / "field_intake_v1.py"))
    connexion = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"), execute=Mock())

    with pytest.raises(RuntimeError, match=r"public\.field_intake.*PostgreSQL"):
        helper["validate_field_intake_v1"](connexion)

    connexion.execute.assert_not_called()

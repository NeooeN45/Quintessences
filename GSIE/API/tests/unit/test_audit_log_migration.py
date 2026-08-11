"""Garde-fous pour la migration audit_log append-only (20260803_0033)."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from gsie_api.infrastructure.models import Base
from gsie_api.infrastructure.models.audit_log import AUDIT_SCHEMA, AuditLogModel

_MIGRATION_FILE = "alembic/versions/20260803_0033_audit_log.py"
_REVISION = "20260803_0033"
_DOWN_REVISION = "20260803_0032"


def test_migration_etend_la_lignee_depuis_0032() -> None:
    script = ScriptDirectory.from_config(Config("alembic.ini"))
    revision = script.get_revision(_REVISION)

    assert revision is not None
    assert revision.down_revision == _DOWN_REVISION


def test_migration_cree_schema_et_table_audit_log() -> None:
    source = Path(_MIGRATION_FILE).read_text(encoding="utf-8")

    assert "CREATE SCHEMA IF NOT EXISTS" in source
    assert '"audit_log"' in source


def test_migration_est_append_only() -> None:
    """La migration révoque UPDATE et DELETE — append-only strict."""
    source = Path(_MIGRATION_FILE).read_text(encoding="utf-8")

    assert "REVOKE UPDATE, DELETE" in source
    assert "GRANT SELECT, INSERT" in source
    assert "prevent_audit_modification" in source
    assert "BEFORE UPDATE" in source
    assert "BEFORE DELETE" in source


def test_migration_active_rls() -> None:
    source = Path(_MIGRATION_FILE).read_text(encoding="utf-8")

    assert "ENABLE ROW LEVEL SECURITY" in source
    assert "FORCE ROW LEVEL SECURITY" in source
    assert "CREATE POLICY audit_log_visible" in source


def test_modele_audit_log_enregistre_dans_base_metadata() -> None:
    assert f"{AUDIT_SCHEMA}.audit_log" in Base.metadata.tables


def test_modele_audit_log_contraintes() -> None:
    table = AuditLogModel.__table__
    check_names = {c.name for c in table.constraints if c.name}

    assert "ck_audit_log_action_non_empty" in check_names
    assert "ck_audit_log_resource_type_non_empty" in check_names
    assert "ck_audit_log_action_enum" in check_names
    assert table.schema == AUDIT_SCHEMA


def test_modele_audit_log_actions_valides() -> None:
    """Le CHECK constraint autorise uniquement les actions attendues."""
    source = Path(_MIGRATION_FILE).read_text(encoding="utf-8")

    for action in (
        "create",
        "read",
        "update",
        "delete",
        "export",
        "login",
        "logout",
        "invite",
        "revoke",
        "sync",
    ):
        assert f"'{action}'" in source


def test_modele_audit_log_indexes() -> None:
    table = AuditLogModel.__table__
    index_names = {idx.name for idx in table.indexes}

    assert "idx_audit_log_timestamp" in index_names
    assert "idx_audit_log_actor" in index_names
    assert "idx_audit_log_resource" in index_names
    assert "idx_audit_log_organisation" in index_names
    assert "idx_audit_log_action" in index_names

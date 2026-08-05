"""Garde-fous pour la migration organisations/workspaces (20260803_0032).

Vérifie que la migration :
- étend la lignée linéaire depuis 20260803_0031,
- crée le schéma gsie_organisations avec les 3 tables,
- active RLS + REVOKE DELETE sur les 3 tables,
- définit la fonction is_member SECURITY DEFINER.

Vérifie que les modèles SQLAlchemy :
- sont enregistrés dans Base.metadata (3 nouvelles tables),
- respectent les contraintes (CHECK, UNIQUE, FK),
- utilisent le bon schéma gsie_organisations.
"""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from gsie_api.infrastructure.models import Base
from gsie_api.infrastructure.models.organisations import (
    ORGANISATIONS_SCHEMA,
    OrganisationMemberModel,
    OrganisationModel,
    WorkspaceModel,
)

_MIGRATION_FILE = "alembic/versions/20260803_0032_organisations_workspaces.py"
_REVISION = "20260803_0032"
_DOWN_REVISION = "20260803_0031"


def test_migration_etend_la_lignee_depuis_0031() -> None:
    script = ScriptDirectory.from_config(Config("alembic.ini"))
    revision = script.get_revision(_REVISION)

    assert revision is not None
    assert revision.down_revision == _DOWN_REVISION


def test_migration_cree_schema_et_trois_tables() -> None:
    source = Path(_MIGRATION_FILE).read_text(encoding="utf-8")

    assert "CREATE SCHEMA IF NOT EXISTS" in source
    assert '"organisation"' in source
    assert '"workspace"' in source
    assert '"organisation_member"' in source


def test_migration_active_rls_et_revoque_delete() -> None:
    source = Path(_MIGRATION_FILE).read_text(encoding="utf-8")

    assert "ENABLE ROW LEVEL SECURITY" in source
    assert "FORCE ROW LEVEL SECURITY" in source
    assert "REVOKE DELETE" in source
    assert "CREATE POLICY organisation_visible" in source
    assert "CREATE POLICY workspace_visible" in source
    assert "CREATE POLICY member_visible" in source


def test_migration_definit_fonction_is_member_security_definer() -> None:
    source = Path(_MIGRATION_FILE).read_text(encoding="utf-8")

    assert "is_member" in source
    assert "SECURITY DEFINER" in source
    assert "GRANT EXECUTE ON FUNCTION" in source


def test_modeles_enregistres_dans_base_metadata() -> None:
    tables = Base.metadata.tables

    assert f"{ORGANISATIONS_SCHEMA}.organisation" in tables
    assert f"{ORGANISATIONS_SCHEMA}.workspace" in tables
    assert f"{ORGANISATIONS_SCHEMA}.organisation_member" in tables


def test_modele_organisation_contraintes() -> None:
    table = OrganisationModel.__table__
    check_names = {c.name for c in table.constraints if c.name}

    assert "ck_organisation_status" in check_names
    assert "ck_organisation_slug_non_empty" in check_names
    assert "ck_organisation_display_name_non_empty" in check_names
    assert "uq_organisation_slug" in check_names
    assert table.schema == ORGANISATIONS_SCHEMA


def test_modele_workspace_contraintes() -> None:
    table = WorkspaceModel.__table__
    check_names = {c.name for c in table.constraints if c.name}

    assert "ck_workspace_slug_non_empty" in check_names
    assert "ck_workspace_display_name_non_empty" in check_names
    assert "uq_workspace_org_slug" in check_names
    assert table.schema == ORGANISATIONS_SCHEMA


def test_modele_organisation_member_contraintes() -> None:
    table = OrganisationMemberModel.__table__
    check_names = {c.name for c in table.constraints if c.name}

    assert "ck_organisation_member_role" in check_names
    assert table.schema == ORGANISATIONS_SCHEMA

    # Clé primaire composite
    pk_columns = {c.name for c in table.primary_key.columns}
    assert pk_columns == {"organisation_id", "account_id"}


def test_modele_organisation_member_roles_valides() -> None:
    """Le CHECK constraint autorise uniquement owner, admin, member."""
    source = Path(_MIGRATION_FILE).read_text(encoding="utf-8")

    assert "role IN ('owner', 'admin', 'member')" in source

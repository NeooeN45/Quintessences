"""Table audit_log append-only (journal d'audit persistant).

Introduit la persistance du journal d'audit GSIE :
- ``audit_log`` — table append-only dans le schéma ``gsie_audit``.
- Aucun UPDATE ni DELETE possible (REVOKE UPDATE, DELETE).
- Trigger ``prevent_audit_modification`` bloque toute modification.
- RLS : visible par l'utilisateur lui-même ou par les admins.

Remplace le stub statique du router audit (données hardcodées).

Revision ID: 20260803_0033
Revises: 20260803_0032
Create Date: 2026-08-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260803_0033"
down_revision: str | None = "20260803_0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_audit"
_ROLE_APPLICATION = "gsie_application"


def _current_user_uuid_expr() -> str:
    return "NULLIF(current_setting('app.current_user_id', true), '')::uuid"


def _current_user_roles_expr() -> str:
    return "COALESCE(current_setting('app.current_user_roles', true), '')"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {_SCHEMA}")

    # --- Table audit_log (append-only) ---
    op.create_table(
        "audit_log",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("actor_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("actor_email", sa.String(length=320), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=200), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("organisation_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("workspace_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("status_code", sa.Integer, nullable=True),
        sa.Column("method", sa.String(length=10), nullable=True),
        sa.Column("path", sa.String(length=500), nullable=True),
        sa.Column("details", PGJSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.CheckConstraint("action <> ''", name="ck_audit_log_action_non_empty"),
        sa.CheckConstraint("resource_type <> ''", name="ck_audit_log_resource_type_non_empty"),
        sa.CheckConstraint(
            "action IN ('create', 'read', 'update', 'delete', 'export', 'login', 'logout', "
            "'invite', 'revoke', 'sync')",
            name="ck_audit_log_action_enum",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["gsie_rgpd_identites.user_account.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["gsie_organisations.organisation.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["gsie_organisations.workspace.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_audit_log_timestamp",
        "audit_log",
        [sa.text("timestamp DESC")],
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_audit_log_actor",
        "audit_log",
        ["actor_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_audit_log_resource",
        "audit_log",
        ["resource_type", "resource_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_audit_log_organisation",
        "audit_log",
        ["organisation_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_audit_log_action",
        "audit_log",
        ["action"],
        schema=_SCHEMA,
    )

    # --- Trigger : bloque UPDATE et DELETE (append-only) ---
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {_SCHEMA}.prevent_audit_modification()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log est append-only : UPDATE et DELETE interdits';
        END;
        $$;
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER trg_prevent_audit_update
        BEFORE UPDATE ON {_SCHEMA}.audit_log
        FOR EACH ROW
        EXECUTE FUNCTION {_SCHEMA}.prevent_audit_modification();
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER trg_prevent_audit_delete
        BEFORE DELETE ON {_SCHEMA}.audit_log
        FOR EACH ROW
        EXECUTE FUNCTION {_SCHEMA}.prevent_audit_modification();
        """
    )

    # --- Row Level Security ---
    _user = _current_user_uuid_expr()
    _roles = _current_user_roles_expr()

    op.execute(f"ALTER TABLE {_SCHEMA}.audit_log ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_SCHEMA}.audit_log FORCE ROW LEVEL SECURITY")

    # Visible par l'acteur lui-même ou par les admins.
    op.execute(
        f"""
        CREATE POLICY audit_log_visible ON {_SCHEMA}.audit_log
        USING (
            actor_id = {_user}
            OR position('admin' IN {_roles}) > 0
        )
        """
    )

    # --- Privilèges rôle applicatif ---
    # INSERT uniquement — pas de UPDATE ni DELETE (append-only).
    op.execute(f"GRANT USAGE ON SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}")
    op.execute(f"GRANT SELECT, INSERT ON TABLE {_SCHEMA}.audit_log TO {_ROLE_APPLICATION}")
    op.execute(f"REVOKE UPDATE, DELETE ON TABLE {_SCHEMA}.audit_log FROM {_ROLE_APPLICATION}")


def downgrade() -> None:
    op.execute(f"REVOKE SELECT, INSERT ON TABLE {_SCHEMA}.audit_log FROM {_ROLE_APPLICATION}")
    op.execute(f"REVOKE USAGE ON SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}")
    op.execute(f"DROP POLICY IF EXISTS audit_log_visible ON {_SCHEMA}.audit_log")
    op.execute(f"ALTER TABLE {_SCHEMA}.audit_log DISABLE ROW LEVEL SECURITY")
    op.execute(f"DROP TRIGGER IF EXISTS trg_prevent_audit_delete ON {_SCHEMA}.audit_log")
    op.execute(f"DROP TRIGGER IF EXISTS trg_prevent_audit_update ON {_SCHEMA}.audit_log")
    op.execute(f"DROP FUNCTION IF EXISTS {_SCHEMA}.prevent_audit_modification()")
    op.drop_index("idx_audit_log_action", schema=_SCHEMA)
    op.drop_index("idx_audit_log_organisation", schema=_SCHEMA)
    op.drop_index("idx_audit_log_resource", schema=_SCHEMA)
    op.drop_index("idx_audit_log_actor", schema=_SCHEMA)
    op.drop_index("idx_audit_log_timestamp", schema=_SCHEMA)
    op.drop_table("audit_log", schema=_SCHEMA)
    op.execute(f"DROP SCHEMA IF EXISTS {_SCHEMA}")

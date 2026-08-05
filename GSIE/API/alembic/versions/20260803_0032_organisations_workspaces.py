"""Organisations, workspaces et appartenance (multi-tenant enterprise).

Introduit le socle multi-tenant GSIE :
- ``organisation`` — entité racine possédée par un compte créateur.
- ``workspace`` — sous-ensemble d'une organisation (périmètre de travail).
- ``organisation_member`` — appartenance compte ↔ organisation avec rôle.

Row Level Security (DEC-000037) :
- Une fonction ``is_member`` SECURITY DEFINER évite la récursion RLS
  entre ``organisation`` et ``organisation_member``.
- ``organisation`` est visible par son créateur ou par ses membres.
- ``workspace`` est visible si l'organisation parente est visible.
- ``organisation_member`` est visible par le compte lui-même ou par le
  créateur de l'organisation.
- ``REVOKE DELETE`` sur les trois tables (soft delete via ``deleted_at``).

Revision ID: 20260803_0032
Revises: 20260803_0031
Create Date: 2026-08-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260803_0032"
down_revision: str | None = "20260803_0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_organisations"
_ROLE_APPLICATION = "gsie_application"


def _current_user_uuid_expr() -> str:
    """Expression SQL pour récupérer l'UUID de l'utilisateur courant (RLS)."""
    return "NULLIF(current_setting('app.current_user_id', true), '')::uuid"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {_SCHEMA}")

    # --- Fonction SECURITY DEFINER pour éviter la récursion RLS ---
    # is_member(org_uuid) → true si le compte courant est membre de l'org.
    # SECURITY DEFINER : bypass RLS sur organisation_member (pas de récursion).
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {_SCHEMA}.is_member(org_uuid uuid)
        RETURNS boolean
        LANGUAGE sql
        SECURITY DEFINER
        STABLE
        AS $$
            SELECT EXISTS (
                SELECT 1 FROM {_SCHEMA}.organisation_member
                WHERE organisation_id = org_uuid
                AND account_id = {_current_user_uuid_expr()}
                AND revoked_at IS NULL
            )
        $$;
        """
    )

    # --- Table organisation ---
    op.create_table(
        "organisation",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column("created_by", PGUUID(as_uuid=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_organisation_status"),
        sa.CheckConstraint("slug <> ''", name="ck_organisation_slug_non_empty"),
        sa.CheckConstraint("display_name <> ''", name="ck_organisation_display_name_non_empty"),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["gsie_rgpd_identites.user_account.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_organisation_slug"),
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_organisation_created_by",
        "organisation",
        ["created_by"],
        schema=_SCHEMA,
    )

    # --- Table workspace ---
    op.create_table(
        "workspace",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("organisation_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("slug <> ''", name="ck_workspace_slug_non_empty"),
        sa.CheckConstraint("display_name <> ''", name="ck_workspace_display_name_non_empty"),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            [f"{_SCHEMA}.organisation.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organisation_id", "slug", name="uq_workspace_org_slug"),
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_workspace_organisation",
        "workspace",
        ["organisation_id"],
        schema=_SCHEMA,
    )

    # --- Table organisation_member ---
    op.create_table(
        "organisation_member",
        sa.Column("organisation_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("account_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default=sa.text("'member'")),
        sa.Column("invited_by", PGUUID(as_uuid=True), nullable=False),
        sa.Column(
            "joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "role IN ('owner', 'admin', 'member')", name="ck_organisation_member_role"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            [f"{_SCHEMA}.organisation.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["gsie_rgpd_identites.user_account.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["invited_by"],
            ["gsie_rgpd_identites.user_account.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("organisation_id", "account_id"),
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_organisation_member_account",
        "organisation_member",
        ["account_id"],
        schema=_SCHEMA,
    )

    # --- Row Level Security ---
    _user = _current_user_uuid_expr()

    for table in ("organisation", "workspace", "organisation_member"):
        op.execute(f"ALTER TABLE {_SCHEMA}.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {_SCHEMA}.{table} FORCE ROW LEVEL SECURITY")

    # organisation : visible par créateur ou membre.
    op.execute(
        f"""
        CREATE POLICY organisation_visible ON {_SCHEMA}.organisation
        USING (
            created_by = {_user}
            OR {_SCHEMA}.is_member(id)
        )
        WITH CHECK (created_by = {_user})
        """
    )

    # workspace : visible si l'org parente est visible (is_member ou créateur).
    op.execute(
        f"""
        CREATE POLICY workspace_visible ON {_SCHEMA}.workspace
        USING (
            {_SCHEMA}.is_member(organisation_id)
            OR organisation_id IN (
                SELECT id FROM {_SCHEMA}.organisation
                WHERE created_by = {_user}
            )
        )
        WITH CHECK (
            {_SCHEMA}.is_member(organisation_id)
            OR organisation_id IN (
                SELECT id FROM {_SCHEMA}.organisation
                WHERE created_by = {_user}
            )
        )
        """
    )

    # organisation_member : visible par le compte lui-même ou le créateur de l'org.
    op.execute(
        f"""
        CREATE POLICY member_visible ON {_SCHEMA}.organisation_member
        USING (
            account_id = {_user}
            OR EXISTS (
                SELECT 1 FROM {_SCHEMA}.organisation
                WHERE id = {_SCHEMA}.organisation_member.organisation_id
                AND created_by = {_user}
            )
        )
        WITH CHECK (
            account_id = {_user}
            OR EXISTS (
                SELECT 1 FROM {_SCHEMA}.organisation
                WHERE id = {_SCHEMA}.organisation_member.organisation_id
                AND created_by = {_user}
            )
        )
        """
    )

    # --- Privilèges rôle applicatif ---
    op.execute(f"GRANT USAGE ON SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_SCHEMA}.is_member(uuid) TO {_ROLE_APPLICATION}")
    for table in ("organisation", "workspace", "organisation_member"):
        op.execute(
            f"GRANT SELECT, INSERT, UPDATE ON TABLE {_SCHEMA}.{table} TO {_ROLE_APPLICATION}"
        )
        op.execute(f"REVOKE DELETE ON TABLE {_SCHEMA}.{table} FROM {_ROLE_APPLICATION}")


def downgrade() -> None:
    for table in ("organisation_member", "workspace", "organisation"):
        op.execute(f"REVOKE ALL ON TABLE {_SCHEMA}.{table} FROM {_ROLE_APPLICATION}")
    op.execute(f"REVOKE EXECUTE ON FUNCTION {_SCHEMA}.is_member(uuid) FROM {_ROLE_APPLICATION}")
    op.execute(f"REVOKE USAGE ON SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}")
    op.drop_table("organisation_member", schema=_SCHEMA)
    op.drop_table("workspace", schema=_SCHEMA)
    op.drop_table("organisation", schema=_SCHEMA)
    op.execute(f"DROP FUNCTION IF EXISTS {_SCHEMA}.is_member(uuid)")
    op.execute(f"DROP SCHEMA IF EXISTS {_SCHEMA}")

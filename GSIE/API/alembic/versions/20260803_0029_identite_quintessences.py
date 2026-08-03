"""Identité Quintessences canonique et moyens de connexion.

RFC-0032 / DEC-000044. Les comptes opérationnels ne sont pas des ressources
scientifiques du métamodèle : ils vivent dans le périmètre identifiant RGPD
et n'entrent pas dans ``resource``. L'application reçoit uniquement DML sans
DELETE sur ces quatre tables et demeure sans accès à ``data_subject``.

Revision ID: 20260803_0029
Revises: 20260801_0028
Create Date: 2026-08-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260803_0029"
down_revision: str | None = "20260801_0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_rgpd_identites"
_ROLE_APPLICATION = "gsie_application"
_TABLES = (
    "user_account",
    "identity_provider_link",
    "local_credential",
    "account_role",
)


def upgrade() -> None:
    op.create_table(
        "user_account",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('active', 'disabled', 'pending_deletion')",
            name="ck_user_account_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=_SCHEMA,
    )
    op.create_table(
        "identity_provider_link",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("issuer", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=320), nullable=False),
        sa.Column("email_normalized", sa.String(length=320), nullable=True),
        sa.Column("email_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_authenticated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "provider IN ('local', 'google', 'oidc', 'saml')",
            name="ck_identity_provider_link_provider",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            [f"{_SCHEMA}.user_account.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "issuer",
            "subject",
            name="uq_identity_provider_link_provider_issuer_subject",
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_identity_provider_link_account",
        "identity_provider_link",
        ["account_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_identity_provider_link_email",
        "identity_provider_link",
        ["email_normalized"],
        schema=_SCHEMA,
    )
    op.create_table(
        "local_credential",
        sa.Column("identity_link_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("password_hash", sa.String(length=500), nullable=False),
        sa.Column(
            "password_changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["identity_link_id"],
            [f"{_SCHEMA}.identity_provider_link.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("identity_link_id"),
        schema=_SCHEMA,
    )
    op.create_table(
        "account_role",
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "application",
            sa.String(length=64),
            server_default="quintessences",
            nullable=False,
        ),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("application <> ''", name="ck_account_role_application_non_empty"),
        sa.CheckConstraint("role <> ''", name="ck_account_role_non_empty"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            [f"{_SCHEMA}.user_account.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("account_id", "application", "role"),
        schema=_SCHEMA,
    )

    # Le rôle applicatif reste sans accès à data_subject. Le GRANT est borné
    # aux quatre tables opérationnelles et exclut DELETE.
    op.execute(f"GRANT USAGE ON SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}")
    for table in _TABLES:
        op.execute(
            f"GRANT SELECT, INSERT, UPDATE ON TABLE {_SCHEMA}.{table} " f"TO {_ROLE_APPLICATION}"
        )
        op.execute(f"REVOKE DELETE ON TABLE {_SCHEMA}.{table} FROM {_ROLE_APPLICATION}")


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.execute(f"REVOKE ALL ON TABLE {_SCHEMA}.{table} FROM {_ROLE_APPLICATION}")
        op.drop_table(table, schema=_SCHEMA)
    op.execute(f"REVOKE USAGE ON SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}")

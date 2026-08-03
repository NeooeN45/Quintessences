"""Cycle complet du compte local Quintessences.

DEC-000046. Ajoute les codes à usage unique, toujours hachés avec Argon2id,
et une version de session incrémentée après réinitialisation du mot de passe.

Revision ID: 20260803_0030
Revises: 20260803_0029
Create Date: 2026-08-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260803_0030"
down_revision: str | None = "20260803_0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_rgpd_identites"
_ROLE_APPLICATION = "gsie_application"
_TABLE = "identity_action_token"


def upgrade() -> None:
    op.add_column(
        "user_account",
        sa.Column("session_version", sa.Integer(), server_default="1", nullable=False),
        schema=_SCHEMA,
    )
    op.create_check_constraint(
        "ck_user_account_session_version",
        "user_account",
        "session_version > 0",
        schema=_SCHEMA,
    )
    op.create_table(
        _TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("code_hash", sa.String(length=500), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "purpose IN ('verify_email', 'reset_password')",
            name="ck_identity_action_token_purpose",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            [f"{_SCHEMA}.user_account.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_identity_action_token_active",
        _TABLE,
        ["account_id", "purpose", "consumed_at"],
        schema=_SCHEMA,
    )
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON TABLE {_SCHEMA}.{_TABLE} TO {_ROLE_APPLICATION}")
    op.execute(f"REVOKE DELETE ON TABLE {_SCHEMA}.{_TABLE} FROM {_ROLE_APPLICATION}")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON TABLE {_SCHEMA}.{_TABLE} FROM {_ROLE_APPLICATION}")
    op.drop_table(_TABLE, schema=_SCHEMA)
    op.drop_constraint(
        "ck_user_account_session_version",
        "user_account",
        schema=_SCHEMA,
        type_="check",
    )
    op.drop_column("user_account", "session_version", schema=_SCHEMA)

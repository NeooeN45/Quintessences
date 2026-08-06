"""Suppression différée et annulation RGPD du compte.

Révision: 20260806_0042
Précède: 20260806_0041
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260806_0042"
down_revision: str | None = "20260806_0041"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_IDENTITY_SCHEMA = "gsie_rgpd_identites"


def upgrade() -> None:
    op.add_column(
        "user_account",
        sa.Column("deletion_requested_at", sa.DateTime(timezone=True), nullable=True),
        schema=_IDENTITY_SCHEMA,
    )
    op.add_column(
        "user_account",
        sa.Column("deletion_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        schema=_IDENTITY_SCHEMA,
    )
    op.create_index(
        "idx_user_account_deletion_schedule",
        "user_account",
        ["status", "deletion_scheduled_at"],
        schema=_IDENTITY_SCHEMA,
    )
    op.drop_constraint(
        "ck_identity_action_token_purpose",
        "identity_action_token",
        schema=_IDENTITY_SCHEMA,
        type_="check",
    )
    op.create_check_constraint(
        "ck_identity_action_token_purpose",
        "identity_action_token",
        "purpose IN ('verify_email', 'reset_password', 'cancel_deletion')",
        schema=_IDENTITY_SCHEMA,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_identity_action_token_purpose",
        "identity_action_token",
        schema=_IDENTITY_SCHEMA,
        type_="check",
    )
    op.create_check_constraint(
        "ck_identity_action_token_purpose",
        "identity_action_token",
        "purpose IN ('verify_email', 'reset_password')",
        schema=_IDENTITY_SCHEMA,
    )
    op.drop_index(
        "idx_user_account_deletion_schedule", table_name="user_account", schema=_IDENTITY_SCHEMA
    )
    op.drop_column("user_account", "deletion_scheduled_at", schema=_IDENTITY_SCHEMA)
    op.drop_column("user_account", "deletion_requested_at", schema=_IDENTITY_SCHEMA)

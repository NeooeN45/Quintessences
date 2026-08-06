"""Demandes de changement d'adresse e-mail à double confirmation.

Révision: 20260806_0041
Précède: 20260805_0039
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260806_0041"
down_revision: str | None = "20260805_0039"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_rgpd_identites"


def upgrade() -> None:
    op.create_table(
        "email_change_request",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column(
            "account_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey(f"{_SCHEMA}.user_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("current_email_normalized", sa.String(320), nullable=False),
        sa.Column("new_email_normalized", sa.String(320), nullable=False),
        sa.Column("current_code_hash", sa.String(500), nullable=False),
        sa.Column("new_code_hash", sa.String(500), nullable=False),
        sa.Column("current_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("new_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_email_change_request_active",
        "email_change_request",
        ["account_id", "completed_at", "expires_at"],
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_email_change_request_new_email",
        "email_change_request",
        ["new_email_normalized", "completed_at"],
        schema=_SCHEMA,
    )
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE ON TABLE {_SCHEMA}.email_change_request TO gsie_application"
    )
    op.execute(f"REVOKE DELETE ON TABLE {_SCHEMA}.email_change_request FROM gsie_application")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON TABLE {_SCHEMA}.email_change_request FROM gsie_application")
    op.drop_index(
        "idx_email_change_request_new_email", table_name="email_change_request", schema=_SCHEMA
    )
    op.drop_index(
        "idx_email_change_request_active", table_name="email_change_request", schema=_SCHEMA
    )
    op.drop_table("email_change_request", schema=_SCHEMA)

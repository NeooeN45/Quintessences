"""Consentements juridiques versionnés du compte Quintessences.

Révision: 20260806_0043
Précède: 20260806_0042
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260806_0043"
down_revision: str | None = "20260806_0042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_rgpd_identites"


def upgrade() -> None:
    op.create_table(
        "account_consent",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column(
            "account_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey(f"{_SCHEMA}.user_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("consent_type", sa.String(64), nullable=False),
        sa.Column("document_version", sa.String(32), nullable=False),
        sa.Column(
            "accepted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "account_id",
            "consent_type",
            "document_version",
            name="uq_account_consent_version",
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_account_consent_active",
        "account_consent",
        ["account_id", "consent_type", "revoked_at"],
        schema=_SCHEMA,
    )
    op.execute(f"ALTER TABLE {_SCHEMA}.account_consent ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_SCHEMA}.account_consent FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY account_consent_scope ON {_SCHEMA}.account_consent
        USING (account_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
        WITH CHECK (account_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
        """
    )
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE ON TABLE {_SCHEMA}.account_consent TO gsie_application"
    )
    op.execute(f"REVOKE DELETE ON TABLE {_SCHEMA}.account_consent FROM gsie_application")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON TABLE {_SCHEMA}.account_consent FROM gsie_application")
    op.execute(f"DROP POLICY IF EXISTS account_consent_scope ON {_SCHEMA}.account_consent")
    op.drop_index("idx_account_consent_active", table_name="account_consent", schema=_SCHEMA)
    op.drop_table("account_consent", schema=_SCHEMA)

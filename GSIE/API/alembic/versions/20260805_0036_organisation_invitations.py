"""Invitations d'organisation par e-mail à usage unique.

Révision: 20260805_0036
Précède: 20260805_0035
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260805_0036"
down_revision: str | None = "20260805_0035"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_organisations"


def upgrade() -> None:
    op.create_table(
        "organisation_invitation",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column(
            "organisation_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey(f"{_SCHEMA}.organisation.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email_normalized", sa.String(320), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default=sa.text("'member'")),
        sa.Column(
            "invited_by",
            PGUUID(as_uuid=True),
            sa.ForeignKey("gsie_rgpd_identites.user_account.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "role IN ('admin', 'member')",
            name="ck_organisation_invitation_role",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_organisation_invitation_token_hash"),
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_organisation_invitation_org",
        "organisation_invitation",
        ["organisation_id", "created_at"],
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_organisation_invitation_email",
        "organisation_invitation",
        ["email_normalized", "expires_at"],
        schema=_SCHEMA,
    )
    op.execute(f"ALTER TABLE {_SCHEMA}.organisation_invitation ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_SCHEMA}.organisation_invitation FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY organisation_invitation_visible
        ON {_SCHEMA}.organisation_invitation
        USING (
            {_SCHEMA}.has_org_role(organisation_id, ARRAY['owner', 'admin'])
            OR email_normalized IN (
                SELECT email_normalized
                FROM gsie_rgpd_identites.identity_provider_link
                WHERE account_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
                  AND revoked_at IS NULL
                  AND email_normalized IS NOT NULL
                  AND email_verified IS TRUE
            )
        )
        WITH CHECK (
            {_SCHEMA}.has_org_role(organisation_id, ARRAY['owner', 'admin'])
        )
        """
    )
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE ON TABLE {_SCHEMA}.organisation_invitation TO gsie_application"
    )
    op.execute(f"REVOKE DELETE ON TABLE {_SCHEMA}.organisation_invitation FROM gsie_application")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON TABLE {_SCHEMA}.organisation_invitation FROM gsie_application")
    op.execute(
        f"DROP POLICY IF EXISTS organisation_invitation_visible ON {_SCHEMA}.organisation_invitation"
    )
    op.drop_index(
        "idx_organisation_invitation_email", table_name="organisation_invitation", schema=_SCHEMA
    )
    op.drop_index(
        "idx_organisation_invitation_org", table_name="organisation_invitation", schema=_SCHEMA
    )
    op.drop_table("organisation_invitation", schema=_SCHEMA)

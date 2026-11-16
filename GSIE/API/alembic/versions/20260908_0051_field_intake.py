"""Ajoute la table d intake applicatif en quarantaine.

Revision ID: 20260908_0051
Revises: 20260815_0050
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260908_0051"
down_revision: str | None = "20260815_0050"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Persiste les soumissions terrain avant leur qualification canonique."""
    op.create_table(
        "field_intake",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_key", sa.String(length=100), nullable=False),
        sa.Column("client_event_id", sa.String(length=200), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("target_resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('quarantined', 'accepted', 'rejected')",
            name="ck_field_intake_status",
        ),
        sa.ForeignKeyConstraint(["target_resource_id"], ["resource.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "application_key",
            "client_event_id",
            name="uq_field_intake_application_event",
        ),
    )
    op.create_index("ix_field_intake_submitted_by", "field_intake", ["submitted_by"])
    op.create_index("ix_field_intake_target_resource_id", "field_intake", ["target_resource_id"])
    op.create_index(
        "ix_field_intake_submitted_by_received",
        "field_intake",
        ["submitted_by", "received_at"],
    )
    op.create_index(
        "ix_field_intake_status_received",
        "field_intake",
        ["status", "received_at"],
    )


def downgrade() -> None:
    """Retire la table de quarantaine et ses index."""
    op.drop_index("ix_field_intake_status_received", table_name="field_intake")
    op.drop_index("ix_field_intake_submitted_by_received", table_name="field_intake")
    op.drop_index("ix_field_intake_target_resource_id", table_name="field_intake")
    op.drop_index("ix_field_intake_submitted_by", table_name="field_intake")
    op.drop_table("field_intake")

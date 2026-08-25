"""Ajoute la table d'intake stationnel et ses index de lecture.

Revision ID: 20260823_0051
Revises: 20260815_0050
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260823_0051"
down_revision: str | None = "20260815_0050"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crée le sas append-only des soumissions stationnelles."""
    op.create_table(
        "field_intake",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("submitted_by", PGUUID(as_uuid=True), nullable=False),
        sa.Column("application_key", sa.String(100), nullable=False),
        sa.Column("client_event_id", sa.String(200), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("provenance", JSONB, nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column(
            "target_resource_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("resource.id"),
            nullable=True,
        ),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", PGUUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "application_key",
            "client_event_id",
            name="uq_field_intake_application_event",
        ),
        sa.CheckConstraint(
            "status IN ('quarantined', 'accepted', 'rejected')",
            name="ck_field_intake_status",
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
    """Retire la table d'intake lors d'un rollback explicite."""
    op.drop_index("ix_field_intake_status_received", table_name="field_intake")
    op.drop_index("ix_field_intake_submitted_by_received", table_name="field_intake")
    op.drop_index("ix_field_intake_target_resource_id", table_name="field_intake")
    op.drop_index("ix_field_intake_submitted_by", table_name="field_intake")
    op.drop_table("field_intake")

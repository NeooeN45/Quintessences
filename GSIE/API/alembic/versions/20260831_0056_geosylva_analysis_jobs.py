"""Jobs asynchrones propriétaires du BFF GeoSylva.

Revision ID: 20260831_0056
Revises: 20260826_0055
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260831_0056"
down_revision: str | None = "20260826_0055"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_rgpd_identites"
_TABLE = "geosylva_analysis_job"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "account_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey(f"{_SCHEMA}.user_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("request_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("station_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("request_payload", JSONB, nullable=False),
        sa.Column("preparation_snapshot", JSONB, nullable=True),
        sa.Column("result_payload", JSONB, nullable=True),
        sa.Column("analysis_run_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column(
            "completed_engines", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column(
            "unavailable_engines", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column("warnings", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(100), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "account_id", "request_id", name="uq_geosylva_analysis_account_request"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'partial', 'completed', 'failed', 'expired')",
            name="ck_geosylva_analysis_status",
        ),
        sa.CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100",
            name="ck_geosylva_analysis_progress",
        ),
        sa.CheckConstraint("attempt_count >= 0", name="ck_geosylva_analysis_attempts"),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_geosylva_analysis_account_status",
        _TABLE,
        ["account_id", "status", "created_at"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_geosylva_analysis_queue",
        _TABLE,
        ["status", "next_attempt_at", "created_at"],
        schema=_SCHEMA,
    )
    op.create_index("ix_geosylva_analysis_expiry", _TABLE, ["expires_at"], schema=_SCHEMA)
    op.execute(f"REVOKE ALL ON {_SCHEMA}.{_TABLE} FROM PUBLIC")
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON {_SCHEMA}.{_TABLE} TO gsie_application")


def downgrade() -> None:
    op.drop_index("ix_geosylva_analysis_expiry", table_name=_TABLE, schema=_SCHEMA)
    op.drop_index("ix_geosylva_analysis_queue", table_name=_TABLE, schema=_SCHEMA)
    op.drop_index("ix_geosylva_analysis_account_status", table_name=_TABLE, schema=_SCHEMA)
    op.drop_table(_TABLE, schema=_SCHEMA)

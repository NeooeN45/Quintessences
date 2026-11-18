"""Sessions de cubage offline-first GeoSylva.

Revision ID: 20260831_0057
Revises: 20260831_0056
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260831_0057"
down_revision: str | None = "20260831_0056"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_rgpd_identites"
_TABLE = "geosylva_cubage_session"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("session_id", PGUUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "account_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey(f"{_SCHEMA}.user_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("calculation_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("idempotency_key", sa.String(36), nullable=False),
        sa.Column("session_fingerprint", sa.String(64), nullable=False),
        sa.Column("measurements_fingerprint", sa.String(64), nullable=False),
        sa.Column("inputs_fingerprint", sa.String(64), nullable=False),
        sa.Column("result_fingerprint", sa.String(64), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="synced"),
        sa.Column("request_payload", JSONB, nullable=False),
        sa.Column("verification_payload", JSONB, nullable=True),
        sa.Column("warnings", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("trace_id", sa.String(100), nullable=False),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "account_id",
            "session_id",
            name="uq_geosylva_cubage_account_session",
        ),
        sa.UniqueConstraint(
            "account_id",
            "idempotency_key",
            name="uq_geosylva_cubage_account_idempotency",
        ),
        sa.CheckConstraint(
            "status IN ('accepted', 'synced', 'review_required', 'rejected', 'retryable_error')",
            name="ck_geosylva_cubage_status",
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_geosylva_cubage_account_status",
        _TABLE,
        ["account_id", "status", "created_at"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_geosylva_cubage_calculation",
        _TABLE,
        ["calculation_id"],
        schema=_SCHEMA,
    )
    op.execute(f"REVOKE ALL ON {_SCHEMA}.{_TABLE} FROM PUBLIC")
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON {_SCHEMA}.{_TABLE} TO gsie_application")


def downgrade() -> None:
    op.drop_index("ix_geosylva_cubage_calculation", table_name=_TABLE, schema=_SCHEMA)
    op.drop_index("ix_geosylva_cubage_account_status", table_name=_TABLE, schema=_SCHEMA)
    op.drop_table(_TABLE, schema=_SCHEMA)

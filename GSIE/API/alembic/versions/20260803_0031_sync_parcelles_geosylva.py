"""Synchronisation privée des parcelles GeoSylva.

Revision ID: 20260803_0031
Revises: 20260803_0030
Create Date: 2026-08-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260803_0031"
down_revision: str | None = "20260803_0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_synchronisation"
_TABLE = "geosylva_parcels"
_ROLE_APPLICATION = "gsie_application"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {_SCHEMA}")
    op.create_table(
        _TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_id", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("client_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("server_version", sa.Integer(), nullable=False),
        sa.Column("last_operation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("server_version > 0", name="ck_geosylva_parcels_version"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["gsie_rgpd_identites.user_account.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_id", "client_id", name="uq_geosylva_parcels_owner_client"),
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_geosylva_parcels_owner_updated",
        _TABLE,
        ["account_id", "updated_at"],
        schema=_SCHEMA,
    )
    op.execute(f"ALTER TABLE {_SCHEMA}.{_TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_SCHEMA}.{_TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY geosylva_parcels_owner ON {_SCHEMA}.{_TABLE} "
        "USING (account_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid) "
        "WITH CHECK (account_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)"
    )
    op.execute(f"GRANT USAGE ON SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}")
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON TABLE {_SCHEMA}.{_TABLE} TO {_ROLE_APPLICATION}")
    op.execute(f"REVOKE DELETE ON TABLE {_SCHEMA}.{_TABLE} FROM {_ROLE_APPLICATION}")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON TABLE {_SCHEMA}.{_TABLE} FROM {_ROLE_APPLICATION}")
    op.drop_table(_TABLE, schema=_SCHEMA)
    op.execute(f"REVOKE USAGE ON SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}")
    op.execute(f"DROP SCHEMA IF EXISTS {_SCHEMA}")

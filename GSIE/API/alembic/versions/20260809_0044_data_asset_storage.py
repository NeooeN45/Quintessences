"""Ajout des URI de stockage et de l'algorithme de checksum des actifs.

Révision: 20260809_0044
Précède: 20260806_0043
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260809_0044"
down_revision: str | None = "20260806_0043"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "data_asset",
        sa.Column("storage_uri", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "data_asset",
        sa.Column("checksum_algorithm", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("data_asset", "checksum_algorithm")
    op.drop_column("data_asset", "storage_uri")

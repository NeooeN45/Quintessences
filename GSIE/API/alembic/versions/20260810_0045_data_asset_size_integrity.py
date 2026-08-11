"""Rend la taille des DataAsset adaptée aux fichiers volumineux et non négative.

Révision: 20260810_0045
Précède: 20260809_0044
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260810_0045"
down_revision: str | None = "20260809_0044"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Passe de INTEGER à BIGINT puis pose l'invariant de taille."""
    op.alter_column(
        "data_asset",
        "size_bytes",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "ck_data_asset_size_non_negative",
        "data_asset",
        "size_bytes >= 0",
    )


def downgrade() -> None:
    """Retire l'invariant puis revient au schéma historique.

    Le downgrade est volontairement strict : PostgreSQL refusera la conversion
    si des assets dépassent la capacité d'un INTEGER, évitant une troncature
    silencieuse.
    """
    op.drop_constraint("ck_data_asset_size_non_negative", "data_asset", type_="check")
    op.alter_column(
        "data_asset",
        "size_bytes",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
    )

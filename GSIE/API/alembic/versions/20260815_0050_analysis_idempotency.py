"""Ajoute l'empreinte d'idempotence des analyses d'orchestration.

Revision ID: 20260815_0050
Revises: 20260813_0049
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0050"
down_revision: str | None = "20260813_0049"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Conserve l'empreinte de la requête avec la preuve append-only."""
    op.add_column(
        "analysis_run",
        sa.Column("requete_fingerprint", sa.String(64), nullable=True),
    )
    op.create_index(
        "uq_analysis_run_requete_fingerprint",
        "analysis_run",
        ["requete_origine", "requete_fingerprint"],
        unique=True,
        postgresql_where=sa.text("requete_fingerprint IS NOT NULL"),
    )


def downgrade() -> None:
    """Retire explicitement la garantie d'idempotence."""
    op.drop_index(
        "uq_analysis_run_requete_fingerprint",
        table_name="analysis_run",
    )
    op.drop_column("analysis_run", "requete_fingerprint")

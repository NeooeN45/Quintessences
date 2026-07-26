"""Reprise sur échec de l'outbox — backoff borné et lettre morte.

Ajoute à `outbox_event` le strict nécessaire pour qu'un échec de publication
soit un fait daté et compté, et non une simple absence de succès :

- `attempt_count`    — tentatives consommées ;
- `next_attempt_at`  — échéance de la prochaine tentative (backoff) ;
- `last_error_code`  — code normalisé du dernier échec, jamais un message ;
- `dead_lettered_at` — bascule en lettre morte après épuisement du quota.

Les événements déjà en base deviennent immédiatement éligibles
(`next_attempt_at = now()`), sans requalification de leur statut : la reprise
n'invente aucun état et ne perd aucun événement en attente.

Revision ID: 20260726_0002
Revises: 20260726_0001
Create Date: 2026-07-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260726_0002"
down_revision: str | None = "20260726_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "outbox_event"
_INDEX = "ix_outbox_status_next_attempt"


def upgrade() -> None:
    op.add_column(
        _TABLE,
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        _TABLE,
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.add_column(
        _TABLE,
        sa.Column("last_error_code", sa.String(length=100), nullable=True),
    )
    op.add_column(
        _TABLE,
        sa.Column("dead_lettered_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Index de sélection du worker : statut + échéance. Sans lui, le filtre
    # d'échéance dégénère en parcours complet dès que l'outbox s'allonge.
    op.create_index(_INDEX, _TABLE, ["status", "next_attempt_at"])


def downgrade() -> None:
    op.drop_index(_INDEX, table_name=_TABLE)
    op.drop_column(_TABLE, "dead_lettered_at")
    op.drop_column(_TABLE, "last_error_code")
    op.drop_column(_TABLE, "next_attempt_at")
    op.drop_column(_TABLE, "attempt_count")

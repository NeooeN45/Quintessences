"""Migration 0011 — Identification botanique assistée (RFC-0018, tranche 1/N)

Ajoute 3 nouveaux types de resource : `botanical_identification_request`,
`botanical_identification_result`, `botanical_identification_decision` —
voir RFC-0018 §5.1, DEC-000030 et
`GSIE/API/src/gsie_api/infrastructure/models/identification.py`.

Crée le nouvel enum `identification_decision_status`. Les autres enums
(`plant_organ`) sont uniquement utilisés côté Python/JSONB (pas de type
Postgres dédié — les organes sont stockés dans le JSONB `photos`).

Rollback : DROP des 3 tables et de l'enum `identification_decision_status`
uniquement. N'affecte aucune donnée existante.

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-20
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    from gsie_api.infrastructure.models import Base, identification  # noqa: F401

    tables_to_create = [
        identification.BotanicalIdentificationRequestModel.__table__,
        identification.BotanicalIdentificationResultModel.__table__,
        identification.BotanicalIdentificationDecisionModel.__table__,
    ]
    Base.metadata.create_all(bind=op.get_bind(), tables=tables_to_create)


def downgrade() -> None:
    op.drop_table("botanical_identification_decision")
    op.drop_table("botanical_identification_result")
    op.drop_table("botanical_identification_request")
    op.execute("DROP TYPE IF EXISTS identification_decision_status")

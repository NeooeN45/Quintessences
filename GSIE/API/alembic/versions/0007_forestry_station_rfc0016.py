"""Migration 0007 — Diagnostic stationnel (RFC-0016, tranche 2/10)

Ajoute 2 nouveaux types de resource : `station_type`, `station_observation`
— voir RFC-0016 §4.3 et
`GSIE/API/src/gsie_api/infrastructure/models/forestry.py`.

Réutilise l'enum PostgreSQL `lifecycle_status` déjà créé par la
migration 0002 (aucune recréation — `checkfirst=True`, comportement par
défaut de `Base.metadata.create_all`).

Rollback : DROP des 2 tables uniquement. N'affecte aucune donnée v6.2
existante.

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-19
"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    from gsie_api.infrastructure.models import Base, forestry  # noqa: F401

    tables_to_create = [
        forestry.StationTypeModel.__table__,
        forestry.StationObservationModel.__table__,
    ]
    Base.metadata.create_all(bind=op.get_bind(), tables=tables_to_create)


def downgrade() -> None:
    op.drop_table("station_observation")
    op.drop_table("station_type")

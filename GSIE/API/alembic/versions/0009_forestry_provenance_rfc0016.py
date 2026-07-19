"""Migration 0009 — Provenance / MFR (RFC-0016, tranche 4/10)

Ajoute 1 nouveau type de resource : `provenance_material` — voir
RFC-0016 §3.1 et
`GSIE/API/src/gsie_api/infrastructure/models/forestry.py`.

Réutilise l'enum PostgreSQL `lifecycle_status` déjà créé par la
migration 0002 (aucune recréation — `checkfirst=True`, comportement par
défaut de `Base.metadata.create_all`). Crée le nouvel enum
`materiel_base_category`.

Rollback : DROP de la table et de l'enum `materiel_base_category`
uniquement. N'affecte aucune donnée v6.2 existante.

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-19
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    from gsie_api.infrastructure.models import Base, forestry  # noqa: F401

    tables_to_create = [
        forestry.ProvenanceMaterialModel.__table__,
    ]
    Base.metadata.create_all(bind=op.get_bind(), tables=tables_to_create)


def downgrade() -> None:
    op.drop_table("provenance_material")
    op.execute("DROP TYPE IF EXISTS materiel_base_category")

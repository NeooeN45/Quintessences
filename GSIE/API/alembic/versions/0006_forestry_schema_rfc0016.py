"""Migration 0006 — Schéma forestier spécialisé (RFC-0016, tranche 1/10)

Ajoute 3 nouveaux types de resource : `autecology_profile`,
`site_index_model`, `fertility_class` — voir RFC-0016 §3.1 et
`GSIE/API/src/gsie_api/infrastructure/models/forestry.py`.

Réutilise les enums PostgreSQL `evidence_level` et `lifecycle_status`
déjà créés par la migration 0002 (aucune recréation — `checkfirst=True`,
comportement par défaut de `Base.metadata.create_all`).

Les sept autres entités du §4 du RFC (`StationType`/`StationObservation`,
`SilviculturalSystem`/`SilviculturalRule`/`Intervention`,
`ProvenanceMaterial`, `DiagnosticProtocol`/`HealthRisk`,
`EvidenceStatement`/`ConflictRecord`) restent à implémenter dans une
migration ultérieure.

Rollback : DROP des 3 tables uniquement. N'affecte aucune donnée v6.2
existante.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-19
"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    from gsie_api.infrastructure.models import Base, forestry  # noqa: F401

    tables_to_create = [
        forestry.AutecologyProfileModel.__table__,
        forestry.SiteIndexModelModel.__table__,
        forestry.FertilityClassModel.__table__,
    ]
    Base.metadata.create_all(bind=op.get_bind(), tables=tables_to_create)


def downgrade() -> None:
    op.drop_table("fertility_class")
    op.drop_table("site_index_model")
    op.drop_table("autecology_profile")

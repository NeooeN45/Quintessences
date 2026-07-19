"""Migration 0008 — Itinéraires sylvicoles (RFC-0016, tranche 3/10)

Ajoute 2 nouveaux types de resource : `silvicultural_system`,
`silvicultural_rule` — voir RFC-0016 §3.1 et
`GSIE/API/src/gsie_api/infrastructure/models/forestry.py`.

`Intervention` (troisième entité citée par le RFC) n'est pas concernée
par cette migration : elle existe déjà depuis la migration 0002
(type 75, `gsie_api.infrastructure.models.business.InterventionModel`).

Réutilise les enums PostgreSQL `lifecycle_status` et `evidence_level`
déjà créés par la migration 0002 (aucune recréation — `checkfirst=True`,
comportement par défaut de `Base.metadata.create_all`). Crée le nouvel
enum `silvicultural_system_category`.

Rollback : DROP des 2 tables et de l'enum `silvicultural_system_category`
uniquement. N'affecte aucune donnée v6.2 existante.

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-19
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    from gsie_api.infrastructure.models import Base, forestry  # noqa: F401

    tables_to_create = [
        forestry.SilviculturalSystemModel.__table__,
        forestry.SilviculturalRuleModel.__table__,
    ]
    Base.metadata.create_all(bind=op.get_bind(), tables=tables_to_create)


def downgrade() -> None:
    op.drop_table("silvicultural_rule")
    op.drop_table("silvicultural_system")
    op.execute("DROP TYPE IF EXISTS silvicultural_system_category")

"""Migration 0010 — Protocoles sanitaires (RFC-0016, tranche 5/10)

Ajoute 2 nouveaux types de resource : `diagnostic_protocol`,
`health_risk` — voir RFC-0016 §3.1 et
`GSIE/API/src/gsie_api/infrastructure/models/forestry.py`.

Réutilise l'enum PostgreSQL `lifecycle_status` déjà créé par la
migration 0002 (aucune recréation — `checkfirst=True`, comportement par
défaut de `Base.metadata.create_all`). Crée le nouvel enum
`health_risk_severity`.

Rollback : DROP des 2 tables et de l'enum `health_risk_severity`
uniquement. N'affecte aucune donnée v6.2 existante.

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-19
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    from gsie_api.infrastructure.models import Base, forestry  # noqa: F401

    tables_to_create = [
        forestry.DiagnosticProtocolModel.__table__,
        forestry.HealthRiskModel.__table__,
    ]
    Base.metadata.create_all(bind=op.get_bind(), tables=tables_to_create)


def downgrade() -> None:
    op.drop_table("health_risk")
    op.drop_table("diagnostic_protocol")
    op.execute("DROP TYPE IF EXISTS health_risk_severity")

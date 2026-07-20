"""Migration 0012 — Index sur les FK source_id des tables forestières RFC-0016

Dette de performance identifiée lors de l'audit du 2026-07-20 : les 10
tables satellite du schéma forestier spécialisé (RFC-0016 §3.1,
tranches 1-5/10) ont toutes une colonne `source_id` (FK vers
`resource.id`, obligatoire) sans index, alors que toutes les autres FK
de ces mêmes tables sont indexées. Ajoute `index=True` côté modèle
(`gsie_api.infrastructure.models.forestry`) et crée les index
correspondants ici pour les bases déjà déployées.

Requête typique accélérée : « toutes les assertions/observations
citant telle source » (`WHERE source_id = :x`), utile pour tracer
l'usage d'une source (GSIE-CON-005) à travers le schéma forestier.

Tables concernées : autecology_profile, site_index_model,
fertility_class, station_type, station_observation,
silvicultural_system, silvicultural_rule, diagnostic_protocol,
health_risk, provenance_material.

Rollback : DROP des 10 index uniquement. N'affecte aucune donnée.

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-20
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = [
    "autecology_profile",
    "site_index_model",
    "fertility_class",
    "station_type",
    "station_observation",
    "silvicultural_system",
    "silvicultural_rule",
    "diagnostic_protocol",
    "health_risk",
    "provenance_material",
]


def upgrade() -> None:
    for table in _TABLES:
        op.create_index(
            f"ix_{table}_source_id",
            table,
            ["source_id"],
            unique=False,
        )


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.drop_index(f"ix_{table}_source_id", table_name=table)

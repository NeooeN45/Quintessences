"""Schema de domaine gsie_foret — RFC-0029 §4.1, GSIE-PROMPT-0027.

Deuxieme des sept schemas de domaine. La foret est le domaine le plus
volumineux : douze tables quittent `public` pour `gsie_foret`.

| Table | Module | Raison |
|---|---|---|
| `management_plan` | business | Plan de gestion forestier (PSG CNPF / Aménagement ONF) |
| `intervention` | business | Intervention sylvicole programmée |
| `economic_scenario` | business | Scénario économique forestier (coûts, valeur bois) |
| `site_index_model` | forestry | Modèle de fertilité pour une essence |
| `fertility_class` | forestry | Classe de fertilité contextualisée |
| `station_type` | forestry | Type de station forestier |
| `station_observation` | forestry | Observation stationnelle (diagnostic) |
| `silvicultural_system` | forestry | Système sylvicole (itinéraire) |
| `silvicultural_rule` | forestry | Règle sylvicole |
| `diagnostic_protocol` | forestry | Protocole sanitaire (ARCHI, DEPERIS, IBP) |
| `health_risk` | forestry | Risque sanitaire forestier |
| `provenance_material` | forestry | Provenance/MFR (matériel forestier de reproduction) |

`resource` reste dans `public` (GSIE-PROMPT-0027 §1). Les clés étrangères
traversent les schémas : `ALTER TABLE SET SCHEMA` préserve les contraintes.

**Renommage des index.** Même mécanisme qu'en `20260728_0013` : `ALTER TABLE
SET SCHEMA` conserve les noms d'index (`ix_<table>_<col>`), mais SQLAlchemy
génère `ix_<schema>_<table>_<col>`. Chaque index est renommé après le
déplacement.

`gsie_application` reçoit SELECT/INSERT/UPDATE — jamais DELETE (CON-010).

Revision ID: 20260728_0014
Revises: 20260728_0013
Create Date: 2026-07-31
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0014"
down_revision: str | None = "20260728_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_foret"
_TABLES = (
    "management_plan",
    "intervention",
    "economic_scenario",
    "site_index_model",
    "fertility_class",
    "station_type",
    "station_observation",
    "silvicultural_system",
    "silvicultural_rule",
    "diagnostic_protocol",
    "health_risk",
    "provenance_material",
)

_INDEXED_COLUMNS: dict[str, tuple[str, ...]] = {
    "management_plan": (
        "spatial_scope_id",
        "status",
        "manager_id",
        "plan_type",
        "owner_id",
    ),
    "intervention": (
        "intervention_type",
        "plan_id",
        "status",
        "operator_id",
        "spatial_scope_id",
    ),
    "economic_scenario": ("category", "plan_id", "intervention_id"),
    "site_index_model": ("species_entity_id", "source_id"),
    "fertility_class": ("site_index_model_id", "source_id", "species_entity_id"),
    "station_type": ("source_id", "guide", "ser_greco_code"),
    "station_observation": ("plot_reference", "source_id", "station_type_id"),
    "silvicultural_system": ("category", "source_id", "name"),
    "silvicultural_rule": (
        "species_entity_id",
        "silvicultural_system_id",
        "source_id",
    ),
    "diagnostic_protocol": ("source_id", "name"),
    "health_risk": ("source_id", "diagnostic_protocol_id", "subject_id"),
    "provenance_material": (
        "provenance_region",
        "species_entity_id",
        "base_material_category",
        "source_id",
    ),
}

_ROLE_APPLICATION = "gsie_application"
_ECRITURE = "SELECT, INSERT, UPDATE"


def _renommer_index(table: str, colonne: str, nouveau_schema: str) -> None:
    ancien = f"ix_{table}_{colonne}"
    nouveau = f"ix_{nouveau_schema}_{table}_{colonne}"
    op.execute(f"ALTER INDEX {nouveau_schema}.{ancien} RENAME TO {nouveau}")


def _restaurer_index(table: str, colonne: str, ancien_schema: str) -> None:
    ancien = f"ix_{ancien_schema}_{table}_{colonne}"
    nouveau = f"ix_{table}_{colonne}"
    op.execute(f"ALTER INDEX {ancien_schema}.{ancien} RENAME TO {nouveau}")


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {_SCHEMA}")

    for table in _TABLES:
        op.execute(f"ALTER TABLE public.{table} SET SCHEMA {_SCHEMA}")

    for table, colonnes in _INDEXED_COLUMNS.items():
        for colonne in colonnes:
            _renommer_index(table, colonne, _SCHEMA)

    op.execute(f"GRANT USAGE ON SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}")
    op.execute(f"GRANT {_ECRITURE} ON ALL TABLES IN SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}")
    op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {_SCHEMA} "
        f"GRANT {_ECRITURE} ON TABLES TO {_ROLE_APPLICATION}"
    )

    op.execute(
        f"COMMENT ON SCHEMA {_SCHEMA} IS "
        "'Domaine forestier : peuplements, itineraires, regles sylvicoles, "
        "dynamique. RFC-0029 §4.1.'"
    )


def downgrade() -> None:
    for table, colonnes in _INDEXED_COLUMNS.items():
        for colonne in colonnes:
            _restaurer_index(table, colonne, _SCHEMA)

    for table in _TABLES:
        op.execute(f"ALTER TABLE {_SCHEMA}.{table} SET SCHEMA public")

    op.execute(f"REVOKE {_ECRITURE} ON ALL TABLES IN SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}")
    op.execute(f"REVOKE USAGE ON SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {_SCHEMA} "
        f"REVOKE {_ECRITURE} ON TABLES FROM {_ROLE_APPLICATION}"
    )

    op.execute(f"DROP SCHEMA IF EXISTS {_SCHEMA} CASCADE")

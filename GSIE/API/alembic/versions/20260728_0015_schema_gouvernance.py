"""Schema de domaine gsie_gouvernance — RFC-0029 §4.1, GSIE-PROMPT-0027.

Troisieme des sept schemas de domaine. La gouvernance porte la chaine de
décision : six tables quittent `public` pour `gsie_gouvernance`.

| Table | Module | Raison |
|---|---|---|
| `regulation` | business | Réglementation structurée (code forestier, obligations) |
| `compliance_check` | business | Vérification de conformité réglementaire |
| `outcome_tracking` | business | Suivi de résultat post-recommandation |
| `conflict_cluster` | governance | Groupe d'assertions contradictoires |
| `decision` | reasoning | Décision prise par un humain (CON-001) |
| `recommendation` | reasoning | Recommandation produite par un moteur GSIE |

`resource` reste dans `public` (GSIE-PROMPT-0027 §1). Les clés étrangères
traversent les schémas : `ALTER TABLE SET SCHEMA` préserve les contraintes.
Aucune clé étrangère ne relie ces six tables entre elles — elles référencent
toutes `resource` (noyau) — donc aucune qualification de FK n'est nécessaire.

**Renommage des index.** Même mécanisme qu'en `20260728_0013` et `0014`.

`gsie_application` reçoit SELECT/INSERT/UPDATE — jamais DELETE (CON-010).

Revision ID: 20260728_0015
Revises: 20260728_0014
Create Date: 2026-07-31
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0015"
down_revision: str | None = "20260728_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_gouvernance"
_TABLES = (
    "regulation",
    "compliance_check",
    "outcome_tracking",
    "conflict_cluster",
    "decision",
    "recommendation",
)

_INDEXED_COLUMNS: dict[str, tuple[str, ...]] = {
    "regulation": ("code", "domain"),
    "compliance_check": ("status", "target_id", "checked_by", "regulation_id"),
    "outcome_tracking": ("decision_id", "status", "recommendation_id"),
    "conflict_cluster": ("status",),
    "decision": ("question_id", "decided_by", "scale_context_id"),
    "recommendation": (
        "question_id",
        "spatial_scope_id",
        "recommended_by",
        "scale_context_id",
        "temporal_context_id",
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
    op.execute(
        f"GRANT {_ECRITURE} ON ALL TABLES IN SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}"
    )
    op.execute(
        f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}"
    )
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {_SCHEMA} "
        f"GRANT {_ECRITURE} ON TABLES TO {_ROLE_APPLICATION}"
    )

    op.execute(
        f"COMMENT ON SCHEMA {_SCHEMA} IS "
        "'Domaine gouvernance : decisions, recommandations, validations, "
        "apprentissage. RFC-0029 §4.1.'"
    )


def downgrade() -> None:
    for table, colonnes in _INDEXED_COLUMNS.items():
        for colonne in colonnes:
            _restaurer_index(table, colonne, _SCHEMA)

    for table in _TABLES:
        op.execute(f"ALTER TABLE {_SCHEMA}.{table} SET SCHEMA public")

    op.execute(
        f"REVOKE {_ECRITURE} ON ALL TABLES IN SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}"
    )
    op.execute(f"REVOKE USAGE ON SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {_SCHEMA} "
        f"REVOKE {_ECRITURE} ON TABLES FROM {_ROLE_APPLICATION}"
    )

    op.execute(f"DROP SCHEMA IF EXISTS {_SCHEMA} CASCADE")

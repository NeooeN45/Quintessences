"""Row-Level Security sur les tables sensibles RGPD/gouvernance.

Audit sécurité 2026-07-27 (P0-4) — le principe de moindre privilège au niveau
rôle PostgreSQL (voir docker/init-roles.sql) ne suffit pas : `gsie_app` a besoin
de SELECT/INSERT/UPDATE/DELETE sur `consent`, `data_subject`, etc. pour servir
l'ensemble des utilisateurs. Sans RLS, une faille applicative (IDOR, injection)
expose l'intégralité de ces tables. RLS restreint chaque ligne visible/modifiable
selon le contexte de session posé par l'API (SET LOCAL) à chaque requête :

- `app.current_user_id`    — UUID de l'utilisateur authentifié.
- `app.current_user_roles` — liste de rôles séparés par des virgules
  (ex. "admin,researcher"), vérifiée avec LIKE '%role%'.

Tables couvertes et colonne « propriétaire » retenue (schéma existant, sans
ajout de colonne — aucune de ces tables ne porte de `created_by` explicite) :

- `consent`                     → `data_subject_id` (le sujet concerné)
- `data_subject`                → `id` (le sujet est sa propre ressource)
- `sensitivity_classification`  → `classified_by` (nullable)
- `access_policy`               → `principal` (identifiant de l'utilisateur/rôle cible)
- `sample`                      → `subject_id`
- `observation`                 → `subject_id`

Bypass admin/gouvernance : les rôles applicatifs `admin`, `dpo` (RGPD) et
`governance` voient/modifient toutes les lignes, quelle que soit la colonne
propriétaire. `FORCE ROW LEVEL SECURITY` garantit que même le propriétaire de
table (`gsie_migrator`) est soumis aux policies hors mode superuser/BYPASSRLS.

Revision ID: 20260727_0004
Revises: 20260727_0003
Create Date: 2026-07-27
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260727_0004"
down_revision: str | None = "20260727_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Rôles applicatifs qui contournent l'isolation par ligne (admin + gouvernance
# RGPD). Comparés via LIKE sur la liste CSV posée dans app.current_user_roles.
_BYPASS_ROLES: tuple[str, ...] = ("admin", "dpo", "governance")

# table -> colonne comparée à current_setting('app.current_user_id', true)
_TABLE_OWNER_COLUMN: dict[str, str] = {
    "consent": "data_subject_id",
    "data_subject": "id",
    "sensitivity_classification": "classified_by",
    "access_policy": "principal",
    "sample": "subject_id",
    "observation": "subject_id",
}

# `principal` est déjà de type text (identifiant libre) ; les autres colonnes
# sont des UUID et doivent être comparées en texte.
_TEXT_COLUMNS: frozenset[str] = frozenset({"principal"})


def _bypass_predicate() -> str:
    """Construit la clause OR de bypass rôle admin/dpo/governance."""
    clauses = [
        f"current_setting('app.current_user_roles', true) LIKE '%{role}%'"
        for role in _BYPASS_ROLES
    ]
    return " OR ".join(clauses)


def _owner_predicate(table: str, column: str) -> str:
    """Construit la clause de comparaison propriétaire pour une table."""
    column_expr = column if column in _TEXT_COLUMNS else f"{column}::text"
    return f"{column_expr} = current_setting('app.current_user_id', true)"


def upgrade() -> None:
    bypass = _bypass_predicate()
    for table, column in _TABLE_OWNER_COLUMN.items():
        owner_predicate = _owner_predicate(table, column)
        policy_name = f"{table}_isolation"
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {policy_name} ON {table} "
            f"USING ({bypass} OR {owner_predicate})"
        )


def downgrade() -> None:
    for table in _TABLE_OWNER_COLUMN:
        policy_name = f"{table}_isolation"
        op.execute(f"DROP POLICY IF EXISTS {policy_name} ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

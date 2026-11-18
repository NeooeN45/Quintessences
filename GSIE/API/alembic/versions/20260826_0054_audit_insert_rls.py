"""Sépare les politiques RLS de lecture et d'insertion de l'audit.

Les événements d'authentification peuvent être produits avant
l'authentification (échec de login) ou avant la pose du contexte RLS (login
réussi). La première politique ``audit_log_visible`` était implicite pour
toutes les opérations et refusait ces insertions légitimes.

Revision: 20260826_0054
Precede: 20260826_0053
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260826_0054"
down_revision: str | None = "20260826_0053"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_audit"
_TABLE = "audit_log"


def _current_user_uuid_expr() -> str:
    return "NULLIF(current_setting('app.current_user_id', true), '')::uuid"


def _current_user_roles_expr() -> str:
    return "COALESCE(current_setting('app.current_user_roles', true), '')"


def upgrade() -> None:
    """Autoriser les insertions contrôlées sans ouvrir la lecture."""
    op.execute(f"DROP POLICY IF EXISTS audit_log_visible ON {_SCHEMA}.{_TABLE}")
    op.execute(
        f"""
        CREATE POLICY audit_log_visible ON {_SCHEMA}.{_TABLE}
        FOR SELECT
        USING (
            actor_id = {_current_user_uuid_expr()}
            OR position('admin' IN {_current_user_roles_expr()}) > 0
        )
        """
    )
    op.execute(
        f"""
        CREATE POLICY audit_log_insert ON {_SCHEMA}.{_TABLE}
        FOR INSERT
        WITH CHECK (
            actor_id IS NULL
            OR actor_id = {_current_user_uuid_expr()}
        )
        """
    )


def downgrade() -> None:
    """Restaurer la politique historique unique, sans toucher aux données."""
    op.execute(f"DROP POLICY IF EXISTS audit_log_insert ON {_SCHEMA}.{_TABLE}")
    op.execute(f"DROP POLICY IF EXISTS audit_log_visible ON {_SCHEMA}.{_TABLE}")
    op.execute(
        f"""
        CREATE POLICY audit_log_visible ON {_SCHEMA}.{_TABLE}
        USING (
            actor_id = {_current_user_uuid_expr()}
            OR position('admin' IN {_current_user_roles_expr()}) > 0
        )
        """
    )

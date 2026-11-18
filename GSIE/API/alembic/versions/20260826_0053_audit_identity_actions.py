"""Autorise les événements détaillés de l'identité dans le journal d'audit.

Le module d'identité journalise des événements plus précis que les actions HTTP
génériques prévues par la première version du ``CHECK`` SQL. L'absence de ces
valeurs faisait échouer l'inscription après la création du compte et de son
abonnement, puis annulait toute la transaction.

Revision: 20260826_0053
Precede: 20260826_0052
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260826_0053"
down_revision: str | None = "20260826_0052"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_audit"
_TABLE = "audit_log"
_CONSTRAINT = "ck_audit_log_action_enum"
_ACTIONS = (
    "'create', 'read', 'update', 'delete', 'export', 'login', 'logout', "
    "'invite', 'revoke', 'sync', 'login_failed', 'login_locked', "
    "'login_mfa_challenge', 'login_success', 'mfa_disable_step_up_failed', "
    "'mfa_disabled', 'mfa_login_failed', 'mfa_recovery_failed', 'mfa_setup', "
    "'mfa_verify_failed', 'mfa_verify_success', 'oidc_link_required', "
    "'oidc_login_failed', 'register_password_compromised', 'register_password_weak', "
    "'register_success', 'session_revoked', 'sessions_revoked_all'"
)


def upgrade() -> None:
    """Étendre le domaine d'actions sans modifier les lignes existantes."""
    op.drop_constraint(_CONSTRAINT, _TABLE, schema=_SCHEMA, type_="check")
    op.create_check_constraint(
        _CONSTRAINT,
        _TABLE,
        f"action IN ({_ACTIONS})",
        schema=_SCHEMA,
    )


def downgrade() -> None:
    """Revenir au domaine historique des actions génériques."""
    op.drop_constraint(_CONSTRAINT, _TABLE, schema=_SCHEMA, type_="check")
    op.create_check_constraint(
        _CONSTRAINT,
        _TABLE,
        "action IN ('create', 'read', 'update', 'delete', 'export', 'login', "
        "'logout', 'invite', 'revoke', 'sync')",
        schema=_SCHEMA,
    )

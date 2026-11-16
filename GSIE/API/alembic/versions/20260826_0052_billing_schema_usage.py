"""Rattrapage du droit USAGE du role applicatif sur la facturation.

La migration 0038 accordait les droits sur les tables de ``gsie_billing``
mais oubliait le droit de resolution du schema. Une base migree pouvait donc
installer un compte local, puis echouer lors de la creation de son abonnement
gratuit.

Revision: 20260826_0052
Precede: 20260823_0051
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260826_0052"
down_revision: str | None = "20260823_0051"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_billing"
_ROLE_APPLICATION = "gsie_application"


def upgrade() -> None:
    """Permettre au role applicatif d'adresser les tables deja protegees."""
    op.execute(f"GRANT USAGE ON SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}")


def downgrade() -> None:
    """Retirer uniquement le droit ajoute par cette migration."""
    op.execute(f"REVOKE USAGE ON SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}")

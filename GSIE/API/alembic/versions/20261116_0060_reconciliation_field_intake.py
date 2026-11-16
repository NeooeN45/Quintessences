"""Vérifie l'intake commun après les deux lignées historiques.

Les bases déjà marquées 20260908_0051 ou 20260929_0059 n'exécutent pas
l'alias 20260908_0051 lors de leur upgrade. Cette vérification finale impose
donc le même contrat gelé à toutes les origines, sans corriger les dérives.

Revision ID: 20261116_0060
Revises: 20260929_0059
"""

from collections.abc import Sequence
from pathlib import Path
from runpy import run_path

from alembic import op

revision: str = "20261116_0060"
down_revision: str | None = "20260929_0059"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Refuse un intake absent ou divergent après chaque parcours historique."""
    if op.get_context().as_sql:
        raise RuntimeError(
            "Réconciliation public.field_intake impossible en mode hors ligne : "
            "la vérification du schéma PostgreSQL réel est obligatoire."
        )
    helper = Path(__file__).resolve().parents[1] / "compatibility" / "field_intake_v1.py"
    run_path(str(helper))["validate_field_intake_v1"](op.get_bind())


def downgrade() -> None:
    """Conserve intégralement l'intake : cette révision ne crée aucun objet."""

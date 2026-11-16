"""Conserve l'identifiant de l'intake main après sa création commune.

L'ancienne révision créait le même contrat que 20260823_0051, dans un autre
ordre physique de colonnes. Elle devient un alias vérifié sans recréation ni
suppression : les bases déjà marquées 20260908_0051 restent reconnues.

Revision ID: 20260908_0051
Revises: 20260823_0051
"""

from collections.abc import Sequence
from pathlib import Path
from runpy import run_path

from alembic import op

revision: str = "20260908_0051"
down_revision: str | None = "20260823_0051"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Vérifie le contrat historique sans réécrire le schéma ni les données."""
    if op.get_context().as_sql:
        raise RuntimeError(
            "Réconciliation public.field_intake impossible en mode hors ligne : "
            "la vérification du schéma PostgreSQL réel est obligatoire."
        )
    helper = Path(__file__).resolve().parents[1] / "compatibility" / "field_intake_v1.py"
    run_path(str(helper))["validate_field_intake_v1"](op.get_bind())


def downgrade() -> None:
    """Ne retire rien : cette révision ne crée aucun objet ni aucune donnée."""

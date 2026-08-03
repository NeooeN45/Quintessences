"""Table validation_result — persistance des sorties bloquées pour le Learning Engine.

Le Validation Engine (VALIDATION_ENGINE.md §3) persiste les résultats
`bloque` et `partiellement_valide` pour alimentation du Learning Engine
(RFC-0028) : sans persistance, un pattern de blocage récurrent disparaît
à la fin de la requête, et l'apprentissage ne peut pas le détecter.

La table est satellite de `resource` (ADR-001) : pas un type du
métamodèle (pas de `register_type`), mais un attribut multi-valué
d'une sortie validée. Elle pointe vers `resource(id)` avec
`ON DELETE CASCADE` — supprimer la resource supprime ses résultats
de validation.

Réversibilité : la table est supprimée au downgrade. Les résultats
persistés ne sont pas migrés (ils sont régénérables par rejeu des
validations).

Revision ID: 20260801_0028
Revises: 20260801_0027
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260801_0028"
down_revision: str | None = "20260801_0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crée la table validation_result et ses index."""
    op.create_table(
        "validation_result",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "requete_origine",
            PGUUID(as_uuid=True),
            sa.ForeignKey("resource.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("statut", sa.String(30), nullable=False),
        sa.Column("type_sortie", sa.String(30), nullable=False),
        sa.Column("controles", JSONB, nullable=False),
        sa.Column("causes_blocage", JSONB, nullable=False, server_default="[]"),
        sa.Column(
            "date_validation",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "idx_validation_result_statut",
        "validation_result",
        ["statut"],
    )
    op.create_index(
        "idx_validation_result_date",
        "validation_result",
        ["date_validation"],
    )
    op.create_index(
        "idx_validation_result_requete_origine",
        "validation_result",
        ["requete_origine"],
    )

    # Data dictionary — documente les colonnes pour l'exploitation.
    op.execute(
        "COMMENT ON TABLE validation_result IS "
        "'Résultats de validation bloqués/partiels — alimentation du Learning Engine (RFC-0028)'"
    )
    op.execute(
        "COMMENT ON COLUMN validation_result.statut IS "
        "'Statut de validation : bloque, partiellement_valide (jamais valide — non persisté)'"
    )
    op.execute(
        "COMMENT ON COLUMN validation_result.controles IS "
        "'Liste des contrôles appliqués avec leur résultat (JSONB)'"
    )
    op.execute(
        "COMMENT ON COLUMN validation_result.causes_blocage IS "
        "'Causes de blocage avec type et description (JSONB)'"
    )


def downgrade() -> None:
    """Supprime la table validation_result et ses index."""
    op.drop_index("idx_validation_result_requete_origine", table_name="validation_result")
    op.drop_index("idx_validation_result_date", table_name="validation_result")
    op.drop_index("idx_validation_result_statut", table_name="validation_result")
    op.drop_table("validation_result")

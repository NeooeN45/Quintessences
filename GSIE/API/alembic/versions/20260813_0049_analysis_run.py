"""Persistance de la preuve complète d'une analyse GSIE.

Revision ID: 20260813_0049
Revises: 20260810_0048
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260813_0049"
down_revision: str | None = "20260810_0048"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crée la table append-only de preuve d'orchestration."""
    op.create_table(
        "analysis_run",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("requete_origine", PGUUID(as_uuid=True), nullable=False),
        sa.Column("station_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("statut_validation", sa.String(30), nullable=False),
        sa.Column("moteur_orchestration_version", sa.String(30), nullable=False),
        sa.Column("contenu", JSONB, nullable=False),
        sa.Column("execute_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "statut_validation IN ('valide', 'bloque', 'partiellement_valide')",
            name="ck_analysis_run_validation_status",
        ),
    )
    op.create_index("idx_analysis_run_requete_origine", "analysis_run", ["requete_origine"])
    op.create_index("idx_analysis_run_station_id", "analysis_run", ["station_id"])
    op.create_index("idx_analysis_run_statut_validation", "analysis_run", ["statut_validation"])
    op.create_index("idx_analysis_run_execute_at", "analysis_run", ["execute_at"])
    op.create_index(
        "idx_analysis_run_requete_execute",
        "analysis_run",
        ["requete_origine", "execute_at"],
    )
    op.execute(
        "COMMENT ON TABLE analysis_run IS "
        "'Preuve append-only de la chaîne Reasoning, Diagnostic, Recommendation et Validation'"
    )
    op.execute(
        "COMMENT ON COLUMN analysis_run.contenu IS " "'Sorties intégrales des quatre moteurs'"
    )
    op.execute(
        """
        CREATE FUNCTION reject_analysis_run_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'analysis_run est append-only : mutation interdite';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER analysis_run_append_only
        BEFORE UPDATE OR DELETE ON analysis_run
        FOR EACH ROW EXECUTE FUNCTION reject_analysis_run_mutation()
        """
    )


def downgrade() -> None:
    """Supprime la table de preuve lors d'un downgrade explicite."""
    op.execute("DROP TRIGGER analysis_run_append_only ON analysis_run")
    op.execute("DROP FUNCTION reject_analysis_run_mutation()")
    op.drop_index("idx_analysis_run_requete_execute", table_name="analysis_run")
    op.drop_index("idx_analysis_run_execute_at", table_name="analysis_run")
    op.drop_index("idx_analysis_run_statut_validation", table_name="analysis_run")
    op.drop_index("idx_analysis_run_station_id", table_name="analysis_run")
    op.drop_index("idx_analysis_run_requete_origine", table_name="analysis_run")
    op.drop_table("analysis_run")

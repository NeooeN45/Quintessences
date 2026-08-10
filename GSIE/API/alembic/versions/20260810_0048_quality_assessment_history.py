"""Versionne les évaluations de qualité et verrouille leurs bornes.

Les lignes historiques deviennent chacune un run ``legacy`` autonome. Cela
préserve les données sans leur attribuer artificiellement un bilan global.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260810_0048"
down_revision: str | None = "20260810_0047"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "quality_assessment",
        sa.Column("assessment_run_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("quality_assessment", sa.Column("policy_version", sa.String(100), nullable=True))
    op.add_column("quality_assessment", sa.Column("weight", sa.Float(), nullable=True))
    op.add_column(
        "quality_assessment",
        sa.Column(
            "details", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
    )
    op.add_column(
        "quality_assessment",
        sa.Column("automated", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.execute(
        sa.text(
            "UPDATE quality_assessment SET assessment_run_id = id, "
            "policy_version = 'legacy', weight = 1.0 "
            "WHERE assessment_run_id IS NULL"
        )
    )
    op.alter_column("quality_assessment", "assessment_run_id", nullable=False)
    op.alter_column("quality_assessment", "policy_version", nullable=False)
    op.alter_column("quality_assessment", "weight", nullable=False)
    op.create_check_constraint(
        "ck_quality_assessment_score", "quality_assessment", "score >= 0 AND score <= 1"
    )
    op.create_check_constraint(
        "ck_quality_assessment_weight", "quality_assessment", "weight > 0 AND weight <= 1"
    )
    op.create_unique_constraint(
        "uq_quality_assessment_run_dimension",
        "quality_assessment",
        ["target_id", "assessment_run_id", "dimension"],
    )
    op.create_index("ix_quality_assessment_run_id", "quality_assessment", ["assessment_run_id"])
    op.create_index(
        "ix_quality_assessment_target_assessed",
        "quality_assessment",
        ["target_id", "assessed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_quality_assessment_target_assessed", table_name="quality_assessment")
    op.drop_index("ix_quality_assessment_run_id", table_name="quality_assessment")
    op.drop_constraint("uq_quality_assessment_run_dimension", "quality_assessment", type_="unique")
    op.drop_constraint("ck_quality_assessment_weight", "quality_assessment", type_="check")
    op.drop_constraint("ck_quality_assessment_score", "quality_assessment", type_="check")
    op.drop_column("quality_assessment", "automated")
    op.drop_column("quality_assessment", "details")
    op.drop_column("quality_assessment", "weight")
    op.drop_column("quality_assessment", "policy_version")
    op.drop_column("quality_assessment", "assessment_run_id")

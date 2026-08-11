"""Périmètre organisation/workspace de la racine resource.

Les ressources historiques restent globales lorsque les colonnes sont NULL.
Toute nouvelle ressource créée dans un contexte organisationnel porte son
organisation et, si fourni, son workspace.

Révision: 20260805_0037
Précède: 20260805_0036
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260805_0037"
down_revision: str | None = "20260805_0036"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "resource",
        sa.Column("organisation_id", PGUUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "resource",
        sa.Column("workspace_id", PGUUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_resource_organisation",
        "resource",
        "organisation",
        ["organisation_id"],
        ["id"],
        source_schema="public",
        referent_schema="gsie_organisations",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_resource_workspace",
        "resource",
        "workspace",
        ["workspace_id"],
        ["id"],
        source_schema="public",
        referent_schema="gsie_organisations",
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_resource_organisation_workspace",
        "resource",
        ["organisation_id", "workspace_id"],
        schema="public",
    )
    op.execute("ALTER TABLE public.resource ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.resource FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY resource_scope_visible ON public.resource
        USING (
            organisation_id IS NULL
            OR (
                organisation_id = NULLIF(
                    current_setting('app.current_organisation_id', true), ''
                )::uuid
                AND (
                    workspace_id IS NULL
                    OR workspace_id = NULLIF(
                        current_setting('app.current_workspace_id', true), ''
                    )::uuid
                )
            )
        )
        WITH CHECK (
            organisation_id IS NULL
            OR (
                organisation_id = NULLIF(
                    current_setting('app.current_organisation_id', true), ''
                )::uuid
                AND (
                    workspace_id IS NULL
                    OR workspace_id = NULLIF(
                        current_setting('app.current_workspace_id', true), ''
                    )::uuid
                )
            )
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS resource_scope_visible ON public.resource")
    op.drop_index("idx_resource_organisation_workspace", table_name="resource", schema="public")
    op.drop_constraint("fk_resource_workspace", "resource", schema="public", type_="foreignkey")
    op.drop_constraint("fk_resource_organisation", "resource", schema="public", type_="foreignkey")
    op.drop_column("resource", "workspace_id")
    op.drop_column("resource", "organisation_id")

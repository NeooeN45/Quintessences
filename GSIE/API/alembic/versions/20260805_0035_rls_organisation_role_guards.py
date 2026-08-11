"""Durcissement RLS des organisations et workspaces.

Les policies initiales de 0032 vérifiaient l'appartenance, mais pas le rôle
pour les opérations de gestion. Cette migration ajoute une fonction
SECURITY DEFINER dédiée aux rôles owner/admin et réécrit les policies afin
que la base protège aussi les invariants si une requête contourne le service.

Révision: 20260805_0035
Précède: 20260803_0034
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260805_0035"
down_revision: str | None = "20260803_0034"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_organisations"
_ROLE_APPLICATION = "gsie_application"


def _current_user() -> str:
    return "NULLIF(current_setting('app.current_user_id', true), '')::uuid"


def upgrade() -> None:
    current_user = _current_user()
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {_SCHEMA}.is_member(org_uuid uuid)
        RETURNS boolean
        LANGUAGE sql
        SECURITY DEFINER
        STABLE
        SET search_path = {_SCHEMA}, pg_catalog
        AS $$
            SELECT EXISTS (
                SELECT 1
                FROM {_SCHEMA}.organisation_member
                WHERE organisation_id = org_uuid
                  AND account_id = {current_user}
                  AND revoked_at IS NULL
            )
        $$;
        """
    )
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {_SCHEMA}.has_org_role(
            org_uuid uuid,
            allowed_roles text[]
        )
        RETURNS boolean
        LANGUAGE sql
        SECURITY DEFINER
        STABLE
        SET search_path = {_SCHEMA}, pg_catalog
        AS $$
            SELECT EXISTS (
                SELECT 1
                FROM {_SCHEMA}.organisation_member
                WHERE organisation_id = org_uuid
                  AND account_id = {current_user}
                  AND revoked_at IS NULL
                  AND role = ANY(allowed_roles)
            )
        $$;
        """
    )

    op.execute(f"DROP POLICY IF EXISTS organisation_visible ON {_SCHEMA}.organisation")
    op.execute(f"DROP POLICY IF EXISTS workspace_visible ON {_SCHEMA}.workspace")
    op.execute(f"DROP POLICY IF EXISTS member_visible ON {_SCHEMA}.organisation_member")

    op.execute(
        f"""
        CREATE POLICY organisation_visible ON {_SCHEMA}.organisation
        USING (
            created_by = {current_user}
            OR {_SCHEMA}.is_member(id)
        )
        WITH CHECK (created_by = {current_user})
        """
    )
    op.execute(
        f"""
        CREATE POLICY workspace_visible ON {_SCHEMA}.workspace
        USING (
            {_SCHEMA}.is_member(organisation_id)
            OR organisation_id IN (
                SELECT id
                FROM {_SCHEMA}.organisation
                WHERE created_by = {current_user}
            )
        )
        WITH CHECK (
            {_SCHEMA}.has_org_role(organisation_id, ARRAY['owner', 'admin'])
            OR organisation_id IN (
                SELECT id
                FROM {_SCHEMA}.organisation
                WHERE created_by = {current_user}
            )
        )
        """
    )
    op.execute(
        f"""
        CREATE POLICY member_visible ON {_SCHEMA}.organisation_member
        USING (
            account_id = {current_user}
            OR {_SCHEMA}.has_org_role(organisation_id, ARRAY['owner', 'admin'])
            OR EXISTS (
                SELECT 1
                FROM {_SCHEMA}.organisation
                WHERE id = {_SCHEMA}.organisation_member.organisation_id
                  AND created_by = {current_user}
            )
        )
        WITH CHECK (
            (
                account_id = {current_user}
                AND EXISTS (
                    SELECT 1
                    FROM {_SCHEMA}.organisation
                    WHERE id = {_SCHEMA}.organisation_member.organisation_id
                      AND created_by = {current_user}
                )
            )
            OR {_SCHEMA}.has_org_role(organisation_id, ARRAY['owner', 'admin'])
        )
        """
    )
    op.execute(f"REVOKE ALL ON FUNCTION {_SCHEMA}.is_member(uuid) FROM PUBLIC")
    op.execute(f"REVOKE ALL ON FUNCTION {_SCHEMA}.has_org_role(uuid, text[]) FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_SCHEMA}.is_member(uuid) TO {_ROLE_APPLICATION}")
    op.execute(
        f"GRANT EXECUTE ON FUNCTION {_SCHEMA}.has_org_role(uuid, text[]) TO {_ROLE_APPLICATION}"
    )


def downgrade() -> None:
    current_user = _current_user()
    op.execute(f"DROP POLICY IF EXISTS organisation_visible ON {_SCHEMA}.organisation")
    op.execute(f"DROP POLICY IF EXISTS workspace_visible ON {_SCHEMA}.workspace")
    op.execute(f"DROP POLICY IF EXISTS member_visible ON {_SCHEMA}.organisation_member")

    op.execute(
        f"""
        CREATE POLICY organisation_visible ON {_SCHEMA}.organisation
        USING (created_by = {current_user} OR {_SCHEMA}.is_member(id))
        WITH CHECK (created_by = {current_user})
        """
    )
    op.execute(
        f"""
        CREATE POLICY workspace_visible ON {_SCHEMA}.workspace
        USING (
            {_SCHEMA}.is_member(organisation_id)
            OR organisation_id IN (
                SELECT id FROM {_SCHEMA}.organisation
                WHERE created_by = {current_user}
            )
        )
        WITH CHECK (
            {_SCHEMA}.is_member(organisation_id)
            OR organisation_id IN (
                SELECT id FROM {_SCHEMA}.organisation
                WHERE created_by = {current_user}
            )
        )
        """
    )
    op.execute(
        f"""
        CREATE POLICY member_visible ON {_SCHEMA}.organisation_member
        USING (
            account_id = {current_user}
            OR EXISTS (
                SELECT 1 FROM {_SCHEMA}.organisation
                WHERE id = {_SCHEMA}.organisation_member.organisation_id
                  AND created_by = {current_user}
            )
        )
        WITH CHECK (
            account_id = {current_user}
            OR EXISTS (
                SELECT 1 FROM {_SCHEMA}.organisation
                WHERE id = {_SCHEMA}.organisation_member.organisation_id
                  AND created_by = {current_user}
            )
        )
        """
    )
    op.execute(
        f"REVOKE EXECUTE ON FUNCTION {_SCHEMA}.has_org_role(uuid, text[]) FROM {_ROLE_APPLICATION}"
    )
    op.execute(f"DROP FUNCTION IF EXISTS {_SCHEMA}.has_org_role(uuid, text[])")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_SCHEMA}.is_member(uuid) TO PUBLIC")

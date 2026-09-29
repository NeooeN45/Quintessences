"""Purge des tables GeoSylva et anonymisation de field_intake.

Révision: 20260929_0058
Précède: 20260831_0057

Corrige deux fuites de données personnelles à la suppression de compte :

- ``geosylva_analysis_job`` et ``geosylva_cubage_session`` portent une FK
  ``ON DELETE CASCADE`` vers ``user_account``, jamais déclenchée car le
  compte n'est pas supprimé physiquement (tombstone ``disabled``). Leurs
  lignes — dont les payloads géométriques — survivaient à la finalisation
  alors que l'audit attestait ``server_synced_data_purged: true``.
- ``field_intake.submitted_by`` n'a pas de FK vers ``user_account`` :
  l'UUID du compte supprimé restait donc ré-identifiable. Conformément à
  la décision Fondateur du 2026-09-29, les soumissions terrain sont
  conservées (traçabilité scientifique) mais rattachées à l'UUID
  sentinelle nul ``00000000-0000-0000-0000-000000000000``.

Le downgrade restaure la fonction de la révision 20260826_0055.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260929_0058"
down_revision: str | None = "20260831_0057"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_AUDIT_SCHEMA = "gsie_audit"
_IDENTITY_SCHEMA = "gsie_rgpd_identites"
_ANONYMIZED_SUBMITTER = "00000000-0000-0000-0000-000000000000"

_FINALIZER_BODY_0055 = """
        DECLARE
            v_account_id uuid;
            v_now timestamptz;
            v_processed integer := 0;
        BEGIN
            IF p_batch_size IS NULL OR p_batch_size < 1 OR p_batch_size > 1000 THEN
                RAISE EXCEPTION 'p_batch_size doit être compris entre 1 et 1000';
            END IF;

            FOR v_account_id IN
                SELECT id
                FROM gsie_rgpd_identites.user_account
                WHERE status = 'pending_deletion'
                  AND deleted_at IS NULL
                  AND deletion_scheduled_at IS NOT NULL
                  AND deletion_scheduled_at <= clock_timestamp()
                ORDER BY deletion_scheduled_at, id
                LIMIT p_batch_size
                FOR UPDATE SKIP LOCKED
            LOOP
                v_now := clock_timestamp();

                -- Les organisations, workspaces et invitations ne sont pas
                -- des données personnelles exclusivement rattachées au
                -- compte ; leurs références RESTRICT restent donc valides.
                DELETE FROM gsie_billing.entitlement
                WHERE account_id = v_account_id;
                DELETE FROM gsie_billing.subscription
                WHERE account_id = v_account_id;
                DELETE FROM gsie_synchronisation.geosylva_parcels
                WHERE account_id = v_account_id;
                DELETE FROM gsie_organisations.organisation_member
                WHERE account_id = v_account_id;

                DELETE FROM gsie_rgpd_identites.identity_action_token
                WHERE account_id = v_account_id;
                DELETE FROM gsie_rgpd_identites.email_change_request
                WHERE account_id = v_account_id;
                DELETE FROM gsie_rgpd_identites.mfa_recovery_code
                WHERE account_id = v_account_id;
                DELETE FROM gsie_rgpd_identites.mfa_secret
                WHERE account_id = v_account_id;
                DELETE FROM gsie_rgpd_identites.revoked_refresh_token
                WHERE account_id = v_account_id;
                DELETE FROM gsie_rgpd_identites.active_session
                WHERE account_id = v_account_id;
                DELETE FROM gsie_rgpd_identites.failed_login_attempt
                WHERE account_id = v_account_id;
                DELETE FROM gsie_rgpd_identites.account_consent
                WHERE account_id = v_account_id;
                DELETE FROM gsie_rgpd_identites.account_role
                WHERE account_id = v_account_id;
                DELETE FROM gsie_rgpd_identites.identity_provider_link
                WHERE account_id = v_account_id;

                -- L'audit garde la preuve structurelle, mais aucune adresse
                -- électronique historique ne survit à l'effacement RGPD.
                PERFORM set_config('gsie.audit_privacy_redaction', '1', true);
                UPDATE gsie_audit.audit_log
                SET actor_email = NULL
                WHERE actor_id = v_account_id
                  AND actor_email IS NOT NULL;
                PERFORM set_config('gsie.audit_privacy_redaction', '0', true);

                UPDATE gsie_rgpd_identites.user_account
                SET status = 'disabled',
                    display_name = NULL,
                    disabled_at = COALESCE(disabled_at, v_now),
                    deleted_at = COALESCE(deleted_at, v_now),
                    deletion_requested_at = NULL,
                    deletion_scheduled_at = NULL,
                    session_version = session_version + 1,
                    updated_at = v_now
                WHERE id = v_account_id;

                INSERT INTO gsie_audit.audit_log (
                    id,
                    timestamp,
                    actor_id,
                    actor_email,
                    action,
                    resource_type,
                    resource_id,
                    status_code,
                    details
                ) VALUES (
                    gen_random_uuid(),
                    v_now,
                    NULL,
                    NULL,
                    'delete',
                    'account',
                    v_account_id::text,
                    200,
                    jsonb_build_object(
                        'event', 'account_deletion_finalized',
                        'personal_data_redacted', true,
                        'server_synced_data_purged', true
                    )
                );

                v_processed := v_processed + 1;
            END LOOP;

            RETURN v_processed;
        END;
"""


def _finalizer_sql(body: str) -> str:
    """Assemble la fonction de finalisation autour d'un corps donné."""
    return f"""
        CREATE OR REPLACE FUNCTION {_IDENTITY_SCHEMA}.finalize_due_account_deletions(
            p_batch_size integer
        )
        RETURNS integer
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog
        AS $${body}$$;
        """


def upgrade() -> None:
    """Étend le finaliseur : purge GeoSylva + sentinelle sur field_intake."""
    body = _FINALIZER_BODY_0055.replace(
        "                DELETE FROM gsie_synchronisation.geosylva_parcels\n"
        "                WHERE account_id = v_account_id;\n",
        "                DELETE FROM gsie_synchronisation.geosylva_parcels\n"
        "                WHERE account_id = v_account_id;\n"
        "                DELETE FROM gsie_rgpd_identites.geosylva_analysis_job\n"
        "                WHERE account_id = v_account_id;\n"
        "                DELETE FROM gsie_rgpd_identites.geosylva_cubage_session\n"
        "                WHERE account_id = v_account_id;\n",
    ).replace(
        "                DELETE FROM gsie_organisations.organisation_member\n"
        "                WHERE account_id = v_account_id;\n",
        "                DELETE FROM gsie_organisations.organisation_member\n"
        "                WHERE account_id = v_account_id;\n\n"
        "                -- Soumissions terrain conservées mais désolidarisées :\n"
        "                -- l'UUID sentinelle remplace l'identifiant du compte\n"
        "                -- effacé (décision Fondateur 2026-09-29, anonymisation).\n"
        f"                UPDATE public.field_intake\n"
        f"                SET submitted_by = '{_ANONYMIZED_SUBMITTER}'::uuid\n"
        "                WHERE submitted_by = v_account_id;\n",
    )
    assert "geosylva_analysis_job" in body
    assert "field_intake" in body
    op.execute(_finalizer_sql(body))


def downgrade() -> None:
    """Restaure le finaliseur de la révision 20260826_0055."""
    op.execute(_finalizer_sql(_FINALIZER_BODY_0055))

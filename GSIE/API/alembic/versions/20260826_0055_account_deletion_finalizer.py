"""Finalisation différée du compte et anonymisation RGPD.

Révision: 20260826_0055
Précède: 20260826_0054

La fonction de finalisation est ``SECURITY DEFINER`` car le rôle applicatif ne
dispose volontairement pas de droits DELETE ni de bypass RLS. Elle conserve
les organisations partagées et les audits, mais purge les données rattachées
au compte et anonymise les adresses présentes dans l'audit.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260826_0055"
down_revision: str | None = "20260826_0054"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_AUDIT_SCHEMA = "gsie_audit"
_IDENTITY_SCHEMA = "gsie_rgpd_identites"
_ROLE_APPLICATION = "gsie_application"


def upgrade() -> None:
    """Installe l'exception d'anonymisation et le finaliseur par lots."""
    # La base de référence ne suppose pas pgcrypto ; la fonction est utilisée
    # uniquement pour générer l'identifiant de l'événement d'audit final.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    # Le journal reste append-only dans tous les cas ordinaires. La seule
    # mutation autorisée ici est actor_email -> NULL, sous un GUC local que
    # seule la fonction SECURITY DEFINER ci-dessous pose.
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {_AUDIT_SCHEMA}.prevent_audit_modification()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF TG_OP = 'UPDATE'
               AND current_setting('gsie.audit_privacy_redaction', true) = '1'
               AND NEW.actor_email IS NULL
               AND (to_jsonb(NEW) - 'actor_email') = (to_jsonb(OLD) - 'actor_email')
            THEN
                RETURN NEW;
            END IF;
            RAISE EXCEPTION 'audit_log est append-only : UPDATE et DELETE interdits';
        END;
        $$;
        """
    )

    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {_IDENTITY_SCHEMA}.finalize_due_account_deletions(
            p_batch_size integer
        )
        RETURNS integer
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog
        AS $$
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
                FROM {_IDENTITY_SCHEMA}.user_account
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

                DELETE FROM {_IDENTITY_SCHEMA}.identity_action_token
                WHERE account_id = v_account_id;
                DELETE FROM {_IDENTITY_SCHEMA}.email_change_request
                WHERE account_id = v_account_id;
                DELETE FROM {_IDENTITY_SCHEMA}.mfa_recovery_code
                WHERE account_id = v_account_id;
                DELETE FROM {_IDENTITY_SCHEMA}.mfa_secret
                WHERE account_id = v_account_id;
                DELETE FROM {_IDENTITY_SCHEMA}.revoked_refresh_token
                WHERE account_id = v_account_id;
                DELETE FROM {_IDENTITY_SCHEMA}.active_session
                WHERE account_id = v_account_id;
                DELETE FROM {_IDENTITY_SCHEMA}.failed_login_attempt
                WHERE account_id = v_account_id;
                DELETE FROM {_IDENTITY_SCHEMA}.account_consent
                WHERE account_id = v_account_id;
                DELETE FROM {_IDENTITY_SCHEMA}.account_role
                WHERE account_id = v_account_id;
                DELETE FROM {_IDENTITY_SCHEMA}.identity_provider_link
                WHERE account_id = v_account_id;

                -- L'audit garde la preuve structurelle, mais aucune adresse
                -- électronique historique ne survit à l'effacement RGPD.
                PERFORM set_config('gsie.audit_privacy_redaction', '1', true);
                UPDATE {_AUDIT_SCHEMA}.audit_log
                SET actor_email = NULL
                WHERE actor_id = v_account_id
                  AND actor_email IS NOT NULL;
                PERFORM set_config('gsie.audit_privacy_redaction', '0', true);

                UPDATE {_IDENTITY_SCHEMA}.user_account
                SET status = 'disabled',
                    display_name = NULL,
                    disabled_at = COALESCE(disabled_at, v_now),
                    deleted_at = COALESCE(deleted_at, v_now),
                    deletion_requested_at = NULL,
                    deletion_scheduled_at = NULL,
                    session_version = session_version + 1,
                    updated_at = v_now
                WHERE id = v_account_id;

                INSERT INTO {_AUDIT_SCHEMA}.audit_log (
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
        $$;
        """
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION {_IDENTITY_SCHEMA}.finalize_due_account_deletions(integer) FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION {_IDENTITY_SCHEMA}.finalize_due_account_deletions(integer) TO {_ROLE_APPLICATION}"
    )


def downgrade() -> None:
    """Retire le finaliseur et restaure l'append-only strict de l'audit."""
    op.execute(
        f"REVOKE EXECUTE ON FUNCTION {_IDENTITY_SCHEMA}.finalize_due_account_deletions(integer) FROM {_ROLE_APPLICATION}"
    )
    op.execute(
        f"DROP FUNCTION IF EXISTS {_IDENTITY_SCHEMA}.finalize_due_account_deletions(integer)"
    )
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {_AUDIT_SCHEMA}.prevent_audit_modification()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log est append-only : UPDATE et DELETE interdits';
        END;
        $$;
        """
    )

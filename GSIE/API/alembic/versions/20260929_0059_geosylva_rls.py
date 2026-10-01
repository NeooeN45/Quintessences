"""Durcissement RLS des tables GeoSylva du BFF.

Révision: 20260929_0059
Précède: 20260929_0058

Isolation : policy RLS propriétaire (comme ``geosylva_parcels``, migration
20260803_0031) sur ``geosylva_analysis_job`` et ``geosylva_cubage_session``,
dont les lignes portent des payloads géométriques et des paquets de cubage
personnels.

- ``geosylva_analysis_job`` : le worker asynchrone traite les jobs de tous
  les comptes ; il pose ``app.internal_worker = 'on'`` en contexte
  transaction-local (``set_internal_worker_context``) — même modèle de
  confiance que les GUC ``app.current_user_*`` déjà utilisées par les
  policies existantes.
- ``geosylva_cubage_session`` : aucun worker ne lit cette table ; la policy
  se limite au compte propriétaire, l'API pose ``app.current_user_id`` via
  ``get_db_user_rls``.

``FORCE ROW LEVEL SECURITY`` soumet aussi le propriétaire de table aux
policies ; le finaliseur RGPD (``finalize_due_account_deletions``,
SECURITY DEFINER) purge ces tables via les privilèges de son propriétaire,
comme il le fait déjà pour ``geosylva_parcels``.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260929_0059"
down_revision: str | None = "20260929_0058"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_rgpd_identites"
_TABLE_JOBS = "geosylva_analysis_job"
_TABLE_CUBAGE = "geosylva_cubage_session"
_ROLE_APPLICATION = "gsie_application"


def _enable_owner_rls(table: str, *, worker_bypass: bool) -> None:
    op.execute(f"REVOKE DELETE ON {_SCHEMA}.{table} FROM {_ROLE_APPLICATION}")
    op.execute(f"ALTER TABLE {_SCHEMA}.{table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_SCHEMA}.{table} FORCE ROW LEVEL SECURITY")
    predicate = "account_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid"
    if worker_bypass:
        predicate += " OR current_setting('app.internal_worker', true) = 'on'"
    op.execute(
        f"CREATE POLICY {table}_owner ON {_SCHEMA}.{table} "
        f"USING ({predicate}) WITH CHECK ({predicate})"
    )


def _disable_rls(table: str) -> None:
    op.execute(f"DROP POLICY IF EXISTS {table}_owner ON {_SCHEMA}.{table}")
    op.execute(f"ALTER TABLE {_SCHEMA}.{table} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_SCHEMA}.{table} DISABLE ROW LEVEL SECURITY")


def upgrade() -> None:
    _enable_owner_rls(_TABLE_JOBS, worker_bypass=True)
    _enable_owner_rls(_TABLE_CUBAGE, worker_bypass=False)


def downgrade() -> None:
    _disable_rls(_TABLE_CUBAGE)
    _disable_rls(_TABLE_JOBS)

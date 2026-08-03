"""rights_statement et spatial_disclosure_policy rejoignent gsie_rgpd.

Le contre-audit a releve que ces deux tables a semantique RGPD
(droits d'acces, politiques de divulgation) restaient dans `public`,
accessibles par `gsie_application` sans restriction particuliere.

`rights_statement` declare les licences et restrictions d'usage.
`spatial_disclosure_policy` declare la degradation spatiale (maille
10km public, exact gestionnaire). Les deux sont des politiques de
controle d'acces — elles appartiennent au schema RGPD.

Apres deplacement, `gsie_application` n'y a plus acces (REVOKE explicite
comme pour data_subject_consent en 0021).

Revision ID: 20260728_0023
Revises: 20260728_0022
Create Date: 2026-07-31
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0023"
down_revision: str | None = "20260728_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_rgpd"
_TABLES = ("rights_statement", "spatial_disclosure_policy")
_ROLE_APPLICATION = "gsie_application"
_ROLE_RGPD = "gsie_rgpd_manager"
_ECRITURE = "SELECT, INSERT, UPDATE"

# Index a renommer apres SET SCHEMA (convention ix_<schema>_<table>_<col>).
_INDEXES = (
    ("ix_rights_statement_licence", "ix_gsie_rgpd_rights_statement_licence"),
    ("ix_spatial_disclosure_policy_target_id", "ix_gsie_rgpd_spatial_disclosure_policy_target_id"),
)


def upgrade() -> None:
    for table in _TABLES:
        op.execute(f"ALTER TABLE public.{table} SET SCHEMA {_SCHEMA}")
        # `gsie_application` a recu SELECT/INSERT/UPDATE sur ALL TABLES IN
        # SCHEMA public (migration 0012). SET SCHEMA conserve les ACL —
        # REVOKE explicite pour retablir l'isolement.
        op.execute(f"REVOKE ALL ON {_SCHEMA}.{table} FROM {_ROLE_APPLICATION}")
        op.execute(f"REVOKE ALL ON {_SCHEMA}.{table} FROM PUBLIC")
        # Etendre les droits du gestionnaire RGPD.
        op.execute(f"GRANT {_ECRITURE} ON {_SCHEMA}.{table} TO {_ROLE_RGPD}")

    for ancien, nouveau in _INDEXES:
        op.execute(f"ALTER INDEX {_SCHEMA}.{ancien} RENAME TO {nouveau}")


def downgrade() -> None:
    for ancien, nouveau in _INDEXES:
        op.execute(f"ALTER INDEX {_SCHEMA}.{nouveau} RENAME TO {ancien}")

    for table in _TABLES:
        op.execute(f"REVOKE {_ECRITURE} ON {_SCHEMA}.{table} FROM {_ROLE_RGPD}")
        op.execute(f"ALTER TABLE {_SCHEMA}.{table} SET SCHEMA public")

"""data_subject_consent rejoint gsie_rgpd — coherence de l'isolement.

Le contre-audit de GSIE-PROMPT-0027 a releve que `data_subject_consent`,
table de jonction entre `data_subject` (gsie_rgpd_identites) et `consent`
(gsie_rgpd), restait dans `public`. Elle est accessible par
`gsie_application` qui n'a aucun droit sur les schemas RGPD — c'est une
**incoherence d'isolement** : la table de jonction contient des
identifiants qui permettent de relier un sujet a ses consentements.

La deplacer vers `gsie_rgpd` la place sous le meme controle d'acces que
`consent` et `sensitivity_classification`. `gsie_application` n'a aucun
droit sur `gsie_rgpd` (REVOKE explicite depuis 0012) — la table de
jonction devient inaccessible a l'application, comme les tables qu'elle
relie.

Les deux index (`ix_ds_consent_subject`, `ix_ds_consent_consent`) sont
renommes selon la convention `ix_<schema>_<table>_<col>`.

Revision ID: 20260728_0021
Revises: 20260728_0020
Create Date: 2026-07-31
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0021"
down_revision: str | None = "20260728_0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_rgpd"
_TABLE = "data_subject_consent"

# Index a renommer apres SET SCHEMA (convention ix_<schema>_<table>_<col>).
_INDEXES = (
    ("ix_ds_consent_subject", "ix_gsie_rgpd_data_subject_consent_data_subject_id"),
    ("ix_ds_consent_consent", "ix_gsie_rgpd_data_subject_consent_consent_id"),
)

_ROLE_RGPD = "gsie_rgpd_manager"
_ECRITURE = "SELECT, INSERT, UPDATE"


def upgrade() -> None:
    op.execute(f"ALTER TABLE public.{_TABLE} SET SCHEMA {_SCHEMA}")

    for ancien, nouveau in _INDEXES:
        op.execute(f"ALTER INDEX {_SCHEMA}.{ancien} RENAME TO {nouveau}")

    # Etendre les droits du gestionnaire RGPD a la table deplacee.
    op.execute(f"GRANT {_ECRITURE} ON {_SCHEMA}.{_TABLE} TO {_ROLE_RGPD}")

    # `gsie_application` a recu SELECT/INSERT/UPDATE sur ALL TABLES IN SCHEMA
    # public (migration 0012). `ALTER TABLE SET SCHEMA` conserve les ACL — il
    # ne les recalcule pas. Sans ce REVOKE explicite, l'application garde ses
    # droits sur la table deplacee, contournant l'isolement RGPD.
    op.execute(f"REVOKE ALL ON {_SCHEMA}.{_TABLE} FROM gsie_application")

    # Retirer les droits a PUBLIC (defense en profondeur, deja fait par 0011
    # sur le schema, mais la table arrive apres le GRANT initial).
    op.execute(f"REVOKE ALL ON {_SCHEMA}.{_TABLE} FROM PUBLIC")


def downgrade() -> None:
    # Retirer les droits avant de deplacer la table.
    op.execute(f"REVOKE {_ECRITURE} ON {_SCHEMA}.{_TABLE} FROM {_ROLE_RGPD}")

    for ancien, nouveau in _INDEXES:
        op.execute(f"ALTER INDEX {_SCHEMA}.{nouveau} RENAME TO {ancien}")

    op.execute(f"ALTER TABLE {_SCHEMA}.{_TABLE} SET SCHEMA public")

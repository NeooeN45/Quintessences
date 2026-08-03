"""Roles par moteur de domaine — RFC-0029 §4.2 moindre privilege.

Le contre-audit a releve que RFC-0029 §4.2 prevoyait des roles par
moteur (ex: `gsie_moteur_foret`, `gsie_moteur_climat`), mais que
seuls `gsie_application`, `gsie_rgpd_manager` et
`gsie_rgpd_identites_manager` existaient.

Cette migration cree un role NOLOGIN par moteur de domaine. Chaque
role herite de `gsie_application` (acces au noyau) et recoit USAGE sur
son schema de domaine. Le deploiement cree le compte de connexion et
lui accorde l'appartenance au role correspondant.

Les roles :
- `gsie_moteur_foret` : USAGE sur gsie_foret
- `gsie_moteur_botanique` : USAGE sur gsie_botanique
- `gsie_moteur_gouvernance` : USAGE sur gsie_gouvernance
- `gsie_moteur_climat` : USAGE sur gsie_climat
- `gsie_moteur_pedologie` : USAGE sur gsie_pedologie
- `gsie_moteur_hydro` : USAGE sur gsie_hydro
- `gsie_moteur_feu` : USAGE sur gsie_feu

Aucun droit sur gsie_rgpd ni gsie_rgpd_identites (herite de
gsie_application qui n'en a aucun).

Revision ID: 20260728_0022
Revises: 20260728_0021
Create Date: 2026-07-31
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0022"
down_revision: str | None = "20260728_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ROLE_APPLICATION = "gsie_application"

# (role, schema) — un role par moteur de domaine.
_MOTEURS = (
    ("gsie_moteur_foret", "gsie_foret"),
    ("gsie_moteur_botanique", "gsie_botanique"),
    ("gsie_moteur_gouvernance", "gsie_gouvernance"),
    ("gsie_moteur_climat", "gsie_climat"),
    ("gsie_moteur_pedologie", "gsie_pedologie"),
    ("gsie_moteur_hydro", "gsie_hydro"),
    ("gsie_moteur_feu", "gsie_feu"),
)


def upgrade() -> None:
    for role, schema in _MOTEURS:
        # Creer le role NOLOGIN s'il n'existe pas deja.
        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN
                    CREATE ROLE {role} NOLOGIN;
                END IF;
            END
            $$;
            """
        )
        # Heriter de gsie_application : acces au noyau, pas de DELETE, pas
        # d'acces RGPD. Le role de moteur est un sous-ensemble de
        # l'application, pas un super-ensemble.
        op.execute(f"GRANT {_ROLE_APPLICATION} TO {role}")
        # USAGE sur son schema de domaine — les droits sur les tables
        # sont deja accordes a gsie_application par les migrations 0013-0019.
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO {role}")
        op.execute(
            f"COMMENT ON ROLE {role} IS "
            f"'Moteur de domaine ({schema}). Herite de {_ROLE_APPLICATION} "
            f"(noyau sans DELETE, aucun acces RGPD). USAGE sur {schema}.'"
        )


def downgrade() -> None:
    for role, schema in _MOTEURS:
        # Retirer USAGE sur le schema de domaine avant de retirer le role.
        op.execute(f"REVOKE USAGE ON SCHEMA {schema} FROM {role}")
        # Retirer l'appartenance a gsie_application.
        op.execute(f"REVOKE {_ROLE_APPLICATION} FROM {role}")
        # DROP OWNED BY retire les droits que le role a reçus ou accordés,
        # sans quoi DROP ROLE échoue (DependentObjectsStillExistError).
        op.execute(f"DROP OWNED BY {role}")
        op.execute(f"DROP ROLE IF EXISTS {role}")

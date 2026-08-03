"""Comptes de connexion : l'application cesse d'etre superutilisateur.

Audit securite 2026-08-01, constat A. Le `docker-compose.yml` faisait
tourner l'API sous `POSTGRES_USER`, cree SUPERUSER et proprietaire de la
base par l'image officielle. Un superutilisateur ignore les ACL et
contourne RLS, `FORCE ROW LEVEL SECURITY` compris : tout ce que
construisent les migrations 0004 et 0011 a 0023 — l'isolement de
`gsie_rgpd_identites`, l'absence de DELETE (CON-010 structurel), les roles
par moteur — etait inoperant. Le cloisonnement existait sur le papier et
nulle part ailleurs.

Le chemin de deploiement correct n'existait pas non plus : aucun artefact
du depot ne creait de role LOGIN membre de `gsie_application`. La presente
migration ferme les deux manques :

1. Elle accorde `gsie_application` au compte de connexion de l'API
   (`gsie_api` par defaut), cree a l'initdb par
   `docker/init/04-comptes-de-connexion.sh`.
2. Elle cree `gsie_viz_lecture`, groupe de lecture seule destine aux
   outils de visualisation, et l'accorde a leur compte (`gsie_viz`).
   Ce groupe n'a **aucun** USAGE sur `gsie_rgpd` ni sur
   `gsie_rgpd_identites` : un outil de BI ne doit jamais pouvoir defaire
   le pseudonymat, quel que soit le SQL qu'on lui soumet.

Les GRANT aux comptes de connexion sont conditionnels : une base
initialisee avant cette migration ne les possede pas, et la migration ne
doit pas echouer pour autant. Le compte cree sans droits ne peut rien
lire — l'echec est ferme.

Revision ID: 20260801_0025
Revises: 20260731_0024
Create Date: 2026-08-01
"""

import os
from collections.abc import Sequence

from alembic import op

revision: str = "20260801_0025"
down_revision: str | None = "20260731_0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ROLE_APPLICATION = "gsie_application"
_ROLE_VIZ = "gsie_viz_lecture"

# Les sept schemas de domaine (RFC-0029). `public` porte le noyau.
_SCHEMAS_LISIBLES = (
    "public",
    "gsie_botanique",
    "gsie_foret",
    "gsie_gouvernance",
    "gsie_climat",
    "gsie_pedologie",
    "gsie_hydro",
    "gsie_feu",
)


def _compte_api() -> str:
    """Nom du compte de connexion de l'API, aligne sur le compose."""
    return os.environ.get("GSIE_API_DB_USER", "gsie_api")


def _compte_viz() -> str:
    """Nom du compte de connexion des outils de visualisation."""
    return os.environ.get("GSIE_VIZ_DB_USER", "gsie_viz")


def _grant_si_le_role_existe(groupe: str, membre: str) -> None:
    """Accorde `groupe` a `membre`, sans echouer si le membre n'existe pas."""
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{membre}') THEN
                EXECUTE 'GRANT {groupe} TO {membre}';
            ELSE
                RAISE NOTICE 'Role de connexion % absent : GRANT {groupe} ignore. '
                    'Creer le compte puis rejouer docker/comptes-de-connexion.sql.', '{membre}';
            END IF;
        END
        $$;
        """
    )


def _revoke_si_le_role_existe(groupe: str, membre: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{membre}') THEN
                EXECUTE 'REVOKE {groupe} FROM {membre}';
            END IF;
        END
        $$;
        """
    )


def upgrade() -> None:
    # --- Groupe de lecture seule pour les outils de visualisation ---
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{_ROLE_VIZ}') THEN
                CREATE ROLE {_ROLE_VIZ} NOLOGIN;
            END IF;
        END
        $$;
        """
    )
    for schema in _SCHEMAS_LISIBLES:
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO {_ROLE_VIZ}")
        op.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {_ROLE_VIZ}")
        # Sans ce defaut, toute table creee apres coup echapperait au groupe
        # et un exploitant serait tente de reaccorder large.
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO {_ROLE_VIZ}"
        )

    # Les deux schemas RGPD ne recoivent rien, et on le dit explicitement :
    # un REVOKE lisible vaut mieux qu'une absence qu'il faut deduire.
    for schema_rgpd in ("gsie_rgpd", "gsie_rgpd_identites"):
        op.execute(f"REVOKE ALL ON SCHEMA {schema_rgpd} FROM {_ROLE_VIZ}")
        op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA {schema_rgpd} FROM {_ROLE_VIZ}")

    op.execute(
        f"COMMENT ON ROLE {_ROLE_VIZ} IS "
        f"'Lecture seule pour les outils de visualisation. SELECT sur le noyau "
        f"et les sept schemas de domaine. Aucun acces a gsie_rgpd ni a "
        f"gsie_rgpd_identites.'"
    )

    # --- Rattachement des comptes de connexion ---
    _grant_si_le_role_existe(_ROLE_APPLICATION, _compte_api())
    _grant_si_le_role_existe(_ROLE_VIZ, _compte_viz())


def downgrade() -> None:
    _revoke_si_le_role_existe(_ROLE_VIZ, _compte_viz())
    _revoke_si_le_role_existe(_ROLE_APPLICATION, _compte_api())
    for schema in _SCHEMAS_LISIBLES:
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} REVOKE SELECT ON TABLES FROM {_ROLE_VIZ}"
        )
    op.execute(f"DROP OWNED BY {_ROLE_VIZ}")
    op.execute(f"DROP ROLE IF EXISTS {_ROLE_VIZ}")

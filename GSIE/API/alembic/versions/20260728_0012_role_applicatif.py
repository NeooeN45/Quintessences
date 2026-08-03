"""Role applicatif : l'isolement RGPD passe de disponible a en vigueur.

`20260728_0011` a place les donnees personnelles dans deux schemas et retire
les droits a `PUBLIC`. Huit tests etablissent que ces droits sont corrects.

Ils n'etablissaient pas que l'application y est soumise — et elle ne l'etait
pas. Verifie par
`test_isolement_rgpd.py::test_le_proprietaire_de_la_base_contourne_l_isolement` :
l'application se connecte avec `gsie`, **proprietaire de la base**, et
PostgreSQL accorde a un proprietaire des droits implicites que `REVOKE` n'ote
pas. Elle lisait donc `gsie_rgpd_identites` sans obstacle.

L'isolement etait **disponible sans etre en vigueur** : exactement la classe de
defaut traquee dans ce depot — une capacite concue et non branchee — et la
migration precedente en aurait cree une de plus.

Cette migration cree le role sous lequel l'application doit se connecter :

* lecture et ecriture sur le noyau, ou vivent les 116 tables du metamodele ;
* **aucun droit** sur `gsie_rgpd` ni `gsie_rgpd_identites`.

Un moteur n'a pas besoin des donnees personnelles pour raisonner. Les rares
traitements qui en ont besoin passeront par un role dedie, obtenu
explicitement — c'est le principe du moindre privilege, et il ne vaut que s'il
est le defaut.

`gsie_application` est un role de groupe sans connexion : le deploiement cree
le compte et lui accorde l'appartenance. Un mot de passe dans une migration
serait un mot de passe dans l'historique git.

Revision ID: 20260728_0012
Revises: 20260728_0011
Create Date: 2026-07-30
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0012"
down_revision: str | None = "20260728_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ROLE_APPLICATION = "gsie_application"
_SCHEMAS_INTERDITS = ("gsie_rgpd", "gsie_rgpd_identites")

# Le noyau du metamodele. `public` en tient lieu tant que `gsie_noyau` n'est pas
# cree : 97 % des cles etrangeres pointent vers `resource`, et le renommer
# imposerait de reecrire la cible de 315 contraintes. Ce renommage n'apporte
# aucune securite — il n'apporte qu'un nom — et sera fait dans un lot dedie.
_SCHEMA_NOYAU = "public"


def upgrade() -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{_ROLE_APPLICATION}') THEN
                CREATE ROLE {_ROLE_APPLICATION} NOLOGIN;
            END IF;
        END
        $$;
        """
    )

    op.execute(f"GRANT USAGE ON SCHEMA {_SCHEMA_NOYAU} TO {_ROLE_APPLICATION}")
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA {_SCHEMA_NOYAU} "
        f"TO {_ROLE_APPLICATION}"
    )
    # Pas de DELETE : `CON-010` interdit la suppression physique. Le retirer ici
    # rend l'interdit structurel plutot que conventionnel — le code ne peut plus
    # supprimer, meme par erreur.
    op.execute(
        f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {_SCHEMA_NOYAU} TO {_ROLE_APPLICATION}"
    )
    # Une table ajoutee plus tard doit heriter des memes droits, sinon
    # l'application perd l'acces au premier ajout sans que rien ne le signale.
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {_SCHEMA_NOYAU} "
        f"GRANT SELECT, INSERT, UPDATE ON TABLES TO {_ROLE_APPLICATION}"
    )

    # Explicite plutot qu'implicite : `20260728_0011` a deja retire les droits a
    # PUBLIC, mais ecrire le refus ici le rend lisible a qui audite ce role.
    for schema in _SCHEMAS_INTERDITS:
        op.execute(f"REVOKE ALL ON SCHEMA {schema} FROM {_ROLE_APPLICATION}")
        op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA {schema} FROM {_ROLE_APPLICATION}")

    op.execute(
        f"COMMENT ON ROLE {_ROLE_APPLICATION} IS "
        "'Role de connexion des moteurs GSIE. Noyau en lecture-ecriture, "
        "aucun acces aux donnees personnelles. Sans DELETE (CON-010).'"
    )


def downgrade() -> None:
    # Le role n'est pas supprime : il peut avoir ete accorde a des comptes de
    # connexion hors de cette migration, et le detruire romprait des acces
    # qu'elle n'a pas crees. Seuls ses droits sont retires.
    op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA {_SCHEMA_NOYAU} FROM {_ROLE_APPLICATION}")
    op.execute(f"REVOKE ALL ON SCHEMA {_SCHEMA_NOYAU} FROM {_ROLE_APPLICATION}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {_SCHEMA_NOYAU} "
        f"REVOKE SELECT, INSERT, UPDATE ON TABLES FROM {_ROLE_APPLICATION}"
    )

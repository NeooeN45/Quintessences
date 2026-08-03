"""Isolement des donnees personnelles en deux schemas distincts (RFC-0029 §4.2, §9.1).

Les 118 tables vivaient toutes dans `public`, atteintes par un role unique
portant 333 privileges. Le Climate Engine pouvait donc lire `consent` et
`data_subject` : rien en base ne l'en empechait, la protection reposant
entierement sur le RBAC applicatif — c'est-a-dire sur du code, dont une fuite
par filtre de type vide a deja ete corrigee le 29 juillet.

**Deux schemas, pas un.** Le contre-audit de `RFC-0029` a corrige la version
initiale sur ce point precis. L'article 32 du RGPD n'exige pas seulement
d'isoler les donnees personnelles : il exige que le **mecanisme de reversion**
— ce qui permet de remonter d'un pseudonyme a une personne — soit conserve
separement des donnees pseudonymisees, sous controle d'acces distinct
(EDPB, lignes directrices 01/2025).

`data_subject` porte `pseudonymized_id`, `agent_id` et `email_encrypted` : ce
n'est pas une donnee pseudonymisee, c'est **la table qui defait le
pseudonymat**. La placer avec `consent` aurait donne l'apparence de la
conformite sans sa propriete principale — un role capable de lire le schema
aurait reconstitue les identites.

| Schema | Contenu | Ce qu'il permet |
|---|---|---|
| `gsie_rgpd` | `consent`, `sensitivity_classification`, `access_policy` | Gerer les consentements sans jamais identifier |
| `gsie_rgpd_identites` | `data_subject` | Resoudre un pseudonyme — le pouvoir le plus sensible |

Les cles etrangeres traversent les schemas : verifie sur cette base avant
d'ecrire cette migration — l'insertion d'un orphelin est refusee, et
`ON DELETE CASCADE` fonctionne au travers. `resource` reste dans `public` ;
`consent.data_subject_id` reference `resource.id`, non `data_subject.id`, donc
le decoupage ne rompt aucun lien.

**Roles de groupe sans connexion.** Les roles crees ici ne peuvent pas se
connecter (`NOLOGIN`) et ne portent aucun mot de passe : un secret dans une
migration serait un secret dans l'historique git. Le deploiement cree les
comptes de connexion et leur accorde l'appartenance a ces groupes. La migration
declare **qui a le droit de quoi**, l'exploitation declare **qui est qui**.

`REVOKE ... FROM PUBLIC` est explicite : sans lui, le role `PUBLIC` conserve
les droits herites et l'isolement ne vaut rien.

Revision ID: 20260728_0011
Revises: 20260728_0010
Create Date: 2026-07-30
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0011"
down_revision: str | None = "20260728_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Donnees pseudonymisees : gerables sans jamais identifier quiconque.
_SCHEMA_RGPD = "gsie_rgpd"
_TABLES_RGPD = ("consent", "sensitivity_classification", "access_policy")

# Mecanisme de reversion : la seule table capable de defaire un pseudonyme.
_SCHEMA_IDENTITES = "gsie_rgpd_identites"
_TABLES_IDENTITES = ("data_subject",)

# Roles de groupe, sans connexion ni mot de passe.
_ROLE_RGPD = "gsie_rgpd_manager"
_ROLE_IDENTITES = "gsie_rgpd_identites_manager"

_ECRITURE = "SELECT, INSERT, UPDATE"


def _creer_role(nom: str) -> None:
    """Cree un role de groupe s'il n'existe pas — les roles sont au cluster.

    Un role survit a la suppression de la base : `CREATE ROLE` echouerait sur
    un cluster ou une autre base GSIE l'a deja cree. Le bloc conditionnel rend
    la migration rejouable, ce que les tests exigent (upgrade/downgrade/upgrade).
    """
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{nom}') THEN
                CREATE ROLE {nom} NOLOGIN;
            END IF;
        END
        $$;
        """
    )


def upgrade() -> None:
    for schema in (_SCHEMA_RGPD, _SCHEMA_IDENTITES):
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    for table in _TABLES_RGPD:
        op.execute(f"ALTER TABLE public.{table} SET SCHEMA {_SCHEMA_RGPD}")
    for table in _TABLES_IDENTITES:
        op.execute(f"ALTER TABLE public.{table} SET SCHEMA {_SCHEMA_IDENTITES}")

    _creer_role(_ROLE_RGPD)
    _creer_role(_ROLE_IDENTITES)

    for schema, role in ((_SCHEMA_RGPD, _ROLE_RGPD), (_SCHEMA_IDENTITES, _ROLE_IDENTITES)):
        # Sans ce REVOKE, PUBLIC conserve ses droits et l'isolement ne vaut rien.
        op.execute(f"REVOKE ALL ON SCHEMA {schema} FROM PUBLIC")
        op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA {schema} FROM PUBLIC")
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO {role}")
        op.execute(f"GRANT {_ECRITURE} ON ALL TABLES IN SCHEMA {schema} TO {role}")
        # Une table ajoutee plus tard doit heriter des memes droits, sinon le
        # role perd l'acces au premier ajout sans que rien ne le signale.
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} " f"GRANT {_ECRITURE} ON TABLES TO {role}"
        )

    # Le gestionnaire d'identites n'herite PAS des droits sur les donnees
    # pseudonymisees, et reciproquement : deux pouvoirs distincts, jamais
    # cumules par construction. Les reunir sur une personne reste possible,
    # mais devient un acte explicite d'exploitation.
    op.execute(
        f"COMMENT ON SCHEMA {_SCHEMA_IDENTITES} IS "
        "'Mecanisme de reversion du pseudonymat (RGPD art. 32). "
        "Acces distinct de gsie_rgpd, jamais accorde a un moteur.'"
    )
    op.execute(
        f"COMMENT ON SCHEMA {_SCHEMA_RGPD} IS "
        "'Donnees personnelles pseudonymisees. Ne permet pas d identifier.'"
    )


def downgrade() -> None:
    for table in _TABLES_RGPD:
        op.execute(f"ALTER TABLE {_SCHEMA_RGPD}.{table} SET SCHEMA public")
    for table in _TABLES_IDENTITES:
        op.execute(f"ALTER TABLE {_SCHEMA_IDENTITES}.{table} SET SCHEMA public")

    for schema in (_SCHEMA_RGPD, _SCHEMA_IDENTITES):
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")

    # Les roles ne sont pas supprimes : ils peuvent avoir ete accordes a des
    # comptes de connexion hors de cette migration, et les detruire romprait
    # des acces qu'elle n'a pas crees.

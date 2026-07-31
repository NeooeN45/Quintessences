"""L'isolement des données personnelles tient par la base, pas par le code.

Avant `20260728_0011`, les 118 tables vivaient dans `public`, atteintes par un
rôle unique portant 333 privilèges. Le Climate Engine pouvait lire `consent` et
`data_subject` : rien en base ne l'en empêchait. La protection reposait
entièrement sur le RBAC applicatif — dont une fuite par filtre de type vide a
déjà été corrigée dans ce dépôt.

Ces tests établissent la protection **au niveau de la base**, en ouvrant de
vraies connexions sous de vrais rôles. Vérifier les `GRANT` dans
`information_schema` ne prouverait rien : c'est le refus effectif de PostgreSQL
qui compte, et lui seul.

Le test central est `test_le_gestionnaire_rgpd_ne_peut_pas_lever_le_pseudonymat`.
Il porte la correction que le contre-audit de `RFC-0029` a imposée : l'article
32 du RGPD exige que le mécanisme de réversion soit séparé des données
pseudonymisées. Un schéma unique aurait donné l'apparence de la conformité sans
sa propriété principale.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.conftest import requires_docker

pytestmark = requires_docker

_SCHEMA_RGPD = "gsie_rgpd"
_SCHEMA_IDENTITES = "gsie_rgpd_identites"

# Role de connexion cree pour ces tests, jouant un moteur de domaine ordinaire.
_MOTEUR = "moteur_domaine_test"
_MOTDEPASSE = "epreuve_isolement"


async def _executer(url: str, *instructions: str) -> None:
    moteur = create_async_engine(url, isolation_level="AUTOCOMMIT")
    try:
        async with moteur.connect() as conn:
            for instruction in instructions:
                await conn.execute(text(instruction))
    finally:
        await moteur.dispose()


async def _lire(url: str, requete: str) -> list[Any]:
    moteur = create_async_engine(url)
    try:
        async with moteur.connect() as conn:
            return list((await conn.execute(text(requete))).scalars().all())
    finally:
        await moteur.dispose()


def _url_pour(url_proprietaire: str, role: str, motdepasse: str) -> str:
    """Réécrit l'URL de connexion pour un autre rôle."""
    _, reste = url_proprietaire.split("://", 1)
    _, hote_et_base = reste.split("@", 1)
    return f"postgresql+asyncpg://{role}:{motdepasse}@{hote_et_base}"


@pytest.fixture(scope="module")
def base_migree() -> Generator[str, None, None]:
    """Base sur laquelle la migration a réellement été jouée.

    `conftest.db_session` construit le schéma par `Base.metadata.create_all` :
    il produit les tables, mais **ni les rôles ni les `GRANT`**, qui sont l'objet
    même de ces tests. Seule la migration les crée, et c'est donc elle qu'il faut
    éprouver — vérifier le registre ne prouverait rien de l'isolement.
    """
    from alembic import command
    from alembic.config import Config
    from testcontainers.postgres import PostgresContainer

    from tests.integration.test_migration_baseline import (
        _IMAGE_DB,
        _REQUIRE_IMAGE,
        _image_disponible,
        _nettoyer_extensions_preinstallees,
    )

    # La migration active l'extension AGE, absente de l'image PostGIS standard.
    # On reprend l'image du test de baseline plutot que d'en decrire une autre :
    # deux descriptions du meme environnement divergeraient.
    if not _image_disponible(_IMAGE_DB):
        message = f"image {_IMAGE_DB} absente ; construire GSIE/API/Dockerfile.db"
        if _REQUIRE_IMAGE:
            pytest.fail(message)
        pytest.skip(message)

    patch = pytest.MonkeyPatch()
    with PostgresContainer(
        image=_IMAGE_DB,
        driver="asyncpg",
        username="gsie",
        password="gsie_test",
        dbname="gsie_isolement",
    ).with_command("postgres -c shared_preload_libraries=age -c search_path=public") as postgres:
        url = postgres.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
        # Nettoyage identique a celui du test de baseline : le decrire
        # autrement ferait diverger deux descriptions du meme environnement.
        asyncio.run(_nettoyer_extensions_preinstallees(url))
        patch.setenv("GSIE_DATABASE_URL", url)
        from gsie_api.core.config import get_settings

        get_settings.cache_clear()
        command.upgrade(Config("alembic.ini"), "head")
        yield url
        get_settings.cache_clear()
    patch.undo()


@pytest.fixture(scope="module")
def url_moteur(base_migree: str) -> Generator[str, None, None]:
    """Crée un rôle de moteur de domaine, avec le noyau et rien d'autre.

    C'est exactement la dotation prévue par `RFC-0029` §4.2 : `USAGE` sur son
    schéma et sur le noyau, aucun droit ailleurs.
    """
    asyncio.run(
        _executer(
            base_migree,
            f"DROP ROLE IF EXISTS {_MOTEUR}",
            f"CREATE ROLE {_MOTEUR} LOGIN PASSWORD '{_MOTDEPASSE}'",
            f"GRANT USAGE ON SCHEMA public TO {_MOTEUR}",
            f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {_MOTEUR}",
        )
    )
    yield _url_pour(base_migree, _MOTEUR, _MOTDEPASSE)
    asyncio.run(
        _executer(
            base_migree,
            f"REASSIGN OWNED BY {_MOTEUR} TO gsie",
            f"DROP OWNED BY {_MOTEUR}",
            f"DROP ROLE IF EXISTS {_MOTEUR}",
        )
    )


# --- Le decoupage lui-meme ---


def test_les_deux_schemas_existent_et_portent_les_bonnes_tables(base_migree: str) -> None:
    """Les données pseudonymisées et le mécanisme de réversion sont séparés.

    `data_subject` porte `pseudonymized_id`, `agent_id` et `email_encrypted` :
    ce n'est pas une donnée pseudonymisée, c'est la table qui **défait** le
    pseudonymat. Elle vit donc seule, dans son propre schéma.
    """
    tables = asyncio.run(
        _lire(
            base_migree,
            "SELECT schemaname || '.' || tablename FROM pg_tables "
            "WHERE schemaname LIKE 'gsie_rgpd%' ORDER BY 1",
        )
    )

    assert set(tables) == {
        f"{_SCHEMA_RGPD}.access_policy",
        f"{_SCHEMA_RGPD}.consent",
        f"{_SCHEMA_RGPD}.sensitivity_classification",
        f"{_SCHEMA_IDENTITES}.data_subject",
    }


def test_aucune_table_personnelle_ne_subsiste_dans_public(base_migree: str) -> None:
    """Le déplacement est complet — une copie oubliée annulerait l'isolement."""
    restantes = asyncio.run(
        _lire(
            base_migree,
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN "
            "('consent', 'data_subject', 'sensitivity_classification', 'access_policy')",
        )
    )

    assert restantes == [], f"tables personnelles encore dans public : {restantes}"


# --- Le refus effectif, sous de vrais roles ---


@pytest.mark.parametrize("schema", [_SCHEMA_RGPD, _SCHEMA_IDENTITES])
def test_un_moteur_de_domaine_est_refuse_sur_les_schemas_personnels(
    url_moteur: str, schema: str
) -> None:
    """PostgreSQL refuse, et c'est le seul refus qui compte.

    Avant cette migration, ce même rôle lisait `consent` et `data_subject` sans
    obstacle. La protection venait du code ; elle vient désormais aussi de la
    base, et il faut que les deux échouent pour qu'une donnée personnelle fuie.
    """
    with pytest.raises(Exception, match="permission denied"):
        asyncio.run(_lire(url_moteur, f"SELECT 1 FROM {schema}.consent"))


def test_un_moteur_de_domaine_lit_toujours_le_noyau(url_moteur: str) -> None:
    """Le cloisonnement n'empêche pas le travail ordinaire.

    Sans ce contrôle, tout refuser ferait passer les tests précédents — et
    rendrait la base inutilisable.
    """
    valeurs = asyncio.run(_lire(url_moteur, "SELECT count(*) FROM public.resource"))

    assert valeurs == [0]


def test_le_gestionnaire_rgpd_ne_peut_pas_lever_le_pseudonymat(base_migree: str) -> None:
    """Le pouvoir de gérer les consentements n'emporte pas celui d'identifier.

    C'est la correction imposée par le contre-audit de `RFC-0029`. L'article 32
    du RGPD exige que le mécanisme de réversion soit conservé séparément des
    données pseudonymisées, sous contrôle d'accès distinct — lignes directrices
    EDPB 01/2025.

    Un schéma unique aurait donné l'apparence de la conformité sans sa propriété
    principale : un rôle capable de lire `gsie_rgpd` aurait reconstitué les
    identités. Ici, `gsie_rgpd_manager` gère les consentements et **ne peut pas**
    remonter à une personne.
    """
    droits = asyncio.run(
        _lire(
            base_migree,
            "SELECT nspname FROM pg_namespace "
            "WHERE nspname LIKE 'gsie_rgpd%' "
            "AND has_schema_privilege('gsie_rgpd_manager', nspname, 'USAGE')",
        )
    )

    assert droits == [_SCHEMA_RGPD], (
        f"`gsie_rgpd_manager` atteint {droits} — il ne doit atteindre que "
        f"{_SCHEMA_RGPD}, jamais le mécanisme de réversion"
    )


def test_le_gestionnaire_d_identites_n_atteint_pas_les_consentements(
    base_migree: str,
) -> None:
    """La séparation vaut dans les deux sens.

    Sans ce contrôle, accorder les deux schémas au second rôle passerait
    inaperçu : le test précédent ne regarde que le premier.
    """
    droits = asyncio.run(
        _lire(
            base_migree,
            "SELECT nspname FROM pg_namespace "
            "WHERE nspname LIKE 'gsie_rgpd%' "
            "AND has_schema_privilege('gsie_rgpd_identites_manager', nspname, 'USAGE')",
        )
    )

    assert droits == [_SCHEMA_IDENTITES]


def test_public_n_a_aucun_droit_sur_les_schemas_personnels(base_migree: str) -> None:
    """Sans le `REVOKE`, le rôle `PUBLIC` garde ses droits et l'isolement est nul."""
    ouverts = asyncio.run(
        _lire(
            base_migree,
            "SELECT nspname FROM pg_namespace "
            "WHERE nspname LIKE 'gsie_rgpd%' "
            "AND has_schema_privilege('public', nspname, 'USAGE')",
        )
    )

    assert ouverts == [], f"PUBLIC atteint encore {ouverts}"


# --- La limite de cet isolement, et pourquoi elle compte ---


def test_le_proprietaire_de_la_base_contourne_l_isolement(base_migree: str) -> None:
    """Un propriétaire PostgreSQL n'est pas soumis aux `GRANT` — vérifié.

    C'est la limite de tout ce qui précède, et elle doit être écrite là où on la
    lira. Les huit tests ci-dessus prouvent que la migration installe des droits
    corrects. Ils ne prouvent **pas** que l'application y est soumise.

    PostgreSQL accorde au propriétaire d'une table des droits implicites que
    `REVOKE` n'ôte pas. L'application se connecte aujourd'hui avec le rôle
    `gsie`, propriétaire de la base : elle lit donc `gsie_rgpd_identites` sans
    obstacle, et l'isolement est **disponible sans être en vigueur**.

    C'est la classe de défaut traquée dans ce dépôt depuis deux jours — une
    capacité conçue et non branchée — et cette migration en aurait créé une de
    plus si personne ne l'avait relevé.

    Ce test échouera le jour où le propriétaire cessera d'avoir accès, et ce
    sera une bonne nouvelle : il faudra alors le réécrire pour constater
    l'inverse.
    """
    lisible = asyncio.run(
        _lire(base_migree, f"SELECT count(*) FROM {_SCHEMA_IDENTITES}.data_subject")
    )

    assert lisible == [0], (
        "le propriétaire ne lit plus le mécanisme de réversion — l'isolement "
        "s'applique désormais à lui, et ce test doit être réécrit"
    )


# --- Le role applicatif : l'isolement mis en vigueur ---


def test_le_role_applicatif_n_atteint_aucune_donnee_personnelle(base_migree: str) -> None:
    """`gsie_application` lit le noyau et rien des données personnelles.

    C'est ce qui fait passer l'isolement de disponible à **en vigueur**. Les
    droits corrects sur les schémas ne servent à rien si l'application se
    connecte en propriétaire — ce qu'elle faisait, et que le test précédent
    établit.
    """
    atteints = asyncio.run(
        _lire(
            base_migree,
            "SELECT nspname FROM pg_namespace "
            "WHERE nspname LIKE 'gsie_rgpd%' "
            "AND has_schema_privilege('gsie_application', nspname, 'USAGE')",
        )
    )

    assert atteints == [], (
        f"le rôle applicatif atteint {atteints} — un moteur n'a pas besoin des "
        "données personnelles pour raisonner"
    )


def test_le_role_applicatif_travaille_sur_le_noyau(base_migree: str) -> None:
    """Le moindre privilège n'empêche pas le travail ordinaire.

    Sans ce contrôle, ne rien accorder ferait passer le test précédent et
    rendrait l'application inopérante.
    """
    droits = asyncio.run(
        _lire(
            base_migree,
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee = 'gsie_application' AND table_name = 'resource' "
            "ORDER BY privilege_type",
        )
    )

    assert set(droits) == {"INSERT", "SELECT", "UPDATE"}


def test_le_role_applicatif_ne_peut_pas_supprimer(base_migree: str) -> None:
    """`CON-010` interdit la suppression physique — l'interdit devient structurel.

    Le retirer des droits rend la règle vérifiée par PostgreSQL plutôt que par
    la seule discipline du code : une suppression écrite par erreur échoue au
    lieu de détruire.
    """
    droits = asyncio.run(
        _lire(
            base_migree,
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee = 'gsie_application' AND privilege_type = 'DELETE'",
        )
    )

    assert droits == [], "le rôle applicatif peut supprimer, contre CON-010"


# --- Les schemas de domaine : pas de DELETE non plus (CON-010) ---


def test_le_role_applicatif_ne_peut_pas_supprimer_dans_gsie_botanique(
    base_migree: str,
) -> None:
    """`CON-010` s'applique à chaque schéma de domaine, pas seulement au noyau.

    Le premier schéma de domaine (GSIE-PROMPT-0027, lot 1) est `gsie_botanique`.
    Sans ce contrôle, accorder `DELETE` sur un schéma de domaine passerait
    inaperçu : le test précédent ne regarde que `public.resource`.
    """
    droits = asyncio.run(
        _lire(
            base_migree,
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee = 'gsie_application' "
            "AND table_schema = 'gsie_botanique' "
            "AND privilege_type = 'DELETE'",
        )
    )

    assert droits == [], (
        "le rôle applicatif peut supprimer dans gsie_botanique, contre CON-010"
    )


def test_le_role_applicatif_ecrit_dans_gsie_botanique(base_migree: str) -> None:
    """Le moindre privilège n'empêche pas le travail ordinaire.

    Sans ce contrôle, ne rien accorder ferait passer le test précédent et
    rendrait le schéma botanique inopérant pour l'application.
    """
    droits = asyncio.run(
        _lire(
            base_migree,
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee = 'gsie_application' "
            "AND table_schema = 'gsie_botanique' "
            "AND table_name = 'autecology_profile' "
            "ORDER BY privilege_type",
        )
    )

    assert set(droits) == {"INSERT", "SELECT", "UPDATE"}


def test_le_role_applicatif_ne_peut_pas_supprimer_dans_gsie_foret(
    base_migree: str,
) -> None:
    """`CON-010` s'applique à gsie_foret — le domaine le plus volumineux.

    Sans ce contrôle, accorder `DELETE` sur le schéma forestier passerait
    inaperçu : le test sur `public.resource` ne regarde pas les schémas de
    domaine.
    """
    droits = asyncio.run(
        _lire(
            base_migree,
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee = 'gsie_application' "
            "AND table_schema = 'gsie_foret' "
            "AND privilege_type = 'DELETE'",
        )
    )

    assert droits == [], (
        "le rôle applicatif peut supprimer dans gsie_foret, contre CON-010"
    )


def test_le_role_applicatif_ecrit_dans_gsie_foret(base_migree: str) -> None:
    """Le moindre privilège n'empêche pas le travail ordinaire en forêt."""
    droits = asyncio.run(
        _lire(
            base_migree,
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee = 'gsie_application' "
            "AND table_schema = 'gsie_foret' "
            "AND table_name = 'management_plan' "
            "ORDER BY privilege_type",
        )
    )

    assert set(droits) == {"INSERT", "SELECT", "UPDATE"}


def test_le_role_applicatif_ne_peut_pas_supprimer_dans_gsie_gouvernance(
    base_migree: str,
) -> None:
    """`CON-010` s'applique à gsie_gouvernance — la chaîne de décision.

    Sans ce contrôle, accorder `DELETE` sur le schéma de gouvernance
    passerait inaperçu : le test sur `public.resource` ne regarde pas les
    schémas de domaine.
    """
    droits = asyncio.run(
        _lire(
            base_migree,
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee = 'gsie_application' "
            "AND table_schema = 'gsie_gouvernance' "
            "AND privilege_type = 'DELETE'",
        )
    )

    assert droits == [], (
        "le rôle applicatif peut supprimer dans gsie_gouvernance, contre CON-010"
    )


def test_le_role_applicatif_ecrit_dans_gsie_gouvernance(base_migree: str) -> None:
    """Le moindre privilège n'empêche pas le travail de gouvernance."""
    droits = asyncio.run(
        _lire(
            base_migree,
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee = 'gsie_application' "
            "AND table_schema = 'gsie_gouvernance' "
            "AND table_name = 'decision' "
            "ORDER BY privilege_type",
        )
    )

    assert set(droits) == {"INSERT", "SELECT", "UPDATE"}

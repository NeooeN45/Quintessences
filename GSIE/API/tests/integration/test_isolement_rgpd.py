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
_SCHEMA_ORGANISATIONS = "gsie_organisations"

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


async def _lire(url: str, requete: str, **params: Any) -> list[Any]:
    moteur = create_async_engine(url)
    try:
        async with moteur.connect() as conn:
            return list((await conn.execute(text(requete), params)).scalars().all())
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
        f"{_SCHEMA_RGPD}.data_subject_consent",
        f"{_SCHEMA_RGPD}.rights_statement",
        f"{_SCHEMA_RGPD}.sensitivity_classification",
        f"{_SCHEMA_RGPD}.spatial_disclosure_policy",
        f"{_SCHEMA_IDENTITES}.account_role",
        f"{_SCHEMA_IDENTITES}.data_subject",
        f"{_SCHEMA_IDENTITES}.identity_provider_link",
        f"{_SCHEMA_IDENTITES}.local_credential",
        f"{_SCHEMA_IDENTITES}.user_account",
        f"{_SCHEMA_IDENTITES}.identity_action_token",
        f"{_SCHEMA_IDENTITES}.email_change_request",
        f"{_SCHEMA_IDENTITES}.account_consent",
        f"{_SCHEMA_IDENTITES}.mfa_secret",
        f"{_SCHEMA_IDENTITES}.mfa_recovery_code",
        f"{_SCHEMA_IDENTITES}.active_session",
        f"{_SCHEMA_IDENTITES}.failed_login_attempt",
        f"{_SCHEMA_IDENTITES}.revoked_refresh_token",
    }


def test_table_invitations_organisation_isolee(base_migree: str) -> None:
    """Les tokens d'invitation restent dans le schéma multi-tenant."""
    tables = asyncio.run(
        _lire(
            base_migree,
            "SELECT schemaname || '.' || tablename FROM pg_tables "
            "WHERE schemaname = 'gsie_organisations' "
            "AND tablename = 'organisation_invitation'",
        )
    )
    assert tables == ["gsie_organisations.organisation_invitation"]


def test_catalogue_billing_initial_est_present(base_migree: str) -> None:
    """Les plans initiaux sont présents sans dépendre d'un fournisseur de paiement."""
    plans = asyncio.run(
        _lire(
            base_migree,
            "SELECT code FROM gsie_billing.plan ORDER BY code",
        )
    )
    assert plans == ["enterprise", "free", "geosylva_pro", "quintessences_pro"]


def test_resource_porte_le_perimetre_et_sa_policy(base_migree: str) -> None:
    """La racine resource est isolable par organisation active."""
    columns = asyncio.run(
        _lire(
            base_migree,
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'resource' "
            "AND column_name IN ('organisation_id', 'workspace_id') ORDER BY 1",
        )
    )
    policies = asyncio.run(
        _lire(
            base_migree,
            "SELECT policyname FROM pg_policies "
            "WHERE schemaname = 'public' AND tablename = 'resource'",
        )
    )
    assert columns == ["organisation_id", "workspace_id"]
    assert policies == ["resource_scope_visible"]


def test_aucune_table_personnelle_ne_subsiste_dans_public(base_migree: str) -> None:
    """Le déplacement est complet — une copie oubliée annulerait l'isolement."""
    restantes = asyncio.run(
        _lire(
            base_migree,
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN "
            "('consent', 'data_subject', 'sensitivity_classification', 'access_policy', "
            "'data_subject_consent', 'rights_statement', 'spatial_disclosure_policy')",
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


def test_le_role_applicatif_n_atteint_pas_les_donnees_personnelles_metier(
    base_migree: str,
) -> None:
    """`gsie_application` atteint l'identité technique, pas les données RGPD métier.

    Le compte canonique et ses moyens de connexion sont indispensables à l'API.
    Ce droit borné ne doit ouvrir ni les consentements, ni la table
    `data_subject` qui permet de lever le pseudonymat.
    """
    atteints = asyncio.run(
        _lire(
            base_migree,
            "SELECT nspname FROM pg_namespace "
            "WHERE nspname LIKE 'gsie_rgpd%' "
            "AND has_schema_privilege('gsie_application', nspname, 'USAGE')",
        )
    )

    assert atteints == [_SCHEMA_IDENTITES], (
        f"le rôle applicatif atteint {atteints} — seul {_SCHEMA_IDENTITES} "
        "est requis pour l'authentification"
    )

    acces_interdits = asyncio.run(
        _lire(
            base_migree,
            "SELECT table_schema || '.' || table_name "
            "FROM information_schema.tables "
            "WHERE table_schema LIKE 'gsie_rgpd%' "
            "AND (table_schema = 'gsie_rgpd' OR table_name = 'data_subject') "
            "AND has_table_privilege("
            "'gsie_application', table_schema || '.' || table_name, "
            "'SELECT,INSERT,UPDATE,DELETE') ORDER BY 1",
        )
    )
    assert acces_interdits == []


def test_le_role_applicatif_accede_uniquement_aux_tables_techniques_d_identite(
    base_migree: str,
) -> None:
    """L'API dispose du DML nécessaire à l'authentification, sans suppression."""
    droits = asyncio.run(
        _lire(
            base_migree,
            "SELECT table_name || ':' || privilege_type "
            "FROM information_schema.role_table_grants "
            "WHERE grantee = 'gsie_application' "
            "AND table_schema = 'gsie_rgpd_identites' ORDER BY 1",
        )
    )

    attendus = {
        f"{table}:{privilege}"
        for table in (
            "account_role",
            "identity_action_token",
            "email_change_request",
            "account_consent",
            "identity_provider_link",
            "local_credential",
            "user_account",
            "mfa_secret",
            "mfa_recovery_code",
            "active_session",
            "failed_login_attempt",
            "revoked_refresh_token",
        )
        for privilege in ("INSERT", "SELECT", "UPDATE")
    }
    assert set(droits) == attendus


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

    assert droits == [], "le rôle applicatif peut supprimer dans gsie_botanique, contre CON-010"


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

    assert droits == [], "le rôle applicatif peut supprimer dans gsie_foret, contre CON-010"


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

    assert droits == [], "le rôle applicatif peut supprimer dans gsie_gouvernance, contre CON-010"


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


# --- Les schemas de domaine vides : reserves et accessibles (RFC-0029) ---


_SCHEMAS_VIDES = ("gsie_climat", "gsie_pedologie", "gsie_hydro", "gsie_feu")


@pytest.mark.parametrize("schema", _SCHEMAS_VIDES)
def test_les_schemas_de_domaine_vides_existent(base_migree: str, schema: str) -> None:
    """Les quatre schémas sans table sont créés — réservés pour les tables futures.

    RFC-0029 §4.1 prévoit sept schémas de domaine. Quatre n'ont pas encore de
    table dédiée dans le métamodèle v6.2 (climat, pédologie, hydro, feu) :
    les données correspondantes vivent dans les tables transverses. Le schéma
    est créé vide, prêt à recevoir les tables futures.
    """
    existe = asyncio.run(
        _lire(
            base_migree,
            "SELECT 1 FROM pg_namespace WHERE nspname = :schema",
            schema=schema,
        )
    )

    assert existe == [1], f"le schéma {schema} n'existe pas"


@pytest.mark.parametrize("schema", _SCHEMAS_VIDES)
def test_le_role_applicatif_a_usage_sur_les_schemas_vides(base_migree: str, schema: str) -> None:
    """`gsie_application` a USAGE sur chaque schéma vide — pas de table, mais le droit.

    Sans USAGE, l'application ne pourrait pas accéder aux tables futures dès
    leur création. Le droit est accordé par défaut (ALTER DEFAULT PRIVILEGES).
    """
    a_usage = asyncio.run(
        _lire(
            base_migree,
            "SELECT has_schema_privilege('gsie_application', :schema, 'USAGE')",
            schema=schema,
        )
    )

    assert a_usage == [True], (
        f"gsie_application n'a pas USAGE sur {schema} — les tables futures "
        "y seraient inaccessibles"
    )


# --- Defense en profondeur : PUBLIC n'a aucun droit (20260728_0020) ---


_TOUS_LES_SCHEMAS_DE_DOMAINE = (
    "gsie_botanique",
    "gsie_foret",
    "gsie_gouvernance",
    "gsie_climat",
    "gsie_pedologie",
    "gsie_hydro",
    "gsie_feu",
)


@pytest.mark.parametrize("schema", _TOUS_LES_SCHEMAS_DE_DOMAINE)
def test_public_n_a_aucun_droit_sur_les_schemas_de_domaine(base_migree: str, schema: str) -> None:
    """Sans le `REVOKE`, le rôle `PUBLIC` garde ses droits et l'isolement est nul.

    `20260728_0020` a ajoute `REVOKE ALL ON SCHEMA ... FROM PUBLIC` sur les sept
    schemas de domaine — defense en profondeur manquante depuis 0013-0019.
    PostgreSQL n'accorde rien a PUBLIC sur les nouveaux schemas par defaut, mais
    le `REVOKE` explicite rend le refus lisible a l'audit et resistant aux
    erreurs d'exploitation.
    """
    ouverts = asyncio.run(
        _lire(
            base_migree,
            "SELECT has_schema_privilege('public', :schema, 'USAGE')",
            schema=schema,
        )
    )

    assert ouverts == [False], f"PUBLIC atteint encore {schema}"


# --- Absence de DELETE sur TOUS les schemas de domaine ---


@pytest.mark.parametrize("schema", _TOUS_LES_SCHEMAS_DE_DOMAINE)
def test_le_role_applicatif_ne_peut_pas_supprimer_dans_aucun_schema_de_domaine(
    base_migree: str, schema: str
) -> None:
    """`CON-010` s'applique a chaque schema de domaine, sans exception.

    Les trois schemas avec tables (botanique, foret, gouvernance) ont deja des
    tests dedies. Ce test parametre couvre les sept schemas, y compris les quatre
    vides — quand des tables y seront ajoutees, rien ne devra inclure DELETE.
    """
    droits = asyncio.run(
        _lire(
            base_migree,
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee = 'gsie_application' "
            "AND table_schema = :schema "
            "AND privilege_type = 'DELETE'",
            schema=schema,
        )
    )

    assert droits == [], f"le rôle applicatif peut supprimer dans {schema}, contre CON-010"


# --- data_subject_consent rejoint gsie_rgpd (20260728_0021) ---


def test_data_subject_consent_n_est_plus_dans_public(base_migree: str) -> None:
    """La table de jonction RGPD a rejoint gsie_rgpd — coherence de l'isolement.

    `data_subject_consent` reliait `data_subject` (gsie_rgpd_identites) et
    `consent` (gsie_rgpd) depuis `public`. Elle etait accessible par
    `gsie_application` qui n'a aucun droit sur les schemas RGPD — une
    incoherence d'isolement. `20260728_0021` l'a deplacee vers `gsie_rgpd`.
    """
    restantes = asyncio.run(
        _lire(
            base_migree,
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'public' AND tablename = 'data_subject_consent'",
        )
    )

    assert (
        restantes == []
    ), "data_subject_consent est encore dans public — gsie_application y a acces"


def test_data_subject_consent_est_dans_gsie_rgpd(base_migree: str) -> None:
    """La table de jonction est bien dans gsie_rgpd apres la migration."""
    presente = asyncio.run(
        _lire(
            base_migree,
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'gsie_rgpd' AND tablename = 'data_subject_consent'",
        )
    )

    assert presente == ["data_subject_consent"]


def test_le_role_applicatif_n_atteint_pas_data_subject_consent(
    base_migree: str,
) -> None:
    """`gsie_application` ne peut pas lire la table de jonction RGPD.

    Avant `20260728_0021`, cette table etait dans `public` et l'application y
    avait acces. Desormais dans `gsie_rgpd`, elle est sous le meme controle
    d'acces que `consent` et `sensitivity_classification`.
    """
    atteint = asyncio.run(
        _lire(
            base_migree,
            "SELECT has_table_privilege('gsie_application', "
            "'gsie_rgpd.data_subject_consent', 'SELECT')",
        )
    )

    assert atteint == [False], (
        "gsie_application peut lire data_subject_consent — " "la table de jonction n'est pas isolee"
    )


# --- rights_statement et spatial_disclosure_policy rejoignent gsie_rgpd (0023) ---


@pytest.mark.parametrize("table", ["rights_statement", "spatial_disclosure_policy"])
def test_les_politiques_d_acces_sont_dans_gsie_rgpd(base_migree: str, table: str) -> None:
    """Les politiques de droits et de divulgation spatiale sont isolees.

    `rights_statement` (licences, restrictions d'usage) et
    `spatial_disclosure_policy` (degradation spatiale) sont des politiques
    de controle d'acces — elles appartiennent au schema RGPD, pas a `public`.
    """
    presente = asyncio.run(
        _lire(
            base_migree,
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'gsie_rgpd' AND tablename = :table",
            table=table,
        )
    )

    assert presente == [table], f"{table} n'est pas dans gsie_rgpd"


@pytest.mark.parametrize("table", ["rights_statement", "spatial_disclosure_policy"])
def test_le_role_applicatif_n_atteint_pas_les_politiques_d_acces(
    base_migree: str, table: str
) -> None:
    """`gsie_application` ne peut pas lire les politiques d'acces.

    Ces tables etaient dans `public` et accessibles par l'application.
    `20260728_0023` les a deplacees vers `gsie_rgpd` avec REVOKE explicite.
    """
    atteint = asyncio.run(
        _lire(
            base_migree,
            "SELECT has_table_privilege('gsie_application', " "'gsie_rgpd.' || :table, 'SELECT')",
            table=table,
        )
    )

    assert atteint == [
        False
    ], f"gsie_application peut lire gsie_rgpd.{table} — la politique n'est pas isolee"

"""Tests unitaires — contrôle des privilèges du rôle de connexion au démarrage.

Cette garde est le seul point où l'application vérifie qu'elle ne tourne
pas en superutilisateur. Si elle y tourne, les `GRANT`/`REVOKE` des
migrations 0011→0023 sont ignorés et RLS est contournée — l'isolement de
`gsie_rgpd_identites`, la table qui défait le pseudonymat, n'existe plus
que sur le papier.

Or `mock_lifespan` (conftest.py) neutralise cette garde dans tout test
qui construit un `TestClient`. C'est nécessaire — un test unitaire n'a
pas de PostgreSQL — mais ça la retirait de toute couverture : elle
n'était vérifiée nulle part. Une garde jamais exécutée par les tests ne
se distingue pas d'une garde absente.

Ces tests l'exercent directement, sans base, en simulant la ligne que
PostgreSQL renvoie.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gsie_api.infrastructure.db_privileges import (
    PrivilegesDeConnexionInvalidesError,
    verifier_privileges_de_connexion,
)


def _fabrique_de_sessions(ligne: object) -> MagicMock:
    """Fabrique de sessions dont l'unique requête renvoie `ligne`."""
    resultat = MagicMock()
    resultat.first.return_value = ligne

    session = MagicMock()
    session.execute = AsyncMock(return_value=resultat)

    contexte = MagicMock()
    contexte.__aenter__ = AsyncMock(return_value=session)
    contexte.__aexit__ = AsyncMock(return_value=False)

    fabrique = MagicMock(return_value=contexte)
    return fabrique


def _ligne(
    *,
    role: str = "gsie_api",
    superutilisateur: bool = False,
    bypass_rls: bool = False,
    membre: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        role_courant=role,
        est_superutilisateur=superutilisateur,
        contourne_rls=bypass_rls,
        membre_du_groupe=membre,
    )


def _environnement(nom: str) -> object:
    """Remplace les settings lus par le module par un environnement donné."""
    return patch(
        "gsie_api.infrastructure.db_privileges.get_settings",
        return_value=SimpleNamespace(environment=nom),
    )


async def should_accept_a_proper_application_role():
    """Un role applicatif conforme laisse le demarrage se poursuivre."""
    with _environnement("production"):
        await verifier_privileges_de_connexion(_fabrique_de_sessions(_ligne()))


@pytest.mark.parametrize(
    ("ecart", "attendu_dans_le_message"),
    [
        ({"superutilisateur": True}, "SUPERUSER"),
        ({"bypass_rls": True}, "BYPASSRLS"),
        ({"membre": False}, "gsie_application"),
    ],
)
async def should_refuse_to_start_in_production_when_the_role_is_too_powerful(
    ecart: dict[str, bool], attendu_dans_le_message: str
):
    """En production, un role trop puissant arrete le demarrage."""
    with _environnement("production"), pytest.raises(PrivilegesDeConnexionInvalidesError) as erreur:
        await verifier_privileges_de_connexion(_fabrique_de_sessions(_ligne(**ecart)))

    assert attendu_dans_le_message in str(erreur.value)


async def should_refuse_to_start_in_staging_too():
    """La pre-production sert de vraies donnees : meme exigence qu'en production."""
    with _environnement("staging"), pytest.raises(PrivilegesDeConnexionInvalidesError):
        await verifier_privileges_de_connexion(_fabrique_de_sessions(_ligne(superutilisateur=True)))


async def should_only_warn_in_development():
    """Un poste local doit pouvoir demarrer — mais le message doit exister."""
    with (
        _environnement("development"),
        patch("gsie_api.infrastructure.db_privileges.logger") as journal,
    ):
        await verifier_privileges_de_connexion(
            _fabrique_de_sessions(_ligne(role="gsie", superutilisateur=True))
        )

    journal.warning.assert_called_once()
    assert journal.warning.call_args.args[0] == "privileges_db_trop_larges"


async def should_not_treat_an_unreadable_role_as_authorised():
    """Une lecture impossible n'est pas une autorisation implicite."""
    with _environnement("production"), pytest.raises(PrivilegesDeConnexionInvalidesError):
        await verifier_privileges_de_connexion(_fabrique_de_sessions(None))

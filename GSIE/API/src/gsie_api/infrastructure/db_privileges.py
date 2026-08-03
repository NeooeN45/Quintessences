"""Contrôle effectif des privilèges du rôle de connexion, au démarrage.

Le garde-fou historique (`core/config.py`) refusait un rôle *nommé* `gsie`
ou `postgres`. Un nom n'est pas un privilège : renommer le superutilisateur
en `gsie_app` suffisait à le satisfaire, et l'application continuait de
tourner en superutilisateur — état dans lequel les ACL sont ignorées et RLS
contournée, `FORCE ROW LEVEL SECURITY` compris. Tout l'isolement construit
par les migrations 0004 et 0011→0023 était alors décoratif.

Ce module pose la question à PostgreSQL plutôt qu'à la chaîne de connexion :

1. Le rôle courant est-il `SUPERUSER` ou `BYPASSRLS` ?
2. Est-il membre de `gsie_application` ?

En production et en pré-production, un « oui » à la première question ou un
« non » à la seconde arrête le démarrage. En développement, l'écart est
seulement journalisé : on ne veut pas empêcher un poste local de démarrer,
mais on veut que le message existe.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text

from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = get_logger("gsie_api.infrastructure.db_privileges")

ROLE_APPLICATION = "gsie_application"

_REQUETE = text(
    """
    SELECT
        current_user                                   AS role_courant,
        r.rolsuper                                     AS est_superutilisateur,
        r.rolbypassrls                                 AS contourne_rls,
        pg_has_role(current_user, :groupe, 'USAGE')    AS membre_du_groupe
    FROM pg_roles AS r
    WHERE r.rolname = current_user
    """
)


class PrivilegesDeConnexionInvalidesError(RuntimeError):
    """Le rôle de connexion est trop puissant pour servir l'application."""


def _diagnostiquer(role: str, superutilisateur: bool, bypass_rls: bool, membre: bool) -> list[str]:
    """Liste les écarts constatés, du plus grave au moins grave."""
    ecarts: list[str] = []
    if superutilisateur:
        ecarts.append(
            f"le role « {role} » est SUPERUSER : il ignore les GRANT/REVOKE et "
            "contourne toute politique RLS, y compris FORCE ROW LEVEL SECURITY. "
            "L'isolement de gsie_rgpd_identites ne s'applique pas a lui"
        )
    if bypass_rls:
        ecarts.append(
            f"le role « {role} » porte BYPASSRLS : les politiques de la migration "
            "20260727_0004 ne le filtrent pas"
        )
    if not membre:
        ecarts.append(
            f"le role « {role} » n'est pas membre de {ROLE_APPLICATION} : soit il "
            "tient ses droits en propre (proprietaire des tables, donc hors "
            "REVOKE), soit il n'en a aucun. Rattacher le compte avec "
            f"GRANT {ROLE_APPLICATION} TO « {role} »"
        )
    return ecarts


async def verifier_privileges_de_connexion(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Vérifie que le rôle de connexion est bien un rôle applicatif.

    Args:
        session_factory: fabrique de sessions SQLAlchemy async (``AsyncSessionLocal``).

    Raises:
        PrivilegesDeConnexionInvalidesError: en production/pré-production, si le
            rôle est superutilisateur, contourne RLS, ou n'est pas membre de
            ``gsie_application``.
    """
    settings = get_settings()
    strict = settings.environment in ("production", "staging")

    async with session_factory() as session:
        ligne = (await session.execute(_REQUETE, {"groupe": ROLE_APPLICATION})).first()

    if ligne is None:
        # `current_user` introuvable dans pg_roles : cas theorique, mais on ne
        # transforme pas une anomalie de lecture en autorisation implicite.
        message = "Impossible de lire les privileges du role de connexion"
        if strict:
            raise PrivilegesDeConnexionInvalidesError(message)
        logger.warning("privileges_db_illisibles", environnement=settings.environment)
        return

    ecarts = _diagnostiquer(
        ligne.role_courant,
        bool(ligne.est_superutilisateur),
        bool(ligne.contourne_rls),
        bool(ligne.membre_du_groupe),
    )

    if not ecarts:
        logger.info("privileges_db_conformes", role=ligne.role_courant)
        return

    if strict:
        raise PrivilegesDeConnexionInvalidesError(
            f"Role de connexion inadapte en {settings.environment} — " + " ; ".join(ecarts)
        )
    logger.warning(
        "privileges_db_trop_larges",
        environnement=settings.environment,
        role=ligne.role_courant,
        ecarts=ecarts,
    )

"""Garanties d'idempotence de la chaîne d'orchestration.

``requete_id`` est l'identifiant stable d'une demande GeoSylva. Une seconde
tentative avec le même identifiant doit rendre exactement la même preuve, sans
réexécuter les moteurs. Le verrou transactionnel PostgreSQL couvre également
la course entre deux replicas derrière HAProxy.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from sqlalchemy import select, text

from gsie_api.engines.orchestration.schemas import AnalyseComplete, AnalyseRequest
from gsie_api.infrastructure.models.enrichment import AnalysisRunModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

__all__ = [
    "AnalyseIdempotencyConflictError",
    "contenu_persistable",
    "empreinte_requete",
    "charger_analyse_idempotente",
]


class AnalyseIdempotencyConflictError(Exception):
    """Le même identifiant a été réutilisé avec un autre contenu."""


def _retirer_champs_calcules(contenu: dict[str, Any]) -> dict[str, Any]:
    """Retire les propriétés de sortie calculées avant validation stricte.

    ``Recommendation.contournable`` est un champ calculé Pydantic : il est
    présent dans la réponse HTTP mais ne constitue pas une entrée du modèle.
    Le retirer avant rejeu permet de relire les preuves produites par les
    versions précédentes tout en conservant ``extra=forbid`` pour toute autre
    divergence de schéma.
    """
    copie = deepcopy(contenu)
    bloc = copie.get("recommandations")
    if not isinstance(bloc, dict):
        return copie
    elements = bloc.get("recommandations")
    if not isinstance(elements, list):
        return copie
    for element in elements:
        if not isinstance(element, dict):
            continue
        element.pop("contournable", None)
        alternatives = element.get("alternatives")
        if isinstance(alternatives, list):
            for alternative in alternatives:
                if isinstance(alternative, dict):
                    alternative.pop("contournable", None)
    return copie


def contenu_persistable(resultat: AnalyseComplete) -> dict[str, Any]:
    """Sérialise une preuve sans les propriétés calculées non entrantes."""
    return _retirer_champs_calcules(resultat.model_dump(mode="json"))


def empreinte_requete(requete: AnalyseRequest) -> str:
    """Calcule une empreinte stable de tout le contrat d'entrée."""
    contenu = json.dumps(
        requete.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(contenu.encode("utf-8")).hexdigest()


async def _verrouiller(session: AsyncSession, cle: str) -> None:
    """Sérialise les tentatives concurrentes pour une même demande.

    Le banc de tests peut utiliser une session sans engine lié ; dans ce cas le
    contrôle de rejeu reste disponible, mais le verrou distribué n'est pas
    simulé. En production GSIE, le chemin est PostgreSQL obligatoire.
    """
    bind = getattr(session, "bind", None)
    dialect = getattr(bind, "dialect", None)
    if getattr(dialect, "name", None) != "postgresql":
        return
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:cle, 0))"),
        {"cle": cle},
    )


async def charger_analyse_idempotente(
    session: AsyncSession, requete: AnalyseRequest
) -> tuple[AnalyseComplete | None, str]:
    """Verrouille la clé puis retourne une preuve déjà produite, si présente.

    Une ligne historique sans empreinte ne peut pas être comparée de manière
    sûre : elle est refusée plutôt que réutilisée silencieusement.
    """
    empreinte = empreinte_requete(requete)
    await _verrouiller(session, str(requete.requete_id))

    resultat = await session.execute(
        select(AnalysisRunModel)
        .where(AnalysisRunModel.requete_origine == requete.requete_id)
        .order_by(AnalysisRunModel.execute_at.desc())
        .limit(1)
    )
    existante = resultat.scalars().first()
    if existante is None:
        return None, empreinte

    empreinte_existante: Any = getattr(existante, "requete_fingerprint", None)
    if not isinstance(empreinte_existante, str):
        raise AnalyseIdempotencyConflictError(
            "requete_id déjà utilisé par une preuve historique sans empreinte ; "
            "une nouvelle requête doit utiliser un autre identifiant"
        )
    if empreinte_existante != empreinte:
        raise AnalyseIdempotencyConflictError(
            "requete_id réutilisé avec un contenu différent ; fournissez un "
            "nouvel identifiant de requête"
        )
    return AnalyseComplete.model_validate(_retirer_champs_calcules(existante.contenu)), empreinte

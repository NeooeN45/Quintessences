"""Validation des URLs d'images en base — distingue le lien mort du réseau qui tousse.

Vérifie que les URLs stockées dans `entity_image` sont accessibles et
enregistre le résultat dans les deux colonnes déjà prévues pour ça :

| `validated_at` | `last_checked_at` | Signification            |
|---|---|---|
| non nul        | non nul           | Lien vérifié accessible  |
| nul            | non nul           | Lien vérifié inaccessible|
| nul            | nul               | Jamais vérifié           |

**Aucune suppression.** `CON-010` interdit la suppression physique, et le
rôle applicatif a été délibérément privé de `DELETE` (migration
`20260728_0012`) : un lien mort se marque, il ne s'efface pas. La métrique
`gsie_images_unvalidated_total` les compte, et une image non validée peut
être remplacée sans perdre la trace de ce qui l'a précédée.

Trois issues, pas deux. Un lien est déclaré mort sur un refus **définitif**
du serveur (404, 410, 451). Un délai dépassé, une coupure DNS ou un 5xx ne
prouvent rien sur le lien : l'image reste dans l'état où elle était, et
seul `last_checked_at` avance. C'est ce qui empêche une micro-coupure
réseau de faire basculer tout le catalogue en « non validé ».

Usage :
    python validate_image_urls.py                # verifie, n'ecrit rien
    python validate_image_urls.py --appliquer    # ecrit le resultat en base
    python validate_image_urls.py --limit 100    # limite a 100 images
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from enum import Enum

import httpx
from sqlalchemy import select

from gsie_api.core.logging import get_logger
from gsie_api.infrastructure.database import async_session_factory
from gsie_api.infrastructure.models.enrichment import EntityImageModel

logger = get_logger("gsie_api.validate_image_urls")

_DEFAULT_TIMEOUT = 10.0
_DEFAULT_CONCURRENCY = 10
_USER_AGENT = "GSIE/1.0 (https://github.com/NeooeN45/Quintessences; contact@gsie.fr)"

# Seuls ces codes prouvent que la ressource n'est plus là. Un 403 en est
# absent : beaucoup de CDN le renvoient à un client qu'ils n'aiment pas,
# alors que l'image reste servie à un navigateur.
_CODES_DEFINITIFS = frozenset({404, 410, 451})

# Nombre total de tentatives sur une erreur non concluante (réseau, 5xx),
# et pause entre deux. Un lien n'est jamais déclassé sur un seul échec.
_TENTATIVES = 3
_PAUSE_ENTRE_TENTATIVES = 2.0

# Schémas acceptés : la colonne `url` est alimentée depuis des sources
# externes (Wikimedia). Sans ce filtre, une valeur `file://` ou un hôte
# interne ferait de ce script un moyen de sonder le réseau local.
_SCHEMAS_AUTORISES = frozenset({"http", "https"})


class Verdict(Enum):
    """Issue d'une vérification d'URL."""

    ACCESSIBLE = "accessible"
    DISPARU = "disparu"
    # Le serveur n'a pas répondu, ou a répondu qu'il allait mal. On ne sait
    # rien du lien : ne rien écrire vaut mieux qu'écrire une supposition.
    INDETERMINE = "indetermine"


async def _sonder_une_fois(client: httpx.AsyncClient, url: str) -> Verdict:
    """Sonde l'URL une fois. `HEAD`, puis `GET` si le serveur refuse `HEAD`."""
    entetes = {"User-Agent": _USER_AGENT}
    try:
        reponse = await client.head(url, follow_redirects=True, headers=entetes)
        # 405/501 : le serveur ne veut pas de HEAD, pas « l'image n'existe
        # pas ». On redemande en GET sans lire le corps.
        if reponse.status_code in (405, 501):
            async with client.stream("GET", url, follow_redirects=True, headers=entetes) as flux:
                reponse = flux
                if reponse.status_code in _CODES_DEFINITIFS:
                    return Verdict.DISPARU
                return Verdict.ACCESSIBLE if reponse.status_code < 400 else Verdict.INDETERMINE
    except httpx.RequestError:
        # Timeout, DNS, connexion refusée : la panne peut être de notre côté.
        return Verdict.INDETERMINE

    if reponse.status_code in _CODES_DEFINITIFS:
        return Verdict.DISPARU
    if reponse.status_code < 400:
        return Verdict.ACCESSIBLE
    return Verdict.INDETERMINE


async def verifier_url(client: httpx.AsyncClient, url: str) -> Verdict:
    """Vérifie une URL, en réessayant tant que l'issue n'est pas concluante.

    Un verdict définitif — accessible ou disparu — sort au premier coup.
    Seul l'indéterminé est réessayé : c'est exactement le cas où une
    seconde tentative apporte une information.
    """
    try:
        schema = httpx.URL(url).scheme
    except httpx.InvalidURL:
        # Une URL illisible n'est pas une preuve que l'image a disparu : c'est
        # une donnée fautive, à corriger en amont, pas à déclasser ici.
        logger.warning("url_illisible", url=url[:80])
        return Verdict.INDETERMINE
    if schema not in _SCHEMAS_AUTORISES:
        logger.warning("schema_url_refuse", url=url[:80])
        return Verdict.INDETERMINE

    verdict = Verdict.INDETERMINE
    for restantes in range(_TENTATIVES - 1, -1, -1):
        verdict = await _sonder_une_fois(client, url)
        if verdict is not Verdict.INDETERMINE:
            return verdict
        if restantes:
            await asyncio.sleep(_PAUSE_ENTRE_TENTATIVES)
    return verdict


async def valider_les_images(
    limit: int = 0,
    appliquer: bool = False,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> dict[str, int]:
    """Vérifie les URLs d'images et, si demandé, écrit le résultat en base.

    Returns:
        Le compte par verdict — utile aux tests et à l'appelant.
    """
    print("=" * 60)
    print(
        f"Validation des URLs d'images "
        f"(limit={'toutes' if limit == 0 else limit}, appliquer={appliquer})"
    )
    print("=" * 60)

    comptes = {v.value: 0 for v in Verdict}

    async with async_session_factory() as session:
        requete = select(EntityImageModel).order_by(EntityImageModel.created_at)
        if limit > 0:
            requete = requete.limit(limit)
        images = list((await session.execute(requete)).scalars().all())

        print(f"\n{len(images)} images à vérifier")

        verrou = asyncio.Semaphore(concurrency)
        maintenant = datetime.now(UTC)

        async def verifier_une(image: EntityImageModel) -> None:
            async with verrou:
                verdict = await verifier_url(client, image.url)
            comptes[verdict.value] += 1

            if verdict is Verdict.INDETERMINE:
                # On ne sait rien : ni `validated_at` ni `last_checked_at` ne
                # bougent. Marquer la date d'un contrôle qui n'a rien conclu
                # ferait passer l'ignorance pour une vérification.
                logger.info("url_indeterminee", entity_id=str(image.entity_id), url=image.url[:80])
                return

            if not appliquer:
                return

            image.last_checked_at = maintenant
            if verdict is Verdict.ACCESSIBLE:
                image.validated_at = maintenant
            else:
                # Le lien est marqué non validé, jamais supprimé (CON-010).
                image.validated_at = None
                logger.warning("url_disparue", entity_id=str(image.entity_id), url=image.url[:80])

        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            # `return_exceptions` : l'echec d'une sonde ne doit pas annuler
            # les autres, ni perdre les verdicts deja rendus.
            resultats = await asyncio.gather(
                *[verifier_une(image) for image in images], return_exceptions=True
            )
        for resultat in resultats:
            if isinstance(resultat, BaseException):
                logger.error("verification_en_erreur", error=str(resultat))

        if appliquer:
            await session.commit()

    print("\nRésultats :")
    print(f"  Accessibles  : {comptes[Verdict.ACCESSIBLE.value]}")
    print(f"  Disparues    : {comptes[Verdict.DISPARU.value]}")
    print(f"  Indéterminées: {comptes[Verdict.INDETERMINE.value]}")
    if not appliquer:
        print("\n  (lecture seule — relancer avec --appliquer pour écrire en base)")

    print("\n" + "=" * 60)
    print("Validation terminée.")
    print("=" * 60)
    return comptes


def main() -> None:
    """Parse les arguments et lance la validation."""
    parser = argparse.ArgumentParser(description="Validation des URLs d'images en base")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Nombre d'images à vérifier (0 = toutes)",
    )
    parser.add_argument(
        "--appliquer",
        action="store_true",
        help=(
            "Écrit le résultat en base (validated_at / last_checked_at). "
            "Sans cette option, le script ne modifie rien."
        ),
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=_DEFAULT_CONCURRENCY,
        help=f"Nombre de vérifications simultanées (défaut: {_DEFAULT_CONCURRENCY})",
    )
    args = parser.parse_args()

    try:
        asyncio.run(
            valider_les_images(
                limit=args.limit,
                appliquer=args.appliquer,
                concurrency=args.concurrency,
            )
        )
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur.")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"\nErreur : {exc}", file=sys.stderr)
        logger.exception("validate_image_urls_echec")
        sys.exit(1)


if __name__ == "__main__":
    main()

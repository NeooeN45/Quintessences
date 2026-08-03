"""Ingestion Treekipedia → GSIE.

Pipeline d'ingestion du catalogue Treekipedia (DEC-000041) :
1. Lit N espèces depuis le CSV local Treekipedia (snapshot officiel)
2. Résout chaque nom scientifique via GBIF (GBIFClient.match_species)
   — parallélisé avec Semaphore pour respecter le rate limit GBIF
3. Crée le taxon GSIE via BotanicalEngine._get_or_create_taxon
4. Ajoute un alias Treekipedia (namespace="treekipedia") pour la
   traçabilité croisée GSIE ↔ Treekipedia
5. Checkpoint de progression pour reprise automatique après crash

Usage :
    python ingest_treekipedia.py              # 100 espèces pilotes
    python ingest_treekipedia.py --limit 50   # 50 espèces
    python ingest_treekipedia.py --dry-run    # affiche sans écrire
    python ingest_treekipedia.py --offset 1000  # commencer à l'offset 1000
    python ingest_treekipedia.py --resume     # reprend depuis le dernier checkpoint
    python ingest_treekipedia.py --concurrency 10  # 10 requêtes GBIF simultanées

Prérequis : base PostgreSQL démarrée (docker compose up -d db).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import select

from gsie_api.core.logging import get_logger
from gsie_api.engines.botanical.engine import BotanicalEngine
from gsie_api.engines.botanical.gbif_client import GBIFClient, GBIFClientError
from gsie_api.engines.botanical.treekipedia_client import (
    TreekipediaClient,
    TreekipediaClientError,
    build_treekipedia_source,
    extract_genus,
    parse_common_names,
)
from gsie_api.infrastructure.database import async_session_factory
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.enrichment import IngestionProgressModel
from gsie_api.infrastructure.models.provenance import EntityAliasModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger("gsie_api.ingest_treekipedia")

_DEFAULT_PILOT_LIMIT = 100
_DEFAULT_CONCURRENCY = 5  # limite pour respecter le rate limit GBIF (30 req/min)
_BATCH_SIZE = 100  # commit par lot de 100 (au lieu de 10 — audit P1-3)
_PIPELINE_NAME = "treekipedia_ingest"


async def _resolve_gbif(
    gbif_client: GBIFClient,
    row: dict[str, str | None],
    sem: asyncio.Semaphore,
) -> dict[str, str | bool]:
    """Résout une espèce via GBIF (phase parallèle, sans écriture DB).

    Returns:
        Dict avec le statut de la résolution (success, gbif_key, raison_echec).
    """
    taxon_id_treekipedia = row.get("taxon_id") or ""
    scientific_name = row.get("species_scientific_name") or ""

    result: dict[str, str | bool] = {
        "taxon_id_treekipedia": taxon_id_treekipedia,
        "scientific_name": scientific_name,
        "success": False,
    }

    if not scientific_name:
        result["raison_echec"] = "nom_scientifique_vide"
        return result

    async with sem:
        try:
            gbif_match = await gbif_client.match_species(scientific_name)
        except GBIFClientError as exc:
            result["raison_echec"] = f"gbif_erreur:{exc!s:.100}"
            return result

    if gbif_match is None:
        result["raison_echec"] = "gbif_aucun_match"
        return result

    gbif_key = gbif_match.get("usageKey")
    if not isinstance(gbif_key, int):
        result["raison_echec"] = "gbif_cle_manquante"
        return result

    result["gbif_key"] = str(gbif_key)
    result["success"] = True
    return result


async def _ingest_one(
    session: AsyncSession,
    botanical_engine: BotanicalEngine,
    row: dict[str, str | None],
    gbif_result: dict[str, str | bool],
) -> dict[str, str | bool]:
    """Ingère une espèce résolue dans GSIE (phase séquentielle, avec écriture DB).

    Returns:
        Dict avec le statut de l'ingestion (success, taxon_id, gbif_key, raison_echec).
    """
    taxon_id_treekipedia = row.get("taxon_id") or ""
    scientific_name = row.get("species_scientific_name") or ""
    common_names_raw = row.get("common_name")

    result: dict[str, str | bool] = {
        "taxon_id_treekipedia": taxon_id_treekipedia,
        "scientific_name": scientific_name,
        "success": False,
    }

    if not gbif_result.get("success"):
        result["raison_echec"] = gbif_result.get("raison_echec", "gbif_echec")
        return result

    gbif_key_str = gbif_result.get("gbif_key", "")
    if not isinstance(gbif_key_str, str) or not gbif_key_str:
        result["raison_echec"] = "gbif_cle_manquante"
        return result

    gbif_key = int(gbif_key_str)
    result["gbif_key"] = gbif_key_str

    # Création du taxon GSIE (déduplication automatique)
    try:
        entity_id = await botanical_engine._get_or_create_taxon(gbif_key)
    except Exception as exc:  # noqa: BLE001 — ingestion non bloquante
        result["raison_echec"] = f"taxon_creation:{exc!s:.100}"
        return result

    # Ajout de l'alias Treekipedia (idempotent — vérifie d'abord)
    existing_alias = await session.execute(
        select(EntityAliasModel.id).where(
            EntityAliasModel.namespace == "treekipedia",
            EntityAliasModel.external_id == taxon_id_treekipedia,
        )
    )
    if existing_alias.scalars().first() is None:
        alias_id = uuid4()
        session.add(
            ResourceModel(
                id=alias_id,
                type="entity_alias",
                gsie_id=f"gsie:alias:treekipedia:{taxon_id_treekipedia}",
                metadata_json={
                    "source": build_treekipedia_source(),
                    "common_names": parse_common_names(common_names_raw),
                    "genus": extract_genus(scientific_name),
                    "taxon_full": row.get("taxon_full"),
                },
            )
        )
        await session.flush()
        session.add(
            EntityAliasModel(
                id=alias_id,
                entity_id=entity_id,
                namespace="treekipedia",
                external_id=taxon_id_treekipedia,
            )
        )

    result["success"] = True
    result["entity_id"] = str(entity_id)
    return result


async def _get_or_create_progress(
    session: AsyncSession,
    total: int,
) -> IngestionProgressModel:
    """Récupère ou crée l'enregistrement de progression du pipeline."""
    result = await session.execute(
        select(IngestionProgressModel).where(IngestionProgressModel.pipeline == _PIPELINE_NAME)
    )
    progress = result.scalars().first()
    if progress is None:
        progress = IngestionProgressModel(
            pipeline=_PIPELINE_NAME,
            last_offset=0,
            total=total,
            status="pending",
        )
        session.add(progress)
        await session.flush()
    return progress


async def ingest_treekipedia(
    limit: int = _DEFAULT_PILOT_LIMIT,
    offset: int = 0,
    dry_run: bool = False,
    concurrency: int = _DEFAULT_CONCURRENCY,
    resume: bool = False,
) -> None:
    """Point d'entrée — ingère `limit` espèces Treekipedia dans GSIE.

    Étapes :
    1. Lecture du CSV Treekipedia (limit + offset, ou reprise depuis checkpoint)
    2. Résolution GBIF parallèle (Semaphore pour respecter le rate limit)
    3. Insertion séquentielle par batch de 100 avec checkpoint
    4. Statistiques finales (succès, échecs, raisons)
    """
    print("=" * 60)
    print(f"Ingestion Treekipedia → GSIE ({limit} espèces, concurrency={concurrency})")
    print("=" * 60)

    if dry_run:
        print("\n[DRY-RUN] Aucune écriture en base — affichage uniquement.\n")

    # Reprise depuis checkpoint
    start_offset = offset
    if resume and not dry_run:
        async with async_session_factory() as session:
            progress = await _get_or_create_progress(session, total=limit)
            start_offset = progress.last_offset
            if start_offset > 0:
                print(f"\n[Reprise] Reprise depuis l'offset {start_offset}")
            progress.status = "running"
            progress.started_at = datetime.now(UTC)
            await session.commit()

    # 1. Lecture du CSV
    treekipedia_client = TreekipediaClient()
    try:
        species = treekipedia_client.list_species(limit=limit, offset=start_offset)
    except TreekipediaClientError as exc:
        print(f"\nErreur : impossible de lire le CSV Treekipedia : {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\n[1/3] {len(species)} espèces lues depuis le CSV Treekipedia (offset={start_offset})")
    if dry_run:
        for row in species[:10]:
            print(
                f"  {row.get('taxon_id', '?'):30s}  " f"{row.get('species_scientific_name', '?')}"
            )
        if len(species) > 10:
            print(f"  ... et {len(species) - 10} autres")
        print(f"\n[DRY-RUN] {len(species)} espèces seraient résolues via GBIF et ingérées")
        print("=" * 60)
        print("Dry-run terminé.")
        print("=" * 60)
        return

    # 2. Résolution GBIF parallèle
    print(f"\n[2/3] Résolution GBIF parallèle (concurrency={concurrency})...")
    gbif_client = GBIFClient()
    sem = asyncio.Semaphore(concurrency)

    # `return_exceptions` : `_resolve_gbif` n'attrape que `GBIFClientError`.
    # Sans ce garde-fou, une seule espèce levant autre chose (réponse
    # inattendue, coupure) annulait la résolution des 99 autres du lot —
    # à 67 927 espèces, un incident isolé faisait perdre tout le travail
    # déjà parallélisé.
    resultats_bruts = await asyncio.gather(
        *[_resolve_gbif(gbif_client, row, sem) for row in species],
        return_exceptions=True,
    )

    gbif_results: list[dict[str, str | bool]] = []
    for ligne, resultat in zip(species, resultats_bruts, strict=True):
        if isinstance(resultat, BaseException):
            nom = ligne.get("species_scientific_name") or ""
            logger.warning("resolution_gbif_en_erreur", espece=nom, erreur=str(resultat))
            gbif_results.append(
                {
                    "taxon_id_treekipedia": ligne.get("taxon_id") or "",
                    "scientific_name": nom,
                    "success": False,
                    "raison_echec": f"erreur inattendue : {type(resultat).__name__}",
                }
            )
        else:
            gbif_results.append(resultat)

    gbif_successes = sum(1 for r in gbif_results if r.get("success"))
    gbif_failures = len(gbif_results) - gbif_successes
    print(f"  Résolution : {gbif_successes} succès, {gbif_failures} échecs")

    # 3. Insertion séquentielle par batch
    print(f"\n[3/3] Ingestion en base (batch de {_BATCH_SIZE})...")
    successes = 0
    failures: list[dict[str, str | bool]] = []
    failure_reasons: dict[str, int] = {}

    async with async_session_factory() as session:
        botanical_engine = BotanicalEngine(session=session)
        progress = await _get_or_create_progress(session, total=len(species))
        progress.status = "running"
        progress.started_at = datetime.now(UTC)

        for i, (row, gbif_result) in enumerate(zip(species, gbif_results, strict=True), 1):
            result = await _ingest_one(session, botanical_engine, row, gbif_result)
            if result["success"]:
                successes += 1
                logger.info(
                    "espece_ingeree",
                    taxon_id=result["taxon_id_treekipedia"],
                    nom=result["scientific_name"],
                    gbif_key=result.get("gbif_key", "?"),
                )
            else:
                failures.append(result)
                raison = str(result.get("raison_echec", "inconnue"))
                failure_reasons[raison] = failure_reasons.get(raison, 0) + 1
                logger.warning(
                    "espece_echec",
                    taxon_id=result["taxon_id_treekipedia"],
                    nom=result["scientific_name"],
                    raison=raison,
                )

            # Commit par batch de 100 + checkpoint
            if i % _BATCH_SIZE == 0:
                progress.last_offset = start_offset + i
                await session.commit()
                print(f"  [{i}/{len(species)}] {successes} succès, {len(failures)} échecs")

        # Commit final + checkpoint
        progress.last_offset = start_offset + len(species)
        progress.status = "completed"
        await session.commit()

    # 4. Statistiques
    print("\nStatistiques finales :")
    print(f"  Total traité : {len(species)}")
    print(f"  Succès : {successes}")
    print(f"  Échecs : {len(failures)}")
    if failure_reasons:
        print("\n  Raisons d'échec :")
        for raison, count in sorted(failure_reasons.items(), key=lambda x: -x[1]):
            print(f"    {raison}: {count}")

    print("\n" + "=" * 60)
    print("Ingestion terminée.")
    print("=" * 60)


def main() -> None:
    """Parse les arguments et lance l'ingestion."""
    parser = argparse.ArgumentParser(description="Ingestion Treekipedia → GSIE")
    parser.add_argument(
        "--limit",
        type=int,
        default=_DEFAULT_PILOT_LIMIT,
        help=f"Nombre d'espèces à ingérer (défaut: {_DEFAULT_PILOT_LIMIT})",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Offset de départ dans le CSV (défaut: 0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche ce qui serait fait sans écrire en base",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=_DEFAULT_CONCURRENCY,
        help=f"Nombre de requêtes GBIF simultanées (défaut: {_DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reprend depuis le dernier checkpoint (table ingestion_progress)",
    )
    args = parser.parse_args()

    try:
        asyncio.run(
            ingest_treekipedia(
                limit=args.limit,
                offset=args.offset,
                dry_run=args.dry_run,
                concurrency=args.concurrency,
                resume=args.resume,
            )
        )
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur.")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"\nErreur : {exc}", file=sys.stderr)
        logger.exception("ingest_treekipedia_echec")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Ingestion pilote Treekipedia → GSIE (100 espèces).

Pipeline d'ingestion du catalogue Treekipedia (DEC-000041) :
1. Lit 100 espèces depuis le CSV local Treekipedia (snapshot officiel)
2. Résout chaque nom scientifique via GBIF (GBIFClient.match_species)
3. Crée le taxon GSIE via BotanicalEngine._get_or_create_taxon
4. Ajoute un alias Treekipedia (namespace="treekipedia") pour la
   traçabilité croisée GSIE ↔ Treekipedia

Usage :
    python ingest_treekipedia.py              # 100 espèces pilotes
    python ingest_treekipedia.py --limit 50   # 50 espèces
    python ingest_treekipedia.py --dry-run    # affiche sans écrire
    python ingest_treekipedia.py --offset 1000  # commencer à l'offset 1000

Prérequis : base PostgreSQL démarrée (docker compose up -d db).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
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
from gsie_api.infrastructure.models.provenance import EntityAliasModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger("gsie_api.ingest_treekipedia")

_DEFAULT_PILOT_LIMIT = 100
_CONCURRENT_GBIF_REQUESTS = 5  # limite pour éviter le rate limit GBIF


async def _resolve_and_ingest_one(
    session: AsyncSession,
    gbif_client: GBIFClient,
    botanical_engine: BotanicalEngine,
    row: dict[str, str | None],
) -> dict[str, str | bool]:
    """Résout une espèce Treekipedia via GBIF et l'ingère dans GSIE.

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

    if not scientific_name:
        result["raison_echec"] = "nom_scientifique_vide"
        return result

    # 1. Résolution GBIF
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

    # 2. Création du taxon GSIE (déduplication automatique)
    try:
        entity_id = await botanical_engine._get_or_create_taxon(gbif_key)
    except Exception as exc:  # noqa: BLE001 — ingestion non bloquante
        result["raison_echec"] = f"taxon_creation:{exc!s:.100}"
        return result

    # 3. Ajout de l'alias Treekipedia (idempotent — vérifie d'abord)
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


async def ingest_treekipedia(
    limit: int = _DEFAULT_PILOT_LIMIT,
    offset: int = 0,
    dry_run: bool = False,
) -> None:
    """Point d'entrée — ingère `limit` espèces Treekipedia dans GSIE.

    Étapes :
    1. Lecture du CSV Treekipedia (limit + offset)
    2. Pour chaque espèce : résolution GBIF + création taxon + alias Treekipedia
    3. Statistiques finales (succès, échecs, raisons)
    """
    print("=" * 60)
    print(f"Ingestion pilote Treekipedia → GSIE ({limit} espèces)")
    print("=" * 60)

    if dry_run:
        print("\n[DRY-RUN] Aucune écriture en base — affichage uniquement.\n")

    # 1. Lecture du CSV
    treekipedia_client = TreekipediaClient()
    try:
        species = treekipedia_client.list_species(limit=limit, offset=offset)
    except TreekipediaClientError as exc:
        print(f"\nErreur : impossible de lire le CSV Treekipedia : {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\n[1/3] {len(species)} espèces lues depuis le CSV Treekipedia")
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

    # 2. Ingestion
    print("\n[2/3] Résolution GBIF + ingestion en cours...")
    gbif_client = GBIFClient()
    successes = 0
    failures: list[dict[str, str | bool]] = []
    failure_reasons: dict[str, int] = {}

    async with async_session_factory() as session:
        botanical_engine = BotanicalEngine(session=session)

        # Traitement séquentiel pour éviter le rate limit GBIF (30 req/min)
        # et garantir l'ordre déterministe pour le débogage
        for i, row in enumerate(species, 1):
            result = await _resolve_and_ingest_one(session, gbif_client, botanical_engine, row)
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

            # Commit par lot de 10 pour éviter une transaction trop longue
            if i % 10 == 0:
                await session.commit()
                print(f"  [{i}/{len(species)}] {successes} succès, {len(failures)} échecs")

        await session.commit()

    # 3. Statistiques
    print("\n[3/3] Statistiques finales :")
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
    parser = argparse.ArgumentParser(description="Ingestion pilote Treekipedia → GSIE")
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
        help="Index de départ dans le CSV (pagination)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche ce qui serait fait sans écrire en base",
    )
    args = parser.parse_args()

    try:
        asyncio.run(
            ingest_treekipedia(
                limit=args.limit,
                offset=args.offset,
                dry_run=args.dry_run,
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

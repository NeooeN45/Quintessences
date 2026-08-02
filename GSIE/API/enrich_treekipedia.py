"""Enrichissement Treekipedia — taxonomie riche + images + descriptions Wikipédia.

Ce script enrichit les espèces pilotes déjà ingérées avec :
1. **Taxonomie riche** depuis le CSV export Treekipedia (genus, family,
   taxonomic_class, taxonomic_order) — stockée dans metadata_json de l'entity
2. **Images Wikimedia Commons** — d'abord depuis le JSON pré-résolu
   Treekipedia (3999 espèces), puis fallback sur l'API Commons en direct.
   Stockées dans la table dédiée `entity_image` (migration 20260801_0027).
3. **Descriptions Wikipédia (EN puis fallback FR)** — extrait introductif.
   Stockées dans la table dédiée `entity_description` (migration 20260801_0027).
   Les descriptions < 100 chars sont filtrées (audit P2-1).

Usage :
    python enrich_treekipedia.py              # enrichit les 100 espèces pilotes
    python enrich_treekipedia.py --limit 50   # limite à 50 espèces
    python enrich_treekipedia.py --dry-run    # affiche sans écrire
    python enrich_treekipedia.py --skip-wikipedia  # ignore les descriptions
    python enrich_treekipedia.py --skip-images     # ignore les images
    python enrich_treekipedia.py --migrate-metadata # migre metadata_json vers tables

Prérequis : base PostgreSQL démarrée + ingestion pilote déjà effectuée
(ingest_treekipedia.py) + migration 20260801_0027 appliquée.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from gsie_api.core.logging import get_logger
from gsie_api.engines.botanical.treekipedia_client import (
    TreekipediaClient,
    TreekipediaClientError,
    parse_common_names,
)
from gsie_api.engines.botanical.wikimedia_client import (
    _MIN_DESCRIPTION_LENGTH,
    WikimediaClient,
    WikimediaClientError,
)
from gsie_api.infrastructure.database import async_session_factory
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.enrichment import (
    EntityDescriptionModel,
    EntityImageModel,
)
from gsie_api.infrastructure.models.provenance import EntityAliasModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger("gsie_api.enrich_treekipedia")

_DEFAULT_LIMIT = 100
_MIN_QUALITY_HIGH = 500  # > 500 chars = high quality
_MIN_QUALITY_MEDIUM = 200  # > 200 chars = medium quality


def _estimate_quality(description: str) -> str:
    """Estime la qualité d'une description (high, medium, low, stub)."""
    length = len(description)
    if length >= _MIN_QUALITY_HIGH:
        return "high"
    if length >= _MIN_QUALITY_MEDIUM:
        return "medium"
    if length >= _MIN_DESCRIPTION_LENGTH:
        return "low"
    return "stub"


async def _enrich_one(
    session: AsyncSession,
    treekipedia_client: TreekipediaClient,
    wikimedia_client: WikimediaClient,
    row: dict[str, str | None],
    *,
    skip_wikipedia: bool = False,
    skip_images: bool = False,
) -> dict[str, Any]:
    """Enrichit une espèce avec taxonomie + image + description.

    Returns:
        Dict avec le statut de l'enrichissement.
    """
    taxon_id_treekipedia = row.get("taxon_id") or ""
    scientific_name = row.get("species_scientific_name") or ""

    result: dict[str, Any] = {
        "taxon_id_treekipedia": taxon_id_treekipedia,
        "scientific_name": scientific_name,
        "success": False,
    }

    if not scientific_name:
        result["raison_echec"] = "nom_scientifique_vide"
        return result

    # 1. Trouver l'entity GSIE via l'alias Treekipedia
    alias_result = await session.execute(
        select(EntityAliasModel.entity_id).where(
            EntityAliasModel.namespace == "treekipedia",
            EntityAliasModel.external_id == taxon_id_treekipedia,
        )
    )
    entity_id = alias_result.scalars().first()
    if entity_id is None:
        result["raison_echec"] = "entity_non_ingeree"
        return result

    # 2. Récupérer la resource entity pour mettre à jour metadata_json
    resource_result = await session.execute(
        select(ResourceModel).where(ResourceModel.id == entity_id)
    )
    resource = resource_result.scalars().first()
    if resource is None:
        result["raison_echec"] = "resource_introuvable"
        return result

    # 3. Construire les métadonnées enrichies (taxonomy + common_names restent
    #    dans metadata_json — ce sont des attributs simples, pas multi-valués)
    metadata: dict[str, Any] = dict(resource.metadata_json or {})

    # 3a. Taxonomie riche depuis le CSV export
    metadata["taxonomy"] = {
        "genus": row.get("genus"),
        "family": row.get("family"),
        "taxonomic_class": row.get("taxonomic_class"),
        "taxonomic_order": row.get("taxonomic_order"),
        "subspecies": row.get("subspecies"),
    }

    # 3b. Noms vernaculaires
    common_names_raw = row.get("species_common_name")
    metadata["common_names"] = parse_common_names(common_names_raw)

    enriched_fields: list[str] = ["taxonomy"]

    # 4. Image Wikimedia Commons → table entity_image
    if not skip_images:
        # D'abord : image pré-résolue Treekipedia (JSON local, rapide)
        try:
            pre_resolved = treekipedia_client.get_species_image(scientific_name)
        except TreekipediaClientError as exc:
            logger.warning("image_json_echec", nom=scientific_name, erreur=str(exc)[:100])
            pre_resolved = None

        if pre_resolved is not None:
            await _upsert_image(
                session,
                entity_id,
                url=pre_resolved.get("image_url", ""),
                license_=pre_resolved.get("license", ""),
                photographer=pre_resolved.get("photographer", ""),
                page_url=pre_resolved.get("page_url", ""),
                source=pre_resolved.get("source", "Wikimedia Commons"),
                is_primary=True,
            )
            enriched_fields.append("image_pre_resolue")
        else:
            # Fallback : API Wikimedia Commons en direct
            try:
                images = await wikimedia_client.search_species_images(scientific_name, limit=1)
                if images:
                    img = images[0]
                    await _upsert_image(
                        session,
                        entity_id,
                        url=img.get("url", ""),
                        license_=img.get("license", ""),
                        photographer=img.get("photographer", ""),
                        page_url=img.get("description_url", ""),
                        source="Wikimedia Commons",
                        is_primary=True,
                    )
                    enriched_fields.append("image_api_commons")
            except WikimediaClientError as exc:
                logger.warning("image_api_echec", nom=scientific_name, erreur=str(exc)[:100])

    # 5. Description Wikipédia (EN puis fallback FR) → table entity_description
    if not skip_wikipedia:
        try:
            description, lang = await wikimedia_client.get_species_description_with_fallback(
                scientific_name
            )
            if description and len(description) >= _MIN_DESCRIPTION_LENGTH:
                quality = _estimate_quality(description)
                await _upsert_description(
                    session,
                    entity_id,
                    language=lang,
                    source="wikipedia",
                    content=description[:2000],
                    quality=quality,
                )
                enriched_fields.append(f"description_wikipedia_{lang}")
            elif description:
                # Description trop courte — stub, on ne stocke pas (audit P2-1)
                logger.info(
                    "description_stub_ignoree",
                    nom=scientific_name,
                    longueur=len(description),
                )
        except WikimediaClientError as exc:
            logger.warning("description_echec", nom=scientific_name, erreur=str(exc)[:100])

    # 6. Persister metadata_json (taxonomy + common_names)
    resource.metadata_json = metadata
    await session.flush()

    result["success"] = True
    result["enriched_fields"] = enriched_fields
    return result


async def _upsert_image(
    session: AsyncSession,
    entity_id: Any,
    *,
    url: str,
    license_: str,
    photographer: str,
    page_url: str,
    source: str,
    is_primary: bool,
) -> None:
    """Insère ou met à jour l'image principale d'une entity.

    Idempotent : si une image primaire existe déjà pour cette entity,
    elle est mise à jour (URL, license, etc.) plutôt que dupliquée.
    """
    existing = await session.execute(
        select(EntityImageModel).where(
            EntityImageModel.entity_id == entity_id,
            EntityImageModel.is_primary.is_(True),
        )
    )
    img = existing.scalars().first()
    if img is not None:
        img.url = url
        img.license = license_ or None
        img.photographer = photographer or None
        img.page_url = page_url or None
        img.source = source
    else:
        session.add(
            EntityImageModel(
                entity_id=entity_id,
                url=url,
                license=license_ or None,
                photographer=photographer or None,
                page_url=page_url or None,
                source=source,
                is_primary=is_primary,
            )
        )


async def _upsert_description(
    session: AsyncSession,
    entity_id: Any,
    *,
    language: str,
    source: str,
    content: str,
    quality: str,
) -> None:
    """Insère ou met à jour la description d'une entity (idempotent).

    Contrainte unique (entity_id, language, source) : si une description
    existe déjà pour cette combinaison, elle est mise à jour.
    """
    existing = await session.execute(
        select(EntityDescriptionModel).where(
            EntityDescriptionModel.entity_id == entity_id,
            EntityDescriptionModel.language == language,
            EntityDescriptionModel.source == source,
        )
    )
    desc = existing.scalars().first()
    if desc is not None:
        desc.content = content
        desc.quality = quality
    else:
        session.add(
            EntityDescriptionModel(
                entity_id=entity_id,
                language=language,
                source=source,
                content=content,
                quality=quality,
            )
        )


async def _migrate_metadata_to_tables(session: AsyncSession) -> dict[str, int]:
    """Migère les images et descriptions de metadata_json vers les tables dédiées.

    Pour les entities déjà enrichies (pilote 100 espèces) qui ont stocké
    image et description dans metadata_json, cette fonction les déplace
    vers entity_image et entity_description.

    Returns:
        Dict avec le nombre d'images et descriptions migrées.
    """
    counts = {"images": 0, "descriptions": 0}
    r = await session.execute(select(ResourceModel).where(ResourceModel.type == "entity"))
    entities = r.scalars().all()
    for entity in entities:
        md = entity.metadata_json or {}
        # Image
        img = md.get("primary_image")
        if img and isinstance(img, dict) and img.get("url"):
            await _upsert_image(
                session,
                entity.id,
                url=img["url"],
                license_=img.get("license", ""),
                photographer=img.get("photographer", ""),
                page_url=img.get("page_url", ""),
                source=img.get("source", "Wikimedia Commons"),
                is_primary=True,
            )
            counts["images"] += 1
        # Description
        desc = md.get("wikipedia_extract")
        if desc and len(desc) >= _MIN_DESCRIPTION_LENGTH:
            lang = md.get("wikipedia_language", "en")
            await _upsert_description(
                session,
                entity.id,
                language=lang,
                source="wikipedia",
                content=desc[:2000],
                quality=_estimate_quality(desc),
            )
            counts["descriptions"] += 1
    await session.commit()
    return counts


async def enrich_treekipedia(
    limit: int = _DEFAULT_LIMIT,
    dry_run: bool = False,
    skip_wikipedia: bool = False,
    skip_images: bool = False,
    migrate_metadata: bool = False,
) -> None:
    """Point d'entrée — enrichit les espèces Treekipedia déjà ingérées.

    Étapes :
    1. Lecture du CSV riche Treekipedia (genus, family, class, order)
    2. Pour chaque espèce : mise à jour metadata_json avec taxonomie +
       insertion dans entity_image + entity_description
    3. Statistiques finales
    """
    print("=" * 60)
    print(f"Enrichissement Treekipedia ({limit} espèces)")
    parts: list[str] = []
    if skip_wikipedia:
        parts.append("sans Wikipédia")
    if skip_images:
        parts.append("sans images")
    if parts:
        print(f"  ({', '.join(parts)})")
    print("=" * 60)

    if dry_run:
        print("\n[DRY-RUN] Aucune écriture en base — affichage uniquement.\n")

    # Mode migration metadata_json → tables
    if migrate_metadata:
        print("\n[Migration] metadata_json → entity_image + entity_description...")
        async with async_session_factory() as session:
            counts = await _migrate_metadata_to_tables(session)
        print(f"  Images migrées      : {counts['images']}")
        print(f"  Descriptions migrées : {counts['descriptions']}")
        print("=" * 60)
        print("Migration terminée.")
        print("=" * 60)
        return

    # 1. Lecture du CSV riche — on charge tout en mémoire pour pouvoir
    #    chercher par taxon_id (les CSV riche et simple ont des ordres différents)
    treekipedia_client = TreekipediaClient()
    try:
        all_rich_species = treekipedia_client.list_species_rich()
    except TreekipediaClientError as exc:
        print(f"\nErreur : CSV riche introuvable : {exc}", file=sys.stderr)
        sys.exit(1)

    # Construire un index taxon_id -> row pour lookup rapide
    rich_index: dict[str, dict[str, str | None]] = {
        row.get("taxon_id", ""): row for row in all_rich_species
    }
    print(f"\n[1/3] {len(all_rich_species)} espèces indexées depuis le CSV riche Treekipedia")

    # 2. Récupérer les taxon_ids déjà ingérés (alias treekipedia en base)
    async with async_session_factory() as session:
        alias_result = await session.execute(
            select(EntityAliasModel.external_id)
            .where(EntityAliasModel.namespace == "treekipedia")
            .limit(limit)
        )
        ingested_taxon_ids = [str(tid) for tid in alias_result.scalars().all()]

    print(f"  {len(ingested_taxon_ids)} espèces déjà ingérées en base à enrichir")

    # Filtrer : ne garder que les taxon_ids présents dans le CSV riche
    species = [rich_index[tid] for tid in ingested_taxon_ids if tid in rich_index]
    missing = len(ingested_taxon_ids) - len(species)
    if missing > 0:
        print(f"  Attention : {missing} taxon_ids ingérés non trouvés dans le CSV riche")
    if dry_run:
        for row in species[:5]:
            print(
                f"  {row.get('taxon_id', '?'):30s}  "
                f"{row.get('species_scientific_name', '?'):30s}  "
                f"family={row.get('family', '?')}"
            )
        if len(species) > 5:
            print(f"  ... et {len(species) - 5} autres")
        print(f"\n[DRY-RUN] {len(species)} espèces seraient enrichies")
        print("=" * 60)
        return

    # 2. Enrichissement
    print("\n[2/3] Enrichissement en cours...")
    wikimedia_client = WikimediaClient()
    successes = 0
    failures: list[dict[str, Any]] = []
    field_counts: dict[str, int] = {}

    async with async_session_factory() as session:
        for i, row in enumerate(species, 1):
            result = await _enrich_one(
                session,
                treekipedia_client,
                wikimedia_client,
                row,
                skip_wikipedia=skip_wikipedia,
                skip_images=skip_images,
            )
            if result["success"]:
                successes += 1
                for field in result.get("enriched_fields", []):
                    field_counts[field] = field_counts.get(field, 0) + 1
                logger.info(
                    "espece_enrichie",
                    nom=result["scientific_name"],
                    champs=result["enriched_fields"],
                )
            else:
                failures.append(result)
                logger.warning(
                    "espece_echec_enrichissement",
                    nom=result["scientific_name"],
                    raison=result.get("raison_echec"),
                )

            if i % 10 == 0:
                await session.commit()
                print(f"  [{i}/{len(species)}] {successes} enrichis, {len(failures)} échecs")

        await session.commit()

    # 3. Statistiques
    print("\n[3/3] Statistiques finales :")
    print(f"  Total traité : {len(species)}")
    print(f"  Succès : {successes}")
    print(f"  Échecs : {len(failures)}")
    if field_counts:
        print("\n  Champs enrichis :")
        for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
            print(f"    {field}: {count}")

    print("\n" + "=" * 60)
    print("Enrichissement terminé.")
    print("=" * 60)


def main() -> None:
    """Parse les arguments et lance l'enrichissement."""
    parser = argparse.ArgumentParser(
        description="Enrichissement Treekipedia (taxonomie + images + descriptions)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=_DEFAULT_LIMIT,
        help=f"Nombre d'espèces à enrichir (défaut: {_DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche ce qui serait fait sans écrire en base",
    )
    parser.add_argument(
        "--skip-wikipedia",
        action="store_true",
        help="Ignore les descriptions Wikipédia (gain de temps)",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Ignore les images Wikimedia Commons",
    )
    parser.add_argument(
        "--migrate-metadata",
        action="store_true",
        help="Migère les images/descriptions de metadata_json vers les tables dédiées",
    )
    args = parser.parse_args()

    try:
        asyncio.run(
            enrich_treekipedia(
                limit=args.limit,
                dry_run=args.dry_run,
                skip_wikipedia=args.skip_wikipedia,
                skip_images=args.skip_images,
                migrate_metadata=args.migrate_metadata,
            )
        )
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur.")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"\nErreur : {exc}", file=sys.stderr)
        logger.exception("enrich_treekipedia_echec")
        sys.exit(1)


if __name__ == "__main__":
    main()

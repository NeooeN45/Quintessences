"""Script de seeding — alimentation de la base PostgreSQL.

Insère les données de référence dans l'ordre :
1. Familles botaniques
2. Genres botaniques
3. Essences forestières
4. Habitats Natura 2000
5. Stations forestières
6. Groupes écologiques

Usage :
    python -m gsie_api.seeds.run_seeds
    python -m gsie_api.seeds.run_seeds --botanical-only
    python -m gsie_api.seeds.run_seeds --ecosystem-only

Idempotent : INSERT ... ON CONFLICT DO NOTHING.
"""

from __future__ import annotations

import argparse
import asyncio
from typing import TYPE_CHECKING

from sqlalchemy import select

from gsie_api.core.logging import get_logger, setup_logging
from gsie_api.infrastructure.database import async_session_factory, engine
from gsie_api.infrastructure.knowledge_models import (
    BotanicalEssenceModel,
    BotanicalFamilleModel,
    BotanicalGenreModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger("gsie_api.seeds")


async def seed_botanical(session: AsyncSession) -> dict[str, int]:
    """Insère les familles, genres et essences botaniques.

    Returns:
        Dictionnaire avec le nombre d'insertions par catégorie.
    """
    from gsie_api.seeds.botanical_data import ESSENCES, FAMILLES, GENRES

    counts = {"familles": 0, "genres": 0, "essences": 0}

    # 1. Familles
    for famille in FAMILLES:
        existing = await session.execute(
            select(BotanicalFamilleModel).where(
                BotanicalFamilleModel.nom_scientifique == famille["nom_scientifique"]
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(BotanicalFamilleModel(**famille))
            counts["familles"] += 1

    await session.flush()

    # 2. Genres (nécessitent les familles)
    famille_cache: dict[str, int] = {}
    for genre in GENRES:
        famille_nom: str = str(genre.pop("famille_nom"))
        if famille_nom not in famille_cache:
            result = await session.execute(
                select(BotanicalFamilleModel.id).where(
                    BotanicalFamilleModel.nom_scientifique == famille_nom
                )
            )
            famille_cache[famille_nom] = result.scalar_one()

        existing = await session.execute(
            select(BotanicalGenreModel).where(
                BotanicalGenreModel.nom_scientifique == genre["nom_scientifique"]
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(BotanicalGenreModel(famille_id=famille_cache[famille_nom], **genre))
            counts["genres"] += 1

    await session.flush()

    # 3. Essences (nécessitent les genres)
    genre_cache: dict[str, int] = {}
    for essence in ESSENCES:
        genre_nom: str = str(essence.pop("genre_nom"))
        if genre_nom not in genre_cache:
            result = await session.execute(
                select(BotanicalGenreModel.id).where(
                    BotanicalGenreModel.nom_scientifique == genre_nom
                )
            )
            genre_cache[genre_nom] = result.scalar_one()

        existing = await session.execute(
            select(BotanicalEssenceModel).where(
                BotanicalEssenceModel.nom_scientifique == essence["nom_scientifique"]
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(BotanicalEssenceModel(genre_id=genre_cache[genre_nom], **essence))
            counts["essences"] += 1

    await session.flush()
    logger.info("botanical_seeded", **counts)
    return counts


async def seed_ecosystem(session: AsyncSession) -> dict[str, int]:
    """Insère les habitats, stations et groupes écologiques.

    Returns:
        Dictionnaire avec le nombre d'insertions par catégorie.
    """
    from gsie_api.infrastructure.knowledge_models import (
        EcosystemGroupeEcologiqueModel,
        EcosystemHabitatModel,
        EcosystemStationModel,
    )
    from gsie_api.seeds.ecosystem_data import (
        GROUPES_ECOLOGIQUES,
        HABITATS_NATURA2000,
        STATIONS_FORESTIERES,
    )

    counts = {"habitats": 0, "stations": 0, "groupes_ecologiques": 0}

    for habitat in HABITATS_NATURA2000:
        existing = await session.execute(
            select(EcosystemHabitatModel).where(
                EcosystemHabitatModel.code_eur28 == habitat["code_eur28"]
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(EcosystemHabitatModel(**habitat))
            counts["habitats"] += 1

    for station in STATIONS_FORESTIERES:
        existing = await session.execute(
            select(EcosystemStationModel).where(
                EcosystemStationModel.code_station == station["code_station"]
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(EcosystemStationModel(**station))
            counts["stations"] += 1

    for groupe in GROUPES_ECOLOGIQUES:
        existing = await session.execute(
            select(EcosystemGroupeEcologiqueModel).where(
                EcosystemGroupeEcologiqueModel.nom_groupe == groupe["nom_groupe"]
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(EcosystemGroupeEcologiqueModel(**groupe))
            counts["groupes_ecologiques"] += 1

    await session.flush()
    logger.info("ecosystem_seeded", **counts)
    return counts


async def run_seeds(botanical: bool = True, ecosystem: bool = True) -> None:
    """Exécute les seeds sélectionnés."""
    setup_logging("INFO", "development")

    async with async_session_factory() as session:
        try:
            if botanical:
                logger.info("seeding_botanical_start")
                counts = await seed_botanical(session)
                logger.info(
                    "botanical_seed_complete",
                    familles=counts["familles"],
                    genres=counts["genres"],
                    essences=counts["essences"],
                )

            if ecosystem:
                logger.info("seeding_ecosystem_start")
                counts = await seed_ecosystem(session)
                logger.info(
                    "ecosystem_seed_complete",
                    habitats=counts["habitats"],
                    stations=counts["stations"],
                    groupes=counts["groupes_ecologiques"],
                )

            await session.commit()
            logger.info("all_seeds_committed")
        except Exception as exc:
            await session.rollback()
            logger.error("seed_failed", error=str(exc))
            raise

    await engine.dispose()


def main() -> None:
    """Point d'entrée CLI."""
    parser = argparse.ArgumentParser(description="Seed de la base GSIE")
    parser.add_argument("--botanical-only", action="store_true", help="Seulement botanique")
    parser.add_argument("--ecosystem-only", action="store_true", help="Seulement écosystèmes")
    args = parser.parse_args()

    botanical = not args.ecosystem_only
    ecosystem = not args.botanical_only

    asyncio.run(run_seeds(botanical=botanical, ecosystem=ecosystem))


if __name__ == "__main__":
    main()

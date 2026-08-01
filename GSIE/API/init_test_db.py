"""Initialisation de la base de test GSIE — seeds + API externes.

Ce script peuple la base PostgreSQL/PostGIS avec :
1. Les seeds internes (autécologie Parelle 2007 + Rameau 2008, 26 profils)
2. Les essences forestières (taxons GBIF de référence)
3. Des données réelles depuis les API externes (IGN altitude)

Usage :
    python init_test_db.py              # seeds internes uniquement
    python init_test_db.py --with-apis  # seeds + appels API externes
    python init_test_db.py --dry-run    # affiche ce qui serait fait sans écrire

Prérequis : la base PostgreSQL doit tourner (docker compose up -d db).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import func, select

from gsie_api.core.logging import get_logger
from gsie_api.engines.botanical.engine import BotanicalEngine
from gsie_api.engines.botanical.schemas import BotanicalQuery
from gsie_api.engines.evidence.schemas import EvidenceLevel
from gsie_api.engines.gis.engine import GISEngine
from gsie_api.engines.gis.schemas import AltitudeRequest
from gsie_api.infrastructure.database import async_session_factory
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.assertion import (
    AssertionModel,
    EvidenceAssessmentModel,
)
from gsie_api.infrastructure.models.enums import ClaimKind, LifecycleStatus
from gsie_api.infrastructure.models.temporal_engine import RevisionModel
from gsie_api.seeds.autecology_rameau_data import all_autecology_profiles

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger("gsie_api.init_test_db")

# Essences forestières françaises de référence — clés GBIF vérifiées
_ESSENCES_REFERENCE: list[dict[str, str | int]] = [
    {
        "nom_scientifique": "Quercus robur",
        "nom_vernaculaire": "Chêne pédonculé",
        "gbif_key": 2878688,
    },
    {
        "nom_scientifique": "Quercus petraea",
        "nom_vernaculaire": "Chêne sessile",
        "gbif_key": 2880130,
    },
    {"nom_scientifique": "Quercus ilex", "nom_vernaculaire": "Chêne vert", "gbif_key": 2878223},
    {"nom_scientifique": "Fagus sylvatica", "nom_vernaculaire": "Hêtre", "gbif_key": 2882431},
    {
        "nom_scientifique": "Pinus sylvestris",
        "nom_vernaculaire": "Pin sylvestre",
        "gbif_key": 2684481,
    },
    {"nom_scientifique": "Abies alba", "nom_vernaculaire": "Sapin pectiné", "gbif_key": 2685764},
]

# Points de test pour l'API IGN altitude
_POINTS_IGN: list[dict[str, float | str]] = [
    {"latitude": 48.1928, "longitude": 7.3289, "label": "Ribeauvillé (Vosges)"},
    {"latitude": 48.5734, "longitude": 7.7521, "label": "Strasbourg (Bas-Rhin)"},
    {"latitude": 44.8378, "longitude": -0.5792, "label": "Bordeaux (Gironde)"},
]


async def _seed_essences(session: AsyncSession) -> int:
    """Crée les taxons GBIF pour les essences de référence via BotanicalEngine.

    Utilise le mécanisme de déduplication du moteur (_get_or_create_taxon)
    plutôt que d'insérer directement — garantit la cohérence avec le
    fonctionnement normal de l'API.
    """
    engine = BotanicalEngine(session=session)
    count = 0
    for essence in _ESSENCES_REFERENCE:
        # Idempotence : vérifie si le taxon GBIF existe déjà
        existing = await session.execute(
            select(ResourceModel.gsie_id).where(
                ResourceModel.gsie_id == f"gsie:entity:taxon:{essence['gbif_key']}"
            )
        )
        if existing.scalars().first() is not None:
            logger.info(
                "essence_existante",
                nom=essence["nom_scientifique"],
                gbif_key=essence["gbif_key"],
            )
            count += 1
            continue

        query = BotanicalQuery(
            essence=essence["nom_scientifique"],  # type: ignore[arg-type]
        )
        try:
            await engine.query(query)
            count += 1
            logger.info(
                "essence_creee",
                nom=essence["nom_scientifique"],
                gbif_key=essence["gbif_key"],
            )
        except Exception as exc:  # noqa: BLE001 — seed non bloquant
            logger.warning(
                "essence_echec",
                nom=essence["nom_scientifique"],
                erreur=str(exc)[:200],
            )
    await session.commit()
    return count


async def _seed_autecology(session: AsyncSession) -> int:
    """Persiste les 26 profils autécologiques (Parelle 2007 + Rameau 2008).

    Chaque profil est une resource `assertion` (ClaimKind.observation) liée
    à l'`entity` du taxon GBIF correspondant, avec une `EvidenceAssessment`
    portant le niveau de preuve de la source.
    """
    from datetime import UTC, datetime

    profiles = all_autecology_profiles()
    engine = BotanicalEngine(session=session)
    count = 0
    now = datetime.now(UTC)

    for profile in profiles:
        # Le taxon doit exister avant l'assertion ; son identifiant n'est pas
        # utilise ici — le gsie_id de l'assertion est deterministe.
        await engine._get_or_create_taxon(profile.species_gbif_taxon_key)

        # Idempotence : vérifie si le profil existe déjà (gsie_id déterministe)
        gsie_id = f"gsie:assertion:autecology:{profile.species_gbif_taxon_key}:{profile.variable}"
        existing = await session.execute(
            select(ResourceModel).where(ResourceModel.gsie_id == gsie_id)
        )
        if existing.scalars().first() is not None:
            logger.info(
                "profil_autecologie_existant",
                gbif_key=profile.species_gbif_taxon_key,
                variable=profile.variable,
            )
            continue

        # Resource assertion — metadata_json porte la variable et la valeur
        assertion_id = uuid4()
        session.add(
            ResourceModel(
                id=assertion_id,
                type="assertion",
                gsie_id=gsie_id,
                metadata_json={
                    "variable": profile.variable,
                    "value_text": profile.value_text,
                    "method": profile.method,
                    "territory_description": profile.territory_description,
                    "source": {
                        "type_source": profile.source.type_source.value,
                        "auteur": profile.source.auteur,
                        "reference": profile.source.reference,
                    },
                },
            )
        )

        # Resource evidence_assessment
        evidence_id = uuid4()
        session.add(
            ResourceModel(
                id=evidence_id,
                type="evidence_assessment",
                gsie_id=f"gsie:evidence:{profile.species_gbif_taxon_key}:{profile.variable}",
                metadata_json={},
            )
        )
        await session.flush()

        # Tables satellites
        session.add(
            AssertionModel(
                id=assertion_id,
                claim_kind=ClaimKind.observation,
                lifecycle_status=LifecycleStatus.accepted,
                version=1,
            )
        )
        session.add(
            EvidenceAssessmentModel(
                id=evidence_id,
                assertion_id=assertion_id,
                level=EvidenceLevel(profile.evidence_level.value),
                method=profile.method[:200],
                evaluated_at=now,
            )
        )
        session.add(
            RevisionModel(
                target_id=assertion_id,
                version=1,
                author_id=None,
                justification=f"Seed initial — profil autécologique {profile.variable}",
                valid_time_start=now,
                transaction_time=now,
            )
        )
        count += 1
        logger.info(
            "profil_autecologie_cree",
            gbif_key=profile.species_gbif_taxon_key,
            variable=profile.variable,
        )

    await session.commit()
    return count


async def _seed_altitude_ign(session: AsyncSession, dry_run: bool = False) -> int:
    """Récupère l'altitude réelle pour 3 points de test via l'API IGN.

    ADR-009 : aucune valeur inventée. Si l'API IGN est indisponible,
    le seed est ignoré avec un avertissement — pas de valeur par défaut.
    """
    if dry_run:
        for point in _POINTS_IGN:
            print(f"  [DRY-RUN] Altitude IGN pour {point['label']}")
        return len(_POINTS_IGN)

    engine = GISEngine(session=session)
    count = 0
    for point in _POINTS_IGN:
        request = AltitudeRequest(
            latitude=point["latitude"],  # type: ignore[arg-type]
            longitude=point["longitude"],  # type: ignore[arg-type]
        )
        try:
            result = await engine.get_altitude(request)
            logger.info(
                "altitude_ign_recuperee",
                label=point["label"],
                altitude_m=result.altitude_m,
            )
            count += 1
        except Exception as exc:  # noqa: BLE001 — API externe non bloquante
            logger.warning(
                "altitude_ign_echec",
                label=point["label"],
                erreur=str(exc)[:200],
            )
    await session.commit()
    return count


async def _verifier_etat_base(session: AsyncSession) -> dict[str, int]:
    """Retourne un résumé de l'état de la base après initialisation."""
    result = await session.execute(
        select(ResourceModel.type, func.count(ResourceModel.id)).group_by(ResourceModel.type)
    )
    return {type_name: count for type_name, count in result.fetchall()}


async def init_base(with_apis: bool = False, dry_run: bool = False) -> None:
    """Point d'entrée principal — initialise la base de test.

    Étapes :
    1. Seeds botaniques (essences de référence via GBIF)
    2. Seeds autécologiques (26 profils Parelle + Rameau)
    3. (Optionnel) Données réelles IGN altitude
    4. Vérification finale
    """
    print("=" * 60)
    print("Initialisation de la base de test GSIE")
    print("=" * 60)

    if dry_run:
        print("\n[DRY-RUN] Aucune écriture en base — affichage uniquement.\n")

    async with async_session_factory() as session:
        # Étape 1 — Essences de référence
        print("\n[1/3] Seeds botaniques — essences forestières de référence...")
        if dry_run:
            print(f"  {len(_ESSENCES_REFERENCE)} essences seraient créées via GBIF")
            n_essences = len(_ESSENCES_REFERENCE)
        else:
            n_essences = await _seed_essences(session)
        print(f"  -> {n_essences} essences créées")

        # Étape 2 — Profils autécologiques
        print("\n[2/3] Seeds autécologiques — Parelle 2007 + Rameau 2008...")
        if dry_run:
            profiles = all_autecology_profiles()
            print(f"  {len(profiles)} profils seraient persistés")
            n_profiles = len(profiles)
        else:
            n_profiles = await _seed_autecology(session)
        print(f"  -> {n_profiles} profils autécologiques créés")

        # Étape 3 — Données IGN (optionnel)
        if with_apis:
            print("\n[3/3] API externes — altitude IGN (3 points de test)...")
            n_altitudes = await _seed_altitude_ign(session, dry_run=dry_run)
            print(f"  -> {n_altitudes} altitudes récupérées")
        else:
            print("\n[3/3] API externes — ignorées (utiliser --with-apis pour les activer)")

        # Vérification finale
        if not dry_run:
            print("\n" + "=" * 60)
            print("État final de la base :")
            stats = await _verifier_etat_base(session)
            if not stats:
                print("  (base toujours vide)")
            else:
                for type_name, count in sorted(stats.items()):
                    print(f"  {type_name}: {count}")

        print("\n" + "=" * 60)
        print("Initialisation terminée.")
        print("=" * 60)


def main() -> None:
    """Parse les arguments et lance l'initialisation."""
    parser = argparse.ArgumentParser(
        description="Initialise la base de test GSIE avec seeds et données API externes"
    )
    parser.add_argument(
        "--with-apis",
        action="store_true",
        help="Active les appels aux API externes (IGN, GBIF)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche ce qui serait fait sans écrire en base",
    )
    args = parser.parse_args()

    try:
        asyncio.run(init_base(with_apis=args.with_apis, dry_run=args.dry_run))
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur.")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"\nErreur : {exc}", file=sys.stderr)
        logger.exception("init_test_db_echec")
        sys.exit(1)


if __name__ == "__main__":
    main()

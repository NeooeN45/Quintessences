"""Métriques Prometheus sur la qualité de la base GSIE.

Expose des Gauges personnalisées sur la complétude, la fraîcheur et
la cohérence des données d'enrichissement (audit qualité base du
2026-08-01). Ces métriques sont calculées à la demande via un
collector custom Prometheus.

Métriques exposées :
- gsie_entities_total : nombre total d'entities (taxons)
- gsie_aliases_total{namespace} : nombre d'aliases par namespace
- gsie_enrichment_completeness{field} : taux de complétude par champ
  (taxonomy, image, description, common_names)
- gsie_descriptions_by_language{language} : descriptions par langue
- gsie_descriptions_by_quality{quality} : descriptions par niveau de qualité
- gsie_images_validated_total : images avec URL validée
- gsie_images_unvalidated_total : images sans validation d'URL
- gsie_ingestion_progress{pipeline,status} : progression des pipelines
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from prometheus_client import Gauge, Info
from sqlalchemy import func, select, text

from gsie_api.core.logging import get_logger
from gsie_api.infrastructure.database import async_session_factory
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.enrichment import (
    EntityDescriptionModel,
    EntityImageModel,
    IngestionProgressModel,
)
from gsie_api.infrastructure.models.provenance import EntityAliasModel

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = get_logger("gsie_api.metrics.db_quality")

# Plafond de séries par métrique étiquetée. Les valeurs de `namespace`,
# `language`, `quality` et `pipeline` viennent de la base, donc de données
# d'ingestion externes : sans plafond, la cardinalité du registre Prometheus
# suit la donnée, et une source mal normalisée fait exploser la mémoire du
# serveur comme celle du scraper. Les séries au-delà du plafond sont écartées
# et journalisées — jamais tronquées en silence.
_MAX_SERIES_PAR_METRIQUE = 50

# Gauges — valeurs calculées à la demande
_g_entities_total = Gauge(
    "gsie_entities_total",
    "Nombre total d'entities (taxons) en base",
)

_g_aliases_total = Gauge(
    "gsie_aliases_total",
    "Nombre d'aliases par namespace",
    labelnames=("namespace",),
)

_g_enrichment_completeness = Gauge(
    "gsie_enrichment_completeness",
    "Taux de complétude des champs d'enrichissement (0-100)",
    labelnames=("field",),
)

_g_descriptions_by_language = Gauge(
    "gsie_descriptions_by_language",
    "Nombre de descriptions par langue",
    labelnames=("language",),
)

_g_descriptions_by_quality = Gauge(
    "gsie_descriptions_by_quality",
    "Nombre de descriptions par niveau de qualité",
    labelnames=("quality",),
)

_g_images_validated = Gauge(
    "gsie_images_validated_total",
    "Images avec URL validée (validated_at non null)",
)

_g_images_unvalidated = Gauge(
    "gsie_images_unvalidated_total",
    "Images sans validation d'URL (validated_at null)",
)

_g_ingestion_progress = Gauge(
    "gsie_ingestion_progress_offset",
    "Dernier offset traité par pipeline d'ingestion",
    labelnames=("pipeline", "status"),
)

_info_db = Info(
    "gsie_db",
    "Informations sur la base GSIE",
)


def _publier_series(
    gauge: Gauge,
    nom_metrique: str,
    nom_du_label: str,
    lignes: Sequence[Any],
    *,
    defaut: str = "unknown",
) -> None:
    """Publie des séries étiquetées, plafonnées et sans reliquat.

    `gauge.clear()` d'abord : sans lui, une valeur d'étiquette disparue de la
    base garde indéfiniment sa dernière valeur. Un namespace supprimé
    continuerait d'être compté, et la métrique décrirait un état révolu.
    """
    gauge.clear()
    if len(lignes) > _MAX_SERIES_PAR_METRIQUE:
        logger.warning(
            "cardinalite_metrique_plafonnee",
            metrique=nom_metrique,
            label=nom_du_label,
            observees=len(lignes),
            publiees=_MAX_SERIES_PAR_METRIQUE,
        )
        lignes = lignes[:_MAX_SERIES_PAR_METRIQUE]
    for valeur_du_label, compte in lignes:
        gauge.labels(**{nom_du_label: valeur_du_label or defaut}).set(compte)


async def _collect_metrics() -> None:
    """Calcule et publie toutes les métriques de qualité DB."""
    async with async_session_factory() as session:
        # Entities total
        n_ent = await session.scalar(
            select(func.count()).select_from(ResourceModel).where(ResourceModel.type == "entity")
        )
        _g_entities_total.set(n_ent or 0)

        # Aliases par namespace — les plus nombreux d'abord, pour que le
        # plafond de cardinalité écarte le bruit, pas le signal.
        r = await session.execute(
            select(
                EntityAliasModel.namespace,
                func.count(),
            )
            .group_by(EntityAliasModel.namespace)
            .order_by(func.count().desc())
        )
        _publier_series(_g_aliases_total, "gsie_aliases_total", "namespace", list(r))

        # Complétude enrichissement (metadata_json)
        r = await session.execute(
            text(
                """
                SELECT
                    count(*) AS total,
                    count(*) FILTER (WHERE metadata_json ? 'taxonomy') AS taxonomy,
                    count(*) FILTER (WHERE metadata_json ? 'primary_image') AS image_meta,
                    count(*) FILTER (WHERE metadata_json ? 'wikipedia_extract') AS desc_meta,
                    count(*) FILTER (WHERE metadata_json ? 'common_names') AS common
                FROM resource
                WHERE type = 'entity'
                """
            )
        )
        # Les taux de complétude sont recalculés en entier à chaque collecte :
        # sans purge, un champ qui cesse d'être mesuré (base vidée, type
        # retiré) garderait son dernier pourcentage.
        _g_enrichment_completeness.clear()
        row = r.fetchone()
        if row is None:
            total = 0
            counts = (0, 0, 0, 0, 0)
        else:
            total = row[0] or 0
            counts = (row[0], row[1], row[2], row[3], row[4])
        if total > 0:
            _g_enrichment_completeness.labels(field="taxonomy").set(100 * counts[1] // total)
            _g_enrichment_completeness.labels(field="image_metadata").set(100 * counts[2] // total)
            _g_enrichment_completeness.labels(field="description_metadata").set(
                100 * counts[3] // total
            )
            _g_enrichment_completeness.labels(field="common_names").set(100 * counts[4] // total)

        # Complétude via tables dédiées (entity_image, entity_description)
        n_images = await session.scalar(
            select(func.count())
            .select_from(EntityImageModel)
            .where(EntityImageModel.is_primary.is_(True))
        )
        if total > 0:
            _g_enrichment_completeness.labels(field="image_table").set(
                100 * (n_images or 0) // total
            )

        n_descs = await session.scalar(select(func.count()).select_from(EntityDescriptionModel))
        if total > 0:
            _g_enrichment_completeness.labels(field="description_table").set(
                100 * (n_descs or 0) // total
            )

        # Descriptions par langue
        r = await session.execute(
            select(
                EntityDescriptionModel.language,
                func.count(),
            )
            .group_by(EntityDescriptionModel.language)
            .order_by(func.count().desc())
        )
        _publier_series(
            _g_descriptions_by_language, "gsie_descriptions_by_language", "language", list(r)
        )

        # Descriptions par qualité
        r = await session.execute(
            select(
                EntityDescriptionModel.quality,
                func.count(),
            )
            .group_by(EntityDescriptionModel.quality)
            .order_by(func.count().desc())
        )
        _publier_series(
            _g_descriptions_by_quality, "gsie_descriptions_by_quality", "quality", list(r)
        )

        # Images validées / non validées
        n_validated = await session.scalar(
            select(func.count())
            .select_from(EntityImageModel)
            .where(EntityImageModel.validated_at.is_not(None))
        )
        n_unvalidated = await session.scalar(
            select(func.count())
            .select_from(EntityImageModel)
            .where(EntityImageModel.validated_at.is_(None))
        )
        _g_images_validated.set(n_validated or 0)
        _g_images_unvalidated.set(n_unvalidated or 0)

        # Progression des pipelines — `.scalars()` rend les modèles ; itérer le
        # Result directement rend des Row, dont `pipeline` n'est pas un attribut.
        progressions = list(
            (
                await session.execute(
                    select(IngestionProgressModel).order_by(
                        IngestionProgressModel.updated_at.desc()
                    )
                )
            ).scalars()
        )
        _g_ingestion_progress.clear()
        if len(progressions) > _MAX_SERIES_PAR_METRIQUE:
            logger.warning(
                "cardinalite_metrique_plafonnee",
                metrique="gsie_ingestion_progress_offset",
                label="pipeline,status",
                observees=len(progressions),
                publiees=_MAX_SERIES_PAR_METRIQUE,
            )
            progressions = progressions[:_MAX_SERIES_PAR_METRIQUE]
        for progress in progressions:
            _g_ingestion_progress.labels(
                pipeline=progress.pipeline,
                status=progress.status,
            ).set(progress.last_offset)

        # Info DB
        _info_db.info(
            {
                "entities": str(n_ent or 0),
                "schema_version": "20260801_0027",
            }
        )


async def collect_db_metrics() -> None:
    """Calcule et publie les métriques de qualité DB.

    Coroutine, et non point d'entrée synchrone : l'appelant est un endpoint
    FastAPI, donc une boucle asyncio est déjà en cours. `asyncio.run()` y
    lève `RuntimeError` — et ouvrirait de toute façon une seconde boucle,
    à laquelle les connexions asyncpg de `async_session_factory` ne sont
    pas rattachées.

    L'échec n'est pas avalé : il est journalisé puis relayé. Des Gauges
    restées à zéro se lisent comme « base vide », pas comme « collecte
    cassée » — c'est la panne qu'un `suppress(Exception)` fabriquait.
    """
    try:
        await _collect_metrics()
    except Exception:
        logger.exception("echec_collecte_metriques_db")
        raise

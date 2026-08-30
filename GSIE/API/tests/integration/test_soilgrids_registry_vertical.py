"""Preuve du vertical SoilGrids replay sans nouvel appel fournisseur."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.data.manifest_application import ManifestAssetInput, ManifestRegistryService
from gsie_api.data.promotion import normalize_soilgrids_record
from gsie_api.data.quality import (
    QUALITY_POLICY_V1,
    QualityObservation,
    QualityReport,
    assess_quality,
)
from gsie_api.data.quality_persistence import QualityAssessmentPersistenceService
from gsie_api.data.silver_promotion import PromotionBlockedError, SilverPromotionService
from gsie_api.data.soilgrids_wcs_policy import SoilGridsWcsRequest
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.enums import QualityDimension
from gsie_api.infrastructure.models.models_ai import DataAssetModel, DatasetVersionModel
from gsie_api.infrastructure.models.observation import QualityAssessmentModel
from gsie_api.ingestion.manifest import DatasetManifest
from tests.conftest import requires_docker

pytestmark = requires_docker

_NOW = datetime(2026, 8, 25, 10, 0, tzinfo=UTC)
_CHECKSUM = "a6fd8b120b11e64612cdf3ee22854d8db28413cbe7bd480291cfb203ee24840e"
_STORAGE_URI = "s3://gsie-assets/raw/fetch/soilgrids/a584c377-ff39-4e58-967a-7304b732bb47.tif"


def _manifest() -> DatasetManifest:
    return DatasetManifest.model_validate(
        {
            "manifest_version": "1",
            "generated_at": "2026-08-25",
            "entries": [
                {
                    "slug": "soilgrids-bdod-replay",
                    "title": "SoilGrids bdod micro-extrait approuvé",
                    "description": "Replay metadata-only de l'actif autorisé par DEC-000061.",
                    "source_registry_id": "soilgrids-wcs",
                    "version": "2.0-bdod-0-5cm-mean",
                    "primary_domain": "pedology",
                    "domains": ["soil_moisture"],
                    "tags": ["soilgrids", "replay"],
                    "purpose": "reference",
                    "status": "discovered",
                    "operation": "archive_copy",
                    "distribution": {
                        "access_method": "ogc_wcs",
                        "access_url": "https://maps.isric.org/mapserv",
                        "licence": "CC-BY 4.0",
                        "format": "geotiff",
                        "offline_pack": False,
                    },
                }
            ],
        }
    )


def _quality_report(target_id: UUID) -> QualityReport:
    return assess_quality(
        target_id=target_id,
        observations=[
            QualityObservation(
                dimension=dimension,
                score=0.9,
                details={"source": "DEC-000061", "mode": "replay"},
            )
            for dimension in QualityDimension
        ],
        policy=QUALITY_POLICY_V1,
        run_id=uuid4(),
    )


async def should_replay_soilgrids_through_registry_without_promotion(
    db_session: AsyncSession,
) -> None:
    manifest = _manifest()
    asset = ManifestAssetInput(
        format="geotiff",
        size_bytes=569,
        checksum=_CHECKSUM,
        storage_uri=_STORAGE_URI,
        original_uri="https://maps.isric.org/mapserv",
        archived_at=_NOW,
    )
    applied = await ManifestRegistryService(db_session).apply(
        manifest,
        dry_run=False,
        assets={"soilgrids-bdod-replay": asset},
    )
    await db_session.commit()

    version_id = UUID(applied.items[0].resources["dataset_version"])
    version = await db_session.get(DatasetVersionModel, version_id)
    assert version is not None
    assert version.status.value == "discovered"
    assert await db_session.scalar(select(func.count()).select_from(DataAssetModel)) == 1

    report = _quality_report(version_id)
    await QualityAssessmentPersistenceService(db_session).persist(
        report,
        method="soilgrids-replay-quality-check",
        assessed_at=_NOW,
    )
    await db_session.commit()
    await QualityAssessmentPersistenceService(db_session).persist(
        report,
        method="soilgrids-replay-quality-check",
        assessed_at=_NOW,
    )
    await db_session.commit()

    quality_count = await db_session.scalar(
        select(func.count())
        .select_from(QualityAssessmentModel)
        .where(
            QualityAssessmentModel.target_id == version_id,
            QualityAssessmentModel.assessment_run_id == report.run_id,
        )
    )
    assert quality_count == len(QualityDimension)

    record = normalize_soilgrids_record(
        SoilGridsWcsRequest(
            property_code="bdod",
            depth="0-5cm",
            quantile="mean",
            bbox=(0.0, 0.0, 500.0, 500.0),
        ),
        storage_uri=_STORAGE_URI,
        checksum=_CHECKSUM,
        size_bytes=569,
    )
    with pytest.raises(PromotionBlockedError, match="SOURCE_NOT_VALIDATED"):
        await SilverPromotionService(db_session).promote_from_registry(
            version_id,
            record=record,
            operator_decision_ref="DEC-000061",
        )

    refreshed = await db_session.get(DatasetVersionModel, version_id)
    assert refreshed is not None
    assert refreshed.status.value == "discovered"
    assert await db_session.get(ResourceModel, version_id) is not None

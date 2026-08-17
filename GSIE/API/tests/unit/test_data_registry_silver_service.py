"""Tests du service transactionnel de promotion SoilGrids vers staging."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from gsie_api.data.promotion import normalize_soilgrids_record
from gsie_api.data.silver_promotion import (
    PromotionBlockedError,
    PromotionEvidence,
    SilverPromotionService,
)
from gsie_api.data.soilgrids_wcs_policy import SoilGridsWcsRequest
from gsie_api.infrastructure.models.enums import DatasetStatus, QualityDimension


def _record():
    return normalize_soilgrids_record(
        SoilGridsWcsRequest(
            property_code="bdod",
            depth="0-5cm",
            quantile="mean",
            bbox=(0.0, 0.0, 500.0, 500.0),
        ),
        storage_uri="s3://gsie-raw/raw/fetch/soilgrids/asset.tif",
        checksum="b" * 64,
        size_bytes=569,
    )


def _version() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        status=DatasetStatus.validated,
        stats={"source": "soilgrids"},
    )


def _evidence() -> PromotionEvidence:
    return PromotionEvidence(
        raw_asset_uri="s3://gsie-raw/raw/fetch/soilgrids/asset.tif",
        raw_asset_checksum="b" * 64,
        checksum_verified=True,
        rights_qualified=True,
        quality_dimensions=frozenset(dimension.value for dimension in QualityDimension),
    )


async def should_promote_validated_soilgrids_to_staging_transactionally() -> None:
    session = AsyncMock()
    version = _version()

    decision = await SilverPromotionService(session).promote(
        version,
        record=_record(),
        evidence=_evidence(),
        operator_decision_ref="DEC-000061",
    )

    assert decision.allowed is True
    assert version.status == DatasetStatus.staging
    assert version.stats["normalized_schema_version"] == "soilgrids.normalized.v0.1"
    assert version.stats["promotion"]["operator_decision_ref"] == "DEC-000061"
    session.flush.assert_awaited_once()


async def should_refuse_promotion_when_quality_dimensions_are_incomplete() -> None:
    session = AsyncMock()
    version = _version()
    evidence = _evidence()
    incomplete = PromotionEvidence(
        raw_asset_uri=evidence.raw_asset_uri,
        raw_asset_checksum=evidence.raw_asset_checksum,
        checksum_verified=True,
        rights_qualified=True,
        quality_dimensions=frozenset({QualityDimension.completeness.value}),
    )

    with pytest.raises(PromotionBlockedError, match="QUALITY_ASSESSMENT_INCOMPLETE"):
        await SilverPromotionService(session).promote(
            version,
            record=_record(),
            evidence=incomplete,
            operator_decision_ref="DEC-000061",
        )

    assert version.status == DatasetStatus.validated
    session.flush.assert_not_awaited()


async def should_refuse_promotion_when_asset_checksum_does_not_match() -> None:
    session = AsyncMock()
    version = _version()
    evidence = _evidence()
    mismatched = PromotionEvidence(
        raw_asset_uri=evidence.raw_asset_uri,
        raw_asset_checksum="c" * 64,
        checksum_verified=True,
        rights_qualified=True,
        quality_dimensions=evidence.quality_dimensions,
    )

    with pytest.raises(PromotionBlockedError, match="RAW_CHECKSUM_MISMATCH"):
        await SilverPromotionService(session).promote(
            version,
            record=_record(),
            evidence=mismatched,
            operator_decision_ref="DEC-000061",
        )
    assert version.status == DatasetStatus.validated


async def should_load_registry_evidence_before_promoting() -> None:
    session = AsyncMock()
    version = _version()
    asset = SimpleNamespace(
        storage_uri="s3://gsie-raw/raw/fetch/soilgrids/asset.tif",
        checksum="b" * 64,
        checksum_algorithm="sha256",
    )
    rights = SimpleNamespace(
        licence="CC BY 4.0",
        usage_rights="open",
        redistribution_allowed=True,
    )
    quality_run_id = uuid4()
    quality_rows = [
        SimpleNamespace(
            target_id=version.id,
            assessment_run_id=quality_run_id,
            dimension=dimension,
            assessed_at=datetime(2026, 8, 13, tzinfo=UTC),
        )
        for dimension in QualityDimension
    ]

    class _Result:
        def __init__(self, values: list[object]) -> None:
            self.values = values

        def scalars(self):  # type: ignore[no-untyped-def]
            return self

        def one_or_none(self):  # type: ignore[no-untyped-def]
            return self.values[0] if self.values else None

        def first(self):  # type: ignore[no-untyped-def]
            return self.values[0] if self.values else None

        def all(self):  # type: ignore[no-untyped-def]
            return self.values

    session.execute.side_effect = [
        _Result([version]),
        _Result([asset]),
        _Result([rights]),
        _Result(quality_rows),
    ]
    decision = await SilverPromotionService(session).promote_from_registry(
        version.id,
        record=_record(),
        operator_decision_ref="DEC-000061",
    )

    assert decision.allowed is True
    assert version.status == DatasetStatus.staging
    session.flush.assert_awaited_once()

"""Tests de normalisation Silver et de garde de promotion du Registry."""

import pytest

from gsie_api.data.promotion import (
    PromotionRequest,
    evaluate_promotion,
    normalize_soilgrids_record,
)
from gsie_api.data.soilgrids_wcs_policy import SoilGridsWcsRequest


def _soilgrids_request() -> SoilGridsWcsRequest:
    return SoilGridsWcsRequest(
        property_code="wv003",
        depth="0-5cm",
        quantile="mean",
        bbox=(0.0, 0.0, 500.0, 500.0),
    )


def should_normalize_soilgrids_micro_extract_without_inventing_units() -> None:
    record = normalize_soilgrids_record(
        _soilgrids_request(),
        storage_uri="s3://gsie-raw/raw/fetch/soilgrids/asset.tif",
        checksum="a" * 64,
        size_bytes=569,
    )

    assert record.schema_version == "soilgrids.normalized.v0.1"
    assert record.property_code == "wv003"
    assert record.wcs_property_code == "wv0033"
    assert record.crs == "EPSG:152160"
    assert record.units is None
    assert "UNIT_PENDING_PROPERTY_QUALIFICATION" in record.quality_flags


def should_refuse_normalization_when_checksum_or_storage_is_missing() -> None:
    with pytest.raises(ValueError, match="checksum"):
        normalize_soilgrids_record(
            _soilgrids_request(),
            storage_uri="s3://gsie-raw/raw/fetch/soilgrids/asset.tif",
            checksum="bad",
            size_bytes=569,
        )
    with pytest.raises(ValueError, match="storage_uri"):
        normalize_soilgrids_record(
            _soilgrids_request(),
            storage_uri="https://example.invalid/asset.tif",
            checksum="a" * 64,
            size_bytes=569,
        )


def should_allow_raw_to_staging_only_with_all_prerequisites() -> None:
    decision = evaluate_promotion(
        PromotionRequest(
            source_status="validated",
            target_status="staging",
            quality_assessment_complete=True,
            rights_qualified=True,
            raw_asset_present=True,
            normalized_schema_version="soilgrids.normalized.v0.1",
            checksum_verified=True,
            operator_decision_ref="DEC-000061",
        )
    )
    assert decision.allowed is True
    assert decision.target_status == "staging"


def should_refuse_production_without_explicit_quality_and_operator() -> None:
    decision = evaluate_promotion(
        PromotionRequest(
            source_status="staging",
            target_status="production",
            quality_assessment_complete=False,
            rights_qualified=True,
            raw_asset_present=True,
            normalized_schema_version="soilgrids.normalized.v0.1",
            checksum_verified=True,
            operator_decision_ref=None,
        )
    )
    assert decision.allowed is False
    assert "QUALITY_ASSESSMENT_INCOMPLETE" in decision.reasons
    assert "OPERATOR_DECISION_MISSING" in decision.reasons


def should_refuse_promotion_from_discovered_status() -> None:
    decision = evaluate_promotion(
        PromotionRequest(
            source_status="discovered",
            target_status="staging",
            quality_assessment_complete=True,
            rights_qualified=True,
            raw_asset_present=True,
            normalized_schema_version="soilgrids.normalized.v0.1",
            checksum_verified=True,
            operator_decision_ref="DEC-000061",
        )
    )
    assert decision.allowed is False
    assert "SOURCE_NOT_VALIDATED" in decision.reasons

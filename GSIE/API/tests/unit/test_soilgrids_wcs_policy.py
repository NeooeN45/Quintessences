"""Contrat fermé de qualification WCS SoilGrids."""

import pytest

from gsie_api.data.soilgrids_wcs_policy import (
    SOILGRIDS_PROPERTIES,
    SOILGRIDS_PROPERTY_TO_WCS_CODE,
    SoilGridsWcsRequest,
    SoilGridsWcsValidationError,
)


def test_builds_canonical_parameters_for_an_allowlisted_coverage() -> None:
    request = SoilGridsWcsRequest(
        property_code="phh2o",
        depth="0-5cm",
        quantile="mean",
        bbox=(-1000.0, 6_000_000.0, 24_000.0, 6_025_000.0),
    )

    assert request.coverage_id == "phh2o_0-5cm_mean"
    assert request.estimated_pixels == 10_000
    assert request.parameters["SERVICE"] == "WCS"
    assert request.parameters["FORMAT"] == "GEOTIFF_INT16"
    assert request.parameters["SUBSET"] == ("X(-1000.0,24000.0)", "Y(6000000.0,6025000.0)")


def test_wv003_maps_to_wv0033_for_wcs_access() -> None:
    request = SoilGridsWcsRequest(
        property_code="wv003",
        depth="0-5cm",
        quantile="mean",
        bbox=(0.0, 0.0, 25_000.0, 25_000.0),
    )

    assert request.property_code == "wv003"
    assert request.wcs_property_code == "wv0033"
    assert request.coverage_id == "wv0033_0-5cm_mean"
    assert request.parameters["map"] == "/map/wv0033.map"


def test_all_other_properties_keep_an_identity_wcs_mapping() -> None:
    assert frozenset(SOILGRIDS_PROPERTY_TO_WCS_CODE) == SOILGRIDS_PROPERTIES
    assert all(
        business_code == wcs_code
        for business_code, wcs_code in SOILGRIDS_PROPERTY_TO_WCS_CODE.items()
        if business_code != "wv003"
    )


def test_rejects_wv0033_as_an_independent_business_property() -> None:
    with pytest.raises(SoilGridsWcsValidationError, match="propriété.*allowlist"):
        SoilGridsWcsRequest(
            property_code="wv0033",
            depth="0-5cm",
            quantile="mean",
            bbox=(0.0, 0.0, 25_000.0, 25_000.0),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("property_code", "../../etc/passwd"),
        ("depth", "0-500cm"),
        ("quantile", "Q1.0"),
    ],
)
def test_rejects_non_allowlisted_coverage_components(field: str, value: str) -> None:
    values = {
        "property_code": "phh2o",
        "depth": "0-5cm",
        "quantile": "mean",
        "bbox": (0.0, 0.0, 25_000.0, 25_000.0),
    }
    values[field] = value

    with pytest.raises(SoilGridsWcsValidationError, match="allowlist"):
        SoilGridsWcsRequest(**values)  # type: ignore[arg-type]


def test_rejects_an_oversized_extent() -> None:
    with pytest.raises(SoilGridsWcsValidationError, match="pixels"):
        SoilGridsWcsRequest(
            property_code="clay",
            depth="5-15cm",
            quantile="Q0.5",
            bbox=(0.0, 0.0, 300_000.0, 300_000.0),
        )


def test_rejects_invalid_or_non_finite_bbox() -> None:
    with pytest.raises(SoilGridsWcsValidationError, match="emprise"):
        SoilGridsWcsRequest(
            property_code="clay",
            depth="5-15cm",
            quantile="Q0.5",
            bbox=(0.0, 0.0, float("nan"), 10.0),
        )

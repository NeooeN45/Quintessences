"""Contrats purs du Data Registry (RFC-0038, tranche Phase 2)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from gsie_api.data.contracts import (
    DOMAIN_VOCABULARY_VERSION,
    decode_cursor,
    encode_cursor,
    normalize_keywords,
    normalize_slug,
    validate_domain,
)
from gsie_api.data.lifecycle import (
    InvalidDatasetTransition,
    can_transition,
    transition_status,
)
from gsie_api.data.schemas import DataSearchQuery, normalize_dataset_tags
from gsie_api.infrastructure.models.enums import DatasetStatus, EvidenceLevel


def should_normalize_a_registry_slug() -> None:
    assert normalize_slug("  Soil-Moisture_FR  ") == "soil-moisture_fr"


@pytest.mark.parametrize("value", ["", "a b", "../local", "énergie", "a--b", "-a"])
def should_reject_an_invalid_registry_slug(value: str) -> None:
    with pytest.raises(ValueError):
        normalize_slug(value)


def should_normalize_keywords_without_duplicates() -> None:
    assert normalize_keywords([" Forêt ", "FORÊT", "sol-humide"]) == ["forêt", "sol-humide"]


def should_validate_the_versioned_domain_vocabulary() -> None:
    assert validate_domain("soil_moisture") == "soil_moisture"
    assert DOMAIN_VOCABULARY_VERSION.startswith("2026-")
    with pytest.raises(ValueError, match="Domaine"):
        validate_domain("invented_domain")


def should_round_trip_an_opaque_cursor() -> None:
    item_id = uuid4()
    created_at = datetime(2026, 8, 10, 12, 30, tzinfo=UTC)
    token = encode_cursor(created_at, item_id, filters_hash="a" * 32)
    payload = decode_cursor(token)
    assert payload.created_at == created_at
    assert payload.resource_id == item_id
    assert payload.filters_hash == "a" * 32


@pytest.mark.parametrize("token", ["", "not-base64", "W10", "e30", "eyJ2Ijo5fQ"])
def should_reject_a_malformed_cursor(token: str) -> None:
    with pytest.raises(ValueError):
        decode_cursor(token)


def should_validate_search_constraints_for_inference() -> None:
    query = DataSearchQuery(
        theme="soil_moisture",
        bbox=(-1.2, 44.1, -0.8, 44.5),
        date_start=datetime(2026, 8, 9, tzinfo=UTC),
        date_end=datetime(2026, 8, 10, tzinfo=UTC),
        minimum_evidence_level=EvidenceLevel.c,
        use="inference",
    )
    assert query.bbox_crs == "EPSG:4326"

    with pytest.raises(ValidationError, match="minimum_evidence_level"):
        DataSearchQuery(use="inference")


def should_reject_an_invalid_search_bbox_or_date_range() -> None:
    with pytest.raises(ValidationError):
        DataSearchQuery(bbox=(-181, 0, 1, 2))
    with pytest.raises(ValidationError):
        DataSearchQuery(
            date_start=datetime(2026, 8, 11, tzinfo=UTC),
            date_end=datetime(2026, 8, 10, tzinfo=UTC),
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("bbox", (0, -91, 1, 2), "latitude"),
        ("bbox", (2, 0, 1, 2), "min <= max"),
        ("date_start", datetime(2026, 8, 10), "date_start"),
        ("date_end", datetime(2026, 8, 10), "date_end"),
    ],
)
def should_reject_invalid_spatial_or_naive_temporal_search_values(
    field: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        DataSearchQuery(**{field: value})


def should_normalize_public_dataset_tags() -> None:
    assert normalize_dataset_tags([" Forêt ", "FORÊT", "sol-humide"]) == [
        "forêt",
        "sol-humide",
    ]
    assert normalize_dataset_tags(None) == []


def should_accept_the_declared_dataset_lifecycle_transitions() -> None:
    assert can_transition(DatasetStatus.discovered, DatasetStatus.link_checked)
    assert transition_status("unavailable", "link_checked") is DatasetStatus.link_checked
    assert (
        transition_status(DatasetStatus.experimental, DatasetStatus.archived)
        is DatasetStatus.archived
    )


def should_reject_an_undeclared_dataset_lifecycle_transition() -> None:
    assert not can_transition(DatasetStatus.production, DatasetStatus.discovered)
    with pytest.raises(InvalidDatasetTransition):
        transition_status(DatasetStatus.production, DatasetStatus.discovered)

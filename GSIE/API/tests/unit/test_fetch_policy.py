"""Tests de la porte de qualification FETCH."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from gsie_api.data.fetch_policy import (
    FetchQualificationError,
    FetchQualificationRegistry,
    FetchSourceQualification,
    load_fetch_qualification,
)

QUALIFICATION_PATH = Path(__file__).resolve().parents[3] / "DATASETS" / "FETCH_QUALIFICATION.json"


def test_canonical_registry_keeps_all_sources_closed() -> None:
    registry = load_fetch_qualification(QUALIFICATION_PATH)

    assert len(registry.sources) == 5
    assert all(not item.fetch_enabled for item in registry.sources)
    for item in registry.sources:
        with pytest.raises(FetchQualificationError, match="FETCH fermé"):
            registry.require_fetch_allowed(item.source_registry_id)


def test_unknown_source_is_closed() -> None:
    registry = load_fetch_qualification(QUALIFICATION_PATH)

    with pytest.raises(FetchQualificationError, match="absente"):
        registry.require_fetch_allowed("inconnue")


def test_enabling_fetch_without_technical_bounds_is_rejected() -> None:
    with pytest.raises(ValidationError, match="max_bytes"):
        FetchSourceQualification(
            source_registry_id="soilgrids-wcs",
            status="qualified",
            fetch_enabled=True,
            legal_basis="SCI-001:OPEN_COPY",
            evidence_refs=["SCI-001"],
            allowed_hosts=["maps.isric.org"],
            allowed_content_types=["application/json"],
            checksum_algorithm="sha256",
            reviewed_by="Fondateur",
            reviewed_at=datetime.now(UTC),
        )


def test_duplicate_source_decisions_are_rejected() -> None:
    decision = load_fetch_qualification(QUALIFICATION_PATH).sources[0]

    with pytest.raises(ValidationError, match="deux décisions"):
        FetchQualificationRegistry(
            schema_version="1",
            generated_at="2026-08-10",
            sources=[decision, decision],
        )

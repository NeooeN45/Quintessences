"""Tests du chargement PostgreSQL des preuves de promotion Silver."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from gsie_api.data.silver_evidence import (
    PromotionEvidenceNotFoundError,
    SilverPromotionEvidenceRepository,
)
from gsie_api.infrastructure.models.enums import QualityDimension, UsageRights


class _ScalarResult:
    def __init__(self, values: list[object]) -> None:
        self._values = values

    def scalars(self) -> _ScalarResult:
        return self

    def one_or_none(self) -> object | None:
        return self._values[0] if self._values else None

    def first(self) -> object | None:
        return self._values[0] if self._values else None

    def all(self) -> list[object]:
        return list(self._values)


def _quality_rows(version_id: object, run_id: object) -> list[object]:
    return [
        SimpleNamespace(
            target_id=version_id,
            assessment_run_id=run_id,
            dimension=dimension,
            assessed_at=datetime(2026, 8, 13, tzinfo=UTC),
        )
        for dimension in QualityDimension
    ]


def _session_for(*results: _ScalarResult) -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=list(results))
    return session


async def should_load_complete_soilgrids_evidence_from_postgres() -> None:
    version_id = uuid4()
    version = SimpleNamespace(id=version_id)
    asset = SimpleNamespace(
        storage_uri="s3://gsie-raw/raw/fetch/soilgrids/asset.tif",
        checksum="a" * 64,
        checksum_algorithm="sha256",
    )
    rights = SimpleNamespace(
        licence="CC BY 4.0",
        usage_rights=UsageRights.open,
        redistribution_allowed=True,
    )
    session = _session_for(
        _ScalarResult([version]),
        _ScalarResult([asset]),
        _ScalarResult([rights]),
        _ScalarResult(_quality_rows(version_id, uuid4())),
    )

    snapshot = await SilverPromotionEvidenceRepository(session).load(version_id)

    assert snapshot.version is version
    assert snapshot.evidence.raw_asset_uri == asset.storage_uri
    assert snapshot.evidence.raw_asset_checksum == asset.checksum
    assert snapshot.evidence.checksum_verified is True
    assert snapshot.evidence.rights_qualified is True
    assert snapshot.evidence.quality_assessment_complete is True


async def should_keep_evidence_incomplete_when_quality_run_is_partial() -> None:
    version_id = uuid4()
    version = SimpleNamespace(id=version_id)
    asset = SimpleNamespace(
        storage_uri="s3://gsie-raw/raw/fetch/soilgrids/asset.tif",
        checksum="a" * 64,
        checksum_algorithm="sha256",
    )
    rights = SimpleNamespace(
        licence="CC BY 4.0",
        usage_rights=UsageRights.open,
        redistribution_allowed=True,
    )
    partial = _quality_rows(version_id, uuid4())[:-1]
    session = _session_for(
        _ScalarResult([version]),
        _ScalarResult([asset]),
        _ScalarResult([rights]),
        _ScalarResult(partial),
    )

    snapshot = await SilverPromotionEvidenceRepository(session).load(version_id)

    assert snapshot.evidence.quality_assessment_complete is False
    assert len(snapshot.evidence.quality_dimensions) == len(QualityDimension) - 1


async def should_fail_closed_when_dataset_version_is_missing() -> None:
    session = _session_for(_ScalarResult([]))

    with pytest.raises(PromotionEvidenceNotFoundError, match="DATASET_VERSION_NOT_FOUND"):
        await SilverPromotionEvidenceRepository(session).load(uuid4())

"""Tests du stockage append-only des évaluations de qualité du Registry."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest

from gsie_api.data.quality import (
    QUALITY_POLICY_V1,
    QualityObservation,
    QualityPolicy,
    QualityReport,
    assess_quality,
)
from gsie_api.data.quality_persistence import (
    QualityAssessmentConflictError,
    QualityAssessmentPersistenceError,
    QualityAssessmentPersistenceService,
)
from gsie_api.infrastructure.models.enums import QualityDimension

_NOW = datetime(2026, 8, 25, 10, 0, tzinfo=UTC)


class _ScalarResult:
    def __init__(self, values: list[object]) -> None:
        self._values = values

    def scalars(self) -> _ScalarResult:
        return self

    def all(self) -> list[object]:
        return list(self._values)


def _report(target_id: UUID, *, complete: bool = False) -> QualityReport:
    dimensions = list(QualityDimension) if complete else [QualityDimension.completeness]
    observations = [
        QualityObservation(
            dimension=dimension,
            score=0.9,
            details={"fixture": "soilgrids-replay"},
        )
        for dimension in dimensions
    ]
    return assess_quality(
        target_id=target_id,
        observations=observations,
        policy=QUALITY_POLICY_V1,
        run_id=uuid4(),
    )


def _session(target: object | None, existing: list[object] | None = None) -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock(return_value=target)
    session.execute = AsyncMock(return_value=_ScalarResult(existing or []))
    session.add = Mock()
    session.flush = AsyncMock()
    return session


async def should_persist_partial_quality_report_without_inventing_global_score() -> None:
    target_id = uuid4()
    target = SimpleNamespace(id=target_id, deleted_at=None)
    report = _report(target_id)
    session = _session(target)

    result = await QualityAssessmentPersistenceService(session).persist(
        report,
        method="soilgrids-replay-check",
        assessed_at=_NOW,
    )

    assert result is report
    assert report.overall_score is None
    assert report.missing_dimensions
    assert session.add.call_count == 2
    session.flush.assert_awaited()


async def should_return_existing_rows_when_quality_report_is_replayed_identically() -> None:
    target_id = uuid4()
    target = SimpleNamespace(id=target_id, deleted_at=None)
    report = _report(target_id)
    observation = report.observations[0]
    existing = SimpleNamespace(
        target_id=target_id,
        assessment_run_id=report.run_id,
        dimension=observation.dimension,
        score=observation.score,
        method="soilgrids-replay-check",
        assessed_at=_NOW,
        policy_version=report.policy_version,
        weight=QUALITY_POLICY_V1.weights[observation.dimension],
        details=dict(observation.details),
        automated=True,
    )
    session = _session(target, [existing])

    result = await QualityAssessmentPersistenceService(session).persist(
        report,
        method="soilgrids-replay-check",
        assessed_at=_NOW,
    )

    assert result is report
    session.add.assert_not_called()
    session.flush.assert_not_awaited()


async def should_refuse_quality_replay_when_existing_observation_differs() -> None:
    target_id = uuid4()
    target = SimpleNamespace(id=target_id, deleted_at=None)
    report = _report(target_id)
    observation = report.observations[0]
    existing = SimpleNamespace(
        target_id=target_id,
        assessment_run_id=report.run_id,
        dimension=observation.dimension,
        score=0.1,
        method="soilgrids-replay-check",
        assessed_at=_NOW,
        policy_version=report.policy_version,
        weight=QUALITY_POLICY_V1.weights[observation.dimension],
        details=dict(observation.details),
        automated=True,
    )
    session = _session(target, [existing])

    with pytest.raises(QualityAssessmentConflictError, match="QUALITY_ASSESSMENT_CONFLICT"):
        await QualityAssessmentPersistenceService(session).persist(
            report,
            method="soilgrids-replay-check",
            assessed_at=_NOW,
        )


async def should_refuse_quality_report_for_unknown_target() -> None:
    target_id = uuid4()
    session = _session(None)

    with pytest.raises(QualityAssessmentPersistenceError, match="QUALITY_TARGET_NOT_FOUND"):
        await QualityAssessmentPersistenceService(session).persist(
            _report(target_id),
            method="soilgrids-replay-check",
            assessed_at=_NOW,
        )


async def should_refuse_quality_report_when_policy_version_differs() -> None:
    target_id = uuid4()
    target = SimpleNamespace(id=target_id, deleted_at=None)
    alternate_policy = QualityPolicy(
        version="registry-quality-other",
        weights={dimension: 0.2 for dimension in QualityDimension},
    )
    report = assess_quality(
        target_id=target_id,
        observations=[QualityObservation(dimension=QualityDimension.completeness, score=0.9)],
        policy=alternate_policy,
        run_id=uuid4(),
    )

    with pytest.raises(QualityAssessmentPersistenceError, match="QUALITY_POLICY_MISMATCH"):
        await QualityAssessmentPersistenceService(_session(target)).persist(
            report,
            method="soilgrids-replay-check",
            assessed_at=_NOW,
        )

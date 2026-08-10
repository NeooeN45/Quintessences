"""Tests de la politique versionnée de qualité du Data Registry."""

from uuid import uuid4

import pytest

from gsie_api.data.quality import (
    QUALITY_POLICY_V1,
    QualityObservation,
    assess_quality,
)
from gsie_api.infrastructure.models.enums import QualityDimension


def test_incomplete_assessment_has_no_global_score() -> None:
    report = assess_quality(
        target_id=uuid4(),
        observations=[
            QualityObservation(QualityDimension.completeness, 1.0, {"champs": "complets"}),
            QualityObservation(QualityDimension.logical_consistency, 0.9),
        ],
    )

    assert report.complete is False
    assert report.overall_score is None
    assert set(report.missing_dimensions) == {
        QualityDimension.positional_accuracy,
        QualityDimension.temporal_accuracy,
        QualityDimension.thematic_accuracy,
    }


def test_complete_assessment_uses_versioned_weights() -> None:
    observations = [QualityObservation(dimension, 0.8) for dimension in QualityDimension]

    report = assess_quality(target_id=uuid4(), observations=observations)

    assert report.complete is True
    assert report.overall_score == pytest.approx(0.8)
    assert report.policy_version == QUALITY_POLICY_V1.version


def test_duplicate_dimension_is_rejected() -> None:
    with pytest.raises(ValueError, match="dimension dupliquée"):
        assess_quality(
            target_id=uuid4(),
            observations=[
                QualityObservation(QualityDimension.completeness, 0.8),
                QualityObservation(QualityDimension.completeness, 0.9),
            ],
        )


@pytest.mark.parametrize("score", [-0.01, 1.01, float("nan")])
def test_invalid_score_is_rejected(score: float) -> None:
    with pytest.raises(ValueError, match="score"):
        QualityObservation(QualityDimension.completeness, score)

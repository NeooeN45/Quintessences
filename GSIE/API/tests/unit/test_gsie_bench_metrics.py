"""Tests des métriques indépendantes des candidats GSIE-Bench."""

from gsie_api.benchmark.metrics import (
    classification_metrics,
    latency_percentiles,
    ranking_metrics,
    relative_degradation,
)


def should_compute_multilabel_classification_metrics() -> None:
    result = classification_metrics(("a", "b"), ("a", "c"))

    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["f1"] == 0.5
    assert result["exact_match"] == 0.0


def should_compute_ranking_metrics_at_k() -> None:
    result = ranking_metrics(("a", "b"), ("c", "a", "b"), k=2)

    assert result["recall_at_k"] == 0.5
    assert 0.0 < result["ndcg_at_k"] < 1.0


def should_compute_latency_percentiles_deterministically() -> None:
    result = latency_percentiles((1.0, 2.0, 3.0, 4.0, 5.0))

    assert result == {"p50_ms": 3.0, "p95_ms": 4.8, "p99_ms": 4.96}


def should_report_relative_degradation_without_dividing_by_zero() -> None:
    assert relative_degradation(1.0, 0.75) == 0.25
    assert relative_degradation(0.0, 0.0) == 0.0

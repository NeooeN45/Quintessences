"""Métriques déterministes et réutilisables de GSIE-Bench v0.1."""

from __future__ import annotations

from math import log2
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence


def classification_metrics(expected: Collection[str], actual: Collection[str]) -> dict[str, float]:
    """Calcule les métriques multilabel sans dépendance externe."""

    expected_set = set(expected)
    actual_set = set(actual)
    overlap = len(expected_set & actual_set)
    precision = overlap / len(actual_set) if actual_set else 1.0 if not expected_set else 0.0
    recall = overlap / len(expected_set) if expected_set else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 1.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exact_match": float(expected_set == actual_set),
    }


def ranking_metrics(
    expected: Collection[str], predicted: Sequence[str], *, k: int
) -> dict[str, float]:
    """Calcule nDCG@k et rappel@k pour une recommandation ordonnée."""

    if k <= 0:
        raise ValueError("k doit être strictement positif")
    expected_set = set(expected)
    top_k = tuple(predicted[:k])
    hits = sum(item in expected_set for item in top_k)
    recall = hits / len(expected_set) if expected_set else 1.0
    dcg = sum(1.0 / log2(index + 2) for index, item in enumerate(top_k) if item in expected_set)
    ideal_hits = min(len(expected_set), k)
    idcg = sum(1.0 / log2(index + 2) for index in range(ideal_hits))
    return {
        "recall_at_k": recall,
        "ndcg_at_k": dcg / idcg if idcg else 1.0,
    }


def latency_percentiles(durations_ms: Sequence[float]) -> dict[str, float]:
    """Calcule p50/p95/p99 par interpolation linéaire déterministe."""

    if not durations_ms:
        raise ValueError("Une série de latences ne peut pas être vide")
    if any(duration < 0 for duration in durations_ms):
        raise ValueError("Une latence négative est invalide")
    values = sorted(float(duration) for duration in durations_ms)
    return {
        "p50_ms": _percentile(values, 0.50),
        "p95_ms": _percentile(values, 0.95),
        "p99_ms": _percentile(values, 0.99),
    }


def relative_degradation(reference: float, observed: float) -> float:
    """Retourne la baisse relative, bornée et sans division par zéro."""

    if reference < 0 or observed < 0:
        raise ValueError("Les scores doivent être positifs ou nuls")
    if reference == 0:
        return 0.0 if observed == 0 else 1.0
    return max(0.0, (reference - observed) / reference)


def _percentile(values: Sequence[float], quantile: float) -> float:
    position = (len(values) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    fraction = position - lower
    return round(values[lower] + (values[upper] - values[lower]) * fraction, 10)


__all__ = [
    "classification_metrics",
    "latency_percentiles",
    "ranking_metrics",
    "relative_degradation",
]

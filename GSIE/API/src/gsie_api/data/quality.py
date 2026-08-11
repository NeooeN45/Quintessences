"""Politique explicite et versionnée de qualité technique des datasets."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from gsie_api.infrastructure.models.enums import QualityDimension

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


@dataclass(frozen=True, slots=True)
class QualityPolicy:
    """Dimensions requises et poids d'une méthode de calcul auditable."""

    version: str
    weights: Mapping[QualityDimension, float]

    def __post_init__(self) -> None:
        weights = dict(self.weights)
        if set(weights) != set(QualityDimension):
            raise ValueError("la politique doit pondérer toutes les dimensions")
        if any(not math.isfinite(value) or value <= 0 for value in weights.values()):
            raise ValueError("les poids doivent être finis et strictement positifs")
        if not math.isclose(sum(weights.values()), 1.0):
            raise ValueError("la somme des poids doit être égale à 1")
        object.__setattr__(self, "weights", MappingProxyType(weights))


QUALITY_POLICY_V1 = QualityPolicy(
    version="registry-quality-1",
    weights={dimension: 0.2 for dimension in QualityDimension},
)


@dataclass(frozen=True, slots=True)
class QualityObservation:
    """Mesure démontrée d'une dimension ; une absence n'est jamais inventée."""

    dimension: QualityDimension
    score: float
    details: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not math.isfinite(self.score) or not 0 <= self.score <= 1:
            raise ValueError("le score doit être fini et compris dans [0, 1]")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))


@dataclass(frozen=True, slots=True)
class QualityReport:
    run_id: UUID
    target_id: UUID
    policy_version: str
    observations: tuple[QualityObservation, ...]
    missing_dimensions: tuple[QualityDimension, ...]
    overall_score: float | None

    @property
    def complete(self) -> bool:
        return not self.missing_dimensions


def assess_quality(
    *,
    target_id: UUID,
    observations: Iterable[QualityObservation],
    policy: QualityPolicy = QUALITY_POLICY_V1,
    run_id: UUID | None = None,
) -> QualityReport:
    """Produit un bilan ; aucun score global n'est calculé s'il est incomplet."""

    values = tuple(observations)
    by_dimension = {item.dimension: item for item in values}
    if len(by_dimension) != len(values):
        raise ValueError("dimension dupliquée dans une même évaluation")
    missing = tuple(dimension for dimension in QualityDimension if dimension not in by_dimension)
    overall = None
    if not missing:
        overall = sum(by_dimension[d].score * policy.weights[d] for d in QualityDimension)
    return QualityReport(
        run_id=run_id or uuid4(),
        target_id=target_id,
        policy_version=policy.version,
        observations=values,
        missing_dimensions=missing,
        overall_score=overall,
    )


__all__ = [
    "QUALITY_POLICY_V1",
    "QualityObservation",
    "QualityPolicy",
    "QualityReport",
    "assess_quality",
]

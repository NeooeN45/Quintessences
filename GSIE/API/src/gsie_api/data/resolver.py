"""Data Selection Engine — sélection déterministe et explicable.

Cette première implémentation ne contacte aucun fournisseur. Elle reçoit les
projections du Registry, applique d'abord les contraintes non négociables,
puis classe les candidats admissibles avec une politique versionnée. Les
adapters et les projections STAC restent des étapes distinctes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from gsie_api.data.schemas import (
    DataSearchQuery,
    ResolutionCandidate,
    ResolutionResponse,
    SearchCandidate,
)
from gsie_api.infrastructure.models.enums import DatasetStatus, EvidenceLevel

if TYPE_CHECKING:
    from uuid import UUID

RESOLVER_POLICY_VERSION = "data-resolver-1"
_EVIDENCE_RANK = {value: rank for rank, value in enumerate("ABCDEF", start=1)}
_DEFAULT_PREFERENCES = ("freshness", "quality", "offline_availability")
_PREFERENCE_WEIGHTS = {
    "freshness": 0.4,
    "quality": 0.4,
    "offline_availability": 0.2,
}


@dataclass(frozen=True, slots=True)
class ResolutionMetadata:
    """Métadonnées optionnelles provenant des tables satellites du Registry."""

    quality_score: float | None = None
    freshness_at: datetime | None = None
    offline_available: bool | None = None


def quality_score_from_stats(stats: dict[str, object] | None) -> float | None:
    """Retourne uniquement un score explicite et borné présent dans ``stats``.

    Un nombre de lignes ou un checksum ne constitue pas une qualité technique
    et ne doit donc jamais être transformé implicitement en score.
    """

    if not isinstance(stats, dict):
        return None
    raw = stats.get("quality_score")
    quality = stats.get("quality")
    if raw is None and isinstance(quality, dict):
        raw = quality.get("score")
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        return None
    score = float(raw)
    return score if 0 <= score <= 1 else None


def _evidence_rank(level: EvidenceLevel | str | None) -> int:
    value = level.value if isinstance(level, EvidenceLevel) else level
    return _EVIDENCE_RANK.get(value or "", 99)


def _freshness_score(freshness_at: datetime | None, now: datetime) -> float | None:
    if freshness_at is None:
        return None
    observed = freshness_at
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=UTC)
    age = max(0.0, (now - observed.astimezone(UTC)).total_seconds())
    # Politique v1 : une observation âgée d'un an ou plus ne contribue plus
    # au classement. La fraîcheur inconnue reste distincte d'un score nul.
    return max(0.0, 1.0 - age / timedelta(days=365).total_seconds())


def _criteria_score(
    *,
    query: DataSearchQuery,
    quality_score: float | None,
    freshness_score: float | None,
    offline_available: bool | None,
    evidence_level: EvidenceLevel | None,
) -> dict[str, float | None]:
    values: dict[str, float | None] = {
        "freshness": freshness_score,
        "quality": quality_score,
        "offline_availability": (
            (1.0 if offline_available else 0.0) if offline_available is not None else None
        ),
        "evidence": (
            max(0.0, 1.0 - (_evidence_rank(evidence_level) - 1) / 5)
            if evidence_level is not None
            else None
        ),
    }
    preferences = tuple(query.prefer) or _DEFAULT_PREFERENCES
    return {criterion: values[criterion] for criterion in preferences}


def _weighted_score(criteria: dict[str, float | None]) -> float:
    weighted_values = [
        (value, _PREFERENCE_WEIGHTS[name])
        for name, value in criteria.items()
        if name in _PREFERENCE_WEIGHTS and value is not None
    ]
    if not weighted_values:
        return 0.0
    total_weight = sum(weight for _, weight in weighted_values)
    return sum(value * weight for value, weight in weighted_values) / total_weight


def resolve_candidates(
    query: DataSearchQuery,
    candidates: list[SearchCandidate],
    *,
    metadata: dict[UUID, ResolutionMetadata] | None = None,
    trace_id: str | None = None,
    vocabulary_version: str,
    now: datetime | None = None,
) -> ResolutionResponse:
    """Évalue et classe une liste de candidats sans effet de bord."""

    metadata = metadata or {}
    clock = now or datetime.now(UTC)
    evaluations: list[ResolutionCandidate] = []
    for candidate in candidates:
        version = candidate.version
        extra = metadata.get(version.id, ResolutionMetadata())
        quality = extra.quality_score
        if quality is None:
            quality = quality_score_from_stats(version.stats)
        freshness_score = _freshness_score(extra.freshness_at, clock)
        reasons = list(dict.fromkeys(candidate.blocking_reasons))
        status = version.status
        status_value = status.value if isinstance(status, DatasetStatus) else str(status)
        if query.use == "inference" and status_value != DatasetStatus.production.value:
            reasons.append("STATUS_NOT_PRODUCTION")
        elif query.use == "display" and status_value in {
            DatasetStatus.archived.value,
            DatasetStatus.broken.value,
            DatasetStatus.unavailable.value,
        }:
            reasons.append("STATUS_NOT_AVAILABLE")
        evidence_rank = _evidence_rank(version.evidence_level)
        required_rank = _evidence_rank(query.minimum_evidence_level)
        if query.minimum_evidence_level is not None:
            if version.evidence_level is None:
                reasons.append("EVIDENCE_MISSING")
            elif evidence_rank > required_rank:
                reasons.append("EVIDENCE_INSUFFICIENT")
        if query.use == "inference" and version.evidence_level is None:
            reasons.append("EVIDENCE_MISSING")
        if query.minimum_quality_score is not None:
            if quality is None:
                reasons.append("QUALITY_MISSING")
            elif quality < query.minimum_quality_score:
                reasons.append("QUALITY_BELOW_MINIMUM")
        criteria = _criteria_score(
            query=query,
            quality_score=quality,
            freshness_score=freshness_score,
            offline_available=extra.offline_available,
            evidence_level=version.evidence_level,
        )
        is_eligible = not reasons
        evaluations.append(
            ResolutionCandidate(
                candidate=candidate,
                eligible=is_eligible,
                blocking_reasons=list(dict.fromkeys(reasons)),
                score=_weighted_score(criteria) if is_eligible else None,
                criteria=criteria,
                freshness_at=extra.freshness_at,
                offline_available=extra.offline_available,
            )
        )

    eligible_items = [item for item in evaluations if item.eligible]
    eligible_items.sort(
        key=lambda item: (
            -(item.score or 0.0),
            _evidence_rank(item.candidate.version.evidence_level),
            -(
                item.candidate.version.release_date.timestamp()
                if item.candidate.version.release_date
                else 0
            ),
            str(item.candidate.version.id),
        )
    )
    selected = eligible_items[0] if eligible_items else None
    fallback_allowed = bool(getattr(query, "fallback_allowed", False))
    fallback = eligible_items[1] if fallback_allowed and len(eligible_items) > 1 else None
    blockers = sorted({reason for item in evaluations for reason in item.blocking_reasons})
    return ResolutionResponse(
        selected=selected,
        fallback=fallback,
        candidates=evaluations,
        blocking_reasons=blockers,
        policy_version=RESOLVER_POLICY_VERSION,
        vocabulary_version=vocabulary_version,
        trace_id=trace_id,
        fallback_allowed=fallback_allowed,
    )

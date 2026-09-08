"""Persistance append-only des rapports de qualité du Data Registry."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from gsie_api.data.quality import QUALITY_POLICY_V1
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.enums import QualityDimension
from gsie_api.infrastructure.models.observation import QualityAssessmentModel

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from gsie_api.data.quality import QualityObservation, QualityPolicy, QualityReport


class QualityAssessmentPersistenceError(ValueError):
    """Le rapport ne peut pas être persisté dans le Registry."""


class QualityAssessmentConflictError(QualityAssessmentPersistenceError):
    """Un rejeu porte des valeurs différentes d'une évaluation existante."""


class QualityAssessmentPersistenceService:
    """Persiste un rapport sans mise à jour ni fusion silencieuse."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        policy: QualityPolicy = QUALITY_POLICY_V1,
    ) -> None:
        self._session = session
        self._policy = policy

    async def persist(
        self,
        report: QualityReport,
        *,
        method: str,
        assessed_at: datetime,
        automated: bool = True,
    ) -> QualityReport:
        """Ajoute les observations, ou rejoue exactement le même rapport."""
        normalized_method = method.strip()
        _validate_request(report, normalized_method, assessed_at, self._policy)
        await self._require_target(report.target_id)
        existing = await self._existing(report)
        for observation in report.observations:
            _ensure_compatible(
                existing.get(_dimension_key(observation.dimension)),
                report,
                observation,
                normalized_method,
                assessed_at,
                automated,
                self._policy,
            )
        for observation in report.observations:
            if _dimension_key(observation.dimension) not in existing:
                await self._create_row(
                    report, observation, normalized_method, assessed_at, automated
                )
        return report

    async def _require_target(self, target_id: UUID) -> None:
        target = await self._session.get(ResourceModel, target_id)
        if target is None or target.deleted_at is not None:
            raise QualityAssessmentPersistenceError("QUALITY_TARGET_NOT_FOUND")

    async def _existing(self, report: QualityReport) -> dict[str, QualityAssessmentModel]:
        result = await self._session.execute(
            select(QualityAssessmentModel).where(
                QualityAssessmentModel.target_id == report.target_id,
                QualityAssessmentModel.assessment_run_id == report.run_id,
            )
        )
        return {_dimension_key(row.dimension): row for row in result.scalars().all()}

    async def _create_row(
        self,
        report: QualityReport,
        observation: QualityObservation,
        method: str,
        assessed_at: datetime,
        automated: bool,
    ) -> None:
        assessment_id = uuid5(
            NAMESPACE_URL,
            f"gsie-quality:{report.target_id}:{report.run_id}:{observation.dimension.value}",
        )
        details = dict(observation.details)
        metadata = {
            "target_id": str(report.target_id),
            "assessment_run_id": str(report.run_id),
            "dimension": observation.dimension.value,
            "score": observation.score,
            "method": method,
            "assessed_at": assessed_at.isoformat(),
            "policy_version": report.policy_version,
            "weight": self._policy.weights[observation.dimension],
            "details": details,
            "automated": automated,
        }
        self._session.add(
            ResourceModel(
                id=assessment_id,
                type="quality_assessment",
                gsie_id=f"gsie:quality:{assessment_id}",
                metadata_json=metadata,
            )
        )
        await self._session.flush()
        self._session.add(
            QualityAssessmentModel(
                id=assessment_id,
                target_id=report.target_id,
                dimension=observation.dimension,
                score=observation.score,
                method=method,
                assessed_at=assessed_at,
                assessment_run_id=report.run_id,
                policy_version=report.policy_version,
                weight=self._policy.weights[observation.dimension],
                details=details,
                automated=automated,
            )
        )
        await self._session.flush()


def _validate_request(
    report: QualityReport,
    method: str,
    assessed_at: datetime,
    policy: QualityPolicy,
) -> None:
    if report.policy_version != policy.version:
        raise QualityAssessmentPersistenceError("QUALITY_POLICY_MISMATCH")
    if not method.strip():
        raise QualityAssessmentPersistenceError("QUALITY_METHOD_MISSING")
    if assessed_at.tzinfo is None:
        raise QualityAssessmentPersistenceError("QUALITY_ASSESSED_AT_TIMEZONE_MISSING")


def _ensure_compatible(
    existing: QualityAssessmentModel | None,
    report: QualityReport,
    observation: QualityObservation,
    method: str,
    assessed_at: datetime,
    automated: bool,
    policy: QualityPolicy,
) -> None:
    if existing is None:
        return
    expected = {
        "score": observation.score,
        "method": method,
        "assessed_at": assessed_at,
        "policy_version": report.policy_version,
        "weight": policy.weights[observation.dimension],
        "details": dict(observation.details),
        "automated": automated,
    }
    differences = [name for name, value in expected.items() if getattr(existing, name) != value]
    if differences:
        raise QualityAssessmentConflictError(
            f"QUALITY_ASSESSMENT_CONFLICT {report.target_id}/{report.run_id}/"
            f"{observation.dimension.value}: {', '.join(differences)}"
        )


def _dimension_key(value: QualityDimension | str) -> str:
    return value.value if isinstance(value, QualityDimension) else str(value)


__all__ = [
    "QualityAssessmentConflictError",
    "QualityAssessmentPersistenceError",
    "QualityAssessmentPersistenceService",
]

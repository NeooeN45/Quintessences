"""Service transactionnel dédié à la promotion contrôlée vers STAGING."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from gsie_api.infrastructure.models.enums import DatasetStatus, QualityDimension

from .promotion import (
    NormalizedSoilGridsRecord,
    PromotionDecision,
    PromotionRequest,
    evaluate_promotion,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from gsie_api.infrastructure.models.models_ai import DatasetVersionModel


class PromotionBlockedError(ValueError):
    """La promotion est refusée avant toute écriture persistante."""

    def __init__(self, reasons: tuple[str, ...]) -> None:
        self.reasons = reasons
        super().__init__(", ".join(reasons))


@dataclass(frozen=True, slots=True)
class PromotionEvidence:
    """Preuves vérifiées par le repository avant l'appel du service."""

    raw_asset_uri: str
    raw_asset_checksum: str
    checksum_verified: bool
    rights_qualified: bool
    quality_dimensions: frozenset[str]

    @property
    def raw_asset_present(self) -> bool:
        return bool(self.raw_asset_uri and self.raw_asset_checksum)

    @property
    def quality_assessment_complete(self) -> bool:
        required = {dimension.value for dimension in QualityDimension}
        return required <= self.quality_dimensions


class SilverPromotionService:
    """Écrit une promotion validated → staging après garde complète.

    Le service ne commit pas la transaction : le gestionnaire de session de
    l'API conserve la responsabilité du commit/rollback global. L'objet
    ``PromotionEvidence`` doit provenir d'une lecture PostgreSQL contrôlée.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def promote(
        self,
        version: DatasetVersionModel,
        *,
        record: NormalizedSoilGridsRecord,
        evidence: PromotionEvidence,
        operator_decision_ref: str | None,
    ) -> PromotionDecision:
        """Promet une version validée vers staging, ou refuse sans flush."""

        source_status = (
            version.status.value
            if isinstance(version.status, DatasetStatus)
            else str(version.status)
        )
        request = PromotionRequest(
            source_status=source_status,
            target_status="staging",
            quality_assessment_complete=evidence.quality_assessment_complete,
            rights_qualified=evidence.rights_qualified,
            raw_asset_present=evidence.raw_asset_present,
            normalized_schema_version=record.schema_version,
            checksum_verified=evidence.checksum_verified,
            operator_decision_ref=operator_decision_ref,
        )
        reasons = list(evaluate_promotion(request).reasons)
        if evidence.raw_asset_checksum.lower() != record.checksum.lower():
            reasons.append("RAW_CHECKSUM_MISMATCH")
        if evidence.raw_asset_uri != record.storage_uri:
            reasons.append("RAW_STORAGE_URI_MISMATCH")
        if reasons:
            raise PromotionBlockedError(tuple(dict.fromkeys(reasons)))

        stats = dict(version.stats or {})
        stats["normalized_schema_version"] = record.schema_version
        stats["normalized_record"] = dict(record.as_mapping())
        stats["promotion"] = {
            "from_status": source_status,
            "to_status": DatasetStatus.staging.value,
            "operator_decision_ref": operator_decision_ref,
            "quality_dimensions": sorted(evidence.quality_dimensions),
            "rights_qualified": evidence.rights_qualified,
            "checksum_verified": evidence.checksum_verified,
        }
        version.stats = stats
        version.status = DatasetStatus.staging
        await self._session.flush()
        return PromotionDecision(allowed=True, target_status="staging", reasons=())

    async def promote_from_registry(
        self,
        version_id: UUID,
        *,
        record: NormalizedSoilGridsRecord,
        operator_decision_ref: str | None,
    ) -> PromotionDecision:
        """Charge les preuves PostgreSQL puis exécute la promotion contrôlée."""

        from .silver_evidence import SilverPromotionEvidenceRepository

        snapshot = await SilverPromotionEvidenceRepository(self._session).load(version_id)
        return await self.promote(
            snapshot.version,
            record=record,
            evidence=snapshot.evidence,
            operator_decision_ref=operator_decision_ref,
        )


__all__ = [
    "PromotionBlockedError",
    "PromotionEvidence",
    "SilverPromotionService",
]

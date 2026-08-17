"""Lecture des preuves PostgreSQL nécessaires à une promotion Silver."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import desc, select

from gsie_api.infrastructure.models.enums import QualityDimension, UsageRights
from gsie_api.infrastructure.models.governance import DataRightsStatementModel
from gsie_api.infrastructure.models.models_ai import (
    DataAssetModel,
    DatasetVersionModel,
    DistributionModel,
)
from gsie_api.infrastructure.models.observation import QualityAssessmentModel

from .silver_promotion import PromotionEvidence

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


class PromotionEvidenceNotFoundError(ValueError):
    """Une preuve obligatoire ne peut pas être chargée depuis le Registry."""


@dataclass(frozen=True, slots=True)
class PromotionEvidenceSnapshot:
    """Version et preuves cohérentes lues dans une même session."""

    version: DatasetVersionModel
    evidence: PromotionEvidence


class SilverPromotionEvidenceRepository:
    """Assemble les preuves sans modifier l'état de la base."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load(self, version_id: UUID) -> PromotionEvidenceSnapshot:
        """Charge version, asset, droits et dernier run de qualité cohérent."""

        version = (
            (
                await self._session.execute(
                    select(DatasetVersionModel).where(DatasetVersionModel.id == version_id)
                )
            )
            .scalars()
            .one_or_none()
        )
        if version is None:
            raise PromotionEvidenceNotFoundError("DATASET_VERSION_NOT_FOUND")

        asset = (
            (
                await self._session.execute(
                    select(DataAssetModel)
                    .where(
                        DataAssetModel.dataset_version_id == version_id,
                        DataAssetModel.storage_uri.is_not(None),
                        DataAssetModel.checksum.is_not(None),
                    )
                    .order_by(desc(DataAssetModel.archived_at))
                )
            )
            .scalars()
            .first()
        )
        rights = (
            (
                await self._session.execute(
                    select(DataRightsStatementModel)
                    .join(
                        DistributionModel,
                        DistributionModel.data_rights_statement_id == DataRightsStatementModel.id,
                    )
                    .where(DistributionModel.dataset_version_id == version_id)
                )
            )
            .scalars()
            .first()
        )
        quality_rows = list(
            (
                await self._session.execute(
                    select(QualityAssessmentModel)
                    .where(QualityAssessmentModel.target_id == version_id)
                    .order_by(desc(QualityAssessmentModel.assessed_at))
                )
            )
            .scalars()
            .all()
        )

        evidence = PromotionEvidence(
            raw_asset_uri=_asset_uri(asset),
            raw_asset_checksum=_asset_checksum(asset),
            checksum_verified=_asset_checksum_verified(asset),
            rights_qualified=_rights_qualified(rights),
            quality_dimensions=_latest_quality_dimensions(quality_rows),
        )
        return PromotionEvidenceSnapshot(version=version, evidence=evidence)


def _asset_uri(asset: DataAssetModel | None) -> str:
    if asset is None or asset.storage_uri is None:
        return ""
    return asset.storage_uri


def _asset_checksum(asset: DataAssetModel | None) -> str:
    if asset is None:
        return ""
    return asset.checksum


def _asset_checksum_verified(asset: DataAssetModel | None) -> bool:
    if asset is None:
        return False
    return asset.checksum_algorithm == "sha256" and bool(_SHA256.fullmatch(asset.checksum))


def _rights_qualified(rights: DataRightsStatementModel | None) -> bool:
    if rights is None or not rights.licence or not rights.redistribution_allowed:
        return False
    usage = (
        rights.usage_rights.value
        if isinstance(rights.usage_rights, UsageRights)
        else str(rights.usage_rights)
    )
    return usage == UsageRights.open.value


def _latest_quality_dimensions(rows: Iterable[QualityAssessmentModel]) -> frozenset[str]:
    """Retourne les dimensions du dernier run, sans fusionner les campagnes."""

    grouped: dict[UUID, list[QualityAssessmentModel]] = {}
    for row in rows:
        grouped.setdefault(row.assessment_run_id, []).append(row)
    if not grouped:
        return frozenset()
    latest_rows = max(
        grouped.values(),
        key=lambda group: max(_assessed_at(row) for row in group),
    )
    return frozenset(
        row.dimension.value if isinstance(row.dimension, QualityDimension) else str(row.dimension)
        for row in latest_rows
    )


def _assessed_at(row: QualityAssessmentModel) -> datetime:
    return row.assessed_at


__all__ = [
    "PromotionEvidenceNotFoundError",
    "PromotionEvidenceSnapshot",
    "SilverPromotionEvidenceRepository",
]

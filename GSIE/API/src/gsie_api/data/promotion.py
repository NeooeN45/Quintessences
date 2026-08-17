"""Normalisation Silver et garde de promotion du Data Registry.

Cette tranche ne modifie pas PostgreSQL : elle fournit le contrat pur qui doit
être appelé par le futur service transactionnel de promotion. Ainsi, une
normalisation ne devient jamais silencieusement une version canonique.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .soilgrids_wcs_policy import SoilGridsWcsRequest

_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_MAX_SILVER_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class NormalizedSoilGridsRecord:
    """Métadonnées Silver d'un extrait WCS sans interprétation scientifique."""

    schema_version: str
    source: str
    property_code: str
    wcs_property_code: str
    coverage_id: str
    depth: str
    quantile: str
    bbox: tuple[float, float, float, float]
    crs: str
    format: str
    storage_uri: str
    checksum: str
    checksum_algorithm: str
    size_bytes: int
    units: str | None
    quality_flags: tuple[str, ...]

    def as_mapping(self) -> MappingProxyType[str, object]:
        """Retourne une représentation JSON-compatible et immuable."""

        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "source": self.source,
                "property_code": self.property_code,
                "wcs_property_code": self.wcs_property_code,
                "coverage_id": self.coverage_id,
                "depth": self.depth,
                "quantile": self.quantile,
                "bbox": self.bbox,
                "crs": self.crs,
                "format": self.format,
                "storage_uri": self.storage_uri,
                "checksum": self.checksum,
                "checksum_algorithm": self.checksum_algorithm,
                "size_bytes": self.size_bytes,
                "units": self.units,
                "quality_flags": self.quality_flags,
            }
        )


def normalize_soilgrids_record(
    request: SoilGridsWcsRequest,
    *,
    storage_uri: str,
    checksum: str,
    size_bytes: int,
) -> NormalizedSoilGridsRecord:
    """Normalise un extrait WCS après réception et checksum vérifié.

    Les unités ne sont pas déduites du nom de couverture : elles restent
    ``None`` jusqu'à qualification par propriété et profondeur. Cela évite de
    transformer un GeoTIFF technique en donnée scientifique Gold par défaut.
    """

    if not storage_uri.startswith("s3://"):
        raise ValueError("storage_uri doit pointer vers un objet s3://")
    if not _SHA256.fullmatch(checksum):
        raise ValueError("checksum doit être un SHA-256 hexadécimal")
    if size_bytes <= 0 or size_bytes > _MAX_SILVER_BYTES:
        raise ValueError("size_bytes sort des limites Silver")
    return NormalizedSoilGridsRecord(
        schema_version="soilgrids.normalized.v0.1",
        source="soilgrids-wcs",
        property_code=request.property_code,
        wcs_property_code=request.wcs_property_code,
        coverage_id=request.coverage_id,
        depth=request.depth,
        quantile=request.quantile,
        bbox=request.bbox,
        crs="EPSG:152160",
        format="GEOTIFF_INT16",
        storage_uri=storage_uri,
        checksum=checksum.lower(),
        checksum_algorithm="sha256",
        size_bytes=size_bytes,
        units=None,
        quality_flags=("UNIT_PENDING_PROPERTY_QUALIFICATION", "NOT_GOLD"),
    )


@dataclass(frozen=True, slots=True)
class PromotionRequest:
    """Préconditions explicites d'une transition vers staging/production."""

    source_status: str
    target_status: Literal["staging", "production"]
    quality_assessment_complete: bool
    rights_qualified: bool
    raw_asset_present: bool
    normalized_schema_version: str | None
    checksum_verified: bool
    operator_decision_ref: str | None


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    """Décision pure, conservée par le futur service de promotion."""

    allowed: bool
    target_status: Literal["staging", "production"]
    reasons: tuple[str, ...]


def evaluate_promotion(request: PromotionRequest) -> PromotionDecision:
    """Évalue une promotion fail-closed sans écrire dans le Registry."""

    reasons: list[str] = []
    if request.source_status not in {"validated", "staging"}:
        reasons.append("SOURCE_NOT_VALIDATED")
    if request.target_status == "staging" and request.source_status != "validated":
        reasons.append("STAGING_REQUIRES_VALIDATED_SOURCE")
    if request.target_status == "production" and request.source_status != "staging":
        reasons.append("PRODUCTION_REQUIRES_STAGING_SOURCE")
    if not request.quality_assessment_complete:
        reasons.append("QUALITY_ASSESSMENT_INCOMPLETE")
    if not request.rights_qualified:
        reasons.append("RIGHTS_NOT_QUALIFIED")
    if not request.raw_asset_present:
        reasons.append("RAW_ASSET_MISSING")
    if not request.normalized_schema_version:
        reasons.append("NORMALIZED_SCHEMA_MISSING")
    if not request.checksum_verified:
        reasons.append("CHECKSUM_NOT_VERIFIED")
    if not request.operator_decision_ref:
        reasons.append("OPERATOR_DECISION_MISSING")
    return PromotionDecision(
        allowed=not reasons,
        target_status=request.target_status,
        reasons=tuple(dict.fromkeys(reasons)),
    )


__all__ = [
    "NormalizedSoilGridsRecord",
    "PromotionDecision",
    "PromotionRequest",
    "evaluate_promotion",
    "normalize_soilgrids_record",
]

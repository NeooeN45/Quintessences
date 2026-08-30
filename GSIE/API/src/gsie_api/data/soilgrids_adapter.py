"""Adapter Data Registry pour SoilGrids via le WCS ISRIC qualifié."""

from __future__ import annotations

import math
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol

from gsie_api.data.adapters import (
    AdapterCapability,
    AdapterContext,
    AdapterDescriptor,
    AdapterFetchRequest,
    AdapterFetchResult,
    AdapterHealthReport,
    AdapterQueryRequest,
    AdapterQueryResult,
    AdapterSecurityError,
    DataSourceAdapter,
)
from gsie_api.data.soilgrids_wcs_client import SoilGridsWcsClient, SoilGridsWcsClientError
from gsie_api.data.soilgrids_wcs_policy import (
    SOILGRIDS_FETCH_MAX_BYTES,
    SOILGRIDS_WCS_ENDPOINT,
    SoilGridsWcsRequest,
)
from gsie_api.infrastructure.models.enums import DatasetHealthStatus

if TYPE_CHECKING:
    from collections.abc import Mapping


_SOILGRIDS_HOST = "maps.isric.org"


class _SoilGridsWcsClientPort(Protocol):
    async def probe(self) -> None: ...

    async def fetch_coverage(
        self, request: SoilGridsWcsRequest, *, timeout_seconds: float, max_bytes: int
    ) -> AdapterFetchResult: ...


def _required_text(parameters: Mapping[str, object], name: str) -> str:
    value = parameters.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"SoilGrids WCS exige parameters.{name}")
    return value.strip()


def _bbox(value: object) -> tuple[float, float, float, float]:
    if not isinstance(value, list | tuple) or len(value) != 4:
        raise ValueError("SoilGrids WCS bbox doit contenir quatre nombres")
    normalized: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise ValueError("SoilGrids WCS bbox doit contenir quatre nombres")
        number = float(item)
        if not math.isfinite(number):
            raise ValueError("SoilGrids WCS bbox doit contenir des nombres finis")
        normalized.append(number)
    return tuple(normalized)  # type: ignore[return-value]


def _request_from_parameters(parameters: Mapping[str, object]) -> SoilGridsWcsRequest:
    return SoilGridsWcsRequest(
        property_code=_required_text(parameters, "property_code"),
        depth=_required_text(parameters, "depth"),
        quantile=_required_text(parameters, "quantile"),
        bbox=_bbox(parameters.get("bbox")),
    )


class SoilGridsAdapter(DataSourceAdapter):
    """Adapter SoilGrids dont l'unique endpoint est le WCS ISRIC.

    La capacité FETCH est implémentée mais reste gouvernée en amont par
    ``FetchQualificationRegistry``. Tant que ``soilgrids-wcs`` est fermé dans
    ce registre, ``BoundedFetchWorker`` n'appelle jamais cette méthode.
    """

    _DESCRIPTOR = AdapterDescriptor(
        key="soilgrids",
        name="SoilGrids ISRIC WCS",
        version="2.0.0",
        capabilities=frozenset(
            {
                AdapterCapability.HEALTH,
                AdapterCapability.QUERY,
                AdapterCapability.FETCH,
                AdapterCapability.NORMALIZE,
            }
        ),
        domains=frozenset({"pedology", "soil_moisture"}),
        endpoint=SOILGRIDS_WCS_ENDPOINT,
        allowlisted_hosts=frozenset({_SOILGRIDS_HOST}),
    )

    def __init__(self, client: SoilGridsWcsClient | _SoilGridsWcsClientPort | None = None) -> None:
        self._client = client or SoilGridsWcsClient()

    @property
    def descriptor(self) -> AdapterDescriptor:
        return self._DESCRIPTOR

    async def health(self, context: AdapterContext) -> AdapterHealthReport:
        checked_at = datetime.now(UTC)
        if context.offline:
            return AdapterHealthReport(
                adapter_key=self.descriptor.key,
                status=DatasetHealthStatus.unknown,
                checked_at=checked_at,
                error_code="OFFLINE_MODE",
            )
        started = time.perf_counter()
        try:
            await self._client.probe()
        except SoilGridsWcsClientError:
            return AdapterHealthReport(
                adapter_key=self.descriptor.key,
                status=DatasetHealthStatus.unavailable,
                checked_at=checked_at,
                latency_ms=(time.perf_counter() - started) * 1000,
                error_code="SOILGRIDS_WCS_HEALTH_CHECK_FAILED",
            )
        return AdapterHealthReport(
            adapter_key=self.descriptor.key,
            status=DatasetHealthStatus.healthy,
            checked_at=checked_at,
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    async def query(
        self, request: AdapterQueryRequest, context: AdapterContext
    ) -> AdapterQueryResult:
        del context
        if request.parameters.get("operation") != "coverage":
            raise ValueError("Opération SoilGrids WCS inconnue")
        wcs_request = _request_from_parameters(request.parameters)
        item: Mapping[str, object] = {
            "source_registry_id": "soilgrids-wcs",
            "property_code": wcs_request.property_code,
            "wcs_property_code": wcs_request.wcs_property_code,
            "coverage_id": wcs_request.coverage_id,
            "depth": wcs_request.depth,
            "quantile": wcs_request.quantile,
            "bbox": wcs_request.bbox,
            "estimated_pixels": wcs_request.estimated_pixels,
            "parameters": dict(wcs_request.parameters),
        }
        return AdapterQueryResult(items=(item,), observed_at=datetime.now(UTC))

    async def fetch(
        self, request: AdapterFetchRequest, context: AdapterContext
    ) -> AdapterFetchResult:
        if context.offline:
            raise AdapterSecurityError("SOILGRIDS_WCS_OFFLINE")
        target = self.validate_target_url(request.distribution_url)
        if target != SOILGRIDS_WCS_ENDPOINT:
            raise AdapterSecurityError("SOILGRIDS_WCS_ENDPOINT_NON_CANONIQUE")
        if request.max_bytes > SOILGRIDS_FETCH_MAX_BYTES:
            raise AdapterSecurityError("SOILGRIDS_WCS_SIZE_LIMIT_EXCEEDED")
        if request.parameters.get("operation") != "coverage":
            raise ValueError("FETCH SoilGrids WCS exige operation=coverage")
        wcs_request = _request_from_parameters(request.parameters)
        if request.external_id != wcs_request.coverage_id:
            raise ValueError("external_id ne correspond pas à coverage_id")
        return await self._client.fetch_coverage(
            wcs_request,
            timeout_seconds=min(context.timeout_seconds, 30.0),
            max_bytes=min(request.max_bytes, context.max_bytes, SOILGRIDS_FETCH_MAX_BYTES),
        )

    def normalize(self, result: AdapterQueryResult) -> tuple[Mapping[str, object], ...]:
        """Retourne le plan WCS sans convertir les valeurs scientifiques."""

        return tuple(dict(item) for item in result.items)


__all__ = ["SoilGridsAdapter"]

"""Façade DataSourceAdapter pour SoilGrids (ISRIC)."""

from __future__ import annotations

import math
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol

from gsie_api.data.adapters import (
    AdapterCapability,
    AdapterContext,
    AdapterDescriptor,
    AdapterHealthReport,
    AdapterQueryRequest,
    AdapterQueryResult,
    DataSourceAdapter,
)
from gsie_api.engines.pedology.soilgrids_client import SoilGridsClientError
from gsie_api.infrastructure.models.enums import DatasetHealthStatus

if TYPE_CHECKING:
    from collections.abc import Mapping

    from gsie_api.engines.pedology.soilgrids_client import SoilGridsClient

_SOILGRIDS_ENDPOINT = "https://rest.isric.org/soilgrids/v2.0/properties/query"
_SOILGRIDS_HOST = "rest.isric.org"
_HEALTH_LATITUDE = 48.8566
_HEALTH_LONGITUDE = 2.3522


class _SoilGridsClientPort(Protocol):
    async def get_properties(
        self, latitude: float, longitude: float, properties: list[str], depth: str = "0-5cm"
    ) -> dict[str, float]: ...

    @staticmethod
    def unit_for(property_name: str) -> str: ...


def _coordinate(value: object, *, name: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"SoilGrids {name} doit être un nombre")
    normalized = float(value)
    if not math.isfinite(normalized) or not minimum <= normalized <= maximum:
        raise ValueError(f"SoilGrids {name} doit être compris entre {minimum} et {maximum}")
    return normalized


def _properties(value: object) -> list[str]:
    if not isinstance(value, list | tuple) or not value:
        raise ValueError("SoilGrids properties doit être une liste non vide")
    normalized: list[str] = []
    for property_name in value:
        if not isinstance(property_name, str) or not property_name.strip():
            raise ValueError("SoilGrids chaque propriété doit être une chaîne non vide")
        normalized.append(property_name.strip())
    return normalized


class SoilGridsAdapter(DataSourceAdapter):
    """Adapter SoilGrids qui conserve l'échelle corrigée par le client réel."""

    _DESCRIPTOR = AdapterDescriptor(
        key="soilgrids",
        name="SoilGrids ISRIC",
        version="1.0.0",
        capabilities=frozenset(
            {
                AdapterCapability.HEALTH,
                AdapterCapability.QUERY,
                AdapterCapability.NORMALIZE,
            }
        ),
        domains=frozenset({"pedology", "soil_moisture"}),
        endpoint=_SOILGRIDS_ENDPOINT,
        allowlisted_hosts=frozenset({_SOILGRIDS_HOST}),
    )

    def __init__(self, client: SoilGridsClient | _SoilGridsClientPort | None = None) -> None:
        if client is None:
            from gsie_api.engines.pedology.soilgrids_client import SoilGridsClient as _Client

            client = _Client()
        self._client = client

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
            await self._client.get_properties(
                _HEALTH_LATITUDE,
                _HEALTH_LONGITUDE,
                ["phh2o"],
            )
        except SoilGridsClientError:
            return AdapterHealthReport(
                adapter_key=self.descriptor.key,
                status=DatasetHealthStatus.unavailable,
                checked_at=checked_at,
                latency_ms=(time.perf_counter() - started) * 1000,
                error_code="SOILGRIDS_HEALTH_CHECK_FAILED",
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
        operation = request.parameters.get("operation")
        if operation != "properties":
            raise ValueError("Opération SoilGrids inconnue")
        latitude = _coordinate(
            request.parameters.get("latitude"),
            name="latitude",
            minimum=-90,
            maximum=90,
        )
        longitude = _coordinate(
            request.parameters.get("longitude"),
            name="longitude",
            minimum=-180,
            maximum=180,
        )
        properties = _properties(request.parameters.get("properties"))
        depth = request.parameters.get("depth", "0-5cm")
        if not isinstance(depth, str) or not depth.strip():
            raise ValueError("SoilGrids depth doit être une chaîne non vide")
        values = await self._client.get_properties(
            latitude,
            longitude,
            properties,
            depth.strip(),
        )
        items: tuple[Mapping[str, object], ...] = (values,) if values else ()
        return AdapterQueryResult(items=items, observed_at=datetime.now(UTC))

    def normalize(self, result: AdapterQueryResult) -> tuple[Mapping[str, object], ...]:
        """Retourne les valeurs SoilGrids après la conversion d_factor du client."""
        return tuple(dict(item) for item in result.items)


__all__ = ["SoilGridsAdapter"]

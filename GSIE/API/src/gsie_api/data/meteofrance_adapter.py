"""Façade DataSourceAdapter pour l'API Météo des forêts de Météo-France."""

from __future__ import annotations

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
from gsie_api.engines.climate.meteofrance_client import MeteoFranceClientError
from gsie_api.infrastructure.models.enums import DatasetHealthStatus

if TYPE_CHECKING:
    from collections.abc import Mapping

    from gsie_api.engines.climate.meteofrance_client import MeteoFranceClient

_METEOFRANCE_ENDPOINT = "https://public-api.meteofrance.fr/public/DPMeteoForets/v1"
_METEOFRANCE_HOST = "public-api.meteofrance.fr"


class _MeteoFranceClientPort(Protocol):
    async def get_danger_feux_departements(self) -> list[dict[str, str | None]]: ...


class MeteoFranceAdapter(DataSourceAdapter):
    """Adapter Météo-France pour le danger de feux de forêt départemental."""

    _DESCRIPTOR = AdapterDescriptor(
        key="meteofrance",
        name="Météo-France Météo des forêts",
        version="1.0.0",
        capabilities=frozenset(
            {
                AdapterCapability.HEALTH,
                AdapterCapability.QUERY,
                AdapterCapability.NORMALIZE,
            }
        ),
        domains=frozenset({"weather", "climate"}),
        endpoint=_METEOFRANCE_ENDPOINT,
        allowlisted_hosts=frozenset({_METEOFRANCE_HOST}),
    )

    def __init__(self, client: MeteoFranceClient | _MeteoFranceClientPort | None = None) -> None:
        if client is None:
            from gsie_api.engines.climate.meteofrance_client import (
                MeteoFranceClient as _Client,
            )

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
            await self._client.get_danger_feux_departements()
        except MeteoFranceClientError:
            return AdapterHealthReport(
                adapter_key=self.descriptor.key,
                status=DatasetHealthStatus.unavailable,
                checked_at=checked_at,
                latency_ms=(time.perf_counter() - started) * 1000,
                error_code="METEOFRANCE_HEALTH_CHECK_FAILED",
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
        if operation != "danger_feux_departements":
            raise ValueError("Opération Météo-France inconnue")
        rows = await self._client.get_danger_feux_departements()
        items: tuple[Mapping[str, object], ...] = tuple(dict(row) for row in rows)
        return AdapterQueryResult(items=items, observed_at=datetime.now(UTC))

    def normalize(self, result: AdapterQueryResult) -> tuple[Mapping[str, object], ...]:
        """Retourne les lignes CSV sans convertir ni compléter les niveaux."""
        return tuple(dict(item) for item in result.items)


__all__ = ["MeteoFranceAdapter"]

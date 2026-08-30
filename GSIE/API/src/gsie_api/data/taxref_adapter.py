"""Adapter Data Registry pour le référentiel TAXREF via son miroir GBIF."""

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
from gsie_api.engines.botanical.taxref_client import TaxrefClient, TaxrefClientError
from gsie_api.infrastructure.models.enums import DatasetHealthStatus

if TYPE_CHECKING:
    from collections.abc import Mapping


_TAXREF_ENDPOINT = "https://api.gbif.org/v1/species/search"
_TAXREF_HOST = "api.gbif.org"
_HEALTH_NAME = "Quercus robur"


class _TaxrefClientPort(Protocol):
    async def search(self, nom_scientifique: str) -> dict[str, object] | None: ...


class TaxrefAdapter(DataSourceAdapter):
    """Façade TAXREF qui conserve la réponse réelle du miroir GBIF."""

    _DESCRIPTOR = AdapterDescriptor(
        key="taxref",
        name="TAXREF MNHN via miroir GBIF",
        version="1.0.0",
        capabilities=frozenset(
            {
                AdapterCapability.HEALTH,
                AdapterCapability.QUERY,
                AdapterCapability.NORMALIZE,
            }
        ),
        domains=frozenset({"botany", "biodiversity"}),
        endpoint=_TAXREF_ENDPOINT,
        allowlisted_hosts=frozenset({_TAXREF_HOST}),
    )

    def __init__(self, client: TaxrefClient | _TaxrefClientPort | None = None) -> None:
        self._client = client or TaxrefClient()

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
            await self._client.search(_HEALTH_NAME)
        except TaxrefClientError:
            return AdapterHealthReport(
                adapter_key=self.descriptor.key,
                status=DatasetHealthStatus.unavailable,
                checked_at=checked_at,
                latency_ms=(time.perf_counter() - started) * 1000,
                error_code="TAXREF_HEALTH_CHECK_FAILED",
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
        if request.parameters.get("operation") != "search":
            raise ValueError("Opération TAXREF inconnue")
        value = request.parameters.get("nom_scientifique", request.parameters.get("name"))
        if not isinstance(value, str) or not value.strip():
            raise ValueError("TAXREF search exige parameters.nom_scientifique")
        match = await self._client.search(value.strip())
        items: tuple[Mapping[str, object], ...] = (match,) if match is not None else ()
        return AdapterQueryResult(items=items, observed_at=datetime.now(UTC))

    def normalize(self, result: AdapterQueryResult) -> tuple[Mapping[str, object], ...]:
        """Ajoute uniquement l'identifiant de source à chaque résultat réel."""

        return tuple(
            {"source_registry_id": "taxref-via-gbif", **dict(item)} for item in result.items
        )


__all__ = ["TaxrefAdapter"]

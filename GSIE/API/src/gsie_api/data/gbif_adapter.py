"""Façade DataSourceAdapter pour le client GBIF existant.

La façade n'est pas enregistrée automatiquement : son activation doit être
faite par un bootstrap explicite après allowlist et configuration opérateur.
Les appels passent exclusivement par ``GBIFClient`` et donc par la résilience
HTTP/SSRF existante.
"""

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
from gsie_api.engines.botanical.gbif_client import GBIFClientError
from gsie_api.infrastructure.models.enums import DatasetHealthStatus

if TYPE_CHECKING:
    from collections.abc import Mapping

    from gsie_api.engines.botanical.gbif_client import GBIFClient

_GBIF_ENDPOINT = "https://api.gbif.org/v1"
_GBIF_HOST = "api.gbif.org"
_HEALTH_SPECIES = "Quercus robur"


class _GBIFClientPort(Protocol):
    async def match_species(self, name: str) -> dict[str, object] | None: ...

    async def get_vernacular_name(self, taxon_key: int, language: str = "fra") -> str | None: ...


class GBIFAdapter(DataSourceAdapter):
    """Adapter taxonomique GBIF, désactivé tant que le bootstrap ne l'enregistre pas."""

    _DESCRIPTOR = AdapterDescriptor(
        key="gbif",
        name="GBIF Species API",
        version="1.0.0",
        capabilities=frozenset(
            {
                AdapterCapability.HEALTH,
                AdapterCapability.QUERY,
                AdapterCapability.NORMALIZE,
            }
        ),
        domains=frozenset({"botany", "biodiversity"}),
        endpoint=_GBIF_ENDPOINT,
        allowlisted_hosts=frozenset({_GBIF_HOST}),
    )

    def __init__(self, client: GBIFClient | _GBIFClientPort | None = None) -> None:
        if client is None:
            from gsie_api.engines.botanical.gbif_client import GBIFClient as _Client

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
            await self._client.match_species(_HEALTH_SPECIES)
        except GBIFClientError:
            return AdapterHealthReport(
                adapter_key=self.descriptor.key,
                status=DatasetHealthStatus.unavailable,
                checked_at=checked_at,
                latency_ms=(time.perf_counter() - started) * 1000,
                error_code="GBIF_HEALTH_CHECK_FAILED",
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
        if operation == "species_match":
            name = request.parameters.get("name")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("GBIF species_match exige parameters.name")
            match = await self._client.match_species(name.strip())
            items: tuple[Mapping[str, object], ...] = (match,) if match is not None else ()
        elif operation == "vernacular_name":
            taxon_key = request.parameters.get("taxon_key")
            language = request.parameters.get("language", "fra")
            if not isinstance(taxon_key, int) or isinstance(taxon_key, bool):
                raise ValueError("GBIF vernacular_name exige un taxon_key entier")
            if not isinstance(language, str) or not language.strip():
                raise ValueError("GBIF vernacular_name exige une langue")
            value = await self._client.get_vernacular_name(taxon_key, language.strip())
            items = ({"taxon_key": taxon_key, "language": language.strip(), "name": value},)
        else:
            raise ValueError("Opération GBIF inconnue")
        return AdapterQueryResult(items=items, observed_at=datetime.now(UTC))

    def normalize(self, result: AdapterQueryResult) -> tuple[Mapping[str, object], ...]:
        """Retourne une copie immuable des observations, sans inventer de champ."""
        return tuple(dict(item) for item in result.items)


__all__ = ["GBIFAdapter"]

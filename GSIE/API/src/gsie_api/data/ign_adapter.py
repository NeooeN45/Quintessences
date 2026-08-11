"""Façade DataSourceAdapter pour les services géographiques IGN.

La façade regroupe le cadastre et l'altimétrie derrière le contrat Data
Registry. Elle n'est pas enregistrée automatiquement : le bootstrap doit
valider l'allowlist et la configuration avant toute activation.
"""

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
from gsie_api.engines.gis.ign_client import IGNClientError
from gsie_api.infrastructure.models.enums import DatasetHealthStatus

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    from gsie_api.engines.gis.ign_client import IGNClient

_CADASTRE_ENDPOINT = "https://apicarto.ign.fr/api/cadastre/parcelle"
_CADASTRE_HOST = "apicarto.ign.fr"
_ALTIMETRIE_HOST = "data.geopf.fr"
_HEALTH_LATITUDE = 48.8566
_HEALTH_LONGITUDE = 2.3522


class _IGNClientPort(Protocol):
    async def get_parcelle(
        self, code_insee: str, section: str, numero: str
    ) -> dict[str, Any] | None: ...

    async def get_altitude(self, latitude: float, longitude: float) -> float: ...


def _coordinate(value: object, *, name: str, minimum: float, maximum: float) -> float:
    """Valide une coordonnée WGS84 avant de la transmettre au client."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"IGN {name} doit être un nombre")
    normalized = float(value)
    if not math.isfinite(normalized) or not minimum <= normalized <= maximum:
        raise ValueError(f"IGN {name} doit être compris entre {minimum} et {maximum}")
    return normalized


def _texte(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"IGN {name} doit être une chaîne non vide")
    return value.strip()


class IGNAdapter(DataSourceAdapter):
    """Adapter IGN pour les parcelles cadastrales et l'altitude RGE ALTI."""

    _DESCRIPTOR = AdapterDescriptor(
        key="ign",
        name="Géoplateforme IGN",
        version="1.0.0",
        capabilities=frozenset(
            {
                AdapterCapability.HEALTH,
                AdapterCapability.QUERY,
                AdapterCapability.NORMALIZE,
            }
        ),
        domains=frozenset({"gis", "elevation"}),
        endpoint=_CADASTRE_ENDPOINT,
        allowlisted_hosts=frozenset({_CADASTRE_HOST, _ALTIMETRIE_HOST}),
    )

    def __init__(self, client: IGNClient | _IGNClientPort | None = None) -> None:
        if client is None:
            from gsie_api.engines.gis.ign_client import IGNClient as _Client

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
            await self._client.get_altitude(_HEALTH_LATITUDE, _HEALTH_LONGITUDE)
        except IGNClientError:
            return AdapterHealthReport(
                adapter_key=self.descriptor.key,
                status=DatasetHealthStatus.unavailable,
                checked_at=checked_at,
                latency_ms=(time.perf_counter() - started) * 1000,
                error_code="IGN_HEALTH_CHECK_FAILED",
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
        if operation == "parcelle":
            code_insee = _texte(request.parameters.get("code_insee"), name="code_insee")
            section = _texte(request.parameters.get("section"), name="section")
            numero = _texte(request.parameters.get("numero"), name="numero")
            feature = await self._client.get_parcelle(code_insee, section, numero)
            items: tuple[Mapping[str, object], ...] = (feature,) if feature is not None else ()
        elif operation == "altitude":
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
            altitude = await self._client.get_altitude(latitude, longitude)
            items = (
                {
                    "latitude": latitude,
                    "longitude": longitude,
                    "altitude_m": altitude,
                },
            )
        else:
            raise ValueError("Opération IGN inconnue")
        return AdapterQueryResult(items=items, observed_at=datetime.now(UTC))

    def normalize(self, result: AdapterQueryResult) -> tuple[Mapping[str, object], ...]:
        """Retourne les observations IGN sans conversion métier implicite."""
        return tuple(dict(item) for item in result.items)


__all__ = ["IGNAdapter"]

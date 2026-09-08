"""Adapter Data Registry pour le dataset local d'indigénat Bellifa 2026."""

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
from gsie_api.engines.botanical.indigenat_loader import (
    IndigenatLoader,
    IndigenatLoaderError,
)
from gsie_api.infrastructure.models.enums import DatasetHealthStatus

if TYPE_CHECKING:
    from collections.abc import Mapping


class _IndigenatLoaderPort(Protocol):
    def find(self, cd_nom: int | None, nom_scientifique: str | None) -> dict[str, str] | None: ...


class IndigenatBellifaAdapter(DataSourceAdapter):
    """Façade locale, déterministe et sans accès réseau pour Bellifa et al."""

    _DESCRIPTOR = AdapterDescriptor(
        key="indigenat-bellifa",
        name="Indigénat Bellifa 2026",
        version="2026.1.0",
        capabilities=frozenset(
            {
                AdapterCapability.HEALTH,
                AdapterCapability.QUERY,
                AdapterCapability.NORMALIZE,
            }
        ),
        domains=frozenset({"botany", "biodiversity"}),
    )

    def __init__(self, loader: IndigenatLoader | _IndigenatLoaderPort | None = None) -> None:
        self._loader = loader or IndigenatLoader()

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
            # La recherche peut ne rien trouver ; elle force toutefois le
            # chargement et la validation de lisibilité du fichier versionné.
            self._loader.find(None, "Quercus robur")
        except IndigenatLoaderError:
            return AdapterHealthReport(
                adapter_key=self.descriptor.key,
                status=DatasetHealthStatus.unavailable,
                checked_at=checked_at,
                latency_ms=(time.perf_counter() - started) * 1000,
                error_code="INDIGENAT_HEALTH_CHECK_FAILED",
            )
        return AdapterHealthReport(
            adapter_key=self.descriptor.key,
            status=DatasetHealthStatus.healthy,
            checked_at=checked_at,
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    @staticmethod
    def _cd_nom(value: object) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("Indigénat cd_nom doit être un entier ou absent")
        return value

    async def query(
        self, request: AdapterQueryRequest, context: AdapterContext
    ) -> AdapterQueryResult:
        del context
        if request.parameters.get("operation") != "find":
            raise ValueError("Opération Indigénat Bellifa inconnue")
        cd_nom = self._cd_nom(request.parameters.get("cd_nom"))
        name = request.parameters.get("nom_scientifique")
        if name is not None and (not isinstance(name, str) or not name.strip()):
            raise ValueError("Indigénat nom_scientifique doit être une chaîne non vide")
        code_ser = request.parameters.get("code_ser")
        if not isinstance(code_ser, str) or not code_ser.strip():
            raise ValueError("Indigénat find exige parameters.code_ser")
        row = self._loader.find(cd_nom, name.strip() if isinstance(name, str) else None)
        if row is None or code_ser.strip() not in row or row.get(code_ser.strip()) is None:
            items: tuple[Mapping[str, object], ...] = ()
        else:
            items = (
                {
                    "source_registry_id": "indigenat-bellifa-2026",
                    "dataset_version": "2026",
                    "code_ser": code_ser.strip(),
                    **row,
                },
            )
        return AdapterQueryResult(items=items, observed_at=datetime.now(UTC))

    def normalize(self, result: AdapterQueryResult) -> tuple[Mapping[str, object], ...]:
        """Préserve les valeurs du TSV et sa provenance sans statut inventé."""

        return tuple(dict(item) for item in result.items)


__all__ = ["IndigenatBellifaAdapter"]

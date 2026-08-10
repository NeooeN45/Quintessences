"""Bootstrap explicite des adapters Data Registry.

Le registre est construit sans instancier de client et sans appel réseau. Les
contrôles de santé sont une opération opérateur séparée : ils retournent des
rapports de contrat et ne sont persistés que lorsqu'une distribution qualifiée
sera associée à la source.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache

from gsie_api.data.adapters import (
    AdapterContext,
    AdapterError,
    AdapterHealthReport,
    AdapterPlugin,
    AdapterPluginRegistry,
)
from gsie_api.data.gbif_adapter import GBIFAdapter
from gsie_api.data.ign_adapter import IGNAdapter
from gsie_api.data.meteofrance_adapter import MeteoFranceAdapter
from gsie_api.data.soilgrids_adapter import SoilGridsAdapter
from gsie_api.infrastructure.models.enums import DatasetHealthStatus


def default_adapter_plugins() -> tuple[AdapterPlugin, ...]:
    """Retourne les plugins fournisseurs autorisés par le bootstrap GSIE.

    Les descripteurs sont lus sur les classes et les factories restent lazy ;
    aucune construction de client HTTP n'est effectuée à cette étape.
    """
    return (
        AdapterPlugin(GBIFAdapter._DESCRIPTOR, GBIFAdapter),  # noqa: SLF001
        AdapterPlugin(IGNAdapter._DESCRIPTOR, IGNAdapter),  # noqa: SLF001
        AdapterPlugin(MeteoFranceAdapter._DESCRIPTOR, MeteoFranceAdapter),  # noqa: SLF001
        AdapterPlugin(SoilGridsAdapter._DESCRIPTOR, SoilGridsAdapter),  # noqa: SLF001
    )


def build_adapter_registry() -> AdapterPluginRegistry:
    """Construit un registre indépendant, utile pour les tests et les jobs."""
    return AdapterPluginRegistry(default_adapter_plugins())


@lru_cache(maxsize=1)
def get_adapter_registry() -> AdapterPluginRegistry:
    """Retourne le registre process-wide du serveur.

    Le cache est volontairement limité à un objet immutable dans sa
    configuration ; les extensions doivent passer par ``build_adapter_registry``
    dans un job ou un test, jamais muter implicitement le singleton global.
    """
    return build_adapter_registry()


@dataclass(frozen=True, slots=True)
class AdapterHealthSummary:
    """Résumé déterministe d'une campagne de santé fournisseur."""

    reports: tuple[AdapterHealthReport, ...]

    @property
    def healthy(self) -> int:
        return sum(item.status is DatasetHealthStatus.healthy for item in self.reports)

    @property
    def unavailable(self) -> int:
        return sum(item.status is DatasetHealthStatus.unavailable for item in self.reports)

    @property
    def unknown(self) -> int:
        return sum(item.status is DatasetHealthStatus.unknown for item in self.reports)


class AdapterHealthService:
    """Exécute les contrôles sans les confondre avec ``DatasetHealth``.

    La concurrence est explicitement bornée et vaut un par défaut. Une
    exception inattendue est ramenée à un rapport indisponible sans exposer
    son message ou un secret.
    """

    def __init__(self, registry: AdapterPluginRegistry | None = None) -> None:
        self._registry = registry or get_adapter_registry()

    async def check_all(
        self,
        *,
        trace_id: str,
        offline: bool = False,
        timeout_seconds: float = 30.0,
        max_bytes: int = 32 * 1024 * 1024,
        max_concurrency: int = 1,
    ) -> AdapterHealthSummary:
        if not 1 <= max_concurrency <= 4:
            raise ValueError("max_concurrency doit être compris entre 1 et 4")
        context = AdapterContext(
            trace_id=trace_id,
            timeout_seconds=timeout_seconds,
            max_bytes=max_bytes,
            offline=offline,
        )
        semaphore = asyncio.Semaphore(max_concurrency)

        async def check(key: str) -> AdapterHealthReport:
            async with semaphore:
                return await self.check_one(key, context=context)

        reports = await asyncio.gather(
            *(check(descriptor.key) for descriptor in self._registry.descriptors())
        )
        return AdapterHealthSummary(reports=tuple(reports))

    async def check_one(
        self,
        key: str,
        *,
        context: AdapterContext,
    ) -> AdapterHealthReport:
        started = time.perf_counter()
        checked_at = datetime.now(UTC)
        try:
            return await self._registry.get(key).health(context)
        except AdapterError:
            raise
        except Exception:
            # Le détail d'une exception de client peut contenir une URL, un
            # jeton ou une réponse fournisseur : il ne sort jamais du job.
            return AdapterHealthReport(
                adapter_key=key,
                status=DatasetHealthStatus.unavailable,
                checked_at=checked_at,
                latency_ms=(time.perf_counter() - started) * 1000,
                error_code="ADAPTER_HEALTH_CHECK_FAILED",
            )


__all__ = [
    "AdapterHealthService",
    "AdapterHealthSummary",
    "build_adapter_registry",
    "default_adapter_plugins",
    "get_adapter_registry",
]

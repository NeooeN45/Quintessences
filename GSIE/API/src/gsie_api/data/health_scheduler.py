"""Scheduler périodique et distribué des contrôles de santé fournisseurs."""

from __future__ import annotations

import asyncio
import time
import uuid
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from prometheus_client import Counter, Gauge, Histogram

from gsie_api.core.logging import get_logger
from gsie_api.data.bootstrap import AdapterHealthService
from gsie_api.data.manifest_application import ManifestHealthSnapshot, ManifestRegistryService
from gsie_api.infrastructure.database import async_session_factory
from gsie_api.infrastructure.redis_client import get_redis
from gsie_api.ingestion.manifest import load_manifest

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from redis.asyncio import Redis

    from gsie_api.core.config import Settings
    from gsie_api.data.adapters import AdapterHealthReport


logger = get_logger("gsie_api.data.health_scheduler")
_LOCK_KEY = "gsie:data-registry:health-scheduler:lock"
_RELEASE_LOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
  return redis.call('del', KEYS[1])
end
return 0
"""
_ADAPTER_TO_MANIFEST_SLUGS: dict[str, tuple[str, ...]] = {
    # Le premier slug est canonique ; le second permet seulement de continuer
    # à mesurer l'ancienne base avant sa migration transactionnelle.
    "gbif": ("gbif-species-api", "gbif-occurrences"),
    "ign": ("ign-apicarto-cadastre", "ign-apicarto"),
    "soilgrids": ("soilgrids-rest-beta", "soilgrids-properties"),
    "meteofrance": ("meteofrance-meteo-forets", "meteofrance-services"),
}


def _resolve_manifest_slug(adapter_key: str, manifest_slugs: set[str]) -> str | None:
    """Retourne le slug canonique présent, sinon le slug historique."""

    for slug in _ADAPTER_TO_MANIFEST_SLUGS.get(adapter_key, ()):
        if slug in manifest_slugs:
            return slug
    return None


HEALTH_RUNS = Counter(
    "gsie_data_registry_health_runs_total",
    "Campagnes périodiques de santé Data Registry.",
    ("outcome",),
)
HEALTH_REPORTS = Counter(
    "gsie_data_registry_health_reports_total",
    "Résultats fournisseurs persistés par le scheduler.",
    ("adapter", "status"),
)
HEALTH_RUN_DURATION = Histogram(
    "gsie_data_registry_health_run_duration_seconds",
    "Durée des campagnes périodiques de santé Data Registry.",
)
HEALTH_LAST_SUCCESS = Gauge(
    "gsie_data_registry_health_last_success_unixtime",
    "Date Unix de la dernière campagne persistée avec succès.",
)


def snapshot_from_report(report: AdapterHealthReport) -> ManifestHealthSnapshot:
    """Convertit le rapport contractuel en historique ``DatasetHealth``."""

    return ManifestHealthSnapshot(
        checked_at=report.checked_at,
        health_status=report.status,
        http_status=report.http_status,
        latency_ms=report.latency_ms,
        observed_version=report.observed_version,
        error_code=report.error_code,
    )


class DataRegistryHealthScheduler:
    """Exécute une seule campagne par intervalle sur l'ensemble des workers."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        """Démarre la boucle sans bloquer le startup FastAPI."""

        if self._task is None:
            self._task = asyncio.create_task(self._loop(), name="data-registry-health")

    async def stop(self) -> None:
        """Arrête la boucle et attend sa terminaison bornée."""

        self._stop_event.set()
        task = self._task
        self._task = None
        if task is None:
            return
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    async def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                HEALTH_RUNS.labels(outcome="failed").inc()
                logger.error("data_registry_health_run_failed", error_type=type(exc).__name__)
            with suppress(TimeoutError):
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self._settings.data_registry_health_interval_seconds,
                )

    async def run_once(self, redis_client: Redis | None = None) -> bool:
        """Tente une campagne ; retourne ``False`` si un autre worker la détient."""

        client = redis_client or await get_redis()
        owns_client = redis_client is None
        token = uuid.uuid4().hex
        acquired = await client.set(
            _LOCK_KEY,
            token,
            nx=True,
            ex=self._settings.data_registry_health_lock_ttl_seconds,
        )
        if not acquired:
            HEALTH_RUNS.labels(outcome="locked").inc()
            if owns_client:
                await client.aclose()
            return False
        started = time.perf_counter()
        try:
            await self._collect_and_persist()
            HEALTH_RUNS.labels(outcome="success").inc()
            HEALTH_LAST_SUCCESS.set_to_current_time()
            return True
        finally:
            HEALTH_RUN_DURATION.observe(time.perf_counter() - started)
            release = client.eval(_RELEASE_LOCK_SCRIPT, 1, _LOCK_KEY, token)
            await cast("Awaitable[Any]", release)
            if owns_client:
                await client.aclose()

    async def _collect_and_persist(self) -> None:
        manifest_path = Path(self._settings.data_registry_health_manifest_path)
        manifest = load_manifest(manifest_path)
        trace_id = f"scheduled-health-{uuid.uuid4().hex[:16]}"
        summary = await AdapterHealthService().check_all(
            trace_id=trace_id,
            timeout_seconds=self._settings.data_registry_health_timeout_seconds,
            max_bytes=self._settings.data_registry_health_max_bytes,
            max_concurrency=self._settings.data_registry_health_max_concurrency,
        )
        snapshots: dict[str, ManifestHealthSnapshot] = {}
        seen_adapters: set[str] = set()
        manifest_slugs = {entry.slug for entry in manifest.entries}
        for report in summary.reports:
            slug = _resolve_manifest_slug(report.adapter_key, manifest_slugs)
            if slug is None:
                raise ValueError(f"adapter sans projection manifeste : {report.adapter_key}")
            snapshots[slug] = snapshot_from_report(report)
            seen_adapters.add(report.adapter_key)
            HEALTH_REPORTS.labels(adapter=report.adapter_key, status=report.status.value).inc()
        if seen_adapters != set(_ADAPTER_TO_MANIFEST_SLUGS):
            raise ValueError("campagne de santé incomplète")
        async with async_session_factory() as session, session.begin():
            await ManifestRegistryService(session).apply(
                manifest,
                dry_run=False,
                health_reports=snapshots,
            )


__all__ = ["DataRegistryHealthScheduler", "snapshot_from_report"]

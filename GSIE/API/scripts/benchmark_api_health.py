"""Benchmark reproductible du chemin HTTP ASGI `/health`.

Ce harness mesure le coût applicatif pur, sans réseau externe ni dépendance DB/Redis.
Il ne remplace pas les futures baselines end-to-end ; il fournit un premier point
stable et peu bruité pour détecter des régressions de sérialisation/middleware.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import platform
import resource
import sys
from pathlib import Path
from time import perf_counter_ns
from typing import Any

from httpx import ASGITransport, AsyncClient

from gsie_api.app import create_app


def _percentile(sorted_values: list[float], percentile: float) -> float:
    index = round((len(sorted_values) - 1) * percentile)
    return sorted_values[index]


async def benchmark(requests: int, warmup: int) -> dict[str, Any]:
    app = create_app()
    transport = ASGITransport(app=app)
    latencies_ms: list[float] = []

    async with AsyncClient(transport=transport, base_url="http://benchmark") as client:
        for _ in range(warmup):
            response = await client.get("/health")
            if response.status_code != 200:
                raise RuntimeError(f"warm-up /health inattendu: {response.status_code}")

        started = perf_counter_ns()
        for _ in range(requests):
            request_started = perf_counter_ns()
            response = await client.get("/health")
            elapsed_ms = (perf_counter_ns() - request_started) / 1_000_000
            if response.status_code != 200:
                raise RuntimeError(f"/health inattendu: {response.status_code}")
            latencies_ms.append(elapsed_ms)
        total_seconds = (perf_counter_ns() - started) / 1_000_000_000

    ordered = sorted(latencies_ms)
    # Linux rapporte ru_maxrss en KiB.
    rss_mib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    return {
        "scenario": "api_health_asgi_in_process",
        "requests": requests,
        "warmup": warmup,
        "latency_ms": {
            "p50": round(_percentile(ordered, 0.50), 6),
            "p95": round(_percentile(ordered, 0.95), 6),
            "p99": round(_percentile(ordered, 0.99), 6),
            "min": round(ordered[0], 6),
            "max": round(ordered[-1], 6),
        },
        "throughput_requests_per_second": round(requests / total_seconds, 2),
        "total_seconds": round(total_seconds, 6),
        "rss_max_mib": round(rss_mib, 2),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/perf/results/benchmark-api-health.json"),
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    if args.requests < 10 or args.warmup < 0:
        raise SystemExit("requests doit être >= 10 et warmup >= 0")
    result = await benchmark(args.requests, args.warmup)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    asyncio.run(main())

"""Profile un endpoint HTTP avec un client réutilisé et sans proxy système."""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time

import httpx


async def run(url: str, requests: int, concurrency: int) -> dict[str, object]:
    semaphore = asyncio.Semaphore(concurrency)
    latencies: list[float] = []
    statuses: dict[int, int] = {}
    errors: list[str] = []
    limits = httpx.Limits(
        max_connections=concurrency,
        max_keepalive_connections=concurrency,
        keepalive_expiry=30.0,
    )

    async with httpx.AsyncClient(limits=limits, trust_env=False, timeout=30.0) as client:

        async def request_once() -> None:
            async with semaphore:
                started = time.perf_counter()
                try:
                    response = await client.get(url)
                    statuses[response.status_code] = statuses.get(response.status_code, 0) + 1
                except Exception as exc:  # noqa: BLE001 - preuve de charge exhaustive
                    errors.append(f"{type(exc).__name__}: {exc}")
                finally:
                    latencies.append((time.perf_counter() - started) * 1000)

        started = time.perf_counter()
        await asyncio.gather(*(request_once() for _ in range(requests)))
        duration = time.perf_counter() - started

    ordered = sorted(latencies)

    def percentile(value: float) -> float:
        index = min(int(len(ordered) * value), len(ordered) - 1)
        return round(ordered[index], 2)

    return {
        "url": url,
        "requests": requests,
        "concurrency": concurrency,
        "duration_seconds": round(duration, 3),
        "requests_per_second": round(requests / duration, 2),
        "statuses": statuses,
        "errors": errors[:10],
        "latency_ms": {
            "mean": round(statistics.mean(ordered), 2),
            "p50": percentile(0.50),
            "p95": percentile(0.95),
            "p99": percentile(0.99),
            "max": round(max(ordered), 2),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--requests", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=20)
    args = parser.parse_args()
    if args.requests <= 0 or args.concurrency <= 0:
        parser.error("requests et concurrency doivent être positifs")
    print(json.dumps(asyncio.run(run(args.url, args.requests, args.concurrency)), indent=2))


if __name__ == "__main__":
    main()

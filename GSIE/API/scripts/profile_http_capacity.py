"""Profile un endpoint HTTP avec un client réutilisé et sans proxy système."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import time
from typing import cast

import httpx


async def run(
    url: str,
    requests: int,
    concurrency: int,
    bearer_token_env: str | None = None,
    ca_file: str | None = None,
) -> dict[str, object]:
    semaphore = asyncio.Semaphore(concurrency)
    latencies: list[float] = []
    statuses: dict[int, int] = {}
    errors: list[str] = []
    backends: dict[str, int] = {}
    limits = httpx.Limits(
        max_connections=concurrency,
        max_keepalive_connections=concurrency,
        keepalive_expiry=30.0,
    )

    headers: dict[str, str] = {}
    if bearer_token_env:
        token = os.environ.get(bearer_token_env)
        if not token:
            raise ValueError(f"Variable de jeton absente : {bearer_token_env}")
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(
        limits=limits,
        trust_env=False,
        timeout=30.0,
        headers=headers,
        verify=ca_file or True,
    ) as client:

        async def request_once() -> None:
            async with semaphore:
                started = time.perf_counter()
                try:
                    response = await client.get(url)
                    statuses[response.status_code] = statuses.get(response.status_code, 0) + 1
                    backend = response.headers.get("x-gsie-backend")
                    if backend:
                        backends[backend] = backends.get(backend, 0) + 1
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
        "backends": backends,
        "error_count": len(errors),
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
    parser.add_argument(
        "--bearer-token-env",
        help="Nom de la variable contenant le jeton Bearer (jamais sa valeur)",
    )
    parser.add_argument("--ca-file", help="Autorité TLS PEM approuvée")
    parser.add_argument("--max-p95-ms", type=float)
    parser.add_argument("--max-p99-ms", type=float)
    parser.add_argument("--min-rps", type=float)
    args = parser.parse_args()
    if args.requests <= 0 or args.concurrency <= 0:
        parser.error("requests et concurrency doivent être positifs")
    result = asyncio.run(
        run(
            args.url,
            args.requests,
            args.concurrency,
            args.bearer_token_env,
            args.ca_file,
        )
    )
    print(json.dumps(result, indent=2))
    statuses = cast(dict[int, int], result["statuses"])
    latency = cast(dict[str, float], result["latency_ms"])
    error_count = cast(int, result["error_count"])
    requests_per_second = cast(float, result["requests_per_second"])
    if error_count or statuses != {200: args.requests}:
        raise SystemExit("La campagne contient des erreurs ou des statuts non 200")
    if args.max_p95_ms is not None and latency["p95"] > args.max_p95_ms:
        raise SystemExit("Le p95 dépasse le seuil")
    if args.max_p99_ms is not None and latency["p99"] > args.max_p99_ms:
        raise SystemExit("Le p99 dépasse le seuil")
    if args.min_rps is not None and requests_per_second < args.min_rps:
        raise SystemExit("Le débit est inférieur au seuil")


if __name__ == "__main__":
    main()

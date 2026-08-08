#!/usr/bin/env python3
"""Benchmark de charge concurrente — Gate 6 Performance (ROADMAP).

`scripts/validation_benchmark.py` mesure déjà la latence en séquentiel
(une requête à la fois, espacée pour respecter le rate limit) — utile
pour la latence nominale, mais silencieux sur le comportement du système
sous charge réelle : plusieurs requêtes en vol simultanément.

Trois volets, chacun teste une couche différente :

1. **Capacité HTTP brute** (`/health`, sans rate limit, sans DB) — mesure
   le débit maximal que gunicorn/uvloop/ASGI peut absorber avant
   dégradation. Isole la couche serveur des couches DB/Redis.
2. **Rate limiting sous rafale** (`/api/v1/resources`, 120/min) —
   `SECURITY_AUDIT_2026-08-07.md` avait vérifié le rate limit en
   séquentiel (11 requêtes lentes). Ici, N requêtes concurrentes en une
   seule rafale : le comportement sous rafale peut différer du
   comportement séquentiel (condition de course sur le compteur Redis).
3. **Pool de connexions DB** — bypass HTTP, ouvre directement N sessions
   SQLAlchemy concurrentes via `async_session_factory` (le même pool que
   l'API utilise). `DEC-000037` fixe la formule
   `workers × (pool_size + max_overflow) ≤ max_connections` mais elle
   n'avait jamais été vérifiée empiriquement : ce volet le fait, en
   dépassant volontairement la capacité d'un worker (pool_size +
   max_overflow) pour observer une dégradation gracieuse (file d'attente)
   plutôt qu'un crash.

Usage :
    python scripts/load_test_concurrent.py [--url http://127.0.0.1:8000]
                                           [--concurrency 50]
                                           [--requests 500]
                                           [--output load_test_resultat.json]

Prérequis : API GSIE démarrée (docker compose up), dev login activé.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from collections import Counter
from dataclasses import dataclass, field

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import httpx

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
NC = "\033[0m"


def ok(msg: str) -> None:
    print(f"{GREEN}[OK]{NC} {msg}")


def info(msg: str) -> None:
    print(f"{CYAN}[INFO]{NC} {msg}")


def warn(msg: str) -> None:
    print(f"{YELLOW}[ATTENTION]{NC} {msg}")


def fail(msg: str) -> None:
    print(f"{RED}[ÉCHEC]{NC} {msg}")


def step(msg: str) -> None:
    print(f"\n{CYAN}=== {msg} ==={NC}")


@dataclass
class RunResult:
    latences_ms: list[float] = field(default_factory=list)
    statuts: Counter = field(default_factory=Counter)
    erreurs: list[str] = field(default_factory=list)
    duree_totale_s: float = 0.0

    def stats(self) -> dict:
        if not self.latences_ms:
            return {
                "n": 0,
                "statuts": dict(self.statuts),
                "erreurs": self.erreurs[:10],
            }
        data = sorted(self.latences_ms)
        n = len(data)

        def pct(p: float) -> float:
            idx = min(int(n * p / 100), n - 1)
            return round(data[idx], 2)

        return {
            "n": n,
            "statuts": dict(self.statuts),
            "req_par_sec": round(n / self.duree_totale_s, 2) if self.duree_totale_s else 0.0,
            "latence_ms": {
                "min": round(min(data), 2),
                "max": round(max(data), 2),
                "mean": round(statistics.mean(data), 2),
                "p50": pct(50),
                "p95": pct(95),
                "p99": pct(99),
                "stdev": round(statistics.stdev(data), 2) if n > 1 else 0.0,
            },
            "erreurs_echantillon": self.erreurs[:10],
        }


def _mint_token() -> str:
    """Émet un token d'accès directement, sans passer par le login.

    Un benchmark de charge interne n'a pas à rejouer Turnstile/lockout —
    ce sont des défenses contre un tiers non authentifié, pas contre
    l'outillage d'exploitation qui a déjà accès au processus du conteneur
    (donc à `_load_private_key()`). `create_access_token` est la même
    fonction que celle utilisée par tous les flux de login réels.
    """
    from uuid import uuid4

    from gsie_api.core.auth import create_access_token

    return create_access_token(
        subject=str(uuid4()),
        claims={"roles": ["admin"], "auth_provider": "load_test", "session_version": 1},
    )


async def _one_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: dict | None,
    result: RunResult,
    sem: asyncio.Semaphore,
) -> None:
    async with sem:
        t0 = time.perf_counter()
        try:
            resp = await client.request(method, url, headers=headers, timeout=30.0)
            t1 = time.perf_counter()
            result.latences_ms.append((t1 - t0) * 1000)
            result.statuts[resp.status_code] += 1
        except Exception as exc:  # noqa: BLE001 — on catalogue toute erreur réseau
            t1 = time.perf_counter()
            result.latences_ms.append((t1 - t0) * 1000)
            result.statuts["exception"] += 1
            result.erreurs.append(f"{type(exc).__name__}: {exc}")


async def _volet_capacite_http(base_url: str, concurrency: int, n_requests: int) -> dict:
    """Volet 1 — /health, sans rate limit ni DB : capacité brute du serveur."""
    step(f"Volet 1/3 — Capacité HTTP brute (/health, {n_requests} req, concurrence {concurrency})")
    result = RunResult()
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient() as client:
        t0 = time.perf_counter()
        await asyncio.gather(
            *[
                _one_request(client, "GET", f"{base_url}/health", None, result, sem)
                for _ in range(n_requests)
            ]
        )
        result.duree_totale_s = time.perf_counter() - t0

    stats = result.stats()
    info(f"{stats['n']} requêtes en {result.duree_totale_s:.2f}s")
    info(f"Débit : {stats.get('req_par_sec', 0):.1f} req/s")
    if "latence_ms" in stats:
        lat = stats["latence_ms"]
        info(f"Latence p50={lat['p50']}ms p95={lat['p95']}ms p99={lat['p99']}ms")
    info(f"Statuts : {stats['statuts']}")
    if stats["statuts"].get(200, 0) == stats["n"]:
        ok("100% des requêtes ont réussi (200)")
    else:
        warn("Des requêtes ont échoué — voir 'erreurs_echantillon'")
    return stats


async def _volet_rate_limit_rafale(base_url: str, token: str, concurrency: int) -> dict:
    """Volet 2 — endpoint réel à 120/min, en rafale plutôt qu'en séquentiel."""
    step(f"Volet 2/3 — Rate limiting sous rafale ({concurrency} req simultanées, limite 120/min)")
    result = RunResult()
    sem = asyncio.Semaphore(concurrency)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        t0 = time.perf_counter()
        await asyncio.gather(
            *[
                _one_request(
                    client,
                    "GET",
                    f"{base_url}/api/v1/resources?size=1",
                    headers,
                    result,
                    sem,
                )
                for _ in range(concurrency)
            ]
        )
        result.duree_totale_s = time.perf_counter() - t0

    stats = result.stats()
    n_200 = stats["statuts"].get(200, 0)
    n_429 = stats["statuts"].get(429, 0)
    info(f"{concurrency} requêtes simultanées en {result.duree_totale_s:.2f}s")
    info(f"200 OK : {n_200} — 429 Too Many Requests : {n_429}")
    info(f"Tous statuts : {stats['statuts']}")
    if stats.get("erreurs_echantillon"):
        info(f"Erreurs (échantillon) : {stats['erreurs_echantillon']}")
    if n_200 <= 125 and n_200 + n_429 == concurrency:
        ok("Le rate limit tient sous rafale (pas de dépassement significatif de 120/min)")
    elif n_200 + n_429 != concurrency:
        warn("Statuts inattendus hors 200/429 — voir détail")
    else:
        fail(f"Rate limit dépassé sous rafale : {n_200} requêtes à 200 (> ~120)")
    return stats


async def _volet_pool_db(pool_size_attendu: int, overflow_attendu: int) -> dict:
    """Volet 3 — dépasse volontairement pool_size+max_overflow d'un worker.

    Bypass HTTP : ouvre directement N sessions concurrentes via le même
    `async_session_factory` que l'API. Un seul processus Python == un
    seul "worker" du point de vue du pool, donc N > pool_size+max_overflow
    doit mettre les requêtes excédentaires en file d'attente (comportement
    gracieux) plutôt que de lever une erreur de pool épuisé.
    """
    capacite = pool_size_attendu + overflow_attendu
    n_sessions = capacite + 10  # dépasse volontairement de 10
    step(
        f"Volet 3/3 — Pool DB : {n_sessions} sessions concurrentes "
        f"(capacité d'un worker : {capacite} = {pool_size_attendu} pool + "
        f"{overflow_attendu} overflow)"
    )

    from sqlalchemy import text

    from gsie_api.infrastructure.database import async_session_factory, engine

    result = RunResult()

    async def _session_query(i: int) -> None:
        t0 = time.perf_counter()
        try:
            async with async_session_factory() as session:
                await session.execute(text("SELECT pg_sleep(0.2)"))
            t1 = time.perf_counter()
            result.latences_ms.append((t1 - t0) * 1000)
            result.statuts["ok"] += 1
        except Exception as exc:  # noqa: BLE001
            t1 = time.perf_counter()
            result.latences_ms.append((t1 - t0) * 1000)
            result.statuts["erreur"] += 1
            result.erreurs.append(f"{type(exc).__name__}: {exc}")

    # Echantillonne le pool SQLAlchemy lui-même (checkedout() est
    # l'information authentique — un compteur applicatif autour de
    # `async with async_session_factory()` mesure le mauvais point : le
    # checkout de connexion est paresseux, il n'a lieu qu'à la première
    # requête exécutée dans la session, pas à l'entrée du context manager.
    pic_checkedout = 0
    stop_poll = asyncio.Event()

    async def _poll_pool() -> None:
        nonlocal pic_checkedout
        while not stop_poll.is_set():
            pic_checkedout = max(pic_checkedout, engine.pool.checkedout())
            await asyncio.sleep(0.01)

    poller = asyncio.create_task(_poll_pool())
    t0 = time.perf_counter()
    await asyncio.gather(*[_session_query(i) for i in range(n_sessions)])
    result.duree_totale_s = time.perf_counter() - t0
    stop_poll.set()
    await poller

    stats = result.stats()
    stats["sessions_concurrentes_simultanees_max"] = pic_checkedout
    stats["capacite_configuree"] = capacite
    info(f"{n_sessions} sessions demandées, capacité configurée {capacite}")
    info(f"Connexions checked-out simultanément (pic réel) : {pic_checkedout}")
    info(f"Statuts : {stats['statuts']}")
    if "latence_ms" in stats:
        lat = stats["latence_ms"]
        info(f"Latence (requête 200ms) : min={lat['min']}ms max={lat['max']}ms")
    if stats["statuts"].get("erreur", 0) == 0 and pic_checkedout <= capacite:
        ok(
            f"Dégradation gracieuse confirmée : le pic de connexions checked-out "
            f"({pic_checkedout}) ne dépasse jamais la capacité configurée ({capacite}) — "
            f"les {n_sessions - capacite} sessions excédentaires ont attendu en file, "
            f"aucune erreur de pool épuisé."
        )
    elif stats["statuts"].get("erreur", 0) > 0:
        fail(f"{stats['statuts']['erreur']} sessions en erreur — voir 'erreurs_echantillon'")
    else:
        warn(f"Pic observé ({pic_checkedout}) dépasse la capacité configurée ({capacite})")
    return stats


async def main_async(args: argparse.Namespace) -> int:
    token = _mint_token()
    ok("Token émis (bypass login/Turnstile — voir docstring _mint_token)")

    rapport: dict = {
        "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "config": {
            "url": args.url,
            "concurrency": args.concurrency,
            "requests": args.requests,
        },
    }

    rapport["volet_1_capacite_http"] = await _volet_capacite_http(
        args.url, args.concurrency, args.requests
    )
    rapport["volet_2_rate_limit_rafale"] = await _volet_rate_limit_rafale(
        args.url, token, min(args.concurrency, 150)
    )

    if not args.skip_db_pool:
        from gsie_api.core.config import get_settings

        settings = get_settings()
        rapport["volet_3_pool_db"] = await _volet_pool_db(
            settings.db_pool_size, settings.db_max_overflow
        )
    else:
        warn("Volet 3 (pool DB) ignoré (--skip-db-pool)")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    info(f"Rapport complet écrit dans {args.output}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark de charge concurrente GSIE — Gate 6")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--concurrency", type=int, default=50)
    parser.add_argument("--requests", type=int, default=500)
    parser.add_argument("--output", default="load_test_resultat.json")
    parser.add_argument(
        "--skip-db-pool",
        action="store_true",
        help="Ignore le volet 3 (nécessite d'importer gsie_api, donc l'environnement complet)",
    )
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())

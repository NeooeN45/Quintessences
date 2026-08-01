"""Vérification en lot des URLs de l'inventaire GSIE.

Outil d'audit temporaire pour GSIE-PROMPT-0026.
Lit SOURCES_DONNEES_EXHAUSTIVES.md et DATASET_CATALOG.md,
extrait les URLs, tente un accès réel et produit un rapport JSON + CSV.

Usage :
    python GSIE/TOOLS/audit_urls_sources.py

Sortie :
    GSIE/TOOLS/url_audit/url_report.json
    GSIE/TOOLS/url_audit/url_report.csv
"""

from __future__ import annotations

import asyncio
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import aiohttp

# Fichiers d'entrée
SOURCES_FILE = Path("A:/Quintessences/GSIE/DATASETS/SOURCES_DONNEES_EXHAUSTIVES.md")
CATALOG_FILE = Path("A:/Quintessences/GSIE/DATASETS/DATASET_CATALOG.md")

# Fichiers de sortie
OUT_DIR = Path("A:/Quintessences/GSIE/TOOLS/url_audit")
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_JSON = OUT_DIR / "url_report.json"
REPORT_CSV = OUT_DIR / "url_report.csv"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

URL_RE = re.compile(r"https?://[^\s\)\]\|<>\"'`]+")

# Placeholders usuels dans les exemples/templates
TEMPLATE_PATTERNS = [
    re.compile(r"\{[^}]+\}"),
    re.compile(r"\[[^\]]+\]"),
    re.compile(
        r"\b(MAP_KEY|SOURCE|AREA_COORDS|DAY_RANGE|DATE|subResource|fileName|"
        r"bbox|your_key|api_key|token|ID|id|lon|lat|start|end|"
        r"minX|minY|maxX|maxY)\b"
    ),
    re.compile(r"\.\.\."),
]


def clean_url(raw: str) -> str:
    """Nettoie une URL extraite du markdown."""
    while raw and raw[-1] in "`*>)}],.;:'\"_-— ":
        raw = raw[:-1]
    return raw.replace("`", "").strip()


def is_template(url: str) -> bool:
    return any(p.search(url) for p in TEMPLATE_PATTERNS)


def make_test_url(url: str) -> tuple[str, str]:
    """Propose une URL testable à partir d'une URL brute.

    Retourne (test_url, note). Si note != '', l'URL brute contient
    des variables ; on teste le préfixe déterministe le plus long.
    """
    if not is_template(url):
        return url, ""

    parts = urlsplit(url)
    # Si le query contient un placeholder, on tente sans query
    if any(c in parts.query for c in "{[."):
        base = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        if not is_template(base):
            return base, "TEMPLATE_QUERY"
    # Si le chemin contient un placeholder, on remonte à la dernière partie sûre
    path_parts = parts.path.split("/")
    safe_prefix: list[str] = []
    for part in path_parts:
        if is_template(part) or part == "":
            break
        safe_prefix.append(part)
    safe_path = "/".join(safe_prefix) if safe_prefix else "/"
    if safe_path in ("", "/"):
        return urlunsplit((parts.scheme, parts.netloc, "/", "", "")), "TEMPLATE_ROOT"
    test = urlunsplit((parts.scheme, parts.netloc, safe_path, "", ""))
    if not is_template(test):
        return test, "TEMPLATE_PREFIX"
    return urlunsplit((parts.scheme, parts.netloc, "/", "", "")), "TEMPLATE_ROOT"


def is_ogc_url(url: str) -> bool:
    lower = url.lower()
    return any(x in lower for x in ("wms", "wmts", "wfs", "wcs")) and "?" not in lower


def ogc_capabilities_url(url: str) -> str:
    lower = url.lower()
    if "wms" in lower:
        return url + "?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0"
    if "wmts" in lower:
        return url + "?SERVICE=WMTS&REQUEST=GetCapabilities&VERSION=1.0.0"
    if "wfs" in lower:
        return url + "?SERVICE=WFS&REQUEST=GetCapabilities&VERSION=2.0.0"
    if "wcs" in lower:
        return url + "?SERVICE=WCS&REQUEST=GetCapabilities&VERSION=2.0.1"
    return url


def find_section(lines: list[str], line_idx: int) -> str:
    """Remonte jusqu'au titre de section (#/##/###) le plus proche."""
    for i in range(line_idx, -1, -1):
        line = lines[i]
        if line.startswith("#"):
            return line.strip("# ").strip()
    return "(racine)"


def extract_urls(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    results: list[dict[str, Any]] = []
    for idx, line in enumerate(lines, start=1):
        for m in URL_RE.finditer(line):
            raw = clean_url(m.group())
            if not raw:
                continue
            test_url, note = make_test_url(raw)
            results.append({
                "file": str(path.name),
                "line": idx,
                "section": find_section(lines, idx - 1),
                "raw_url": raw,
                "test_url": test_url,
                "template_note": note,
            })
    return results


async def fetch_one(
    session: aiohttp.ClientSession,
    item: dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    url = item["test_url"]
    async with semaphore:
        record: dict[str, Any] = {
            **item,
            "status": None,
            "final_url": None,
            "content_type": None,
            "error": None,
            "elapsed_ms": None,
            "ogc_attempted": "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if is_template(url):
            record["status"] = "TEMPLATE"
            record["error"] = "URL contient des variables non substituees"
            return record

        loop = asyncio.get_event_loop()
        start = loop.time()
        for method in ("head", "get"):
            try:
                async with session.request(method, url, allow_redirects=True) as resp:
                    record["status"] = resp.status
                    record["final_url"] = str(resp.url)
                    record["content_type"] = resp.headers.get("Content-Type", "")
                    if method == "get" and resp.status < 300:
                        try:
                            await resp.text(encoding="utf-8", errors="ignore")
                        except Exception:
                            pass
                    break
            except aiohttp.ClientResponseError as e:
                record["status"] = e.status
                record["error"] = f"{e.status} {e.message}"
                continue
            except aiohttp.ClientConnectorCertificateError as e:
                # Certificat invalide : la source n'est pas authentifiable.
                # On ne peut rien conclure sur sa vitalité — on le dit.
                record["error"] = f"TLS_INVALIDE: {e.certificate_error}"
                break
            except aiohttp.ClientConnectorError as e:
                record["error"] = f"CONNECT: {e}"
            except asyncio.TimeoutError:
                record["error"] = "TIMEOUT"
            except Exception as e:
                record["error"] = f"{type(e).__name__}: {e}"

        record["elapsed_ms"] = round((loop.time() - start) * 1000)

        # Pour les URLs OGC vides de paramètres qui répondent 400/405/None,
        # on tente un GetCapabilities.
        if record["status"] in (400, 405, None) and is_ogc_url(url):
            cap_url = ogc_capabilities_url(url)
            record["ogc_attempted"] = cap_url
            try:
                async with session.get(
                    cap_url, allow_redirects=True, timeout=15
                ) as resp:
                    record["status"] = resp.status
                    record["final_url"] = str(resp.url)
                    record["content_type"] = resp.headers.get("Content-Type", "")
            except Exception as e:
                suffix = f" ; OGC_ERROR: {e}"
                record["error"] = (record["error"] or "") + suffix

        return record


def classify(record: dict[str, Any]) -> None:
    status = record["status"]
    if status == "TEMPLATE":
        record["verdict"] = "INDETERMINEE"
        record["verdict_detail"] = "URL contient des variables non substituees"
    elif status is None and str(record["error"] or "").startswith("TLS_INVALIDE"):
        record["verdict"] = "TLS_INVALIDE"
        record["verdict_detail"] = record["error"]
    elif status is None:
        record["verdict"] = "INDETERMINEE"
        record["verdict_detail"] = record["error"] or "Erreur de connexion"
    elif 200 <= status < 400:
        record["verdict"] = "VIVANTE"
        record["verdict_detail"] = f"HTTP {status}"
    elif status == 403:
        record["verdict"] = "INDETERMINEE"
        record["verdict_detail"] = "HTTP 403 (anti-bot / acces interdit)"
    elif status in (404, 410):
        record["verdict"] = "MORTE"
        record["verdict_detail"] = f"HTTP {status}"
    elif status in (500, 502, 503, 504):
        record["verdict"] = "INDETERMINEE"
        record["verdict_detail"] = f"HTTP {status} (erreur serveur temporaire)"
    else:
        record["verdict"] = "A_VERIFIER"
        record["verdict_detail"] = f"HTTP {status}"


async def main() -> None:
    print(f"[{datetime.now(timezone.utc).isoformat()}] Extraction des URLs...")
    urls = extract_urls(SOURCES_FILE) + extract_urls(CATALOG_FILE)
    print(f"[{datetime.now(timezone.utc).isoformat()}] {len(urls)} URLs extraites.")

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for u in urls:
        if u["test_url"] not in seen:
            seen.add(u["test_url"])
            unique.append(u)
    print(f"[{datetime.now(timezone.utc).isoformat()}] {len(unique)} URLs uniques a tester.")

    # La vérification TLS reste active. Elle l'était désactivée (`ssl=False`),
    # ce qui rendait le verdict de chaque URL falsifiable par quiconque tient
    # une position réseau entre l'auditeur et la source : un certificat forgé
    # suffisait à faire passer une source morte pour vivante, ou l'inverse.
    # Un certificat réellement invalide devient un verdict à part entière
    # (`TLS_INVALIDE`) plutôt qu'une acceptation silencieuse.
    connector = aiohttp.TCPConnector(limit=20, limit_per_host=5)
    timeout = aiohttp.ClientTimeout(total=20, connect=10)
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    semaphore = asyncio.Semaphore(20)

    async with aiohttp.ClientSession(
        connector=connector, timeout=timeout, headers=headers, raise_for_status=False
    ) as session:
        tasks = [fetch_one(session, u, semaphore) for u in unique]
        results: list[dict[str, Any]] = []
        for coro in asyncio.as_completed(tasks):
            r = await coro
            results.append(r)
            if len(results) % 25 == 0:
                print(f"[{datetime.now(timezone.utc).isoformat()}] "
                      f"{len(results)}/{len(unique)} testees...")

    print(f"[{datetime.now(timezone.utc).isoformat()}] {len(results)} resultats. Sauvegarde...")

    for r in results:
        classify(r)

    REPORT_JSON.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with REPORT_CSV.open("w", newline="", encoding="utf-8") as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            for r in results:
                writer.writerow(r)

    counts = {"VIVANTE": 0, "MORTE": 0, "INDETERMINEE": 0, "A_VERIFIER": 0}
    template_count = 0
    for r in results:
        if r["status"] == "TEMPLATE":
            template_count += 1
        else:
            counts[r["verdict"]] += 1

    print("\n=== BILAN ===")
    print(f"URLs uniques testees : {len(results)}")
    print(f"  TEMPLATE (non testees) : {template_count}")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"\nRapports ecrits dans :\n  {REPORT_JSON}\n  {REPORT_CSV}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(1)

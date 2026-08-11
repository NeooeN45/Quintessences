#!/usr/bin/env python3
"""Collecte les contrôles de santé réels des adapters du manifeste.

Le job n'interroge que les endpoints ``health`` des adapters enregistrés. Il
ne télécharge aucun dataset et ne modifie pas PostgreSQL. Le JSON produit est
directement consommable par ``apply_dataset_manifest.py --health-json``.

Dans un environnement TLS d'entreprise, fournir le certificat de confiance
via ``SSL_CERT_FILE``. La vérification TLS ne doit jamais être désactivée.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gsie_api.data.bootstrap import AdapterHealthService  # noqa: E402
from gsie_api.data.manifest_application import (  # noqa: E402
    ManifestHealthSnapshot,
)
from gsie_api.ingestion.manifest import load_manifest  # noqa: E402

if TYPE_CHECKING:
    from gsie_api.data.adapters import AdapterHealthReport  # noqa: E402

# Une source SCI-001 peut porter plusieurs datasets, mais les quatre entrées
# de REGISTRY_MANIFEST.json sont actuellement une projection univoque des
# adapters. Toute nouvelle source doit être ajoutée explicitement ici et dans
# le manifeste : aucune correspondance par approximation de nom n'est faite.
_ADAPTER_TO_MANIFEST_SLUG: dict[str, str] = {
    "gbif": "gbif-occurrences",
    "ign": "ign-apicarto",
    "soilgrids": "soilgrids-properties",
    "meteofrance": "meteofrance-services",
}


def _snapshot_from_report(report: AdapterHealthReport) -> dict[str, object]:
    """Convertit un rapport dataclass en snapshot Pydantic sérialisable."""

    snapshot = ManifestHealthSnapshot(
        checked_at=report.checked_at,
        health_status=report.status,
        http_status=report.http_status,
        latency_ms=report.latency_ms,
        observed_version=report.observed_version,
        error_code=report.error_code,
    )
    return snapshot.model_dump(mode="json")


async def _collect(*, trace_id: str, offline: bool, timeout_seconds: float) -> dict[str, object]:
    summary = await AdapterHealthService().check_all(
        trace_id=trace_id,
        offline=offline,
        timeout_seconds=timeout_seconds,
    )
    result: dict[str, object] = {}
    unknown_adapters: list[str] = []
    for report in summary.reports:
        slug = _ADAPTER_TO_MANIFEST_SLUG.get(report.adapter_key)
        if slug is None:
            unknown_adapters.append(report.adapter_key)
            continue
        if slug in result:
            raise ValueError(f"Deux rapports ciblent le même dataset : {slug}")
        result[slug] = _snapshot_from_report(report)
    if unknown_adapters:
        raise ValueError(
            "Adapter(s) sans projection de manifeste : " + ", ".join(sorted(unknown_adapters))
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        type=Path,
        help="manifeste dont les slugs doivent recevoir un contrôle",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="fichier JSON de sortie (sinon sortie standard)",
    )
    parser.add_argument(
        "--trace-id",
        default=f"manifest-health-{uuid.uuid4().hex[:12]}",
        help="identifiant de traçabilité transmis aux adapters",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="produire des états unknown sans appel réseau",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="timeout borné de chaque contrôle fournisseur",
    )
    args = parser.parse_args()

    try:
        manifest = load_manifest(args.manifest)
        manifest_slugs = {entry.slug for entry in manifest.entries}
        snapshots = asyncio.run(
            _collect(
                trace_id=args.trace_id,
                offline=args.offline,
                timeout_seconds=args.timeout_seconds,
            )
        )
        missing = sorted(set(_ADAPTER_TO_MANIFEST_SLUG.values()).difference(manifest_slugs))
        if missing:
            raise ValueError(
                "Le manifeste ne contient pas les slugs attendus pour les adapters : "
                + ", ".join(missing)
            )
        snapshots = {slug: value for slug, value in snapshots.items() if slug in manifest_slugs}
        if len(snapshots) != len(_ADAPTER_TO_MANIFEST_SLUG):
            missing_reports = sorted(set(_ADAPTER_TO_MANIFEST_SLUG.values()).difference(snapshots))
            raise ValueError(
                "Contrôle absent pour le(s) dataset(s) : " + ", ".join(missing_reports)
            )
        payload = json.dumps(snapshots, ensure_ascii=False, indent=2) + "\n"
        if args.output is None:
            print(payload, end="")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
            print(f"Contrôles écrits dans {args.output}")
    except (OSError, ValueError) as exc:
        print(f"COLLECTE SANTÉ IMPOSSIBLE : {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - garde opérateur réseau
        print(f"ÉCHEC TECHNIQUE : {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

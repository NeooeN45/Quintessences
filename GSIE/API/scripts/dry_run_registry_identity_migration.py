#!/usr/bin/env python3
"""Produit le dry-run non mutatif de réconciliation des identités SCI-001.

Le script ne se connecte ni à PostgreSQL, ni à MinIO, ni aux fournisseurs.
Il lit deux manifestes locaux et retourne ``UNRESOLVED`` dès que le contenu
historique ne permet pas de prouver une scission. Il ne doit jamais être
transformé en commande d'application implicite.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gsie_api.ingestion.manifest import load_manifest  # noqa: E402
from gsie_api.ingestion.source_reconciliation import (  # noqa: E402
    build_migration_dry_run,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("historical_manifest", type=Path)
    parser.add_argument("candidate_manifest", type=Path)
    parser.add_argument("--output", type=Path, help="écrit le rapport JSON sans modifier la base")
    args = parser.parse_args()

    report = build_migration_dry_run(
        load_manifest(args.historical_manifest),
        load_manifest(args.candidate_manifest),
    ).as_dict()
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

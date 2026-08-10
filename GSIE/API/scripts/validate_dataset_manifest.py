#!/usr/bin/env python3
"""Valide un manifeste de datasets sans réseau ni écriture en base."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gsie_api.ingestion.manifest import load_manifest, manifest_preview  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="chemin vers le manifeste JSON")
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="émettre l'aperçu normalisé en JSON",
    )
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
    except ValueError as exc:
        print(f"MANIFESTE INVALIDE : {exc}", file=sys.stderr)
        return 2

    preview = manifest_preview(manifest)
    if args.as_json:
        print(json.dumps(preview, ensure_ascii=False, indent=2))
    else:
        print(f"Manifeste valide (version {manifest.manifest_version})")
        print(f"Entrées : {len(preview)}")
        for item in preview:
            print(
                f"- {item['slug']}@{item['version']} — {item['operation']} — "
                f"{item['source_registry_id']} — {item['status']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

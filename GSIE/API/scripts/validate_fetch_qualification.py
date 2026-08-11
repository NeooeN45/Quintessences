#!/usr/bin/env python3
"""Valide la qualification FETCH et affiche les décisions source par source."""

from __future__ import annotations

import argparse
from pathlib import Path

from gsie_api.data.fetch_policy import load_fetch_qualification

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "DATASETS" / "FETCH_QUALIFICATION.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?", default=DEFAULT_PATH)
    args = parser.parse_args()
    registry = load_fetch_qualification(args.path)
    for decision in registry.sources:
        print(
            f"{decision.source_registry_id}: {decision.status.value} "
            f"(FETCH={'ouvert' if decision.fetch_enabled else 'fermé'})"
        )
    print(f"Verdict : {len(registry.sources)} source(s) qualifiée(s), aucun FETCH implicite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

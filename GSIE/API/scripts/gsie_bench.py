#!/usr/bin/env python3
"""Exécute une suite GSIE-Bench locale sans réseau ni promotion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from gsie_api.benchmark import (
    DeterministicRunner,
    NaiveBaseline,
    RuleBaseline,
    build_open_silver_catalog,
)
from gsie_api.benchmark.reporting import run_result_to_dict


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Runner local GSIE-Bench v0.1")
    parser.add_argument(
        "--suite",
        choices=("open-silver",),
        default="open-silver",
        help="Suite exécutable sans qualification Gold",
    )
    parser.add_argument("--candidate", choices=("rules", "naive"), default="rules")
    parser.add_argument("--output", type=Path, help="Fichier JSON de sortie optionnel")
    args = parser.parse_args(argv)

    candidate = RuleBaseline() if args.candidate == "rules" else NaiveBaseline()
    result = DeterministicRunner.open_silver().run(candidate, build_open_silver_catalog())
    document = json.dumps(run_result_to_dict(result), ensure_ascii=False, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.write_text(document + "\n", encoding="utf-8")
    else:
        print(document)
    return 0 if result.status == "GO" else 2


if __name__ == "__main__":
    raise SystemExit(main())

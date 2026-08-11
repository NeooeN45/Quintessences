#!/usr/bin/env python3
"""Vérifie la politique de couverture multicouche définie par DEC-000066."""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

GLOBAL_MINIMUM = 97.10
PUBLIC_CONTRACT_MINIMUM = 100.00
BUSINESS_MINIMUM = 80.00
INFRASTRUCTURE_MINIMUM = 60.00


def _normalize_path(value: str) -> str:
    return value.replace("\\", "/")


def _is_public_contract(path: str) -> bool:
    name = PurePosixPath(path).name
    return (
        name == "router.py"
        or name.endswith("_router.py")
        or name == "schemas.py"
        or name.endswith("_schemas.py")
    )


def _percentage(covered: int, statements: int) -> float:
    return covered / statements * 100


def _summary(payload: object) -> tuple[int, int] | None:
    if not isinstance(payload, Mapping):
        return None
    raw_summary = payload.get("summary")
    if not isinstance(raw_summary, Mapping):
        return None
    covered = raw_summary.get("covered_lines")
    statements = raw_summary.get("num_statements")
    if (
        isinstance(covered, bool)
        or isinstance(statements, bool)
        or not isinstance(covered, int)
        or not isinstance(statements, int)
    ):
        return None
    if statements < 0 or covered < 0 or covered > statements:
        return None
    return covered, statements


def evaluate_coverage_policy(report: Mapping[str, Any]) -> list[str]:
    """Retourne toutes les violations sans masquer les erreurs de rapport."""
    totals = report.get("totals")
    files = report.get("files")
    if not isinstance(totals, Mapping) or not isinstance(files, Mapping) or not files:
        return ["Rapport de couverture inexploitable : totaux ou fichiers absents."]

    raw_total = totals.get("percent_covered")
    if isinstance(raw_total, bool) or not isinstance(raw_total, int | float):
        return ["Rapport de couverture inexploitable : pourcentage global absent."]

    violations: list[str] = []
    total = float(raw_total)
    if not math.isfinite(total) or not 0 <= total <= 100:
        return ["Rapport de couverture inexploitable : pourcentage global invalide."]
    if total < GLOBAL_MINIMUM:
        violations.append(
            f"Couverture globale {total:.2f}% < seuil anti-régression {GLOBAL_MINIMUM:.2f}%."
        )

    business_covered = 0
    business_statements = 0
    infrastructure_covered = 0
    infrastructure_statements = 0
    public_contracts = 0

    for raw_path, payload in files.items():
        if not isinstance(raw_path, str):
            violations.append("Rapport de couverture inexploitable : chemin non textuel.")
            continue
        summary = _summary(payload)
        if summary is None:
            violations.append(f"Rapport de couverture inexploitable pour {raw_path}.")
            continue
        covered, statements = summary
        if statements == 0:
            continue

        path = _normalize_path(raw_path)
        if _is_public_contract(path):
            public_contracts += 1
            percent = _percentage(covered, statements)
            if covered != statements:
                violations.append(
                    f"Contrat public {path} : {percent:.2f}% < {PUBLIC_CONTRACT_MINIMUM:.2f}%."
                )
        elif "/infrastructure/" in f"/{path}":
            infrastructure_covered += covered
            infrastructure_statements += statements
        else:
            business_covered += covered
            business_statements += statements

    if public_contracts == 0:
        violations.append("Rapport de couverture inexploitable : aucun contrat public détecté.")

    if business_statements == 0:
        violations.append("Rapport de couverture inexploitable : aucune logique métier détectée.")
    else:
        business_percent = _percentage(business_covered, business_statements)
        if business_percent < BUSINESS_MINIMUM:
            violations.append(
                f"Couverture métier {business_percent:.2f}% < {BUSINESS_MINIMUM:.2f}%."
            )

    if infrastructure_statements == 0:
        violations.append("Rapport de couverture inexploitable : aucune infrastructure détectée.")
    else:
        infrastructure_percent = _percentage(infrastructure_covered, infrastructure_statements)
        if infrastructure_percent < INFRASTRUCTURE_MINIMUM:
            violations.append(
                "Couverture infrastructure "
                f"{infrastructure_percent:.2f}% < {INFRASTRUCTURE_MINIMUM:.2f}%."
            )

    return violations


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True, help="Rapport JSON de coverage.py")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ÉCHEC — rapport de couverture illisible : {exc}")
        return 1
    if not isinstance(report, Mapping):
        print("ÉCHEC — la racine du rapport de couverture doit être un objet JSON.")
        return 1

    violations = evaluate_coverage_policy(report)
    if violations:
        print("ÉCHEC — politique de couverture non respectée :")
        for violation in violations:
            print(f"  - {violation}")
        return 1

    print(
        "SUCCÈS — couverture conforme : "
        f"global >= {GLOBAL_MINIMUM:.2f}%, contrats publics = {PUBLIC_CONTRACT_MINIMUM:.0f}%, "
        f"métier >= {BUSINESS_MINIMUM:.0f}%, infrastructure >= {INFRASTRUCTURE_MINIMUM:.0f}%."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

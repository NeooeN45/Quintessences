#!/usr/bin/env python3
"""Vérifie la fraîcheur et l'intégrité du registre documentaire canonique."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "23_QUALITY_MANAGEMENT" / "SOURCE_OF_TRUTH_REGISTRY.json"
REQUIRED_FIELDS = {
    "id",
    "scope",
    "paths",
    "authority",
    "owner",
    "status",
    "last_reviewed",
    "next_review",
    "superseded_by",
}
ALLOWED_STATUSES = {"canonique", "reference", "archive"}


def _parse_date(
    value: object, field: str, source_id: str, errors: list[str]
) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str):
        errors.append(f"{source_id}: {field} doit être une date ISO ou null")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{source_id}: {field} invalide ({value!r})")
        return None


def validate_registry(data: dict[str, Any], root: Path, today: date) -> list[str]:
    """Retourne toutes les non-conformités du registre sans s'arrêter à la première."""
    errors: list[str] = []
    sources = data.get("sources")
    precedence = data.get("precedence")

    if data.get("schema_version") != 1:
        errors.append("schema_version doit valoir 1")
    if not isinstance(sources, list) or not sources:
        return [*errors, "sources doit être une liste non vide"]
    if not isinstance(precedence, list):
        errors.append("precedence doit être une liste")
        precedence = []

    ids: set[str] = set()
    for index, source in enumerate(sources):
        source_id = (
            source.get("id", f"index-{index}")
            if isinstance(source, dict)
            else f"index-{index}"
        )
        if not isinstance(source, dict):
            errors.append(f"{source_id}: entrée non objet")
            continue

        missing = REQUIRED_FIELDS - source.keys()
        if missing:
            errors.append(
                f"{source_id}: champs manquants: {', '.join(sorted(missing))}"
            )
            continue
        if not isinstance(source_id, str) or not source_id:
            errors.append(f"index-{index}: id invalide")
            continue
        if source_id in ids:
            errors.append(f"{source_id}: id dupliqué")
        ids.add(source_id)

        status = source["status"]
        if status not in ALLOWED_STATUSES:
            errors.append(f"{source_id}: statut inconnu {status!r}")
        if (
            not isinstance(source["authority"], int)
            or not 0 <= source["authority"] <= 100
        ):
            errors.append(f"{source_id}: authority doit être un entier entre 0 et 100")
        if not isinstance(source["owner"], str) or not source["owner"].strip():
            errors.append(f"{source_id}: owner obligatoire")

        paths = source["paths"]
        if not isinstance(paths, list) or not paths:
            errors.append(f"{source_id}: paths doit être une liste non vide")
        else:
            for pattern in paths:
                if not isinstance(pattern, str):
                    errors.append(f"{source_id}: chemin non textuel")
                    continue
                pure_path = PurePosixPath(pattern)
                if pure_path.is_absolute() or ".." in pure_path.parts:
                    errors.append(f"{source_id}: chemin interdit {pattern!r}")
                    continue
                if not any(path.is_file() for path in root.glob(pattern)):
                    errors.append(f"{source_id}: aucun fichier pour {pattern!r}")

        last_reviewed = _parse_date(
            source["last_reviewed"], "last_reviewed", source_id, errors
        )
        next_review = _parse_date(
            source["next_review"], "next_review", source_id, errors
        )
        if status == "archive":
            if source["superseded_by"] is None:
                errors.append(f"{source_id}: une archive doit indiquer superseded_by")
        else:
            if next_review is None:
                errors.append(f"{source_id}: next_review obligatoire")
            elif next_review < today:
                errors.append(
                    f"{source_id}: revue expirée depuis le {next_review.isoformat()}"
                )
            if last_reviewed and next_review and next_review <= last_reviewed:
                errors.append(f"{source_id}: next_review doit suivre last_reviewed")

    unknown = [source_id for source_id in precedence if source_id not in ids]
    missing_from_precedence = [
        source_id for source_id in ids if source_id not in precedence
    ]
    if unknown:
        errors.append(f"precedence référence des ids inconnus: {', '.join(unknown)}")
    if missing_from_precedence:
        errors.append(
            f"ids absents de precedence: {', '.join(sorted(missing_from_precedence))}"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()

    try:
        data = json.loads(args.registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Registre illisible: {exc}")
        return 2

    errors = validate_registry(data, args.root.resolve(), args.today)
    if errors:
        print("Registre des sources de vérité NON CONFORME:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Registre conforme: {len(data['sources'])} sources contrôlées au {args.today.isoformat()}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

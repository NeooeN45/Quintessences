#!/usr/bin/env python3
"""Vérifie les contrats de tâches IA versionnés."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT_DIRECTORY = Path("GSIE/PROMPTS")
REGISTER_PATH = PROMPT_DIRECTORY / "REGISTER.md"
PROMPT_FILE_PATTERN = re.compile(r"^(GSIE-PROMPT-\d{4})-[a-z0-9-]+\.md$")
REGISTER_ID_PATTERN = re.compile(r"\|\s*(GSIE-PROMPT-\d{4})\s*\|")
STATUS_PATTERN = re.compile(r"^\|\s*Statut\s*\|\s*([^|]+)\|", re.MULTILINE)
ALLOWED_STATUSES = {
    "PROPOSÉE",
    "PRÊTE",
    "ASSIGNÉE",
    "EN_COURS",
    "BLOQUÉE",
    "EN_REVUE",
    "VALIDÉE",
    "INTÉGRÉE",
    "REJETÉE",
    "ANNULÉE",
}
REQUIRED_HEADINGS = {
    "## Mission",
    "## Documents obligatoires",
    "## Interdictions",
}
REPORT_HEADINGS = {"## Rapport obligatoire", "## Format du rapport"}


def _base_status(value: str) -> str:
    """Retourne l'état avant un éventuel motif séparé par un tiret long."""
    return value.strip().split("—", maxsplit=1)[0].strip()


def validate_prompt_catalog(root: Path = ROOT) -> list[str]:
    """Retourne toutes les non-conformités du catalogue de prompts."""
    errors: list[str] = []
    prompt_directory = root / PROMPT_DIRECTORY
    register_path = root / REGISTER_PATH

    if not register_path.is_file():
        return [f"registre absent: {REGISTER_PATH.as_posix()}"]

    register_text = register_path.read_text(encoding="utf-8")
    registered_ids = REGISTER_ID_PATTERN.findall(register_text)
    duplicate_registered = sorted(
        prompt_id
        for prompt_id in set(registered_ids)
        if registered_ids.count(prompt_id) > 1
    )
    for prompt_id in duplicate_registered:
        errors.append(f"{prompt_id}: entrée dupliquée dans le registre")

    files_by_id: dict[str, Path] = {}
    for path in sorted(prompt_directory.glob("GSIE-PROMPT-*.md")):
        match = PROMPT_FILE_PATTERN.fullmatch(path.name)
        if match is None:
            errors.append(f"{path.name}: nom de fichier invalide")
            continue

        prompt_id = match.group(1)
        if prompt_id in files_by_id:
            errors.append(
                f"{prompt_id}: plusieurs fichiers ({files_by_id[prompt_id].name}, {path.name})"
            )
            continue
        files_by_id[prompt_id] = path

        text = path.read_text(encoding="utf-8")
        if not text.startswith(f"# {prompt_id} — "):
            errors.append(f"{path.name}: titre absent ou identifiant incohérent")

        status_match = STATUS_PATTERN.search(text)
        if status_match is None:
            errors.append(f"{path.name}: champ Statut absent")
        else:
            status = _base_status(status_match.group(1))
            if status not in ALLOWED_STATUSES:
                errors.append(f"{path.name}: statut inconnu {status!r}")

        for heading in sorted(REQUIRED_HEADINGS):
            if heading not in text:
                errors.append(f"{path.name}: section obligatoire absente {heading!r}")
        if not any(heading in text for heading in REPORT_HEADINGS):
            errors.append(f"{path.name}: section de rapport obligatoire absente")

    registered_set = set(registered_ids)
    file_set = set(files_by_id)
    for prompt_id in sorted(file_set - registered_set):
        errors.append(f"{prompt_id}: fichier absent du registre")
    for prompt_id in sorted(registered_set - file_set):
        errors.append(f"{prompt_id}: entrée du registre sans fichier")

    if not files_by_id:
        errors.append("aucun prompt versionné trouvé")
    return errors


def main() -> int:
    errors = validate_prompt_catalog()
    if errors:
        print("Catalogue des prompts IA NON CONFORME:")
        for error in errors:
            print(f"- {error}")
        return 1

    count = len(list((ROOT / PROMPT_DIRECTORY).glob("GSIE-PROMPT-*.md")))
    print(f"Catalogue des prompts IA conforme: {count} mission(s) contrôlée(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

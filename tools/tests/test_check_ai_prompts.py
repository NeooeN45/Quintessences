"""Tests du garde-fou des prompts IA."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.check_ai_prompts import validate_prompt_catalog

VALID_PROMPT = """# GSIE-PROMPT-0001 — Mission de test

| Champ | Valeur |
|---|---|
| Statut | PRÊTE |

## Mission

Tester le catalogue.

## Documents obligatoires

- AGENTS.md

## Interdictions

- Aucun push.

## Rapport obligatoire

Rapport factuel.
"""


class AiPromptCatalogTest(unittest.TestCase):
    def _catalog(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        directory = tempfile.TemporaryDirectory()
        root = Path(directory.name)
        prompts = root / "GSIE" / "PROMPTS"
        prompts.mkdir(parents=True)
        register = prompts / "REGISTER.md"
        return directory, prompts, register

    def test_valid_catalog_is_accepted(self) -> None:
        directory, prompts, register = self._catalog()
        self.addCleanup(directory.cleanup)
        register.write_text(
            "| ID | Agent |\n|---|---|\n| GSIE-PROMPT-0001 | Claude |\n",
            encoding="utf-8",
        )
        (prompts / "GSIE-PROMPT-0001-test.md").write_text(
            VALID_PROMPT, encoding="utf-8"
        )

        self.assertEqual(validate_prompt_catalog(Path(directory.name)), [])

    def test_missing_section_and_unknown_status_are_rejected(self) -> None:
        directory, prompts, register = self._catalog()
        self.addCleanup(directory.cleanup)
        register.write_text("| GSIE-PROMPT-0001 | Claude |\n", encoding="utf-8")
        invalid = VALID_PROMPT.replace("PRÊTE", "TERMINÉE").replace(
            "## Interdictions", "## Notes"
        )
        (prompts / "GSIE-PROMPT-0001-test.md").write_text(invalid, encoding="utf-8")

        errors = validate_prompt_catalog(Path(directory.name))

        self.assertTrue(any("statut inconnu" in error for error in errors))
        self.assertTrue(any("section obligatoire absente" in error for error in errors))

    def test_registry_and_files_must_match(self) -> None:
        directory, prompts, register = self._catalog()
        self.addCleanup(directory.cleanup)
        register.write_text("| GSIE-PROMPT-0002 | GLM |\n", encoding="utf-8")
        (prompts / "GSIE-PROMPT-0001-test.md").write_text(
            VALID_PROMPT, encoding="utf-8"
        )

        errors = validate_prompt_catalog(Path(directory.name))

        self.assertTrue(any("fichier absent du registre" in error for error in errors))
        self.assertTrue(
            any("entrée du registre sans fichier" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()

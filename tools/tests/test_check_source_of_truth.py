"""Tests du garde-fou des sources de vérité."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from typing import Any

from tools.check_source_of_truth import validate_registry


def source(source_id: str, path: str, *, status: str = "canonique") -> dict[str, Any]:
    return {
        "id": source_id,
        "scope": "Test",
        "paths": [path],
        "authority": 50,
        "owner": "QA",
        "status": status,
        "last_reviewed": "2026-07-01",
        "next_review": None if status == "archive" else "2026-08-01",
        "superseded_by": "canonical" if status == "archive" else None,
    }


class SourceOfTruthRegistryTest(unittest.TestCase):
    def test_valid_registry_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "canonical.md").write_text("# Canonique", encoding="utf-8")
            (root / "archive.md").write_text("# Archive", encoding="utf-8")
            data = {
                "schema_version": 1,
                "precedence": ["canonical", "archive"],
                "sources": [
                    source("canonical", "canonical.md"),
                    source("archive", "archive.md", status="archive"),
                ],
            }

            self.assertEqual(validate_registry(data, root, date(2026, 7, 21)), [])

    def test_expired_or_missing_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            item = source("canonical", "missing.md")
            item["next_review"] = "2026-07-20"
            data = {
                "schema_version": 1,
                "precedence": ["canonical"],
                "sources": [item],
            }

            errors = validate_registry(data, Path(directory), date(2026, 7, 21))

            self.assertTrue(any("aucun fichier" in error for error in errors))
            self.assertTrue(any("revue expirée" in error for error in errors))

    def test_duplicate_identifier_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "doc.md").write_text("# Document", encoding="utf-8")
            data = {
                "schema_version": 1,
                "precedence": ["canonical"],
                "sources": [
                    source("canonical", "doc.md"),
                    source("canonical", "doc.md"),
                ],
            }

            errors = validate_registry(data, root, date(2026, 7, 21))

            self.assertTrue(any("id dupliqué" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

"""Valide le corpus de fixtures partagé Python/Kotlin contre ses verdicts attendus.

Ce test protège contre la dérive silencieuse du corpus : si quelqu'un
régénère `fixtures/contract-interop/` sans mettre à jour `expected.json`,
ou modifie une fixture à la main, ce test échoue côté Python avant même que
Kotlin ne soit exécuté. Le vérificateur Kotlin doit produire les mêmes
verdicts sur exactement les mêmes fichiers (voir capsule-verifier côté
GeoSylva).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from gsie_execution_kit.capsule import CapsuleError, verify_capsule

PROJECT_DIR = Path(__file__).resolve().parents[1]
CORPUS_DIR = PROJECT_DIR / "fixtures" / "contract-interop"


class InteropFixturesTests(unittest.TestCase):
    def setUp(self) -> None:
        expected_path = CORPUS_DIR / "expected.json"
        if not expected_path.is_file():
            self.skipTest(
                "Corpus d'interopérabilité absent — exécuter "
                "scripts/generate_interop_fixtures.py avant ce test."
            )
        self.manifest = json.loads(expected_path.read_text(encoding="utf-8"))

    def test_corpus_matches_expected_verdicts(self) -> None:
        failures: list[str] = []
        for case in self.manifest["cases"]:
            capsule_path = CORPUS_DIR / case["file"]
            public_key_path = CORPUS_DIR / case.get("public_key", "trusted-public.pem")
            try:
                verify_capsule(capsule_path, public_key_path)
                observed = "valid"
                observed_message = ""
            except CapsuleError as exc:
                observed = "invalid"
                observed_message = str(exc)

            if observed != case["expected"]:
                failures.append(
                    f"{case['id']}: attendu {case['expected']!r}, obtenu {observed!r} "
                    f"({observed_message!r})"
                )
                continue

            if case["expected"] == "invalid":
                expected_substring = case.get("error_contains")
                if expected_substring and expected_substring not in observed_message:
                    failures.append(
                        f"{case['id']}: message d'erreur {observed_message!r} ne contient pas "
                        f"{expected_substring!r}"
                    )

        self.assertEqual(failures, [], "\n".join(failures))

    def test_every_case_has_a_distinct_id(self) -> None:
        ids = [case["id"] for case in self.manifest["cases"]]
        self.assertEqual(
            len(ids), len(set(ids)), "identifiants de cas dupliqués dans expected.json"
        )

    def test_sha256sums_file_matches_corpus(self) -> None:
        import hashlib

        sums_path = CORPUS_DIR / "SHA256SUMS.txt"
        self.assertTrue(sums_path.is_file())
        recorded = {}
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", 1)
            recorded[name] = digest

        for entry in CORPUS_DIR.iterdir():
            if entry.name == "SHA256SUMS.txt":
                continue
            actual = hashlib.sha256(entry.read_bytes()).hexdigest()
            self.assertEqual(
                recorded.get(entry.name),
                actual,
                f"SHA-256 de {entry.name} ne correspond pas à SHA256SUMS.txt",
            )


if __name__ == "__main__":
    unittest.main()

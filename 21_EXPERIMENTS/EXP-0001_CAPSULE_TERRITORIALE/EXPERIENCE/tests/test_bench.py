from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from gsie_execution_kit.bench import BenchError, run_bench

PROJECT_DIR = Path(__file__).resolve().parents[1]
CASES_DIR = PROJECT_DIR / "fixtures" / "golden-bench"


class GoldenBenchTests(unittest.TestCase):
    def test_all_numeric_cases_pass_without_claiming_scientific_approval(self) -> None:
        report = run_bench(CASES_DIR)

        self.assertTrue(report["success"])
        self.assertTrue(report["numeric_success"])
        self.assertEqual(report["status"], "passed_with_review_pending")
        self.assertEqual(report["summary"]["numeric_passed"], 3)
        self.assertEqual(report["summary"]["review_pending"], 3)
        self.assertEqual(report["summary"]["production_eligible"], 0)

    def test_review_gate_fails_until_experts_approve_cases(self) -> None:
        report = run_bench(CASES_DIR, require_reviewed=True)

        self.assertFalse(report["success"])
        self.assertEqual(report["status"], "failed_review_gate")

    def test_detects_numeric_regression(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source = CASES_DIR / "GSIE-GB-DENDRO-ST-001.json"
            case = json.loads(source.read_text(encoding="utf-8"))
            case["expected"]["value"] = 999.0
            (temporary_path / source.name).write_text(json.dumps(case), encoding="utf-8")

            report = run_bench(temporary_path)

        self.assertFalse(report["success"])
        self.assertEqual(report["summary"]["numeric_failed"], 1)

    def test_rejects_physically_invalid_negative_diameter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source = CASES_DIR / "GSIE-GB-DENDRO-ST-001.json"
            case = json.loads(source.read_text(encoding="utf-8"))
            case["inputs"]["diameters_cm"] = [-10.0]
            (temporary_path / source.name).write_text(json.dumps(case), encoding="utf-8")

            with self.assertRaisesRegex(BenchError, "strictement positif"):
                run_bench(temporary_path)

    def test_reviewed_case_must_name_a_reviewer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source = CASES_DIR / "GSIE-GB-DENDRO-ST-001.json"
            case = json.loads(source.read_text(encoding="utf-8"))
            case["scientific_review"]["status"] = "reviewed"
            (temporary_path / source.name).write_text(json.dumps(case), encoding="utf-8")

            with self.assertRaisesRegex(BenchError, "identifier au moins un relecteur"):
                run_bench(temporary_path)

    def test_approved_case_requires_two_independent_reviewers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source = CASES_DIR / "GSIE-GB-DENDRO-ST-001.json"
            case = json.loads(source.read_text(encoding="utf-8"))
            case["scientific_review"]["status"] = "approved"
            case["scientific_review"]["reviewers"] = ["expert-1"]
            (temporary_path / source.name).write_text(json.dumps(case), encoding="utf-8")

            with self.assertRaisesRegex(BenchError, "deux relecteurs indépendants"):
                run_bench(temporary_path)


if __name__ == "__main__":
    unittest.main()

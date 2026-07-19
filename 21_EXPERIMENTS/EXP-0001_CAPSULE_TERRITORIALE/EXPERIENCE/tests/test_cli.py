from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from gsie_execution_kit.cli import main

PROJECT_DIR = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_demo_produces_machine_readable_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workdir = Path(temporary_directory) / "demo"
            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "demo",
                        "--source",
                        str(PROJECT_DIR / "fixtures" / "territoire-reference"),
                        "--cases",
                        str(PROJECT_DIR / "fixtures" / "golden-bench"),
                        "--workdir",
                        str(workdir),
                    ]
                )

            report = json.loads((workdir / "demonstration-report.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertIn("DÉMONSTRATION GSIE : SUCCÈS", output.getvalue())
        self.assertTrue(report["success"])
        self.assertTrue(report["offline"])
        self.assertFalse(report["production_ready"])
        self.assertEqual(report["scientific_review_pending"], 3)


if __name__ == "__main__":
    unittest.main()

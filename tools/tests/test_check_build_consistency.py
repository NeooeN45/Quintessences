"""Tests du garde-fou de cohérence de construction."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.check_build_consistency import validate_build_consistency


class BuildConsistencyTest(unittest.TestCase):
    def _root(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        api = root / "GSIE" / "API"
        rust = root / "GSIE" / "ENGINES" / "EVIDENCE_ENGINE" / "rust"
        api.mkdir(parents=True)
        rust.mkdir(parents=True)
        (api / "Dockerfile").write_text(
            "ENV MATURIN_VERSION=1.9.6\n"
            "RUN uv pip install --system --require-hashes -r requirements.txt\n",
            encoding="utf-8",
        )
        (api / "pyproject.toml").write_text(
            "[project]\n"
            "dependencies = [\n"
            '  "eccodes==2.47.0",\n'
            """  "eccodeslib==2.47.3.23; sys_platform != 'win32'",\n"""
            "]\n",
            encoding="utf-8",
        )
        (api / "uv.lock").write_text(
            '[[package]]\nname = "eccodeslib"\nversion = "2.47.3.23"\n',
            encoding="utf-8",
        )
        (rust / "pyproject.toml").write_text(
            '[build-system]\nrequires = ["maturin==1.9.6"]\n',
            encoding="utf-8",
        )
        return root

    def test_consistent_build_is_accepted(self) -> None:
        self.assertEqual(validate_build_consistency(self._root()), [])

    def test_maturin_drift_is_rejected(self) -> None:
        root = self._root()
        manifest = (
            root / "GSIE" / "ENGINES" / "EVIDENCE_ENGINE" / "rust" / "pyproject.toml"
        )
        manifest.write_text(
            '[build-system]\nrequires = ["maturin==1.8.0"]\n',
            encoding="utf-8",
        )
        self.assertTrue(
            any("Maturin" in error for error in validate_build_consistency(root))
        )

    def test_unlocked_eccodeslib_is_rejected(self) -> None:
        root = self._root()
        (root / "GSIE" / "API" / "uv.lock").write_text("", encoding="utf-8")
        self.assertTrue(
            any("uv.lock" in error for error in validate_build_consistency(root))
        )


if __name__ == "__main__":
    unittest.main()

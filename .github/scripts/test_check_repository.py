"""Tests du garde de fichiers, sans identifiant réel ni réseau."""

import hashlib
import importlib.util
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "guard", Path(__file__).with_name("check_repository.py")
)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class RepositoryGuardTest(unittest.TestCase):
    def test_environment_files_are_private_but_templates_are_allowed(self):
        for path in [
            ".env",
            "app/.env.production",
            "keys/release.jks",
            "local.properties",
        ]:
            self.assertTrue(guard.forbidden(path), path)
        for path in [
            ".env.example",
            "api/.env.template",
            "api/.env.sample",
            "app/config.py",
        ]:
            self.assertFalse(guard.forbidden(path), path)

    def test_fixture_content_is_checked_and_unknown_private_files_fail(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".github").mkdir()
            fixture = root / "test.pem"
            fixture.write_text("fixture publique de test")
            (root / ".github/security-fixtures.json").write_text(
                json.dumps(
                    {
                        "test.pem": hashlib.sha256(fixture.read_bytes()).hexdigest(),
                    }
                )
            )
            output = io.StringIO()
            with (
                patch.object(guard, "ROOT", root),
                patch.object(
                    guard.subprocess, "check_output", return_value=b"test.pem\0"
                ),
                redirect_stdout(output),
            ):
                self.assertEqual(guard.main(), 0)
                fixture.write_text("contenu remplacé non autorisé")
                self.assertEqual(guard.main(), 1)
            self.assertNotIn("contenu remplacé", output.getvalue())
            with (
                patch.object(guard, "ROOT", root),
                patch.object(
                    guard.subprocess, "check_output", return_value=b".env.production\0"
                ),
                redirect_stdout(output),
            ):
                self.assertEqual(guard.main(), 1)

    def test_symlink_cannot_bypass_fixture_hash(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".github").mkdir()
            target = root / "test-data"
            target.write_text("fixture")
            (root / "test.pem").symlink_to(target)
            (root / ".github/security-fixtures.json").write_text(
                json.dumps(
                    {"test.pem": hashlib.sha256(target.read_bytes()).hexdigest()}
                )
            )
            with (
                patch.object(guard, "ROOT", root),
                patch.object(
                    guard.subprocess, "check_output", return_value=b"test.pem\0"
                ),
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(guard.main(), 1)


if __name__ == "__main__":
    unittest.main()

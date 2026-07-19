from __future__ import annotations

import tempfile
import unittest
import warnings
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from gsie_execution_kit.capsule import (
    CapsuleError,
    build_capsule,
    generate_keypair,
    verify_capsule,
)

PROJECT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_DIR = PROJECT_DIR / "fixtures" / "territoire-reference"


class CapsuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.workdir = Path(self.temporary_directory.name)
        self.private_key = self.workdir / "private.pem"
        self.public_key = self.workdir / "public.pem"
        self.capsule = self.workdir / "territoire.gsiecap"
        generate_keypair(self.private_key, self.public_key)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _build(self) -> None:
        build_capsule(
            FIXTURE_DIR,
            self.capsule,
            self.private_key,
            created_at=datetime(2026, 7, 18, tzinfo=UTC),
        )

    def _rewrite_archive(self, target: Path, mutation: dict[str, bytes]) -> None:
        with (
            zipfile.ZipFile(self.capsule, "r") as source,
            zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as destination,
        ):
            for info in source.infolist():
                data = mutation.get(info.filename, source.read(info.filename))
                destination.writestr(info.filename, data)

    def test_builds_and_verifies_capsule(self) -> None:
        self._build()

        report = verify_capsule(
            self.capsule,
            self.public_key,
            now=datetime(2026, 7, 18, 1, tzinfo=UTC),
        )

        self.assertTrue(report["valid"])
        self.assertEqual(report["signature"], "valid")
        self.assertEqual(report["territory"]["operational_use"], "forbidden")
        self.assertEqual(report["file_count"], 4)

    def test_rejects_tampered_payload(self) -> None:
        self._build()
        tampered = self.workdir / "tampered.gsiecap"
        original_name = "payload/data/observations.json"
        with zipfile.ZipFile(self.capsule, "r") as source:
            altered_data = source.read(original_name) + b" "
        self._rewrite_archive(tampered, {original_name: altered_data})

        with self.assertRaisesRegex(CapsuleError, "Taille divergente|Empreinte divergente"):
            verify_capsule(tampered, self.public_key)

    def test_rejects_untrusted_key(self) -> None:
        self._build()
        other_private = self.workdir / "other-private.pem"
        other_public = self.workdir / "other-public.pem"
        generate_keypair(other_private, other_public)

        with self.assertRaisesRegex(CapsuleError, "clé publique approuvée"):
            verify_capsule(self.capsule, other_public)

    def test_rejects_path_traversal(self) -> None:
        self._build()
        hostile = self.workdir / "hostile.gsiecap"
        self._rewrite_archive(hostile, {})
        with zipfile.ZipFile(hostile, "a") as archive:
            archive.writestr("../intrusion.txt", b"intrusion")

        with self.assertRaisesRegex(CapsuleError, "Chemin d'archive non sûr"):
            verify_capsule(hostile, self.public_key)

    def test_rejects_duplicate_members(self) -> None:
        self._build()
        duplicate = self.workdir / "duplicate.gsiecap"
        self._rewrite_archive(duplicate, {})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(duplicate, "a") as archive:
                archive.writestr("manifest.json", b"{}")

        with self.assertRaisesRegex(CapsuleError, "membres dupliqués"):
            verify_capsule(duplicate, self.public_key)

    def test_rejects_expired_capsule(self) -> None:
        build_capsule(
            FIXTURE_DIR,
            self.capsule,
            self.private_key,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            valid_until=datetime(2026, 1, 2, tzinfo=UTC),
        )

        with self.assertRaisesRegex(CapsuleError, "Capsule expirée"):
            verify_capsule(
                self.capsule,
                self.public_key,
                now=datetime(2026, 1, 3, tzinfo=UTC),
            )

    def test_key_generation_refuses_silent_overwrite(self) -> None:
        with self.assertRaisesRegex(CapsuleError, "existe déjà"):
            generate_keypair(self.private_key, self.public_key)

    def test_refuses_private_key_inside_payload(self) -> None:
        payload_key = FIXTURE_DIR / "payload" / "forbidden-private.pem"
        with self.assertRaisesRegex(CapsuleError, "clé privée"):
            build_capsule(FIXTURE_DIR, self.capsule, payload_key)


if __name__ == "__main__":
    unittest.main()

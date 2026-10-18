#!/usr/bin/env python3
"""Refuse les fichiers sensibles versionnés sans afficher leur contenu."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def forbidden(path):
    name = Path(path).name.lower()
    return (
        (
            (name == ".env" or name.startswith(".env."))
            and name not in {".env.example", ".env.template", ".env.sample"}
        )
        or name in {"id_rsa", "id_ed25519", "keystore.properties", "local.properties"}
        or (Path(name).suffix in {".jks", ".keystore", ".p12", ".pfx", ".pem", ".key"})
    )


def main():
    manifest = ROOT / ".github/security-fixtures.json"
    exceptions = json.loads(manifest.read_text()) if manifest.exists() else {}
    files = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
        .decode()
        .split("\0")
    )
    failures = []
    for name in filter(None, files):
        if not forbidden(name):
            continue
        path = ROOT / name
        expected = exceptions.get(name)
        if (
            not expected
            or path.is_symlink()
            or not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            failures.append(name)
    if failures:
        print("Fichiers sensibles non autorisés (aucune valeur affichée) :")
        print("\n".join(failures))
        return 1
    print("Fichiers versionnés : contrôle réussi ; exceptions vérifiées par empreinte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

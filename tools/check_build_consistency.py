#!/usr/bin/env python3
"""Vérifie la cohérence des versions utilisées pour construire GSIE."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _read_toml(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        errors.append(f"{path}: TOML illisible ({exc})")
        return {}


def validate_build_consistency(root: Path) -> list[str]:
    """Retourne les dérives entre Docker, les manifestes et le verrou."""
    errors: list[str] = []
    dockerfile = root / "GSIE" / "API" / "Dockerfile"
    api_manifest = root / "GSIE" / "API" / "pyproject.toml"
    api_lock = root / "GSIE" / "API" / "uv.lock"
    rust_manifest = (
        root / "GSIE" / "ENGINES" / "EVIDENCE_ENGINE" / "rust" / "pyproject.toml"
    )

    try:
        docker_text = dockerfile.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"GSIE/API/Dockerfile illisible ({exc})"]

    maturin_match = re.search(
        r"^ENV MATURIN_VERSION=([^\s]+)$", docker_text, flags=re.MULTILINE
    )
    if maturin_match is None:
        errors.append("Dockerfile: MATURIN_VERSION doit être épinglée")
        maturin_version = None
    else:
        maturin_version = maturin_match.group(1)

    rust_data = _read_toml(rust_manifest, errors)
    build_requirements = rust_data.get("build-system", {}).get("requires", [])
    maturin_requirements = [
        requirement
        for requirement in build_requirements
        if isinstance(requirement, str) and requirement.startswith("maturin")
    ]
    expected_maturin = (
        f"maturin=={maturin_version}" if maturin_version is not None else None
    )
    if expected_maturin and maturin_requirements != [expected_maturin]:
        errors.append(
            "Maturin doit être épinglé à la même version dans Dockerfile "
            "et GSIE/ENGINES/EVIDENCE_ENGINE/rust/pyproject.toml"
        )

    api_data = _read_toml(api_manifest, errors)
    dependencies = api_data.get("project", {}).get("dependencies", [])
    eccodes_requirement = next(
        (
            item
            for item in dependencies
            if isinstance(item, str) and item.startswith("eccodes==")
        ),
        None,
    )
    eccodeslib_requirement = next(
        (
            item
            for item in dependencies
            if isinstance(item, str) and item.startswith("eccodeslib==")
        ),
        None,
    )
    if eccodeslib_requirement is None:
        errors.append(
            "GSIE/API/pyproject.toml: eccodeslib doit être une dépendance directe épinglée"
        )
        eccodeslib_version = None
    else:
        version_match = re.match(r"eccodeslib==([^;\s]+)", eccodeslib_requirement)
        eccodeslib_version = version_match.group(1) if version_match else None
        if "sys_platform != 'win32'" not in eccodeslib_requirement:
            errors.append("eccodeslib doit être limité aux plateformes hors Windows")

    if eccodes_requirement and eccodeslib_version:
        eccodes_version = eccodes_requirement.removeprefix("eccodes==").split(";", 1)[0]
        if eccodes_version.split(".")[:2] != eccodeslib_version.split(".")[:2]:
            errors.append(
                "eccodes et eccodeslib doivent partager la version majeure.mineure"
            )

    lock_data = _read_toml(api_lock, errors)
    locked_packages = {
        package.get("name"): package.get("version")
        for package in lock_data.get("package", [])
        if isinstance(package, dict)
    }
    if eccodeslib_version and locked_packages.get("eccodeslib") != eccodeslib_version:
        errors.append("uv.lock ne correspond pas à la version eccodeslib du manifeste")

    if "--require-hashes" in docker_text and eccodeslib_requirement is None:
        errors.append(
            "Docker exige les empreintes mais eccodeslib transitif n'est pas verrouillé"
        )
    return errors


def main() -> int:
    errors = validate_build_consistency(ROOT)
    if errors:
        print("Cohérence de construction NON CONFORME :")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Cohérence de construction conforme.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Génère le corpus de fixtures partagé Python/Kotlin pour le contrat de capsule.

Ce script produit, une fois pour toutes, un ensemble déterministe de fichiers
`.gsiecap` (valides et hostiles) accompagnés d'un fichier `expected.json`
machine-readable listant le verdict attendu pour chacun. Le corpus est copié
tel quel dans le module Kotlin (`capsule-verifier/src/test/resources/`) — voir
`docs/COMPATIBILITE_KOTLIN.md` pour la stratégie de partage retenue.

Usage :
    PYTHONPATH=src python scripts/generate_interop_fixtures.py

Ne pas exécuter en production. Les clés générées ici sont strictement des
clés de test, jamais suivies comme clés de confiance réelles.
"""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gsie_execution_kit.capsule import (
    MANIFEST_NAME,
    PAYLOAD_PREFIX,
    SIGNATURE_ALGORITHM,
    SIGNATURE_NAME,
    SIGNATURE_SCHEMA_VERSION,
    _load_private_key,
    _manifest_id,
    _zip_info,
    build_capsule,
    generate_keypair,
)
from gsie_execution_kit.json_utils import canonical_json, loads_strict

PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_DIR / "fixtures" / "territoire-reference"
OUTPUT_DIR = PROJECT_DIR / "fixtures" / "contract-interop"
FIXED_CREATED_AT = datetime(2026, 7, 19, 8, 0, 0, tzinfo=UTC)


def _read_zip_members(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path, "r") as archive:
        return {info.filename: archive.read(info) for info in archive.infolist()}


def _zip_info_raw_name(name: str) -> zipfile.ZipInfo:
    """Comme `_zip_info`, mais sans la normalisation `os.sep -> '/'` de `ZipInfo.__init__`.

    Sur Windows, `zipfile.ZipInfo.__init__` remplace silencieusement chaque
    backslash du nom par un slash (car `os.sep == '\\\\'`), rendant impossible
    la construction d'une fixture "séparateur Windows dans le nom d'archive"
    via le constructeur normal. On construit avec un nom neutre puis on force
    l'attribut après coup, ce qui contourne uniquement cette normalisation et
    préserve le reste du comportement de `_zip_info` (horodatage, permissions).
    """

    info = _zip_info("placeholder.bin")
    info.filename = name
    return info


def _write_zip(
    path: Path,
    members: dict[str, bytes],
    *,
    extra_stored: dict[str, bytes] | None = None,
) -> None:
    """Réécrit une archive à partir d'un dict nom -> octets (ordre trié, déflate niveau 9)."""

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(members):
            archive.writestr(_zip_info_raw_name(name), members[name])
        for name, data in (extra_stored or {}).items():
            archive.writestr(_zip_info_raw_name(name), data)


def _mutate_manifest(
    members: dict[str, bytes],
    mutation: Any,
) -> dict[str, bytes]:
    """Reparse manifest.json, applique `mutation(dict) -> dict`, re-sérialise canoniquement.

    Ne re-signe PAS : utilisé uniquement pour les cas où la structure attendue
    est rejetée avant toute vérification cryptographique (schema_version,
    tailles invalides, clé incohérente) — l'ordre des contrôles dans
    `verify_capsule` garantit que ces rejets surviennent avant `public_key.verify`.
    """

    updated = dict(members)
    manifest = loads_strict(members[MANIFEST_NAME])
    assert isinstance(manifest, dict)
    mutated_manifest = mutation(manifest)
    updated[MANIFEST_NAME] = canonical_json(mutated_manifest)
    return updated


def _mutate_signature(members: dict[str, bytes], mutation: Any) -> dict[str, bytes]:
    updated = dict(members)
    signature = loads_strict(members[SIGNATURE_NAME])
    assert isinstance(signature, dict)
    updated[SIGNATURE_NAME] = canonical_json(mutation(signature))
    return updated


def _highly_compressible_blob(size: int) -> bytes:
    return b"0" * size


def generate() -> dict[str, Any]:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    trusted_private = OUTPUT_DIR / "trusted-private-TEST-ONLY.pem"
    trusted_public = OUTPUT_DIR / "trusted-public.pem"
    other_private = OUTPUT_DIR / "other-private-TEST-ONLY.pem"
    other_public = OUTPUT_DIR / "other-public.pem"
    trusted_key_id = generate_keypair(trusted_private, trusted_public)
    other_key_id = generate_keypair(other_private, other_public)

    # --- 1. Capsule valide de référence ---------------------------------
    valid_path = OUTPUT_DIR / "valid-minimal.gsiecap"
    build_capsule(SOURCE_DIR, valid_path, trusted_private, created_at=FIXED_CREATED_AT)
    base_members = _read_zip_members(valid_path)

    cases: list[dict[str, Any]] = [
        {
            "id": "valid-minimal",
            "file": "valid-minimal.gsiecap",
            "public_key": "trusted-public.pem",
            "expected": "valid",
        }
    ]

    def emit(
        case_id: str,
        members: dict[str, bytes],
        *,
        public_key: str = "trusted-public.pem",
        expected_error_contains: str,
    ) -> None:
        path = OUTPUT_DIR / f"{case_id}.gsiecap"
        _write_zip(path, members)
        cases.append(
            {
                "id": case_id,
                "file": path.name,
                "public_key": public_key,
                "expected": "invalid",
                "error_contains": expected_error_contains,
            }
        )

    # --- 2. Payload altéré ------------------------------------------------
    tampered = dict(base_members)
    tampered[f"{PAYLOAD_PREFIX}data/observations.json"] = (
        base_members[f"{PAYLOAD_PREFIX}data/observations.json"] + b" "
    )
    emit("tampered-payload", tampered, expected_error_contains="divergente")

    # --- 3. Clé non fiable (signée par une autre clé valide) --------------
    other_capsule = OUTPUT_DIR / "_scratch-other-key.gsiecap"
    build_capsule(SOURCE_DIR, other_capsule, other_private, created_at=FIXED_CREATED_AT)
    emit(
        "untrusted-key",
        _read_zip_members(other_capsule),
        expected_error_contains="clé publique approuvée",
    )
    other_capsule.unlink()

    # --- 4. Membre non déclaré (path traversal) ---------------------------
    hostile = dict(base_members)
    hostile["../intrusion.txt"] = b"intrusion"
    emit("path-traversal", hostile, expected_error_contains="Chemin d'archive non s")

    # --- 5. Séparateur Windows dans un chemin déclaré du manifeste ---------
    # Note technique : un backslash littéral dans un NOM DE MEMBRE ZIP brut
    # n'est pas observable via `zipfile` — le module normalise silencieusement
    # os.sep -> '/' à chaque reconstruction de ZipInfo depuis le répertoire
    # central, y compris en lecture (donc même une archive forgée à la main
    # est "corrigée" dès qu'on la relit). Le contrôle "\\ interdit" de
    # `_validate_relative_name` reste néanmoins réellement atteignable via le
    # champ `path` du manifeste (une chaîne JSON, non concernée par cette
    # normalisation) : c'est ce que ce cas exerce.
    def _windows_separator_path(manifest: dict[str, Any]) -> dict[str, Any]:
        files = [dict(entry) for entry in manifest["files"]]
        files[0]["path"] = files[0]["path"].replace("/", "\\")
        return {**manifest, "files": files}

    windows_sep = _mutate_manifest(base_members, _windows_separator_path)
    emit("windows-separator-name", windows_sep, expected_error_contains="Chemin d'archive interdit")

    # --- 6. Membre non déclaré (entrée répertoire) ------------------------
    directory_entry = dict(base_members)
    directory_entry["payload/extra/"] = b""
    emit("unexpected-directory-entry", directory_entry, expected_error_contains="non canonique")

    # --- 7. Membre non déclaré (Unicode ambigu, NFD vs NFC) ---------------
    import unicodedata

    nfc_name = f"{PAYLOAD_PREFIX}data/dé.json"
    nfd_name = f"{PAYLOAD_PREFIX}data/" + unicodedata.normalize("NFD", "dé") + ".json"
    assert nfc_name != nfd_name
    ambiguous = dict(base_members)
    ambiguous[nfd_name] = b"{}"
    emit("ambiguous-unicode-name", ambiguous, expected_error_contains="non déclar")

    # --- 8. Membres dupliqués ---------------------------------------------
    # écrit directement (contourne la déduplication par dict Python)
    dup_path = OUTPUT_DIR / "duplicate-members.gsiecap"
    with zipfile.ZipFile(dup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(base_members):
            archive.writestr(_zip_info(name), base_members[name])
        archive.writestr(_zip_info(MANIFEST_NAME), b"{}")
    cases.append(
        {
            "id": "duplicate-members",
            "file": dup_path.name,
            "public_key": "trusted-public.pem",
            "expected": "invalid",
            "error_contains": "membres dupliqués",
        }
    )

    # --- 9. Membre manquant ------------------------------------------------
    missing = dict(base_members)
    del missing[f"{PAYLOAD_PREFIX}data/observations.json"]
    emit("missing-member", missing, expected_error_contains="manquants")

    # --- 10. Archive vide ---------------------------------------------------
    empty_path = OUTPUT_DIR / "empty-archive.gsiecap"
    with zipfile.ZipFile(empty_path, "w"):
        pass
    cases.append(
        {
            "id": "empty-archive",
            "file": empty_path.name,
            "public_key": "trusted-public.pem",
            "expected": "invalid",
            "error_contains": "Membre obligatoire absent",
        }
    )

    # --- 11. Budget dépassé (ratio de compression) -------------------------
    bomb = dict(base_members)
    bomb[f"{PAYLOAD_PREFIX}data/territory.geojson"] = _highly_compressible_blob(20 * 1024 * 1024)
    emit("budget-exceeded-ratio", bomb, expected_error_contains="Ratio de compression suspect")

    # --- 12. Version majeure de schéma inconnue ----------------------------
    unsupported_version = _mutate_manifest(base_members, lambda m: {**m, "schema_version": "2.0.0"})
    emit(
        "unsupported-schema-version",
        unsupported_version,
        expected_error_contains="Version majeure de manifeste non supportée",
    )

    # --- 13. Taille de fichier invalide (négative) -------------------------
    def _negative_size(manifest: dict[str, Any]) -> dict[str, Any]:
        files = [dict(entry) for entry in manifest["files"]]
        files[0]["size"] = -1
        return {**manifest, "files": files}

    invalid_size = _mutate_manifest(base_members, _negative_size)
    emit("invalid-negative-size", invalid_size, expected_error_contains="Taille invalide")

    # --- 14. Empreinte de clé incohérente (manifest vs signature) ----------
    inconsistent_key = _mutate_signature(base_members, lambda s: {**s, "key_id": other_key_id})
    emit(
        "inconsistent-key-fingerprint",
        inconsistent_key,
        expected_error_contains="identifiants de clé du manifeste divergent",
    )

    # --- 15. key_id falsifié mais signature cryptographique invalide -------
    # Le manifeste ET la signature déclarent tous deux la clé de confiance,
    # mais la signature a réellement été produite par l'autre clé privée :
    # doit échouer à la vérification cryptographique, pas à la comparaison
    # d'identifiants (chemin de code distinct du cas "untrusted-key"). Toute
    # mutation du manifeste change son hash (capsule_id) : on doit donc
    # recalculer un capsule_id cohérent avec le contenu muté avant de signer
    # avec la MAUVAISE clé privée, pour que le rejet survienne bien à l'étape
    # cryptographique et non à l'étape "capsule_id ne correspond pas".
    falsified_manifest_without_id = dict(loads_strict(base_members[MANIFEST_NAME]))
    falsified_manifest_without_id.pop("capsule_id")
    falsified_manifest_without_id["signature"] = {
        "algorithm": SIGNATURE_ALGORITHM,
        "key_id": trusted_key_id,
    }
    falsified_manifest = {
        "capsule_id": _manifest_id(falsified_manifest_without_id),
        **falsified_manifest_without_id,
    }
    falsified_manifest_bytes = canonical_json(falsified_manifest)
    wrong_private_key = _load_private_key(other_private)
    wrong_signature_bytes = wrong_private_key.sign(falsified_manifest_bytes)
    falsified_signature_document = {
        "schema_version": SIGNATURE_SCHEMA_VERSION,
        "algorithm": SIGNATURE_ALGORITHM,
        "key_id": trusted_key_id,
        "signature_base64": base64.b64encode(wrong_signature_bytes).decode("ascii"),
    }
    falsified = dict(base_members)
    falsified[MANIFEST_NAME] = falsified_manifest_bytes
    falsified[SIGNATURE_NAME] = canonical_json(falsified_signature_document)
    emit(
        "falsified-key-id-crypto-invalid",
        falsified,
        expected_error_contains="Signature cryptographique invalide",
    )

    # --- 16. NaN littéral injecté dans le manifeste ------------------------
    # Ne peut pas passer par canonical_json (allow_nan=False) : construit
    # les octets bruts à la main en remplaçant un nombre du bbox par NaN,
    # dans une copie du manifeste dont l'agencement (espaces/tri) est
    # préservé par ailleurs — ce cas casse volontairement la canonicité,
    # ce qui est également un comportement attendu et testé.
    manifest_text = base_members[MANIFEST_NAME].decode("utf-8")
    nan_manifest_text = manifest_text.replace("1.89", "NaN", 1)
    assert nan_manifest_text != manifest_text
    nan_manifest = dict(base_members)
    nan_manifest[MANIFEST_NAME] = nan_manifest_text.encode("utf-8")
    emit(
        "nan-in-manifest",
        nan_manifest,
        expected_error_contains="Constante JSON non finie interdite",
    )

    # --- 17. Clés JSON dupliquées dans le manifeste ------------------------
    duplicated_key_text = manifest_text.replace(
        '"schema_version":"1.0.0"',
        '"schema_version":"1.0.0","schema_version":"1.0.0"',
        1,
    )
    assert duplicated_key_text != manifest_text
    dup_key_manifest = dict(base_members)
    dup_key_manifest[MANIFEST_NAME] = duplicated_key_text.encode("utf-8")
    emit(
        "duplicate-json-keys",
        dup_key_manifest,
        expected_error_contains="Clé JSON dupliquée",
    )

    manifest_json = {
        "schema_version": "1.0.0",
        "generated_at": FIXED_CREATED_AT.isoformat().replace("+00:00", "Z"),
        "trusted_key_id": trusted_key_id,
        "other_key_id": other_key_id,
        "cases": cases,
    }
    (OUTPUT_DIR / "expected.json").write_text(
        json.dumps(manifest_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    sha256_lines = []
    for entry in sorted(OUTPUT_DIR.iterdir()):
        if entry.name == "SHA256SUMS.txt":
            continue
        digest = hashlib.sha256(entry.read_bytes()).hexdigest()
        sha256_lines.append(f"{digest}  {entry.name}")
    (OUTPUT_DIR / "SHA256SUMS.txt").write_text("\n".join(sha256_lines) + "\n", encoding="utf-8")

    return manifest_json


if __name__ == "__main__":
    result = generate()
    print(f"{len(result['cases'])} cas générés dans {OUTPUT_DIR}")

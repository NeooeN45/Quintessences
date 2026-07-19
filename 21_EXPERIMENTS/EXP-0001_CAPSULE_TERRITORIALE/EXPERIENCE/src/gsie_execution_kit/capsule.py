"""Construction et vérification d'une capsule territoriale GSIE v1."""

from __future__ import annotations

import base64
import binascii
import hashlib
import os
import re
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import IO, Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from gsie_execution_kit.json_utils import (
    StrictJsonError,
    canonical_json,
    loads_strict,
)

SCHEMA_VERSION = "1.0.0"
SIGNATURE_SCHEMA_VERSION = "1.0.0"
SIGNATURE_ALGORITHM = "Ed25519"
MANIFEST_NAME = "manifest.json"
SIGNATURE_NAME = "signature.json"
PAYLOAD_PREFIX = "payload/"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{2,127}$")
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class CapsuleError(RuntimeError):
    """Signale qu'une capsule ne peut pas être créée ou approuvée."""


@dataclass(frozen=True, slots=True)
class CapsuleLimits:
    """Budgets défensifs appliqués avant de lire le contenu métier."""

    max_files: int = 512
    max_total_uncompressed_bytes: int = 512 * 1024 * 1024
    max_member_uncompressed_bytes: int = 256 * 1024 * 1024
    max_metadata_bytes: int = 2 * 1024 * 1024
    max_compression_ratio: float = 200.0


@dataclass(frozen=True, slots=True)
class _PayloadFile:
    source_path: Path
    archive_path: str
    size: int
    sha256: str


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _isoformat(value: datetime) -> str:
    if value.tzinfo is None:
        raise CapsuleError("Une date de capsule doit inclure un fuseau horaire")
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_datetime(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise CapsuleError(f"{field} doit être une date ISO 8601")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CapsuleError(f"{field} n'est pas une date ISO 8601 valide") from exc
    if parsed.tzinfo is None:
        raise CapsuleError(f"{field} doit inclure un fuseau horaire")
    return parsed.astimezone(UTC)


def _sha256_stream(stream: IO[bytes]) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
        size += len(chunk)
    return digest.hexdigest(), size


def _sha256_file(path: Path) -> tuple[str, int]:
    with path.open("rb") as stream:
        return _sha256_stream(stream)


def _validate_relative_name(name: str, *, prefix_required: bool = False) -> None:
    if not name or "\\" in name or "\x00" in name:
        raise CapsuleError(f"Chemin d'archive interdit : {name!r}")
    pure = PurePosixPath(name)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise CapsuleError(f"Chemin d'archive non sûr : {name!r}")
    if pure.as_posix() != name or name.endswith("/"):
        raise CapsuleError(f"Chemin d'archive non canonique : {name!r}")
    if prefix_required and not name.startswith(PAYLOAD_PREFIX):
        raise CapsuleError(f"Membre hors payload interdit : {name!r}")


def _load_json_file(path: Path, *, max_bytes: int) -> dict[str, Any]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise CapsuleError(f"Impossible de lire {path}: {exc}") from exc
    if size > max_bytes:
        raise CapsuleError(f"Métadonnée trop volumineuse : {path} ({size} octets)")
    try:
        value = loads_strict(path.read_bytes())
    except (OSError, StrictJsonError) as exc:
        raise CapsuleError(f"Métadonnée JSON invalide {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CapsuleError(f"{path} doit contenir un objet JSON")
    return value


def _atomic_write(path: Path, payload: bytes, *, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        temporary_path.chmod(mode)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _load_private_key(path: Path) -> Ed25519PrivateKey:
    try:
        key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    except (OSError, ValueError, TypeError) as exc:
        raise CapsuleError(f"Clé privée illisible : {path}") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise CapsuleError("La clé privée doit être une clé Ed25519")
    return key


def _load_public_key(path: Path) -> Ed25519PublicKey:
    try:
        key = serialization.load_pem_public_key(path.read_bytes())
    except (OSError, ValueError, TypeError) as exc:
        raise CapsuleError(f"Clé publique illisible : {path}") from exc
    if not isinstance(key, Ed25519PublicKey):
        raise CapsuleError("La clé publique doit être une clé Ed25519")
    return key


def _key_id(public_key: Ed25519PublicKey) -> str:
    encoded = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def generate_keypair(private_path: Path, public_path: Path, *, overwrite: bool = False) -> str:
    """Génère une paire Ed25519 de démonstration et retourne son identifiant."""

    if private_path.resolve() == public_path.resolve():
        raise CapsuleError("Les chemins des clés privée et publique doivent être distincts")
    if not overwrite and (private_path.exists() or public_path.exists()):
        raise CapsuleError(
            "Une clé existe déjà ; utiliser explicitement overwrite pour la remplacer"
        )

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    _atomic_write(private_path, private_bytes, mode=0o600)
    _atomic_write(public_path, public_bytes, mode=0o644)
    return _key_id(public_key)


def _collect_payload(source_dir: Path, limits: CapsuleLimits) -> list[_PayloadFile]:
    payload_dir = source_dir / "payload"
    if not payload_dir.is_dir():
        raise CapsuleError(f"Dossier payload manquant : {payload_dir}")

    payload_files: list[_PayloadFile] = []
    total_size = 0
    for root, directories, filenames in os.walk(payload_dir, followlinks=False):
        root_path = Path(root)
        for directory in directories:
            candidate = root_path / directory
            if candidate.is_symlink():
                raise CapsuleError(f"Lien symbolique interdit dans le payload : {candidate}")
        for filename in filenames:
            candidate = root_path / filename
            if candidate.is_symlink() or not candidate.is_file():
                raise CapsuleError(f"Fichier non régulier interdit : {candidate}")
            relative_name = candidate.relative_to(payload_dir).as_posix()
            _validate_relative_name(relative_name)
            digest, size = _sha256_file(candidate)
            if size > limits.max_member_uncompressed_bytes:
                raise CapsuleError(f"Fichier trop volumineux : {relative_name} ({size} octets)")
            total_size += size
            if total_size > limits.max_total_uncompressed_bytes:
                raise CapsuleError("Le payload dépasse le budget total autorisé")
            payload_files.append(_PayloadFile(candidate, relative_name, size, digest))

    payload_files.sort(key=lambda item: item.archive_path)
    if not payload_files:
        raise CapsuleError("Le payload est vide")
    if len(payload_files) > limits.max_files:
        raise CapsuleError(f"Le payload contient trop de fichiers : {len(payload_files)}")
    if not any(item.archive_path == "territory.json" for item in payload_files):
        raise CapsuleError("Le payload doit contenir territory.json")
    return payload_files


def _territory_summary(source_dir: Path, limits: CapsuleLimits) -> dict[str, Any]:
    territory = _load_json_file(
        source_dir / "payload" / "territory.json",
        max_bytes=limits.max_metadata_bytes,
    )
    required = {
        "territory_id": str,
        "name": str,
        "crs": str,
        "bbox": list,
        "synthetic": bool,
        "operational_use": str,
    }
    for field, expected_type in required.items():
        if not isinstance(territory.get(field), expected_type):
            raise CapsuleError(f"territory.json : champ {field!r} manquant ou invalide")
    territory_id = territory["territory_id"]
    if not _IDENTIFIER_RE.fullmatch(territory_id):
        raise CapsuleError("territory_id contient des caractères non autorisés")
    bbox = territory["bbox"]
    if len(bbox) != 4 or any(
        isinstance(value, bool) or not isinstance(value, int | float) for value in bbox
    ):
        raise CapsuleError("territory.json : bbox doit contenir quatre nombres")
    min_x, min_y, max_x, max_y = (float(value) for value in bbox)
    if not (min_x < max_x and min_y < max_y):
        raise CapsuleError("territory.json : bbox est vide ou inversée")

    summary: dict[str, Any] = {
        "territory_id": territory_id,
        "name": territory["name"],
        "crs": territory["crs"],
        "bbox": [min_x, min_y, max_x, max_y],
        "synthetic": territory["synthetic"],
        "operational_use": territory["operational_use"],
    }
    for optional_field in ("data_classification", "license"):
        if optional_field in territory:
            if not isinstance(territory[optional_field], str):
                raise CapsuleError(f"territory.json : {optional_field} doit être une chaîne")
            summary[optional_field] = territory[optional_field]
    return summary


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename=name, date_time=_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def _manifest_id(manifest_without_id: dict[str, Any]) -> str:
    return f"cap_{hashlib.sha256(canonical_json(manifest_without_id)).hexdigest()[:32]}"


def build_capsule(
    source_dir: Path,
    output_path: Path,
    private_key_path: Path,
    *,
    created_at: datetime | None = None,
    valid_until: datetime | None = None,
    limits: CapsuleLimits | None = None,
) -> dict[str, Any]:
    """Construit une capsule déterministe pour un contenu, une date et une clé donnés."""

    effective_limits = limits or CapsuleLimits()
    source_dir = source_dir.resolve()
    if not source_dir.is_dir():
        raise CapsuleError(f"Source de capsule introuvable : {source_dir}")
    payload_root = (source_dir / "payload").resolve()
    if private_key_path.resolve().is_relative_to(payload_root):
        raise CapsuleError("La clé privée ne doit jamais se trouver dans le payload")
    if output_path.resolve().is_relative_to(payload_root):
        raise CapsuleError("La capsule de sortie ne doit pas écraser ou intégrer le payload")
    private_key = _load_private_key(private_key_path)
    public_key = private_key.public_key()
    key_id = _key_id(public_key)
    payload_files = _collect_payload(source_dir, effective_limits)
    territory = _territory_summary(source_dir, effective_limits)

    created = created_at or _utc_now()
    manifest_without_id: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at": _isoformat(created),
        "producer": {
            "name": "GSIE / Quintessences",
            "tool": "gsie-execution-kit",
            "tool_version": "0.1.0",
        },
        "territory": territory,
        "files": [
            {
                "path": item.archive_path,
                "size": item.size,
                "sha256": item.sha256,
            }
            for item in payload_files
        ],
        "signature": {
            "algorithm": SIGNATURE_ALGORITHM,
            "key_id": key_id,
        },
    }
    if valid_until is not None:
        if valid_until <= created:
            raise CapsuleError("valid_until doit être postérieur à created_at")
        manifest_without_id["valid_until"] = _isoformat(valid_until)

    manifest = {"capsule_id": _manifest_id(manifest_without_id), **manifest_without_id}
    manifest_bytes = canonical_json(manifest)
    signature_bytes = private_key.sign(manifest_bytes)
    signature_document = {
        "schema_version": SIGNATURE_SCHEMA_VERSION,
        "algorithm": SIGNATURE_ALGORITHM,
        "key_id": key_id,
        "signature_base64": base64.b64encode(signature_bytes).decode("ascii"),
    }
    signature_json = canonical_json(signature_document)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        with zipfile.ZipFile(
            temporary_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            strict_timestamps=True,
        ) as archive:
            archive.writestr(_zip_info(MANIFEST_NAME), manifest_bytes)
            archive.writestr(_zip_info(SIGNATURE_NAME), signature_json)
            for item in payload_files:
                data = item.source_path.read_bytes()
                observed_digest = hashlib.sha256(data).hexdigest()
                if len(data) != item.size or observed_digest != item.sha256:
                    raise CapsuleError(
                        f"Le fichier source a changé pendant la construction : {item.archive_path}"
                    )
                archive.writestr(_zip_info(f"{PAYLOAD_PREFIX}{item.archive_path}"), data)
        os.replace(temporary_path, output_path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise CapsuleError(f"Impossible de construire la capsule : {exc}") from exc
    finally:
        temporary_path.unlink(missing_ok=True)

    return {
        "capsule_id": manifest["capsule_id"],
        "schema_version": SCHEMA_VERSION,
        "output": str(output_path),
        "key_id": key_id,
        "territory_id": territory["territory_id"],
        "file_count": len(payload_files),
        "payload_bytes": sum(item.size for item in payload_files),
        "capsule_bytes": output_path.stat().st_size,
        "created_at": manifest["created_at"],
        "valid_until": manifest.get("valid_until"),
    }


def _read_metadata(archive: zipfile.ZipFile, name: str, limits: CapsuleLimits) -> bytes:
    try:
        info = archive.getinfo(name)
    except KeyError as exc:
        raise CapsuleError(f"Membre obligatoire absent : {name}") from exc
    if info.file_size > limits.max_metadata_bytes:
        raise CapsuleError(f"Métadonnée trop volumineuse : {name}")
    return archive.read(info)


def _validate_archive_budgets(infos: list[zipfile.ZipInfo], limits: CapsuleLimits) -> None:
    if len(infos) > limits.max_files + 2:
        raise CapsuleError(f"Archive trop riche en membres : {len(infos)}")
    total_size = 0
    for info in infos:
        _validate_relative_name(info.filename)
        if info.flag_bits & 0x1:
            raise CapsuleError(f"Membre ZIP chiffré non supporté : {info.filename}")
        if info.file_size > limits.max_member_uncompressed_bytes:
            raise CapsuleError(f"Membre trop volumineux : {info.filename}")
        total_size += info.file_size
        if total_size > limits.max_total_uncompressed_bytes + 2 * limits.max_metadata_bytes:
            raise CapsuleError("Archive trop volumineuse après décompression")
        ratio = info.file_size / max(info.compress_size, 1)
        if ratio > limits.max_compression_ratio:
            raise CapsuleError(f"Ratio de compression suspect pour {info.filename} : {ratio:.1f}")


def _validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    schema_version = manifest.get("schema_version")
    if not isinstance(schema_version, str) or schema_version.split(".", maxsplit=1)[0] != "1":
        raise CapsuleError(f"Version majeure de manifeste non supportée : {schema_version!r}")
    capsule_id = manifest.get("capsule_id")
    if not isinstance(capsule_id, str) or not capsule_id.startswith("cap_"):
        raise CapsuleError("capsule_id absent ou invalide")
    _parse_datetime(manifest.get("created_at"), "created_at")

    territory = manifest.get("territory")
    if not isinstance(territory, dict) or not isinstance(territory.get("territory_id"), str):
        raise CapsuleError("Résumé territorial absent ou invalide")
    signature = manifest.get("signature")
    if not isinstance(signature, dict):
        raise CapsuleError("Métadonnée de signature absente du manifeste")
    if signature.get("algorithm") != SIGNATURE_ALGORITHM:
        raise CapsuleError("Algorithme de signature non supporté")
    if not isinstance(signature.get("key_id"), str):
        raise CapsuleError("Identifiant de clé absent du manifeste")

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise CapsuleError("Liste de fichiers absente ou vide")
    normalized: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for raw_entry in files:
        if not isinstance(raw_entry, dict):
            raise CapsuleError("Entrée de fichier invalide dans le manifeste")
        path = raw_entry.get("path")
        size = raw_entry.get("size")
        digest = raw_entry.get("sha256")
        if not isinstance(path, str):
            raise CapsuleError("Chemin de fichier absent du manifeste")
        _validate_relative_name(path)
        if path in seen_paths:
            raise CapsuleError(f"Chemin dupliqué dans le manifeste : {path}")
        seen_paths.add(path)
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise CapsuleError(f"Taille invalide dans le manifeste : {path}")
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            raise CapsuleError(f"SHA-256 invalide dans le manifeste : {path}")
        normalized.append({"path": path, "size": size, "sha256": digest})
    if not any(entry["path"] == "territory.json" for entry in normalized):
        raise CapsuleError("territory.json n'est pas déclaré dans le manifeste")
    return normalized


def verify_capsule(
    capsule_path: Path,
    public_key_path: Path,
    *,
    now: datetime | None = None,
    limits: CapsuleLimits | None = None,
) -> dict[str, Any]:
    """Vérifie la confiance, l'intégrité et les budgets d'une capsule."""

    effective_limits = limits or CapsuleLimits()
    public_key = _load_public_key(public_key_path)
    trusted_key_id = _key_id(public_key)
    try:
        with zipfile.ZipFile(capsule_path, mode="r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                raise CapsuleError("L'archive contient des membres dupliqués")
            _validate_archive_budgets(infos, effective_limits)

            manifest_bytes = _read_metadata(archive, MANIFEST_NAME, effective_limits)
            signature_bytes = _read_metadata(archive, SIGNATURE_NAME, effective_limits)
            try:
                raw_manifest = loads_strict(manifest_bytes)
                raw_signature = loads_strict(signature_bytes)
            except StrictJsonError as exc:
                raise CapsuleError(str(exc)) from exc
            if not isinstance(raw_manifest, dict) or not isinstance(raw_signature, dict):
                raise CapsuleError("Le manifeste et la signature doivent être des objets JSON")
            manifest: dict[str, Any] = raw_manifest
            signature_document: dict[str, Any] = raw_signature
            if canonical_json(manifest) != manifest_bytes:
                raise CapsuleError("Le manifeste n'utilise pas la représentation canonique")
            if canonical_json(signature_document) != signature_bytes:
                raise CapsuleError("Le document de signature n'est pas canonique")

            files = _validate_manifest(manifest)
            manifest_without_id = dict(manifest)
            observed_capsule_id = manifest_without_id.pop("capsule_id")
            if observed_capsule_id != _manifest_id(manifest_without_id):
                raise CapsuleError("capsule_id ne correspond pas au contenu du manifeste")

            manifest_signature = manifest["signature"]
            if signature_document.get("schema_version") != SIGNATURE_SCHEMA_VERSION:
                raise CapsuleError("Version du document de signature non supportée")
            if signature_document.get("algorithm") != SIGNATURE_ALGORITHM:
                raise CapsuleError("Algorithme du document de signature non supporté")
            signed_key_id = signature_document.get("key_id")
            if signed_key_id != manifest_signature["key_id"]:
                raise CapsuleError("Les identifiants de clé du manifeste divergent")
            if signed_key_id != trusted_key_id:
                raise CapsuleError("La capsule n'est pas signée par la clé publique approuvée")
            encoded_signature = signature_document.get("signature_base64")
            if not isinstance(encoded_signature, str):
                raise CapsuleError("Signature Base64 absente")
            try:
                decoded_signature = base64.b64decode(encoded_signature, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise CapsuleError("Signature Base64 invalide") from exc
            try:
                public_key.verify(decoded_signature, manifest_bytes)
            except InvalidSignature as exc:
                raise CapsuleError("Signature cryptographique invalide") from exc

            expected_names = {
                MANIFEST_NAME,
                SIGNATURE_NAME,
                *(f"{PAYLOAD_PREFIX}{entry['path']}" for entry in files),
            }
            observed_names = set(names)
            unexpected = sorted(observed_names - expected_names)
            missing = sorted(expected_names - observed_names)
            if unexpected:
                raise CapsuleError(f"Membres non déclarés : {', '.join(unexpected)}")
            if missing:
                raise CapsuleError(f"Membres manquants : {', '.join(missing)}")

            total_payload = 0
            verified_files: list[dict[str, Any]] = []
            for entry in files:
                archive_name = f"{PAYLOAD_PREFIX}{entry['path']}"
                _validate_relative_name(archive_name, prefix_required=True)
                info = archive.getinfo(archive_name)
                if info.file_size != entry["size"]:
                    raise CapsuleError(f"Taille divergente : {entry['path']}")
                with archive.open(info, mode="r") as stream:
                    observed_digest, observed_size = _sha256_stream(stream)
                if observed_size != entry["size"] or observed_digest != entry["sha256"]:
                    raise CapsuleError(f"Empreinte divergente : {entry['path']}")
                total_payload += observed_size
                verified_files.append(
                    {
                        "path": entry["path"],
                        "size": observed_size,
                        "sha256": observed_digest,
                    }
                )

            checked_at = (now or _utc_now()).astimezone(UTC)
            valid_until_value = manifest.get("valid_until")
            if valid_until_value is not None:
                expiration = _parse_datetime(valid_until_value, "valid_until")
                if checked_at > expiration:
                    raise CapsuleError(f"Capsule expirée depuis {_isoformat(expiration)}")

            territory = manifest["territory"]
            return {
                "valid": True,
                "checked_at": _isoformat(checked_at),
                "capsule_id": manifest["capsule_id"],
                "schema_version": manifest["schema_version"],
                "key_id": trusted_key_id,
                "signature": "valid",
                "territory": territory,
                "file_count": len(verified_files),
                "payload_bytes": total_payload,
                "files": verified_files,
            }
    except FileNotFoundError as exc:
        raise CapsuleError(f"Capsule introuvable : {capsule_path}") from exc
    except zipfile.BadZipFile as exc:
        raise CapsuleError(f"Conteneur ZIP invalide : {capsule_path}") from exc

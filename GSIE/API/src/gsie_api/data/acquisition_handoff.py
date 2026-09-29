"""Contrat et matérialisation du handoff Forge → Data Registry GSIE.

Le manifeste imbriqué réutilise ``DatasetManifest``. Le handoff n'ajoute pas
de Registry concurrent : il transporte seulement la preuve d'une archive
locale produite par Forge afin que GSIE puisse la vérifier, l'archiver dans
ObjectStorage et appliquer le manifeste existant.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime  # noqa: TC003 - Pydantic résout ce type au runtime
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Literal, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from gsie_api.data.contracts import normalize_slug
from gsie_api.data.fetch_sink import TransactionalObjectStorageSink
from gsie_api.ingestion.manifest import DatasetManifest, ManifestOperation

if TYPE_CHECKING:
    from gsie_api.data.manifest_application import ManifestAssetInput
    from gsie_api.infrastructure.object_storage import ObjectStorage

HandoffSchemaVersion = Literal["gsie_acquisition_handoff.v1"]
HANDOFF_SCHEMA_VERSION: HandoffSchemaVersion = "gsie_acquisition_handoff.v1"
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_FORMAT = re.compile(r"^[a-z0-9][a-z0-9._-]{0,49}$")
_CHUNK_SIZE = 1024 * 1024


class AcquisitionHandoffError(ValueError):
    """Handoff incohérent, archive absente ou preuve divergente."""


def _https_url(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    parsed = urlsplit(normalized)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{field_name} doit être une URL HTTPS sans identifiant ni paramètres")
    return normalized


def _relative_path(value: str) -> str:
    normalized = value.strip()
    if not normalized or "\\" in normalized:
        raise ValueError("relative_path doit utiliser un chemin POSIX relatif")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("relative_path ne doit pas sortir du dossier de staging")
    if path.as_posix() != normalized:
        raise ValueError("relative_path doit être normalisé")
    return normalized


class AcquisitionArtifact(BaseModel):
    """Preuve d'un artefact brut placé dans le staging Forge."""

    model_config = ConfigDict(extra="forbid")

    dataset_slug: str = Field(min_length=1, max_length=200)
    kind: Literal["raw"] = "raw"
    relative_path: str = Field(min_length=1, max_length=500)
    format: str = Field(min_length=1, max_length=50)
    content_type: str = Field(min_length=1, max_length=200)
    size_bytes: int = Field(gt=0)
    checksum: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    checksum_algorithm: Literal["sha256"] = "sha256"
    original_uri: str = Field(min_length=1, max_length=500)
    archived_at: datetime

    @field_validator("dataset_slug")
    @classmethod
    def normalize_dataset_slug(cls, value: str) -> str:
        return normalize_slug(value)

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        return _relative_path(value)

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _FORMAT.fullmatch(normalized):
            raise ValueError("format d'artefact invalide")
        return normalized

    @field_validator("content_type")
    @classmethod
    def normalize_content_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("content_type obligatoire")
        return normalized

    @field_validator("checksum")
    @classmethod
    def normalize_checksum(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("original_uri")
    @classmethod
    def validate_original_uri(cls, value: str) -> str:
        return _https_url(value, field_name="original_uri")

    @field_validator("archived_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("archived_at doit être horodaté avec un fuseau")
        return value


class AcquisitionHandoff(BaseModel):
    """Document versionné de passage entre Forge et GSIE."""

    model_config = ConfigDict(extra="forbid")

    schema_version: HandoffSchemaVersion = HANDOFF_SCHEMA_VERSION
    generated_at: datetime
    producer: str = Field(min_length=1, max_length=100)
    producer_version: str = Field(min_length=1, max_length=50)
    adapter_key: str = Field(min_length=1, max_length=100)
    pipeline_id: str = Field(min_length=1, max_length=200)
    manifest: DatasetManifest
    artifacts: list[AcquisitionArtifact] = Field(min_length=1, max_length=500)

    @field_validator("generated_at")
    @classmethod
    def require_generated_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("generated_at doit être horodaté avec un fuseau")
        return value

    @field_validator("adapter_key")
    @classmethod
    def normalize_adapter_key(cls, value: str) -> str:
        return normalize_slug(value)

    @model_validator(mode="after")
    def validate_artifact_mapping(self) -> Self:
        entries = {entry.slug: entry for entry in self.manifest.entries}
        artifacts: dict[str, AcquisitionArtifact] = {}
        for artifact in self.artifacts:
            if artifact.dataset_slug in artifacts:
                raise ValueError(f"artefact brut dupliqué pour {artifact.dataset_slug}")
            artifacts[artifact.dataset_slug] = artifact
        if set(entries) != set(artifacts):
            raise ValueError("les artefacts doivent couvrir exactement les entrées du manifeste")
        for slug, entry in entries.items():
            if entry.operation is not ManifestOperation.archive_copy:
                raise ValueError(f"{slug} exige operation=archive_copy dans un handoff")
        return self


@dataclass(frozen=True, slots=True)
class MaterializedAcquisitionAsset:
    """Actif GSIE prêt pour ``ManifestRegistryService.apply``."""

    dataset_slug: str
    asset: ManifestAssetInput
    storage_key: str
    created: bool


def load_acquisition_handoff(path: str | Path) -> AcquisitionHandoff:
    """Charge et valide un handoff sans réseau ni écriture."""

    handoff_path = Path(path)
    try:
        payload = json.loads(handoff_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise AcquisitionHandoffError(f"Impossible de lire le handoff {handoff_path}") from exc
    except json.JSONDecodeError as exc:
        raise AcquisitionHandoffError(
            f"JSON de handoff invalide à la ligne {exc.lineno}"
        ) from exc
    if not isinstance(payload, dict):
        raise AcquisitionHandoffError("le handoff JSON doit être un objet")
    try:
        return AcquisitionHandoff.model_validate(payload)
    except ValueError as exc:
        raise AcquisitionHandoffError(f"handoff non conforme : {exc}") from exc


def _resolve_staged_path(staging_root: Path, relative_path: str) -> Path:
    root = staging_root.resolve()
    candidate = (root / Path(*PurePosixPath(relative_path).parts)).resolve()
    if candidate == root or not candidate.is_relative_to(root):
        raise AcquisitionHandoffError("l'artefact sort du dossier de staging")
    if not candidate.is_file():
        raise AcquisitionHandoffError(f"artefact staging introuvable : {relative_path}")
    return candidate


def _file_evidence(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


async def _stored_evidence(storage: ObjectStorage, key: str) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    async for chunk in storage.iter_chunks(key, chunk_size=_CHUNK_SIZE):
        if not chunk:
            raise AcquisitionHandoffError("le stockage a fourni un bloc vide")
        size += len(chunk)
        digest.update(chunk)
    return size, digest.hexdigest()


def _storage_key(artifact: AcquisitionArtifact) -> str:
    return (
        f"raw/fetch/forge/{normalize_slug(artifact.dataset_slug)}/"
        f"{artifact.checksum}.{artifact.format}"
    )


async def materialize_handoff_assets(
    handoff: AcquisitionHandoff,
    *,
    staging_root: str | Path,
    storage: ObjectStorage,
    archive: bool,
) -> dict[str, MaterializedAcquisitionAsset]:
    """Vérifie les artefacts et les archive de façon idempotente si demandé."""

    from gsie_api.data.manifest_application import ManifestAssetInput

    root = Path(staging_root)
    materialized: dict[str, MaterializedAcquisitionAsset] = {}
    for artifact in handoff.artifacts:
        source_path = _resolve_staged_path(root, artifact.relative_path)
        size, checksum = await asyncio.to_thread(_file_evidence, source_path)
        if (size, checksum) != (artifact.size_bytes, artifact.checksum):
            raise AcquisitionHandoffError(
                f"preuve divergente pour {artifact.dataset_slug} : taille/checksum"
            )

        key = _storage_key(artifact)
        created = False
        if archive:
            if await storage.exists(key):
                stored_size, stored_checksum = await _stored_evidence(storage, key)
                if (stored_size, stored_checksum) != (size, checksum):
                    raise AcquisitionHandoffError(
                        f"objet existant divergent pour {artifact.dataset_slug}"
                    )
            else:
                sink = TransactionalObjectStorageSink(
                    storage,
                    final_key=key,
                    content_type=artifact.content_type,
                    spool_max_bytes=min(max(size, 1), 8 * 1024 * 1024),
                )
                try:
                    with source_path.open("rb") as handle:
                        while chunk := await asyncio.to_thread(handle.read, _CHUNK_SIZE):
                            await sink.write(chunk)
                    await sink.commit()
                    created = True
                except BaseException:
                    await sink.abort()
                    raise

        materialized[artifact.dataset_slug] = MaterializedAcquisitionAsset(
            dataset_slug=artifact.dataset_slug,
            asset=ManifestAssetInput(
                format=artifact.format,
                size_bytes=size,
                checksum=checksum,
                checksum_algorithm=artifact.checksum_algorithm,
                storage_uri=storage.uri_for_key(key),
                original_uri=artifact.original_uri,
                archived_at=artifact.archived_at,
            ),
            storage_key=key,
            created=created,
        )
    return materialized


__all__ = [
    "AcquisitionArtifact",
    "AcquisitionHandoff",
    "AcquisitionHandoffError",
    "HANDOFF_SCHEMA_VERSION",
    "MaterializedAcquisitionAsset",
    "load_acquisition_handoff",
    "materialize_handoff_assets",
]

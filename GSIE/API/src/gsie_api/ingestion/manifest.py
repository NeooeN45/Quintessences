"""Manifeste déterministe des datasets GSIE.

Le manifeste est une porte de qualification avant toute écriture en base ou
tout téléchargement. Il ne contacte aucun fournisseur et ne copie aucun
octet. Il rassemble uniquement les métadonnées nécessaires à la prochaine
tranche d'ingestion, en réutilisant le registre juridique SCI-001 comme
source de vérité.

Deux opérations sont explicites :

``metadata_only``
    Enregistrer un lien et des métadonnées, sans copier le contenu. Ce mode
    reste possible pour une source sous restriction ou en revue juridique.

``archive_copy``
    Préparer une copie contrôlée. Ce mode est fermé par
    ``require_ingestible`` et ne peut donc être utilisé que pour une source
    ``OPEN_COPY``.

Le fichier est volontairement indépendant de SQLAlchemy. La persistance fera
l'objet d'une étape ultérieure, après validation du manifeste et attribution
des identifiants de provenance.
"""

from __future__ import annotations

import json
from enum import StrEnum
from ipaddress import ip_address
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from gsie_api.data.contracts import normalize_keywords, normalize_slug, validate_domain
from gsie_api.governance.source_registry import (
    SourceIngestionForbiddenError,
    get_source,
    require_ingestible,
)
from gsie_api.infrastructure.models.enums import AccessMethod, DatasetPurpose, DatasetStatus

MANIFEST_VERSION = "1"
_MAX_ENTRIES = 500
_MAX_URL_LENGTH = 500


class ManifestOperation(StrEnum):
    """Action autorisée par le manifeste, avant l'implémentation du worker."""

    metadata_only = "metadata_only"
    archive_copy = "archive_copy"


class ManifestDistribution(BaseModel):
    """Canal d'accès déclaré pour une entrée du manifeste."""

    model_config = ConfigDict(extra="forbid")

    access_method: AccessMethod
    access_url: str
    licence: str = Field(min_length=1, max_length=200)
    format: str | None = Field(default=None, max_length=50)
    offline_pack: bool = False

    @field_validator("access_url")
    @classmethod
    def validate_access_url(cls, value: str) -> str:
        """Refuse les URLs qui pourraient introduire un secret ou un SSRF."""

        value = value.strip()
        if len(value) > _MAX_URL_LENGTH:
            raise ValueError(f"access_url dépasse {_MAX_URL_LENGTH} caractères")
        try:
            parsed = urlsplit(value)
        except ValueError as exc:
            raise ValueError("access_url est une URL malformée") from exc
        if parsed.scheme.lower() != "https" or not parsed.hostname:
            raise ValueError("access_url doit utiliser HTTPS et indiquer un hôte")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("access_url ne doit pas contenir d'identifiants")
        if parsed.query or parsed.fragment:
            raise ValueError("access_url ne doit pas contenir de query ou fragment")
        # Une adresse IP littérale privée ou locale n'est jamais une source de
        # registre. Les noms DNS restent soumis à l'allowlist de l'adapter au
        # moment de l'appel réseau.
        try:
            address = ip_address(parsed.hostname)
        except ValueError:
            address = None
        if address is not None and (
            address.is_private or address.is_loopback or address.is_link_local
        ):
            raise ValueError("access_url ne peut pas cibler une adresse privée ou locale")
        return value

    @field_validator("licence")
    @classmethod
    def normalize_licence(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("licence obligatoire : une URL seule ne suffit pas")
        return value

    @field_validator("format")
    @classmethod
    def normalize_format(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower()
        return value or None


class DatasetManifestEntry(BaseModel):
    """Entrée normalisée et juridiquement qualifiée d'un dataset."""

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=10_000)
    source_registry_id: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=50)
    primary_domain: str
    domains: list[str] = Field(default_factory=list, max_length=20)
    tags: list[str] = Field(default_factory=list, max_length=50)
    purpose: DatasetPurpose = DatasetPurpose.reference
    status: DatasetStatus = DatasetStatus.discovered
    operation: ManifestOperation = ManifestOperation.metadata_only
    release_date: str | None = Field(default=None, max_length=50)
    changes: str | None = Field(default=None, max_length=10_000)
    schema_hash: str | None = Field(default=None, max_length=128)
    stats: dict[str, Any] | None = None
    distribution: ManifestDistribution

    @field_validator("slug")
    @classmethod
    def normalize_dataset_slug(cls, value: str) -> str:
        return normalize_slug(value)

    @field_validator("title", "description", "version", "source_registry_id")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ce champ ne peut pas être vide")
        return value

    @field_validator("primary_domain")
    @classmethod
    def normalize_primary_domain(cls, value: str) -> str:
        return validate_domain(value)

    @field_validator("domains")
    @classmethod
    def normalize_domains(cls, values: list[str]) -> list[str]:
        normalized = [validate_domain(value) for value in values]
        if len(set(normalized)) != len(normalized):
            raise ValueError("domains ne doit pas contenir de doublon")
        return normalized

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        return normalize_keywords(values)

    @model_validator(mode="after")
    def validate_contract(self) -> DatasetManifestEntry:
        """Applique les règles croisées avant toute persistance."""

        if self.primary_domain in self.domains:
            raise ValueError("primary_domain ne doit pas être répété dans domains")

        source = get_source(self.source_registry_id)
        if source is None:
            raise ValueError(f"Source '{self.source_registry_id}' absente du registre SCI-001")
        if self.distribution.licence != source.licence:
            raise ValueError(
                "distribution.licence doit reprendre exactement la licence du registre "
                f"SCI-001 ({source.licence})"
            )

        if self.status in {
            DatasetStatus.production,
            DatasetStatus.staging,
            DatasetStatus.validated,
        }:
            raise ValueError(
                "un manifeste ne peut pas promouvoir un dataset : utilisez discovered, "
                "metadata_extracted ou un statut de qualification déjà approuvé"
            )

        if self.operation is ManifestOperation.archive_copy:
            try:
                require_ingestible(self.source_registry_id)
            except SourceIngestionForbiddenError as exc:
                raise ValueError(str(exc)) from exc
        if self.distribution.offline_pack:
            if self.operation is not ManifestOperation.archive_copy:
                raise ValueError("offline_pack exige operation=archive_copy")
            if not source.droit_redistribution_offline:
                raise ValueError(
                    "offline_pack interdit par le registre juridique pour cette source"
                )
        return self


class DatasetManifest(BaseModel):
    """Document complet de catalogue/ingestion, versionné et rejouable."""

    model_config = ConfigDict(extra="forbid")

    manifest_version: str = MANIFEST_VERSION
    generated_at: str | None = Field(default=None, max_length=50)
    entries: list[DatasetManifestEntry] = Field(min_length=1, max_length=_MAX_ENTRIES)

    @field_validator("manifest_version")
    @classmethod
    def validate_manifest_version(cls, value: str) -> str:
        if value != MANIFEST_VERSION:
            raise ValueError(f"version de manifeste inconnue : {value}")
        return value

    @model_validator(mode="after")
    def validate_unique_identity(self) -> DatasetManifest:
        seen: set[tuple[str, str]] = set()
        for entry in self.entries:
            identity = (entry.slug, entry.version)
            if identity in seen:
                raise ValueError(
                    f"doublon de dataset/version dans le manifeste : {entry.slug}@{entry.version}"
                )
            seen.add(identity)
        return self


def load_manifest(path: str | Path) -> DatasetManifest:
    """Charge un manifeste JSON local sans jamais ouvrir d'URL."""

    manifest_path = Path(path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Impossible de lire le manifeste {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON de manifeste invalide à la ligne {exc.lineno}") from exc
    if not isinstance(payload, dict):
        raise ValueError("le manifeste JSON doit être un objet")
    return DatasetManifest.model_validate(payload)


def manifest_preview(manifest: DatasetManifest) -> list[dict[str, object]]:
    """Produit un aperçu stable pour le CLI et la future ingestion DB."""

    preview: list[dict[str, object]] = []
    for entry in manifest.entries:
        source = get_source(entry.source_registry_id)
        if source is None:  # défense en profondeur si le registre change en mémoire
            raise ValueError(f"Source absente du registre : {entry.source_registry_id}")
        preview.append(
            {
                "slug": entry.slug,
                "version": entry.version,
                "title": entry.title,
                "source_registry_id": entry.source_registry_id,
                "publisher": source.organisme,
                "operation": entry.operation.value,
                "status": entry.status.value,
                "licence": entry.distribution.licence,
                "access_method": entry.distribution.access_method.value,
                "access_url": entry.distribution.access_url,
                "offline_pack": entry.distribution.offline_pack,
            }
        )
    return preview

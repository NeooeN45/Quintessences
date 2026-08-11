"""Application transactionnelle du manifeste Data Registry (RFC-0038).

Cette façade assemble les projections du manifeste dans le métamodèle v6.2 :
``Agent``/``Source``/``EntityAlias``, ``Dataset``, ``DatasetVersion``,
``DataRightsStatement``, ``Distribution`` et ``Citation``. Elle ne contacte
aucune URL de fournisseur. Les octets ne sont acceptés que lorsqu'un appelant
leur fournit déjà un actif archivé, son URI de stockage et son empreinte.

Le service ne valide pas de transition implicite et n'écrase pas les champs
immuables d'une version publiée. L'appelant garde la transaction : le CLI,
un worker ou un endpoint doit ouvrir une transaction et la valider après le
rapport d'application.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select

from gsie_api.data.contracts import DOMAIN_VOCABULARY_VERSION
from gsie_api.data.lifecycle import transition_status
from gsie_api.governance.source_registry import get_source
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.enums import (
    AgentType,
    CitationRole,
    DatasetHealthStatus,
    SourceNature,
    SourceSubtype,
    UsageRights,
)
from gsie_api.infrastructure.models.governance import (
    DataRightsStatementModel,
    DatasetHealthModel,
)
from gsie_api.infrastructure.models.models_ai import (
    DataAssetModel,
    DatasetModel,
    DatasetVersionModel,
    DistributionModel,
)
from gsie_api.infrastructure.models.prov import (
    AgentModel,
    CitationModel,
    SourceModel,
)
from gsie_api.infrastructure.models.provenance import EntityAliasModel
from gsie_api.ingestion.manifest import (
    DatasetManifest,
    DatasetManifestEntry,
    ManifestOperation,
)
from gsie_api.resources.service import ResourceService

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sqlalchemy.ext.asyncio import AsyncSession

    from gsie_api.governance.source_registry import ScientificSourceEntry


class ManifestApplicationError(ValueError):
    """Erreur de cohérence empêchant l'application du manifeste."""


class ManifestApplyAction(StrEnum):
    """Action observée pour une entrée du manifeste."""

    created = "created"
    updated = "updated"
    unchanged = "unchanged"


class ManifestHealthSnapshot(BaseModel):
    """Observation de santé fournie par un adapter ou un job de contrôle.

    Le snapshot est volontairement séparé de l'appel réseau : un adapter
    produit cette structure, puis l'application du manifeste la persiste.
    """

    model_config = ConfigDict(extra="forbid")

    checked_at: datetime
    health_status: DatasetHealthStatus
    http_status: int | None = Field(default=None, ge=100, le=599)
    latency_ms: float | None = Field(default=None, ge=0)
    last_modified: datetime | None = None
    observed_version: str | None = Field(default=None, max_length=200)
    schema_hash: str | None = Field(default=None, max_length=128)
    checksum_verified: bool | None = None
    error_code: str | None = Field(default=None, max_length=100)

    @field_validator("checked_at", "last_modified")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        """Refuse une observation dont l'instant serait ambigu."""

        if value is not None and value.tzinfo is None:
            raise ValueError("un contrôle de santé doit être horodaté avec un fuseau")
        return value


class ManifestAssetInput(BaseModel):
    """Actif déjà archivé dans MinIO/S3, prêt à être référencé."""

    model_config = ConfigDict(extra="forbid")

    format: str = Field(min_length=1, max_length=50)
    size_bytes: int = Field(ge=0)
    checksum: str = Field(min_length=1, max_length=200)
    checksum_algorithm: str = Field(default="sha256", min_length=1, max_length=50)
    storage_uri: str = Field(min_length=1, max_length=500)
    original_uri: str | None = Field(default=None, max_length=500)
    archived_at: datetime
    archived_from: UUID | None = None

    @field_validator("format", "checksum_algorithm")
    @classmethod
    def normalize_short_text(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("ce champ ne peut pas être vide")
        return value

    @field_validator("checksum")
    @classmethod
    def normalize_checksum(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("checksum obligatoire")
        return value

    @field_validator("storage_uri")
    @classmethod
    def validate_storage_uri(cls, value: str) -> str:
        """Accepte uniquement une URI S3 ou locale de développement."""

        value = value.strip()
        parsed = urlsplit(value)
        if parsed.scheme == "s3":
            if not parsed.netloc or parsed.username or parsed.password:
                raise ValueError("storage_uri S3 doit avoir un bucket sans identifiants")
        elif parsed.scheme == "local":
            if not parsed.path:
                raise ValueError("storage_uri local doit contenir un chemin")
        else:
            raise ValueError("storage_uri doit utiliser s3:// ou local://")
        if parsed.query or parsed.fragment:
            raise ValueError("storage_uri ne doit pas contenir de query ou fragment")
        return value

    @field_validator("archived_at")
    @classmethod
    def require_archive_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("archived_at doit être horodaté avec un fuseau")
        return value


@dataclass(frozen=True, slots=True)
class ManifestApplyItem:
    """Résultat détaillé d'une entrée appliquée."""

    slug: str
    version: str
    action: ManifestApplyAction
    resources: dict[str, str]
    notes: tuple[str, ...] = ()
    created_resources: int = 0
    updated_resources: int = 0
    health_created: bool = False
    asset_created: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "slug": self.slug,
            "version": self.version,
            "action": self.action.value,
            "resources": dict(self.resources),
            "notes": list(self.notes),
            "created_resources": self.created_resources,
            "updated_resources": self.updated_resources,
            "health_created": self.health_created,
            "asset_created": self.asset_created,
        }


@dataclass(frozen=True, slots=True)
class ManifestApplyReport:
    """Rapport stable utilisable par le CLI, un job ou une API interne."""

    manifest_version: str
    dry_run: bool
    items: tuple[ManifestApplyItem, ...]

    @property
    def created(self) -> int:
        return sum(item.created_resources for item in self.items)

    @property
    def updated(self) -> int:
        return sum(item.updated_resources for item in self.items)

    @property
    def health_created(self) -> int:
        return sum(item.health_created for item in self.items)

    @property
    def assets_created(self) -> int:
        return sum(item.asset_created for item in self.items)

    def as_dict(self) -> dict[str, object]:
        return {
            "manifest_version": self.manifest_version,
            "dry_run": self.dry_run,
            "entries": len(self.items),
            "created_resources": self.created,
            "updated_resources": self.updated,
            "health_created": self.health_created,
            "assets_created": self.assets_created,
            "items": [item.as_dict() for item in self.items],
        }


@dataclass(slots=True)
class _ResourceResult:
    resource: ResourceModel
    typed: Any
    created: bool
    changes: list[dict[str, object]] = field(default_factory=list)


_REGISTRY_NAMESPACE = "scientific_source_registry"
_IMMUTABLE_VERSION_FIELDS = frozenset(
    {"dataset_id", "version", "release_date", "changes", "stats", "schema_hash"}
)
_IMMUTABLE_ASSET_FIELDS = frozenset(
    {
        "dataset_version_id",
        "format",
        "size_bytes",
        "checksum",
        "checksum_algorithm",
        "storage_uri",
        "archived_at",
    }
)
_IMMUTABLE_HEALTH_FIELDS = frozenset(
    {
        "dataset_version_id",
        "distribution_id",
        "checked_at",
        "health_status",
        "http_status",
        "latency_ms",
        "last_modified",
        "observed_version",
        "schema_hash",
        "checksum_verified",
        "error_code",
    }
)


def _stable_gsie_id(type_name: str, identity: str) -> str:
    """Construit un identifiant stable sous la limite de ``resource.gsie_id``."""

    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]
    return f"registry:{type_name}:{digest}"


def _planned_uuid(gsie_id: str) -> UUID:
    """Retourne un UUID déterministe pour les références d'un dry-run."""

    return uuid5(NAMESPACE_URL, f"https://quintessences.local/registry/{gsie_id}")


def _parse_release_date(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.combine(date.fromisoformat(normalized), datetime.min.time())
        except ValueError as exc:
            raise ManifestApplicationError(
                f"release_date invalide pour le manifeste : {value!r}"
            ) from exc
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _as_metadata(entry: DatasetManifestEntry, manifest: DatasetManifest) -> dict[str, object]:
    return {
        "registry": "data_registry",
        "manifest_version": manifest.manifest_version,
        "manifest_generated_at": manifest.generated_at,
        "manifest_slug": entry.slug,
        "manifest_dataset_version": entry.version,
        "source_registry_id": entry.source_registry_id,
        "operation": entry.operation.value,
    }


class ManifestRegistryService:
    """Projection applicative idempotente du manifeste vers PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._resource_service = ResourceService(session)

    async def apply(
        self,
        manifest: DatasetManifest,
        *,
        dry_run: bool = True,
        health_reports: Mapping[str, ManifestHealthSnapshot] | None = None,
        assets: Mapping[str, ManifestAssetInput] | None = None,
    ) -> ManifestApplyReport:
        """Prévisualise ou applique le manifeste dans la transaction courante.

        ``health_reports`` et ``assets`` sont indexés par ``slug``. Pour une
        compatibilité opérateur, l'identifiant ``source_registry_id`` est
        aussi accepté lorsqu'il est unique dans le manifeste.
        """

        health_reports = health_reports or {}
        assets = assets or {}
        self._validate_inputs(manifest, health_reports, assets)
        items: list[ManifestApplyItem] = []
        source_occurrences = _source_occurrences(manifest)
        for entry in manifest.entries:
            items.append(
                await self._apply_entry(
                    manifest,
                    entry,
                    dry_run=dry_run,
                    health_snapshot=_lookup_by_slug_or_source(
                        health_reports, entry, source_occurrences
                    ),
                    asset=_lookup_by_slug_or_source(assets, entry, source_occurrences),
                )
            )
        return ManifestApplyReport(manifest.manifest_version, dry_run, tuple(items))

    @staticmethod
    def _validate_inputs(
        manifest: DatasetManifest,
        health_reports: Mapping[str, ManifestHealthSnapshot],
        assets: Mapping[str, ManifestAssetInput],
    ) -> None:
        source_occurrences = _source_occurrences(manifest)
        valid_keys = {entry.slug for entry in manifest.entries}
        valid_keys.update(
            entry.source_registry_id
            for entry in manifest.entries
            if source_occurrences[entry.source_registry_id] == 1
        )
        unknown_health = set(health_reports).difference(valid_keys)
        unknown_assets = set(assets).difference(valid_keys)
        if unknown_health:
            raise ManifestApplicationError(
                "Contrôles de santé sans entrée de manifeste : " + ", ".join(sorted(unknown_health))
            )
        if unknown_assets:
            raise ManifestApplicationError(
                "Actifs sans entrée de manifeste : " + ", ".join(sorted(unknown_assets))
            )
        for entry in manifest.entries:
            asset = _lookup_by_slug_or_source(assets, entry, source_occurrences)
            if entry.operation is ManifestOperation.archive_copy and asset is None:
                raise ManifestApplicationError(
                    f"{entry.slug}@{entry.version} exige un actif archivé "
                    "pour operation=archive_copy"
                )
            if entry.operation is ManifestOperation.metadata_only and asset is not None:
                raise ManifestApplicationError(
                    f"{entry.slug}@{entry.version} est metadata_only : "
                    "aucun actif ne peut être associé sans passer à archive_copy"
                )

    async def _apply_entry(
        self,
        manifest: DatasetManifest,
        entry: DatasetManifestEntry,
        *,
        dry_run: bool,
        health_snapshot: ManifestHealthSnapshot | None,
        asset: ManifestAssetInput | None,
    ) -> ManifestApplyItem:
        source = _source_for_entry(entry)
        metadata = _as_metadata(entry, manifest)
        source_metadata = {
            "registry": "data_registry",
            "manifest_version": manifest.manifest_version,
            "source_registry_id": entry.source_registry_id,
        }
        resources: dict[str, str] = {}
        notes: list[str] = []
        created = 0
        updated = 0
        health_created = False
        asset_created = False

        agent_id = _stable_gsie_id("agent", entry.source_registry_id)
        agent = await self._ensure(
            "agent",
            agent_id,
            AgentModel,
            {"name": source.organisme, "type": AgentType.organisation},
            {**source_metadata, "scientific_source": source.model_dump(mode="json")},
            dry_run=dry_run,
        )
        resources["agent"] = str(agent.resource.id)
        created, updated = _counts(agent, created, updated)

        source_id = _stable_gsie_id("source", entry.source_registry_id)
        source_result = await self._ensure(
            "source",
            source_id,
            SourceModel,
            {
                "title": f"{source.organisme} — {entry.source_registry_id}",
                "subtype": SourceSubtype.api,
                "source_nature": SourceNature.data_provider,
                "auteur": source.organisme,
                "date_publication": source.version_ou_date,
                "url": source.url,
                "licence": source.licence,
            },
            {**source_metadata, "scientific_source": source.model_dump(mode="json")},
            dry_run=dry_run,
        )
        resources["source"] = str(source_result.resource.id)
        created, updated = _counts(source_result, created, updated)

        alias = await self._ensure(
            "entity_alias",
            _stable_gsie_id("entity_alias", entry.source_registry_id),
            EntityAliasModel,
            {
                "entity_id": source_result.resource.id,
                "namespace": _REGISTRY_NAMESPACE,
                "external_id": entry.source_registry_id,
                "external_url": source.url,
            },
            {**source_metadata, "alias_target_type": "source"},
            dry_run=dry_run,
            immutable_fields=frozenset({"entity_id", "namespace", "external_id"}),
        )
        resources["entity_alias"] = str(alias.resource.id)
        created, updated = _counts(alias, created, updated)

        rights = await self._ensure(
            "data_rights_statement",
            _stable_gsie_id("data_rights_statement", entry.source_registry_id),
            DataRightsStatementModel,
            {
                "licence": source.licence,
                "usage_rights": _usage_rights(source.mode_ingestion.value),
                "commercial_use_allowed": source.usage_commercial_autorise is True,
                "redistribution_allowed": source.droit_redistribution_offline is True,
                "attribution_required": source.attribution_requise is not None,
                # L'indexation n'est pas une autorisation implicite
                # d'entraînement : seul un consentement explicite pourra
                # passer ce champ à True lors de la revue juridique.
                "ai_training_allowed": False,
                "notes": _rights_notes(source),
            },
            {**source_metadata, "scientific_source": source.model_dump(mode="json")},
            dry_run=dry_run,
        )
        resources["data_rights_statement"] = str(rights.resource.id)
        created, updated = _counts(rights, created, updated)

        dataset = await self._ensure(
            "dataset",
            _stable_gsie_id("dataset", entry.slug),
            DatasetModel,
            {
                "title": entry.title,
                "description": entry.description,
                "publisher_id": agent.resource.id,
                "topic": entry.primary_domain,
                "purpose": entry.purpose,
                "slug": entry.slug,
                "primary_domain": entry.primary_domain,
                "domains": list(entry.domains),
                "tags": list(entry.tags),
                "domain_vocabulary_version": DOMAIN_VOCABULARY_VERSION,
            },
            metadata,
            dry_run=dry_run,
        )
        resources["dataset"] = str(dataset.resource.id)
        created, updated = _counts(dataset, created, updated)

        release_date = _parse_release_date(entry.release_date)
        version = await self._ensure(
            "dataset_version",
            _stable_gsie_id("dataset_version", f"{entry.slug}@{entry.version}"),
            DatasetVersionModel,
            {
                "dataset_id": dataset.resource.id,
                "version": entry.version,
                "release_date": release_date,
                "changes": entry.changes,
                "stats": dict(entry.stats) if entry.stats is not None else None,
                "schema_hash": entry.schema_hash,
                "status": entry.status,
            },
            metadata,
            dry_run=dry_run,
            immutable_fields=_IMMUTABLE_VERSION_FIELDS,
            status_target=entry.status,
            notes=notes,
        )
        resources["dataset_version"] = str(version.resource.id)
        created, updated = _counts(version, created, updated)

        distribution = await self._ensure(
            "distribution",
            _stable_gsie_id(
                "distribution",
                f"{entry.slug}@{entry.version}:{entry.source_registry_id}:"
                f"{entry.distribution.access_method.value}",
            ),
            DistributionModel,
            {
                "dataset_version_id": version.resource.id,
                "access_method": entry.distribution.access_method,
                "access_url": entry.distribution.access_url,
                "licence": entry.distribution.licence,
                "data_rights_statement_id": rights.resource.id,
                "format": entry.distribution.format,
            },
            {**metadata, "offline_pack": entry.distribution.offline_pack},
            dry_run=dry_run,
            immutable_fields=frozenset({"dataset_version_id"}),
        )
        resources["distribution"] = str(distribution.resource.id)
        created, updated = _counts(distribution, created, updated)

        citation = await self._ensure(
            "citation",
            _stable_gsie_id("citation", f"{entry.slug}@{entry.version}:{entry.source_registry_id}"),
            CitationModel,
            {
                "source_id": source_result.resource.id,
                "target_id": version.resource.id,
                "citation_role": CitationRole.primary,
                "locator": entry.version,
            },
            metadata,
            dry_run=dry_run,
            immutable_fields=frozenset({"source_id", "target_id", "citation_role"}),
        )
        resources["citation"] = str(citation.resource.id)
        created, updated = _counts(citation, created, updated)

        if asset is not None:
            asset_result = await self._ensure(
                "data_asset",
                _stable_gsie_id(
                    "data_asset",
                    f"{entry.slug}@{entry.version}:{asset.format}:"
                    f"{asset.checksum}:{asset.storage_uri}",
                ),
                DataAssetModel,
                {
                    "dataset_version_id": version.resource.id,
                    "format": asset.format,
                    "size_bytes": asset.size_bytes,
                    "checksum": asset.checksum,
                    "archived_from": asset.archived_from,
                    "original_uri": asset.original_uri or entry.distribution.access_url,
                    "storage_uri": asset.storage_uri,
                    "checksum_algorithm": asset.checksum_algorithm,
                    "archived_at": asset.archived_at,
                },
                {**metadata, "asset_checksum": asset.checksum},
                dry_run=dry_run,
                immutable_fields=_IMMUTABLE_ASSET_FIELDS,
            )
            resources["data_asset"] = str(asset_result.resource.id)
            created, updated = _counts(asset_result, created, updated)
            asset_created = asset_result.created

        if health_snapshot is not None:
            health_identity = _health_identity(distribution.resource.id, health_snapshot)
            health_result = await self._ensure(
                "dataset_health",
                _stable_gsie_id("dataset_health", health_identity),
                DatasetHealthModel,
                {
                    "dataset_version_id": version.resource.id,
                    "distribution_id": distribution.resource.id,
                    **health_snapshot.model_dump(),
                },
                {**metadata, "health_identity": health_identity},
                dry_run=dry_run,
                immutable_fields=_IMMUTABLE_HEALTH_FIELDS,
            )
            resources["dataset_health"] = str(health_result.resource.id)
            created, updated = _counts(health_result, created, updated)
            health_created = health_result.created

        if entry.operation is ManifestOperation.metadata_only:
            notes.append("metadata_only : aucun octet fournisseur copié")
        if entry.status.value == "discovered":
            notes.append("version laissée à discovered : aucune promotion automatique")

        if created:
            action = ManifestApplyAction.created
        elif updated:
            action = ManifestApplyAction.updated
        else:
            action = ManifestApplyAction.unchanged
        return ManifestApplyItem(
            slug=entry.slug,
            version=entry.version,
            action=action,
            resources=resources,
            notes=tuple(notes),
            created_resources=created,
            updated_resources=updated,
            health_created=health_created,
            asset_created=asset_created,
        )

    async def _ensure(
        self,
        type_name: str,
        gsie_id: str,
        model_cls: type[Any],
        values: dict[str, Any],
        metadata: dict[str, object],
        *,
        dry_run: bool,
        immutable_fields: frozenset[str] = frozenset(),
        status_target: Any | None = None,
        notes: list[str] | None = None,
    ) -> _ResourceResult:
        existing = await self._session.scalar(
            select(ResourceModel).where(
                ResourceModel.gsie_id == gsie_id,
                ResourceModel.deleted_at.is_(None),
            )
        )
        if existing is None:
            if dry_run:
                resource = ResourceModel(
                    id=_planned_uuid(gsie_id),
                    type=type_name,
                    gsie_id=gsie_id,
                    metadata_json=metadata,
                )
                typed = model_cls(id=resource.id, **values)
                return _ResourceResult(resource, typed, True)
            resource = ResourceModel(
                type=type_name,
                gsie_id=gsie_id,
                metadata_json=metadata,
                organisation_id=self._session.info.get("organisation_id"),
                workspace_id=self._session.info.get("workspace_id"),
            )
            self._session.add(resource)
            await self._session.flush()
            typed = model_cls(id=resource.id, **values)
            self._session.add(typed)
            await self._session.flush()
            await self._resource_service._create_revision(
                resource.id,
                1,
                "Application du manifeste Data Registry",
            )
            return _ResourceResult(resource, typed, True)

        if existing.type != type_name:
            raise ManifestApplicationError(
                f"Identifiant Registry collision : {gsie_id} porte déjà le type "
                f"{existing.type!r}, attendu {type_name!r}"
            )
        typed = await self._session.get(model_cls, existing.id)
        if typed is None:
            raise ManifestApplicationError(
                f"Resource {gsie_id} sans projection {type_name} : reprise manuelle requise"
            )
        changes: list[dict[str, object]] = []
        for field_name in immutable_fields:
            if field_name in values and getattr(typed, field_name) != values[field_name]:
                raise ManifestApplicationError(
                    f"{type_name} {gsie_id} immuable divergent sur {field_name}"
                )
        if type_name == "dataset_version" and status_target is not None:
            current_status = typed.status
            if current_status != status_target:
                # Réappliquer un manifeste de découverte ne doit jamais
                # rétrograder une version déjà qualifiée.
                if getattr(status_target, "value", status_target) == "discovered":
                    if notes is not None:
                        notes.append(
                            f"statut {getattr(current_status, 'value', current_status)} "
                            "préservé (manifeste non rétrogradant)"
                        )
                    # Le manifeste de découverte documente l'état minimal,
                    # il ne doit pas réécrire l'état plus avancé observé en
                    # base lors de la boucle d'affectation ci-dessous.
                    values["status"] = current_status
                else:
                    try:
                        values["status"] = transition_status(current_status, status_target)
                    except ValueError as exc:
                        raise ManifestApplicationError(str(exc)) from exc
        if not dry_run:
            for field_name, new_value in values.items():
                old_value = getattr(typed, field_name)
                if old_value != new_value:
                    changes.append(_field_change(field_name, old_value, new_value))
                    setattr(typed, field_name, new_value)
            merged_metadata = {**(existing.metadata_json or {}), **metadata}
            if merged_metadata != (existing.metadata_json or {}):
                changes.append(
                    _field_change("metadata_json", existing.metadata_json, merged_metadata)
                )
                existing.metadata_json = merged_metadata
            if changes:
                next_version = await self._resource_service._get_next_version(existing.id)
                await self._resource_service._create_revision(
                    existing.id,
                    next_version,
                    "Mise à jour idempotente du manifeste Data Registry",
                    diff_data={"field_changes": changes},
                )
        else:
            for field_name, new_value in values.items():
                if getattr(typed, field_name) != new_value:
                    changes.append(_field_change(field_name, getattr(typed, field_name), new_value))
            merged_metadata = {**(existing.metadata_json or {}), **metadata}
            if merged_metadata != (existing.metadata_json or {}):
                changes.append(
                    _field_change("metadata_json", existing.metadata_json, merged_metadata)
                )
        return _ResourceResult(existing, typed, False, changes)


def _counts(result: _ResourceResult, created: int, updated: int) -> tuple[int, int]:
    if result.created:
        return created + 1, updated
    if result.changes:
        return created, updated + 1
    return created, updated


def _field_change(field_name: str, old: object, new: object) -> dict[str, object]:
    return {
        "field": field_name,
        "old_value": _json_safe(old),
        "new_value": _json_safe(new),
    }


def _json_safe(value: object) -> object:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    return value


def _source_occurrences(manifest: DatasetManifest) -> dict[str, int]:
    occurrences: dict[str, int] = {}
    for entry in manifest.entries:
        occurrences[entry.source_registry_id] = occurrences.get(entry.source_registry_id, 0) + 1
    return occurrences


def _lookup_by_slug_or_source(
    values: Mapping[str, Any],
    entry: DatasetManifestEntry,
    source_occurrences: Mapping[str, int],
) -> Any | None:
    value = values.get(entry.slug)
    if value is not None:
        return value
    if source_occurrences.get(entry.source_registry_id) == 1:
        return values.get(entry.source_registry_id)
    return None


def _source_for_entry(entry: DatasetManifestEntry) -> ScientificSourceEntry:
    source = get_source(entry.source_registry_id)
    if source is None:  # défense en profondeur après validation Pydantic
        raise ManifestApplicationError(f"Source SCI-001 absente : {entry.source_registry_id}")
    return source


def _usage_rights(mode: str) -> UsageRights:
    return UsageRights.open if mode == "OPEN_COPY" else UsageRights.restricted


def _rights_notes(source: ScientificSourceEntry) -> str:
    parts = [
        "Source SCI-001",
        f"statut={source.statut_juridique.value}",
        f"mode={source.mode_ingestion.value}",
    ]
    if source.attribution_requise:
        parts.append(f"attribution={source.attribution_requise}")
    if source.notes:
        parts.append(source.notes)
    return " — ".join(parts)


def _health_identity(distribution_id: UUID, snapshot: ManifestHealthSnapshot) -> str:
    payload = "|".join(
        [
            str(distribution_id),
            snapshot.checked_at.isoformat(),
            snapshot.health_status.value,
            str(snapshot.http_status),
            str(snapshot.latency_ms),
            snapshot.last_modified.isoformat() if snapshot.last_modified else "",
            snapshot.observed_version or "",
            snapshot.schema_hash or "",
            str(snapshot.checksum_verified),
            snapshot.error_code or "",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = [
    "ManifestApplicationError",
    "ManifestApplyAction",
    "ManifestApplyItem",
    "ManifestApplyReport",
    "ManifestAssetInput",
    "ManifestHealthSnapshot",
    "ManifestRegistryService",
]

"""Preuves PostgreSQL de l'application idempotente du manifeste RFC-0038."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest
from sqlalchemy import func, select

from gsie_api.data.manifest_application import (
    ManifestAssetInput,
    ManifestHealthSnapshot,
    ManifestRegistryService,
)
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.enums import DatasetHealthStatus
from gsie_api.infrastructure.models.governance import DatasetHealthModel
from gsie_api.infrastructure.models.models_ai import DataAssetModel, DatasetModel
from gsie_api.ingestion.manifest import DatasetManifest, load_manifest
from tests.conftest import requires_docker

MANIFEST_PATH = Path(__file__).parents[3] / "DATASETS" / "REGISTRY_MANIFEST.json"


@pytest.mark.asyncio
@requires_docker
async def test_manifest_dry_run_then_apply_is_idempotent(db_session) -> None:
    manifest = load_manifest(MANIFEST_PATH)
    service = ManifestRegistryService(db_session)

    dry_run = await service.apply(manifest, dry_run=True)
    assert dry_run.dry_run is True
    assert len(dry_run.items) == 4
    assert all(item.action.value == "created" for item in dry_run.items)
    assert await db_session.scalar(select(func.count()).select_from(ResourceModel)) == 0

    applied = await service.apply(manifest, dry_run=False)
    await db_session.commit()
    assert applied.created > 0
    assert all("dataset" in item.resources for item in applied.items)

    resource_count = await db_session.scalar(select(func.count()).select_from(ResourceModel))
    dataset_count = await db_session.scalar(select(func.count()).select_from(DatasetModel))

    replay = await service.apply(manifest, dry_run=False)
    await db_session.commit()
    assert replay.created == 0
    assert replay.updated == 0
    assert all(item.action.value == "unchanged" for item in replay.items)
    assert (
        await db_session.scalar(select(func.count()).select_from(ResourceModel)) == resource_count
    )
    assert await db_session.scalar(select(func.count()).select_from(DatasetModel)) == dataset_count


@pytest.mark.asyncio
@requires_docker
async def test_manifest_persists_explicit_health_and_archive_asset_once(db_session) -> None:
    manifest = load_manifest(MANIFEST_PATH)
    checked_at = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
    health = ManifestHealthSnapshot(
        checked_at=checked_at,
        health_status=DatasetHealthStatus.healthy,
        http_status=200,
        latency_ms=18.5,
        observed_version="metadata-2026-08-10",
        checksum_verified=None,
    )
    service = ManifestRegistryService(db_session)
    applied = await service.apply(
        manifest,
        dry_run=False,
        health_reports={"gbif-occurrences": health},
    )
    await db_session.commit()
    assert applied.health_created == 1
    assert await db_session.scalar(select(func.count()).select_from(DatasetHealthModel)) == 1

    replay = await service.apply(
        manifest,
        dry_run=False,
        health_reports={"gbif-occurrences": health},
    )
    await db_session.commit()
    assert replay.health_created == 0
    assert await db_session.scalar(select(func.count()).select_from(DatasetHealthModel)) == 1

    archive_payload = manifest.entries[0].model_dump(mode="json")
    # Le manifeste historique utilise ``gbif`` pour rester lisible, mais toute
    # nouvelle application doit porter l'identité canonique réconciliée.
    archive_payload.update(
        {
            "operation": "archive_copy",
            "version": "archive-2026-08-10",
            "source_registry_id": "taxref-via-gbif",
        }
    )
    archive_payload["distribution"]["licence"] = "Licence Ouverte / Etalab (TAXREF)"
    archive_payload["distribution"]["access_url"] = (
        "https://www.gbif.org/dataset/0e61f8fe-7d25-4f81-ada7-d970bbb2c6d6"
    )
    archive_manifest = DatasetManifest(
        manifest_version=manifest.manifest_version,
        generated_at=manifest.generated_at,
        entries=[archive_payload],
    )
    body = "asset archivé de test".encode()
    asset = ManifestAssetInput(
        format="json",
        size_bytes=len(body),
        checksum=sha256(body).hexdigest(),
        storage_uri="s3://gsie-assets/registry/gbif-occurrences/archive.json",
        original_uri=archive_manifest.entries[0].distribution.access_url,
        archived_at=checked_at,
    )
    archive_result = await service.apply(
        archive_manifest,
        dry_run=False,
        assets={"gbif-occurrences": asset},
    )
    await db_session.commit()
    assert archive_result.assets_created == 1
    assert await db_session.scalar(select(func.count()).select_from(DataAssetModel)) == 1

    archive_replay = await service.apply(
        archive_manifest,
        dry_run=False,
        assets={"gbif-occurrences": asset},
    )
    await db_session.commit()
    assert archive_replay.assets_created == 0
    assert await db_session.scalar(select(func.count()).select_from(DataAssetModel)) == 1

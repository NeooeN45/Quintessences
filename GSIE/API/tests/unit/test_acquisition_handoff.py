"""Tests du contrat et de la matérialisation Forge → GSIE."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from gsie_api.data.acquisition_handoff import (
    AcquisitionHandoffError,
    load_acquisition_handoff,
    materialize_handoff_assets,
)
from gsie_api.infrastructure.object_storage import LocalStorage

if TYPE_CHECKING:
    from pathlib import Path


def _payload(archive: Path) -> dict[str, object]:
    content = archive.read_bytes()
    checksum = hashlib.sha256(content).hexdigest()
    timestamp = datetime(2026, 8, 26, 12, 0, tzinfo=UTC).isoformat()
    return {
        "schema_version": "gsie_acquisition_handoff.v1",
        "generated_at": timestamp,
        "producer": "dataset_forge",
        "producer_version": "0.1.0",
        "adapter_key": "ifn",
        "pipeline_id": "ifn/derniere-campagne",
        "manifest": {
            "manifest_version": "1",
            "generated_at": timestamp,
            "entries": [
                {
                    "slug": "ifn-brut-derniere-campagne",
                    "title": "Inventaire Forestier National",
                    "description": "Archive brute IGN.",
                    "source_registry_id": "ifn-donnees-brutes",
                    "version": "derniere-campagne",
                    "primary_domain": "forest_inventory",
                    "domains": ["gis"],
                    "tags": ["ifn"],
                    "purpose": "reference",
                    "status": "discovered",
                    "operation": "archive_copy",
                    "distribution": {
                        "access_method": "file_download",
                        "access_url": (
                            "https://inventaire-forestier.ign.fr/dataifn/data/"
                            "export_dataifn_2024.zip"
                        ),
                        "licence": "Licence Ouverte / Etalab 2.0",
                        "format": "zip",
                        "offline_pack": False,
                    },
                }
            ],
        },
        "artifacts": [
            {
                "dataset_slug": "ifn-brut-derniere-campagne",
                "kind": "raw",
                "relative_path": "ifn.zip",
                "format": "zip",
                "content_type": "application/zip",
                "size_bytes": len(content),
                "checksum": checksum,
                "checksum_algorithm": "sha256",
                "original_uri": (
                    "https://inventaire-forestier.ign.fr/dataifn/data/"
                    "export_dataifn_2024.zip"
                ),
                "archived_at": timestamp,
            }
        ],
    }


@pytest.mark.asyncio
async def test_materializes_and_replays_handoff_idempotently(tmp_path: Path) -> None:
    archive = tmp_path / "ifn.zip"
    archive.write_bytes(b"archive-ifn")
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(json.dumps(_payload(archive)), encoding="utf-8")
    handoff = load_acquisition_handoff(handoff_path)
    storage = LocalStorage(str(tmp_path / "storage"))

    first = await materialize_handoff_assets(
        handoff, staging_root=tmp_path, storage=storage, archive=True
    )
    second = await materialize_handoff_assets(
        handoff, staging_root=tmp_path, storage=storage, archive=True
    )

    first_asset = first["ifn-brut-derniere-campagne"]
    second_asset = second["ifn-brut-derniere-campagne"]
    assert first_asset.created is True
    assert second_asset.created is False
    assert first_asset.asset.storage_uri == second_asset.asset.storage_uri
    assert first_asset.asset.checksum == second_asset.asset.checksum


def test_rejects_path_traversal_in_handoff(tmp_path: Path) -> None:
    archive = tmp_path / "ifn.zip"
    archive.write_bytes(b"archive-ifn")
    payload = _payload(archive)
    artifact = payload["artifacts"][0]
    assert isinstance(artifact, dict)
    artifact["relative_path"] = "../ifn.zip"
    with pytest.raises(AcquisitionHandoffError):
        load_acquisition_handoff(tmp_path / "missing.json")
    (tmp_path / "handoff.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(AcquisitionHandoffError, match="handoff non conforme"):
        load_acquisition_handoff(tmp_path / "handoff.json")


@pytest.mark.asyncio
async def test_dry_run_verifies_without_writing_object(tmp_path: Path) -> None:
    archive = tmp_path / "ifn.zip"
    archive.write_bytes(b"archive-ifn")
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(json.dumps(_payload(archive)), encoding="utf-8")
    handoff = load_acquisition_handoff(handoff_path)
    storage = LocalStorage(str(tmp_path / "storage"))

    result = await materialize_handoff_assets(
        handoff, staging_root=tmp_path, storage=storage, archive=False
    )

    assert result["ifn-brut-derniere-campagne"].created is False
    assert not list((tmp_path / "storage").rglob("*"))

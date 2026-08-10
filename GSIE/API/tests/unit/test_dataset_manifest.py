"""Tests de la porte de manifeste : pas de réseau, pas de DB, pas de licence inventée."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from gsie_api.ingestion.manifest import (
    DatasetManifest,
    ManifestOperation,
    load_manifest,
    manifest_preview,
)

MANIFEST_PATH = Path(__file__).parents[3] / "DATASETS" / "REGISTRY_MANIFEST.json"


def _entry(**overrides: object) -> dict[str, object]:
    entry: dict[str, object] = {
        "slug": "source-test",
        "title": "Source de test",
        "description": "Métadonnées de test sans copie d'octets.",
        "source_registry_id": "gbif",
        "version": "metadata-test",
        "primary_domain": "biodiversity",
        "domains": ["botany"],
        "purpose": "reference",
        "status": "discovered",
        "operation": "metadata_only",
        "distribution": {
            "access_method": "api_rest",
            "access_url": "https://api.gbif.org",
            "licence": "CC0 / CC-BY selon jeu de données constitutif",
            "format": "json",
        },
    }
    entry.update(overrides)
    return entry


def test_loads_the_versioned_repository_manifest() -> None:
    manifest = load_manifest(MANIFEST_PATH)
    assert len(manifest.entries) == 4
    assert manifest.entries[0].operation is ManifestOperation.metadata_only
    assert manifest_preview(manifest)[0]["publisher"] == (
        "GBIF (Global Biodiversity Information Facility)"
    )


def test_rejects_duplicate_dataset_version() -> None:
    with pytest.raises(ValidationError, match="doublon"):
        DatasetManifest(entries=[_entry(), _entry()])


def test_rejects_a_restricted_source_for_archive_copy() -> None:
    entry = _entry(
        slug="climessences-test",
        source_registry_id="climessences",
        operation="archive_copy",
        distribution={
            "access_method": "api_rest",
            "access_url": "https://climessences.fr",
            "licence": "CGU ClimEssences — propriétaire",
        },
    )
    with pytest.raises(ValidationError, match="pipeline automatique interdit"):
        DatasetManifest(entries=[entry])


@pytest.mark.parametrize(
    "url",
    [
        "http://api.gbif.org",
        "https://user:secret@api.gbif.org",
        "https://api.gbif.org?token=secret",
        "https://127.0.0.1/internal",
    ],
)
def test_rejects_an_unsafe_distribution_url(url: str) -> None:
    with pytest.raises(ValidationError, match="access_url"):
        DatasetManifest(
            entries=[
                _entry(
                    distribution={
                        "access_method": "api_rest",
                        "access_url": url,
                        "licence": "CC0 / CC-BY selon jeu de données constitutif",
                    }
                )
            ]
        )


def test_rejects_a_license_drift_from_the_legal_registry() -> None:
    with pytest.raises(ValidationError, match="exactement la licence"):
        DatasetManifest(
            entries=[
                _entry(
                    distribution={
                        "access_method": "api_rest",
                        "access_url": "https://api.gbif.org",
                        "licence": "Licence inventée",
                    }
                )
            ]
        )


def test_rejects_an_unknown_domain() -> None:
    with pytest.raises(ValidationError, match="Domaine GSIE inconnu"):
        DatasetManifest(entries=[_entry(primary_domain="foresterie_magique")])


def test_rejects_offline_pack_without_an_archive_operation() -> None:
    with pytest.raises(ValidationError, match="offline_pack"):
        DatasetManifest(
            entries=[
                _entry(
                    distribution={
                        "access_method": "api_rest",
                        "access_url": "https://api.gbif.org",
                        "licence": "CC0 / CC-BY selon jeu de données constitutif",
                        "offline_pack": True,
                    }
                )
            ]
        )


def test_load_manifest_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON"):
        load_manifest(path)


def test_load_manifest_rejects_a_non_object(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps([]), encoding="utf-8")
    with pytest.raises(ValueError, match="objet"):
        load_manifest(path)

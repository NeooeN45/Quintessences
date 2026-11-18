"""Tests du miroir GSIE du contrat Forge ``forge_analysis_bundle.v1``."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003 - annotation d'API de test
from uuid import uuid4

import pytest

from gsie_api.data.analysis_bundle import (
    AnalysisBundleContractError,
    load_analysis_bundle,
    validate_analysis_bundle,
)

_NOW = datetime(2026, 8, 31, 10, 0, tzinfo=UTC)


def _payload() -> dict[str, object]:
    return {
        "schema_version": "forge_analysis_bundle.v1",
        "bundle_id": str(uuid4()),
        "station_id": str(uuid4()),
        "profile_id": "geosylva.station.analysis",
        "generated_at": _NOW.isoformat(),
        "sources": [
            {
                "source_id": "soilgrids-wcs",
                "adapter_key": "soilgrids",
                "adapter_version": "2.0.0",
                "dataset_version": "2026.1",
                "license": "Licence Ouverte",
                "reference": "registry:soilgrids-wcs",
                "retrieved_at": _NOW.isoformat(),
                "qualification": "qualified",
            }
        ],
        "parameters": [
            {
                "parameter_id": "pedology.soilgrids.phh2o",
                "value": 5.4,
                "unit": "pH",
                "source_id": "soilgrids-wcs",
                "observed_at": _NOW.isoformat(),
                "evidence_level": "C",
                "quality_score": 0.95,
                "uncertainty": 0.2,
                "method_id": "soilgrids.wcs.phh2o",
                "method_version": "2.0",
            }
        ],
        "derived_features": [],
        "lineage": {
            "pipeline_id": "geosylva.station.analysis",
            "forge_version": "0.2.0",
            "config_hash": "a" * 64,
            "input_manifest_hash": "b" * 64,
            "reproducible": True,
            "transformations": ["normalisation"],
            "seed": 42,
        },
        "omitted_parameter_ids": [],
    }


def test_validates_bundle_and_returns_stable_fingerprint() -> None:
    bundle = validate_analysis_bundle(_payload())

    assert bundle.schema_version == "forge_analysis_bundle.v1"
    assert len(bundle.fingerprint()) == 64
    assert bundle.fingerprint() == bundle.fingerprint()


def test_rejects_soilgrids_rest_beta() -> None:
    payload = _payload()
    sources = payload["sources"]
    assert isinstance(sources, list)
    source = sources[0]
    assert isinstance(source, dict)
    source["reference"] = "https://example.org/soilgrids/rest/beta"

    with pytest.raises(AnalysisBundleContractError, match="REST"):
        validate_analysis_bundle(payload)


def test_rejects_unknown_dependency() -> None:
    payload = _payload()
    payload["derived_features"] = [
        {
            "feature_id": "risk.water_stress",
            "value": 0.8,
            "unit": "score",
            "dependencies": ["pedology.soilgrids.missing"],
            "source_ids": ["soilgrids-wcs"],
            "formula": "f(missing)",
            "calculator_id": "forge.water-stress",
            "calculator_version": "1.0.0",
            "evidence_level": "C",
            "quality_score": 0.8,
        }
    ]

    with pytest.raises(AnalysisBundleContractError, match="dépendance inconnue"):
        validate_analysis_bundle(payload)


def test_load_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(AnalysisBundleContractError):
        load_analysis_bundle(path)


def test_load_round_trips_json(tmp_path: Path) -> None:
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(_payload()), encoding="utf-8")

    bundle = load_analysis_bundle(path)

    assert bundle.station_id

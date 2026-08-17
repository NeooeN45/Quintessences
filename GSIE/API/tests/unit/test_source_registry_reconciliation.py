"""Tests de réconciliation des identités SCI-001 agrégées."""

from pathlib import Path

import pytest

from gsie_api.ingestion.manifest import load_manifest
from gsie_api.ingestion.source_reconciliation import (
    DryRunDecision,
    SourceReconciliationRequiredError,
    build_migration_dry_run,
    find_legacy_source_references,
    require_canonical_source_references,
)

DATASETS_DIR = Path(__file__).parents[3] / "DATASETS"
ACTIVE_MANIFEST = DATASETS_DIR / "REGISTRY_MANIFEST.json"
CANDIDATE_MANIFEST = DATASETS_DIR / "REGISTRY_MANIFEST_I0_CANDIDATE_2026-08-13.json"


def test_active_manifest_exposes_the_four_legacy_identities() -> None:
    references = find_legacy_source_references(load_manifest(ACTIVE_MANIFEST))

    assert {item.legacy_source_id for item in references} == {
        "gbif",
        "ign-apicarto-geopf",
        "meteofrance-portail-api",
        "soilgrids",
    }


def test_active_manifest_cannot_be_silently_reused_as_canonical() -> None:
    with pytest.raises(SourceReconciliationRequiredError, match="Réconciliation SCI-001"):
        require_canonical_source_references(load_manifest(ACTIVE_MANIFEST))


def test_i0_candidate_uses_only_canonical_source_identities() -> None:
    manifest = load_manifest(CANDIDATE_MANIFEST)

    assert find_legacy_source_references(manifest) == ()
    require_canonical_source_references(manifest)


def test_migration_dry_run_is_fail_closed_and_preserves_soilgrids_lineage() -> None:
    report = build_migration_dry_run(
        load_manifest(ACTIVE_MANIFEST),
        load_manifest(CANDIDATE_MANIFEST),
    )

    assert report.mode == "DRY_RUN_ONLY"
    assert report.writes == 0
    assert report.fetch_enabled is False
    assert report.promotion_allowed is False
    decisions = {item.legacy_source_id: item.decision for item in report.items}
    assert decisions["soilgrids"] is DryRunDecision.preserve_lineage
    assert decisions["gbif"] is DryRunDecision.unresolved
    assert decisions["ign-apicarto-geopf"] is DryRunDecision.unresolved
    assert decisions["meteofrance-portail-api"] is DryRunDecision.unresolved


def test_migration_dry_run_exposes_only_scoped_adapter_proposals() -> None:
    report = build_migration_dry_run(
        load_manifest(ACTIVE_MANIFEST),
        load_manifest(CANDIDATE_MANIFEST),
    )

    proposals = {(item.adapter_key, item.target_source_id) for item in report.adapter_proposals}
    assert proposals == {
        ("gbif", "gbif-species-api"),
        ("meteofrance", "meteofrance-meteo-forets"),
    }

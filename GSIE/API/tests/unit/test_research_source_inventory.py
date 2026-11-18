"""Tests de réconciliation des sources D1 à D8."""

from pathlib import Path

from scripts.audit_research_source_inventory import audit_research_source_inventory


def test_les_inventaires_d1_a_d8_sont_parsables_sans_promotion_automatique() -> None:
    root = Path(__file__).parents[4]
    audit = audit_research_source_inventory(root)

    assert audit.valid, audit.errors
    assert len(audit.records) >= 100
    assert audit.unique_name_count >= 100
    assert all(record.candidate_id.startswith("research:") for record in audit.records)

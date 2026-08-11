"""Portes de validation du Registry exposées au CRUD générique."""

from datetime import UTC, datetime
from uuid import uuid4

from gsie_api.resources.validators import validate_resource_state


def should_validate_a_discovered_dataset_identity() -> None:
    assert (
        validate_resource_state(
            "dataset",
            {
                "title": "Humidité des sols",
                "description": "Mesures contrôlées",
                "slug": "soil-moisture-fr",
                "primary_domain": "soil_moisture",
                "domains": ["hydrology"],
                "tags": ["satellite"],
                "domain_vocabulary_version": "2026-08-10",
            },
        )
        == []
    )


def should_reject_an_unknown_dataset_domain_or_duplicate_primary_domain() -> None:
    errors = validate_resource_state(
        "dataset",
        {
            "title": "Jeu",
            "description": "Description",
            "primary_domain": "unknown",
            "domains": ["soil_moisture"],
        },
    )
    assert any("Domaine" in error for error in errors)
    assert any("vocabulary" in error for error in errors)

    errors = validate_resource_state(
        "dataset",
        {
            "title": "Jeu",
            "description": "Description",
            "primary_domain": "soil_moisture",
            "domains": ["soil_moisture"],
            "domain_vocabulary_version": "2026-08-10",
        },
    )
    assert any("répété" in error for error in errors)


def should_reject_a_production_version_without_qualification() -> None:
    errors = validate_resource_state(
        "dataset_version",
        {
            "dataset_id": uuid4(),
            "version": "2026.08",
            "status": "production",
            "release_date": datetime.now(UTC),
            "schema_hash": "a" * 64,
        },
    )
    assert any("evidence_level" in error for error in errors)
    assert any("evidence_assessed_at" in error for error in errors)
    assert any("evidence_basis" in error for error in errors)


def should_accept_a_qualified_version_with_traceable_evidence() -> None:
    assert (
        validate_resource_state(
            "dataset_version",
            {
                "dataset_id": uuid4(),
                "version": "2026.08",
                "status": "production",
                "release_date": datetime.now(UTC),
                "schema_hash": "a" * 64,
                "evidence_level": "A",
                "evidence_assessed_at": datetime.now(UTC),
                "evidence_basis": {
                    "source_ids": [str(uuid4())],
                    "justification": "Source primaire qualifiée",
                },
            },
        )
        == []
    )


def should_reject_an_invalid_health_measurement() -> None:
    errors = validate_resource_state(
        "dataset_health",
        {
            "dataset_version_id": uuid4(),
            "distribution_id": uuid4(),
            "checked_at": datetime.now(UTC),
            "health_status": "healthy",
            "latency_ms": -1,
            "http_status": 700,
        },
    )
    assert any("latency_ms" in error for error in errors)
    assert any("http_status" in error for error in errors)

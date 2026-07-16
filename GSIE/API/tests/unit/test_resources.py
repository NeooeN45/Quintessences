"""Tests unitaires — CRUD générique resources (v6.2).

Teste le registry, la validation, les schemas, le service.
Pas de DB requise — utilise des mocks pour la session.
"""

from uuid import uuid4

import pytest

from gsie_api.resources.service import ResourceService
from gsie_api.resources.validators import validate_resource_data


class TestResourceTypes:
    """Tests du registry des types."""

    def test_should_list_69_types_when_called(self) -> None:
        types = ResourceService.list_types()
        assert len(types) == 69
        assert "assertion" in types
        assert "observation" in types
        assert "concept" in types
        assert "ecological_state" in types

    def test_should_return_sorted_types(self) -> None:
        types = ResourceService.list_types()
        assert types == sorted(types)


class TestValidators:
    """Tests de la validation dynamique par type."""

    def test_should_pass_when_required_fields_present(self) -> None:
        errors = validate_resource_data("assertion", {
            "claim_kind": "relation",
            "lifecycle_status": "draft",
        })
        assert errors == []

    def test_should_fail_when_required_field_missing(self) -> None:
        errors = validate_resource_data("assertion", {
            "claim_kind": "relation",
            # lifecycle_status manquant
        })
        assert len(errors) == 1
        assert "lifecycle_status" in errors[0]

    def test_should_fail_when_enum_value_invalid(self) -> None:
        errors = validate_resource_data("assertion", {
            "claim_kind": "toto",  # invalide
            "lifecycle_status": "draft",
        })
        assert len(errors) == 1
        assert "claim_kind" in errors[0]

    def test_should_pass_when_no_required_fields(self) -> None:
        errors = validate_resource_data("entity", {})
        assert errors == []

    def test_should_fail_when_observation_missing_subject(self) -> None:
        errors = validate_resource_data("observation", {})
        assert len(errors) == 1
        assert "subject_id" in errors[0]

    def test_should_pass_when_all_required_present(self) -> None:
        errors = validate_resource_data("observation", {
            "subject_id": uuid4(),
        })
        assert errors == []

    def test_should_validate_flow_all_required(self) -> None:
        errors = validate_resource_data("flow", {
            "flow_type": "carbon",
            "source_id": uuid4(),
            "sink_id": uuid4(),
            "magnitude": 12.5,
            "magnitude_unit_id": uuid4(),
        })
        assert errors == []

    def test_should_fail_when_flow_missing_fields(self) -> None:
        errors = validate_resource_data("flow", {"flow_type": "carbon"})
        assert len(errors) == 4  # source_id, sink_id, magnitude, magnitude_unit_id

    def test_should_validate_consent_legal_basis(self) -> None:
        errors = validate_resource_data("consent", {
            "data_subject_id": uuid4(),
            "purpose": "recherche",
            "granted_at": "2026-07-16T00:00:00Z",
            "legal_basis": "consent",
        })
        assert errors == []

    def test_should_fail_when_consent_invalid_legal_basis(self) -> None:
        errors = validate_resource_data("consent", {
            "data_subject_id": uuid4(),
            "purpose": "recherche",
            "granted_at": "2026-07-16T00:00:00Z",
            "legal_basis": "toto",  # invalide
        })
        assert len(errors) == 1

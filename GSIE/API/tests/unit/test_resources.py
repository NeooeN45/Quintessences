"""Tests unitaires — CRUD générique resources (v6.2).

Teste le registry, la validation, les schemas, le service.
Pas de DB requise — utilise des mocks pour la session.
"""

from uuid import uuid4

from gsie_api.resources.service import ResourceService
from gsie_api.resources.validators import validate_resource_data


class TestResourceTypes:
    """Tests du registry des types."""

    def test_should_list_89_types_when_called(self) -> None:
        # 76 types + 3 types forestiers spécialisés (RFC-0016, tranche 1/10 :
        # autecology_profile, site_index_model, fertility_class) + 2 types
        # de diagnostic stationnel (RFC-0016, tranche 2/10 : station_type,
        # station_observation) + 2 types d'itinéraires sylvicoles
        # (RFC-0016, tranche 3/10 : silvicultural_system,
        # silvicultural_rule — Intervention réutilise le type existant) +
        # 1 type provenance/MFR (RFC-0016, tranche 4/10 :
        # provenance_material) + 2 types sanitaires (RFC-0016, tranche
        # 5/10 : diagnostic_protocol, health_risk) + 3 types d'identification
        # botanique assistée (RFC-0018, tranche 1/N, DEC-000030 :
        # botanical_identification_request/result/decision).
        types = ResourceService.list_types()
        assert len(types) == 89
        assert "assertion" in types
        assert "observation" in types
        assert "concept" in types
        assert "ecological_state" in types
        assert "management_plan" in types
        assert "intervention" in types
        assert "outcome_tracking" in types
        assert "autecology_profile" in types
        assert "site_index_model" in types
        assert "fertility_class" in types
        assert "station_type" in types
        assert "station_observation" in types
        assert "silvicultural_system" in types
        assert "silvicultural_rule" in types
        assert "provenance_material" in types
        assert "diagnostic_protocol" in types
        assert "health_risk" in types
        assert "botanical_identification_request" in types
        assert "botanical_identification_result" in types
        assert "botanical_identification_decision" in types

    def test_should_return_sorted_types(self) -> None:
        types = ResourceService.list_types()
        assert types == sorted(types)


class TestValidators:
    """Tests de la validation dynamique par type."""

    def test_should_pass_when_required_fields_present(self) -> None:
        errors = validate_resource_data(
            "assertion",
            {
                "claim_kind": "relation",
                "lifecycle_status": "draft",
            },
        )
        assert errors == []

    def test_should_fail_when_required_field_missing(self) -> None:
        errors = validate_resource_data(
            "assertion",
            {
                "claim_kind": "relation",
                # lifecycle_status manquant
            },
        )
        assert len(errors) == 1
        assert "lifecycle_status" in errors[0]

    def test_should_fail_when_enum_value_invalid(self) -> None:
        errors = validate_resource_data(
            "assertion",
            {
                "claim_kind": "toto",  # invalide
                "lifecycle_status": "draft",
            },
        )
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
        errors = validate_resource_data(
            "observation",
            {
                "subject_id": uuid4(),
            },
        )
        assert errors == []

    def test_should_validate_flow_all_required(self) -> None:
        errors = validate_resource_data(
            "flow",
            {
                "flow_type": "carbon",
                "source_id": uuid4(),
                "sink_id": uuid4(),
                "magnitude": 12.5,
                "magnitude_unit_id": uuid4(),
            },
        )
        assert errors == []

    def test_should_fail_when_flow_missing_fields(self) -> None:
        errors = validate_resource_data("flow", {"flow_type": "carbon"})
        assert len(errors) == 4  # source_id, sink_id, magnitude, magnitude_unit_id

    def test_should_validate_consent_legal_basis(self) -> None:
        errors = validate_resource_data(
            "consent",
            {
                "data_subject_id": uuid4(),
                "purpose": "recherche",
                "granted_at": "2026-07-16T00:00:00Z",
                "legal_basis": "consent",
            },
        )
        assert errors == []

    def test_should_fail_when_consent_invalid_legal_basis(self) -> None:
        errors = validate_resource_data(
            "consent",
            {
                "data_subject_id": uuid4(),
                "purpose": "recherche",
                "granted_at": "2026-07-16T00:00:00Z",
                "legal_basis": "toto",  # invalide
            },
        )
        assert len(errors) == 1

    def test_should_validate_fertility_class_all_required(self) -> None:
        """Porte de validation RFC-0016 §5 Phase A point 3 : même via l'API

        générique de resources (pas seulement les schémas Pydantic des
        engines), une FertilityClass sans ses 5 champs non négociables
        est rejetée.
        """
        errors = validate_resource_data(
            "fertility_class",
            {
                "species_entity_id": uuid4(),
                "site_index_model_id": uuid4(),
                "class_label": "Classe 1",
                "reference_age_years": 50,
                "calibration_region": "Provence calcaire",
                "source_id": uuid4(),
            },
        )
        assert errors == []

    def test_should_fail_when_fertility_class_missing_fields(self) -> None:
        errors = validate_resource_data("fertility_class", {"species_entity_id": uuid4()})
        assert len(errors) == 5

    def test_should_fail_when_silvicultural_rule_invalid_evidence_level(self) -> None:
        errors = validate_resource_data(
            "silvicultural_rule",
            {
                "required_context": "Peuplement régulier",
                "trigger": "Densité > 800 tiges/ha",
                "action": "Éclaircie",
                "intensity": "25 %",
                "evidence_level": "Z",  # invalide
                "source_id": uuid4(),
            },
        )
        assert len(errors) == 1

    def test_should_fail_when_provenance_material_invalid_category(self) -> None:
        errors = validate_resource_data(
            "provenance_material",
            {
                "species_entity_id": uuid4(),
                "provenance_region": "Massif central",
                "base_material": "Verger à graines VG-034",
                "base_material_category": "invente",  # invalide
                "aid_eligible": True,
                "decree_version": "Arrêté du 6 mars 2026",
                "source_id": uuid4(),
            },
        )
        assert len(errors) == 1

    def test_should_validate_botanical_identification_request_all_required(self) -> None:
        errors = validate_resource_data(
            "botanical_identification_request",
            {
                "requested_by_id": uuid4(),
                "photos": [{"organ": "feuille", "content_hash": "abc123"}],
                "captured_at": "2026-07-20T10:00:00Z",
            },
        )
        assert errors == []

    def test_should_fail_when_botanical_identification_request_missing_fields(self) -> None:
        errors = validate_resource_data("botanical_identification_request", {})
        assert len(errors) == 3

    def test_should_validate_botanical_identification_result_all_required(self) -> None:
        errors = validate_resource_data(
            "botanical_identification_result",
            {
                "request_id": uuid4(),
                "provider": "plantnet",
                "provider_engine_version": "2026.1",
                "candidates": [{"scientific_name": "Quercus robur", "score": 0.82}],
                "received_at": "2026-07-20T10:05:00Z",
            },
        )
        assert errors == []

    def test_should_fail_when_botanical_identification_result_missing_fields(self) -> None:
        errors = validate_resource_data("botanical_identification_result", {})
        assert len(errors) == 5

    def test_should_validate_botanical_identification_decision_default_status(self) -> None:
        """Porte de validation RFC-0018 §4 : même via l'API générique de

        resources, une décision d'identification exige un statut explicite
        (jamais implicitement validée par défaut).
        """
        errors = validate_resource_data(
            "botanical_identification_decision",
            {
                "result_id": uuid4(),
                "status": "suggestion_ia",
            },
        )
        assert errors == []

    def test_should_fail_when_botanical_identification_decision_invalid_status(self) -> None:
        errors = validate_resource_data(
            "botanical_identification_decision",
            {
                "result_id": uuid4(),
                "status": "auto_confirmee",  # invalide — n'existe pas dans l'enum
            },
        )
        assert len(errors) == 1

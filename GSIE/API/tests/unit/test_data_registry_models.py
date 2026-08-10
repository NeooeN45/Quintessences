"""Contrats SQLAlchemy du Data Registry."""

from gsie_api.infrastructure.models import RESOURCE_TYPES
from gsie_api.infrastructure.models.enums import DatasetHealthStatus, DatasetStatus
from gsie_api.infrastructure.models.governance import (
    DataRightsStatementModel,
    DatasetHealthModel,
)
from gsie_api.infrastructure.models.models_ai import (
    DatasetModel,
    DatasetVersionModel,
    DistributionModel,
)


def should_register_the_registry_projection_types() -> None:
    assert RESOURCE_TYPES["dataset_health"] is DatasetHealthModel
    assert RESOURCE_TYPES["data_rights_statement"] is DataRightsStatementModel


def should_expose_the_phase_two_dataset_columns() -> None:
    assert {
        "slug",
        "primary_domain",
        "domains",
        "tags",
        "domain_vocabulary_version",
    }.issubset(DatasetModel.__table__.columns.keys())
    assert {
        "status",
        "temporal_coverage_start",
        "temporal_coverage_end",
        "schema_hash",
        "evidence_level",
        "evidence_basis",
        "evidence_assessed_at",
    }.issubset(DatasetVersionModel.__table__.columns.keys())
    assert {
        "data_rights_statement_id",
        "coverage_place_id",
        "format",
        "crs",
    }.issubset(DistributionModel.__table__.columns.keys())


def should_keep_dataset_and_health_enums_distinct() -> None:
    assert DatasetStatus.production.value == "production"
    assert DatasetHealthStatus.healthy.value == "healthy"
    assert DatasetStatus.production.value != DatasetHealthStatus.healthy.value


def should_keep_health_in_the_governance_schema() -> None:
    assert DatasetHealthModel.__table__.schema == "gsie_gouvernance"
    assert DataRightsStatementModel.__table__.schema == "gsie_gouvernance"


def should_enforce_health_distribution_version_coherence() -> None:
    distribution_constraints = {
        constraint.name for constraint in DistributionModel.__table__.constraints
    }
    health_constraints = {
        constraint.name for constraint in DatasetHealthModel.__table__.constraints
    }
    assert "uq_distribution_id_dataset_version" in distribution_constraints
    assert "fk_dataset_health_distribution_version" in health_constraints

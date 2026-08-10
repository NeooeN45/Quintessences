"""Tests unitaires de la façade de lecture Registry (session simulée)."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from gsie_api.data.contracts import encode_cursor
from gsie_api.data.lifecycle import InvalidDatasetTransition
from gsie_api.data.schemas import DataSearchQuery
from gsie_api.data.service import DataRegistryService, RegistryContractError
from gsie_api.infrastructure.models.enums import (
    AccessMethod,
    AgentType,
    CitationRole,
    DatasetHealthStatus,
    DatasetPurpose,
    DatasetStatus,
    EvidenceLevel,
    SourceNature,
    SourceSubtype,
    UsageRights,
)
from gsie_api.infrastructure.models.models_ai import DatasetVersionModel
from gsie_api.resources.service import ResourceService
from gsie_api.resources.validators import ResourceValidationError


class _Result:
    def __init__(
        self,
        values: object = None,
        scalar: object = None,
        rows: list[object] | None = None,
    ):
        self.values = values
        self.scalar = scalar
        self.rows = rows if rows is not None else []

    def scalars(self) -> "_Result":
        return self

    def all(self) -> list[object]:
        if isinstance(self.values, list):
            return list(self.values)
        return list(self.rows)

    def scalar_one_or_none(self) -> object:
        return self.scalar


class _Session:
    def __init__(self, results: list[_Result]):
        self.results = results
        self.statements: list[object] = []

    async def execute(self, statement: object) -> _Result:
        self.statements.append(statement)
        return self.results.pop(0)


def _dataset(*, created_at: datetime, dataset_id=None) -> SimpleNamespace:
    return SimpleNamespace(
        id=dataset_id or uuid4(),
        slug="soil-moisture-fr",
        title="Humidité des sols",
        description="Mesures",
        publisher_id=uuid4(),
        purpose=DatasetPurpose.production,
        topic="historique",
        primary_domain="soil_moisture",
        domains=["hydrology"],
        tags=["satellite"],
        domain_vocabulary_version="2026-08-10",
        created_at=created_at,
    )


def _version(
    dataset_id,
    *,
    created_at: datetime,
    status=DatasetStatus.production,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        dataset_id=dataset_id,
        version="2026.08",
        release_date=created_at,
        temporal_coverage_start=created_at,
        temporal_coverage_end=created_at,
        changes=None,
        schema_hash="a" * 64,
        stats={"rows": 1},
        status=status,
        evidence_level=EvidenceLevel.a,
        evidence_basis={"source_ids": [str(uuid4())], "justification": "test"},
        evidence_assessed_at=created_at,
        created_at=created_at,
    )


def _distribution(version_id, *, created_at: datetime) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        dataset_version_id=version_id,
        access_method=AccessMethod.file_download,
        access_url="https://example.test/data.parquet",
        licence="ODbL-1.0",
        data_rights_statement_id=uuid4(),
        scale_context_id=uuid4(),
        coverage_place_id=uuid4(),
        format="geoparquet",
        crs={"code": "EPSG:2154"},
        created_at=created_at,
    )


def _rights(rights_id, *, commercial=True) -> SimpleNamespace:
    return SimpleNamespace(
        id=rights_id,
        licence="ODbL-1.0",
        usage_rights=UsageRights.open,
        commercial_use_allowed=commercial,
        redistribution_allowed=True,
        attribution_required=True,
        ai_training_allowed=True,
        notes=None,
    )


@pytest.mark.asyncio
async def should_return_a_cursor_paginated_catalog() -> None:
    now = datetime(2026, 8, 10, tzinfo=UTC)
    first, second = _dataset(created_at=now), _dataset(created_at=now.replace(hour=11))
    response = await DataRegistryService(_Session([_Result(values=[first, second])])).catalog(
        cursor=None, limit=1
    )
    assert len(response.items) == 1
    assert response.page.next_cursor is not None


@pytest.mark.asyncio
async def should_reject_a_catalog_cursor_with_the_wrong_filter_set() -> None:
    token = encode_cursor(datetime(2026, 8, 10, tzinfo=UTC), uuid4(), filters_hash="0" * 32)
    with pytest.raises(RegistryContractError, match="filtres"):
        await DataRegistryService(_Session([])).catalog(cursor=token, limit=20)


@pytest.mark.asyncio
async def should_return_dataset_detail_and_redacted_rights() -> None:
    now = datetime(2026, 8, 10, tzinfo=UTC)
    dataset = _dataset(created_at=now)
    version = _version(dataset.id, created_at=now)
    distribution = _distribution(version.id, created_at=now)
    rights = _rights(distribution.data_rights_statement_id)
    session = _Session(
        [
            _Result(scalar=dataset),
            _Result(values=[version]),
            _Result(values=[distribution]),
            _Result(values=[rights]),
        ]
    )
    response = await DataRegistryService(session).dataset(dataset.id)
    assert response is not None
    assert response.item.versions[0].distributions[0].rights is not None
    assert (
        response.item.versions[0].distributions[0].access_url == "https://example.test/data.parquet"
    )


@pytest.mark.asyncio
async def should_return_none_for_an_unknown_dataset() -> None:
    assert await DataRegistryService(_Session([_Result(scalar=None)])).dataset(uuid4()) is None


@pytest.mark.asyncio
async def should_project_providers_without_exposing_agent_to_a_reader() -> None:
    now = datetime(2026, 8, 10, tzinfo=UTC)
    citation = SimpleNamespace(
        id=uuid4(),
        source_id=uuid4(),
        target_id=uuid4(),
        citation_role=CitationRole.primary,
        created_at=now,
    )
    source = SimpleNamespace(
        id=citation.source_id,
        title="Catalogue officiel",
        subtype=SourceSubtype.api,
        source_nature=SourceNature.data_provider,
        url="https://example.test/catalogue",
    )
    agent = SimpleNamespace(id=uuid4(), name="Organisation publique", type=AgentType.organisation)
    dataset_id = uuid4()
    session = _Session([_Result(rows=[(citation, source, dataset_id, agent)])])
    response = await DataRegistryService(session).providers(
        cursor=None, limit=20, dataset_id=dataset_id, include_agent=False
    )
    assert response.items[0].agent_name is None
    assert response.items[0].source_url == "https://example.test/catalogue"


@pytest.mark.asyncio
async def should_return_health_and_coverage_projections() -> None:
    now = datetime(2026, 8, 10, tzinfo=UTC)
    health = SimpleNamespace(
        id=uuid4(),
        dataset_version_id=uuid4(),
        distribution_id=uuid4(),
        checked_at=now,
        health_status=DatasetHealthStatus.healthy,
        http_status=200,
        latency_ms=12.0,
        last_modified=now,
        observed_version="2026.08",
        schema_hash="a" * 64,
        checksum_verified=True,
        error_code=None,
        created_at=now,
    )
    distribution = _distribution(health.dataset_version_id, created_at=now)
    place = SimpleNamespace(label="France", area_m2=100.0)
    scale = SimpleNamespace(grain_m2=25.0, extent_m2=100.0)
    session = _Session([_Result(values=[health]), _Result(rows=[(distribution, place, scale)])])
    health_response = await DataRegistryService(session).health(
        cursor=None,
        limit=20,
        health_status=None,
        dataset_version_id=None,
        distribution_id=None,
    )
    coverage_response = await DataRegistryService(session).coverage(cursor=None, limit=20)
    assert health_response.items[0].http_status == 200
    assert coverage_response.items[0].place_label == "France"
    assert coverage_response.items[0].grain_m2 == 25.0


@pytest.mark.asyncio
async def should_report_search_blockers_before_any_future_resolver() -> None:
    now = datetime(2026, 8, 10, tzinfo=UTC)
    dataset = _dataset(created_at=now)
    version = _version(dataset.id, created_at=now)
    distribution = _distribution(version.id, created_at=now)
    rights = _rights(distribution.data_rights_statement_id, commercial=False)
    asset = SimpleNamespace(
        id=uuid4(),
        dataset_version_id=version.id,
        storage_uri="s3://gsie/archive.parquet",
        checksum="a" * 64,
        archived_at=now,
    )
    session = _Session(
        [
            _Result(rows=[(version, dataset)]),
            _Result(values=[distribution]),
            _Result(values=[rights]),
            _Result(values=[asset]),
        ]
    )
    query = DataSearchQuery(
        theme="soil_moisture",
        use="inference",
        minimum_evidence_level=EvidenceLevel.c,
        commercial_use_required=True,
        minimum_quality_score=0.75,
    )
    response = await DataRegistryService(session).search(query)
    assert response.policy_version == "registry-search-1"
    assert response.items[0].blocking_reasons == ["COMMERCIAL_USE_NOT_ALLOWED", "QUALITY_MISSING"]


def should_validate_status_transitions_through_the_service_port() -> None:
    service = DataRegistryService(_Session([]))
    assert (
        service.validate_status_transition("discovered", "link_checked")
        is DatasetStatus.link_checked
    )
    with pytest.raises(InvalidDatasetTransition):
        service.validate_status_transition("production", "discovered")


@pytest.mark.asyncio
async def should_block_an_invalid_status_transition_through_generic_crud() -> None:
    session = SimpleNamespace(rollback=AsyncMock())
    service = ResourceService(session)
    instance = DatasetVersionModel(
        id=uuid4(),
        dataset_id=uuid4(),
        version="2026.08",
        status=DatasetStatus.production,
    )
    with pytest.raises(ResourceValidationError, match="DATASET_STATUS_TRANSITION_INVALID"):
        await service._reject_invalid_update(
            "dataset_version",
            instance,
            {"status": "discovered"},
            {"status": DatasetStatus.discovered},
        )
    session.rollback.assert_awaited_once()

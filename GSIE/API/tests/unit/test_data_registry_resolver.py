"""Tests de la politique déterministe du Data Selection Engine."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from gsie_api.data.resolver import (
    RESOLVER_POLICY_VERSION,
    ResolutionMetadata,
    resolve_candidates,
)
from gsie_api.data.schemas import (
    DatasetSummary,
    DatasetVersionRead,
    DistributionRead,
    ResolveRequest,
    SearchCandidate,
)
from gsie_api.infrastructure.models.enums import (
    AccessMethod,
    DatasetPurpose,
    DatasetStatus,
    EvidenceLevel,
)


def _candidate(
    *,
    status: DatasetStatus = DatasetStatus.production,
    evidence: EvidenceLevel | None = EvidenceLevel.a,
    quality: float | None = None,
) -> SearchCandidate:
    dataset_id = uuid4()
    version_id = uuid4()
    now = datetime(2026, 8, 10, tzinfo=UTC)
    version = DatasetVersionRead(
        id=version_id,
        dataset_id=dataset_id,
        version="2026.08",
        release_date=now,
        temporal_coverage_start=None,
        temporal_coverage_end=None,
        changes=None,
        schema_hash="a" * 64,
        stats={"quality_score": quality} if quality is not None else None,
        status=status,
        evidence_level=evidence,
        evidence_basis={"source_ids": [str(uuid4())], "justification": "test"}
        if evidence is not None
        else None,
        evidence_assessed_at=now if evidence is not None else None,
        distributions=[
            DistributionRead(
                id=uuid4(),
                dataset_version_id=version_id,
                access_method=AccessMethod.file_download,
                access_url="https://example.test/data.parquet",
                licence="Etalab-2.0",
                data_rights_statement_id=None,
                scale_context_id=None,
                coverage_place_id=None,
                format="parquet",
                crs={"code": "EPSG:2154"},
            )
        ],
    )
    return SearchCandidate(
        dataset=DatasetSummary(
            id=dataset_id,
            slug="jeu-test",
            title="Jeu test",
            description="Jeu test",
            publisher_id=None,
            purpose=DatasetPurpose.production,
            topic=None,
            primary_domain="soil_moisture",
            domains=["soil_moisture"],
            tags=[],
            domain_vocabulary_version="2026-08-10",
        ),
        version=version,
    )


def should_ignore_quality_score_in_dataset_version_stats() -> None:
    candidate = _candidate(quality=0.99)
    query = ResolveRequest(minimum_quality_score=0.8)

    response = resolve_candidates(
        query,
        [candidate],
        metadata={},
        vocabulary_version="2026-08-10",
    )

    assert response.selected is None
    assert "QUALITY_MISSING" in response.candidates[0].blocking_reasons
    assert response.candidates[0].criteria["quality"] is None


def should_apply_constraints_before_scoring_and_expose_blockers() -> None:
    candidate = _candidate(status=DatasetStatus.staging, evidence=EvidenceLevel.d)
    query = ResolveRequest(
        use="inference",
        minimum_evidence_level=EvidenceLevel.c,
        minimum_quality_score=0.75,
    )
    response = resolve_candidates(
        query,
        [candidate],
        vocabulary_version="2026-08-10",
        now=datetime(2026, 8, 10, tzinfo=UTC),
    )
    assert response.selected is None
    assert response.fallback is None
    assert response.candidates[0].eligible is False
    assert {
        "STATUS_NOT_PRODUCTION",
        "EVIDENCE_INSUFFICIENT",
        "QUALITY_MISSING",
        "EVIDENCE_MISSING",
    }.isdisjoint(set(response.candidates[0].blocking_reasons)) is False
    assert response.policy_version == RESOLVER_POLICY_VERSION


def should_rank_quality_and_return_only_an_explicit_fallback() -> None:
    older = _candidate(quality=0.7)
    newer = _candidate(quality=0.95)
    query = ResolveRequest(
        minimum_quality_score=0.5,
        prefer=["quality"],
        allow_fallback=True,
    )
    response = resolve_candidates(
        query,
        [older, newer],
        metadata={
            older.version.id: ResolutionMetadata(quality_score=0.7),
            newer.version.id: ResolutionMetadata(quality_score=0.95),
        },
        vocabulary_version="2026-08-10",
        trace_id="trace-resolve-test",
    )
    assert response.selected is not None
    assert response.selected.candidate.version.id == newer.version.id
    assert response.fallback is not None
    assert response.fallback.candidate.version.id == older.version.id
    assert response.trace_id == "trace-resolve-test"


def should_use_freshness_and_offline_as_versioned_criteria() -> None:
    candidate = _candidate(quality=0.8)
    now = datetime(2026, 8, 10, tzinfo=UTC)
    query = ResolveRequest(prefer=["freshness", "offline_availability"])
    response = resolve_candidates(
        query,
        [candidate],
        metadata={
            candidate.version.id: ResolutionMetadata(
                freshness_at=now - timedelta(days=10), offline_available=True
            )
        },
        vocabulary_version="2026-08-10",
        now=now,
    )
    assert response.selected is not None
    assert response.selected.criteria["offline_availability"] == 1.0
    assert response.selected.freshness_at == now - timedelta(days=10)

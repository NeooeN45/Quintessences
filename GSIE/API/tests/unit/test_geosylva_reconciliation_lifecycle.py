"""Cycle de vie BFF avec doubles aval explicitement synthétiques.

Ces tests portent sur le transport, la provenance et les refus. Les statuts
de validation simulés ne constituent aucune homologation scientifique des
moteurs, de DEC-000073 ou des écarts E01 à E06.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.diagnostic.schemas import EtatGlobalDeclare
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference
from gsie_api.engines.orchestration.hydration import HydratationVideError, StationIntrouvableError
from gsie_api.engines.orchestration.preparation import (
    EtatGlobalNonSourceError,
    RapportPreparation,
    ReglesQualifieesAbsentesError,
    ResultatPreparation,
)
from gsie_api.engines.orchestration.schemas import QualificationParRegle
from gsie_api.engines.reasoning.schemas import (
    BlocContexte,
    Conclusion,
    EtapeInference,
    InferenceResult,
    RegleInference,
    StationContexte,
)
from gsie_api.engines.validation.schemas import ValidationStatut
from gsie_api.geosylva import service as service_module
from gsie_api.geosylva import worker
from gsie_api.geosylva.cubage_schemas import CubageSyncRequest, canonical_cubage_fingerprint
from gsie_api.geosylva.cubage_service import GeoSylvaCubageService
from gsie_api.geosylva.publication import RECOMMENDATION_WARNING, build_scientific_result
from gsie_api.geosylva.repository import (
    AnalysisIdempotencyConflictError,
    GeoSylvaAnalysisRepository,
)
from gsie_api.geosylva.schemas import GeoSylvaAnalysisRequest, canonical_request_fingerprint
from gsie_api.geosylva.service import GeoSylvaAnalysisService
from gsie_api.infrastructure.models.geosylva_analysis import GeoSylvaAnalysisJobModel
from gsie_api.infrastructure.models.geosylva_cubage import GeoSylvaCubageSessionModel
from tests.unit.test_geosylva_reconciliation_routes import (
    analysis_request_payload,
    cubage_request_payload,
)

if TYPE_CHECKING:
    from uuid import UUID

_NOW = datetime(2026, 11, 16, 10, tzinfo=UTC)
_SOURCE = SourceReference(
    type_source="observation_terrain",
    auteur="Fixture synthétique de non-régression",
    reference="fixture://reconciliation/contrat-seulement",
    version_source="test",
)


def _session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def _scalar(value: object) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _request() -> GeoSylvaAnalysisRequest:
    return GeoSylvaAnalysisRequest.model_validate(analysis_request_payload())


def _job(
    request: GeoSylvaAnalysisRequest | None = None, **changes: Any
) -> GeoSylvaAnalysisJobModel:
    request = request or _request()
    values = {
        "id": uuid4(),
        "account_id": uuid4(),
        "request_id": request.request_id,
        "station_id": request.station_id,
        "request_payload": request.model_dump(mode="json"),
        "request_fingerprint": canonical_request_fingerprint(request),
        "status": "running",
        "progress_percent": 5,
        "attempt_count": 1,
        "trace_id": "trace-job-origine",
        "lease_expires_at": _NOW + timedelta(minutes=10),
        "started_at": _NOW,
    }
    return GeoSylvaAnalysisJobModel(**(values | changes))


def _fingerprint(payload: Any) -> str:
    encoded = json.dumps(payload.model_dump(mode="json"), sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _preparation(station_id: UUID) -> ResultatPreparation:
    """Le niveau E et les valeurs test ne décrivent aucune station réelle."""
    block = BlocContexte(
        source_moteur="TERRAIN",
        source=_SOURCE,
        evidence_level=EvidenceLevel.E,
        valeurs={"signal_fixture": 1},
        date_observation=_NOW,
    )
    context = StationContexte(pedologie=block, correlations=[block])
    rule = RegleInference(
        identifiant="fixture-contrat",
        condition="pedologie_signal_fixture == 1",
        enonce_conclusion="Le signal synthétique de contrat est présent.",
        source=_SOURCE,
        evidence_level=EvidenceLevel.E,
        niveau_confiance=0,
    )
    qualification = QualificationParRegle(
        identifiant_regle=rule.identifiant, role="contrainte", domaine_element="pedologique"
    )
    state = EtatGlobalDeclare(
        etat="vigueur_reduite",
        justification="Étiquette synthétique imposée par le schéma ; aucune station réelle.",
        source=_SOURCE,
        evidence_level=EvidenceLevel.E,
    )
    intake_id = uuid4()
    report = RapportPreparation(
        station_id=station_id,
        regles_selectionnees=[rule.identifiant],
        regles_versions={rule.identifiant: 7},
        regles_fingerprint={rule.identifiant: _fingerprint(rule)},
        regles_snapshot=[rule],
        qualifications_utilisees=[qualification],
        etat_global_field_intake=intake_id,
        etat_global_snapshot=state,
        etat_global_fingerprint=_fingerprint(state),
        contexte_snapshot=context,
        contexte_fingerprint=_fingerprint(context),
    )
    return ResultatPreparation(
        contexte=context,
        rapport=report,
        regles=[rule],
        qualifications=[qualification],
        etat_global=state,
        etat_global_field_intake=intake_id,
    )


def _analysis(request: GeoSylvaAnalysisRequest, status: ValidationStatut) -> SimpleNamespace:
    """Double de sortie aval : aucun moteur scientifique n'est exécuté."""
    conclusions = [
        Conclusion(
            conclusion_id=uuid4(),
            enonce=f"Conclusion synthétique de contrat {index}",
            niveau_confiance=0,
            methode_confiance="fournie_par_regle",
            evidence_level_plancher=EvidenceLevel.E,
            chaine_inference=[
                EtapeInference(
                    ordre=1,
                    regle_appliquee="fixture-contrat",
                    source_regle=_SOURCE,
                    premisses=["signal synthétique de test = 1"],
                    conclusion_locale=f"Conclusion synthétique de contrat {index}",
                    evidence_level=EvidenceLevel.E,
                )
            ],
            sources_utilisees=[_SOURCE],
        )
        for index in range(2)
    ]
    return SimpleNamespace(
        analyse_id=uuid4(),
        requete_origine=request.request_id,
        inference=InferenceResult(
            resultat_id=uuid4(),
            requete_origine=request.request_id,
            conclusions=conclusions,
            date_inference=_NOW,
        ),
        diagnostic=SimpleNamespace(
            contradictions=[], incertitudes=["Données de test synthétiques"]
        ),
        validation=SimpleNamespace(statut=status),
    )


async def should_persist_pending_intent_when_account_submits_for_first_time() -> None:
    session, request, account_id = _session(), _request(), uuid4()
    session.execute.side_effect = [_scalar(None), _scalar(None)]

    job, created = await GeoSylvaAnalysisService(session).submit(
        account_id, request, now=_NOW, trace_id="trace-soumission"
    )

    assert created is True
    assert job.account_id == account_id
    assert job.request_id == request.request_id
    assert job.station_id == request.station_id
    assert job.request_payload == request.model_dump(mode="json")
    assert job.request_fingerprint == canonical_request_fingerprint(request)
    assert job.status == "pending"
    assert job.progress_percent == 0
    assert job.next_attempt_at == _NOW
    assert job.expires_at == _NOW + timedelta(days=30)
    assert job.trace_id == "trace-soumission"
    session.add.assert_called_once_with(job)
    session.flush.assert_awaited_once()
    lock, lookup = session.execute.await_args_list
    assert lock.args[1] == {"lock_key": f"geosylva-analysis:{account_id}:{request.request_id}"}
    assert set(lookup.args[0].compile().params.values()) == {account_id, request.request_id}


async def should_replay_existing_job_when_equivalent_request_is_reordered() -> None:
    session, request = _session(), _request()
    existing = _job(request)
    reordered = GeoSylvaAnalysisRequest.model_validate(
        request.model_dump(mode="json")
        | {
            "species_taxref_ids": list(reversed(request.species_taxref_ids)),
            "requested_capabilities": list(reversed(request.requested_capabilities)),
        }
    )
    session.execute.side_effect = [_scalar(None), _scalar(existing)]

    job, created = await GeoSylvaAnalysisRepository(session).create_or_get(
        existing.account_id, reordered, now=_NOW, trace_id="trace-rejeu"
    )

    assert job is existing
    assert created is False
    assert job.trace_id == "trace-job-origine"
    session.add.assert_not_called()
    session.flush.assert_not_awaited()


async def should_refuse_reused_request_key_when_intent_changes() -> None:
    session, request = _session(), _request()
    existing = _job(request)
    changed = GeoSylvaAnalysisRequest.model_validate(
        request.model_dump(mode="json") | {"maximum_depth": request.maximum_depth + 1}
    )
    session.execute.side_effect = [_scalar(None), _scalar(existing)]

    with pytest.raises(AnalysisIdempotencyConflictError, match="demande différente"):
        await GeoSylvaAnalysisRepository(session).create_or_get(
            existing.account_id, changed, now=_NOW, trace_id="trace-conflit"
        )

    session.add.assert_not_called()
    session.flush.assert_not_awaited()
    assert existing.request_payload == request.model_dump(mode="json")


async def should_filter_owned_job_lookup_when_account_reads_status() -> None:
    session, account_id, analysis_id = _session(), uuid4(), uuid4()
    session.execute.return_value = _scalar(None)
    repository = GeoSylvaAnalysisRepository(session)

    assert await repository.get_owned(analysis_id, account_id) is None

    statement = session.execute.await_args.args[0]
    assert set(statement.compile().params.values()) == {analysis_id, account_id}
    session.get.return_value = _job(id=analysis_id)
    assert await repository.get(analysis_id) is session.get.return_value
    session.get.assert_awaited_once_with(GeoSylvaAnalysisJobModel, analysis_id)


@pytest.mark.parametrize("previous_progress", [0, 42])
async def should_lease_eligible_job_when_worker_claims_queue(previous_progress: int) -> None:
    session = _session()
    previous_start = _NOW - timedelta(minutes=11) if previous_progress else None
    job = _job(progress_percent=previous_progress, started_at=previous_start, attempt_count=1)
    session.execute.return_value = _scalar(job)

    claimed = await GeoSylvaAnalysisRepository(session).claim_next(now=_NOW)

    assert claimed is job
    assert job.status == "running"
    assert job.progress_percent == max(previous_progress, 5)
    assert job.started_at == (previous_start or _NOW)
    assert job.lease_expires_at == _NOW + timedelta(minutes=10)
    assert job.attempt_count == 2
    statement = session.execute.await_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    sql = str(compiled)
    assert "FOR UPDATE SKIP LOCKED" in sql
    assert "expires_at >" in sql
    assert "next_attempt_at <=" in sql
    assert "lease_expires_at <" in sql
    assert set(compiled.params.values()) == {_NOW, "pending", "running", 1}
    session.flush.assert_awaited_once()


async def should_leave_queue_unchanged_when_no_job_is_eligible() -> None:
    session = _session()
    session.execute.return_value = _scalar(None)

    assert await GeoSylvaAnalysisRepository(session).claim_next(now=_NOW) is None

    session.flush.assert_not_awaited()


@pytest.mark.parametrize(
    ("validation_status", "capabilities", "expected_status"),
    [
        (ValidationStatut.valide, [], "completed"),
        (ValidationStatut.partiellement_valide, [], "partial"),
        (ValidationStatut.valide, ["climate"], "partial"),
        (ValidationStatut.bloque, [], "failed"),
    ],
)
async def should_preserve_preparation_and_map_aval_state_when_execution_finishes(
    monkeypatch: pytest.MonkeyPatch,
    validation_status: ValidationStatut,
    capabilities: list[str],
    expected_status: str,
) -> None:
    session = _session()
    request = GeoSylvaAnalysisRequest.model_validate(
        analysis_request_payload()
        | {
            "requested_capabilities": ["reasoning", "diagnostic", "validation", *capabilities],
            "evidence_levels": {"pedologie": "E"},
        }
    )
    job = _job(request, started_at=None)
    preparation = _preparation(request.station_id)
    analysis = _analysis(request, validation_status)
    preparer, engine = AsyncMock(), AsyncMock()
    preparer.prepare.return_value = preparation
    engine.analyser_idempotente.return_value = analysis
    monkeypatch.setattr(service_module, "StationPreparationService", lambda _session: preparer)
    monkeypatch.setattr(service_module, "OrchestrationEngine", lambda _session: engine)

    await GeoSylvaAnalysisService(session).execute(job, now=_NOW)

    preparer.prepare.assert_awaited_once_with(
        request.station_id, niveaux_declares={"pedologie": EvidenceLevel.E}
    )
    analysis_request, observed_now = engine.analyser_idempotente.await_args.args
    assert observed_now == _NOW
    assert analysis_request.requete_id == request.request_id
    assert analysis_request.station_id == request.station_id
    assert analysis_request.contexte == preparation.contexte
    assert analysis_request.regles == preparation.regles
    assert analysis_request.qualifications == preparation.qualifications
    assert analysis_request.etat_global == preparation.etat_global
    assert analysis_request.question == request.question
    assert analysis_request.objectif_forestier == request.objective
    assert analysis_request.profondeur_max == request.maximum_depth
    assert analysis_request.alternatives_demandees == request.alternatives_requested
    assert job.preparation_snapshot == preparation.rapport.model_dump(mode="json")
    assert job.analysis_run_id == analysis.analyse_id
    assert job.status == expected_status
    assert job.progress_percent == 100
    assert job.completed_at is not None
    assert job.lease_expires_at is None
    assert job.completed_engines == ["reasoning", "diagnostic", "validation", "orchestration"]
    assert job.unavailable_engines == capabilities
    assert job.result_payload["trace_id"] == "trace-job-origine"
    assert job.result_payload["data_versions"]["rules"] == {"fixture-contrat": 7}
    assert job.result_payload["sources"] == [_SOURCE.model_dump(mode="json")]
    assert job.result_payload["recommendations"] == []
    if expected_status == "failed":
        assert job.error_code == "SCIENTIFIC_VALIDATION_BLOCKED"
        assert job.error_detail == "La validation scientifique a bloqué la publication complète"
    session.flush.assert_awaited()


@pytest.mark.parametrize(
    "error",
    [
        ReglesQualifieesAbsentesError("AUCUNE_REGLE_QUALIFIEE"),
        EtatGlobalNonSourceError("ETAT_GLOBAL_NON_SOURCE"),
    ],
)
async def should_avoid_orchestration_and_publication_when_preparation_refuses(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    session, job = _session(), _job()
    preparer, engine = AsyncMock(), MagicMock()
    preparer.prepare.side_effect = error
    monkeypatch.setattr(service_module, "StationPreparationService", lambda _session: preparer)
    monkeypatch.setattr(service_module, "OrchestrationEngine", engine)

    with pytest.raises(type(error), match=str(error)):
        await GeoSylvaAnalysisService(session).execute(job, now=_NOW)

    engine.assert_not_called()
    assert job.preparation_snapshot is None
    assert job.result_payload is None
    session.flush.assert_not_awaited()


@pytest.mark.parametrize(
    ("attempt_count", "retryable", "expected"),
    [(1, True, "pending"), (2, True, "pending"), (3, True, "failed"), (1, False, "failed")],
)
async def should_bound_retries_when_execution_reports_failure(
    attempt_count: int, retryable: bool, expected: str
) -> None:
    job = _job(attempt_count=attempt_count)

    await GeoSylvaAnalysisService(_session()).mark_failure(
        job, error_code="E" * 120, public_detail="d" * 2100, now=_NOW, retryable=retryable
    )

    assert job.status == expected
    assert job.lease_expires_at is None
    if expected == "pending":
        assert job.next_attempt_at == _NOW + timedelta(seconds=2**attempt_count)
        assert job.completed_at is None
        assert job.result_payload is None
    else:
        assert job.progress_percent == 100
        assert job.completed_at == _NOW
        assert job.error_code == "E" * 100
        assert job.error_detail == "d" * 2000


def should_preserve_sources_versions_and_limits_when_building_public_projection() -> None:
    request = _request()
    analysis = _analysis(request, ValidationStatut.partiellement_valide)
    analysis.inference = analysis.inference.model_copy(
        update={"resultat_partiel": True, "regles_non_appliquees": ["fixture-limite"]}
    )
    preparation = _preparation(request.station_id)
    report = preparation.rapport
    report_before = report.model_dump(mode="json")

    public = build_scientific_result(
        analysis,
        report,
        requested_capabilities=[
            "reasoning",
            "diagnostic",
            "validation",
            "recommendation",
            "climate",
            "climate",
        ],
        started_at=_NOW,
        completed_at=_NOW + timedelta(milliseconds=1250),
        trace_id="trace-projection",
    )

    assert public.analysis_id == analysis.analyse_id
    assert public.request_id == request.request_id
    assert public.station_id == request.station_id
    assert public.sources == [_SOURCE.model_dump(mode="json")]
    assert public.conclusions == [
        item.model_dump(mode="json") for item in analysis.inference.conclusions
    ]
    assert [step["conclusion_id"] for step in public.calculations] == [
        str(item.conclusion_id) for item in analysis.inference.conclusions
    ]
    assert all(
        step["source_regle"] == _SOURCE.model_dump(mode="json") for step in public.calculations
    )
    assert public.data_versions == {
        "rules": report.regles_versions,
        "rule_fingerprints": report.regles_fingerprint,
        "global_state_fingerprint": report.etat_global_fingerprint,
        "field_intake_id": str(report.etat_global_field_intake),
    }
    assert public.data_coverage == {
        "present_domains": ["correlation", "pedologie"],
        "missing_domains": ["botanique", "climat", "geographie", "peuplement"],
        "context_fingerprint": report.contexte_fingerprint,
    }
    assert [item["domain"] for item in public.observations] == ["pedologie", "correlation"]
    assert public.recommendations == []
    assert public.unavailable_engines == ["climate", "recommendation"]
    assert RECOMMENDATION_WARNING in public.warnings
    assert len(public.warnings) == 2
    assert any("profondeur maximale" in warning for warning in public.uncertainties)
    assert "Données de test synthétiques" in public.uncertainties
    assert public.duration_ms == 1250
    assert public.trace_id == "trace-projection"
    assert report == preparation.rapport
    assert report.model_dump(mode="json") == report_before


@pytest.fixture
def worker_dependencies(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    claim_session, execution_session = _session(), _session()
    claim_session.__aenter__.return_value = claim_session
    execution_session.__aenter__.return_value = execution_session
    factory = MagicMock(side_effect=[claim_session, execution_session])
    claim_repository, execution_repository, service = AsyncMock(), AsyncMock(), AsyncMock()
    repositories = MagicMock(side_effect=[claim_repository, execution_repository])
    context = AsyncMock()
    monkeypatch.setattr(worker, "async_session_factory", factory)
    monkeypatch.setattr(worker, "GeoSylvaAnalysisRepository", repositories)
    monkeypatch.setattr(worker, "GeoSylvaAnalysisService", lambda _session: service)
    monkeypatch.setattr(worker, "set_internal_worker_context", context)
    job = _job()
    claim_repository.claim_next.return_value = job
    execution_repository.get.return_value = job
    return SimpleNamespace(
        claim_session=claim_session,
        execution_session=execution_session,
        factory=factory,
        claim_repository=claim_repository,
        execution_repository=execution_repository,
        context=context,
        service=service,
        job=job,
    )


async def should_commit_claim_and_execute_owned_job_when_worker_finds_work(
    worker_dependencies: SimpleNamespace,
) -> None:
    deps = worker_dependencies

    assert await worker.process_next() is True

    deps.claim_session.commit.assert_awaited_once()
    deps.execution_repository.get.assert_awaited_once_with(deps.job.id)
    deps.service.execute.assert_awaited_once_with(deps.job, now=deps.job.started_at)
    deps.service.mark_failure.assert_not_awaited()
    deps.execution_session.commit.assert_awaited_once()
    assert [call.args[0] for call in deps.context.await_args_list] == [
        deps.claim_session,
        deps.execution_session,
    ]


async def should_return_idle_when_worker_cannot_claim_a_job(
    worker_dependencies: SimpleNamespace,
) -> None:
    deps = worker_dependencies
    deps.claim_repository.claim_next.return_value = None

    assert await worker.process_next() is False

    deps.claim_session.commit.assert_awaited_once()
    deps.execution_repository.get.assert_not_awaited()
    deps.service.execute.assert_not_awaited()
    assert deps.factory.call_count == 1


async def should_skip_execution_when_claimed_job_disappeared(
    worker_dependencies: SimpleNamespace,
) -> None:
    deps = worker_dependencies
    deps.execution_repository.get.return_value = None

    assert await worker.process_next() is False

    deps.service.execute.assert_not_awaited()
    deps.service.mark_failure.assert_not_awaited()
    deps.execution_session.commit.assert_not_awaited()


@pytest.mark.parametrize(
    ("error", "retryable"),
    [
        (StationIntrouvableError("station absente"), False),
        (HydratationVideError("contexte absent"), False),
        (ReglesQualifieesAbsentesError("AUCUNE_REGLE_QUALIFIEE"), False),
        (EtatGlobalNonSourceError("ETAT_GLOBAL_NON_SOURCE"), False),
        (RuntimeError("information technique interne à ne pas publier"), True),
    ],
)
async def should_distinguish_scientific_refusal_from_technical_retry_when_worker_fails(
    worker_dependencies: SimpleNamespace, error: Exception, retryable: bool
) -> None:
    deps = worker_dependencies
    deps.service.execute.side_effect = error

    assert await worker.process_next() is True

    deps.service.mark_failure.assert_awaited_once()
    args, kwargs = deps.service.mark_failure.await_args
    assert args == (deps.job,)
    assert kwargs["error_code"] == type(error).__name__
    assert kwargs["retryable"] is retryable
    assert kwargs["public_detail"] == (
        "Échec technique temporaire de l'analyse" if retryable else str(error)
    )
    deps.execution_session.commit.assert_awaited_once()


class _StopWorkerError(Exception):
    """Arrêt contrôlé de la boucle infinie après une itération utile."""


@pytest.mark.parametrize("processed", [False, True])
async def should_emit_heartbeat_and_sleep_only_when_idle(
    monkeypatch: pytest.MonkeyPatch, processed: bool
) -> None:
    process = AsyncMock(side_effect=[processed, _StopWorkerError("arrêt du test")])
    heartbeat, logging, sleep = MagicMock(), MagicMock(), AsyncMock()
    monkeypatch.setattr(worker, "process_next", process)
    monkeypatch.setattr(worker, "write_worker_heartbeat", heartbeat)
    monkeypatch.setattr(worker, "setup_logging", logging)
    monkeypatch.setattr(worker.asyncio, "sleep", sleep)
    monkeypatch.setenv("GSIE_GEOSYLVA_WORKER_HEALTHCHECK_PATH", "/tmp/fixture-geosylva-heartbeat")

    with pytest.raises(_StopWorkerError, match="arrêt du test"):
        await worker.run()

    logging.assert_called_once_with("INFO", "worker")
    heartbeat.assert_called_once_with("/tmp/fixture-geosylva-heartbeat")
    if processed:
        sleep.assert_not_awaited()
    else:
        sleep.assert_awaited_once_with(1.0)


async def should_replay_cubage_packet_without_server_verification_when_owner_reads() -> None:
    session, account_id = _session(), uuid4()
    request = CubageSyncRequest.model_validate(cubage_request_payload(account_id))
    model = GeoSylvaCubageSessionModel(
        session_id=request.session.session_id,
        account_id=account_id,
        calculation_id=request.calculation.calculation_id,
        request_payload=request.model_dump(mode="json"),
        request_fingerprint=canonical_cubage_fingerprint(request),
        status="synced",
        warnings=list(request.calculation.quality.warnings),
    )
    session.execute.return_value = _scalar(model)
    service = GeoSylvaCubageService(session)

    response, created = await service.synchronize(
        account_id, request, idempotency_key="clé-fixture", trace_id="trace-rejeu", now=_NOW
    )
    stored = await service.get_owned(model.session_id, account_id, trace_id="trace-lecture")

    assert created is False
    assert response.status == "synced"
    assert response.session_id == model.session_id
    assert response.calculation_id == model.calculation_id
    assert response.warnings == request.calculation.quality.warnings
    assert response.server_verification_id is None
    assert response.trace_id == "trace-rejeu"
    assert stored.session == request.session
    assert stored.measurements == request.measurements
    assert stored.calculation == request.calculation
    assert stored.verification is None
    assert stored.trace_id == "trace-lecture"
    session.add.assert_not_called()
    session.flush.assert_not_awaited()


async def should_persist_cubage_packet_as_supplied_when_no_prior_record_exists() -> None:
    session, account_id = _session(), uuid4()
    request = CubageSyncRequest.model_validate(cubage_request_payload(account_id))
    session.execute.side_effect = [_scalar(None), _scalar(None)]
    session.get.return_value = None
    transaction = AsyncMock()
    session.begin_nested.return_value = transaction
    idempotency_key = str(uuid4())

    response, created = await GeoSylvaCubageService(session).synchronize(
        account_id, request, idempotency_key=idempotency_key, trace_id="trace-création", now=_NOW
    )

    assert created is True
    model = session.add.call_args.args[0]
    assert model.account_id == account_id
    assert model.idempotency_key == idempotency_key
    assert model.request_fingerprint == canonical_cubage_fingerprint(request)
    assert model.request_payload == request.model_dump(mode="json")
    assert model.request_payload["calculation"]["quality"]["status"] == "blocked"
    assert model.created_at == model.updated_at == _NOW
    assert response.status == "synced"
    assert response.server_verification_id is None
    assert response.warnings == request.calculation.quality.warnings
    session.begin_nested.assert_called_once()
    transaction.__aenter__.assert_awaited_once()
    transaction.__aexit__.assert_awaited_once_with(None, None, None)
    session.flush.assert_awaited_once()
    session.rollback.assert_not_awaited()


async def should_hide_cubage_session_when_repository_finds_no_owned_record() -> None:
    session, account_id, session_id = _session(), uuid4(), uuid4()
    session.execute.return_value = _scalar(None)

    assert (
        await GeoSylvaCubageService(session).get_owned(
            session_id, account_id, trace_id="trace-absente"
        )
        is None
    )

    statement = session.execute.await_args.args[0]
    assert set(statement.compile().params.values()) == {session_id, account_id}

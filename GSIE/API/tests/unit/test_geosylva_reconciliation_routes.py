"""Non-régression du contrat BFF ; aucune qualification scientifique réelle.

Les dépendances de persistance sont simulées ; l'authentification JWT, les
validations Pydantic et la sérialisation HTTP restent réellement exécutées.
"""

from __future__ import annotations

from datetime import UTC, datetime
from inspect import unwrap
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import Request, Response
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.data.schemas import CatalogResponse, DatasetResponse, PageInfo
from gsie_api.geosylva import router as bff
from gsie_api.geosylva.cubage_schemas import CubageGeometry, CubageSyncRequest
from gsie_api.geosylva.repository import AnalysisIdempotencyConflictError
from gsie_api.geosylva.schemas import (
    GeoJsonGeometry,
    GeoSylvaAnalysisRequest,
    ScientificAnalysisResult,
    canonical_request_fingerprint,
)
from gsie_api.geosylva.service import GeoSylvaAnalysisService
from gsie_api.infrastructure.database import get_db_user_rls
from gsie_api.infrastructure.models.enums import DatasetStatus
from gsie_api.infrastructure.models.geosylva_analysis import GeoSylvaAnalysisJobModel

if TYPE_CHECKING:
    from collections.abc import Iterator

_NOW = datetime(2026, 11, 16, 10, tzinfo=UTC)


def analysis_request_payload() -> dict[str, Any]:
    """Contrat hérité avec géométrie et espèces déclarées ; DEC-000073 non homologuée."""
    return {
        "request_id": str(uuid4()),
        "station_id": str(uuid4()),
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[2.0, 46.0], [2.1, 46.0], [2.1, 46.1], [2.0, 46.0]]],
        },
        "species_taxref_ids": [11612, 11614],
        "question": "Contrôler le contrat de réponse de cette station de test ?",
        "objective": "mixte",
        "app_version": "test-reconciliation",
    }


def cubage_request_payload(account_id: UUID | None = None) -> dict[str, Any]:
    """Paquet synthétique : aucun résultat de cubage n'est calculé ou qualifié."""
    return {
        "session": {
            "session_id": str(uuid4()),
            "owner_account_id": str(account_id) if account_id else None,
            "purpose": "other",
            "created_at": _NOW.isoformat(),
            "updated_at": _NOW.isoformat(),
            "revision": 1,
            "sync_state": "QUEUED_FOR_SYNC",
            "session_fingerprint": "a" * 64,
        },
        "measurements": {"items": [], "measurements_fingerprint": "b" * 64},
        "calculation": {
            "calculation_id": str(uuid4()),
            "engine": "fixture.cubage",
            "engine_version": "test",
            "method_id": "FIXTURE_CONTRAT",
            "method_version": "test",
            "quality": {"status": "blocked", "warnings": ["Jeu synthétique de test"]},
            "inputs_fingerprint": "c" * 64,
            "result_fingerprint": "d" * 64,
            "calculated_at": _NOW.isoformat(),
        },
        "client": {
            "application_id": "geosylva",
            "application_version": "test",
            "os_version": "test",
            "locale": "fr-FR",
        },
    }


def _headers(account_id: UUID | str) -> dict[str, str]:
    token = create_access_token(subject=str(account_id), claims={"roles": ["user"]})
    return {"Authorization": f"Bearer {token}"}


def _job(status: str = "pending", **changes: Any) -> GeoSylvaAnalysisJobModel:
    values = {
        "id": uuid4(),
        "status": status,
        "progress_percent": 35 if status == "running" else 0,
        "completed_engines": ["reasoning"],
        "unavailable_engines": ["climate"],
        "warnings": ["Données aval simulées pour le contrat"],
        "created_at": _NOW,
        "updated_at": _NOW,
        "result_payload": None,
    }
    return GeoSylvaAnalysisJobModel(**(values | changes))


@pytest.fixture
def bff_client(
    mock_lifespan: object, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[TestClient, AsyncMock, AsyncMock, AsyncMock, AsyncMock]]:
    del mock_lifespan
    app = create_app()
    session = AsyncMock(spec=AsyncSession)
    service = AsyncMock()
    repository = AsyncMock()
    registry = AsyncMock()
    app.dependency_overrides[get_db_user_rls] = lambda: session
    monkeypatch.setattr(bff, "GeoSylvaAnalysisService", lambda _session: service)
    monkeypatch.setattr(bff, "GeoSylvaAnalysisRepository", lambda _session: repository)
    monkeypatch.setattr(bff, "DataRegistryService", lambda _session: registry)
    with TestClient(app) as client:
        yield client, session, service, repository, registry


@pytest.mark.parametrize("created", [True, False], ids=["nouvelle", "rejeu"])
def should_accept_async_submission_when_idempotency_header_matches(
    bff_client: tuple, created: bool
) -> None:
    client, _session, service, _repository, _registry = bff_client
    payload = analysis_request_payload()
    account_id, job = uuid4(), _job()
    client_trace_id = str(uuid4())
    service.submit.return_value = job, created

    response = client.post(
        "/api/v1/geosylva/analyses",
        json=payload,
        headers=_headers(account_id)
        | {"Idempotency-Key": payload["request_id"], "X-Trace-ID": client_trace_id},
    )

    assert response.status_code == 202
    assert response.json() == {
        "analysis_id": str(job.id),
        "status": "pending",
        "status_url": f"/api/v1/geosylva/analyses/{job.id}",
        "result_url": f"/api/v1/geosylva/analyses/{job.id}/result",
        "retry_after_seconds": 2,
    }
    assert response.headers["Location"] == response.json()["status_url"]
    assert response.headers["Idempotency-Key"] == payload["request_id"]
    service.submit.assert_awaited_once()
    args, kwargs = service.submit.await_args
    assert args == (account_id, GeoSylvaAnalysisRequest.model_validate(payload))
    assert kwargs["trace_id"] == response.headers["X-Trace-ID"]
    assert kwargs["trace_id"] == client_trace_id
    assert kwargs["now"].tzinfo is UTC


def should_document_uncorrelated_job_trace_when_client_supplies_no_trace_header(
    bff_client: tuple, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Défaut existant : le contexte de logs n'alimente pas request.state.

    Le service et le repository réels conservent alors n/a dans le job,
    tandis que le middleware retourne un UUID. Aucune correction implicite.
    """
    client, session, _service, _repository, _registry = bff_client
    monkeypatch.setattr(bff, "GeoSylvaAnalysisService", GeoSylvaAnalysisService)
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    async def assign_generated_job_id() -> None:
        session.add.call_args.args[0].id = uuid4()

    session.flush.side_effect = assign_generated_job_id
    payload = analysis_request_payload()

    response = client.post(
        "/api/v1/geosylva/analyses",
        json=payload,
        headers=_headers(uuid4()) | {"Idempotency-Key": payload["request_id"]},
    )

    assert response.status_code == 202
    job = session.add.call_args.args[0]
    assert job.trace_id == "n/a"
    assert UUID(response.headers["X-Trace-ID"]).version == 4
    assert job.trace_id != response.headers["X-Trace-ID"]


def should_reject_submission_when_header_names_another_request(bff_client: tuple) -> None:
    client, _session, service, _repository, _registry = bff_client

    response = client.post(
        "/api/v1/geosylva/analyses",
        json=analysis_request_payload(),
        headers=_headers(uuid4()) | {"Idempotency-Key": str(uuid4())},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Idempotency-Key doit être égal à request_id"
    service.submit.assert_not_awaited()


def should_return_conflict_when_request_key_has_changed_content(bff_client: tuple) -> None:
    client, _session, service, _repository, _registry = bff_client
    payload = analysis_request_payload()
    service.submit.side_effect = AnalysisIdempotencyConflictError("demande différente")

    response = client.post(
        "/api/v1/geosylva/analyses",
        json=payload,
        headers=_headers(uuid4()) | {"Idempotency-Key": payload["request_id"]},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "demande différente"


@pytest.mark.parametrize("subject", ["compte-non-nominatif", ""])
def should_reject_analysis_access_when_token_subject_is_not_uuid(
    bff_client: tuple, subject: str
) -> None:
    client, _session, _service, repository, _registry = bff_client

    response = client.get(f"/api/v1/geosylva/analyses/{uuid4()}", headers=_headers(subject))

    assert response.status_code == 401
    repository.get_owned.assert_not_awaited()


@pytest.mark.parametrize("path", ["", "/result"])
def should_hide_absent_or_foreign_analysis_when_owner_reads_it(
    bff_client: tuple, path: str
) -> None:
    client, _session, _service, repository, _registry = bff_client
    account_id, analysis_id = uuid4(), uuid4()
    repository.get_owned.return_value = None

    response = client.get(
        f"/api/v1/geosylva/analyses/{analysis_id}{path}", headers=_headers(account_id)
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Analyse introuvable"
    repository.get_owned.assert_awaited_once_with(analysis_id, account_id)


@pytest.mark.parametrize(
    "status", ["pending", "running", "completed", "partial", "failed", "expired"]
)
def should_report_job_state_when_owner_polls(bff_client: tuple, status: str) -> None:
    client, _session, _service, repository, _registry = bff_client
    account_id, job = uuid4(), _job(status, error_code="TEMPORAIRE" if status == "failed" else None)
    repository.get_owned.return_value = job

    response = client.get(f"/api/v1/geosylva/analyses/{job.id}", headers=_headers(account_id))

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == status
    assert data["progress_percent"] == job.progress_percent
    assert data["completed_engines"] == job.completed_engines
    assert data["unavailable_engines"] == job.unavailable_engines
    assert data["warnings"] == job.warnings
    assert data["error_code"] == job.error_code
    retry = 2 if status in {"pending", "running"} else None
    assert data["retry_after_seconds"] == retry
    repository.get_owned.assert_awaited_once_with(job.id, account_id)


async def should_advertise_two_seconds_when_submission_handler_accepts_intent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contrat du handler isolé ; le test HTTP ci-dessous distingue SlowAPI."""
    service = AsyncMock()
    service.submit.return_value = _job(), True
    monkeypatch.setattr(bff, "GeoSylvaAnalysisService", lambda _session: service)
    request = GeoSylvaAnalysisRequest.model_validate(analysis_request_payload())
    response = Response()

    accepted = await unwrap(bff.create_analysis)(
        body=request,
        request=Request({"type": "http", "headers": []}),
        response=response,
        session=AsyncMock(spec=AsyncSession),
        current_user={"sub": str(uuid4())},
        idempotency_key=str(request.request_id),
    )

    assert accepted.retry_after_seconds == 2
    assert response.headers["Retry-After"] == "2"


@pytest.mark.parametrize(
    "status", ["pending", "running", "completed", "partial", "failed", "expired"]
)
async def should_set_polling_hint_only_when_handler_state_is_unfinished(
    monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    repository = AsyncMock()
    job = _job(status)
    repository.get_owned.return_value = job
    monkeypatch.setattr(bff, "GeoSylvaAnalysisRepository", lambda _session: repository)
    response = Response()

    result = await unwrap(bff.get_analysis_status)(
        analysis_id=job.id,
        request=Request({"type": "http", "headers": []}),
        response=response,
        session=AsyncMock(spec=AsyncSession),
        current_user={"sub": str(uuid4())},
    )

    expected = 2 if status in {"pending", "running"} else None
    assert result.retry_after_seconds == expected
    assert response.headers.get("Retry-After") == (str(expected) if expected else None)


@pytest.mark.parametrize("status", ["pending", "completed"])
def should_expose_rate_window_in_http_retry_header_when_slowapi_is_active(
    bff_client: tuple, status: str
) -> None:
    """Écart constaté : SlowAPI remplace l'en-tête du handler même hors 429.

    Ce constat de transport ne garantit donc pas un délai HTTP de 2 secondes
    et ne constitue pas une approbation du comportement du middleware.
    """
    client, _session, _service, repository, _registry = bff_client
    job = _job(status)
    repository.get_owned.return_value = job

    response = client.get(f"/api/v1/geosylva/analyses/{job.id}", headers=_headers(uuid4()))

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "60"
    assert 2 < int(response.headers["Retry-After"]) <= 61
    assert response.json()["retry_after_seconds"] == (2 if status == "pending" else None)


@pytest.mark.parametrize(
    ("status", "http_status", "detail"),
    [
        ("pending", 409, "Résultat non disponible"),
        ("running", 409, "Résultat non disponible"),
        ("failed", 422, "L'analyse n'a produit aucun résultat scientifique publiable"),
        ("expired", 422, "L'analyse n'a produit aucun résultat scientifique publiable"),
    ],
)
def should_refuse_result_when_no_scientific_payload_exists(
    bff_client: tuple, status: str, http_status: int, detail: str
) -> None:
    client, _session, _service, repository, _registry = bff_client
    job = _job(status)
    repository.get_owned.return_value = job

    response = client.get(f"/api/v1/geosylva/analyses/{job.id}/result", headers=_headers(uuid4()))

    assert response.status_code == http_status
    assert response.json()["detail"] == detail


def should_return_stored_provenance_when_owner_reads_a_partial_result(bff_client: tuple) -> None:
    client, _session, _service, repository, _registry = bff_client
    job = _job("partial")
    result = ScientificAnalysisResult(
        analysis_id=job.id,
        request_id=uuid4(),
        station_id=uuid4(),
        summary="Projection synthétique du contrat, sans conclusion qualifiée",
        sources=[{"reference": "fixture://contrat/provenance", "version_source": "test"}],
        data_versions={"rules": {"fixture-contrat": 7}},
        warnings=["Jeu synthétique ; aucune analyse scientifique exécutée"],
        unavailable_engines=["recommendation"],
        duration_ms=1,
        trace_id="trace-origine",
        completed_at=_NOW,
    )
    job.result_payload = result.model_dump(mode="json")
    repository.get_owned.return_value = job

    response = client.get(f"/api/v1/geosylva/analyses/{job.id}/result", headers=_headers(uuid4()))

    assert response.status_code == 200
    assert response.json() == result.model_dump(mode="json")


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/analyses"),
        ("GET", f"/analyses/{uuid4()}"),
        ("GET", f"/analyses/{uuid4()}/result"),
        ("POST", "/cubage/sessions/sync"),
        ("GET", f"/cubage/sessions/{uuid4()}"),
        ("GET", "/resources"),
        ("GET", f"/resources/{uuid4()}"),
    ],
)
def should_require_authentication_when_any_bff_route_is_called(
    bff_client: tuple, method: str, path: str
) -> None:
    client, _session, service, repository, registry = bff_client

    response = client.request(method, f"/api/v1/geosylva{path}")

    assert response.status_code == 401
    service.submit.assert_not_awaited()
    repository.get_owned.assert_not_awaited()
    registry.catalog.assert_not_awaited()
    registry.dataset.assert_not_awaited()


def should_expose_paginated_production_catalog_when_authenticated(bff_client: tuple) -> None:
    client, _session, _service, _repository, registry = bff_client
    catalog = CatalogResponse(items=[], page=PageInfo(limit=7, next_cursor="suivante"))
    registry.catalog.return_value = catalog

    response = client.get(
        "/api/v1/geosylva/resources",
        params={"cursor": "courante", "limit": 7, "domain": "pedology"},
        headers=_headers(uuid4()),
    )

    assert response.status_code == 200
    assert response.json() == catalog.model_dump(mode="json")
    registry.catalog.assert_awaited_once_with(
        cursor="courante", limit=7, status=DatasetStatus.production, domain="pedology"
    )


@pytest.mark.parametrize("limit", [0, 101])
def should_reject_catalog_request_when_pagination_is_out_of_bounds(
    bff_client: tuple, limit: int
) -> None:
    client, _session, _service, _repository, registry = bff_client

    response = client.get(
        "/api/v1/geosylva/resources", params={"limit": limit}, headers=_headers(uuid4())
    )

    assert response.status_code == 422
    registry.catalog.assert_not_awaited()


def _dataset(statuses: list[DatasetStatus]) -> DatasetResponse:
    dataset_id = uuid4()
    return DatasetResponse.model_validate(
        {
            "item": {
                "dataset": {
                    "id": dataset_id,
                    "slug": None,
                    "title": "Jeu synthétique de contrat",
                    "description": "Aucune ressource réelle publiée",
                    "publisher_id": None,
                    "purpose": "reference",
                    "topic": None,
                    "primary_domain": None,
                    "domain_vocabulary_version": None,
                },
                "versions": [
                    {
                        "id": uuid4(),
                        "dataset_id": dataset_id,
                        "version": str(index),
                        "status": status,
                        **dict.fromkeys(
                            [
                                "release_date",
                                "temporal_coverage_start",
                                "temporal_coverage_end",
                                "changes",
                                "schema_hash",
                                "stats",
                                "evidence_level",
                                "evidence_basis",
                                "evidence_assessed_at",
                            ]
                        ),
                    }
                    for index, status in enumerate(statuses)
                ],
            }
        }
    )


@pytest.mark.parametrize("kind", ["absent", "staging", "sans-version"])
def should_hide_resource_when_no_production_version_exists(bff_client: tuple, kind: str) -> None:
    client, _session, _service, _repository, registry = bff_client
    registry.dataset.return_value = (
        None if kind == "absent" else _dataset([DatasetStatus.staging] if kind == "staging" else [])
    )

    response = client.get(f"/api/v1/geosylva/resources/{uuid4()}", headers=_headers(uuid4()))

    assert response.status_code == 404
    assert response.json()["detail"] == "Ressource introuvable"


def should_filter_unpublished_versions_when_resource_contains_mixed_states(
    bff_client: tuple,
) -> None:
    client, _session, _service, _repository, registry = bff_client
    dataset = _dataset([DatasetStatus.staging, DatasetStatus.production, DatasetStatus.archived])
    registry.dataset.return_value = dataset

    response = client.get(
        f"/api/v1/geosylva/resources/{dataset.item.dataset.id}", headers=_headers(uuid4())
    )

    assert response.status_code == 200
    assert response.json()["item"]["versions"] == [dataset.item.versions[1].model_dump(mode="json")]
    assert len(dataset.item.versions) == 3
    registry.dataset.assert_awaited_once_with(dataset.item.dataset.id)


@pytest.mark.parametrize(
    ("coordinates", "message"),
    [
        ([[[float("inf"), 46.0]]], "doivent être finies"),
        ([[[float("nan"), 46.0]]], "doivent être finies"),
        ([], "structure GeoJSON"),
        ([[[True, 46.0]]], "structure GeoJSON"),
        ([[[2.0, 46.0]]], "au moins quatre"),
    ],
)
def should_refuse_analysis_geometry_when_coordinates_are_unusable(
    coordinates: list, message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        GeoJsonGeometry(type="Polygon", coordinates=coordinates)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (
            "requested_capabilities",
            ["reasoning", "reasoning", "diagnostic", "validation"],
            "qu'une fois",
        ),
        ("requested_capabilities", ["reasoning"], "capacités scientifiques obligatoires"),
        ("user_constraints", ["  "], "entre 1 et 300"),
        ("user_constraints", ["a" * 301], "entre 1 et 300"),
        ("contexte", {"pedologie": {}}, "Extra inputs are not permitted"),
        ("regles", [], "Extra inputs are not permitted"),
    ],
)
def should_refuse_mobile_intent_when_validation_or_server_only_fields_are_violated(
    field: str, value: object, message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        GeoSylvaAnalysisRequest.model_validate(analysis_request_payload() | {field: value})


def should_normalize_constraints_and_default_core_when_request_is_minimal() -> None:
    payload = analysis_request_payload() | {"user_constraints": ["  conserver la trace  "]}
    request = GeoSylvaAnalysisRequest.model_validate(payload)
    reordered = GeoSylvaAnalysisRequest.model_validate(
        payload | {"species_taxref_ids": list(reversed(request.species_taxref_ids))}
    )

    assert request.requested_capabilities == ["reasoning", "diagnostic", "validation"]
    assert request.user_constraints == ["conserver la trace"]
    assert canonical_request_fingerprint(request) == canonical_request_fingerprint(reordered)


@pytest.mark.parametrize(
    ("geometry_type", "coordinates", "message"),
    [
        ("Point", [181, 46], "bornes WGS84"),
        ("Polygon", [], "structure GeoJSON"),
        ("Polygon", [[[]]], "structure GeoJSON"),
        ("Point", [False, 46], "structure GeoJSON"),
    ],
)
def should_refuse_cubage_geometry_when_positions_are_invalid(
    geometry_type: str, coordinates: list, message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        CubageGeometry.model_validate({"type": geometry_type, "coordinates": coordinates})


def should_accept_nested_cubage_geometry_when_positions_respect_wgs84() -> None:
    coordinates = [[[[2, 46], [2.1, 46], [2.1, 46.1], [2, 46]]]]

    geometry = CubageGeometry(type="MultiPolygon", coordinates=coordinates)

    assert geometry.coordinates == coordinates


@pytest.mark.parametrize(
    ("section", "field"),
    [
        ("session", "session_fingerprint"),
        ("measurements", "measurements_fingerprint"),
        ("calculation", "inputs_fingerprint"),
        ("calculation", "result_fingerprint"),
    ],
)
def should_refuse_cubage_packet_when_fingerprint_is_not_sha256(section: str, field: str) -> None:
    payload = cubage_request_payload()
    payload[section][field] = "empreinte invalide"

    with pytest.raises(ValidationError, match="empreinte.*SHA-256"):
        CubageSyncRequest.model_validate(payload)


def should_refuse_cubage_packet_when_session_and_calculation_identifiers_collide() -> None:
    payload = cubage_request_payload()
    payload["calculation"]["calculation_id"] = payload["session"]["session_id"]

    with pytest.raises(
        ValidationError, match="session_id et calculation_id doivent être distincts"
    ):
        CubageSyncRequest.model_validate(payload)


@pytest.mark.parametrize("trace", [None, "trace-entete"])
def should_resolve_trace_when_request_has_no_middleware_state(trace: str | None) -> None:
    headers = [] if trace is None else [(b"x-trace-id", trace.encode())]
    request = Request({"type": "http", "headers": headers})

    assert bff._trace_id(request) == (trace or "n/a")


def should_prefer_state_trace_when_header_contains_another_value() -> None:
    request = Request({"type": "http", "headers": [(b"x-trace-id", b"trace-entete")]})
    request.state.trace_id = "trace-middleware"

    assert bff._trace_id(request) == "trace-middleware"

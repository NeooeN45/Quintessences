"""Contrat HTTP et barrières du Data Registry."""

from inspect import unwrap
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException, Request, Response

from gsie_api.app import create_app
from gsie_api.data import router as data_router
from gsie_api.data.schemas import ResolveRequest
from gsie_api.data.service import RegistryContractError, _safe_url

_ADMIN = {"sub": "test-admin", "roles": ["admin"]}


def _request(*, trace_id: str | None = None) -> Request:
    headers = [] if trace_id is None else [(b"x-trace-id", trace_id.encode("ascii"))]
    return Request({"type": "http", "headers": headers})


@pytest.fixture
def registry_service(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    service = MagicMock()
    monkeypatch.setattr(data_router, "DataRegistryService", lambda _session: service)
    return service


def should_register_all_phase_two_registry_routes() -> None:
    paths = {route.path for route in create_app().routes}
    assert {
        "/api/v1/data/catalog",
        "/api/v1/data/datasets/{dataset_id}",
        "/api/v1/data/providers",
        "/api/v1/data/search",
        "/api/v1/data/resolve",
        "/api/v1/data/health",
        "/api/v1/data/coverage",
    }.issubset(paths)


def should_never_expose_local_or_presigned_distribution_urls() -> None:
    assert _safe_url("local:///tmp/dataset.parquet") is None
    assert _safe_url("s3://private-bucket/object.parquet") is None
    assert _safe_url("https://example.test/object.parquet?X-Amz-Signature=secret") is None
    assert _safe_url("https://example.test/object.parquet") == "https://example.test/object.parquet"


async def should_delegate_catalog_and_translate_contract_errors(
    registry_service: MagicMock,
) -> None:
    expected = object()
    registry_service.catalog = AsyncMock(return_value=expected)
    route = unwrap(data_router.catalog)

    result = await route(
        request=_request(),
        response=Response(),
        user=_ADMIN,
        session=MagicMock(),
        cursor="cursor",
        limit=10,
        status_filter=None,
        domain="forestry",
        publisher_id=None,
    )

    assert result is expected
    registry_service.catalog.assert_awaited_once_with(
        cursor="cursor",
        limit=10,
        status=None,
        domain="forestry",
        publisher_id=None,
    )

    registry_service.catalog.side_effect = RegistryContractError("CURSOR_INVALID", "invalide")
    with pytest.raises(HTTPException) as error:
        await route(
            request=_request(),
            response=Response(),
            user=_ADMIN,
            session=MagicMock(),
            cursor="invalide",
            limit=20,
            status_filter=None,
            domain=None,
            publisher_id=None,
        )

    assert error.value.status_code == 422
    assert error.value.detail == {"code": "CURSOR_INVALID", "message": "invalide"}


async def should_return_dataset_or_explicit_not_found(
    registry_service: MagicMock,
) -> None:
    dataset_id = uuid4()
    expected = object()
    registry_service.dataset = AsyncMock(side_effect=[expected, None])
    route = unwrap(data_router.dataset)
    arguments = {
        "dataset_id": dataset_id,
        "request": _request(),
        "response": Response(),
        "user": _ADMIN,
        "session": MagicMock(),
    }

    assert await route(**arguments) is expected
    with pytest.raises(HTTPException) as error:
        await route(**arguments)

    assert error.value.status_code == 404
    assert error.value.detail == {
        "code": "DATASET_NOT_FOUND",
        "dataset_id": str(dataset_id),
    }


async def should_project_providers_with_agent_access(
    registry_service: MagicMock,
) -> None:
    expected = object()
    dataset_id = uuid4()
    registry_service.providers = AsyncMock(return_value=expected)

    result = await unwrap(data_router.providers)(
        request=_request(),
        response=Response(),
        user=_ADMIN,
        session=MagicMock(),
        dataset_id=dataset_id,
        cursor=None,
        limit=30,
    )

    assert result is expected
    registry_service.providers.assert_awaited_once_with(
        cursor=None,
        limit=30,
        dataset_id=dataset_id,
        include_agent=True,
    )


def _search_arguments() -> dict[str, object]:
    return {
        "request": _request(),
        "response": Response(),
        "user": _ADMIN,
        "session": MagicMock(),
        "theme": None,
        "bbox": None,
        "date_start": None,
        "date_end": None,
        "max_grain_m2": None,
        "minimum_evidence_level": None,
        "minimum_quality_score": None,
        "commercial_use_required": False,
        "use": "display",
        "prefer": None,
        "cursor": None,
        "limit": 20,
    }


async def should_validate_and_delegate_search(registry_service: MagicMock) -> None:
    route = unwrap(data_router.search)
    invalid_arguments = _search_arguments()
    invalid_arguments["bbox"] = [1.0, 2.0, 3.0]

    with pytest.raises(HTTPException) as error:
        await route(**invalid_arguments)

    assert error.value.status_code == 422
    assert error.value.detail["code"] == "BBOX_INVALID"

    expected = object()
    registry_service.search = AsyncMock(return_value=expected)
    assert await route(**_search_arguments()) is expected
    query = registry_service.search.await_args.args[0]
    assert query.bbox is None
    assert query.prefer == []

    registry_service.search.side_effect = RegistryContractError("SEARCH_INVALID", "invalide")
    with pytest.raises(HTTPException) as contract_error:
        await route(**_search_arguments())
    assert contract_error.value.detail["code"] == "SEARCH_INVALID"


async def should_resolve_with_trace_and_translate_contract_errors(
    registry_service: MagicMock,
) -> None:
    expected = object()
    payload = ResolveRequest()
    registry_service.resolve = AsyncMock(return_value=expected)
    route = unwrap(data_router.resolve)
    arguments = {
        "request": _request(trace_id="trace-registry"),
        "response": Response(),
        "user": _ADMIN,
        "session": MagicMock(),
        "payload": payload,
    }

    assert await route(**arguments) is expected
    registry_service.resolve.assert_awaited_once_with(payload, trace_id="trace-registry")

    registry_service.resolve.side_effect = RegistryContractError("RESOLVE_INVALID", "invalide")
    with pytest.raises(HTTPException) as error:
        await route(**arguments)
    assert error.value.detail["code"] == "RESOLVE_INVALID"


async def should_delegate_health_and_translate_contract_errors(
    registry_service: MagicMock,
) -> None:
    expected = object()
    registry_service.health = AsyncMock(return_value=expected)
    route = unwrap(data_router.health)
    arguments = {
        "request": _request(),
        "response": Response(),
        "user": _ADMIN,
        "session": MagicMock(),
        "health_status": None,
        "dataset_version_id": None,
        "distribution_id": None,
        "cursor": None,
        "limit": 20,
    }

    assert await route(**arguments) is expected
    registry_service.health.assert_awaited_once_with(
        cursor=None,
        limit=20,
        health_status=None,
        dataset_version_id=None,
        distribution_id=None,
    )

    registry_service.health.side_effect = RegistryContractError("HEALTH_INVALID", "invalide")
    with pytest.raises(HTTPException) as error:
        await route(**arguments)
    assert error.value.detail["code"] == "HEALTH_INVALID"


async def should_delegate_coverage_and_translate_contract_errors(
    registry_service: MagicMock,
) -> None:
    expected = object()
    registry_service.coverage = AsyncMock(return_value=expected)
    route = unwrap(data_router.coverage)
    arguments = {
        "request": _request(),
        "response": Response(),
        "user": _ADMIN,
        "session": MagicMock(),
        "cursor": None,
        "limit": 20,
    }

    assert await route(**arguments) is expected
    registry_service.coverage.assert_awaited_once_with(cursor=None, limit=20)

    registry_service.coverage.side_effect = RegistryContractError("COVERAGE_INVALID", "invalide")
    with pytest.raises(HTTPException) as error:
        await route(**arguments)
    assert error.value.detail["code"] == "COVERAGE_INVALID"

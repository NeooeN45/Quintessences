"""Tests du sas persistant Forge → GSIE TEST."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from gsie_api.data.analysis_bundle import load_analysis_bundle
from gsie_api.data.analysis_bundle_import import (
    AnalysisBundleImportError,
    AnalysisBundleImportResponse,
    ForgeAnalysisBundleImporter,
)
from gsie_api.data.analysis_bundle_router import import_analysis_bundle
from gsie_api.data.field_intake import FieldIntakeConflict, FieldIntakeResponse

_EXAMPLE = Path(__file__).parents[4] / "Forge" / "examples" / "gsie_analysis_bundle_v1.json"


def _bundle():
    return load_analysis_bundle(_EXAMPLE)


def _request(headers: dict[str, str] | None = None) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/data/analysis-bundles/import",
            "headers": [
                (name.lower().encode(), value.encode()) for name, value in (headers or {}).items()
            ],
        }
    )


async def should_persist_a_canonical_bundle_in_quarantine() -> None:
    service_result = FieldIntakeResponse(
        id=uuid4(), status="quarantined", duplicate=False, payload_hash="a" * 64
    )
    service = MagicMock()
    service.submit = AsyncMock(return_value=service_result)
    operator = uuid4()

    with patch("gsie_api.data.analysis_bundle_import.FieldIntakeService", return_value=service):
        result = await ForgeAnalysisBundleImporter(MagicMock(), database_role="test").import_bundle(
            _bundle(),
            submitted_by=operator,
            authorized_roles={"writer"},
            application_version="forge-test",
            trace_id="trace-001",
        )

    assert result.status == "quarantined"
    assert result.duplicate is False
    submission = service.submit.await_args.args[0]
    assert submission.kind == "analysis_bundle"
    assert submission.client_event_id == str(_bundle().bundle_id)
    assert submission.payload["bundle_fingerprint"] == _bundle().fingerprint()
    assert submission.payload["analysis_bundle"]["sources"] == sorted(
        submission.payload["analysis_bundle"]["sources"],
        key=lambda item: item["source_id"],
    )
    assert service.submit.await_args.kwargs["submitted_by"] == operator


async def should_return_duplicate_when_field_intake_replays_the_bundle() -> None:
    service_result = FieldIntakeResponse(
        id=uuid4(), status="quarantined", duplicate=True, payload_hash="b" * 64
    )
    service = MagicMock()
    service.submit = AsyncMock(return_value=service_result)

    with patch("gsie_api.data.analysis_bundle_import.FieldIntakeService", return_value=service):
        result = await ForgeAnalysisBundleImporter(MagicMock(), database_role="test").import_bundle(
            _bundle(), submitted_by=uuid4(), authorized_roles={"admin"}
        )

    assert result.duplicate is True
    assert result.field_intake_id == service_result.id


async def should_map_a_field_intake_conflict_to_a_bundle_conflict() -> None:
    service = MagicMock()
    service.submit = AsyncMock(side_effect=FieldIntakeConflict("payload différent"))

    with (
        patch("gsie_api.data.analysis_bundle_import.FieldIntakeService", return_value=service),
        pytest.raises(AnalysisBundleImportError, match="empreinte différente") as captured,
    ):
        await ForgeAnalysisBundleImporter(MagicMock(), database_role="test").import_bundle(
            _bundle(), submitted_by=uuid4(), authorized_roles={"writer"}
        )

    assert captured.value.code == "FORGE_ANALYSIS_BUNDLE_IDEMPOTENCY_CONFLICT"


async def should_refuse_non_test_profile_and_unauthorized_imports() -> None:
    importer = ForgeAnalysisBundleImporter(
        MagicMock(), database_role="test", allowed_profiles=["autre.profil"]
    )
    with pytest.raises(AnalysisBundleImportError, match="profil Forge non autorisé") as profile:
        await importer.import_bundle(_bundle(), submitted_by=uuid4(), authorized_roles={"writer"})
    assert profile.value.code == "FORGE_ANALYSIS_BUNDLE_PROFILE_NOT_ALLOWED"

    importer = ForgeAnalysisBundleImporter(MagicMock(), database_role="test")
    with pytest.raises(AnalysisBundleImportError, match="rôle writer ou admin") as auth:
        await importer.import_bundle(_bundle(), submitted_by=uuid4(), authorized_roles={"reader"})
    assert auth.value.code == "FORGE_ANALYSIS_BUNDLE_UNAUTHORIZED"


async def should_refuse_import_outside_test_database() -> None:
    with pytest.raises(AnalysisBundleImportError, match="database_role") as captured:
        await ForgeAnalysisBundleImporter(MagicMock(), database_role="production").import_bundle(
            _bundle(), submitted_by=uuid4(), authorized_roles={"admin"}
        )
    assert captured.value.code == "FORGE_ANALYSIS_BUNDLE_TEST_ONLY"


async def should_map_import_policy_errors_to_http() -> None:
    bundle = _bundle()
    result = AnalysisBundleImportResponse(
        bundle_id=bundle.bundle_id,
        station_id=bundle.station_id,
        profile_id=bundle.profile_id,
        bundle_fingerprint=bundle.fingerprint(),
        field_intake_id=uuid4(),
        status="quarantined",
        duplicate=False,
    )
    importer = MagicMock()
    importer.import_bundle = AsyncMock(return_value=result)
    with patch(
        "gsie_api.data.analysis_bundle_router.ForgeAnalysisBundleImporter",
        return_value=importer,
    ):
        response = await import_analysis_bundle(
            payload=bundle,
            request=_request({"X-Application-Version": "test", "X-Trace-Id": "trace"}),
            response=Response(),
            user={"sub": str(uuid4()), "roles": ["writer"]},
            session=MagicMock(),
        )
    assert response == result
    importer.import_bundle.assert_awaited_once()

    importer.import_bundle = AsyncMock(
        side_effect=AnalysisBundleImportError("FORGE_ANALYSIS_BUNDLE_TEST_ONLY", "test only")
    )
    with (
        patch(
            "gsie_api.data.analysis_bundle_router.ForgeAnalysisBundleImporter",
            return_value=importer,
        ),
        pytest.raises(HTTPException) as captured,
    ):
        await import_analysis_bundle(
            payload=bundle,
            request=_request(),
            response=Response(),
            user={"sub": str(uuid4()), "roles": ["writer"]},
            session=MagicMock(),
        )
    assert captured.value.status_code == 403

    importer.import_bundle = AsyncMock(
        side_effect=AnalysisBundleImportError(
            "FORGE_ANALYSIS_BUNDLE_PROFILE_NOT_ALLOWED", "profil refusé"
        )
    )
    with (
        patch(
            "gsie_api.data.analysis_bundle_router.ForgeAnalysisBundleImporter",
            return_value=importer,
        ),
        pytest.raises(HTTPException) as captured,
    ):
        await import_analysis_bundle(
            payload=bundle,
            request=_request(),
            response=Response(),
            user={"sub": str(uuid4()), "roles": ["writer"]},
            session=MagicMock(),
        )
    assert captured.value.status_code == 422

    importer.import_bundle = AsyncMock(
        side_effect=AnalysisBundleImportError(
            "FORGE_ANALYSIS_BUNDLE_IDEMPOTENCY_CONFLICT", "bundle différent"
        )
    )
    with (
        patch(
            "gsie_api.data.analysis_bundle_router.ForgeAnalysisBundleImporter",
            return_value=importer,
        ),
        pytest.raises(HTTPException) as captured,
    ):
        await import_analysis_bundle(
            payload=bundle,
            request=_request(),
            response=Response(),
            user={"sub": str(uuid4()), "roles": ["writer"]},
            session=MagicMock(),
        )
    assert captured.value.status_code == 409


async def should_require_a_jwt_subject_after_rbac_authorization() -> None:
    with pytest.raises(HTTPException) as captured:
        await import_analysis_bundle(
            payload=_bundle(),
            request=_request(),
            response=Response(),
            user={"roles": ["writer"]},
            session=MagicMock(),
        )
    assert captured.value.status_code == 401


def should_expose_the_forge_import_route() -> None:
    import gsie_api.app as app_module

    with patch.object(app_module._settings, "database_role", "test"):
        paths = {route.path for route in app_module.create_app().routes}
    assert "/api/v1/data/analysis-bundles/import" in paths

    with patch.object(app_module._settings, "database_role", "production"):
        paths = {route.path for route in app_module.create_app().routes}
    assert "/api/v1/data/analysis-bundles/import" not in paths

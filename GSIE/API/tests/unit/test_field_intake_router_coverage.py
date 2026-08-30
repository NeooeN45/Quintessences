"""Branches HTTP du routeur Field Intake, sans dépendre d'une base réelle."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, Response

from gsie_api.data.field_intake import (
    FieldIntakeConflict,
    FieldIntakeResponse,
    FieldIntakeSubmission,
)
from gsie_api.data.field_intake_router import submit_field_intake


def _submission() -> FieldIntakeSubmission:
    return FieldIntakeSubmission(
        application_key="geosylva-test",
        client_event_id="evenement-001",
        kind="observation",
        observed_at=datetime(2026, 8, 30, 10, 0, tzinfo=UTC),
        payload={"observation": "pH"},
        provenance={"source": "terrain"},
    )


@pytest.mark.asyncio
async def should_accept_a_field_intake_with_http_metadata() -> None:
    submitted_by = uuid4()
    result = FieldIntakeResponse(
        id=uuid4(), status="quarantined", duplicate=False, payload_hash="a" * 64
    )
    service = MagicMock()
    service.submit = AsyncMock(return_value=result)
    request = SimpleNamespace(
        headers={"X-Application-Version": "geosylva-1.2", "X-Trace-Id": "trace-001"}
    )

    with patch("gsie_api.data.field_intake_router.FieldIntakeService", return_value=service):
        response = await submit_field_intake(
            _submission(), request, Response(), {"sub": str(submitted_by)}, MagicMock()
        )

    assert response == result
    service.submit.assert_awaited_once()
    assert service.submit.await_args.kwargs == {
        "submitted_by": submitted_by,
        "application_version": "geosylva-1.2",
        "trace_id": "trace-001",
    }


@pytest.mark.asyncio
async def should_reject_field_intake_without_a_jwt_subject() -> None:
    with pytest.raises(HTTPException) as captured:
        await submit_field_intake(
            _submission(), SimpleNamespace(headers={}), Response(), {}, MagicMock()
        )

    assert captured.value.status_code == 401
    assert captured.value.detail == "Sujet JWT absent"


@pytest.mark.asyncio
async def should_map_field_intake_idempotency_conflict_to_http_409() -> None:
    service = MagicMock()
    service.submit = AsyncMock(side_effect=FieldIntakeConflict("payload différent"))

    with (
        patch("gsie_api.data.field_intake_router.FieldIntakeService", return_value=service),
        pytest.raises(HTTPException) as captured,
    ):
        await submit_field_intake(
            _submission(),
            SimpleNamespace(headers={}),
            Response(),
            {"sub": str(uuid4())},
            MagicMock(),
        )

    assert captured.value.status_code == 409
    assert captured.value.detail == {
        "code": "FIELD_INTAKE_IDEMPOTENCY_CONFLICT",
        "message": "payload différent",
    }

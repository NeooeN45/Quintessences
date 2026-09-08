"""Contrat HTTP du point d'entrée field-intake."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException, Request, Response

from gsie_api.data.field_intake import (
    FieldIntakeConflict,
    FieldIntakeResponse,
    FieldIntakeSubmission,
    _submitted_by,
)
from gsie_api.data.field_intake_router import submit_field_intake


def _request(*, application_version: str = "1.2.3", trace_id: str = "trace-test") -> Request:
    return Request(
        {
            "type": "http",
            "headers": [
                (b"x-application-version", application_version.encode("ascii")),
                (b"x-trace-id", trace_id.encode("ascii")),
            ],
        }
    )


def _submission() -> FieldIntakeSubmission:
    return FieldIntakeSubmission(
        application_key="geosylva",
        client_event_id="event-1",
        kind="observation",
        observed_at=datetime(2026, 9, 8, 10, 0, tzinfo=UTC),
        payload={"value": 42},
        provenance={"source": "test"},
    )


@pytest.mark.asyncio
async def should_submit_field_intake_with_authenticated_subject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AsyncMock()
    expected = FieldIntakeResponse(
        id=uuid4(),
        status="quarantined",
        duplicate=False,
        payload_hash="a" * 64,
    )
    service.submit.return_value = expected
    monkeypatch.setattr(
        "gsie_api.data.field_intake_router.FieldIntakeService",
        lambda _session: service,
    )

    result = await submit_field_intake(
        _submission(),
        request=_request(),
        response=Response(),
        user={"sub": "user-1", "roles": ["user"]},
        session=MagicMock(),
    )

    assert result is expected
    service.submit.assert_awaited_once()
    kwargs = service.submit.await_args.kwargs
    assert kwargs["application_version"] == "1.2.3"
    assert kwargs["trace_id"] == "trace-test"
    assert kwargs["submitted_by"] == _submitted_by("user-1")


@pytest.mark.asyncio
async def should_reject_missing_subject() -> None:
    with pytest.raises(HTTPException) as error:
        await submit_field_intake(
            _submission(),
            request=_request(),
            response=Response(),
            user={},
            session=MagicMock(),
        )

    assert error.value.status_code == 401
    assert error.value.detail == "Sujet JWT absent"


@pytest.mark.asyncio
async def should_translate_idempotency_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AsyncMock()
    service.submit.side_effect = FieldIntakeConflict("déjà reçu")
    monkeypatch.setattr(
        "gsie_api.data.field_intake_router.FieldIntakeService",
        lambda _session: service,
    )

    with pytest.raises(HTTPException) as error:
        await submit_field_intake(
            _submission(),
            request=_request(trace_id="trace-conflict"),
            response=Response(),
            user={"sub": "user-2"},
            session=MagicMock(),
        )

    assert error.value.status_code == 409
    assert error.value.detail == {
        "code": "FIELD_INTAKE_IDEMPOTENCY_CONFLICT",
        "message": "déjà reçu",
    }

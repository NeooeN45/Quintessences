"""Tests de l'idempotence transactionnelle du sas FieldIntake."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from gsie_api.data.field_intake import (
    FieldIntakeService,
    FieldIntakeSubmission,
    _payload_hash,
)


class _Savepoint:
    async def __aenter__(self) -> _Savepoint:
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        return False


def _submission() -> FieldIntakeSubmission:
    return FieldIntakeSubmission(
        application_key="forge-analysis-bundle-v1",
        client_event_id=str(uuid4()),
        kind="analysis_bundle",
        observed_at=datetime(2026, 8, 31, tzinfo=UTC),
        payload={"analysis_bundle": {"bundle_id": "bundle-1"}},
        provenance={"source": "Forge"},
    )


async def should_insert_a_field_intake_inside_a_savepoint() -> None:
    session = MagicMock()
    session.begin_nested.return_value = _Savepoint()
    session.flush = AsyncMock()
    session.add.side_effect = lambda intake: setattr(intake, "id", uuid4())
    session.execute = AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None))
    submission = _submission()

    response = await FieldIntakeService(session).submit(
        submission,
        submitted_by=uuid4(),
        application_version="test",
        trace_id="trace",
    )

    assert response.duplicate is False
    session.begin_nested.assert_called_once()
    session.flush.assert_awaited_once()


async def should_replay_the_row_winning_a_concurrent_unique_race() -> None:
    session = MagicMock()
    session.begin_nested.return_value = _Savepoint()
    session.flush = AsyncMock(side_effect=IntegrityError("insert", {}, RuntimeError("duplicate")))
    submission = _submission()
    existing = SimpleNamespace(id=uuid4(), payload_hash=_payload_hash(submission))
    session.execute = AsyncMock(
        side_effect=[
            SimpleNamespace(scalar_one_or_none=lambda: None),
            SimpleNamespace(scalar_one_or_none=lambda: existing),
        ]
    )

    response = await FieldIntakeService(session).submit(
        submission,
        submitted_by=uuid4(),
        application_version="test",
        trace_id="trace",
    )

    assert response.duplicate is True
    assert response.id == existing.id
    assert session.execute.await_count == 2


async def should_reraise_an_integrity_error_without_a_competing_row() -> None:
    session = MagicMock()
    session.begin_nested.return_value = _Savepoint()
    error = IntegrityError("insert", {}, RuntimeError("foreign key"))
    session.flush = AsyncMock(side_effect=error)
    session.execute = AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None))

    with pytest.raises(IntegrityError) as captured:
        await FieldIntakeService(session).submit(
            _submission(),
            submitted_by=uuid4(),
            application_version="test",
            trace_id="trace",
        )

    assert captured.value is error

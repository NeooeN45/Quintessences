"""Contrats unitaires du worker de finalisation RGPD."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from gsie_api import account_deletion_worker as worker


class _Result:
    def __init__(self, value: int) -> None:
        self.value = value

    def scalar_one(self) -> int:
        return self.value


class _Session:
    def __init__(self, value: int = 0) -> None:
        self.value = value
        self.statements: list[tuple[object, dict[str, int]]] = []
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> _Session:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def execute(self, statement: object, params: dict[str, int]) -> _Result:
        self.statements.append((statement, params))
        return _Result(self.value)

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


@pytest.mark.asyncio
async def should_call_the_security_definer_with_a_bounded_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session(value=3)
    monkeypatch.setattr(worker, "async_session_factory", lambda: session)

    processed = await worker.finalize_due_accounts(batch_size=7)

    assert processed == 3
    assert session.committed is True
    assert session.rolled_back is False
    statement, params = session.statements[0]
    assert "finalize_due_account_deletions" in str(statement)
    assert params == {"batch_size": 7}


@pytest.mark.asyncio
async def should_write_the_heartbeat_only_after_a_successful_cycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(worker, "finalize_due_accounts", AsyncMock(return_value=1))
    heartbeat = MagicMock()
    monkeypatch.setattr(worker, "write_worker_heartbeat", heartbeat)

    processed = await worker.run_once()

    assert processed == 1
    heartbeat.assert_called_once_with(worker._settings.account_deletion_healthcheck_path)

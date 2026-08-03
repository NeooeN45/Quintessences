"""Cycle de vie du compte local Quintessences (DEC-000046)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from gsie_api.auth.account_lifecycle import (
    AccountActionCode,
    AccountLifecycleService,
    AccountNotFoundError,
    AccountProfile,
    InvalidActionCodeError,
)
from gsie_api.auth.identity import PasswordService


class FakeAccountLifecycleRepository:
    """Dépôt mémoire focalisé sur les invariants du cycle de compte."""

    def __init__(self) -> None:
        self.account_id = uuid4()
        self.profile = AccountProfile(
            account_id=self.account_id,
            display_name="Forestier Test",
            email="forestier@example.fr",
            email_verified=False,
            providers=("local",),
            roles=("user",),
        )
        self.action: AccountActionCode | None = None
        self.password_hash: str | None = None
        self.session_version = 1

    async def get_profile(self, account_id: UUID) -> AccountProfile | None:
        return self.profile if account_id == self.account_id else None

    async def update_display_name(
        self,
        account_id: UUID,
        display_name: str | None,
    ) -> AccountProfile | None:
        if account_id != self.account_id:
            return None
        self.profile = replace(self.profile, display_name=display_name)
        return self.profile

    async def find_local_account_id(self, email: str) -> UUID | None:
        return self.account_id if email == self.profile.email else None

    async def replace_action_code(
        self,
        account_id: UUID,
        purpose: str,
        code_hash: str,
        expires_at: datetime,
    ) -> str | None:
        if account_id != self.account_id:
            return None
        self.action = AccountActionCode(
            token_id=uuid4(),
            account_id=account_id,
            purpose=purpose,
            code_hash=code_hash,
            expires_at=expires_at,
        )
        return self.profile.email

    async def get_active_action_code(
        self,
        account_id: UUID,
        purpose: str,
    ) -> AccountActionCode | None:
        action = self.action
        if action is None or action.account_id != account_id or action.purpose != purpose:
            return None
        return action

    async def consume_action_code(self, token_id: UUID) -> None:
        if self.action is not None and self.action.token_id == token_id:
            self.action = None

    async def mark_email_verified(self, account_id: UUID) -> None:
        if account_id == self.account_id:
            self.profile = replace(self.profile, email_verified=True)

    async def update_local_password(self, account_id: UUID, password_hash: str) -> None:
        if account_id == self.account_id:
            self.password_hash = password_hash
            self.session_version += 1


def _service(
    repository: FakeAccountLifecycleRepository,
    *,
    now: datetime | None = None,
) -> AccountLifecycleService:
    fixed_now = now or datetime(2026, 8, 3, 12, 0, tzinfo=UTC)
    return AccountLifecycleService(
        repository=repository,
        password_service=PasswordService(),
        code_expire_minutes=15,
        now=lambda: fixed_now,
    )


async def should_verify_email_once_when_code_is_valid() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)

    delivery = await service.request_email_verification(repository.account_id)
    assert delivery is not None
    assert delivery.email == "forestier@example.fr"
    assert len(delivery.code.replace("-", "")) == 8

    profile = await service.confirm_email_verification(
        repository.account_id,
        delivery.code,
    )

    assert profile.email_verified is True
    with pytest.raises(InvalidActionCodeError):
        await service.confirm_email_verification(repository.account_id, delivery.code)


async def should_refuse_expired_email_verification_code() -> None:
    repository = FakeAccountLifecycleRepository()
    issued_at = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)
    delivery = await _service(repository, now=issued_at).request_email_verification(
        repository.account_id
    )
    assert delivery is not None

    with pytest.raises(InvalidActionCodeError):
        await _service(
            repository,
            now=issued_at + timedelta(minutes=16),
        ).confirm_email_verification(repository.account_id, delivery.code)


async def should_not_reveal_unknown_email_during_password_reset_request() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)

    delivery = await service.request_password_reset("inconnu@example.fr")

    assert delivery is None


async def should_reset_password_and_increment_session_version_when_code_is_valid() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)
    delivery = await service.request_password_reset("FORESTIER@example.fr")
    assert delivery is not None

    await service.confirm_password_reset(
        email="forestier@example.fr",
        code=delivery.code,
        new_password="nouveau-mot-de-passe-solide",
    )

    assert repository.password_hash is not None
    assert repository.password_hash.startswith("$argon2id$")
    assert repository.session_version == 2


async def should_trim_display_name_when_profile_is_updated() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)

    profile = await service.update_profile(repository.account_id, "  Camille  ")

    assert profile.display_name == "Camille"


async def should_reject_missing_accounts_for_profile_operations() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)
    absent = uuid4()

    with pytest.raises(AccountNotFoundError):
        await service.get_profile(absent)
    with pytest.raises(AccountNotFoundError):
        await service.update_profile(absent, "Absent")


async def should_skip_verification_when_email_is_absent_or_already_verified() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)

    repository.profile = replace(repository.profile, email_verified=True)
    assert await service.request_email_verification(repository.account_id) is None

    repository.profile = replace(repository.profile, email=None, email_verified=False)
    assert await service.request_email_verification(repository.account_id) is None


async def should_reject_password_reset_for_unknown_email_without_revealing_it() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)

    with pytest.raises(InvalidActionCodeError):
        await service.confirm_password_reset(
            email="absent@example.fr",
            code="ABCD-EFGH",
            new_password="nouveau-mot-de-passe-solide",
        )


async def should_reject_incorrect_action_code() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)
    delivery = await service.request_email_verification(repository.account_id)
    assert delivery is not None

    with pytest.raises(InvalidActionCodeError):
        await service.confirm_email_verification(repository.account_id, "ZZZZ-ZZZZ")

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
    EmailAlreadyUsedError,
    EmailChangeRequest,
    InvalidActionCodeError,
    InvalidCurrentPasswordError,
    InvalidEmailChangeCodeError,
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
        self.email_change: EmailChangeRequest | None = None
        self.email_codes: dict[str, str] = {}
        self.password_hash: str | None = PasswordService().hash("ancien-mot-de-passe-solide")
        self.session_version = 1
        self.deletion_requested_at: datetime | None = None
        self.deletion_scheduled_at: datetime | None = None
        self.deletion_cancelled = False
        self.replace_action_code_returns_none = False
        self.other_account_id = uuid4()
        self.other_account_email: str | None = None

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
        if email == self.other_account_email:
            return self.other_account_id
        return self.account_id if email == self.profile.email else None

    async def get_local_password_hash(self, account_id: UUID) -> str | None:
        return self.password_hash if account_id == self.account_id else None

    async def replace_email_change_request(
        self,
        account_id: UUID,
        current_email: str,
        new_email: str,
        current_code_hash: str,
        new_code_hash: str,
        expires_at: datetime,
    ) -> EmailChangeRequest:
        self.email_codes = {
            "current": current_code_hash,
            "new": new_code_hash,
        }
        self.email_change = EmailChangeRequest(
            request_id=uuid4(),
            current_email=current_email,
            new_email=new_email,
            current_confirmed=False,
            new_confirmed=False,
            expires_at=expires_at,
        )
        return self.email_change

    async def get_active_email_change_request(self, account_id: UUID) -> EmailChangeRequest | None:
        return self.email_change if account_id == self.account_id else None

    async def confirm_email_change_code(
        self, request_id: UUID, channel: str, code: str
    ) -> EmailChangeRequest | None:
        if self.email_change is None or request_id != self.email_change.request_id:
            return None
        if not PasswordService().verify(self.email_codes[channel], code):
            return None
        self.email_change = replace(
            self.email_change,
            current_confirmed=self.email_change.current_confirmed or channel == "current",
            new_confirmed=self.email_change.new_confirmed or channel == "new",
        )
        return self.email_change

    async def complete_email_change(self, request_id: UUID) -> None:
        if self.email_change is None or request_id != self.email_change.request_id:
            raise InvalidEmailChangeCodeError
        self.profile = replace(
            self.profile,
            email=self.email_change.new_email,
            email_verified=True,
        )
        self.session_version += 1

    async def replace_action_code(
        self,
        account_id: UUID,
        purpose: str,
        code_hash: str,
        expires_at: datetime,
    ) -> str | None:
        if account_id != self.account_id or self.replace_action_code_returns_none:
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

    async def find_account_id_for_email(self, email: str) -> UUID | None:
        return self.account_id if email == self.profile.email else None

    async def mark_deletion_requested(
        self, account_id: UUID, requested_at: datetime, scheduled_at: datetime
    ) -> None:
        if account_id == self.account_id:
            self.deletion_requested_at = requested_at
            self.deletion_scheduled_at = scheduled_at

    async def cancel_deletion(self, account_id: UUID) -> None:
        if account_id == self.account_id:
            self.deletion_cancelled = True


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


async def should_change_password_when_current_password_is_valid() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)

    await service.change_password(
        repository.account_id,
        "ancien-mot-de-passe-solide",
        "nouveau-mot-de-passe-solide",
    )

    assert repository.session_version == 2
    assert PasswordService().verify(repository.password_hash or "", "nouveau-mot-de-passe-solide")


async def should_change_email_only_after_both_codes_are_confirmed() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)
    delivery = await service.request_email_change(
        repository.account_id,
        "ancien-mot-de-passe-solide",
        "nouvelle@example.fr",
    )

    profile, completed = await service.confirm_email_change(
        repository.account_id,
        "current",
        delivery.current_code,
    )
    assert completed is False
    assert profile.email == "forestier@example.fr"

    profile, completed = await service.confirm_email_change(
        repository.account_id,
        "new",
        delivery.new_code,
    )
    assert completed is True
    assert profile.email == "nouvelle@example.fr"
    assert profile.email_verified is True


async def should_reject_email_change_with_wrong_current_password() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)

    with pytest.raises(InvalidCurrentPasswordError):
        await service.request_email_change(
            repository.account_id,
            "mauvais-mot-de-passe",
            "nouvelle@example.fr",
        )


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


async def should_reject_password_change_with_wrong_current_password() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)

    with pytest.raises(InvalidCurrentPasswordError):
        await service.change_password(
            repository.account_id,
            "mauvais-mot-de-passe",
            "nouveau-mot-de-passe-solide",
        )


async def should_reject_email_change_when_profile_has_no_email() -> None:
    repository = FakeAccountLifecycleRepository()
    repository.profile = replace(repository.profile, email=None)
    service = _service(repository)

    with pytest.raises(AccountNotFoundError):
        await service.request_email_change(
            repository.account_id,
            "ancien-mot-de-passe-solide",
            "nouvelle@example.fr",
        )


async def should_reject_email_change_to_same_current_address() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)

    with pytest.raises(EmailAlreadyUsedError):
        await service.request_email_change(
            repository.account_id,
            "ancien-mot-de-passe-solide",
            "forestier@example.fr",
        )


async def should_reject_email_change_to_address_used_by_another_account() -> None:
    repository = FakeAccountLifecycleRepository()
    repository.other_account_email = "occupee@example.fr"
    service = _service(repository)

    with pytest.raises(EmailAlreadyUsedError):
        await service.request_email_change(
            repository.account_id,
            "ancien-mot-de-passe-solide",
            "occupee@example.fr",
        )


async def should_reject_confirm_email_change_when_request_is_expired() -> None:
    repository = FakeAccountLifecycleRepository()
    issued_at = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)
    delivery = await _service(repository, now=issued_at).request_email_change(
        repository.account_id,
        "ancien-mot-de-passe-solide",
        "nouvelle@example.fr",
    )
    assert delivery is not None

    with pytest.raises(InvalidEmailChangeCodeError):
        await _service(
            repository,
            now=issued_at + timedelta(minutes=16),
        ).confirm_email_change(repository.account_id, "current", delivery.current_code)


async def should_reject_confirm_email_change_with_wrong_code() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)
    delivery = await service.request_email_change(
        repository.account_id,
        "ancien-mot-de-passe-solide",
        "nouvelle@example.fr",
    )
    assert delivery is not None

    with pytest.raises(InvalidEmailChangeCodeError):
        await service.confirm_email_change(repository.account_id, "current", "ZZZZ-ZZZZ")


async def should_reject_account_deletion_with_wrong_current_password() -> None:
    repository = FakeAccountLifecycleRepository()
    repository.profile = replace(repository.profile, email_verified=True)
    service = _service(repository)

    with pytest.raises(InvalidCurrentPasswordError):
        await service.request_account_deletion(
            repository.account_id,
            "mauvais-mot-de-passe",
        )


async def should_reject_account_deletion_when_email_is_unverified() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)

    with pytest.raises(AccountNotFoundError):
        await service.request_account_deletion(
            repository.account_id,
            "ancien-mot-de-passe-solide",
        )


async def should_reject_account_deletion_when_delivery_cannot_be_created() -> None:
    repository = FakeAccountLifecycleRepository()
    repository.profile = replace(repository.profile, email_verified=True)
    repository.replace_action_code_returns_none = True
    service = _service(repository)

    with pytest.raises(AccountNotFoundError):
        await service.request_account_deletion(
            repository.account_id,
            "ancien-mot-de-passe-solide",
        )


async def should_request_account_deletion_and_schedule_grace_period() -> None:
    repository = FakeAccountLifecycleRepository()
    repository.profile = replace(repository.profile, email_verified=True)
    now = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)
    service = _service(repository, now=now)

    delivery = await service.request_account_deletion(
        repository.account_id,
        "ancien-mot-de-passe-solide",
        grace_period_days=30,
    )

    assert delivery.email == "forestier@example.fr"
    assert repository.deletion_requested_at == now
    assert repository.deletion_scheduled_at == now + timedelta(days=30)


async def should_reject_cancel_deletion_for_unknown_email() -> None:
    repository = FakeAccountLifecycleRepository()
    service = _service(repository)

    with pytest.raises(InvalidActionCodeError):
        await service.cancel_account_deletion("inconnu@example.fr", "ABCD-EFGH")


async def should_cancel_account_deletion_when_code_is_valid() -> None:
    repository = FakeAccountLifecycleRepository()
    repository.profile = replace(repository.profile, email_verified=True)
    service = _service(repository)
    delivery = await service.request_account_deletion(
        repository.account_id,
        "ancien-mot-de-passe-solide",
    )

    await service.cancel_account_deletion("forestier@example.fr", delivery.code)

    assert repository.deletion_cancelled is True

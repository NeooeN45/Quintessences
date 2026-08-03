"""Profil, vérification d'adresse et récupération de compte Quintessences."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal, Protocol

from gsie_api.auth.identity import PasswordService, normalize_email

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

ActionPurpose = Literal["verify_email", "reset_password"]
_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


class AccountLifecycleError(Exception):
    """Erreur métier racine du cycle de vie d'un compte."""


class AccountNotFoundError(AccountLifecycleError):
    """Le compte demandé n'existe pas ou n'est plus actif."""


class InvalidActionCodeError(AccountLifecycleError):
    """Le code est absent, expiré, consommé ou incorrect."""


@dataclass(frozen=True, slots=True)
class AccountProfile:
    """Vue personnelle du compte canonique, sans aucun secret."""

    account_id: UUID
    display_name: str | None
    email: str | None
    email_verified: bool
    providers: tuple[str, ...]
    roles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AccountActionCode:
    """Code Argon2 actif, chargé sous verrou par le dépôt SQL."""

    token_id: UUID
    account_id: UUID
    purpose: ActionPurpose
    code_hash: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ActionCodeDelivery:
    """Instruction éphémère transmise uniquement au service d'e-mail."""

    email: str
    code: str


class AccountLifecycleRepositoryProtocol(Protocol):
    """Persistance minimale du cycle de compte."""

    async def get_profile(self, account_id: UUID) -> AccountProfile | None: ...

    async def update_display_name(
        self,
        account_id: UUID,
        display_name: str | None,
    ) -> AccountProfile | None: ...

    async def find_local_account_id(self, email: str) -> UUID | None: ...

    async def replace_action_code(
        self,
        account_id: UUID,
        purpose: ActionPurpose,
        code_hash: str,
        expires_at: datetime,
    ) -> str | None: ...

    async def get_active_action_code(
        self,
        account_id: UUID,
        purpose: ActionPurpose,
    ) -> AccountActionCode | None: ...

    async def consume_action_code(self, token_id: UUID) -> None: ...

    async def mark_email_verified(self, account_id: UUID) -> None: ...

    async def update_local_password(self, account_id: UUID, password_hash: str) -> None: ...


class AccountLifecycleService:
    """Orchestre les actions sensibles sans exposer l'existence d'un compte."""

    def __init__(
        self,
        repository: AccountLifecycleRepositoryProtocol,
        password_service: PasswordService,
        code_expire_minutes: int,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._password_service = password_service
        self._code_expire_minutes = code_expire_minutes
        self._now = now or (lambda: datetime.now(UTC))

    async def get_profile(self, account_id: UUID) -> AccountProfile:
        profile = await self._repository.get_profile(account_id)
        if profile is None:
            raise AccountNotFoundError
        return profile

    async def update_profile(
        self,
        account_id: UUID,
        display_name: str | None,
    ) -> AccountProfile:
        normalized_name = display_name.strip() if display_name is not None else None
        normalized_name = normalized_name or None
        profile = await self._repository.update_display_name(account_id, normalized_name)
        if profile is None:
            raise AccountNotFoundError
        return profile

    async def request_email_verification(
        self,
        account_id: UUID,
    ) -> ActionCodeDelivery | None:
        profile = await self.get_profile(account_id)
        if profile.email is None or profile.email_verified:
            return None
        return await self._create_delivery(account_id, "verify_email")

    async def confirm_email_verification(
        self,
        account_id: UUID,
        code: str,
    ) -> AccountProfile:
        await self._consume_valid_code(account_id, "verify_email", code)
        await self._repository.mark_email_verified(account_id)
        return await self.get_profile(account_id)

    async def request_password_reset(self, email: str) -> ActionCodeDelivery | None:
        normalized_email = normalize_email(email)
        # Le coût Argon2 est payé même pour une adresse absente afin de limiter
        # les différences temporelles exploitables pour énumérer les comptes.
        code = self._generate_code()
        code_hash = self._password_service.hash(self._normalize_code(code))
        account_id = await self._repository.find_local_account_id(normalized_email)
        if account_id is None:
            return None
        recipient = await self._repository.replace_action_code(
            account_id,
            "reset_password",
            code_hash,
            self._expires_at(),
        )
        return ActionCodeDelivery(recipient, code) if recipient is not None else None

    async def confirm_password_reset(
        self,
        email: str,
        code: str,
        new_password: str,
    ) -> None:
        account_id = await self._repository.find_local_account_id(normalize_email(email))
        if account_id is None:
            self._password_service.verify_dummy(self._normalize_code(code))
            raise InvalidActionCodeError
        await self._consume_valid_code(account_id, "reset_password", code)
        await self._repository.update_local_password(
            account_id,
            self._password_service.hash(new_password),
        )

    async def _create_delivery(
        self,
        account_id: UUID,
        purpose: ActionPurpose,
    ) -> ActionCodeDelivery | None:
        code = self._generate_code()
        recipient = await self._repository.replace_action_code(
            account_id,
            purpose,
            self._password_service.hash(self._normalize_code(code)),
            self._expires_at(),
        )
        return ActionCodeDelivery(recipient, code) if recipient is not None else None

    async def _consume_valid_code(
        self,
        account_id: UUID,
        purpose: ActionPurpose,
        code: str,
    ) -> None:
        action = await self._repository.get_active_action_code(account_id, purpose)
        normalized_code = self._normalize_code(code)
        if action is None:
            self._password_service.verify_dummy(normalized_code)
            raise InvalidActionCodeError
        if action.expires_at <= self._now():
            await self._repository.consume_action_code(action.token_id)
            raise InvalidActionCodeError
        if not self._password_service.verify(action.code_hash, normalized_code):
            raise InvalidActionCodeError
        await self._repository.consume_action_code(action.token_id)

    def _expires_at(self) -> datetime:
        return self._now() + timedelta(minutes=self._code_expire_minutes)

    @staticmethod
    def _generate_code() -> str:
        raw = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(8))
        return f"{raw[:4]}-{raw[4:]}"

    @staticmethod
    def _normalize_code(code: str) -> str:
        return code.replace("-", "").replace(" ", "").upper()

"""Persistance SQLAlchemy du compte canonique Quintessences."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Select, or_, select, update
from sqlalchemy.exc import IntegrityError

from gsie_api.auth.account_lifecycle import AccountActionCode, AccountProfile, ActionPurpose
from gsie_api.auth.identity import (
    AccountAlreadyExistsError,
    AuthenticatedAccount,
    GoogleIdentity,
    InvalidCredentialsError,
    LocalCredentialRecord,
    ProviderAlreadyLinkedError,
)
from gsie_api.auth.mfa import MfaSecretRecord
from gsie_api.infrastructure.models.accounts import (
    AccountRoleModel,
    IdentityActionTokenModel,
    IdentityProviderLinkModel,
    LocalCredentialModel,
    MfaRecoveryCodeModel,
    MfaSecretModel,
    UserAccountModel,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyIdentityRepository:
    """Dépôt transactionnel des comptes et liens de fournisseurs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_local_account(
        self,
        email: str,
        password_hash: str,
        display_name: str | None,
    ) -> AuthenticatedAccount:
        if await self.has_account_with_verified_email(email):
            raise AccountAlreadyExistsError

        account = UserAccountModel(display_name=display_name)
        self._session.add(account)
        await self._session.flush()
        link = IdentityProviderLinkModel(
            account_id=account.id,
            provider="local",
            issuer="quintessences",
            subject=email,
            email_normalized=email,
            # Le service d'envoi de vérification est une tranche ultérieure.
            email_verified=False,
        )
        self._session.add(link)
        try:
            # Le flush matérialise l'UUID du lien avant de créer la FK du hash
            # et transforme aussi une inscription concurrente en erreur métier.
            await self._session.flush()
            self._session.add_all(
                [
                    LocalCredentialModel(
                        identity_link_id=link.id,
                        password_hash=password_hash,
                    ),
                    AccountRoleModel(
                        account_id=account.id,
                        application="quintessences",
                        role="user",
                    ),
                ]
            )
            await self._session.flush()
        except IntegrityError as exc:
            raise AccountAlreadyExistsError from exc
        return self._account(account, ("user",), "local")

    async def find_local_credentials(self, email: str) -> LocalCredentialRecord | None:
        statement = (
            select(UserAccountModel, IdentityProviderLinkModel, LocalCredentialModel)
            .join(
                IdentityProviderLinkModel,
                IdentityProviderLinkModel.account_id == UserAccountModel.id,
            )
            .join(
                LocalCredentialModel,
                LocalCredentialModel.identity_link_id == IdentityProviderLinkModel.id,
            )
            .where(
                IdentityProviderLinkModel.provider == "local",
                IdentityProviderLinkModel.issuer == "quintessences",
                IdentityProviderLinkModel.subject == email,
                IdentityProviderLinkModel.revoked_at.is_(None),
                UserAccountModel.deleted_at.is_(None),
            )
        )
        row = (await self._session.execute(statement)).first()
        if row is None:
            return None
        account, link, credential = row
        roles = await self._roles(account.id)
        return LocalCredentialRecord(
            account=self._account(account, roles, "local"),
            identity_link_id=link.id,
            password_hash=credential.password_hash,
        )

    async def update_password_hash(self, identity_link_id: UUID, password_hash: str) -> None:
        credential = await self._session.get(LocalCredentialModel, identity_link_id)
        if credential is None:
            raise InvalidCredentialsError
        credential.password_hash = password_hash
        credential.password_changed_at = datetime.now(UTC)
        await self._session.flush()

    async def mark_authenticated(self, identity_link_id: UUID) -> None:
        link = await self._session.get(IdentityProviderLinkModel, identity_link_id)
        if link is not None:
            link.last_authenticated_at = datetime.now(UTC)
            await self._session.flush()

    async def find_provider_account(
        self,
        provider: str,
        issuer: str,
        subject: str,
    ) -> AuthenticatedAccount | None:
        statement = (
            select(UserAccountModel, IdentityProviderLinkModel)
            .join(
                IdentityProviderLinkModel,
                IdentityProviderLinkModel.account_id == UserAccountModel.id,
            )
            .where(
                IdentityProviderLinkModel.provider == provider,
                IdentityProviderLinkModel.issuer == issuer,
                IdentityProviderLinkModel.subject == subject,
                IdentityProviderLinkModel.revoked_at.is_(None),
                UserAccountModel.deleted_at.is_(None),
            )
        )
        row = (await self._session.execute(statement)).first()
        if row is None:
            return None
        account, link = row
        link.last_authenticated_at = datetime.now(UTC)
        roles = await self._roles(account.id)
        await self._session.flush()
        return self._account(account, roles, provider)

    async def has_account_with_verified_email(self, email: str) -> bool:
        statement: Select[tuple[UUID]] = (
            select(IdentityProviderLinkModel.account_id)
            .join(UserAccountModel, UserAccountModel.id == IdentityProviderLinkModel.account_id)
            .where(
                IdentityProviderLinkModel.email_normalized == email,
                IdentityProviderLinkModel.revoked_at.is_(None),
                UserAccountModel.deleted_at.is_(None),
                or_(
                    IdentityProviderLinkModel.provider == "local",
                    IdentityProviderLinkModel.email_verified.is_(True),
                ),
            )
            .limit(1)
        )
        return (await self._session.execute(statement)).scalar_one_or_none() is not None

    async def create_google_account(self, identity: GoogleIdentity) -> AuthenticatedAccount:
        account = UserAccountModel(display_name=identity.display_name)
        self._session.add(account)
        await self._session.flush()
        link = IdentityProviderLinkModel(
            account_id=account.id,
            provider="google",
            issuer=identity.issuer,
            subject=identity.subject,
            email_normalized=identity.email,
            email_verified=True,
            last_authenticated_at=datetime.now(UTC),
        )
        self._session.add_all(
            [
                link,
                AccountRoleModel(
                    account_id=account.id,
                    application="quintessences",
                    role="user",
                ),
            ]
        )
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ProviderAlreadyLinkedError from exc
        return self._account(account, ("user",), "google")

    async def link_google_identity(
        self,
        account_id: UUID,
        identity: GoogleIdentity,
    ) -> AuthenticatedAccount:
        account = await self._session.get(UserAccountModel, account_id)
        if account is None or account.deleted_at is not None or account.status != "active":
            raise InvalidCredentialsError
        self._session.add(
            IdentityProviderLinkModel(
                account_id=account_id,
                provider="google",
                issuer=identity.issuer,
                subject=identity.subject,
                email_normalized=identity.email,
                email_verified=True,
                last_authenticated_at=datetime.now(UTC),
            )
        )
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ProviderAlreadyLinkedError from exc
        return self._account(account, await self._roles(account_id), "google")

    async def get_profile(self, account_id: UUID) -> AccountProfile | None:
        account = await self._session.get(UserAccountModel, account_id)
        if account is None or account.deleted_at is not None or account.status != "active":
            return None
        links_statement = (
            select(IdentityProviderLinkModel)
            .where(
                IdentityProviderLinkModel.account_id == account_id,
                IdentityProviderLinkModel.revoked_at.is_(None),
            )
            .order_by(IdentityProviderLinkModel.provider)
        )
        links = list((await self._session.execute(links_statement)).scalars().all())
        preferred_link = next((link for link in links if link.provider == "local"), None)
        if preferred_link is None:
            preferred_link = next((link for link in links if link.email_normalized), None)
        return AccountProfile(
            account_id=account.id,
            display_name=account.display_name,
            email=preferred_link.email_normalized if preferred_link is not None else None,
            email_verified=preferred_link.email_verified if preferred_link is not None else False,
            providers=tuple(dict.fromkeys(link.provider for link in links)),
            roles=await self._roles(account_id),
        )

    async def update_display_name(
        self,
        account_id: UUID,
        display_name: str | None,
    ) -> AccountProfile | None:
        account = await self._session.get(UserAccountModel, account_id)
        if account is None or account.deleted_at is not None or account.status != "active":
            return None
        account.display_name = display_name
        await self._session.flush()
        return await self.get_profile(account_id)

    async def find_local_account_id(self, email: str) -> UUID | None:
        statement = (
            select(IdentityProviderLinkModel.account_id)
            .join(UserAccountModel, UserAccountModel.id == IdentityProviderLinkModel.account_id)
            .where(
                IdentityProviderLinkModel.provider == "local",
                IdentityProviderLinkModel.issuer == "quintessences",
                IdentityProviderLinkModel.subject == email,
                IdentityProviderLinkModel.revoked_at.is_(None),
                UserAccountModel.status == "active",
                UserAccountModel.deleted_at.is_(None),
            )
            .limit(1)
        )
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def replace_action_code(
        self,
        account_id: UUID,
        purpose: ActionPurpose,
        code_hash: str,
        expires_at: datetime,
    ) -> str | None:
        email_statement = select(IdentityProviderLinkModel.email_normalized).where(
            IdentityProviderLinkModel.account_id == account_id,
            IdentityProviderLinkModel.provider == "local",
            IdentityProviderLinkModel.issuer == "quintessences",
            IdentityProviderLinkModel.revoked_at.is_(None),
        )
        email = (await self._session.execute(email_statement)).scalar_one_or_none()
        if email is None:
            return None
        now = datetime.now(UTC)
        await self._session.execute(
            update(IdentityActionTokenModel)
            .where(
                IdentityActionTokenModel.account_id == account_id,
                IdentityActionTokenModel.purpose == purpose,
                IdentityActionTokenModel.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )
        self._session.add(
            IdentityActionTokenModel(
                account_id=account_id,
                purpose=purpose,
                code_hash=code_hash,
                expires_at=expires_at,
            )
        )
        await self._session.flush()
        return email

    async def get_active_action_code(
        self,
        account_id: UUID,
        purpose: ActionPurpose,
    ) -> AccountActionCode | None:
        statement = (
            select(IdentityActionTokenModel)
            .where(
                IdentityActionTokenModel.account_id == account_id,
                IdentityActionTokenModel.purpose == purpose,
                IdentityActionTokenModel.consumed_at.is_(None),
            )
            .order_by(IdentityActionTokenModel.created_at.desc())
            .limit(1)
            .with_for_update()
        )
        token = (await self._session.execute(statement)).scalar_one_or_none()
        if token is None:
            return None
        return AccountActionCode(
            token_id=token.id,
            account_id=token.account_id,
            purpose=purpose,
            code_hash=token.code_hash,
            expires_at=token.expires_at,
        )

    async def consume_action_code(self, token_id: UUID) -> None:
        token = await self._session.get(IdentityActionTokenModel, token_id)
        if token is not None and token.consumed_at is None:
            token.consumed_at = datetime.now(UTC)
            await self._session.flush()

    async def mark_email_verified(self, account_id: UUID) -> None:
        await self._session.execute(
            update(IdentityProviderLinkModel)
            .where(
                IdentityProviderLinkModel.account_id == account_id,
                IdentityProviderLinkModel.provider == "local",
                IdentityProviderLinkModel.issuer == "quintessences",
                IdentityProviderLinkModel.revoked_at.is_(None),
            )
            .values(email_verified=True)
        )
        await self._session.flush()

    async def update_local_password(self, account_id: UUID, password_hash: str) -> None:
        statement = (
            select(LocalCredentialModel)
            .join(
                IdentityProviderLinkModel,
                IdentityProviderLinkModel.id == LocalCredentialModel.identity_link_id,
            )
            .where(
                IdentityProviderLinkModel.account_id == account_id,
                IdentityProviderLinkModel.provider == "local",
                IdentityProviderLinkModel.revoked_at.is_(None),
            )
            .with_for_update()
        )
        credential = (await self._session.execute(statement)).scalar_one_or_none()
        account = await self._session.get(UserAccountModel, account_id, with_for_update=True)
        if credential is None or account is None or account.status != "active":
            raise InvalidCredentialsError
        credential.password_hash = password_hash
        credential.password_changed_at = datetime.now(UTC)
        account.session_version += 1
        await self._session.flush()

    async def is_session_version_current(self, account_id: UUID, version: int) -> bool:
        statement = select(UserAccountModel.session_version).where(
            UserAccountModel.id == account_id,
            UserAccountModel.status == "active",
            UserAccountModel.deleted_at.is_(None),
        )
        current_version = (await self._session.execute(statement)).scalar_one_or_none()
        return current_version == version

    async def _roles(self, account_id: UUID) -> tuple[str, ...]:
        statement = (
            select(AccountRoleModel.role)
            .where(
                AccountRoleModel.account_id == account_id,
                AccountRoleModel.application == "quintessences",
            )
            .order_by(AccountRoleModel.role)
        )
        return tuple((await self._session.execute(statement)).scalars().all())

    # --- MFA TOTP (implémente MfaRepositoryProtocol) ---

    async def get_active_secret(self, account_id: UUID) -> MfaSecretRecord | None:
        stmt = select(MfaSecretModel).where(
            MfaSecretModel.account_id == account_id,
            MfaSecretModel.disabled_at.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        return MfaSecretRecord(account_id=model.account_id, secret_cipher=model.secret_cipher)

    async def save_secret(self, account_id: UUID, secret_cipher: str) -> None:
        self._session.add(MfaSecretModel(account_id=account_id, secret_cipher=secret_cipher))
        await self._session.flush()

    async def disable_secret(self, account_id: UUID) -> None:
        from datetime import UTC, datetime

        stmt = (
            update(MfaSecretModel)
            .where(
                MfaSecretModel.account_id == account_id,
                MfaSecretModel.disabled_at.is_(None),
            )
            .values(disabled_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)

    async def save_recovery_codes(self, account_id: UUID, code_hashes: list[str]) -> None:
        from sqlalchemy import delete as sa_delete

        await self._session.execute(
            sa_delete(MfaRecoveryCodeModel).where(
                MfaRecoveryCodeModel.account_id == account_id,
                MfaRecoveryCodeModel.consumed_at.is_(None),
            )
        )
        for code_hash in code_hashes:
            self._session.add(MfaRecoveryCodeModel(account_id=account_id, code_hash=code_hash))
        await self._session.flush()

    async def consume_recovery_code(self, account_id: UUID, code_hash: str) -> bool:
        from datetime import UTC, datetime

        stmt = select(MfaRecoveryCodeModel).where(
            MfaRecoveryCodeModel.account_id == account_id,
            MfaRecoveryCodeModel.consumed_at.is_(None),
        )
        models = (await self._session.execute(stmt)).scalars().all()
        for model in models:
            if self._password_service_verify(code_hash, model.code_hash):
                model.consumed_at = datetime.now(UTC)
                await self._session.flush()
                return True
        return False

    async def has_recovery_codes(self, account_id: UUID) -> bool:
        stmt = (
            select(MfaRecoveryCodeModel.id)
            .where(
                MfaRecoveryCodeModel.account_id == account_id,
                MfaRecoveryCodeModel.consumed_at.is_(None),
            )
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    @staticmethod
    def _password_service_verify(plain_hash: str, stored_hash: str) -> bool:
        """Vérifie un hash Argon2 contre un autre hash (pour recovery codes)."""
        from argon2 import PasswordHasher
        from argon2.exceptions import InvalidHashError, VerificationError

        hasher = PasswordHasher()
        try:
            return hasher.verify(stored_hash, plain_hash.replace("-", "").upper())
        except (InvalidHashError, VerificationError):
            return False

    @staticmethod
    def _account(
        account: UserAccountModel,
        roles: tuple[str, ...],
        provider: str,
    ) -> AuthenticatedAccount:
        return AuthenticatedAccount(
            account_id=account.id,
            roles=roles,
            provider=provider,
            is_active=account.status == "active" and account.deleted_at is None,
            session_version=account.session_version,
        )

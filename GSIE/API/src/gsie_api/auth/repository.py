"""Persistance SQLAlchemy du compte canonique Quintessences."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Select, or_, select
from sqlalchemy.exc import IntegrityError

from gsie_api.auth.identity import (
    AccountAlreadyExistsError,
    AuthenticatedAccount,
    GoogleIdentity,
    InvalidCredentialsError,
    LocalCredentialRecord,
    ProviderAlreadyLinkedError,
)
from gsie_api.infrastructure.models.accounts import (
    AccountRoleModel,
    IdentityProviderLinkModel,
    LocalCredentialModel,
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
        )

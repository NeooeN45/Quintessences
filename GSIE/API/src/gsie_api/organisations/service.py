"""Service organisations — domain layer (multi-tenant enterprise).

Ce module ne dépend ni de FastAPI ni de SQLAlchemy. Il porte les invariants
métier des organisations et workspaces GSIE, et reste testable avec un dépôt
mémoire.

Invariants :
- Un compte peut créer une organisation et en devient automatiquement ``owner``.
- Le slug d'organisation est unique globalement.
- Le slug de workspace est unique par organisation.
- Un compte ne peut pas être membre deux fois d'une même organisation.
- Le rôle ``owner`` ne peut pas être révoqué s'il est le dernier owner.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Protocol

from gsie_api.auth.identity import normalize_email

if TYPE_CHECKING:
    from uuid import UUID


class OrganisationError(Exception):
    """Erreur métier racine du module organisations."""


class SlugAlreadyTakenError(OrganisationError):
    """Le slug demandé est déjà utilisé."""


class OrganisationNotFoundError(OrganisationError):
    """L'organisation demandée n'existe pas ou n'est pas visible."""


class WorkspaceNotFoundError(OrganisationError):
    """Le workspace demandé n'existe pas ou n'est pas visible."""


class AlreadyMemberError(OrganisationError):
    """Le compte est déjà membre de cette organisation."""


class NotMemberError(OrganisationError):
    """Le compte n'est pas membre de cette organisation."""


class LastOwnerError(OrganisationError):
    """Impossible de révoquer le dernier owner de l'organisation."""


class InsufficientRoleError(OrganisationError):
    """Le compte n'a pas le rôle requis pour cette action."""


class InvitationInvalidError(OrganisationError):
    """L'invitation est inconnue, expirée, révoquée ou déjà consommée."""


class InvitationEmailMismatchError(OrganisationError):
    """L'invitation ne correspond pas à une adresse vérifiée du compte."""


@dataclass(frozen=True, slots=True)
class OrganisationRecord:
    """Instantané d'une organisation GSIE."""

    id: UUID
    slug: str
    display_name: str
    status: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


@dataclass(frozen=True, slots=True)
class WorkspaceRecord:
    """Instantané d'un workspace GSIE."""

    id: UUID
    organisation_id: UUID
    slug: str
    display_name: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


@dataclass(frozen=True, slots=True)
class MemberRecord:
    """Appartenance d'un compte à une organisation."""

    organisation_id: UUID
    account_id: UUID
    role: str
    invited_by: UUID
    joined_at: datetime
    revoked_at: datetime | None


@dataclass(frozen=True, slots=True)
class InvitationRecord:
    """Invitation e-mail persistée sans exposer le token brut."""

    id: UUID
    organisation_id: UUID
    email_normalized: str
    role: str
    invited_by: UUID
    token_hash: str
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None


@dataclass(frozen=True, slots=True)
class InvitationDelivery:
    """Invitation et token brut destiné uniquement au service d'e-mail."""

    invitation: InvitationRecord
    token: str


class OrganisationRepositoryProtocol(Protocol):
    """Contrat de persistance requis par le service organisations."""

    async def create_organisation(
        self,
        slug: str,
        display_name: str,
        created_by: UUID,
    ) -> OrganisationRecord: ...

    async def get_organisation_by_slug(self, slug: str) -> OrganisationRecord | None: ...

    async def get_organisation(self, organisation_id: UUID) -> OrganisationRecord | None: ...

    async def list_organisations_for_account(
        self,
        account_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[OrganisationRecord], int]: ...

    async def create_workspace(
        self,
        organisation_id: UUID,
        slug: str,
        display_name: str,
    ) -> WorkspaceRecord: ...

    async def get_workspace(
        self,
        organisation_id: UUID,
        workspace_id: UUID,
    ) -> WorkspaceRecord | None: ...

    async def list_workspaces(
        self,
        organisation_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[WorkspaceRecord], int]: ...

    async def add_member(
        self,
        organisation_id: UUID,
        account_id: UUID,
        role: str,
        invited_by: UUID,
    ) -> MemberRecord: ...

    async def get_member(
        self,
        organisation_id: UUID,
        account_id: UUID,
    ) -> MemberRecord | None: ...

    async def list_members(
        self,
        organisation_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[MemberRecord], int]: ...

    async def revoke_member(
        self,
        organisation_id: UUID,
        account_id: UUID,
    ) -> MemberRecord: ...

    async def count_owners(self, organisation_id: UUID) -> int: ...

    async def create_invitation(
        self,
        organisation_id: UUID,
        email_normalized: str,
        role: str,
        invited_by: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> InvitationRecord: ...

    async def get_pending_invitation(self, token_hash: str) -> InvitationRecord | None: ...

    async def get_verified_emails(self, account_id: UUID) -> tuple[str, ...]: ...

    async def mark_invitation_accepted(self, invitation_id: UUID) -> None: ...


class OrganisationService:
    """Orchestre les organisations, workspaces et appartenances."""

    def __init__(self, repository: OrganisationRepositoryProtocol) -> None:
        self._repository = repository

    async def create_organisation(
        self,
        slug: str,
        display_name: str,
        created_by: UUID,
    ) -> OrganisationRecord:
        existing = await self._repository.get_organisation_by_slug(slug)
        if existing is not None:
            raise SlugAlreadyTakenError(f"Le slug '{slug}' est déjà utilisé")
        organisation = await self._repository.create_organisation(slug, display_name, created_by)
        # Le créateur devient automatiquement owner.
        await self._repository.add_member(
            organisation.id,
            created_by,
            role="owner",
            invited_by=created_by,
        )
        return organisation

    async def get_organisation(self, organisation_id: UUID) -> OrganisationRecord:
        organisation = await self._repository.get_organisation(organisation_id)
        if organisation is None:
            raise OrganisationNotFoundError(str(organisation_id))
        return organisation

    async def list_organisations(
        self,
        account_id: UUID,
        *,
        page: int,
        size: int,
    ) -> tuple[list[OrganisationRecord], int]:
        return await self._repository.list_organisations_for_account(
            account_id,
            offset=(page - 1) * size,
            limit=size,
        )

    async def create_personal_space(
        self,
        account_id: UUID,
        email: str,
        display_name: str | None,
    ) -> tuple[OrganisationRecord, WorkspaceRecord]:
        """Crée l'organisation personnelle et son workspace initial."""
        slug = f"personal-{account_id.hex[:12]}"
        label = display_name or email.split("@", 1)[0]
        organisation = await self.create_organisation(slug, label, account_id)
        workspace = await self.create_workspace(
            organisation.id,
            "personal",
            "Espace personnel",
            account_id,
        )
        return organisation, workspace

    async def create_workspace(
        self,
        organisation_id: UUID,
        slug: str,
        display_name: str,
        actor: UUID,
    ) -> WorkspaceRecord:
        await self._require_role(organisation_id, actor, {"owner", "admin"})
        return await self._repository.create_workspace(organisation_id, slug, display_name)

    async def list_workspaces(
        self,
        organisation_id: UUID,
        *,
        page: int,
        size: int,
    ) -> tuple[list[WorkspaceRecord], int]:
        return await self._repository.list_workspaces(
            organisation_id,
            offset=(page - 1) * size,
            limit=size,
        )

    async def invite_member(
        self,
        organisation_id: UUID,
        account_id: UUID,
        role: str,
        invited_by: UUID,
    ) -> MemberRecord:
        await self._require_role(organisation_id, invited_by, {"owner", "admin"})
        existing = await self._repository.get_member(organisation_id, account_id)
        if existing is not None and existing.revoked_at is None:
            raise AlreadyMemberError(str(account_id))
        return await self._repository.add_member(
            organisation_id,
            account_id,
            role,
            invited_by,
        )

    async def list_members(
        self,
        organisation_id: UUID,
        *,
        page: int,
        size: int,
    ) -> tuple[list[MemberRecord], int]:
        return await self._repository.list_members(
            organisation_id,
            offset=(page - 1) * size,
            limit=size,
        )

    async def invite_by_email(
        self,
        organisation_id: UUID,
        email: str,
        role: str,
        invited_by: UUID,
        expires_in_hours: int,
    ) -> InvitationDelivery:
        """Crée une invitation signée par un token aléatoire à usage unique."""
        await self._require_role(organisation_id, invited_by, {"owner", "admin"})
        if role not in {"admin", "member"}:
            raise ValueError("Rôle d'invitation invalide")
        normalized_email = normalize_email(email)
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        invitation = await self._repository.create_invitation(
            organisation_id,
            normalized_email,
            role,
            invited_by,
            token_hash,
            datetime.now(UTC) + timedelta(hours=expires_in_hours),
        )
        return InvitationDelivery(invitation=invitation, token=token)

    async def accept_invitation(self, token: str, account_id: UUID) -> MemberRecord:
        """Accepte une invitation après vérification de l'e-mail du compte."""
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        invitation = await self._repository.get_pending_invitation(token_hash)
        if invitation is None or invitation.expires_at <= datetime.now(UTC):
            raise InvitationInvalidError
        if invitation.accepted_at is not None or invitation.revoked_at is not None:
            raise InvitationInvalidError
        verified_emails = await self._repository.get_verified_emails(account_id)
        if invitation.email_normalized not in verified_emails:
            raise InvitationEmailMismatchError
        member = await self._repository.add_member(
            invitation.organisation_id,
            account_id,
            invitation.role,
            invitation.invited_by,
        )
        await self._repository.mark_invitation_accepted(invitation.id)
        return member

    async def revoke_member(
        self,
        organisation_id: UUID,
        account_id: UUID,
        actor: UUID,
    ) -> MemberRecord:
        await self._require_role(organisation_id, actor, {"owner", "admin"})
        member = await self._repository.get_member(organisation_id, account_id)
        if member is None or member.revoked_at is not None:
            raise NotMemberError(str(account_id))
        if member.role == "owner":
            owner_count = await self._repository.count_owners(organisation_id)
            if owner_count <= 1:
                raise LastOwnerError("Impossible de révoquer le dernier owner de l'organisation")
        return await self._repository.revoke_member(organisation_id, account_id)

    async def _require_role(
        self,
        organisation_id: UUID,
        account_id: UUID,
        allowed_roles: set[str],
    ) -> None:
        member = await self._repository.get_member(organisation_id, account_id)
        if member is None or member.revoked_at is not None or member.role not in allowed_roles:
            raise InsufficientRoleError(
                f"Le compte {account_id} n'a pas le rôle requis "
                f"({', '.join(sorted(allowed_roles))}) sur l'organisation {organisation_id}"
            )

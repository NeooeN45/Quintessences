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

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime
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

"""Tests unitaires du service organisations (domain layer).

Le service est testé avec un dépôt mémoire — aucune dépendance SQLAlchemy
ni FastAPI. Valide les invariants métier :
- slug unique global pour les organisations,
- slug unique par organisation pour les workspaces,
- le créateur devient automatiquement owner,
- le dernier owner ne peut pas être révoqué,
- les rôles owner/admin sont requis pour inviter/révoquer/créer workspace.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from gsie_api.organisations.service import (
    AlreadyMemberError,
    InsufficientRoleError,
    LastOwnerError,
    MemberRecord,
    NotMemberError,
    OrganisationNotFoundError,
    OrganisationRecord,
    OrganisationService,
    SlugAlreadyTakenError,
    WorkspaceRecord,
)

# --- Fake repository ---


class FakeOrganisationRepository:
    """Dépôt mémoire pour tests unitaires du service organisations."""

    def __init__(self) -> None:
        self._organisations: dict[UUID, OrganisationRecord] = {}
        self._workspaces: dict[UUID, WorkspaceRecord] = {}
        self._members: dict[tuple[UUID, UUID], MemberRecord] = {}
        self._slugs: set[str] = set()
        self._ws_slugs: dict[UUID, set[str]] = {}

    async def create_organisation(
        self,
        slug: str,
        display_name: str,
        created_by: UUID,
    ) -> OrganisationRecord:
        if slug in self._slugs:
            raise SlugAlreadyTakenError(slug)
        org_id = uuid4()
        now = datetime.now(UTC)
        record = OrganisationRecord(
            id=org_id,
            slug=slug,
            display_name=display_name,
            status="active",
            created_by=created_by,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        self._organisations[org_id] = record
        self._slugs.add(slug)
        self._ws_slugs[org_id] = set()
        return record

    async def get_organisation_by_slug(self, slug: str) -> OrganisationRecord | None:
        for record in self._organisations.values():
            if record.slug == slug and record.deleted_at is None:
                return record
        return None

    async def get_organisation(self, organisation_id: UUID) -> OrganisationRecord | None:
        record = self._organisations.get(organisation_id)
        if record is not None and record.deleted_at is None:
            return record
        return None

    async def list_organisations_for_account(
        self,
        account_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[OrganisationRecord], int]:
        visible = [
            record
            for record in self._organisations.values()
            if record.created_by == account_id and record.deleted_at is None
        ]
        return visible[offset : offset + limit], len(visible)

    async def create_workspace(
        self,
        organisation_id: UUID,
        slug: str,
        display_name: str,
    ) -> WorkspaceRecord:
        existing_slugs = self._ws_slugs.get(organisation_id, set())
        if slug in existing_slugs:
            raise SlugAlreadyTakenError(slug)
        ws_id = uuid4()
        now = datetime.now(UTC)
        record = WorkspaceRecord(
            id=ws_id,
            organisation_id=organisation_id,
            slug=slug,
            display_name=display_name,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        self._workspaces[ws_id] = record
        existing_slugs.add(slug)
        self._ws_slugs[organisation_id] = existing_slugs
        return record

    async def get_workspace(
        self,
        organisation_id: UUID,
        workspace_id: UUID,
    ) -> WorkspaceRecord | None:
        record = self._workspaces.get(workspace_id)
        if (
            record is not None
            and record.organisation_id == organisation_id
            and record.deleted_at is None
        ):
            return record
        return None

    async def list_workspaces(
        self,
        organisation_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[WorkspaceRecord], int]:
        visible = [
            ws
            for ws in self._workspaces.values()
            if ws.organisation_id == organisation_id and ws.deleted_at is None
        ]
        return visible[offset : offset + limit], len(visible)

    async def add_member(
        self,
        organisation_id: UUID,
        account_id: UUID,
        role: str,
        invited_by: UUID,
    ) -> MemberRecord:
        key = (organisation_id, account_id)
        existing = self._members.get(key)
        if existing is not None and existing.revoked_at is None:
            raise AlreadyMemberError(str(account_id))
        now = datetime.now(UTC)
        record = MemberRecord(
            organisation_id=organisation_id,
            account_id=account_id,
            role=role,
            invited_by=invited_by,
            joined_at=now,
            revoked_at=None,
        )
        self._members[key] = record
        return record

    async def get_member(
        self,
        organisation_id: UUID,
        account_id: UUID,
    ) -> MemberRecord | None:
        return self._members.get((organisation_id, account_id))

    async def list_members(
        self,
        organisation_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[MemberRecord], int]:
        visible = [
            m
            for m in self._members.values()
            if m.organisation_id == organisation_id and m.revoked_at is None
        ]
        return visible[offset : offset + limit], len(visible)

    async def revoke_member(
        self,
        organisation_id: UUID,
        account_id: UUID,
    ) -> MemberRecord:
        key = (organisation_id, account_id)
        record = self._members.get(key)
        if record is None:
            raise NotMemberError(str(account_id))
        revoked = MemberRecord(
            organisation_id=record.organisation_id,
            account_id=record.account_id,
            role=record.role,
            invited_by=record.invited_by,
            joined_at=record.joined_at,
            revoked_at=datetime.now(UTC),
        )
        self._members[key] = revoked
        return revoked

    async def count_owners(self, organisation_id: UUID) -> int:
        return sum(
            1
            for m in self._members.values()
            if m.organisation_id == organisation_id and m.role == "owner" and m.revoked_at is None
        )


# --- Tests ---


@pytest.fixture()
def repo() -> FakeOrganisationRepository:
    return FakeOrganisationRepository()


@pytest.fixture()
def service() -> OrganisationService:
    return OrganisationService(FakeOrganisationRepository())


@pytest.mark.asyncio
async def test_create_organisation_makes_creator_owner(
    repo: FakeOrganisationRepository,
) -> None:
    service = OrganisationService(repo)
    created_by = uuid4()

    org = await service.create_organisation("onf", "Office National des Forêts", created_by)

    assert org.slug == "onf"
    assert org.display_name == "Office National des Forêts"
    member = await repo.get_member(org.id, created_by)
    assert member is not None
    assert member.role == "owner"


@pytest.mark.asyncio
async def test_create_organisation_rejects_duplicate_slug(
    repo: FakeOrganisationRepository,
) -> None:
    service = OrganisationService(repo)
    await service.create_organisation("onf", "ONF", uuid4())

    with pytest.raises(SlugAlreadyTakenError, match="onf"):
        await service.create_organisation("onf", "Autre ONF", uuid4())


@pytest.mark.asyncio
async def test_get_organisation_raises_when_not_found(
    service: OrganisationService,
) -> None:
    with pytest.raises(OrganisationNotFoundError):
        await service.get_organisation(uuid4())


@pytest.mark.asyncio
async def test_create_workspace_requires_owner_or_admin(
    repo: FakeOrganisationRepository,
) -> None:
    service = OrganisationService(repo)
    owner = uuid4()
    org = await service.create_organisation("onf", "ONF", owner)
    member = uuid4()
    await service.invite_member(org.id, member, "member", owner)

    with pytest.raises(InsufficientRoleError):
        await service.create_workspace(org.id, "ws1", "Workspace 1", member)


@pytest.mark.asyncio
async def test_create_workspace_succeeds_for_owner(
    repo: FakeOrganisationRepository,
) -> None:
    service = OrganisationService(repo)
    owner = uuid4()
    org = await service.create_organisation("onf", "ONF", owner)

    ws = await service.create_workspace(org.id, "ws1", "Workspace 1", owner)

    assert ws.organisation_id == org.id
    assert ws.slug == "ws1"


@pytest.mark.asyncio
async def test_invite_member_requires_owner_or_admin(
    repo: FakeOrganisationRepository,
) -> None:
    service = OrganisationService(repo)
    owner = uuid4()
    org = await service.create_organisation("onf", "ONF", owner)
    member1 = uuid4()
    await service.invite_member(org.id, member1, "member", owner)
    member2 = uuid4()

    with pytest.raises(InsufficientRoleError):
        await service.invite_member(org.id, member2, "member", member1)


@pytest.mark.asyncio
async def test_invite_member_rejects_already_member(
    repo: FakeOrganisationRepository,
) -> None:
    service = OrganisationService(repo)
    owner = uuid4()
    org = await service.create_organisation("onf", "ONF", owner)
    member = uuid4()
    await service.invite_member(org.id, member, "member", owner)

    with pytest.raises(AlreadyMemberError):
        await service.invite_member(org.id, member, "admin", owner)


@pytest.mark.asyncio
async def test_revoke_member_blocks_last_owner(
    repo: FakeOrganisationRepository,
) -> None:
    service = OrganisationService(repo)
    owner = uuid4()
    org = await service.create_organisation("onf", "ONF", owner)

    with pytest.raises(LastOwnerError, match="dernier owner"):
        await service.revoke_member(org.id, owner, owner)


@pytest.mark.asyncio
async def test_revoke_member_succeeds_when_other_owners_exist(
    repo: FakeOrganisationRepository,
) -> None:
    service = OrganisationService(repo)
    owner1 = uuid4()
    org = await service.create_organisation("onf", "ONF", owner1)
    owner2 = uuid4()
    await service.invite_member(org.id, owner2, "owner", owner1)

    revoked = await service.revoke_member(org.id, owner1, owner2)

    assert revoked.revoked_at is not None


@pytest.mark.asyncio
async def test_revoke_non_member_raises(
    service: OrganisationService,
    repo: FakeOrganisationRepository,
) -> None:
    owner = uuid4()
    org = await service.create_organisation("onf", "ONF", owner)
    stranger = uuid4()

    with pytest.raises(NotMemberError):
        await service.revoke_member(org.id, stranger, owner)


@pytest.mark.asyncio
async def test_list_organisations_for_account(
    repo: FakeOrganisationRepository,
) -> None:
    service = OrganisationService(repo)
    account = uuid4()
    await service.create_organisation("onf", "ONF", account)
    await service.create_organisation("cnpf", "CNPF", account)

    orgs, total = await service.list_organisations(account, page=1, size=10)

    assert total == 2
    assert len(orgs) == 2


@pytest.mark.asyncio
async def test_list_workspaces_for_organisation(
    repo: FakeOrganisationRepository,
) -> None:
    service = OrganisationService(repo)
    owner = uuid4()
    org = await service.create_organisation("onf", "ONF", owner)
    await service.create_workspace(org.id, "ws1", "WS1", owner)
    await service.create_workspace(org.id, "ws2", "WS2", owner)

    workspaces, total = await service.list_workspaces(org.id, page=1, size=10)

    assert total == 2
    assert len(workspaces) == 2


@pytest.mark.asyncio
async def test_list_members_for_organisation(
    repo: FakeOrganisationRepository,
) -> None:
    service = OrganisationService(repo)
    owner = uuid4()
    org = await service.create_organisation("onf", "ONF", owner)
    m1 = uuid4()
    m2 = uuid4()
    await service.invite_member(org.id, m1, "member", owner)
    await service.invite_member(org.id, m2, "admin", owner)

    members, total = await service.list_members(org.id, page=1, size=10)

    assert total == 3  # owner + m1 + m2
    assert len(members) == 3

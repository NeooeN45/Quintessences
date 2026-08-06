"""Dépôt SQLAlchemy des organisations, workspaces et appartenances."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.infrastructure.models.accounts import IdentityProviderLinkModel
from gsie_api.infrastructure.models.organisations import (
    OrganisationInvitationModel,
    OrganisationMemberModel,
    OrganisationModel,
    WorkspaceModel,
)
from gsie_api.organisations.service import (
    AlreadyMemberError,
    InvitationRecord,
    MemberRecord,
    NotMemberError,
    OrganisationRecord,
    SlugAlreadyTakenError,
    WorkspaceRecord,
)


class SqlAlchemyOrganisationRepository:
    """Implémentation SQLAlchemy du protocole OrganisationRepositoryProtocol."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_organisation(
        self,
        slug: str,
        display_name: str,
        created_by: UUID,
    ) -> OrganisationRecord:
        model = OrganisationModel(
            slug=slug,
            display_name=display_name,
            created_by=created_by,
        )
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise SlugAlreadyTakenError(f"Le slug '{slug}' est déjà utilisé") from exc
        await self._session.refresh(model)
        return self._org_record(model)

    async def get_organisation_by_slug(self, slug: str) -> OrganisationRecord | None:
        statement = select(OrganisationModel).where(
            OrganisationModel.slug == slug,
            OrganisationModel.deleted_at.is_(None),
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return self._org_record(model) if model is not None else None

    async def get_organisation(self, organisation_id: UUID) -> OrganisationRecord | None:
        statement = select(OrganisationModel).where(
            OrganisationModel.id == organisation_id,
            OrganisationModel.deleted_at.is_(None),
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return self._org_record(model) if model is not None else None

    async def list_organisations_for_account(
        self,
        account_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[OrganisationRecord], int]:
        # Une organisation est visible si le compte en est créateur ou membre.
        member_orgs = (
            select(OrganisationMemberModel.organisation_id)
            .where(
                OrganisationMemberModel.account_id == account_id,
                OrganisationMemberModel.revoked_at.is_(None),
            )
            .scalar_subquery()
        )
        filters = (
            OrganisationModel.deleted_at.is_(None),
            or_(
                OrganisationModel.created_by == account_id,
                OrganisationModel.id.in_(member_orgs),
            ),
        )
        count = await self._session.scalar(
            select(func.count()).select_from(OrganisationModel).where(*filters)
        )
        statement = (
            select(OrganisationModel)
            .where(*filters)
            .order_by(OrganisationModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        models = (await self._session.execute(statement)).scalars().all()
        return [self._org_record(m) for m in models], int(count or 0)

    async def create_workspace(
        self,
        organisation_id: UUID,
        slug: str,
        display_name: str,
    ) -> WorkspaceRecord:
        model = WorkspaceModel(
            organisation_id=organisation_id,
            slug=slug,
            display_name=display_name,
        )
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise SlugAlreadyTakenError(
                f"Le slug '{slug}' est déjà utilisé dans cette organisation"
            ) from exc
        await self._session.refresh(model)
        return self._ws_record(model)

    async def get_workspace(
        self,
        organisation_id: UUID,
        workspace_id: UUID,
    ) -> WorkspaceRecord | None:
        statement = select(WorkspaceModel).where(
            WorkspaceModel.id == workspace_id,
            WorkspaceModel.organisation_id == organisation_id,
            WorkspaceModel.deleted_at.is_(None),
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return self._ws_record(model) if model is not None else None

    async def list_workspaces(
        self,
        organisation_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[WorkspaceRecord], int]:
        filters = (
            WorkspaceModel.organisation_id == organisation_id,
            WorkspaceModel.deleted_at.is_(None),
        )
        count = await self._session.scalar(
            select(func.count()).select_from(WorkspaceModel).where(*filters)
        )
        statement = (
            select(WorkspaceModel)
            .where(*filters)
            .order_by(WorkspaceModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        models = (await self._session.execute(statement)).scalars().all()
        return [self._ws_record(m) for m in models], int(count or 0)

    async def add_member(
        self,
        organisation_id: UUID,
        account_id: UUID,
        role: str,
        invited_by: UUID,
    ) -> MemberRecord:
        existing = await self._session.get(
            OrganisationMemberModel,
            (organisation_id, account_id),
            with_for_update=True,
        )
        if existing is not None:
            if existing.revoked_at is None:
                raise AlreadyMemberError(str(account_id))
            existing.role = role
            existing.invited_by = invited_by
            existing.joined_at = datetime.now(UTC)
            existing.revoked_at = None
            await self._session.flush()
            await self._session.refresh(existing)
            return self._member_record(existing)

        model = OrganisationMemberModel(
            organisation_id=organisation_id,
            account_id=account_id,
            role=role,
            invited_by=invited_by,
        )
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise AlreadyMemberError(str(account_id)) from exc
        await self._session.refresh(model)
        return self._member_record(model)

    async def get_member(
        self,
        organisation_id: UUID,
        account_id: UUID,
    ) -> MemberRecord | None:
        statement = select(OrganisationMemberModel).where(
            OrganisationMemberModel.organisation_id == organisation_id,
            OrganisationMemberModel.account_id == account_id,
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return self._member_record(model) if model is not None else None

    async def list_members(
        self,
        organisation_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[MemberRecord], int]:
        filters = (
            OrganisationMemberModel.organisation_id == organisation_id,
            OrganisationMemberModel.revoked_at.is_(None),
        )
        count = await self._session.scalar(
            select(func.count()).select_from(OrganisationMemberModel).where(*filters)
        )
        statement = (
            select(OrganisationMemberModel)
            .where(*filters)
            .order_by(OrganisationMemberModel.joined_at.desc())
            .offset(offset)
            .limit(limit)
        )
        models = (await self._session.execute(statement)).scalars().all()
        return [self._member_record(m) for m in models], int(count or 0)

    async def revoke_member(
        self,
        organisation_id: UUID,
        account_id: UUID,
    ) -> MemberRecord:
        statement = select(OrganisationMemberModel).where(
            OrganisationMemberModel.organisation_id == organisation_id,
            OrganisationMemberModel.account_id == account_id,
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        if model is None:
            raise NotMemberError(str(account_id))
        model.revoked_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(model)
        return self._member_record(model)

    async def count_owners(self, organisation_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(OrganisationMemberModel)
            .where(
                OrganisationMemberModel.organisation_id == organisation_id,
                OrganisationMemberModel.role == "owner",
                OrganisationMemberModel.revoked_at.is_(None),
            )
        )
        return int((await self._session.scalar(statement)) or 0)

    async def create_invitation(
        self,
        organisation_id: UUID,
        email_normalized: str,
        role: str,
        invited_by: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> InvitationRecord:
        model = OrganisationInvitationModel(
            organisation_id=organisation_id,
            email_normalized=email_normalized,
            role=role,
            invited_by=invited_by,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._invitation_record(model)

    async def get_pending_invitation(self, token_hash: str) -> InvitationRecord | None:
        statement = (
            select(OrganisationInvitationModel)
            .where(
                OrganisationInvitationModel.token_hash == token_hash,
                OrganisationInvitationModel.accepted_at.is_(None),
                OrganisationInvitationModel.revoked_at.is_(None),
            )
            .with_for_update()
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return self._invitation_record(model) if model is not None else None

    async def mark_invitation_accepted(self, invitation_id: UUID) -> None:
        statement = (
            update(OrganisationInvitationModel)
            .where(
                OrganisationInvitationModel.id == invitation_id,
                OrganisationInvitationModel.accepted_at.is_(None),
                OrganisationInvitationModel.revoked_at.is_(None),
            )
            .values(accepted_at=datetime.now(UTC))
        )
        result = await self._session.execute(statement)
        if result.rowcount != 1:
            raise AlreadyMemberError("Invitation déjà consommée")
        await self._session.flush()

    async def get_verified_emails(self, account_id: UUID) -> tuple[str, ...]:
        statement = select(IdentityProviderLinkModel.email_normalized).where(
            IdentityProviderLinkModel.account_id == account_id,
            IdentityProviderLinkModel.revoked_at.is_(None),
            IdentityProviderLinkModel.email_normalized.is_not(None),
            IdentityProviderLinkModel.email_verified.is_(True),
        )
        return tuple(
            email
            for email in (await self._session.execute(statement)).scalars().all()
            if email is not None
        )

    @staticmethod
    def _invitation_record(model: OrganisationInvitationModel) -> InvitationRecord:
        return InvitationRecord(
            id=model.id,
            organisation_id=model.organisation_id,
            email_normalized=model.email_normalized,
            role=model.role,
            invited_by=model.invited_by,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            accepted_at=model.accepted_at,
            revoked_at=model.revoked_at,
        )

    @staticmethod
    def _org_record(model: OrganisationModel) -> OrganisationRecord:
        return OrganisationRecord(
            id=model.id,
            slug=model.slug,
            display_name=model.display_name,
            status=model.status,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _ws_record(model: WorkspaceModel) -> WorkspaceRecord:
        return WorkspaceRecord(
            id=model.id,
            organisation_id=model.organisation_id,
            slug=model.slug,
            display_name=model.display_name,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _member_record(model: OrganisationMemberModel) -> MemberRecord:
        return MemberRecord(
            organisation_id=model.organisation_id,
            account_id=model.account_id,
            role=model.role,
            invited_by=model.invited_by,
            joined_at=model.joined_at,
            revoked_at=model.revoked_at,
        )

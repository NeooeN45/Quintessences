"""API privée des organisations et workspaces GSIE (multi-tenant enterprise).

Endpoints :
- ``POST /orgs`` — créer une organisation (le créateur devient owner).
- ``GET /orgs`` — lister mes organisations.
- ``GET /orgs/{org_id}`` — détail d'une organisation.
- ``POST /orgs/{org_id}/workspaces`` — créer un workspace (owner/admin).
- ``GET /orgs/{org_id}/workspaces`` — lister les workspaces.
- ``POST /orgs/{org_id}/members`` — inviter un membre (owner/admin).
- ``GET /orgs/{org_id}/members`` — lister les membres.
- ``DELETE /orgs/{org_id}/members/{account_id}`` — révoquer un membre (owner/admin).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.auth.transactional_email import (
    TransactionalEmailSender,
    get_transactional_email_sender,
)
from gsie_api.core.auth import get_current_user
from gsie_api.core.config import get_settings
from gsie_api.core.limiter import limiter
from gsie_api.core.logging import get_logger
from gsie_api.infrastructure.database import get_db_user_rls
from gsie_api.organisations.repository import SqlAlchemyOrganisationRepository
from gsie_api.organisations.schemas import (
    EmailInvitationRequest,
    InvitationAcceptRequest,
    InvitationResponse,
    MemberInviteRequest,
    MemberPage,
    MemberResponse,
    OrganisationCreateRequest,
    OrganisationPage,
    OrganisationResponse,
    WorkspaceCreateRequest,
    WorkspacePage,
    WorkspaceResponse,
)
from gsie_api.organisations.service import (
    AlreadyMemberError,
    InsufficientRoleError,
    InvitationEmailMismatchError,
    InvitationInvalidError,
    LastOwnerError,
    NotMemberError,
    OrganisationNotFoundError,
    OrganisationService,
    SlugAlreadyTakenError,
)

router = APIRouter(prefix="/orgs", tags=["organisations"])
_settings = get_settings()
logger = get_logger("gsie_api.organisations")


async def get_organisation_service(
    session: Annotated[AsyncSession, Depends(get_db_user_rls)],
) -> OrganisationService:
    return OrganisationService(SqlAlchemyOrganisationRepository(session))


def _account_id(current_user: dict[str, object]) -> UUID:
    try:
        return UUID(str(current_user.get("sub", "")))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide"
        ) from None


def _org_response(record: object) -> OrganisationResponse:
    return OrganisationResponse(
        id=record.id,  # type: ignore[attr-defined]
        slug=record.slug,  # type: ignore[attr-defined]
        display_name=record.display_name,  # type: ignore[attr-defined]
        status=record.status,  # type: ignore[attr-defined]
        created_by=record.created_by,  # type: ignore[attr-defined]
        created_at=record.created_at,  # type: ignore[attr-defined]
        updated_at=record.updated_at,  # type: ignore[attr-defined]
    )


def _ws_response(record: object) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=record.id,  # type: ignore[attr-defined]
        organisation_id=record.organisation_id,  # type: ignore[attr-defined]
        slug=record.slug,  # type: ignore[attr-defined]
        display_name=record.display_name,  # type: ignore[attr-defined]
        created_at=record.created_at,  # type: ignore[attr-defined]
        updated_at=record.updated_at,  # type: ignore[attr-defined]
    )


def _member_response(record: object) -> MemberResponse:
    return MemberResponse(
        organisation_id=record.organisation_id,  # type: ignore[attr-defined]
        account_id=record.account_id,  # type: ignore[attr-defined]
        role=record.role,  # type: ignore[attr-defined]
        invited_by=record.invited_by,  # type: ignore[attr-defined]
        joined_at=record.joined_at,  # type: ignore[attr-defined]
        revoked_at=record.revoked_at,  # type: ignore[attr-defined]
    )


def _invitation_response(record: object) -> InvitationResponse:
    return InvitationResponse(
        id=record.id,  # type: ignore[attr-defined]
        organisation_id=record.organisation_id,  # type: ignore[attr-defined]
        email=record.email_normalized,  # type: ignore[attr-defined]
        role=record.role,  # type: ignore[attr-defined]
        expires_at=record.expires_at,  # type: ignore[attr-defined]
    )


def _map_error(exc: Exception) -> HTTPException:
    """Convertit une erreur métier en HTTPException avec le bon statut."""
    if isinstance(exc, SlugAlreadyTakenError | AlreadyMemberError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, OrganisationNotFoundError | NotMemberError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, InsufficientRoleError | LastOwnerError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("", response_model=OrganisationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_organisation(
    request: Request,
    response: Response,
    body: OrganisationCreateRequest,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[OrganisationService, Depends(get_organisation_service)],
) -> OrganisationResponse:
    del request, response
    account_id = _account_id(current_user)
    try:
        org = await service.create_organisation(body.slug, body.display_name, account_id)
    except SlugAlreadyTakenError as exc:
        raise _map_error(exc) from exc
    logger.info(
        "organisation_created", org_id=str(org.id), slug=org.slug, created_by=str(account_id)
    )
    return _org_response(org)


@router.get("", response_model=OrganisationPage)
@limiter.limit("30/minute")
async def list_organisations(
    request: Request,
    response: Response,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[OrganisationService, Depends(get_organisation_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OrganisationPage:
    del request, response
    account_id = _account_id(current_user)
    records, total = await service.list_organisations(account_id, page=page, size=size)
    return OrganisationPage(
        items=[_org_response(r) for r in records],
        page=page,
        size=size,
        total=total,
    )


@router.get("/{org_id}", response_model=OrganisationResponse)
@limiter.limit("60/minute")
async def get_organisation(
    request: Request,
    response: Response,
    org_id: UUID,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[OrganisationService, Depends(get_organisation_service)],
) -> OrganisationResponse:
    del request, response
    del current_user
    try:
        org = await service.get_organisation(org_id)
    except OrganisationNotFoundError as exc:
        raise _map_error(exc) from exc
    return _org_response(org)


@router.post(
    "/{org_id}/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
async def create_workspace(
    request: Request,
    response: Response,
    org_id: UUID,
    body: WorkspaceCreateRequest,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[OrganisationService, Depends(get_organisation_service)],
) -> WorkspaceResponse:
    del request, response
    account_id = _account_id(current_user)
    try:
        ws = await service.create_workspace(org_id, body.slug, body.display_name, account_id)
    except (InsufficientRoleError, SlugAlreadyTakenError, OrganisationNotFoundError) as exc:
        raise _map_error(exc) from exc
    logger.info("workspace_created", org_id=str(org_id), ws_id=str(ws.id), slug=ws.slug)
    return _ws_response(ws)


@router.get("/{org_id}/workspaces", response_model=WorkspacePage)
@limiter.limit("60/minute")
async def list_workspaces(
    request: Request,
    response: Response,
    org_id: UUID,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[OrganisationService, Depends(get_organisation_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> WorkspacePage:
    del request, response
    del current_user
    records, total = await service.list_workspaces(org_id, page=page, size=size)
    return WorkspacePage(
        items=[_ws_response(r) for r in records],
        page=page,
        size=size,
        total=total,
    )


@router.post(
    "/{org_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
async def invite_member(
    request: Request,
    response: Response,
    org_id: UUID,
    body: MemberInviteRequest,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[OrganisationService, Depends(get_organisation_service)],
) -> MemberResponse:
    del request, response
    account_id = _account_id(current_user)
    try:
        member = await service.invite_member(org_id, body.account_id, body.role, account_id)
    except (InsufficientRoleError, AlreadyMemberError, OrganisationNotFoundError) as exc:
        raise _map_error(exc) from exc
    logger.info(
        "member_invited",
        org_id=str(org_id),
        account_id=str(body.account_id),
        role=body.role,
        invited_by=str(account_id),
    )
    return _member_response(member)


@router.post(
    "/{org_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def create_email_invitation(
    request: Request,
    response: Response,
    org_id: UUID,
    body: EmailInvitationRequest,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[OrganisationService, Depends(get_organisation_service)],
    email_sender: Annotated[TransactionalEmailSender, Depends(get_transactional_email_sender)],
) -> InvitationResponse:
    del request, response
    if not email_sender.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service de messagerie non configuré",
        )
    actor_id = _account_id(current_user)
    try:
        organisation = await service.get_organisation(org_id)
        delivery = await service.invite_by_email(
            organisation_id=org_id,
            email=str(body.email),
            role=body.role,
            invited_by=actor_id,
            expires_in_hours=_settings.organisation_invitation_expire_hours,
        )
    except (InsufficientRoleError, OrganisationNotFoundError) as exc:
        raise _map_error(exc) from exc
    from urllib.parse import quote

    invite_url = f"{_settings.organisation_invitation_base_url}?token={quote(delivery.token)}"
    delivered = await email_sender.send_organisation_invitation(
        email=delivery.invitation.email_normalized,
        organisation_name=organisation.display_name,
        invite_url=invite_url,
        role=delivery.invitation.role,
    )
    if not delivered:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Envoi temporairement indisponible",
        )
    logger.info(
        "organisation_invitation_created",
        org_id=str(org_id),
        invited_by=str(actor_id),
        role=body.role,
    )
    return _invitation_response(delivery.invitation)


@router.post(
    "/invitations/accept",
    response_model=MemberResponse,
)
@limiter.limit("20/minute")
async def accept_email_invitation(
    request: Request,
    response: Response,
    body: InvitationAcceptRequest,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[OrganisationService, Depends(get_organisation_service)],
) -> MemberResponse:
    del request, response
    account_id = _account_id(current_user)
    try:
        member = await service.accept_invitation(body.token, account_id)
    except InvitationInvalidError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation introuvable ou expirée",
        ) from exc
    except InvitationEmailMismatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="L'adresse vérifiée du compte ne correspond pas à l'invitation",
        ) from exc
    except AlreadyMemberError as exc:
        raise _map_error(exc) from exc
    logger.info(
        "organisation_invitation_accepted",
        account_id=str(account_id),
        org_id=str(member.organisation_id),
    )
    return _member_response(member)


@router.get("/{org_id}/members", response_model=MemberPage)
@limiter.limit("60/minute")
async def list_members(
    request: Request,
    response: Response,
    org_id: UUID,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[OrganisationService, Depends(get_organisation_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> MemberPage:
    del request, response
    del current_user
    records, total = await service.list_members(org_id, page=page, size=size)
    return MemberPage(
        items=[_member_response(r) for r in records],
        page=page,
        size=size,
        total=total,
    )


@router.delete("/{org_id}/members/{account_id}", response_model=MemberResponse)
@limiter.limit("20/minute")
async def revoke_member(
    request: Request,
    response: Response,
    org_id: UUID,
    account_id: UUID,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[OrganisationService, Depends(get_organisation_service)],
) -> MemberResponse:
    del request, response
    actor_id = _account_id(current_user)
    try:
        member = await service.revoke_member(org_id, account_id, actor_id)
    except (InsufficientRoleError, LastOwnerError, NotMemberError) as exc:
        raise _map_error(exc) from exc
    logger.info(
        "member_revoked",
        org_id=str(org_id),
        account_id=str(account_id),
        revoked_by=str(actor_id),
    )
    return _member_response(member)

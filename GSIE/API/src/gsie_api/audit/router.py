"""Router Audit — journal d'audit persistant avec filtrage et pagination.

Endpoints :
- ``GET /audit-logs`` — liste paginée avec filtres (actor_id, resource_type,
  action, organisation_id, page, size).

Sécurité : auth JWT obligatoire. RLS limite la visibilité à l'acteur
lui-même ou aux admins.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.audit.repository import SqlAlchemyAuditRepository
from gsie_api.audit.schemas import AuditLogPage, AuditLogResponse
from gsie_api.audit.service import AuditService
from gsie_api.core.auth import get_current_user
from gsie_api.core.limiter import limiter as _limiter
from gsie_api.infrastructure.database import get_db_user_rls

router = APIRouter(prefix="/audit-logs", tags=["audit"])


async def get_audit_service(
    session: Annotated[AsyncSession, Depends(get_db_user_rls)],
) -> AuditService:
    return AuditService(SqlAlchemyAuditRepository(session))


def _response(entry: object) -> AuditLogResponse:
    return AuditLogResponse(
        id=entry.id,  # type: ignore[attr-defined]
        timestamp=entry.timestamp,  # type: ignore[attr-defined]
        actor_id=entry.actor_id,  # type: ignore[attr-defined]
        actor_email=entry.actor_email,  # type: ignore[attr-defined]
        action=entry.action,  # type: ignore[attr-defined]
        resource_type=entry.resource_type,  # type: ignore[attr-defined]
        resource_id=entry.resource_id,  # type: ignore[attr-defined]
        ip_address=entry.ip_address,  # type: ignore[attr-defined]
        user_agent=entry.user_agent,  # type: ignore[attr-defined]
        organisation_id=entry.organisation_id,  # type: ignore[attr-defined]
        workspace_id=entry.workspace_id,  # type: ignore[attr-defined]
        status_code=entry.status_code,  # type: ignore[attr-defined]
        method=entry.method,  # type: ignore[attr-defined]
        path=entry.path,  # type: ignore[attr-defined]
        details=entry.details,  # type: ignore[attr-defined]
        trace_id=entry.trace_id,  # type: ignore[attr-defined]
    )


@router.get(
    "",
    response_model=AuditLogPage,
    summary="Journal d'audit paginé avec filtrage",
    description=(
        "Retourne les entrées d'audit avec filtres optionnels : "
        "actor_id, resource_type, action, organisation_id. "
        "RLS limite la visibilité à l'acteur lui-même ou aux admins."
    ),
)
@_limiter.limit("30/minute")
async def list_audit_logs(
    request: Request,
    response: Response,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    service: Annotated[AuditService, Depends(get_audit_service)],
    actor_id: Annotated[UUID | None, Query(description="Filtrer par acteur")] = None,
    resource_type: Annotated[str | None, Query(description="Filtrer par type de ressource")] = None,
    action: Annotated[str | None, Query(description="Filtrer par action")] = None,
    organisation_id: Annotated[UUID | None, Query(description="Filtrer par organisation")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> AuditLogPage:
    del request, response, current_user
    entries, total = await service.list(
        actor_id=actor_id,
        resource_type=resource_type,
        action=action,
        organisation_id=organisation_id,
        page=page,
        size=size,
    )
    return AuditLogPage(
        items=[_response(e) for e in entries],
        page=page,
        size=size,
        total=total,
    )

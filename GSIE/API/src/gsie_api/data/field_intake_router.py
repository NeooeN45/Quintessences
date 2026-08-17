"""Route authentifiée d'entrée des observations et retours applicatifs."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.auth import get_current_user
from gsie_api.core.config import get_settings
from gsie_api.core.limiter import limiter
from gsie_api.data.field_intake import (
    FieldIntakeConflict,
    FieldIntakeResponse,
    FieldIntakeService,
    FieldIntakeSubmission,
    _submitted_by,
)
from gsie_api.infrastructure.database import get_db_resource

router = APIRouter(prefix="/field-intake", tags=["field-intake"])
_settings = get_settings()
CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db_resource)]


@router.post(
    "",
    response_model=FieldIntakeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Réceptionner une observation ou un feedback en quarantaine",
)
@limiter.limit(_settings.rate_limit_default)
async def submit_field_intake(
    payload: FieldIntakeSubmission,
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DbSession,
) -> FieldIntakeResponse:
    """Accepte une soumission sans écriture directe dans la connaissance canonique."""

    subject = user.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sujet JWT absent")
    application_version = request.headers.get("X-Application-Version", "unknown")
    trace_id = request.headers.get("X-Trace-Id", "")
    try:
        return await FieldIntakeService(session).submit(
            payload,
            submitted_by=_submitted_by(subject),
            application_version=application_version,
            trace_id=trace_id,
        )
    except FieldIntakeConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "FIELD_INTAKE_IDEMPOTENCY_CONFLICT", "message": str(exc)},
        ) from exc


__all__ = ["router"]

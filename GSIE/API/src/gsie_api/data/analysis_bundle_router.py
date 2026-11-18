"""Route authentifiée d'import du bundle Forge dans GSIE TEST."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.auth import get_current_user
from gsie_api.core.config import get_settings
from gsie_api.core.limiter import limiter
from gsie_api.core.rbac import check_permission, get_user_roles
from gsie_api.data.analysis_bundle import ForgeAnalysisBundle  # noqa: TC001
from gsie_api.data.analysis_bundle_import import (
    AnalysisBundleImportError,
    AnalysisBundleImportResponse,
    ForgeAnalysisBundleImporter,
)
from gsie_api.data.field_intake import _submitted_by
from gsie_api.infrastructure.database import get_db_resource

router = APIRouter(prefix="/data", tags=["forge-analysis-bundle"])
_settings = get_settings()
CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db_resource)]


@router.post(
    "/analysis-bundles/import",
    response_model=AnalysisBundleImportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Importer un bundle Forge validé dans le sas GSIE TEST",
)
@limiter.limit(_settings.rate_limit_default)
async def import_analysis_bundle(
    payload: ForgeAnalysisBundle,
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DbSession,
) -> AnalysisBundleImportResponse:
    """Persiste le bundle en quarantaine après autorisation RBAC explicite."""

    check_permission(user, "dataset", "write")
    subject = user.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sujet JWT absent")

    try:
        return await ForgeAnalysisBundleImporter(
            session,
            database_role=_settings.database_role,
            allowed_profiles=_settings.forge_analysis_bundle_allowed_profiles,
        ).import_bundle(
            payload,
            submitted_by=_submitted_by(subject),
            authorized_roles=get_user_roles(user),
            application_version=request.headers.get("X-Application-Version", "unknown"),
            trace_id=request.headers.get("X-Trace-Id", ""),
        )
    except AnalysisBundleImportError as exc:
        if exc.code in {
            "FORGE_ANALYSIS_BUNDLE_TEST_ONLY",
            "FORGE_ANALYSIS_BUNDLE_UNAUTHORIZED",
        }:
            error_status = status.HTTP_403_FORBIDDEN
        elif exc.code == "FORGE_ANALYSIS_BUNDLE_IDEMPOTENCY_CONFLICT":
            error_status = status.HTTP_409_CONFLICT
        else:
            error_status = status.HTTP_422_UNPROCESSABLE_CONTENT
        raise HTTPException(
            status_code=error_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc


__all__ = ["import_analysis_bundle", "router"]

"""Router CRUD générique — 8 endpoints pour les 73 types (ADR-007).

GET    /resources                 — liste paginée filtrée par type
POST   /resources                 — créer une resource
GET    /resources/types           — liste des types disponibles
GET    /resources/{id}            — détail
PUT    /resources/{id}            — mise à jour (crée une Revision)
DELETE /resources/{id}            — soft delete (crée une Revision finale)
GET    /resources/{id}/revisions  — historique des révisions (Temporal Engine)
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from gsie_api.core.auth import get_current_user
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.resources.schemas import (
    ResourceCreate,
    ResourceListResponse,
    ResourceRead,
    ResourceTypesResponse,
    ResourceUpdate,
    RevisionRead,
)
from gsie_api.resources.service import ResourceService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/resources", tags=["resources"])

_limiter = Limiter(key_func=get_remote_address)


def _extract_author_id(user: dict[str, Any]) -> UUID | None:
    """Extrait l'UUID de l'utilisateur depuis le payload JWT."""
    sub = user.get("sub")
    if sub:
        try:
            return UUID(sub)
        except (ValueError, TypeError):
            return None
    return None


@router.get(
    "/types",
    response_model=ResourceTypesResponse,
    summary="Liste des types de resources disponibles",
)
async def list_types(
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> ResourceTypesResponse:
    """Retourne la liste des 69 types de resources du métamodèle v6.2."""
    types = ResourceService.list_types()
    return ResourceTypesResponse(types=types, count=len(types))


@router.get(
    "",
    response_model=ResourceListResponse,
    summary="Liste paginée de resources",
)
@_limiter.limit("60/minute")
async def list_resources(
    request: Request,
    type: str | None = Query(None, description="Filtrer par type (ex. assertion, observation)"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Taille de page (max 100)"),
    _user: Annotated[dict[str, Any], Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> ResourceListResponse:
    """Liste paginée de resources, optionnellement filtrée par type."""
    service = ResourceService(session)
    return await service.list_resources(type_filter=type, page=page, size=size)


@router.post(
    "",
    response_model=ResourceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une resource",
)
@_limiter.limit("30/minute")
async def create_resource(
    body: ResourceCreate,
    request: Request,
    user: Annotated[dict[str, Any], Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResourceRead:
    """Crée une resource du type spécifié avec ses champs spécifiques."""
    service = ResourceService(session)
    try:
        return await service.create(body, author_id=_extract_author_id(user))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/{resource_id}",
    response_model=ResourceRead,
    summary="Détail d'une resource",
)
@_limiter.limit("120/minute")
async def get_resource(
    resource_id: UUID,
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> ResourceRead:
    """Récupère une resource par son ID."""
    service = ResourceService(session)
    result = await service.get(resource_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Resource non trouvée")
    return result


@router.put(
    "/{resource_id}",
    response_model=ResourceRead,
    summary="Mettre à jour une resource",
)
@_limiter.limit("30/minute")
async def update_resource(
    resource_id: UUID,
    body: ResourceUpdate,
    request: Request,
    user: Annotated[dict[str, Any], Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResourceRead:
    """Met à jour une resource — crée une Revision + ResourceDiff (CON-010)."""
    service = ResourceService(session)
    try:
        result = await service.update(
            resource_id, body, author_id=_extract_author_id(user)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Resource non trouvée")
    return result


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une resource (soft delete)",
)
@_limiter.limit("10/minute")
async def delete_resource(
    resource_id: UUID,
    request: Request,
    justification: str = Query("Suppression", description="Justification (CON-010)"),
    user: Annotated[dict[str, Any], Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> None:
    """Soft delete — marque deleted_at + crée une Revision finale (CON-010)."""
    service = ResourceService(session)
    deleted = await service.delete(
        resource_id,
        justification=justification,
        author_id=_extract_author_id(user) if user else None,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Resource non trouvée")


@router.get(
    "/{resource_id}/revisions",
    response_model=list[RevisionRead],
    summary="Historique des révisions d'une resource",
)
@_limiter.limit("60/minute")
async def list_revisions(
    resource_id: UUID,
    request: Request,
    _user: Annotated[dict[str, Any], Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> list[RevisionRead]:
    """Retourne l'historique des révisions d'une resource (Temporal Engine)."""
    service = ResourceService(session)
    return await service.list_revisions(resource_id)

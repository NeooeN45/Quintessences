"""Router CRUD générique — 8 endpoints pour les 73 types (ADR-007).

GET    /resources                 — liste paginée filtrée par type
POST   /resources                 — créer une resource
GET    /resources/types           — liste des types disponibles
GET    /resources/{id}            — détail
PUT    /resources/{id}            — mise à jour (crée une Revision)
DELETE /resources/{id}            — soft delete (crée une Revision finale)
GET    /resources/{id}/revisions  — historique des révisions (Temporal Engine)

Sécurité : auth JWT obligatoire sur tous les endpoints (OWASP A01).
"""

from typing import Annotated, Any
from uuid import UUID, uuid5

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.auth import get_current_user
from gsie_api.core.rbac import check_permission
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

router = APIRouter(prefix="/resources", tags=["resources"])

# Réutiliser le limiter global (storage_uri Redis configuré)
# — ne pas instancier un Limiter local (serait memory://, non distribué)
from gsie_api.core.limiter import limiter as _limiter  # noqa: E402

# Type aliases pour lisibilité
CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]

# Namespace UUID fixe pour générer des author_id déterministes depuis les usernames
# (login dev émet "admin" pas un UUID — uuid5 garantit la traçabilité CON-010)
_GSIE_AUTHOR_NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _extract_author_id(user: dict[str, Any]) -> UUID | None:
    """Extrait l'UUID de l'utilisateur depuis le payload JWT.

    Le subject JWT peut être un UUID (DB users) ou un username (dev login).
    Si ce n'est pas un UUID valide, on génère un UUID déterministe via uuid5
    (namespace GSIE + username) pour garantir la traçabilité (CON-010).
    """
    subject_claim = user.get("sub")
    if not subject_claim:
        return None
    try:
        return UUID(subject_claim)
    except (ValueError, TypeError):
        # subject est un username (ex: "admin") — UUID déterministe
        return uuid5(_GSIE_AUTHOR_NAMESPACE, subject_claim)


@router.get(
    "/types",
    response_model=ResourceTypesResponse,
    summary="Liste des types de resources disponibles",
)
async def list_types(
    request: Request,
    _user: CurrentUser,
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
    _user: CurrentUser,
    session: DbSession,
    type: str | None = Query(None, description="Filtrer par type (ex. assertion, observation)"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Taille de page (max 100)"),
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
    user: CurrentUser,
    session: DbSession,
) -> ResourceRead:
    """Crée une resource du type spécifié avec ses champs spécifiques."""
    check_permission(user, body.type, "write")
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
    _user: CurrentUser,
    session: DbSession,
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
    user: CurrentUser,
    session: DbSession,
) -> ResourceRead:
    """Met à jour une resource — crée une Revision + ResourceDiff (CON-010)."""
    # Vérifier le type de la resource existante pour le RBAC
    service = ResourceService(session)
    existing = await service.get(resource_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Resource non trouvée")
    check_permission(user, existing.type, "write")
    try:
        result = await service.update(resource_id, body, author_id=_extract_author_id(user))
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
    user: CurrentUser,
    session: DbSession,
    justification: str = Query("Suppression", description="Justification (CON-010)"),
) -> None:
    """Soft delete — marque deleted_at + crée une Revision finale (CON-010)."""
    service = ResourceService(session)
    existing = await service.get(resource_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Resource non trouvée")
    check_permission(user, existing.type, "delete")
    deleted = await service.delete(
        resource_id,
        justification=justification,
        author_id=_extract_author_id(user),
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
    _user: CurrentUser,
    session: DbSession,
) -> list[RevisionRead]:
    """Retourne l'historique des révisions d'une resource (Temporal Engine)."""
    service = ResourceService(session)
    return await service.list_revisions(resource_id)

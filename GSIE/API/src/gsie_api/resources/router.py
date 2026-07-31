"""Router CRUD générique pour les types enregistrés (ADR-007).

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

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.auth import get_current_user
from gsie_api.core.rbac import (
    RGPD_RESOURCE_TYPES,
    can_access_resource,
    check_permission,
)
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.resources.schemas import (
    BulkIngestRequest,
    ResourceCreate,
    ResourceListResponse,
    ResourceRead,
    ResourceTypesResponse,
    ResourceUpdate,
    RevisionRead,
)
from gsie_api.resources.service import ResourceService
from gsie_api.resources.validators import ResourceValidationError
from gsie_api.shared.schemas import BulkIngestResult

router = APIRouter(prefix="/resources", tags=["resources"])

# Code stable de la réponse 422 — contrat pour les clients (Hub UE5, GeoSylva).
VALIDATION_ERROR_CODE = "resource_validation_failed"


def _erreur_validation(exc: ResourceValidationError) -> HTTPException:
    """Traduit une erreur métier en 422 au corps stable.

    422 et non 400 : le corps est syntaxiquement correct, ce sont les
    invariants du métamodèle qui refusent l'état demandé.
    """
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "code": VALIDATION_ERROR_CODE,
            "resource_type": exc.type_name,
            "errors": exc.errors,
        },
    )


# Réutiliser le limiter global (storage_uri Redis configuré)
# — ne pas instancier un Limiter local (serait memory://, non distribué)
from gsie_api.core.config import get_settings as _get_settings  # noqa: E402
from gsie_api.core.limiter import limiter as _limiter  # noqa: E402

_settings = _get_settings()

# Type aliases pour lisibilité
CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]

# Note : tout endpoint décoré par `@_limiter.limit` doit déclarer
# `response: Response`. Le limiter est configuré avec `headers_enabled=True`
# et y injecte les en-têtes de quota ; sans ce paramètre, slowapi lève sur le
# chemin nominal — la réponse en succès, pas l'erreur (cf. auth/router.py).

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


def _excluded_read_types(user: dict[str, Any]) -> frozenset[str]:
    """Calcule les types à retirer avant toute requête paginée."""
    check_permission(user, "resource", "read")
    return frozenset(
        resource_type
        for resource_type in RGPD_RESOURCE_TYPES
        if not can_access_resource(user, resource_type, "read")
    )


@router.get(
    "/types",
    response_model=ResourceTypesResponse,
    summary="Liste des types de resources disponibles",
)
async def list_types(
    request: Request,
    user: CurrentUser,
) -> ResourceTypesResponse:
    """Retourne la liste autorisée des types de ressources enregistrés."""
    excluded = _excluded_read_types(user)
    types = [item for item in ResourceService.list_types() if item not in excluded]
    return ResourceTypesResponse(types=types, count=len(types))


@router.get(
    "",
    response_model=ResourceListResponse,
    summary="Liste paginée de resources",
)
@_limiter.limit("60/minute")
async def list_resources(
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DbSession,
    type: str | None = Query(None, description="Filtrer par type (ex. assertion, observation)"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Taille de page (max 100)"),
) -> ResourceListResponse:
    """Liste paginée de resources, optionnellement filtrée par type."""
    # Un `?type=` vide n'est pas un filtre : le service l'ignore (chaîne
    # falsy), et le traiter comme un filtre désactivait l'exclusion RGPD,
    # exposant consent / data_subject / access_policy / sensitivity_classification
    # à tout porteur du rôle `reader`. Absent et vide doivent suivre le même chemin.
    type_filter = type.strip() if type else None
    if type_filter:
        check_permission(user, type_filter, "read")
        excluded_types: frozenset[str] = frozenset()
    else:
        excluded_types = _excluded_read_types(user)

    service = ResourceService(session)
    return await service.list_resources(
        type_filter=type_filter,
        page=page,
        size=size,
        excluded_types=excluded_types,
    )


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
    response: Response,
    user: CurrentUser,
    session: DbSession,
) -> ResourceRead:
    """Crée une resource du type spécifié avec ses champs spécifiques."""
    check_permission(user, body.type, "write")
    service = ResourceService(session)
    try:
        return await service.create(body, author_id=_extract_author_id(user))
    except ResourceValidationError as exc:
        raise _erreur_validation(exc) from exc
    except ValueError as exc:
        # Type inconnu du registre — la requête ne désigne aucune ressource.
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/bulk",
    response_model=BulkIngestResult,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un lot de resources (ingestion massive)",
    description=(
        "Crée jusqu'à 1000 resources en une seule transaction. "
        "Chaque item est validé indépendamment — un item invalide n'interrompt "
        "pas le lot. Le rapport détaillé permet de corriger et rejouer les "
        "items en échec. Rate limit différencié : 600 req/min (vs 30 pour "
        "le unitaire) — conçu pour l'ingestion de datasets externes "
        "(Treekipedia, BD Forêt IGN, etc.)."
    ),
)
@_limiter.limit(_settings.rate_limit_bulk)
async def create_resources_bulk(
    body: BulkIngestRequest,
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DbSession,
) -> BulkIngestResult:
    """Crée un lot de resources en une transaction.

    RBAC : chaque item est vérifié individuellement. Un item dont le
    type n'est pas autorisé pour l'utilisateur est marqué en erreur
    dans le rapport, sans interrompre le lot.
    """
    # Vérifier les permissions pour chaque type présent dans le lot.
    # On ne lève pas immédiatement : on marque les items non autorisés
    # dans le rapport. Mais on lève si l'utilisateur n'a aucune permission
    # write (protection contre le scan de types).
    types_present = {item.type for item in body.items}
    for type_name in types_present:
        check_permission(user, type_name, "write")

    from gsie_api.ingestion.bulk import BulkIngestService

    service = BulkIngestService(session)
    try:
        return await service.ingest(body, author_id=_extract_author_id(user))
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
    response: Response,
    user: CurrentUser,
    session: DbSession,
) -> ResourceRead:
    """Récupère une resource par son ID."""
    service = ResourceService(session)
    resource_type = await service.get_type(resource_id)
    if resource_type is None:
        raise HTTPException(status_code=404, detail="Resource non trouvée")
    check_permission(user, resource_type, "read")
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
    response: Response,
    user: CurrentUser,
    session: DbSession,
) -> ResourceRead:
    """Met à jour une resource — crée une Revision + ResourceDiff (CON-010)."""
    # Vérifier le type de la resource existante pour le RBAC
    service = ResourceService(session)
    resource_type = await service.get_type(resource_id)
    if resource_type is None:
        raise HTTPException(status_code=404, detail="Resource non trouvée")
    check_permission(user, resource_type, "write")
    try:
        result = await service.update(resource_id, body, author_id=_extract_author_id(user))
    except ResourceValidationError as exc:
        raise _erreur_validation(exc) from exc
    except ValueError as exc:
        # Type inconnu du registre — la requête ne désigne aucune ressource.
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
    response: Response,
    user: CurrentUser,
    session: DbSession,
    justification: str = Query("Suppression", description="Justification (CON-010)"),
) -> None:
    """Soft delete — marque deleted_at + crée une Revision finale (CON-010)."""
    service = ResourceService(session)
    resource_type = await service.get_type(resource_id)
    if resource_type is None:
        raise HTTPException(status_code=404, detail="Resource non trouvée")
    check_permission(user, resource_type, "delete")
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
    response: Response,
    user: CurrentUser,
    session: DbSession,
) -> list[RevisionRead]:
    """Retourne l'historique des révisions d'une resource (Temporal Engine)."""
    service = ResourceService(session)
    resource_type = await service.get_type(resource_id)
    if resource_type is None:
        raise HTTPException(status_code=404, detail="Resource non trouvée")
    check_permission(user, resource_type, "read")
    return await service.list_revisions(resource_id)

"""Service CRUD générique — opérations sur toutes les resources via le registry.

Le service utilise RESOURCE_TYPES pour router vers le bon modèle SQLAlchemy
selon le type demandé. Les champs spécifiques sont stockés dans la table
du type (class-table inheritance ADR-001).

CON-010 : jamais UPDATE ni DELETE physique.
- create  → insère resource + ligne type + Revision v1
- update  → insère nouvelle Revision + ResourceDiff + modifie les colonnes
- delete  → soft delete (deleted_at + Revision finale)
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.infrastructure.models import RESOURCE_TYPES, ResourceModel
from gsie_api.infrastructure.models.temporal_engine import (
    ResourceDiffModel,
    RevisionModel,
)
from gsie_api.resources.schemas import (
    ResourceCreate,
    ResourceListResponse,
    ResourceRead,
    ResourceUpdate,
    RevisionRead,
)
from gsie_api.resources.validators import validate_resource_data
from gsie_api.websocket.events import EventType, WSEvent
from gsie_api.websocket.manager import manager as ws_manager

logger = get_logger("gsie_api.resources.service")

# Constantes
_GSIE_ID_SUFFIX_LENGTH = 8
_MAX_STRING_LENGTH = 10000


class ResourceService:
    """Service CRUD générique pour les 73 types du métamodèle v6.2."""

    # Champs système non modifiables par l'utilisateur (mass assignment protection)
    _FORBIDDEN_FIELDS: frozenset[str] = frozenset({
        "id", "created_at", "updated_at", "deleted_at",
        "revision_id", "version", "author_id",
        "transaction_time", "valid_time_start", "valid_time_end",
    })

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- Helpers privés ---

    def _get_model_cls(self, type_name: str) -> type:
        """Récupère la classe modèle SQLAlchemy pour un type donné."""
        if type_name not in RESOURCE_TYPES:
            raise ValueError(
                f"Type inconnu : {type_name}. "
                f"Types disponibles : {sorted(RESOURCE_TYPES.keys())}"
            )
        return RESOURCE_TYPES[type_name]

    def _filter_data(self, model_cls: type, data: dict[str, Any]) -> dict[str, Any]:
        """Filtre les champs interdits (mass assignment protection, OWASP A01)."""
        allowed_columns = {
            col.name for col in model_cls.__table__.columns if col.name != "id"
        }
        return {
            k: v for k, v in data.items()
            if k in allowed_columns and k not in self._FORBIDDEN_FIELDS
        }

    @staticmethod
    def _generate_gsie_id(type_name: str) -> str:
        """Génère un identifiant lisible (ex. assertion:2026:a1b2c3d4)."""
        year = datetime.now(UTC).year
        short_uuid = uuid4().hex[:_GSIE_ID_SUFFIX_LENGTH]
        return f"{type_name}:{year}:{short_uuid}"

    async def _get_next_version(self, resource_id: UUID) -> int:
        """Récupère le numéro de version suivant pour une resource."""
        current = (
            await self._session.execute(
                select(func.max(RevisionModel.version)).where(
                    RevisionModel.target_id == resource_id
                )
            )
        ).scalar_one()
        return (current or 0) + 1

    async def _create_revision(
        self,
        resource_id: UUID,
        version: int,
        justification: str,
        author_id: UUID | None = None,
        diff_data: dict[str, Any] | None = None,
    ) -> RevisionModel:
        """Crée une Revision (append-only, CON-010)."""
        now = datetime.now(UTC)
        revision = RevisionModel(
            target_id=resource_id,
            version=version,
            author_id=author_id,
            justification=justification,
            valid_time_start=now,
            transaction_time=now,
        )
        self._session.add(revision)
        await self._session.flush()
        if diff_data:
            self._add_resource_diff(revision, diff_data)
        return revision

    def _add_resource_diff(
        self, revision: RevisionModel, diff_data: dict[str, Any]
    ) -> None:
        """Ajoute un ResourceDiff à une Revision."""
        resource_diff = ResourceDiffModel(
            id=uuid4(),
            to_revision_id=revision.id,
            field_changes=diff_data.get("field_changes", []),
            added_relations=diff_data.get("added_relations", []),
            removed_relations=diff_data.get("removed_relations", []),
        )
        self._session.add(resource_diff)
        revision.diff_id = resource_diff.id

    async def _broadcast_event(
        self,
        event_type: EventType,
        resource_id: UUID,
        resource_type: str,
        data: dict[str, Any],
    ) -> None:
        """Diffuse un event WebSocket (best-effort, non bloquant)."""
        event = WSEvent(
            event_type=event_type,
            resource_id=resource_id,
            resource_type=resource_type,
            data=data,
            timestamp=datetime.now(UTC).isoformat(),
        )
        try:
            await ws_manager.broadcast_event(
                resource_type, event.model_dump(mode="json")
            )
        except Exception:
            logger.warning("ws_broadcast_failed", event_type=event_type, exc_info=True)

    async def _build_resource_read(self, resource: ResourceModel) -> ResourceRead:
        """Construit un ResourceRead depuis un ResourceModel + sa ligne type."""
        model_cls = self._get_model_cls(resource.type)
        type_result = await self._session.get(model_cls, resource.id)
        type_data: dict[str, Any] = {}
        if type_result is not None:
            type_data = {
                col.name: getattr(type_result, col.name)
                for col in type_result.__table__.columns
                if col.name != "id"
            }
        return ResourceRead(
            id=resource.id,
            type=resource.type,
            gsie_id=resource.gsie_id,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
            metadata_json=resource.metadata_json,
            data=type_data,
        )

    @staticmethod
    def _to_resource_read(resource: ResourceModel, data: dict[str, Any]) -> ResourceRead:
        """Construit un ResourceRead léger (sans fetch de la ligne type)."""
        return ResourceRead(
            id=resource.id,
            type=resource.type,
            gsie_id=resource.gsie_id,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
            metadata_json=resource.metadata_json,
            data=data,
        )

    def _compute_field_changes(
        self, type_instance: Any, safe_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Calcule le diff entre les valeurs actuelles et les nouvelles valeurs."""
        changes: list[dict[str, Any]] = []
        for key, new_value in safe_data.items():
            if not hasattr(type_instance, key):
                continue
            old_value = getattr(type_instance, key)
            if old_value != new_value:
                changes.append({
                    "field": key,
                    "old_value": str(old_value) if old_value is not None else None,
                    "new_value": str(new_value) if new_value is not None else None,
                })
                setattr(type_instance, key, new_value)
        return changes

    # --- Opérations CRUD publiques ---

    async def create(
        self, request: ResourceCreate, author_id: UUID | None = None
    ) -> ResourceRead:
        """Crée une resource + sa ligne dans la table du type + Revision v1."""
        model_cls = self._get_model_cls(request.type)
        errors = validate_resource_data(request.type, request.data)
        if errors:
            raise ValueError(f"Validation échouée : {'; '.join(errors)}")

        safe_data = self._filter_data(model_cls, request.data)
        gsie_id = request.gsie_id or self._generate_gsie_id(request.type)
        resource = await self._insert_resource(request.type, gsie_id, model_cls, safe_data)

        await self._create_revision(
            resource_id=resource.id, version=1,
            justification="Création initiale", author_id=author_id,
        )
        await self._session.commit()

        logger.info("resource_created", resource_id=str(resource.id),
                     type=request.type, gsie_id=gsie_id)
        await self._broadcast_event(
            EventType.resource_created, resource.id, request.type,
            {"gsie_id": gsie_id, **safe_data},
        )
        return await self._build_resource_read(resource)

    async def _insert_resource(
        self, type_name: str, gsie_id: str, model_cls: type, safe_data: dict[str, Any]
    ) -> ResourceModel:
        """Insère la ligne racine resource + la ligne dans la table du type."""
        resource = ResourceModel(type=type_name, gsie_id=gsie_id)
        self._session.add(resource)
        await self._session.flush()
        type_instance = model_cls(id=resource.id, **safe_data)
        self._session.add(type_instance)
        return resource

    async def get(self, resource_id: UUID) -> ResourceRead | None:
        """Récupère une resource par son ID (exclut les soft-deleted)."""
        result = await self._session.get(ResourceModel, resource_id)
        if result is None or result.deleted_at is not None:
            return None
        return await self._build_resource_read(result)

    async def list_resources(
        self, type_filter: str | None = None, page: int = 1, size: int = 20,
    ) -> ResourceListResponse:
        """Liste paginée de resources, optionnellement filtrée par type."""
        query = select(ResourceModel).where(ResourceModel.deleted_at.is_(None))
        count_query = select(func.count()).select_from(ResourceModel).where(
            ResourceModel.deleted_at.is_(None)
        )
        if type_filter:
            query = query.where(ResourceModel.type == type_filter)
            count_query = count_query.where(ResourceModel.type == type_filter)

        total = (await self._session.execute(count_query)).scalar_one()
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(
            ResourceModel.created_at.desc()
        )
        results = (await self._session.execute(query)).scalars().all()
        items = [self._to_resource_read(r, {}) for r in results]

        return ResourceListResponse(
            items=items, total=total, page=page, size=size, type_filter=type_filter,
        )

    async def update(
        self, resource_id: UUID, request: ResourceUpdate,
        author_id: UUID | None = None,
    ) -> ResourceRead | None:
        """Met à jour une resource — crée une Revision + ResourceDiff (CON-010)."""
        resource = await self._session.get(ResourceModel, resource_id)
        if resource is None or resource.deleted_at is not None:
            return None

        model_cls = self._get_model_cls(resource.type)
        type_instance = await self._session.get(model_cls, resource_id)
        if type_instance is None:
            return None

        safe_data = self._filter_data(model_cls, request.data)
        field_changes = self._compute_field_changes(type_instance, safe_data)
        next_version = await self._get_next_version(resource_id)

        await self._create_revision(
            resource_id=resource_id, version=next_version,
            justification=request.justification, author_id=author_id,
            diff_data={"field_changes": field_changes},
        )
        await self._session.commit()

        logger.info("resource_updated", resource_id=str(resource_id),
                     type=resource.type, version=next_version,
                     justification=request.justification)
        result = await self.get(resource_id)
        if result:
            await self._broadcast_event(
                EventType.resource_updated, resource_id, resource.type,
                {"version": next_version, "changes": field_changes},
            )
        return result

    async def delete(
        self, resource_id: UUID, justification: str = "Suppression",
        author_id: UUID | None = None,
    ) -> bool:
        """Soft delete — marque deleted_at + crée une Revision finale (CON-010)."""
        resource = await self._session.get(ResourceModel, resource_id)
        if resource is None or resource.deleted_at is not None:
            return False

        resource.deleted_at = datetime.now(UTC)
        next_version = await self._get_next_version(resource_id)

        await self._create_revision(
            resource_id=resource_id, version=next_version,
            justification=f"[DELETED] {justification}", author_id=author_id,
        )
        await self._session.commit()

        logger.info("resource_soft_deleted", resource_id=str(resource_id),
                     version=next_version)
        await self._broadcast_event(
            EventType.resource_deleted, resource_id, resource.type,
            {"version": next_version},
        )
        return True

    async def list_revisions(self, resource_id: UUID) -> list[RevisionRead]:
        """Liste l'historique des révisions d'une resource."""
        result = await self._session.execute(
            select(RevisionModel)
            .where(RevisionModel.target_id == resource_id)
            .order_by(RevisionModel.version.desc())
        )
        return [
            RevisionRead(
                id=r.id, target_id=r.target_id, version=r.version,
                author_id=r.author_id, justification=r.justification,
                valid_time_start=r.valid_time_start,
                valid_time_end=r.valid_time_end,
                transaction_time=r.transaction_time, created_at=r.created_at,
            )
            for r in result.scalars().all()
        ]

    @staticmethod
    def list_types() -> list[str]:
        """Retourne la liste des types disponibles."""
        return sorted(RESOURCE_TYPES.keys())

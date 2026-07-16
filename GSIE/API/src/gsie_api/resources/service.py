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


class ResourceService:
    """Service CRUD générique pour les 73 types du métamodèle v6.2."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _get_model_cls(self, type_name: str) -> type:
        """Récupère la classe modèle SQLAlchemy pour un type donné."""
        if type_name not in RESOURCE_TYPES:
            raise ValueError(
                f"Type inconnu : {type_name}. "
                f"Types disponibles : {sorted(RESOURCE_TYPES.keys())}"
            )
        return RESOURCE_TYPES[type_name]

    @staticmethod
    def _generate_gsie_id(type_name: str) -> str:
        """Génère un identifiant lisible (ex. assertion:2026:a1b2c3d4)."""
        year = datetime.now(UTC).year
        short_uuid = uuid4().hex[:8]
        return f"{type_name}:{year}:{short_uuid}"

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
            resource_diff = ResourceDiffModel(
                id=uuid4(),
                revision_id=revision.id,
                field_changes=diff_data.get("field_changes", []),
                added_relations=diff_data.get("added_relations", []),
                removed_relations=diff_data.get("removed_relations", []),
            )
            self._session.add(resource_diff)
            revision.diff_id = resource_diff.id

        return revision

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
            logger.warning("ws_broadcast_failed", event_type=event_type)

    async def create(self, request: ResourceCreate, author_id: UUID | None = None) -> ResourceRead:
        """Crée une resource + sa ligne dans la table du type + Revision v1."""
        model_cls = self._get_model_cls(request.type)

        # Validation dynamique des données
        errors = validate_resource_data(request.type, request.data)
        if errors:
            raise ValueError(f"Validation échouée : {'; '.join(errors)}")

        gsie_id = request.gsie_id or self._generate_gsie_id(request.type)

        # Créer la ligne racine dans resource
        resource = ResourceModel(
            type=request.type,
            gsie_id=gsie_id,
        )
        self._session.add(resource)
        await self._session.flush()

        # Créer la ligne dans la table du type
        type_instance = model_cls(id=resource.id, **request.data)
        self._session.add(type_instance)

        # Revision v1 (CON-010)
        await self._create_revision(
            resource_id=resource.id,
            version=1,
            justification="Création initiale",
            author_id=author_id,
        )

        await self._session.commit()

        logger.info(
            "resource_created",
            resource_id=str(resource.id),
            type=request.type,
            gsie_id=gsie_id,
        )

        await self._broadcast_event(
            EventType.resource_created,
            resource.id,
            request.type,
            {"gsie_id": gsie_id, **request.data},
        )

        return ResourceRead(
            id=resource.id,
            type=resource.type,
            gsie_id=resource.gsie_id,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
            metadata_json=resource.metadata_json,
            data=request.data,
        )

    async def get(self, resource_id: UUID) -> ResourceRead | None:
        """Récupère une resource par son ID (exclut les soft-deleted)."""
        result = await self._session.get(ResourceModel, resource_id)
        if result is None or result.deleted_at is not None:
            return None

        return await self._build_resource_read(result)

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

    async def list_resources(
        self,
        type_filter: str | None = None,
        page: int = 1,
        size: int = 20,
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
        items = [
            ResourceRead(
                id=r.id,
                type=r.type,
                gsie_id=r.gsie_id,
                created_at=r.created_at,
                updated_at=r.updated_at,
                metadata_json=r.metadata_json,
                data={},
            )
            for r in results
        ]

        return ResourceListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            type_filter=type_filter,
        )

    async def update(
        self,
        resource_id: UUID,
        request: ResourceUpdate,
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

        # Calculer le diff
        field_changes: list[dict[str, Any]] = []
        for key, new_value in request.data.items():
            if not hasattr(type_instance, key):
                continue
            old_value = getattr(type_instance, key)
            if old_value != new_value:
                field_changes.append(
                    {
                        "field": key,
                        "old_value": str(old_value) if old_value is not None else None,
                        "new_value": str(new_value) if new_value is not None else None,
                    }
                )
                setattr(type_instance, key, new_value)

        # Récupérer la version courante
        current_version = (
            await self._session.execute(
                select(func.max(RevisionModel.version)).where(
                    RevisionModel.target_id == resource_id
                )
            )
        ).scalar_one()
        next_version = (current_version or 0) + 1

        # Créer la Revision + ResourceDiff
        await self._create_revision(
            resource_id=resource_id,
            version=next_version,
            justification=request.justification,
            author_id=author_id,
            diff_data={"field_changes": field_changes},
        )

        await self._session.commit()

        logger.info(
            "resource_updated",
            resource_id=str(resource_id),
            type=resource.type,
            version=next_version,
            justification=request.justification,
        )

        result = await self.get(resource_id)
        if result:
            await self._broadcast_event(
                EventType.resource_updated,
                resource_id,
                resource.type,
                {"version": next_version, "changes": field_changes},
            )
        return result

    async def delete(
        self,
        resource_id: UUID,
        justification: str = "Suppression",
        author_id: UUID | None = None,
    ) -> bool:
        """Soft delete — marque deleted_at + crée une Revision finale (CON-010)."""
        resource = await self._session.get(ResourceModel, resource_id)
        if resource is None or resource.deleted_at is not None:
            return False

        # Soft delete
        resource.deleted_at = datetime.now(UTC)

        # Revision finale
        current_version = (
            await self._session.execute(
                select(func.max(RevisionModel.version)).where(
                    RevisionModel.target_id == resource_id
                )
            )
        ).scalar_one()
        next_version = (current_version or 0) + 1

        await self._create_revision(
            resource_id=resource_id,
            version=next_version,
            justification=f"[DELETED] {justification}",
            author_id=author_id,
        )

        await self._session.commit()

        logger.info(
            "resource_soft_deleted",
            resource_id=str(resource_id),
            version=next_version,
        )

        await self._broadcast_event(
            EventType.resource_deleted,
            resource_id,
            resource.type,
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
        revisions = result.scalars().all()
        return [
            RevisionRead(
                id=r.id,
                target_id=r.target_id,
                version=r.version,
                author_id=r.author_id,
                justification=r.justification,
                valid_time_start=r.valid_time_start,
                valid_time_end=r.valid_time_end,
                transaction_time=r.transaction_time,
                created_at=r.created_at,
            )
            for r in revisions
        ]

    @staticmethod
    def list_types() -> list[str]:
        """Retourne la liste des types disponibles."""
        return sorted(RESOURCE_TYPES.keys())

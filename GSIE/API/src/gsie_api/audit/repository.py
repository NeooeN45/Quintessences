"""Dépôt SQLAlchemy du journal d'audit append-only."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.audit.service import AuditEntry
from gsie_api.infrastructure.models.audit_log import AuditLogModel


class SqlAlchemyAuditRepository:
    """Implémentation SQLAlchemy du protocole AuditRepositoryProtocol."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert(self, entry: AuditEntry) -> AuditEntry:
        model = AuditLogModel(
            id=entry.id,
            timestamp=entry.timestamp,
            actor_id=entry.actor_id,
            actor_email=entry.actor_email,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            ip_address=entry.ip_address,
            user_agent=entry.user_agent,
            organisation_id=entry.organisation_id,
            workspace_id=entry.workspace_id,
            status_code=entry.status_code,
            method=entry.method,
            path=entry.path,
            details=entry.details,
            trace_id=entry.trace_id,
        )
        self._session.add(model)
        await self._session.flush()
        return self._entry(model)

    async def list_entries(
        self,
        *,
        actor_id: UUID | None = None,
        resource_type: str | None = None,
        action: str | None = None,
        organisation_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditEntry], int]:
        filters = []
        if actor_id is not None:
            filters.append(AuditLogModel.actor_id == actor_id)
        if resource_type is not None:
            filters.append(AuditLogModel.resource_type == resource_type)
        if action is not None:
            filters.append(AuditLogModel.action == action)
        if organisation_id is not None:
            filters.append(AuditLogModel.organisation_id == organisation_id)

        count = await self._session.scalar(
            select(func.count()).select_from(AuditLogModel).where(*filters)
        )
        statement = (
            select(AuditLogModel)
            .where(*filters)
            .order_by(AuditLogModel.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        models = (await self._session.execute(statement)).scalars().all()
        return [self._entry(m) for m in models], int(count or 0)

    @staticmethod
    def _entry(model: AuditLogModel) -> AuditEntry:
        return AuditEntry(
            id=model.id,
            timestamp=model.timestamp,
            actor_id=model.actor_id,
            actor_email=model.actor_email,
            action=model.action,
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            organisation_id=model.organisation_id,
            workspace_id=model.workspace_id,
            status_code=model.status_code,
            method=model.method,
            path=model.path,
            details=dict(model.details),
            trace_id=model.trace_id,
        )

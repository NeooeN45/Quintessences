"""Service audit — écriture et lecture du journal d'audit append-only.

Le service ne dépend que du protocole AuditRepositoryProtocol — testable
avec un fake. L'écriture est fire-and-forget : une erreur d'audit ne
doit jamais casser la requête principale.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuditEntry:
    """Entrée du journal d'audit — immutable."""

    id: UUID
    timestamp: datetime
    actor_id: UUID | None
    actor_email: str | None
    action: str
    resource_type: str
    resource_id: str | None
    ip_address: str | None
    user_agent: str | None
    organisation_id: UUID | None
    workspace_id: UUID | None
    status_code: int | None
    method: str | None
    path: str | None
    details: dict[str, object]
    trace_id: str | None


class AuditRepositoryProtocol(Protocol):
    """Contrat de persistance requis par le service audit."""

    async def insert(self, entry: AuditEntry) -> AuditEntry: ...

    async def list_entries(
        self,
        *,
        actor_id: UUID | None = None,
        resource_type: str | None = None,
        action: str | None = None,
        organisation_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditEntry], int]: ...


class AuditService:
    """Écrit et lit le journal d'audit append-only."""

    def __init__(self, repository: AuditRepositoryProtocol) -> None:
        self._repository = repository

    async def log(self, entry: AuditEntry) -> AuditEntry:
        """Insère une entrée d'audit. Append-only — jamais modifiée."""
        return await self._repository.insert(entry)

    async def list(
        self,
        *,
        actor_id: UUID | None = None,
        resource_type: str | None = None,
        action: str | None = None,
        organisation_id: UUID | None = None,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[AuditEntry], int]:
        """Liste les entrées d'audit avec filtrage et pagination."""
        return await self._repository.list_entries(
            actor_id=actor_id,
            resource_type=resource_type,
            action=action,
            organisation_id=organisation_id,
            offset=(page - 1) * size,
            limit=size,
        )

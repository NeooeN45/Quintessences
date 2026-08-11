"""Schemas Pydantic pour la feature Audit (v2 persistant).

Alignés sur le contrat du frontend (AuditLogViewer.tsx) avec extension
pour les nouveaux champs (actor_id, organisation_id, status_code, etc.).
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

AuditAction = Literal[
    "create", "read", "update", "delete", "export", "login", "logout", "invite", "revoke", "sync"
]


class AuditLogResponse(BaseModel):
    """Une entrée de journal d'audit — réponse API."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    timestamp: datetime
    actor_id: UUID | None = None
    actor_email: str | None = None
    action: AuditAction
    resource_type: str
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    organisation_id: UUID | None = None
    workspace_id: UUID | None = None
    status_code: int | None = None
    method: str | None = None
    path: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None


class AuditLogPage(BaseModel):
    """Réponse paginée du journal d'audit."""

    model_config = ConfigDict(extra="forbid")

    items: list[AuditLogResponse]
    page: int
    size: int
    total: int


# Alias pour compatibilité avec le frontend existant (AuditLog)
AuditLog = AuditLogResponse
AuditLogListResponse = AuditLogPage

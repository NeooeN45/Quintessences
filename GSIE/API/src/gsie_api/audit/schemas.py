"""Schémas Pydantic pour la feature Audit.

Alignés sur le contrat du frontend (AuditLogViewer.tsx) :
- AuditLog : id, timestamp, user, action, resource, ip, details
- AuditLogListResponse : items + total (pagination future)
"""

from typing import Any

from pydantic import BaseModel, Field


class AuditLog(BaseModel):
    """Une entrée de journal d'audit."""

    id: str = Field(..., description="Identifiant unique de l'entrée")
    timestamp: str = Field(..., description="ISO 8601 — moment de l'action")
    user: str = Field(..., description="Utilisateur ayant effectué l'action")
    action: str = Field(
        ...,
        description="Type d'action : create | update | delete | export",
    )
    resource: str = Field(..., description="Ressource concernée (type + id)")
    ip: str = Field(..., description="Adresse IP d'origine")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Détails contextuels supplémentaires",
    )


class AuditLogListResponse(BaseModel):
    """Réponse paginée — actuellement une simple liste (Phase 4)."""

    items: list[AuditLog] = Field(default_factory=list)
    total: int = Field(0, ge=0, description="Nombre total d'entrées")

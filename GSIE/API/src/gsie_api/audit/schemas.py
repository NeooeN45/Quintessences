"""Schemas Pydantic pour la feature Audit (v2 persistant).

Alignés sur le contrat du frontend (AuditLogViewer.tsx) avec extension
pour les nouveaux champs (actor_id, organisation_id, status_code, etc.).
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

AuditAction = Literal[
    "create",
    "read",
    "update",
    "delete",
    "export",
    "login",
    "logout",
    "invite",
    "revoke",
    "sync",
    "login_failed",
    "login_locked",
    "login_mfa_challenge",
    "login_success",
    "mfa_disable_step_up_failed",
    "mfa_disabled",
    "mfa_login_failed",
    "mfa_recovery_failed",
    "mfa_setup",
    "mfa_verify_failed",
    "mfa_verify_success",
    "oidc_link_required",
    "oidc_login_failed",
    "register_password_compromised",
    "register_password_weak",
    "register_success",
    "session_revoked",
    "sessions_revoked_all",
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

"""Événements d'authentification — bridge vers le journal d'audit.

Capture les événements spécifiques à l'authentification (login réussi/échoué,
lockout, MFA, lien provider, révocation) et les insère dans le journal d'audit
append-only existant. Fire-and-forget : une erreur d'audit ne casse jamais
la requête principale.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from gsie_api.audit.repository import SqlAlchemyAuditRepository
from gsie_api.audit.service import AuditEntry, AuditService
from gsie_api.core.logging import get_logger

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger("gsie_api.auth.auth_events")


async def log_auth_event(
    session: AsyncSession,
    *,
    action: str,
    actor_id: UUID | None = None,
    actor_email: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    status_code: int | None = None,
    details: dict[str, object] | None = None,
) -> None:
    """Insère un événement d'authentification dans le journal d'audit.

    Fire-and-forget : toute exception est loggée mais jamais propagée.
    """
    try:
        entry = AuditEntry(
            id=uuid4(),
            timestamp=datetime.now(UTC),
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            resource_type="auth",
            resource_id=str(actor_id) if actor_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            organisation_id=None,
            workspace_id=None,
            status_code=status_code,
            method=None,
            path=None,
            details=details or {},
            trace_id=None,
        )
        service = AuditService(SqlAlchemyAuditRepository(session))
        await service.log(entry)
    except Exception:
        logger.exception("auth_event_log_failed", action=action)

"""Middleware d'audit — capture automatique des mutations HTTP.

Capture les requêtes POST/PUT/PATCH/DELETE et les journalise dans
``audit_log`` après exécution. Les requêtes GET ne sont pas journalisées
par défaut (volume trop élevé) sauf si ``audit_get_requests`` est activé.

Le middleware est fire-and-forget : une erreur d'audit ne doit jamais
casser la requête principale. Les erreurs sont loggées mais pas
propagées.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from starlette.middleware.base import RequestResponseEndpoint
    from starlette.requests import Request
    from starlette.responses import Response

from gsie_api.audit.service import AuditEntry, AuditService
from gsie_api.core.logging import get_logger

logger = get_logger("gsie_api.audit.middleware")

_MUTATION_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Routes exclues de l'audit (health, metrics, docs).
_EXCLUDED_PREFIXES = frozenset(
    {"/health", "/metrics", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}
)


def _extract_actor(request: Request) -> tuple[UUID | None, str | None]:
    """Extrait l'ID et l'email de l'acteur depuis le state de la requête."""
    user = request.state.user if hasattr(request.state, "user") else None
    if user is None:
        return None, None
    try:
        actor_id = UUID(str(user.get("sub", "")))
    except (ValueError, TypeError):
        actor_id = None
    actor_email = user.get("email") if isinstance(user, dict) else None
    return actor_id, actor_email


def _extract_resource(request: Request) -> tuple[str, str | None]:
    """Déduit resource_type et resource_id depuis le path et la méthode."""
    path = request.url.path
    # /api/v1/orgs/{org_id}/workspaces → resource_type=organisation_workspace
    # /api/v1/resources/{resource_id} → resource_type=resource
    parts = [p for p in path.split("/") if p]
    if not parts:
        return "unknown", None
    # Ignorer le préfixe api/v1
    if parts[0] == "api" and len(parts) > 1 and parts[1].startswith("v"):
        parts = parts[2:]
    if not parts:
        return "unknown", None
    resource_type = parts[0]
    resource_id = parts[1] if len(parts) > 1 else None
    return resource_type, resource_id


def _deduce_action(method: str, path: str) -> str:
    """Déduit l'action d'audit depuis la méthode HTTP et le path."""
    if "auth" in path and "login" in path:
        return "login"
    if "auth" in path and "logout" in path:
        return "logout"
    if "members" in path and method == "POST":
        return "invite"
    if "members" in path and method == "DELETE":
        return "revoke"
    if "sync" in path:
        return "sync"
    if method == "POST":
        return "create"
    if method in ("PUT", "PATCH"):
        return "update"
    if method == "DELETE":
        return "delete"
    if "export" in path:
        return "export"
    return "read"


class AuditMiddleware(BaseHTTPMiddleware):
    """Capture les mutations HTTP et les journalise dans audit_log."""

    def __init__(self, app: Any, audit_service: AuditService) -> None:
        super().__init__(app)
        self._audit_service = audit_service

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Exclure les routes techniques
        path = request.url.path
        if any(path.startswith(prefix) for prefix in _EXCLUDED_PREFIXES):
            return await call_next(request)

        # Exclure les GET sauf si explicitement demandé
        method = request.method.upper()
        if method not in _MUTATION_METHODS:
            return await call_next(request)

        response = await call_next(request)

        # Fire-and-forget : ne jamais casser la requête
        try:
            await self._log_request(request, response, method, path)
        except Exception:
            logger.warning("audit_log_failed", path=path, method=method, exc_info=True)

        return response

    async def _log_request(
        self,
        request: Request,
        response: Response,
        method: str,
        path: str,
    ) -> None:
        from datetime import UTC, datetime

        actor_id, actor_email = _extract_actor(request)
        resource_type, resource_id = _extract_resource(request)
        action = _deduce_action(method, path)

        # IP d'origine — respecte Cloudflare (CF-Connecting-IP)
        ip_address = (
            request.headers.get("CF-Connecting-IP")
            or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.client.host
            if request.client
            else None
        )
        user_agent = request.headers.get("User-Agent")
        trace_id = getattr(request.state, "trace_id", None)

        entry = AuditEntry(
            id=uuid4(),
            timestamp=datetime.now(UTC),
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            organisation_id=None,
            workspace_id=None,
            status_code=response.status_code,
            method=method,
            path=path,
            details={},
            trace_id=trace_id if isinstance(trace_id, str) else None,
        )
        await self._audit_service.log(entry)

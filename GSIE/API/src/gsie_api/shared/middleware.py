"""Middleware — trace_id, headers de sécurité, timing, limite taille requête.

CON-005 : traçabilité via trace_id propagé dans logs et réponses.
Sécurité : validation trace_id + headers OWASP A05 + limite taille corps.
"""

import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger, set_trace_id

_settings = get_settings()

# Regex de validation du trace_id client (CON-005 + sécurité anti-injection)
# Format : alphanumérique + tirets, max 64 caractères
_TRACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9\-]{1,64}$")

# Headers de sécurité ajoutés à chaque réponse (OWASP A05)
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}

# Taille max du corps de requête (bytes) — défaut 1 MiB
_MAX_BODY_SIZE = _settings.max_request_body_size


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Injecte un trace_id + headers de sécurité + limite taille corps.

    Si le client fournit X-Trace-Id et qu'il est valide (regex), on le réutilise.
    Sinon, on génère un UUID4.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Limite taille corps de requête (OWASP A04)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > _MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large", "error_code": "PAYLOAD_TOO_LARGE"},
            )

        client_trace_id = request.headers.get("X-Trace-Id")
        validated_id = _validate_trace_id(client_trace_id)
        trace_id = set_trace_id(validated_id)

        logger = get_logger("gsie_api.middleware")
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        # Headers de sécurité (OWASP A05)
        for header, value in _SECURITY_HEADERS.items():
            response.headers[header] = value

        # Suppression du header Server (fingerprinting OWASP A05)
        if "server" in response.headers:
            del response.headers["server"]

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response


def _validate_trace_id(client_trace_id: str | None) -> str | None:
    """Valide le trace_id client. Retourne None si invalide (UUID généré ensuite)."""
    if client_trace_id is None:
        return None
    if _TRACE_ID_PATTERN.match(client_trace_id):
        return client_trace_id
    return None

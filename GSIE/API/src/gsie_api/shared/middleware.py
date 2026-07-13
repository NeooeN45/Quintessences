"""Middleware — trace_id injection + headers de sécurité + timing.

CON-005 : traçabilité via trace_id propagé dans logs et réponses.
Sécurité : validation du trace_id client + headers de sécurité.
"""

import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from gsie_api.core.logging import get_logger, set_trace_id

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
}


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Injecte un trace_id dans chaque requête (CON-005 traçabilité).

    Si le client fournit X-Trace-Id et qu'il est valide (regex), on le réutilise.
    Sinon, on génère un UUID4.
    Le trace_id est propagé dans les logs structlog et la réponse.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
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
    # Trace ID invalide — on ignore la valeur client et on générera un UUID
    return None

"""Middleware — trace_id injection + CORS + timing."""

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from gsie_api.core.logging import get_logger, set_trace_id


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Injecte un trace_id dans chaque requête (CON-005 traçabilité).

    Si le client fournit X-Trace-Id, on le réutilise.
    Sinon, on génère un UUID4.
    Le trace_id est propagé dans les logs structlog et la réponse.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        client_trace_id = request.headers.get("X-Trace-Id")
        trace_id = set_trace_id(client_trace_id)

        logger = get_logger("gsie_api.middleware")
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response

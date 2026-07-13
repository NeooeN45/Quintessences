"""Application FastAPI — point d'entrée principal.

Architecture (DEC-000019) :
- Clean architecture par modules moteurs (pas DDD pur)
- OpenTelemetry pour observabilité (CON-005)
- TraceId middleware : traçabilité + headers de sécurité + limite taille
- Health/Ready séparés : liveness (instantané) vs readiness (DB+Redis + cache)
- Rate limiting (OWASP A07 — slowapi)
- Documentation désactivée en production (OWASP A05)
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger, setup_logging
from gsie_api.engines.evidence.router import router as evidence_router
from gsie_api.engines.gis.router import router as gis_router
from gsie_api.engines.knowledge.router import router as knowledge_router
from gsie_api.infrastructure.health import router as health_router
from gsie_api.shared.middleware import TraceIdMiddleware

_settings = get_settings()
logger = get_logger("gsie_api.app")

# Rate limiter — par IP, configurable (OWASP A07)
# default_limits s'applique à toutes les routes sans décorateur explicite
limiter = Limiter(
    key_func=get_remote_address,
    enabled=_settings.rate_limit_enabled,
    default_limits=[_settings.rate_limit_default],
)

# Tags OpenAPI déclarés à la racine pour groupement Swagger/ReDoc
_OPENAPI_TAGS = [
    {"name": "health", "description": "Health checks — liveness (/health) et readiness (/ready)"},
    {"name": "evidence", "description": "Evidence Engine — collecte et validation de sources"},
    {"name": "knowledge", "description": "Knowledge Engine — structuration des connaissances"},
    {"name": "gis", "description": "GIS Engine — traitement géospatial"},
]

# CORS — méthodes et headers explicites (sécurité OWASP A05)
_ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
_ALLOWED_HEADERS = ["Content-Type", "Authorization", "X-Trace-Id"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Cycle de vie : startup + shutdown."""
    setup_logging(_settings.log_level, _settings.environment)
    logger.info(
        "api_starting",
        app=_settings.app_name,
        version=_settings.app_version,
        environment=_settings.environment,
    )
    yield
    logger.info("api_stopping")


def create_app() -> FastAPI:
    """Factory FastAPI — app creation avec tous les middlewares et routes."""
    is_production = _settings.environment == "production"

    app = FastAPI(
        title=_settings.app_name,
        version=_settings.app_version,
        description="GSIE — General System Intelligence Engine API",
        lifespan=lifespan,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else f"{_settings.api_v1_prefix}/openapi.json",
        openapi_tags=_OPENAPI_TAGS,
    )

    # Rate limiting (OWASP A07 — slowapi)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Middlewares (ordre important : trace_id en premier)
    app.add_middleware(TraceIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.cors_origins,
        allow_credentials=True,
        allow_methods=_ALLOWED_METHODS,
        allow_headers=_ALLOWED_HEADERS,
    )

    # Routes — health/ready à la racine, moteurs sous /api/v1/
    app.include_router(health_router)
    app.include_router(evidence_router, prefix=_settings.api_v1_prefix)
    app.include_router(knowledge_router, prefix=_settings.api_v1_prefix)
    app.include_router(gis_router, prefix=_settings.api_v1_prefix)

    return app


app = create_app()

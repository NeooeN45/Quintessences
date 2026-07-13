"""Application FastAPI — point d'entrée principal.

Architecture (DEC-000019) :
- Clean architecture par modules moteurs (pas DDD pur)
- OpenTelemetry pour observabilité (CON-005)
- TraceId middleware pour traçabilité
- Health endpoint pour monitoring
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gsie_api.core.config import get_settings
from gsie_api.core.health import router as health_router
from gsie_api.core.logging import get_logger, setup_logging
from gsie_api.engines.evidence.router import router as evidence_router
from gsie_api.engines.gis.router import router as gis_router
from gsie_api.engines.knowledge.router import router as knowledge_router
from gsie_api.shared.middleware import TraceIdMiddleware

_settings = get_settings()
logger = get_logger("gsie_api.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Cycle de vie : startup + shutdown."""
    setup_logging(_settings.log_level)
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
    app = FastAPI(
        title=_settings.app_name,
        version=_settings.app_version,
        description="GSIE — General System Intelligence Engine API",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{_settings.api_v1_prefix}/openapi.json",
    )

    # Middlewares (ordre important : trace_id en premier)
    app.add_middleware(TraceIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes — health à la racine, moteurs sous /api/v1/
    app.include_router(health_router)
    app.include_router(evidence_router, prefix=_settings.api_v1_prefix)
    app.include_router(knowledge_router, prefix=_settings.api_v1_prefix)
    app.include_router(gis_router, prefix=_settings.api_v1_prefix)

    return app


app = create_app()

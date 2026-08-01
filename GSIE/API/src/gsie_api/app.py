"""Application FastAPI — point d'entrée principal.

Architecture (DEC-000019) :
- Clean architecture par modules moteurs (pas DDD pur)
- OpenTelemetry pour observabilité (CON-005) — instrumentation conditionnelle
- Prometheus /metrics pour monitoring production
- TraceId middleware : traçabilité + headers de sécurité + limite taille
- Health/Ready séparés : liveness (instantané) vs readiness (DB+Redis + cache)
- Rate limiting (OWASP A07 — slowapi, middleware ASGI pour performance)
- Gzip compression (performance)
- Documentation désactivée en production (OWASP A05)
- RFC 7807 Problem Details pour les réponses d'erreur
- 404 handler custom avec trace_id (ne divulgue pas l'arborescence)
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIASGIMiddleware

from gsie_api.auth.router import router as auth_router
from gsie_api.core.config import get_settings
from gsie_api.core.limiter import limiter
from gsie_api.core.logging import get_logger, setup_logging
from gsie_api.core.rbac import require_roles
from gsie_api.engines.botanical.router import router as botanical_router
from gsie_api.engines.climate.router import router as climate_router
from gsie_api.engines.correlation.router import router as correlation_router
from gsie_api.engines.diagnostic.router import router as diagnostic_router
from gsie_api.engines.evidence.router import router as evidence_router
from gsie_api.engines.forest_dynamics.router import router as forest_dynamics_router
from gsie_api.engines.gis.router import router as gis_router
from gsie_api.engines.knowledge.router import router as knowledge_router
from gsie_api.engines.learning.router import router as learning_router
from gsie_api.engines.orchestration.router import router as orchestration_router
from gsie_api.engines.pedology.router import router as pedology_router
from gsie_api.engines.reasoning.router import router as reasoning_router
from gsie_api.engines.recommendation.router import router as recommendation_router
from gsie_api.engines.simulation.router import router as simulation_router
from gsie_api.engines.validation.router import router as validation_router
from gsie_api.infrastructure.health import router as health_router
from gsie_api.resources.router import router as resources_router
from gsie_api.shared.middleware import RequestBodyLimitMiddleware, TraceIdMiddleware
from gsie_api.websocket.router import router as ws_router

_settings = get_settings()
logger = get_logger("gsie_api.app")

# Le limiter est défini dans core/limiter.py (storage_uri Redis configuré)
# — importé ci-dessus pour éviter les imports circulaires

# Tags OpenAPI déclarés à la racine pour groupement Swagger/ReDoc
_OPENAPI_TAGS = [
    {"name": "auth", "description": "Authentification JWT RS256 — login, refresh, verify"},
    {"name": "health", "description": "Health checks — liveness (/health) et readiness (/ready)"},
    {"name": "metrics", "description": "Prometheus metrics endpoint (/metrics)"},
    {"name": "resources", "description": "CRUD générique — types enregistrés du métamodèle"},
    {"name": "evidence", "description": "Evidence Engine — collecte et validation de sources"},
    {"name": "knowledge", "description": "Knowledge Engine — structuration des connaissances"},
    {"name": "gis", "description": "GIS Engine — traitement géospatial"},
    {"name": "websocket", "description": "WebSocket temps réel — Hub (UE5.8) et events système"},
    {
        "name": "orchestration",
        "description": ("Chaîne complète — Reasoning → Diagnostic → Recommendation → Validation"),
    },
]

# CORS — méthodes et headers explicites (sécurité OWASP A05)
_ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
_ALLOWED_HEADERS = ["Content-Type", "Authorization", "X-Trace-Id"]


def _build_problem_detail(
    status_code: int,
    title: str,
    detail: str,
    error_code: str,
    trace_id: str,
    request: Request,
) -> dict[str, object]:
    """Construit une réponse d'erreur au format RFC 7807 Problem Details.

    RFC 7807 : https://datatracker.ietf.org/doc/html/rfc7807
    Champs : type, title, status, detail, instance + extensions (error_code, trace_id).
    """
    return {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": request.url.path,
        "error_code": error_code,
        "trace_id": trace_id,
    }


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Cycle de vie : startup + shutdown.

    Startup :
    - OpenTelemetry instrumentation si otel_enabled=True (CON-005)
    - WebSocket : subscriber Redis + heartbeat
    - Graceful shutdown : ferme proprement les connexions DB, Redis et WebSocket
    """
    setup_logging(_settings.log_level, _settings.environment)
    logger.info(
        "api_starting",
        app=_settings.app_name,
        version=_settings.app_version,
        environment=_settings.environment,
    )

    # Privilèges du rôle de connexion — on interroge PostgreSQL, on ne se fie
    # pas au nom présent dans la chaîne de connexion. Un superutilisateur
    # rendrait inopérants l'isolement RGPD et toutes les politiques RLS.
    from gsie_api.infrastructure.database import async_session_factory
    from gsie_api.infrastructure.db_privileges import verifier_privileges_de_connexion

    await verifier_privileges_de_connexion(async_session_factory)

    # OpenTelemetry — instrumentation conditionnelle (CON-005, DEC-000019)
    if _settings.otel_enabled:
        _setup_opentelemetry(app)

    # WebSocket — démarrer le subscriber Redis + heartbeat
    from gsie_api.websocket.manager import manager

    await manager.start_redis_subscriber()
    await manager.start_heartbeat()

    yield
    logger.info("api_stopping")
    # Graceful shutdown — ferme WebSocket, pools de connexions (P0 résilience)
    try:
        await manager.shutdown()
    except Exception as exc:
        logger.error(
            "ws_shutdown_failed",
            error_type=type(exc).__name__,
            error=str(exc),
        )
    try:
        from gsie_api.auth.refresh_tokens import close_refresh_token_store

        await close_refresh_token_store()
    except Exception as exc:
        logger.error(
            "auth_store_shutdown_failed",
            error_type=type(exc).__name__,
            error=str(exc),
        )
    try:
        from gsie_api.infrastructure.database import engine
        from gsie_api.infrastructure.redis_client import redis_pool

        await engine.dispose()
        await redis_pool.disconnect()
        logger.info("connections_closed")
    except Exception as exc:
        logger.error(
            "shutdown_cleanup_failed",
            error_type=type(exc).__name__,
            error=str(exc),
        )


def _setup_opentelemetry(app: FastAPI) -> None:
    """Configure l'instrumentation OpenTelemetry si otel_enabled=True.

    Instrumente FastAPI, SQLAlchemy et Redis pour la traçabilité distribuée (CON-005).
    Les traces sont exportées vers l'endpoint OTLP configuré (otel_endpoint).
    """
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        from gsie_api.infrastructure.database import engine

        resource = Resource.create({"service.name": _settings.otel_service_name})
        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=_settings.otel_endpoint))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
        RedisInstrumentor().instrument()
        logger.info("otel_instrumented", endpoint=_settings.otel_endpoint)
    except Exception as exc:
        logger.error(
            "otel_setup_failed",
            error_type=type(exc).__name__,
            error=str(exc),
        )


def create_app() -> FastAPI:
    """Factory FastAPI — app creation avec tous les middlewares et routes."""
    # La pré-production sert de vraies données et est exposée comme la
    # production. `validate_production_security` les traite déjà à
    # l'identique ; laisser `/docs` et l'OpenAPI ouverts sur l'une des deux
    # revenait à publier l'arborescence que le handler 404 s'applique à taire.
    is_production = _settings.environment in ("production", "staging")

    app = FastAPI(
        title=_settings.app_name,
        version=_settings.app_version,
        description="GSIE — General System Intelligence Engine API",
        lifespan=lifespan,
        debug=_settings.debug,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else f"{_settings.api_v1_prefix}/openapi.json",
        openapi_tags=_OPENAPI_TAGS,
    )

    # Prometheus /metrics — monitoring production (CON-005)
    #
    # L'endpoint était ouvert dans tous les environnements. Le label `handler`
    # des histogrammes énumère les routes réellement servies : c'est
    # exactement ce que `docs_url=None` et le handler 404 s'appliquent à
    # taire en production. Les compteurs de l'outbox sont en outre labellisés
    # par type d'agrégat (`data_subject`, `consent`), donc la cadence des
    # traitements RGPD devenait publique. Hors développement, il faut le rôle
    # `admin` — un scraper Prometheus porte un jeton comme un autre appelant.
    metrics_dependencies = (
        [] if _settings.environment == "development" else [Depends(require_roles("admin"))]
    )
    Instrumentator().instrument(app).expose(
        app,
        endpoint="/metrics",
        tags=["metrics"],
        include_in_schema=not is_production,
        dependencies=metrics_dependencies,
    )

    # Métriques métier personnalisées (audit qualité base du 2026-08-01) :
    # complétude, fraîcheur, cohérence des données d'enrichissement.
    # Calculées à la demande via /metrics/db-quality (admin-only hors dev).
    from gsie_api.metrics import collect_db_metrics

    # POST et non GET : l'appel n'est pas une lecture. Il déclenche cinq
    # agrégats sur toute la table `resource`, dont des `count(*) FILTER` sur
    # `metadata_json`. En GET, un préchargement de navigateur, un retry de
    # proxy ou un crawler suffisait à les rejouer. Le débit est plafonné dans
    # tous les environnements — l'authentification, elle, ne s'applique pas en
    # développement, où l'endpoint reste donc ouvert.
    #
    # À terme, une tâche périodique devrait alimenter les Gauges plutôt qu'un
    # déclenchement par requête, comme l'annonce le docstring de
    # `collect_db_metrics`.
    @app.post(
        "/metrics/db-quality",
        tags=["metrics"],
        include_in_schema=not is_production,
        dependencies=metrics_dependencies,
    )
    @limiter.limit("6/minute")
    async def _db_quality_metrics(request: Request, response: Response) -> dict[str, str]:
        """Déclenche le calcul des métriques de qualité DB et retourne un ack."""
        # Le calcul publie directement dans le registry Prometheus par défaut.
        # Il est attendu : `collect_db_metrics` est une coroutine, la boucle
        # asyncio du serveur est déjà en cours.
        try:
            await collect_db_metrics()
        except Exception as exc:
            # L'ack ne doit pas annoncer une collecte qui n'a pas eu lieu. Le
            # motif reste generique — le texte du pilote est deja au journal
            # (`collect_db_metrics` le trace avant de relayer).
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Collecte des metriques de qualite DB indisponible",
            ) from exc
        return {"status": "collected"}

    # Rate limiting (OWASP A07 — slowapi, middleware ASGI pour performance)
    app.state.limiter = limiter

    def _rate_limit_handler(request: Request, exc: Exception) -> Response:
        if isinstance(exc, RateLimitExceeded):
            return _rate_limit_exceeded_handler(request, exc)
        logger.error("unexpected_rate_limit_exception", exc_type=type(exc).__name__)
        raise TypeError(f"Unexpected exception type: {type(exc).__name__}")

    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_middleware(SlowAPIASGIMiddleware)

    # Middlewares : Starlette place le dernier ajouté à l'extérieur.
    # Gzip : compresse les réponses > 500 bytes (performance)
    app.add_middleware(GZipMiddleware, minimum_size=500)
    # Compte aussi les fragments sans Content-Length (Transfer-Encoding chunked).
    app.add_middleware(RequestBodyLimitMiddleware, max_body_size=_settings.max_request_body_size)
    # CORS : origines restrictives
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.cors_origins,
        allow_credentials=True,
        allow_methods=_ALLOWED_METHODS,
        allow_headers=_ALLOWED_HEADERS,
    )

    # Outermost : ajoute trace_id et headers de sécurité aux réponses CORS et 413.
    app.add_middleware(TraceIdMiddleware)
    # Routes — health/ready à la racine, auth + moteurs sous /api/v1/
    app.include_router(health_router)
    app.include_router(auth_router, prefix=_settings.api_v1_prefix)
    app.include_router(resources_router, prefix=_settings.api_v1_prefix)
    app.include_router(evidence_router, prefix=_settings.api_v1_prefix)
    app.include_router(knowledge_router, prefix=_settings.api_v1_prefix)
    app.include_router(correlation_router, prefix=_settings.api_v1_prefix)
    app.include_router(gis_router, prefix=_settings.api_v1_prefix)
    app.include_router(botanical_router, prefix=_settings.api_v1_prefix)
    app.include_router(pedology_router, prefix=_settings.api_v1_prefix)
    app.include_router(forest_dynamics_router, prefix=_settings.api_v1_prefix)
    app.include_router(climate_router, prefix=_settings.api_v1_prefix)
    app.include_router(reasoning_router, prefix=_settings.api_v1_prefix)
    app.include_router(diagnostic_router, prefix=_settings.api_v1_prefix)
    app.include_router(recommendation_router, prefix=_settings.api_v1_prefix)
    app.include_router(validation_router, prefix=_settings.api_v1_prefix)
    app.include_router(simulation_router, prefix=_settings.api_v1_prefix)
    app.include_router(learning_router, prefix=_settings.api_v1_prefix)
    # Enregistre apres les moteurs qu'il enchaine : l'orchestration ne fait
    # que les brancher les uns sur les autres (GSIE-CON-007).
    app.include_router(orchestration_router, prefix=_settings.api_v1_prefix)
    app.include_router(ws_router, prefix=_settings.api_v1_prefix)

    # 404 handler custom — RFC 7807 Problem Details (OWASP A05)
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        trace_id = request.headers.get("X-Trace-Id", "")
        return JSONResponse(
            status_code=404,
            content=_build_problem_detail(
                status_code=404,
                title="Not Found",
                detail="Resource not found",
                error_code="NOT_FOUND",
                trace_id=trace_id,
                request=request,
            ),
        )

    # Handler global 500 — RFC 7807 Problem Details (OWASP A05)
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        trace_id = request.headers.get("X-Trace-Id", "")
        logger.error(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            error_type=type(exc).__name__,
            error=str(exc),
            trace_id=trace_id,
        )
        return JSONResponse(
            status_code=500,
            content=_build_problem_detail(
                status_code=500,
                title="Internal Server Error",
                detail="Internal server error",
                error_code="INTERNAL_ERROR",
                trace_id=trace_id,
                request=request,
            ),
        )

    # Startup/shutdown WebSocket gérés par le lifespan (plus de on_event déprécié)
    return app


app = create_app()

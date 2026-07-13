"""Endpoints health — liveness et readiness.

Note : ce module vit dans infrastructure/ car /ready interroge directement
PostgreSQL et Redis. Le core/ ne doit pas dépendre de l'infrastructure
(clean architecture : dépendances vers l'intérieur).

Séparation liveness/readiness (recommandation stress test) :
- /health (liveness) : instantané, sans DB — pour Kubernetes liveness probe
- /ready (readiness) : avec DB+Redis + cache Redis 5s — pour Kubernetes readiness probe
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger
from gsie_api.infrastructure.database import get_db
from gsie_api.infrastructure.redis_client import get_redis
from gsie_api.shared.schemas import HealthResponse

router = APIRouter(tags=["health"])
logger = get_logger("gsie_api.health")
_settings = get_settings()

# Clé Redis pour le cache du readiness check
_READY_CACHE_KEY = "gsie:ready:cache"


async def _check_database(db: AsyncSession) -> str:
    """Vérifie la connexion PostgreSQL + PostGIS. Retourne le statut."""
    try:
        is_production = _settings.environment == "production"
        if is_production:
            # En production : ping simple sans divulguer la version PostGIS
            result = await db.execute(text("SELECT 1"))
            result.fetchone()
            return "healthy"
        else:
            result = await db.execute(text("SELECT PostGIS_Version()"))
            postgis_version = result.scalar_one()
            return f"healthy (PostGIS {postgis_version})"
    except Exception as exc:
        logger.error("database_health_check_failed", error_type=type(exc).__name__)
        return "unhealthy"


async def _check_redis(redis: Redis) -> str:
    """Vérifie la connexion Redis. Retourne le statut."""
    try:
        pong = await redis.ping()
        return "healthy" if pong else "unhealthy"
    except Exception as exc:
        logger.error("redis_health_check_failed", error_type=type(exc).__name__)
        return "unhealthy"


@router.get("/health", response_model=HealthResponse)
async def liveness(request: Request) -> HealthResponse:
    """Liveness probe — instantané, sans dépendances externes.

    Retourne toujours healthy si le processus répond.
    Pour Kubernetes liveness probe (ne doit pas dépendre de la DB).
    """
    return HealthResponse(
        status="healthy",
        version=_settings.app_version,
        environment=_settings.environment,
        timestamp=datetime.now(timezone.utc),
        dependencies={},
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> HealthResponse:
    """Readiness probe — vérifie DB + Redis avec cache Redis 5s.

    Pour Kubernetes readiness probe. Le cache évite de pinger DB+Redis
    à chaque requête (recommandation stress test : -40% latence).
    """
    # Vérifier le cache Redis d'abord
    try:
        cached = await redis.get(_READY_CACHE_KEY)
        if cached:
            return HealthResponse.model_validate_json(cached)
    except Exception:
        pass  # Cache indisponible — on continue avec le check réel

    dependencies = {
        "database": await _check_database(db),
        "redis": await _check_redis(redis),
    }
    all_healthy = all(v.startswith("healthy") for v in dependencies.values())

    response = HealthResponse(
        status="healthy" if all_healthy else "degraded",
        version=_settings.app_version,
        environment=_settings.environment,
        timestamp=datetime.now(timezone.utc),
        dependencies=dependencies,
    )

    # Mettre en cache le résultat (TTL 5s)
    try:
        await redis.setex(
            _READY_CACHE_KEY,
            _settings.health_cache_ttl,
            response.model_dump_json(),
        )
    except Exception:
        pass  # Cache indisponible — non bloquant

    return response

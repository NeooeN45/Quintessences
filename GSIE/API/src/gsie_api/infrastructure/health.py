"""Endpoint health — vérifie l'état de l'API et de ses dépendances.

Note : ce module vit dans infrastructure/ car il interroge directement
PostgreSQL et Redis. Le core/ ne doit pas dépendre de l'infrastructure
(clean architecture : dépendances vers l'intérieur).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger
from gsie_api.infrastructure.database import get_db
from gsie_api.infrastructure.redis_client import get_redis
from gsie_api.shared.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger("gsie_api.health")
_settings = get_settings()


async def _check_database(db: AsyncSession) -> str:
    """Vérifie la connexion PostgreSQL + PostGIS. Retourne le statut."""
    try:
        result = await db.execute(text("SELECT PostGIS_Version()"))
        postgis_version = result.scalar_one()
        return f"healthy (PostGIS {postgis_version})"
    except Exception as exc:
        logger.error("database_health_check_failed", error=str(exc))
        return "unhealthy"


async def _check_redis(redis: Redis) -> str:
    """Vérifie la connexion Redis. Retourne le statut."""
    try:
        pong = await redis.ping()
        return "healthy" if pong else "unhealthy"
    except Exception as exc:
        logger.error("redis_health_check_failed", error=str(exc))
        return "unhealthy"


@router.get("", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> HealthResponse:
    """Vérifie l'état de l'API, de la base PostgreSQL/PostGIS et de Redis."""
    dependencies = {
        "database": await _check_database(db),
        "redis": await _check_redis(redis),
    }
    all_healthy = all(v.startswith("healthy") for v in dependencies.values())

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        version=_settings.app_version,
        environment=_settings.environment,
        timestamp=datetime.now(timezone.utc),
        dependencies=dependencies,
    )

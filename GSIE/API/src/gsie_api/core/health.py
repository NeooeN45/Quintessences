"""Endpoint health — vérifie l'état de l'API et de ses dépendances."""

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


@router.get("", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> HealthResponse:
    """Vérifie l'état de l'API, de la base PostgreSQL/PostGIS et de Redis."""
    dependencies: dict[str, str] = {}

    # PostgreSQL + PostGIS
    try:
        result = await db.execute(text("SELECT PostGIS_Version()"))
        postgis_version = result.scalar_one()
        dependencies["database"] = f"healthy (PostGIS {postgis_version})"
    except Exception as exc:
        logger.error("database_health_check_failed", error=str(exc))
        dependencies["database"] = "unhealthy"

    # Redis
    try:
        pong = await redis.ping()
        dependencies["redis"] = "healthy" if pong else "unhealthy"
    except Exception as exc:
        logger.error("redis_health_check_failed", error=str(exc))
        dependencies["redis"] = "unhealthy"

    all_healthy = all(v.startswith("healthy") for v in dependencies.values())
    status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=status,
        version=_settings.app_version,
        environment=_settings.environment,
        timestamp=datetime.now(timezone.utc),
        dependencies=dependencies,
    )

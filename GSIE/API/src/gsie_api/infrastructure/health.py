"""Endpoints health — liveness et readiness.

Note : ce module vit dans infrastructure/ car /ready interroge directement
PostgreSQL et Redis. Le core/ ne doit pas dépendre de l'infrastructure
(clean architecture : dépendances vers l'intérieur).

Les sondes ne sont volontairement pas soumises au rate limiter applicatif.
Leur disponibilité doit rester indépendante de Redis : une panne Redis doit
faire passer `/ready` à 503, sans empêcher `/health` de confirmer que le
processus est vivant. Une éventuelle protection contre l'abus se fait à la
bordure (HAProxy, Cloudflare ou réseau de supervision), pas dans le processus.

Séparation liveness/readiness (recommandation stress test) :
- /health (liveness) : instantané, sans DB — pour Kubernetes liveness probe
- /ready (readiness) : avec DB+Redis + cache Redis 5s — pour Kubernetes readiness probe
"""

from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
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


def _code_http(statut: str) -> int:
    """Traduit le statut de disponibilité en code HTTP.

    Un seul endroit décide, pour que le chemin avec cache et le chemin sans
    cache ne puissent pas diverger : un `degraded` relu du cache rendait
    autrement un 200.
    """
    return status.HTTP_200_OK if statut == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE


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
        timestamp=datetime.now(UTC),
        dependencies={},
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> HealthResponse:
    """Readiness probe — vérifie DB + Redis avec cache Redis 5s.

    Le code HTTP porte la réponse, et non le seul corps : une sonde de
    disponibilité Kubernetes décide sur le statut, jamais sur le contenu. Cet
    endpoint rendait `200` avec un corps `degraded` et une base `unhealthy` —
    vérifié, reproduit. Le pod restait donc en rotation alors que sa base était
    inaccessible, ce qui est exactement ce que la sonde existe pour éviter.

    `503 Service Unavailable` est la réponse attendue d'une sonde readiness :
    « ce processus vit, ne lui envoyez pas de trafic ». Le corps reste complet
    pour le diagnostic — quelle dépendance est tombée.

    `/health` (liveness) reste inconditionnellement `200` : il répond « le
    processus n'est pas bloqué », et rendre 503 y ferait redémarrer le pod pour
    une panne de base qu'un redémarrage ne corrige pas.

    Le cache est appliqué au corps **et** au code : un `degraded` en cache
    rejouerait sinon un 200.
    """
    # Le signal de retrait prime sur le cache : un résultat healthy ancien ne
    # doit jamais maintenir ce replica dans la rotation pendant son arrêt.
    if Path(_settings.graceful_drain_file).is_file():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="degraded",
            version=_settings.app_version,
            environment=_settings.environment,
            timestamp=datetime.now(UTC),
            dependencies={"draining": "active"},
        )

    # Vérifier le cache Redis d'abord
    try:
        cached = await redis.get(_READY_CACHE_KEY)
        if cached:
            en_cache = HealthResponse.model_validate_json(cached)
            response.status_code = _code_http(en_cache.status)
            return en_cache
    except Exception:
        pass  # Cache indisponible — on continue avec le check réel

    dependencies = {
        "database": await _check_database(db),
        "redis": await _check_redis(redis),
    }
    all_healthy = all(v.startswith("healthy") for v in dependencies.values())

    corps = HealthResponse(
        status="healthy" if all_healthy else "degraded",
        version=_settings.app_version,
        environment=_settings.environment,
        timestamp=datetime.now(UTC),
        dependencies=dependencies,
    )
    response.status_code = _code_http(corps.status)

    # Mettre en cache le résultat (TTL 5s)
    with suppress(Exception):
        await redis.setex(
            _READY_CACHE_KEY,
            _settings.health_cache_ttl,
            corps.model_dump_json(),
        )

    return corps

# GSIE API — Configuration
# Les valeurs sont lues depuis les variables d'environnement (.env)
# Aucun secret n'est commité (CON-008 souveraineté, global_rules security).

from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration globale de l'API GSIE.

    Toutes les valeurs sont surchargeables via variables d'environnement
    ou fichier .env (non commité).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GSIE_",
        extra="ignore",
    )

    # Application
    app_name: str = "GSIE API"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"]
    )
    # Limite taille corps de requête (bytes) — défaut 1 MiB (OWASP A04)
    max_request_body_size: int = 1_048_576

    # Rate limiting (OWASP A07 — slowapi)
    rate_limit_enabled: bool = True
    # Format slowapi : "count/period" — défaut 60 req/min par IP
    rate_limit_default: str = "60/minute"
    # Endpoints health/ready plus permissifs (monitoring)
    rate_limit_health: str = "300/minute"
    # Endpoints POST plus stricts (protection flood)
    rate_limit_evaluate: str = "30/minute"

    # PostgreSQL + PostGIS
    # Format : postgresql+asyncpg://user:pass@host:5432/dbname
    database_url: str = "postgresql+asyncpg://gsie:gsie_dev@localhost:5432/gsie"
    # Pool sizing : pool_size par worker Gunicorn (5 workers × 5 = 25 connexions max)
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_echo: bool = False
    db_pool_timeout: int = 30  # secondes

    # PgBouncer — statement_cache_size=0 requis (DEC-000019 ajustement P0)
    db_pgbouncer_mode: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 20
    # Timeouts Redis (secondes) — évite les requêtes bloquantes (résilience P0)
    redis_socket_timeout: float = 5.0
    redis_connect_timeout: float = 5.0
    # Cache TTL pour /ready (secondes) — évite de pinger DB+Redis à chaque requête
    health_cache_ttl: int = 5
    # Rate limit stocké dans Redis (DB 1) pour distribution entre workers
    # En développement/test, "memory://" est utilisé (pas de Redis requis)
    rate_limit_storage_url: str = "memory://"

    # WebSocket (ADR-007)
    ws_max_connections: int = 1000
    ws_heartbeat_interval: int = 30  # secondes
    ws_allowed_origins: list[str] = ["*"]  # CORS WS — restreindre en prod

    # Object Storage (ADR-006)
    object_storage_local_path: str = "./data/assets"
    object_storage_s3_endpoint: str | None = None
    object_storage_s3_bucket: str = "gsie-assets"

    # Auth — JWT RS256 (DEC-000019)
    jwt_algorithm: Literal["RS256"] = "RS256"
    jwt_issuer: str = "gsie-api"
    jwt_audience: str = "gsie-clients"
    jwt_access_token_expire_minutes: int = Field(default=15, ge=1, le=60)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1, le=30)
    jwt_private_key_path: str = "keys/private.pem"
    jwt_public_key_path: str = "keys/public.pem"
    # Dev login — jamais en production ; credentials via variables d'environnement
    auth_dev_login_enabled: bool = True
    auth_dev_username: str = "admin"
    auth_dev_password: str = ""

    # Moteur Evidence
    require_rust_backend: bool = False
    evidence_experimental_conflicts_enabled: bool = False

    # Observabilité — OpenTelemetry (DEC-000019)
    otel_enabled: bool = False
    otel_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "gsie-api"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Valide que la configuration est sûre en production."""
        if self.environment == "production":
            if self.debug:
                raise ValueError("debug must be False in production")
            if "gsie_dev" in self.database_url:
                raise ValueError("Default database password not allowed in production")
            if "*" in self.cors_origins:
                raise ValueError("Wildcard CORS origin not allowed in production")
            if any("localhost" in o for o in self.cors_origins):
                raise ValueError("localhost CORS origins not allowed in production")
            redis_password = urlparse(self.redis_url).password
            if not redis_password:
                raise ValueError("Redis without password not allowed in production")
            if self.rate_limit_storage_url == "memory://":
                raise ValueError("Distributed rate-limit storage required in production")
            if self.auth_dev_login_enabled:
                raise ValueError("Development login must be disabled in production")
            if not self.require_rust_backend:
                raise ValueError("Rust Evidence backend must be required in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Retourne un singleton Settings (cache pour éviter les relectures .env)."""
    return Settings()

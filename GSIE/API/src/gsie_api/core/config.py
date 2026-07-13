# GSIE API — Configuration
# Les valeurs sont lues depuis les variables d'environnement (.env)
# Aucun secret n'est commité (CON-008 souveraineté, global_rules security).

from functools import lru_cache

from pydantic import Field
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
    environment: str = Field(default="development", description="development|staging|production")
    debug: bool = False
    log_level: str = "INFO"

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"]
    )

    # PostgreSQL + PostGIS
    # Format : postgresql+asyncpg://user:pass@host:5432/dbname
    database_url: str = "postgresql+asyncpg://gsie:gsie_dev@localhost:5432/gsie"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_echo: bool = False

    # PgBouncer — statement_cache_size=0 requis (DEC-000019 ajustement P0)
    db_pgbouncer_mode: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # Auth — JWT RS256 (DEC-000019)
    jwt_algorithm: str = "RS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    jwt_private_key_path: str = "keys/private.pem"
    jwt_public_key_path: str = "keys/public.pem"

    # Observabilité — OpenTelemetry (DEC-000019)
    otel_enabled: bool = False
    otel_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "gsie-api"


@lru_cache
def get_settings() -> Settings:
    """Retourne un singleton Settings (cache pour éviter les relectures .env)."""
    return Settings()

"""Schemas Pydantic communs — pagination, erreurs, réponses standard."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PageParams(BaseModel):
    """Paramètres de pagination (global_rules — pas de listes non bornées)."""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée."""

    model_config = ConfigDict(extra="forbid")

    detail: str = Field(max_length=1000)
    error_code: str | None = Field(default=None, max_length=50)
    trace_id: str | None = Field(default=None, max_length=64)


class HealthResponse(BaseModel):
    """Réponse des endpoints health/ready."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(description="healthy|degraded|unhealthy")
    version: str
    environment: str
    timestamp: datetime
    dependencies: dict[str, str] = Field(
        default_factory=dict,
        description="État des dépendances (database, redis)",
    )


class EngineStatusResponse(BaseModel):
    """Réponse standardisée pour le statut d'un moteur."""

    model_config = ConfigDict(extra="forbid")

    engine: str = Field(description="Nom du moteur")
    status: str = Field(description="not_implemented|active|degraded")
    planned_week: int = Field(description="Semaine d'implémentation prévue")
    language: str = Field(description="Langage d'implémentation")


class EngineVersionResponse(BaseModel):
    """Réponse standardisée pour la version d'un moteur."""

    model_config = ConfigDict(extra="forbid")

    version: str
    backend: str

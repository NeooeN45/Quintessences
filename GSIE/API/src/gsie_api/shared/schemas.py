"""Schemas Pydantic communs — pagination, erreurs, réponses standard."""

from datetime import datetime

from pydantic import BaseModel, Field


class PageParams(BaseModel):
    """Paramètres de pagination (global_rules — pas de listes non bornées)."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée."""

    detail: str
    error_code: str | None = None
    trace_id: str | None = None


class HealthResponse(BaseModel):
    """Réponse des endpoints health/ready."""

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

    engine: str = Field(description="Nom du moteur")
    status: str = Field(description="not_implemented|active|degraded")
    planned_week: int = Field(description="Semaine d'implémentation prévue")
    language: str = Field(description="Langage d'implémentation")

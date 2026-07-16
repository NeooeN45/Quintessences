"""Schemas Pydantic génériques pour le CRUD resource (ADR-007).

DTOs pour le router générique /api/v1/resources.
Les champs spécifiques à chaque type sont validés dynamiquement.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResourceBase(BaseModel):
    """Base — champs communs à toutes les resources."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    gsie_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ResourceCreate(BaseModel):
    """Création d'une resource — type + champs spécifiques en JSON."""

    type: str = Field(..., description="Type de resource (ex. assertion, observation, concept)")
    gsie_id: str | None = Field(None, description="Identifiant lisible optionnel")
    data: dict[str, Any] = Field(..., description="Champs spécifiques au type")


class ResourceUpdate(BaseModel):
    """Mise à jour d'une resource — champs modifiés en JSON."""

    data: dict[str, Any] = Field(..., description="Champs modifiés")
    justification: str = Field(..., description="Justification de la révision (CON-010)")


class ResourceRead(ResourceBase):
    """Resource lue — inclut les champs spécifiques."""

    metadata_json: dict[str, Any] = Field(default_factory=dict)
    data: dict[str, Any] = Field(default_factory=dict, description="Champs spécifiques au type")


class ResourceListResponse(BaseModel):
    """Réponse paginée — liste de resources."""

    items: list[ResourceRead]
    total: int
    page: int
    size: int
    type_filter: str | None = None


class RevisionRead(BaseModel):
    """Révision d'une resource (Temporal Engine)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    target_id: UUID
    version: int
    author_id: UUID | None = None
    justification: str
    valid_time_start: datetime
    valid_time_end: datetime | None = None
    transaction_time: datetime
    created_at: datetime


class SnapshotRead(BaseModel):
    """Snapshot d'une resource (Temporal Engine)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    target_id: UUID
    revision_id: int | None = None
    captured_at: datetime
    serialized_state: dict[str, Any]
    checksum: str


class ResourceTypesResponse(BaseModel):
    """Liste des types de resources disponibles."""

    types: list[str]
    count: int

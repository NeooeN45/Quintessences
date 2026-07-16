"""Modèles SQLAlchemy — base racine resource (ADR-001) + mixins.

Architecture :
- Table racine `resource` (ADR-001) — tout type hérite de resource
- Class-table inheritance : chaque type a sa propre table avec PK = FK vers resource.id
- TimestampMixin : created_at + updated_at avec timezone
- RevisionMixin : support du Temporal Engine (Revision + Snapshot)

Le registry RESOURCE_TYPES mappe type_name → modèle pour le CRUD générique.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base déclarative SQLAlchemy 2.0 pour tous les modèles."""


class TimestampMixin:
    """Mixin : created_at + updated_at avec timezone."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ResourceModel(Base, TimestampMixin):
    """Table racine resource (ADR-001).

    Toute ressource du métamodèle v6.2 a une ligne ici.
    Les tables spécifiques (assertion, observation, concept, etc.)
    référencent resource.id comme PK et FK.
    """

    __tablename__ = "resource"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    gsie_id: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    # Soft delete (CON-010 — jamais DELETE physique)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


# Registry — mappe type_name → modèle SQLAlchemy pour le CRUD générique
RESOURCE_TYPES: dict[str, type[Base]] = {}


def register_type(type_name: str) -> Any:
    """Décorateur — enregistre un modèle dans le registry par type_name.

    Usage :
        @register_type("assertion")
        class AssertionModel(ResourceBase):
            ...
    """

    def decorator(cls: type[Base]) -> type[Base]:
        RESOURCE_TYPES[type_name] = cls
        return cls

    return decorator

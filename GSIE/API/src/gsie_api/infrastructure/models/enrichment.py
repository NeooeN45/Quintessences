"""Modèles d'enrichissement — images, descriptions multilingues, progression,
résultats de validation.

Tables satellites attachées à une `resource` existante (pas des types du
métamodèle — pas de `register_type`) :

- `entity_image` : images d'espèces (Wikimedia Commons, etc.) — remplace
  le stockage dans `metadata_json->primary_image`. Permet multi-images,
  validation de URLs, index sur `entity_id`. Introduite par la migration
  `20260801_0027` (audit qualité base du 2026-08-01).
- `entity_description` : descriptions multilingues (Wikipédia EN/FR,
  etc.) — remplace `metadata_json->wikipedia_extract`. Migration 0027.
- `ingestion_progress` : checkpoint de progression pour reprise
  automatique après crash du pipeline d'ingestion. Migration 0027.
- `validation_result` : résultat de validation persisté — alimentation
  du Learning Engine (RFC-0028, migration 0028). Seuls les résultats
  `bloque` et `partiellement_valide` sont persistés ; la FK
  `requete_origine` pointe vers la resource validée (diagnostic ou
  recommandation), pas vers une resource fantôme.

Ces tables ne sont pas des types du métamodèle (pas de `register_type`) :
ce sont des attributs multi-valués d'une `resource`, pas des ressources à
part entière. Elles ont leur propre PK UUID et FK vers `resource.id`.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin


class EntityImageModel(Base, TimestampMixin):
    """Image d'une entity (taxon) — Wikimedia Commons, etc.

    Plusieurs images par entity possibles ; une seule `is_primary=true`
    (contrainte unique partielle `idx_entity_image_entity_primary`).
    """

    __tablename__ = "entity_image"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    license: Mapped[str | None] = mapped_column(String(200), nullable=True)
    photographer: Mapped[str | None] = mapped_column(String(300), nullable=True)
    page_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="Wikimedia Commons")
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Index unique partiel : une seule image primaire par entity.
        Index(
            "idx_entity_image_entity_primary",
            "entity_id",
            unique=True,
            postgresql_where=text("is_primary = true"),
        ),
    )


class EntityDescriptionModel(Base, TimestampMixin):
    """Description multilingue d'une entity (taxon).

    Plusieurs descriptions par entity possibles (une par langue × source).
    Contrainte unique `(entity_id, language, source)`.
    """

    __tablename__ = "entity_description"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    quality: Mapped[str | None] = mapped_column(String(20), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "entity_id",
            "language",
            "source",
            name="idx_entity_description_entity_lang_src",
        ),
    )


class IngestionProgressModel(Base):
    """Checkpoint de progression d'un pipeline d'ingestion.

    Permet la reprise automatique après crash : le pipeline lit
    `last_offset` au démarrage et reprend où il s'est arrêté.
    """

    __tablename__ = "ingestion_progress"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    pipeline: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    last_offset: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class ValidationResultModel(Base, TimestampMixin):
    """Résultat de validation persisté — alimentation du Learning Engine.

    Seuls les résultats `bloque` et `partiellement_valide` sont persistés
    (les résultats `valide` ne portent pas d'information d'apprentissage).
    Le Learning Engine consomme ces lignes pour détecter des patterns
    de blocage récurrents (RFC-0028, VALIDATION_ENGINE.md §3).
    """

    __tablename__ = "validation_result"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    requete_origine: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    statut: Mapped[str] = mapped_column(String(30), nullable=False)
    type_sortie: Mapped[str] = mapped_column(String(30), nullable=False)
    controles: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    causes_blocage: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    date_validation: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_validation_result_statut", "statut"),
        Index("idx_validation_result_date", "date_validation"),
    )

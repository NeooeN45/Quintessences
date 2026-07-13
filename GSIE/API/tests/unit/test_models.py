"""Tests unitaires — modèles SQLAlchemy (infrastructure/models.py)."""

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models import Base, TimestampMixin


def should_be_declarative_base_when_imported():
    """Base doit être une sous-classe de DeclarativeBase."""
    from sqlalchemy.orm import DeclarativeBase
    assert issubclass(Base, DeclarativeBase)


def should_have_created_at_when_timestamp_mixin_used():
    """TimestampMixin doit définir created_at avec timezone."""
    assert "created_at" in TimestampMixin.__dict__ or "created_at" in dir(TimestampMixin)


def should_have_updated_at_when_timestamp_mixin_used():
    """TimestampMixin doit définir updated_at avec timezone."""
    assert "updated_at" in TimestampMixin.__dict__ or "updated_at" in dir(TimestampMixin)


def should_create_model_with_timestamps_when_mixin_applied():
    """Un modèle utilisant TimestampMixin doit avoir created_at et updated_at."""

    class TestModel(TimestampMixin, Base):
        __tablename__ = "test_model"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(100))

    # Vérifier que les colonnes sont présentes dans le modèle
    columns = {c.name for c in TestModel.__table__.columns}
    assert "id" in columns
    assert "name" in columns
    assert "created_at" in columns
    assert "updated_at" in columns

    # Vérifier que created_at a un server_default
    created_at_col = TestModel.__table__.c.created_at
    assert created_at_col.server_default is not None

    # Vérifier que updated_at a onupdate
    updated_at_col = TestModel.__table__.c.updated_at
    assert updated_at_col.onupdate is not None

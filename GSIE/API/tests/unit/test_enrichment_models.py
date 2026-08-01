"""Tests unitaires — modèles d'enrichissement (entity_image, entity_description).

Vérifie que les modèles SQLAlchemy déclarés dans `enrichment.py` sont
correctement enregistrés dans `Base.metadata` et que leurs contraintes
(index, FK, unicité) sont présentes.
"""

from __future__ import annotations

from gsie_api.infrastructure.models import Base


def test_entity_image_model_is_registered_in_metadata() -> None:
    """La table entity_image doit être dans Base.metadata."""
    assert "entity_image" in Base.metadata.tables


def test_entity_description_model_is_registered_in_metadata() -> None:
    """La table entity_description doit être dans Base.metadata."""
    assert "entity_description" in Base.metadata.tables


def test_ingestion_progress_model_is_registered_in_metadata() -> None:
    """La table ingestion_progress doit être dans Base.metadata."""
    assert "ingestion_progress" in Base.metadata.tables


def test_entity_image_has_index_on_entity_id() -> None:
    """entity_image doit avoir un index sur entity_id (FK fréquemment requêtée)."""
    table = Base.metadata.tables["entity_image"]
    index_columns = [tuple(col.name for col in index.columns) for index in table.indexes]
    assert ("entity_id",) in index_columns


def test_entity_description_has_index_on_entity_id() -> None:
    """entity_description doit avoir un index sur entity_id."""
    table = Base.metadata.tables["entity_description"]
    index_columns = [tuple(col.name for col in index.columns) for index in table.indexes]
    assert ("entity_id",) in index_columns


def test_ingestion_progress_has_unique_constraint_on_pipeline() -> None:
    """ingestion_progress.pipeline doit être unique (un checkpoint par pipeline)."""
    table = Base.metadata.tables["ingestion_progress"]
    assert table.columns["pipeline"].unique is True


def test_entity_image_has_fk_to_resource_cascade() -> None:
    """entity_image.entity_id doit être une FK vers resource.id avec ON DELETE CASCADE."""
    table = Base.metadata.tables["entity_image"]
    fk = list(table.foreign_keys)[0]
    assert fk.column.name == "id"
    assert fk.column.table.name == "resource"
    assert fk.ondelete == "CASCADE"


def test_entity_description_has_fk_to_resource_cascade() -> None:
    """entity_description.entity_id doit être une FK vers resource.id avec ON DELETE CASCADE."""
    table = Base.metadata.tables["entity_description"]
    fk = list(table.foreign_keys)[0]
    assert fk.column.name == "id"
    assert fk.column.table.name == "resource"
    assert fk.ondelete == "CASCADE"


def test_entity_image_has_is_primary_column() -> None:
    """entity_image doit avoir une colonne is_primary (booléen)."""
    table = Base.metadata.tables["entity_image"]
    assert "is_primary" in table.columns
    assert table.columns["is_primary"].type.python_type is bool


def test_entity_description_has_quality_column() -> None:
    """entity_description doit avoir une colonne quality (varchar, nullable)."""
    table = Base.metadata.tables["entity_description"]
    assert "quality" in table.columns
    assert table.columns["quality"].nullable is True


def test_ingestion_progress_has_status_and_offset() -> None:
    """ingestion_progress doit avoir status et last_offset."""
    table = Base.metadata.tables["ingestion_progress"]
    assert "status" in table.columns
    assert "last_offset" in table.columns
    assert table.columns["last_offset"].type.python_type is int

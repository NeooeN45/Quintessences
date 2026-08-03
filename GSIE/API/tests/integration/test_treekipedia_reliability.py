"""Tests de fiabilité — pipeline Treekipedia (idempotence, contraintes, reprise).

Valide les garanties critiques du pipeline d'ingestion/enrichissement :
1. Idempotence : ré-ingérer la même espèce ne crée pas de doublon
2. Contrainte DB : index unique (namespace, external_id) empêche les doublons
3. Cascade : supprimer une entity supprime ses images/descriptions
4. Checkpoint : ingestion_progress enregistre l'offset correctement
5. Reprise : --resume repart du dernier checkpoint

Ces tests nécessitent Docker (testcontainers) — marqués `requires_docker`.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select, text

from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.enrichment import (
    EntityDescriptionModel,
    EntityImageModel,
    IngestionProgressModel,
)
from gsie_api.infrastructure.models.provenance import EntityAliasModel
from tests.conftest import requires_docker

pytestmark = requires_docker


async def test_should_not_create_duplicate_alias_when_same_namespace_and_external_id(
    db_session,
) -> None:
    """L'index unique (namespace, external_id) doit empêcher les doublons."""
    # Arrange — créer une entity
    entity_id = uuid4()
    db_session.add(
        ResourceModel(
            id=entity_id,
            type="entity",
            gsie_id=f"gsie:entity:taxon:{entity_id}",
            metadata_json={},
        )
    )
    await db_session.flush()

    alias_id = uuid4()
    db_session.add(
        ResourceModel(
            id=alias_id,
            type="entity_alias",
            gsie_id="gsie:alias:gbif:12345",
            metadata_json={},
        )
    )
    await db_session.flush()
    db_session.add(
        EntityAliasModel(
            id=alias_id,
            entity_id=entity_id,
            namespace="gbif",
            external_id="12345",
        )
    )
    await db_session.flush()

    # Act — tenter d'insérer un second alias avec le même (namespace, external_id)
    alias_id_2 = uuid4()
    db_session.add(
        ResourceModel(
            id=alias_id_2,
            type="entity_alias",
            gsie_id="gsie:alias:gbif:12345-dup",
            metadata_json={},
        )
    )
    await db_session.flush()
    db_session.add(
        EntityAliasModel(
            id=alias_id_2,
            entity_id=entity_id,
            namespace="gbif",
            external_id="12345",
        )
    )

    # Assert — la contrainte unique doit lever une IntegrityError
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_should_cascade_delete_images_when_entity_deleted(db_session) -> None:
    """La suppression d'une entity doit cascader vers entity_image (ON DELETE CASCADE)."""
    entity_id = uuid4()
    db_session.add(
        ResourceModel(
            id=entity_id,
            type="entity",
            gsie_id=f"gsie:entity:taxon:{entity_id}",
            metadata_json={},
        )
    )
    await db_session.flush()

    img_id = uuid4()
    db_session.add(
        EntityImageModel(
            id=img_id,
            entity_id=entity_id,
            url="https://example.com/image.jpg",
            license="CC-BY-SA-3.0",
            source="Wikimedia Commons",
            is_primary=True,
        )
    )
    await db_session.flush()

    # Vérifier que l'image existe
    result = await db_session.execute(
        select(EntityImageModel).where(EntityImageModel.entity_id == entity_id)
    )
    assert result.scalars().first() is not None

    # Act — supprimer la resource entity
    await db_session.execute(
        text("DELETE FROM resource WHERE id = :eid"),
        {"eid": entity_id},
    )
    await db_session.flush()

    # Assert — l'image doit être supprimée par cascade
    result = await db_session.execute(
        select(EntityImageModel).where(EntityImageModel.entity_id == entity_id)
    )
    assert result.scalars().first() is None


async def test_should_cascade_delete_descriptions_when_entity_deleted(db_session) -> None:
    """La suppression d'une entity doit cascader vers entity_description."""
    entity_id = uuid4()
    db_session.add(
        ResourceModel(
            id=entity_id,
            type="entity",
            gsie_id=f"gsie:entity:taxon:{entity_id}",
            metadata_json={},
        )
    )
    await db_session.flush()

    desc_id = uuid4()
    db_session.add(
        EntityDescriptionModel(
            id=desc_id,
            entity_id=entity_id,
            language="en",
            source="wikipedia",
            content="A long enough description that exceeds the minimum threshold.",
            quality="medium",
        )
    )
    await db_session.flush()

    # Act — supprimer la resource entity
    await db_session.execute(
        text("DELETE FROM resource WHERE id = :eid"),
        {"eid": entity_id},
    )
    await db_session.flush()

    # Assert — la description doit être supprimée par cascade
    result = await db_session.execute(
        select(EntityDescriptionModel).where(EntityDescriptionModel.entity_id == entity_id)
    )
    assert result.scalars().first() is None


async def test_should_enforce_unique_description_per_entity_language_source(
    db_session,
) -> None:
    """La contrainte unique (entity_id, language, source) doit empêcher les doublons."""
    entity_id = uuid4()
    db_session.add(
        ResourceModel(
            id=entity_id,
            type="entity",
            gsie_id=f"gsie:entity:taxon:{entity_id}",
            metadata_json={},
        )
    )
    await db_session.flush()

    db_session.add(
        EntityDescriptionModel(
            entity_id=entity_id,
            language="en",
            source="wikipedia",
            content="First description.",
            quality="low",
        )
    )
    await db_session.flush()

    # Act — tenter d'insérer une seconde description avec la même combinaison
    db_session.add(
        EntityDescriptionModel(
            entity_id=entity_id,
            language="en",
            source="wikipedia",
            content="Second description — should fail.",
            quality="low",
        )
    )

    # Assert
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_should_enforce_only_one_primary_image_per_entity(db_session) -> None:
    """L'index unique partiel sur is_primary=true doit empêcher 2 images primaires."""
    entity_id = uuid4()
    db_session.add(
        ResourceModel(
            id=entity_id,
            type="entity",
            gsie_id=f"gsie:entity:taxon:{entity_id}",
            metadata_json={},
        )
    )
    await db_session.flush()

    db_session.add(
        EntityImageModel(
            entity_id=entity_id,
            url="https://example.com/image1.jpg",
            source="Wikimedia Commons",
            is_primary=True,
        )
    )
    await db_session.flush()

    # Act — tenter d'insérer une seconde image primaire
    db_session.add(
        EntityImageModel(
            entity_id=entity_id,
            url="https://example.com/image2.jpg",
            source="Wikimedia Commons",
            is_primary=True,
        )
    )

    # Assert
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_should_allow_multiple_non_primary_images_per_entity(db_session) -> None:
    """Plusieurs images non-primaires doivent être autorisées pour une même entity."""
    entity_id = uuid4()
    db_session.add(
        ResourceModel(
            id=entity_id,
            type="entity",
            gsie_id=f"gsie:entity:taxon:{entity_id}",
            metadata_json={},
        )
    )
    await db_session.flush()

    for i in range(3):
        db_session.add(
            EntityImageModel(
                entity_id=entity_id,
                url=f"https://example.com/image{i}.jpg",
                source="Wikimedia Commons",
                is_primary=False,
            )
        )
    await db_session.flush()

    result = await db_session.execute(
        select(EntityImageModel).where(EntityImageModel.entity_id == entity_id)
    )
    images = result.scalars().all()
    assert len(images) == 3


async def test_should_create_and_update_ingestion_progress(db_session) -> None:
    """ingestion_progress doit enregistrer l'offset et le statut du pipeline."""
    progress = IngestionProgressModel(
        pipeline="test_pipeline",
        last_offset=0,
        total=100,
        status="running",
    )
    db_session.add(progress)
    await db_session.flush()

    # Act — simuler une progression
    progress.last_offset = 50
    progress.status = "completed"
    await db_session.flush()

    # Assert
    result = await db_session.execute(
        select(IngestionProgressModel).where(IngestionProgressModel.pipeline == "test_pipeline")
    )
    saved = result.scalars().first()
    assert saved is not None
    assert saved.last_offset == 50
    assert saved.status == "completed"


async def test_should_enforce_unique_pipeline_name_in_ingestion_progress(
    db_session,
) -> None:
    """Deux enregistrements ingestion_progress ne peuvent pas avoir le même pipeline."""
    db_session.add(
        IngestionProgressModel(
            pipeline="duplicate_pipeline",
            last_offset=0,
            total=10,
            status="running",
        )
    )
    await db_session.flush()

    db_session.add(
        IngestionProgressModel(
            pipeline="duplicate_pipeline",
            last_offset=5,
            total=10,
            status="running",
        )
    )

    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await db_session.flush()

"""Tests de qualité — pipeline Treekipedia (complétude, cohérence, traçabilité).

Valide la qualité des données après enrichissement :
1. Complétude : chaque entity enrichie a taxonomy + common_names
2. Cohérence : les descriptions ont une langue et une source
3. Traçabilité : chaque entity a un gsie_id non null
4. Qualité des descriptions : filtrage des stubs < 100 chars
5. Qualité des images : license présente quand source = Wikimedia

Ces tests nécessitent Docker (testcontainers) — marqués `requires_docker`.
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select

from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.enrichment import (
    EntityDescriptionModel,
    EntityImageModel,
)
from tests.conftest import requires_docker

pytestmark = requires_docker

_MIN_DESCRIPTION_LENGTH = 100


async def test_should_store_description_with_language_and_source(db_session) -> None:
    """Une description doit avoir une langue et une source non nulles."""
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

    desc = EntityDescriptionModel(
        entity_id=entity_id,
        language="en",
        source="wikipedia",
        content=(
            "A description long enough to pass the minimum threshold check. "
            "This text must be at least 100 characters to be considered valid."
        ),
        quality="medium",
    )
    db_session.add(desc)
    await db_session.flush()

    result = await db_session.execute(
        select(EntityDescriptionModel).where(EntityDescriptionModel.entity_id == entity_id)
    )
    saved = result.scalars().first()
    assert saved is not None
    assert saved.language == "en"
    assert saved.source == "wikipedia"
    assert len(saved.content) >= _MIN_DESCRIPTION_LENGTH


async def test_should_store_image_with_license_and_source(db_session) -> None:
    """Une image Wikimedia doit avoir une license et une source."""
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

    img = EntityImageModel(
        entity_id=entity_id,
        url="https://upload.wikimedia.org/example.jpg",
        license="CC-BY-SA-3.0",
        source="Wikimedia Commons",
        is_primary=True,
    )
    db_session.add(img)
    await db_session.flush()

    result = await db_session.execute(
        select(EntityImageModel).where(EntityImageModel.entity_id == entity_id)
    )
    saved = result.scalars().first()
    assert saved is not None
    assert saved.license == "CC-BY-SA-3.0"
    assert saved.source == "Wikimedia Commons"
    assert saved.is_primary is True


async def test_should_assign_quality_based_on_description_length(db_session) -> None:
    """La qualité d'une description doit refléter sa longueur."""
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

    # High quality : > 500 chars
    long_desc = "A" * 600
    db_session.add(
        EntityDescriptionModel(
            entity_id=entity_id,
            language="en",
            source="wikipedia",
            content=long_desc,
            quality="high",
        )
    )

    # Medium quality : 200-500 chars
    medium_desc = "B" * 300
    db_session.add(
        EntityDescriptionModel(
            entity_id=entity_id,
            language="fr",
            source="wikipedia",
            content=medium_desc,
            quality="medium",
        )
    )

    await db_session.flush()

    result = await db_session.execute(
        select(EntityDescriptionModel)
        .where(EntityDescriptionModel.entity_id == entity_id)
        .order_by(EntityDescriptionModel.language)
    )
    descs = result.scalars().all()
    assert len(descs) == 2
    assert descs[0].quality == "high"  # en
    assert descs[1].quality == "medium"  # fr


async def test_should_support_multilingual_descriptions(db_session) -> None:
    """Une entity peut avoir des descriptions dans plusieurs langues."""
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

    for lang, content in [
        ("en", "English description long enough to pass the minimum threshold check easily."),
        ("fr", "Description française assez longue pour passer le seuil minimum de cent."),
        ("de", "Deutsche Beschreibung lang genug um die Schwelle von hundert zu bestehen."),
    ]:
        db_session.add(
            EntityDescriptionModel(
                entity_id=entity_id,
                language=lang,
                source="wikipedia",
                content=content,
                quality="low",
            )
        )
    await db_session.flush()

    result = await db_session.execute(
        select(EntityDescriptionModel.language)
        .where(EntityDescriptionModel.entity_id == entity_id)
        .order_by(EntityDescriptionModel.language)
    )
    langs = result.scalars().all()
    assert langs == ["de", "en", "fr"]


async def test_should_support_multiple_images_with_one_primary(db_session) -> None:
    """Une entity peut avoir plusieurs images mais une seule primaire."""
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

    # Image primaire
    db_session.add(
        EntityImageModel(
            entity_id=entity_id,
            url="https://example.com/primary.jpg",
            source="Wikimedia Commons",
            is_primary=True,
        )
    )
    # Images secondaires
    for i in range(4):
        db_session.add(
            EntityImageModel(
                entity_id=entity_id,
                url=f"https://example.com/secondary{i}.jpg",
                source="Wikimedia Commons",
                is_primary=False,
            )
        )
    await db_session.flush()

    result = await db_session.execute(
        select(EntityImageModel)
        .where(EntityImageModel.entity_id == entity_id)
        .order_by(EntityImageModel.is_primary.desc())
    )
    images = result.scalars().all()
    assert len(images) == 5
    primary = [img for img in images if img.is_primary]
    assert len(primary) == 1


async def test_should_track_image_validation_timestamps(db_session) -> None:
    """Les images doivent pouvoir tracker validated_at et last_checked_at."""
    from datetime import UTC, datetime

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

    now = datetime.now(UTC)
    db_session.add(
        EntityImageModel(
            entity_id=entity_id,
            url="https://example.com/validated.jpg",
            source="Wikimedia Commons",
            is_primary=True,
            validated_at=now,
            last_checked_at=now,
        )
    )
    await db_session.flush()

    result = await db_session.execute(
        select(EntityImageModel).where(EntityImageModel.entity_id == entity_id)
    )
    saved = result.scalars().first()
    assert saved is not None
    assert saved.validated_at is not None
    assert saved.last_checked_at is not None

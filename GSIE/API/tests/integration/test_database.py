"""Tests d'intégration — base PostgreSQL/PostGIS + Redis via testcontainers.

Ces tests nécessitent Docker. Ils sont ignorés si Docker n'est pas accessible.

Couverture :
- Connexion PostgreSQL + PostGIS (extension vérifiée)
- Création du schéma complet (76 types métamodèle v6.2)
- CRUD resource : insert, read, update, soft delete (CON-010)
- PostGIS : Geometry avec SRID 2154 (Lambert-93)
- JSONB : metadata_json stocké et requêté
- Redis : ping + set/get + Pub/Sub
"""

from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.redis import RedisContainer

from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.redis_client import get_redis
from tests.conftest import requires_docker

pytestmark = requires_docker


@pytest.fixture(scope="module")
def redis_url():
    """Lance un conteneur Redis et retourne son URL."""
    with RedisContainer(image="redis:7-alpine") as redis:
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(6379)
        yield f"redis://{host}:{port}/0"


# --- Tests connexion ----------------------------------------------------------


@pytest.mark.asyncio
async def should_connect_to_postgres_and_verify_postgis(postgres_url: str):
    """La connexion PostgreSQL + PostGIS fonctionne."""
    engine = create_async_engine(postgres_url, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT PostGIS_Full_Version()"))
            version = result.scalar_one()
            assert version is not None
            assert "postgis" in version.lower()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def should_connect_to_redis_and_ping(redis_url: str):
    """La connexion Redis fonctionne."""
    import redis.asyncio as redis

    original_pool = None
    client = None
    try:
        from gsie_api.infrastructure import redis_client as redis_module

        original_pool = redis_module.redis_pool
        redis_module.redis_pool = redis.ConnectionPool.from_url(
            redis_url,
            decode_responses=True,
        )
        client = await get_redis()
        pong = await client.ping()
        assert pong is True
    finally:
        if original_pool is not None:
            redis_module.redis_pool = original_pool
        if client is not None:
            await client.aclose()


# --- Tests CRUD resource (PostgreSQL réel) ------------------------------------


@pytest.mark.asyncio
async def should_create_and_read_resource_on_postgres(db_session: AsyncSession):
    """CRUD de base — créer et lire une resource sur PostgreSQL réel."""
    resource = ResourceModel(
        id=uuid4(),
        type="entity",
        gsie_id="GSIE-TEST-000001",
        metadata_json={"domain": "forestry", "source": "integration-test"},
    )
    db_session.add(resource)
    await db_session.commit()

    # Recharger depuis la DB
    from sqlalchemy import select

    result = await db_session.execute(
        select(ResourceModel).where(ResourceModel.gsie_id == "GSIE-TEST-000001")
    )
    fetched = result.scalar_one()
    assert fetched.type == "entity"
    assert fetched.metadata_json["domain"] == "forestry"
    assert fetched.deleted_at is None


@pytest.mark.asyncio
async def should_soft_delete_resource_on_postgres(db_session: AsyncSession):
    """Soft delete (CON-010) — deleted_at setté, pas de DELETE physique."""
    from datetime import UTC, datetime

    resource_id = uuid4()
    resource = ResourceModel(
        id=resource_id,
        type="concept",
        gsie_id="GSIE-TEST-000002",
        metadata_json={},
    )
    db_session.add(resource)
    await db_session.commit()

    # Soft delete
    from sqlalchemy import select

    result = await db_session.execute(select(ResourceModel).where(ResourceModel.id == resource_id))
    fetched = result.scalar_one()
    fetched.deleted_at = datetime.now(UTC)
    await db_session.commit()

    # Vérifier — la ligne existe toujours
    result2 = await db_session.execute(select(ResourceModel).where(ResourceModel.id == resource_id))
    fetched2 = result2.scalar_one()
    assert fetched2.deleted_at is not None


@pytest.mark.asyncio
async def should_query_jsonb_metadata_on_postgres(db_session: AsyncSession):
    """JSONB — requête sur metadata_json avec opérateur PostgreSQL ->>."""
    resource = ResourceModel(
        id=uuid4(),
        type="observation",
        gsie_id="GSIE-TEST-000003",
        metadata_json={"domain": "botanical", "essence": "chene_sessile"},
    )
    db_session.add(resource)
    await db_session.commit()

    # Requête JSONB — opérateur ->> pour extraire une clé en texte
    result = await db_session.execute(
        text("SELECT gsie_id FROM resource WHERE metadata_json->>'essence' = :essence"),
        {"essence": "chene_sessile"},
    )
    row = result.scalar_one()
    assert row == "GSIE-TEST-000003"


# --- Tests PostGIS Geometry ---------------------------------------------------


@pytest.mark.asyncio
async def should_create_place_with_geometry_on_postgres(db_session: AsyncSession):
    """PostGIS — créer un Place avec Geometry SRID 2154 (Lambert-93)."""
    from gsie_api.infrastructure.models.spatial_temporal import PlaceModel

    resource_id = uuid4()
    # Créer la resource racine d'abord
    resource = ResourceModel(
        id=resource_id,
        type="place",
        gsie_id="GSIE-TEST-PLACE-001",
        metadata_json={"label": "Landiras"},
    )
    db_session.add(resource)
    await db_session.flush()

    # Créer le Place avec un point en Lambert-93 (SRID 2154)
    # Landiras approx : X=425000, Y=6390000 (zone de test Ignis)
    place = PlaceModel(
        id=resource_id,
        geometry="SRID=2154;POINT(425000 6390000)",
        srid=2154,
        label="Landiras",
        area_m2=15000.0,
    )
    db_session.add(place)
    await db_session.commit()

    # Vérifier — requête ST_AsText pour lire la géométrie
    result = await db_session.execute(
        text("SELECT ST_AsText(geometry), ST_SRID(geometry), label FROM place WHERE id = :rid"),
        {"rid": str(resource_id)},
    )
    row = result.one()
    assert "POINT" in row[0]
    assert row[1] == 2154
    assert row[2] == "Landiras"


@pytest.mark.asyncio
async def should_query_place_within_distance_on_postgres(db_session: AsyncSession):
    """PostGIS — requête spatiale ST_DWithin pour trouver les places proches."""
    from gsie_api.infrastructure.models.spatial_temporal import PlaceModel

    # Créer deux places proches en Lambert-93
    for i, (x, y, label) in enumerate(
        [
            (425000, 6390000, "Landiras"),
            (425100, 6390100, "Landiras_Nord"),
            (500000, 6400000, "Loin"),
        ],
        start=1,
    ):
        rid = uuid4()
        resource = ResourceModel(
            id=rid,
            type="place",
            gsie_id=f"GSIE-TEST-PLACE-{i:03d}",
            metadata_json={},
        )
        db_session.add(resource)
        await db_session.flush()
        place = PlaceModel(
            id=rid,
            geometry=f"SRID=2154;POINT({x} {y})",
            srid=2154,
            label=label,
        )
        db_session.add(place)
    await db_session.commit()

    # Requête ST_DWithin — places dans un rayon de 200m autour de Landiras
    result = await db_session.execute(
        text(
            "SELECT label FROM place "
            "WHERE ST_DWithin(geometry, "
            "ST_SetSRID(ST_MakePoint(425000, 6390000), 2154), 200)"
        )
    )
    labels = [row[0] for row in result.all()]
    assert "Landiras" in labels
    assert "Landiras_Nord" in labels
    assert "Loin" not in labels


# --- Tests Redis avancés ------------------------------------------------------


@pytest.mark.asyncio
async def should_set_and_get_redis_key(redis_url: str):
    """Redis — set/get d'une clé."""
    import redis.asyncio as redis

    client = redis.from_url(redis_url, decode_responses=True)
    try:
        await client.set("gsie:test:key1", "value1", ex=60)
        value = await client.get("gsie:test:key1")
        assert value == "value1"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def should_publish_and_subscribe_redis(redis_url: str):
    """Redis — Pub/Sub (utilisé par le WebSocket fan-out)."""
    import redis.asyncio as redis

    client = redis.from_url(redis_url, decode_responses=True)
    try:
        # Publier un message sur le canal de test
        received: list[str] = []
        pubsub = client.pubsub()
        await pubsub.subscribe("gsie:test:channel")

        # Publier
        await client.publish("gsie:test:channel", "hello-gsie")

        # Lire le message (avec un petit délai pour le Pub/Sub)
        import asyncio

        await asyncio.sleep(0.1)
        message = await pubsub.get_message(timeout=1.0)
        while message is not None:
            if message["type"] == "message":
                received.append(message["data"])
            message = await pubsub.get_message(timeout=1.0)

        assert "hello-gsie" in received
        await pubsub.unsubscribe("gsie:test:channel")
    finally:
        await client.aclose()

"""Tests unitaires — ResourceService (CRUD, mass-assignment, append-only, soft-delete).

Utilise SQLite in-memory (aiosqlite) pour tester le service sans Docker.
Les types UUID/JSONB/PostGIS sont adaptés pour SQLite via @compiles.
"""

from datetime import datetime, UTC
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import JSON, String, event, func, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

try:
    from geoalchemy2 import Geometry as _GeometryType
except ImportError:
    _GeometryType = None  # type: ignore

from gsie_api.infrastructure.models import Base, ResourceModel
from gsie_api.infrastructure.models.temporal_engine import RevisionModel
from gsie_api.resources.schemas import ResourceCreate, ResourceUpdate
from gsie_api.resources.service import ResourceService


# --- Adaptateurs de types pour SQLite ----------------------------------------

@compiles(JSONB, "sqlite")
def _jsonb_to_sqlite(element: Any, compiler: Any, **kw: Any) -> str:
    """JSONB → JSON en SQLite."""
    return "JSON"


if _GeometryType is not None:
    @compiles(_GeometryType, "sqlite")
    def _geometry_to_sqlite(element: Any, compiler: Any, **kw: Any) -> str:
        """Geometry → TEXT (WKT) en SQLite."""
        return "TEXT"


@pytest.fixture
async def session():
    """Session SQLite in-memory avec schéma créé.

    Les types PostgreSQL (JSONB, Geometry) sont adaptés via @compiles.
    Les server_default problématiques (func.text('...::jsonb'), "now()" string)
    sont remplacés par des équivalents SQLite compatibles.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Patch des server_default incompatibles SQLite (restaurés après les tests)
    from sqlalchemy.sql.schema import DefaultClause
    replaced: list[tuple[Any, str, Any]] = []
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if col.server_default is not None:
                sd = col.server_default
                sd_arg = getattr(sd, "arg", sd)
                # "now()" string → DefaultClause(func.now()) (compatible SQLite)
                if isinstance(sd_arg, str) and sd_arg == "now()":
                    replaced.append((col, "server_default", col.server_default))
                    col.server_default = DefaultClause(func.now())
                # func.text('...::jsonb') → DefaultClause("'{}'") (cast PG non supporté)
                elif not isinstance(sd_arg, str) and getattr(sd_arg, "name", "") == "text":
                    replaced.append((col, "server_default", col.server_default))
                    col.server_default = DefaultClause("'{}'")
            # Désactiver onupdate=func.now() (déclenche lazy load en SQLite async)
            if col.onupdate is not None:
                replaced.append((col, "onupdate", col.onupdate))
                col.onupdate = None

    async with engine.begin() as conn:
        # Exclure les tables avec Geometry (GeoAlchemy2 ajoute des DDL PostGIS)
        from geoalchemy2 import Geometry
        tables_to_create = [
            t for t in Base.metadata.sorted_tables
            if not any(isinstance(c.type, Geometry) for c in t.columns)
        ]
        await conn.run_sync(Base.metadata.create_all, tables=tables_to_create)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as s:
        yield s

    # Restaurer les server_default originaux
    for col, attr_name, original in replaced:
        setattr(col, attr_name, original)

    await engine.dispose()


class TestMassAssignmentProtection:
    """Tests de la protection mass-assignment (OWASP A01)."""

    @pytest.mark.asyncio
    async def test_should_filter_forbidden_fields_on_create(self, session: AsyncSession) -> None:
        """Les champs id, created_at, updated_at, deleted_at, version ne peuvent
        pas être définis par l'utilisateur lors de la création."""
        service = ResourceService(session)
        req = ResourceCreate(
            type="entity",
            data={
                "entity_subtype": "test",
                "id": "12345678-1234-1234-1234-123456789012",  # interdit
                "created_at": "2020-01-01T00:00:00Z",  # interdit
                "updated_at": "2020-01-01T00:00:00Z",  # interdit
                "deleted_at": "2020-01-01T00:00:00Z",  # interdit
                "version": 999,  # interdit
            },
        )
        result = await service.create(req)
        # entity_subtype doit être présent, les champs interdits non
        assert result.data.get("entity_subtype") == "test"
        assert "id" not in result.data or result.data.get("id") != req.data["id"]
        # created_at doit être défini par le système, pas par l'utilisateur
        assert result.created_at != req.data["created_at"]

    @pytest.mark.asyncio
    async def test_should_filter_unknown_fields_on_create(self, session: AsyncSession) -> None:
        """Les champs qui ne sont pas des colonnes du modèle sont ignorés."""
        service = ResourceService(session)
        req = ResourceCreate(
            type="entity",
            data={
                "entity_subtype": "test",
                "fake_field": "should be ignored",
                "another_fake": 123,
            },
        )
        result = await service.create(req)
        assert "fake_field" not in result.data
        assert "another_fake" not in result.data
        assert result.data.get("entity_subtype") == "test"

    @pytest.mark.asyncio
    async def test_should_filter_forbidden_fields_on_update(self, session: AsyncSession) -> None:
        """Les champs système ne peuvent pas être modifiés via update."""
        service = ResourceService(session)
        # Créer d'abord
        create_req = ResourceCreate(type="entity", data={"entity_subtype": "initial"})
        created = await service.create(create_req)

        # Tenter de modifier created_at via update
        update_req = ResourceUpdate(
            data={
                "entity_subtype": "modified",
                "created_at": "2020-01-01T00:00:00Z",  # interdit
                "deleted_at": "2020-01-01T00:00:00Z",  # interdit
            },
            justification="Test mass-assignment",
        )
        result = await service.update(created.id, update_req)
        assert result is not None
        # entity_subtype doit être modifié
        assert result.data.get("entity_subtype") == "modified"
        # created_at ne doit pas avoir changé
        assert result.created_at == created.created_at


class TestAppendOnlyRevisions:
    """Tests du caractère append-only des révisions (CON-010)."""

    @pytest.mark.asyncio
    async def test_should_create_revision_v1_on_create(self, session: AsyncSession) -> None:
        """La création d'une resource doit créer une Revision v1."""
        service = ResourceService(session)
        req = ResourceCreate(type="entity", data={"entity_subtype": "test"})
        result = await service.create(req)

        revisions = await service.list_revisions(result.id)
        assert len(revisions) == 1
        assert revisions[0].version == 1
        assert "Création" in revisions[0].justification

    @pytest.mark.asyncio
    async def test_should_create_new_revision_on_update(self, session: AsyncSession) -> None:
        """L'update crée une nouvelle Revision (v2), n'écrase pas v1."""
        service = ResourceService(session)
        # Créer
        create_req = ResourceCreate(type="entity", data={"entity_subtype": "v1"})
        created = await service.create(create_req)

        # Updater
        update_req = ResourceUpdate(
            data={"entity_subtype": "v2"},
            justification="Modification test",
        )
        await service.update(created.id, update_req)

        # Vérifier qu'on a 2 révisions
        revisions = await service.list_revisions(created.id)
        assert len(revisions) == 2
        assert revisions[0].version == 2  # tri desc
        assert revisions[1].version == 1
        assert "Modification test" in revisions[0].justification

    @pytest.mark.asyncio
    async def test_should_preserve_old_revisions_after_multiple_updates(
        self, session: AsyncSession
    ) -> None:
        """Plusieurs updates créent plusieurs révisions, toutes préservées."""
        service = ResourceService(session)
        created = await service.create(
            ResourceCreate(type="entity", data={"entity_subtype": "v1"})
        )

        for i in range(2, 6):
            await service.update(
                created.id,
                ResourceUpdate(
                    data={"entity_subtype": f"v{i}"},
                    justification=f"Update {i}",
                ),
            )

        revisions = await service.list_revisions(created.id)
        assert len(revisions) == 5
        versions = [r.version for r in revisions]
        assert versions == [5, 4, 3, 2, 1]  # tri desc


class TestSoftDelete:
    """Tests du soft-delete (CON-010 — jamais DELETE physique)."""

    @pytest.mark.asyncio
    async def test_should_mark_deleted_at_on_delete(self, session: AsyncSession) -> None:
        """Le soft-delete marque deleted_at, ne supprime pas la ligne."""
        service = ResourceService(session)
        created = await service.create(
            ResourceCreate(type="entity", data={"entity_subtype": "to-delete"})
        )

        deleted = await service.delete(created.id, justification="Test soft-delete")
        assert deleted is True

        # Vérifier que la resource existe toujours en DB mais avec deleted_at
        result = await session.get(ResourceModel, created.id)
        assert result is not None  # toujours en DB
        assert result.deleted_at is not None  # marqué supprimé

    @pytest.mark.asyncio
    async def test_should_not_return_soft_deleted_resource_on_get(
        self, session: AsyncSession
    ) -> None:
        """get() retourne None pour une resource soft-deleted."""
        service = ResourceService(session)
        created = await service.create(
            ResourceCreate(type="entity", data={"entity_subtype": "to-delete"})
        )

        await service.delete(created.id)
        result = await service.get(created.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_should_not_list_soft_deleted_resources(self, session: AsyncSession) -> None:
        """list_resources() exclut les resources soft-deleted."""
        service = ResourceService(session)
        await service.create(ResourceCreate(type="entity", data={"entity_subtype": "alive"}))
        to_delete = await service.create(
            ResourceCreate(type="entity", data={"entity_subtype": "dead"})
        )
        await service.delete(to_delete.id)

        result = await service.list_resources()
        assert result.total == 1
        assert all(r.data.get("entity_subtype") != "dead" for r in result.items)

    @pytest.mark.asyncio
    async def test_should_return_false_when_deleting_nonexistent(self, session: AsyncSession) -> None:
        """delete() retourne False si la resource n'existe pas."""
        service = ResourceService(session)
        from uuid import uuid4
        result = await service.delete(uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_should_return_false_when_deleting_already_deleted(
        self, session: AsyncSession
    ) -> None:
        """delete() retourne False si la resource est déjà soft-deleted."""
        service = ResourceService(session)
        created = await service.create(ResourceCreate(type="entity", data={}))
        await service.delete(created.id)
        # Second delete
        result = await service.delete(created.id)
        assert result is False

    @pytest.mark.asyncio
    async def test_should_create_final_revision_on_delete(self, session: AsyncSession) -> None:
        """Le soft-delete crée une Revision finale avec [DELETED]."""
        service = ResourceService(session)
        created = await service.create(ResourceCreate(type="entity", data={}))
        await service.delete(created.id, justification="Fin de vie")

        revisions = await service.list_revisions(created.id)
        assert len(revisions) == 2  # v1 création + v2 suppression
        assert "[DELETED]" in revisions[0].justification
        assert "Fin de vie" in revisions[0].justification


class TestCreateAndRead:
    """Tests de création et lecture."""

    @pytest.mark.asyncio
    async def test_should_create_and_read_resource(self, session: AsyncSession) -> None:
        """Création puis lecture retourne les mêmes données."""
        service = ResourceService(session)
        req = ResourceCreate(type="entity", data={"entity_subtype": "my-entity"})
        created = await service.create(req)

        read = await service.get(created.id)
        assert read is not None
        assert read.type == "entity"
        assert read.data.get("entity_subtype") == "my-entity"
        assert read.gsie_id is not None

    @pytest.mark.asyncio
    async def test_should_generate_gsie_id_if_not_provided(self, session: AsyncSession) -> None:
        """Un gsie_id est généré automatiquement si non fourni."""
        service = ResourceService(session)
        req = ResourceCreate(type="entity", data={})
        result = await service.create(req)
        assert result.gsie_id is not None
        assert result.gsie_id.startswith("entity:")

    @pytest.mark.asyncio
    async def test_should_use_provided_gsie_id(self, session: AsyncSession) -> None:
        """Le gsie_id fourni est utilisé tel quel."""
        service = ResourceService(session)
        req = ResourceCreate(
            type="entity", gsie_id="entity:custom:123", data={}
        )
        result = await service.create(req)
        assert result.gsie_id == "entity:custom:123"

    @pytest.mark.asyncio
    async def test_should_return_none_for_nonexistent_id(self, session: AsyncSession) -> None:
        """get() retourne None pour un ID inexistant."""
        service = ResourceService(session)
        from uuid import uuid4
        result = await service.get(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_should_raise_for_unknown_type(self, session: AsyncSession) -> None:
        """create() lève ValueError pour un type inconnu."""
        service = ResourceService(session)
        req = ResourceCreate(type="unknown_type", data={})
        with pytest.raises(ValueError, match="Type inconnu"):
            await service.create(req)


class TestListPagination:
    """Tests de la pagination."""

    @pytest.mark.asyncio
    async def test_should_paginate_results(self, session: AsyncSession) -> None:
        """list_resources pagine correctement."""
        service = ResourceService(session)
        for i in range(5):
            await service.create(
                ResourceCreate(type="entity", data={"entity_subtype": f"e{i}"})
            )

        page1 = await service.list_resources(page=1, size=2)
        assert page1.total == 5
        assert len(page1.items) == 2
        assert page1.page == 1

        page2 = await service.list_resources(page=2, size=2)
        assert len(page2.items) == 2

        page3 = await service.list_resources(page=3, size=2)
        assert len(page3.items) == 1

    @pytest.mark.asyncio
    async def test_should_filter_by_type(self, session: AsyncSession) -> None:
        """list_resources filtre par type."""
        service = ResourceService(session)
        await service.create(ResourceCreate(type="entity", data={}))
        await service.create(ResourceCreate(type="concept", data={
            "preferred_label": "Test", "description": "Test"
        }))

        result = await service.list_resources(type_filter="entity")
        assert result.total == 1
        assert result.type_filter == "entity"
        assert result.items[0].type == "entity"


class TestUpdateBehavior:
    """Tests du comportement d'update."""

    @pytest.mark.asyncio
    async def test_should_return_none_for_nonexistent_update(self, session: AsyncSession) -> None:
        """update() retourne None pour un ID inexistant."""
        service = ResourceService(session)
        from uuid import uuid4
        req = ResourceUpdate(data={"entity_subtype": "x"}, justification="test")
        result = await service.update(uuid4(), req)
        assert result is None

    @pytest.mark.asyncio
    async def test_should_return_none_for_soft_deleted_update(
        self, session: AsyncSession
    ) -> None:
        """update() retourne None pour une resource soft-deleted."""
        service = ResourceService(session)
        created = await service.create(ResourceCreate(type="entity", data={}))
        await service.delete(created.id)
        req = ResourceUpdate(data={"entity_subtype": "x"}, justification="test")
        result = await service.update(created.id, req)
        assert result is None

    @pytest.mark.asyncio
    async def test_should_only_update_provided_fields(self, session: AsyncSession) -> None:
        """update() ne modifie que les champs fournis."""
        service = ResourceService(session)
        created = await service.create(
            ResourceCreate(type="entity", data={"entity_subtype": "original"})
        )
        req = ResourceUpdate(data={}, justification="empty update")
        result = await service.update(created.id, req)
        assert result is not None
        # entity_subtype ne doit pas changer
        assert result.data.get("entity_subtype") == "original"

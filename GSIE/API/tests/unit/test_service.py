"""Tests unitaires — ResourceService (CRUD, mass-assignment, append-only, soft-delete).

Utilise SQLite in-memory (aiosqlite) pour tester le service sans Docker.
Les types UUID/JSONB/PostGIS sont adaptés pour SQLite via @compiles.
"""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

try:
    from geoalchemy2 import Geometry as _GeometryType
except ImportError:
    _GeometryType = None  # type: ignore

from gsie_api.infrastructure.models import RESOURCE_TYPES, Base, ResourceModel
from gsie_api.infrastructure.models.outbox import OutboxEvent
from gsie_api.outbox_worker import deliver_outbox_batch
from gsie_api.resources.schemas import ResourceCreate, ResourceUpdate
from gsie_api.resources.service import ResourceService
from gsie_api.resources.validators import MAX_STRING_LENGTH, ResourceValidationError

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
                # "now()" (chaîne ou text()) → DefaultClause(func.now()),
                # seule forme que SQLite sait compiler.
                if str(sd_arg) == "now()":
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
            t
            for t in Base.metadata.sorted_tables
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


class TestTransactionalOutbox:
    """Tests de la cohérence écriture métier + événement (ADR-005)."""

    @pytest.mark.asyncio
    async def test_should_create_pending_event_in_same_transaction(
        self, session: AsyncSession
    ) -> None:
        service = ResourceService(session)
        created = await service.create(
            ResourceCreate(type="entity", data={"entity_subtype": "outbox"})
        )

        events = (await session.execute(select(OutboxEvent))).scalars().all()

        assert len(events) == 1
        assert events[0].aggregate_id == created.id
        assert events[0].aggregate_type == "entity"
        assert events[0].event_type == "resource.created"
        assert events[0].status == "pending"
        assert events[0].payload["data"] == {"gsie_id": created.gsie_id}

    @pytest.mark.asyncio
    async def test_should_redact_values_from_update_event(self, session: AsyncSession) -> None:
        """Le temps réel expose les champs modifiés, jamais leurs valeurs."""
        service = ResourceService(session)
        created = await service.create(
            ResourceCreate(type="entity", data={"entity_subtype": "avant"})
        )
        await service.update(
            created.id,
            ResourceUpdate(
                data={"entity_subtype": "apres"},
                justification="test de redaction",
            ),
        )

        events = (await session.execute(select(OutboxEvent))).scalars().all()
        updated = next(event for event in events if event.event_type == "resource.updated")

        assert updated.payload["data"] == {
            "version": 2,
            "changed_fields": ["entity_subtype"],
        }
        assert "avant" not in str(updated.payload)
        assert "apres" not in str(updated.payload)

    @pytest.mark.asyncio
    async def test_should_mark_event_published_after_success(self, session: AsyncSession) -> None:
        service = ResourceService(session)
        await service.create(ResourceCreate(type="entity", data={"entity_subtype": "deliver"}))
        publisher = AsyncMock()

        delivered = await deliver_outbox_batch(session, publisher=publisher)
        event = (await session.execute(select(OutboxEvent))).scalar_one()

        assert delivered == 1
        assert event.status == "published"
        assert event.published_at is not None
        publisher.assert_awaited_once()
        channel, payload = publisher.await_args.args
        assert channel == "entity"
        assert payload["event_id"] == str(event.id)

    @pytest.mark.asyncio
    async def test_should_keep_event_pending_after_publish_failure(
        self, session: AsyncSession
    ) -> None:
        service = ResourceService(session)
        await service.create(ResourceCreate(type="entity", data={"entity_subtype": "retry"}))
        publisher = AsyncMock(side_effect=RuntimeError("redis indisponible"))

        delivered = await deliver_outbox_batch(session, publisher=publisher)
        event = (await session.execute(select(OutboxEvent))).scalar_one()

        assert delivered == 0
        assert event.status == "pending"
        assert event.published_at is None


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
        created = await service.create(ResourceCreate(type="entity", data={"entity_subtype": "v1"}))

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
    async def test_should_return_false_when_deleting_nonexistent(
        self, session: AsyncSession
    ) -> None:
        """delete() retourne False si la resource n'existe pas."""
        service = ResourceService(session)
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
        req = ResourceCreate(type="entity", gsie_id="entity:custom:123", data={})
        result = await service.create(req)
        assert result.gsie_id == "entity:custom:123"

    @pytest.mark.asyncio
    async def test_should_return_none_for_nonexistent_id(self, session: AsyncSession) -> None:
        """get() retourne None pour un ID inexistant."""
        service = ResourceService(session)
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
            await service.create(ResourceCreate(type="entity", data={"entity_subtype": f"e{i}"}))

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
        await service.create(
            ResourceCreate(type="concept", data={"preferred_label": "Test", "description": "Test"})
        )

        result = await service.list_resources(type_filter="entity")
        assert result.total == 1
        assert result.type_filter == "entity"
        assert result.items[0].type == "entity"

    @pytest.mark.asyncio
    async def test_should_exclude_sensitive_types_from_list(self, session: AsyncSession) -> None:
        """La pagination doit exclure les types interdits avant le comptage."""
        service = ResourceService(session)
        await service.create(ResourceCreate(type="entity", data={}))
        await service.create(
            ResourceCreate(
                type="consent",
                data={
                    "data_subject_id": uuid4(),
                    "purpose": "test de confidentialite",
                    "scope": "full",
                    "granted_at": datetime.now(UTC),
                    "legal_basis": "consent",
                },
            )
        )

        result = await service.list_resources(excluded_types={"consent"})

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].type == "entity"


class TestUpdateBehavior:
    """Tests du comportement d'update."""

    @pytest.mark.asyncio
    async def test_should_return_none_for_nonexistent_update(self, session: AsyncSession) -> None:
        """update() retourne None pour un ID inexistant."""
        service = ResourceService(session)
        req = ResourceUpdate(data={"entity_subtype": "x"}, justification="test")
        result = await service.update(uuid4(), req)
        assert result is None

    @pytest.mark.asyncio
    async def test_should_return_none_for_soft_deleted_update(self, session: AsyncSession) -> None:
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


class TestUpdateValidationGate:
    """La mise à jour est validée sur l'état final, pas sur le patch seul.

    Avant ce garde-fou, `update()` ne passait jamais par
    `validate_resource_data` : un enum inconnu ou une règle métier violée
    entrait en base par la porte de derrière, avec Revision et événement
    d'outbox à l'appui — donc traçable et faux à la fois.
    """

    @staticmethod
    async def _assertion_valide(service: ResourceService) -> Any:
        return await service.create(
            ResourceCreate(
                type="assertion",
                data={"claim_kind": "relation", "lifecycle_status": "draft"},
            )
        )

    @staticmethod
    async def _etat_persiste(session: AsyncSession, resource_id: Any) -> dict[str, Any]:
        """Relit l'état réellement écrit, hors cache d'identité de la session."""
        session.expire_all()
        model_cls = RESOURCE_TYPES["assertion"]
        instance = await session.get(model_cls, resource_id)
        assert instance is not None
        return {
            col.name: getattr(instance, col.name)
            for col in instance.__table__.columns
            if col.name != "id"
        }

    @pytest.mark.asyncio
    async def test_should_reject_invalid_enum_on_update(self, session: AsyncSession) -> None:
        """Un enum invalide est refusé — mêmes règles qu'à la création."""
        service = ResourceService(session)
        created = await self._assertion_valide(service)

        with pytest.raises(ResourceValidationError) as exc_info:
            await service.update(
                created.id,
                ResourceUpdate(data={"claim_kind": "toto"}, justification="enum invalide"),
            )

        assert exc_info.value.type_name == "assertion"
        assert any("claim_kind" in erreur for erreur in exc_info.value.errors)

    @pytest.mark.asyncio
    async def test_should_leave_state_revision_and_outbox_untouched_on_reject(
        self, session: AsyncSession
    ) -> None:
        """Un refus ne laisse ni mutation, ni Revision, ni événement fantôme."""
        service = ResourceService(session)
        created = await self._assertion_valide(service)
        revisions_avant = len(await service.list_revisions(created.id))
        evenements_avant = len((await session.execute(select(OutboxEvent))).scalars().all())

        with pytest.raises(ResourceValidationError):
            await service.update(
                created.id,
                ResourceUpdate(data={"claim_kind": "toto"}, justification="enum invalide"),
            )

        etat = await self._etat_persiste(session, created.id)
        assert etat["claim_kind"] == "relation"
        assert len(await service.list_revisions(created.id)) == revisions_avant
        evenements = (await session.execute(select(OutboxEvent))).scalars().all()
        assert len(evenements) == evenements_avant

    @pytest.mark.asyncio
    async def test_should_reject_update_emptying_required_field(
        self, session: AsyncSession
    ) -> None:
        """Vider un champ obligatoire est refusé, même en patch partiel."""
        service = ResourceService(session)
        created = await self._assertion_valide(service)

        with pytest.raises(ResourceValidationError) as exc_info:
            await service.update(
                created.id,
                ResourceUpdate(
                    data={"lifecycle_status": None},
                    justification="tentative de vidage",
                ),
            )

        assert any("lifecycle_status" in erreur for erreur in exc_info.value.errors)
        etat = await self._etat_persiste(session, created.id)
        assert etat["lifecycle_status"] == "draft"

    @pytest.mark.asyncio
    async def test_should_reject_conditional_rule_violation_on_update(
        self, session: AsyncSession
    ) -> None:
        """Les règles conditionnelles valent aussi à la mise à jour.

        `silvicultural_rule` interdit `status='accepted'` sans validateur
        humain : jamais d'auto-validation par le pipeline (RFC-0016 §3.2).
        """
        service = ResourceService(session)
        created = await service.create(
            ResourceCreate(
                type="silvicultural_rule",
                data={
                    "required_context": "futaie reguliere",
                    "validity_zone_description": "Haute-Normandie",
                    "trigger": "surface terriere > 30",
                    "action": "eclaircie",
                    "intensity": "moderee",
                    "evidence_level": "B",
                    "source_id": uuid4(),
                },
            )
        )

        with pytest.raises(ResourceValidationError) as exc_info:
            await service.update(
                created.id,
                ResourceUpdate(
                    data={"status": "accepted"},
                    justification="auto-validation interdite",
                ),
            )

        assert any("human_validator" in erreur for erreur in exc_info.value.errors)

    @pytest.mark.asyncio
    async def test_should_accept_valid_partial_patch_and_keep_other_fields(
        self, session: AsyncSession
    ) -> None:
        """Un patch partiel valide passe et préserve les champs non fournis."""
        service = ResourceService(session)
        created = await self._assertion_valide(service)

        result = await service.update(
            created.id,
            ResourceUpdate(
                data={"lifecycle_status": "accepted"},
                justification="passage en accepted",
            ),
        )

        assert result is not None
        etat = await self._etat_persiste(session, created.id)
        assert etat["lifecycle_status"] == "accepted"
        # claim_kind n'était pas dans le patch : il doit survivre intact.
        assert etat["claim_kind"] == "relation"

    @pytest.mark.asyncio
    async def test_should_reject_oversized_string_on_update(self, session: AsyncSession) -> None:
        """Les bornes de transport s'appliquent au corps reçu."""
        service = ResourceService(session)
        created = await self._assertion_valide(service)

        with pytest.raises(ResourceValidationError) as exc_info:
            await service.update(
                created.id,
                ResourceUpdate(
                    data={"rule_subtype": "x" * (MAX_STRING_LENGTH + 1)},
                    justification="corps abusif",
                ),
            )

        assert any("trop long" in erreur for erreur in exc_info.value.errors)

    @pytest.mark.asyncio
    async def test_should_not_reject_wide_resource_on_field_count(
        self, session: AsyncSession
    ) -> None:
        """La limite de nombre de champs ne s'applique pas à l'état fusionné.

        Sinon un type large deviendrait immodifiable dès que son état complet
        dépasse la borne prévue pour le corps de requête.
        """
        service = ResourceService(session)
        created = await self._assertion_valide(service)
        colonnes = len(RESOURCE_TYPES["assertion"].__table__.columns)

        result = await service.update(
            created.id,
            ResourceUpdate(data={"lifecycle_status": "proposed"}, justification="patch etroit"),
        )

        assert result is not None
        assert colonnes > 1  # l'état fusionné compte bien plus d'un champ

    @pytest.mark.asyncio
    async def test_should_apply_same_rules_on_create_and_update(
        self, session: AsyncSession
    ) -> None:
        """Création et mise à jour refusent exactement la même faute."""
        service = ResourceService(session)

        with pytest.raises(ResourceValidationError) as creation:
            await service.create(
                ResourceCreate(
                    type="assertion",
                    data={"claim_kind": "toto", "lifecycle_status": "draft"},
                )
            )

        created = await self._assertion_valide(service)
        with pytest.raises(ResourceValidationError) as mise_a_jour:
            await service.update(
                created.id,
                ResourceUpdate(data={"claim_kind": "toto"}, justification="meme faute"),
            )

        assert creation.value.errors == mise_a_jour.value.errors

"""Tests d'intégration — pipeline d'ingestion en lot (bulk).

Ces tests vérifient le pipeline bulk de bout en bout sur PostgreSQL :
1. Création d'un lot de 3 resources valides → 3 succès.
2. Lot avec 1 item invalide → 2 succès + 1 erreur (échec partiel).
3. Lot vide → 400 (validation Pydantic).
4. Lot > 1000 items → 400 (limite schéma).
5. RBAC : un reader ne peut pas créer (403).
6. Les resources créées sont persistées (vérification en DB).
7. Une Revision v1 est créée pour chaque resource (CON-010).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.infrastructure.database import get_db
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.temporal_engine import RevisionModel
from tests.conftest import requires_docker

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = requires_docker

_SUJET = "forestier-bulk"


@pytest.fixture
def entetes_ecriture() -> dict[str, str]:
    """Jeton writer forgé à l'exécution."""
    token = create_access_token(subject=_SUJET, claims={"roles": ["writer"]})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def entetes_lecture() -> dict[str, str]:
    """Jeton reader forgé à l'exécution."""
    token = create_access_token(subject="liseur-bulk", claims={"roles": ["reader"]})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP avec session DB partagée."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestBulkIngestion:
    """Pipeline d'ingestion en lot — bout en bout sur PostgreSQL."""

    async def test_should_create_3_valid_resources_in_one_batch(
        self, client: AsyncClient, entetes_ecriture: dict[str, str]
    ) -> None:
        """Un lot de 3 resources valides doit réussir entièrement."""
        reponse = await client.post(
            "/api/v1/resources/bulk",
            json={
                "items": [
                    {"type": "entity", "data": {"entity_subtype": "parcelle"}},
                    {"type": "entity", "data": {"entity_subtype": "essence"}},
                    {"type": "entity", "data": {"entity_subtype": "station"}},
                ]
            },
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 201, reponse.text
        body = reponse.json()
        assert body["total"] == 3
        assert body["success"] == 3
        assert body["errors"] == 0
        assert len(body["items"]) == 3
        for item in body["items"]:
            assert item["success"] is True
            assert item["resource_id"] is not None

    async def test_should_allow_partial_failure_with_2_success_1_error(
        self, client: AsyncClient, entetes_ecriture: dict[str, str]
    ) -> None:
        """Un lot avec 1 item invalide doit réussir partiellement (2 succès + 1 erreur)."""
        reponse = await client.post(
            "/api/v1/resources/bulk",
            json={
                "items": [
                    {"type": "entity", "data": {"entity_subtype": "parcelle"}},
                    # Item invalide : type inconnu
                    {"type": "type_inexistant", "data": {}},
                    {"type": "entity", "data": {"entity_subtype": "station"}},
                ]
            },
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 201, reponse.text
        body = reponse.json()
        assert body["total"] == 3
        assert body["success"] == 2
        assert body["errors"] == 1
        # L'item en erreur est à l'index 1
        item_echec = next(i for i in body["items"] if not i["success"])
        assert item_echec["index"] == 1
        assert item_echec["error_code"] in ("unknown_type", "validation_failed")

    async def test_une_violation_d_integrite_n_annule_que_son_item(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        entetes_ecriture: dict[str, str],
    ) -> None:
        """L'échec d'un item ne doit effacer aucun des items déjà insérés.

        Le service annulait la transaction entière (`session.rollback()`) au
        premier `IntegrityError`, tout en laissant les items précédents
        annoncés `success: true` avec un `resource_id`. Le client se voyait
        confirmer des resources qui n'existaient plus. Chaque item vit
        désormais dans son propre point de reprise.
        """
        gsie_id_double = "entity:2026:aaaaaaaa"
        reponse = await client.post(
            "/api/v1/resources/bulk",
            json={
                "items": [
                    {
                        "type": "entity",
                        "gsie_id": gsie_id_double,
                        "data": {"entity_subtype": "parcelle"},
                    },
                    # Même gsie_id : viole la contrainte d'unicité.
                    {
                        "type": "entity",
                        "gsie_id": gsie_id_double,
                        "data": {"entity_subtype": "essence"},
                    },
                    {"type": "entity", "data": {"entity_subtype": "station"}},
                ]
            },
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 201, reponse.text
        body = reponse.json()
        assert body["success"] == 2
        assert body["errors"] == 1

        echec = next(i for i in body["items"] if not i["success"])
        assert echec["index"] == 1
        assert echec["error_code"] == "integrity_error"
        # Le texte du pilote ne doit pas ressortir (OWASP A01/A09).
        assert "constraint" not in str(echec["error_detail"])
        assert "resource_gsie_id_key" not in str(echec["error_detail"])

        # Les deux succès annoncés doivent réellement exister.
        succes = [i for i in body["items"] if i["success"]]
        assert len(succes) == 2
        for item in succes:
            persistee = await db_session.get(ResourceModel, item["resource_id"])
            assert (
                persistee is not None
            ), f"l'item {item['index']} est annoncé créé mais absent de la base"

    async def test_should_reject_empty_batch(
        self, client: AsyncClient, entetes_ecriture: dict[str, str]
    ) -> None:
        """Un lot vide doit être rejeté (422 — validation Pydantic)."""
        reponse = await client.post(
            "/api/v1/resources/bulk",
            json={"items": []},
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 422, reponse.text

    async def test_should_reject_batch_over_1000_items(
        self, client: AsyncClient, entetes_ecriture: dict[str, str]
    ) -> None:
        """Un lot de 1001 items doit être rejeté (422 — limite schéma)."""
        items = [{"type": "entity", "data": {"entity_subtype": "x"}} for _ in range(1001)]
        reponse = await client.post(
            "/api/v1/resources/bulk",
            json={"items": items},
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 422, reponse.text

    async def test_should_reject_reader_creating_bulk(
        self, client: AsyncClient, entetes_lecture: dict[str, str]
    ) -> None:
        """Un reader ne peut pas créer de resources (403)."""
        reponse = await client.post(
            "/api/v1/resources/bulk",
            json={"items": [{"type": "entity", "data": {"entity_subtype": "x"}}]},
            headers=entetes_lecture,
        )

        assert reponse.status_code == 403, reponse.text

    async def test_should_persist_resources_in_database(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        entetes_ecriture: dict[str, str],
    ) -> None:
        """Les resources créées en lot doivent être persistées en DB."""
        reponse = await client.post(
            "/api/v1/resources/bulk",
            json={
                "items": [
                    {"type": "entity", "data": {"entity_subtype": "parcelle"}},
                    {"type": "entity", "data": {"entity_subtype": "essence"}},
                ]
            },
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 201, reponse.text
        body = reponse.json()
        assert body["success"] == 2

        # Vérifier que les resources sont en DB
        for item in body["items"]:
            if item["success"]:
                result = await db_session.get(ResourceModel, item["resource_id"])
                assert result is not None, "La resource doit être persistée"
                assert result.deleted_at is None

    async def test_should_create_revision_v1_for_each_resource(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        entetes_ecriture: dict[str, str],
    ) -> None:
        """Une Revision v1 doit être créée pour chaque resource (CON-010)."""
        reponse = await client.post(
            "/api/v1/resources/bulk",
            json={
                "items": [
                    {"type": "entity", "data": {"entity_subtype": "parcelle"}},
                ]
            },
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 201, reponse.text
        body = reponse.json()
        assert body["success"] == 1
        resource_id = body["items"][0]["resource_id"]

        # Vérifier qu'une Revision v1 existe
        query = select(RevisionModel).where(
            RevisionModel.target_id == resource_id,
            RevisionModel.version == 1,
        )
        result = await db_session.execute(query)
        revision = result.scalar_one_or_none()
        assert revision is not None, "Une Revision v1 doit exister (CON-010)"
        assert revision.version == 1
        assert revision.justification == "Création en lot"

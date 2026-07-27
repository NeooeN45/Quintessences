"""Fiabilité du CRUD générique sur base réelle — chemins jamais couverts.

Trois défauts se cachaient derrière les tests existants :

* `revision.author_id` et `resource_diff.id` référencent `resource(id)` ; le
  service citait des identifiants sans ligne parente, donc toute écriture
  authentifiée échouait en `ForeignKeyViolationError` sur PostgreSQL. Les tests
  unitaires tournent sur SQLite, qui n'applique pas les clés étrangères, et la
  suite d'intégration créait l'Agent à la main dans sa fixture — le chemin de
  production, lui, n'était garanti par rien.
* la relecture qui suit l'écriture touchait des colonnes `onupdate=func.now()`
  expirées par le commit, déclenchant un chargement paresseux hors greenlet.
* `GET /resources?type=` (vide) était traité comme un filtre : l'exclusion RGPD
  était désactivée alors qu'aucun filtre n'était réellement appliqué.

Ces tests exercent donc le chemin nominal **sans** rien préparer à la main.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.core.rbac import RGPD_RESOURCE_TYPES
from gsie_api.infrastructure.database import get_db
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.temporal_engine import ResourceDiffModel, RevisionModel
from tests.conftest import requires_docker

pytestmark = requires_docker

_SUJET = "forestier-fiabilite"
_ENTETES_ECRITURE = {
    "Authorization": f"Bearer {create_access_token(subject=_SUJET, claims={'roles': ['writer']})}"
}
_ENTETES_LECTURE = {
    "Authorization": f"Bearer {create_access_token(subject='liseur', claims={'roles': ['reader']})}"
}


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP sans aucune préparation : l'Agent auteur n'existe pas."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestEcritureAuthentifiee:
    """L'auteur cité doit exister : le service le matérialise lui-même."""

    async def test_creation_reussit_sans_agent_pre_cree(self, client: AsyncClient) -> None:
        reponse = await client.post(
            "/api/v1/resources",
            json={"type": "entity", "data": {"entity_subtype": "parcelle"}},
            headers=_ENTETES_ECRITURE,
        )

        assert reponse.status_code == 201, reponse.text

    async def test_mise_a_jour_ecrit_un_diff_rattache(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        cree = await client.post(
            "/api/v1/resources",
            json={"type": "entity", "data": {"entity_subtype": "avant"}},
            headers=_ENTETES_ECRITURE,
        )
        assert cree.status_code == 201, cree.text
        identifiant = cree.json()["id"]

        maj = await client.put(
            f"/api/v1/resources/{identifiant}",
            json={"data": {"entity_subtype": "apres"}, "justification": "affinage station"},
            headers=_ENTETES_ECRITURE,
        )

        assert maj.status_code == 200, maj.text
        # La valeur relue après commit prouve l'absence de chargement paresseux.
        assert maj.json()["data"]["entity_subtype"] == "apres"

        diff = (await db_session.execute(select(ResourceDiffModel))).scalars().one()
        revision = (
            (await db_session.execute(select(RevisionModel).where(RevisionModel.version == 2)))
            .scalars()
            .one()
        )
        assert revision.diff_id == diff.id
        # Le diff est bien une resource du métamodèle (type 61, ADR-002),
        # pas un identifiant orphelin.
        parent = await db_session.get(ResourceModel, diff.id)
        assert parent is not None
        assert parent.type == "resource_diff"


class TestExclusionRGPD:
    """Un `?type=` vide n'est pas un filtre et ne lève aucune protection."""

    @pytest.mark.parametrize("requete", ["/api/v1/resources", "/api/v1/resources?type="])
    async def test_lecteur_ne_voit_jamais_les_types_rgpd(
        self, client: AsyncClient, db_session: AsyncSession, requete: str
    ) -> None:
        db_session.add(ResourceModel(type="consent", gsie_id="consent:2026:fiabilite"))
        db_session.add(ResourceModel(type="entity", gsie_id="entity:2026:fiabilite"))
        await db_session.commit()

        reponse = await client.get(requete, headers=_ENTETES_LECTURE)

        assert reponse.status_code == 200, reponse.text
        types_vus = {item["type"] for item in reponse.json()["items"]}
        assert types_vus.isdisjoint(RGPD_RESOURCE_TYPES)
        assert "entity" in types_vus

"""Contrat HTTP de la porte de validation des resources.

Vérifie de bout en bout — routeur, service, base réelle — que la mise à jour
est jugée sur l'**état final**, que le refus est un 422 au corps stable, et
qu'un refus ne laisse derrière lui ni révision ni événement d'outbox.
"""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.infrastructure.database import get_db
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.outbox import OutboxEvent
from gsie_api.infrastructure.models.temporal_engine import RevisionModel
from gsie_api.resources.router import VALIDATION_ERROR_CODE, _extract_author_id
from tests.conftest import requires_docker

pytestmark = requires_docker

_SUJET = "test-resources"
_ACCESS_TOKEN = create_access_token(subject=_SUJET, claims={"roles": ["writer"]})
_AUTH = {"Authorization": f"Bearer {_ACCESS_TOKEN}"}
_ASSERTION_VALIDE = {"claim_kind": "relation", "lifecycle_status": "draft"}


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # `revision.author_id` référence `resource(id)` : l'auteur des révisions
    # doit exister comme resource avant toute écriture.
    auteur = _extract_author_id({"sub": _SUJET})
    assert auteur is not None
    db_session.add(ResourceModel(id=auteur, type="agent", gsie_id=f"agent:test:{auteur.hex[:8]}"))
    await db_session.commit()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


async def _creer_assertion(client: AsyncClient) -> dict[str, Any]:
    reponse = await client.post(
        "/api/v1/resources",
        json={"type": "assertion", "data": _ASSERTION_VALIDE},
        headers=_AUTH,
    )
    assert reponse.status_code == 201, reponse.text
    resultat: dict[str, Any] = reponse.json()
    return resultat


async def _compter(session: AsyncSession, modele: Any) -> int:
    total = (await session.execute(select(func.count()).select_from(modele))).scalar_one()
    return int(total)


async def _creer(client: AsyncClient, type_name: str, data: dict[str, Any]) -> str:
    """Crée une resource et retourne son identifiant."""
    reponse = await client.post(
        "/api/v1/resources",
        json={"type": type_name, "data": data},
        headers=_AUTH,
    )
    assert reponse.status_code == 201, reponse.text
    identifiant: str = reponse.json()["id"]
    return identifiant


# Le défaut de clé étrangère sur `resource_diff` est corrigé : aucun arbitrage
# de métamodèle n'était en fait requis, ADR-002 tranche déjà (ResourceDiff est le
# type 61, donc une resource, et il figure au registre des 90 types).
# `_add_resource_diff` crée désormais la ligne racine, comme tout autre type.
# Non-régression sur base réelle : tests/integration/test_resources_fiabilite.py.

# Le défaut `EvidenceLevel` est corrigé lui aussi : les colonnes de
# `forestry.py` déclarent désormais `values_callable`, comme le faisaient déjà
# `assertion.py` et `diagnostic.py`. SQLAlchemy persiste la valeur ('B') que le
# type PostgreSQL attend, et non plus le nom du membre ('b').


class TestValidation422:
    """Une faute métier est un 422 au corps stable, jamais un 400 ni un 500."""

    @pytest.mark.asyncio
    async def test_should_return_422_on_invalid_enum_update(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        cree = await _creer_assertion(client)

        reponse = await client.put(
            f"/api/v1/resources/{cree['id']}",
            json={"data": {"claim_kind": "toto"}, "justification": "enum invalide"},
            headers=_AUTH,
        )

        assert reponse.status_code == 422
        detail = reponse.json()["detail"]
        assert detail["code"] == VALIDATION_ERROR_CODE
        assert detail["resource_type"] == "assertion"
        assert any("claim_kind" in erreur for erreur in detail["errors"])

    @pytest.mark.asyncio
    async def test_should_return_422_on_conditional_rule_violation(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Jamais d'auto-validation d'une règle sylvicole (RFC-0016 §3.2).

        `status='accepted'` sans `human_validator` doit être refusé — la règle
        conditionnelle vaut à la mise à jour comme à la création.
        """
        # `source_id` référence `resource(id)` : la cible doit exister.
        source = await _creer(
            client,
            "source",
            {
                "title": "Guide des sylvicultures CNPF",
                "subtype": "publication",
                "source_nature": "reference",
            },
        )
        regle = await _creer(
            client,
            "silvicultural_rule",
            {
                "required_context": "futaie reguliere de hetre",
                "trigger": "surface terriere > 30",
                "action": "eclaircie par le haut",
                "intensity": "moderee",
                "evidence_level": "B",
                "source_id": source,
            },
        )

        reponse = await client.put(
            f"/api/v1/resources/{regle}",
            json={
                "data": {"status": "accepted"},
                "justification": "auto-validation interdite",
            },
            headers=_AUTH,
        )

        assert reponse.status_code == 422
        detail = reponse.json()["detail"]
        assert detail["code"] == VALIDATION_ERROR_CODE
        assert any("human_validator" in erreur for erreur in detail["errors"])

    @pytest.mark.asyncio
    async def test_should_leave_no_revision_nor_outbox_event_on_reject(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        cree = await _creer_assertion(client)
        revisions_avant = await _compter(db_session, RevisionModel)
        evenements_avant = await _compter(db_session, OutboxEvent)

        reponse = await client.put(
            f"/api/v1/resources/{cree['id']}",
            json={"data": {"claim_kind": "toto"}, "justification": "enum invalide"},
            headers=_AUTH,
        )

        assert reponse.status_code == 422
        assert await _compter(db_session, RevisionModel) == revisions_avant
        assert await _compter(db_session, OutboxEvent) == evenements_avant

        # L'état exposé est resté celui d'avant la tentative.
        lecture = await client.get(f"/api/v1/resources/{cree['id']}", headers=_AUTH)
        assert lecture.status_code == 200
        assert lecture.json()["data"]["claim_kind"] == "relation"

    @pytest.mark.asyncio
    async def test_should_return_422_on_invalid_creation_too(self, client: AsyncClient) -> None:
        """La création refuse la même faute, avec le même contrat de réponse."""
        reponse = await client.post(
            "/api/v1/resources",
            json={
                "type": "assertion",
                "data": {"claim_kind": "toto", "lifecycle_status": "draft"},
            },
            headers=_AUTH,
        )

        assert reponse.status_code == 422
        detail = reponse.json()["detail"]
        assert detail["code"] == VALIDATION_ERROR_CODE
        assert detail["resource_type"] == "assertion"


class TestPatchPartiel:
    """Un patch partiel valide passe et ne détruit rien autour de lui."""

    @pytest.mark.asyncio
    async def test_should_accept_valid_partial_patch(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        cree = await _creer_assertion(client)

        reponse = await client.put(
            f"/api/v1/resources/{cree['id']}",
            json={
                "data": {"lifecycle_status": "accepted"},
                "justification": "passage en accepted",
            },
            headers=_AUTH,
        )

        assert reponse.status_code == 200
        donnees = reponse.json()["data"]
        assert donnees["lifecycle_status"] == "accepted"
        # Champ absent du patch : inchangé.
        assert donnees["claim_kind"] == "relation"

    @pytest.mark.asyncio
    async def test_should_still_create_revision_on_accepted_update(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        cree = await _creer_assertion(client)

        reponse = await client.put(
            f"/api/v1/resources/{cree['id']}",
            json={"data": {"lifecycle_status": "proposed"}, "justification": "revision v2"},
            headers=_AUTH,
        )
        assert reponse.status_code == 200

        revisions = await client.get(f"/api/v1/resources/{cree['id']}/revisions", headers=_AUTH)
        assert revisions.status_code == 200
        versions = [element["version"] for element in revisions.json()]
        assert versions == [2, 1]

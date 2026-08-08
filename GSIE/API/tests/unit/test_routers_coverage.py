"""Tests unitaires — couverture des routers FastAPI (resources + 7 engines).

Objectif : combler la coverage des routers de 54-87% vers 90%+.
Tests sans Docker — la DB est mockee via dependency_overrides.

Routers couverts :
1. resources/router.py       — CRUD generique (auth, RBAC, validation 422)
2. engines/climate/router.py — observations Meteo-France (502 sur erreur)
3. engines/botanical/router.py — taxonomie GBIF/TAXREF (502 sur erreur)
4. engines/gis/router.py     — cadastre + altitude IGN (502 sur erreur)
5. engines/pedology/router.py — SoilGrids (502 sur erreur)
6. engines/forest_dynamics/router.py — dendrometrie geometrique
7. engines/diagnostic/router.py — diagnostic stationnel (400 sur erreur)
8. engines/knowledge/router.py — graphe de connaissances (400/404)
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from slowapi import Limiter
from slowapi.middleware import SlowAPIASGIMiddleware
from slowapi.util import get_remote_address

from gsie_api.core.auth import create_access_token
from gsie_api.engines.botanical.router import router as botanical_router
from gsie_api.engines.climate.router import router as climate_router
from gsie_api.engines.diagnostic.router import router as diagnostic_router
from gsie_api.engines.forest_dynamics.router import router as forest_dynamics_router
from gsie_api.engines.gis.router import router as gis_router
from gsie_api.engines.knowledge.router import router as knowledge_router
from gsie_api.engines.pedology.router import router as pedology_router
from gsie_api.engines.recommendation.router import router as recommendation_router
from gsie_api.infrastructure.database import get_db
from gsie_api.resources.router import router as resources_router
from gsie_api.resources.schemas import (
    ResourceListResponse,
    ResourceRead,
    RevisionRead,
)

# ---------------------------------------------------------------------------
# Helpers communs
# ---------------------------------------------------------------------------

_API_PREFIX = "/api/v1"


def _auth_headers(roles: list[str] | None = None) -> dict[str, str]:
    """Genere des headers d'auth avec un token JWT valide."""
    if roles is None:
        roles = ["reader"]
    token = create_access_token(subject="test-user", claims={"roles": roles})
    return {"Authorization": f"Bearer {token}"}


def _no_auth() -> dict[str, str]:
    """Headers sans token — pour tester la porte d'auth (401)."""
    return {}


def _source_ref() -> dict[str, Any]:
    """Dictionnaire SourceReference valide pour les reponses mockees."""
    return {
        "type_source": "peer_reviewed",
        "auteur": "Test Author",
        "reference": "https://example.org/test",
    }


def _build_engine_app(router: Any, mock_db: Any = None) -> FastAPI:
    """Cree une app FastAPI minimale avec un router engine et le limiter slowapi.

    Les routers engine utilisent des limiters locaux (Limiter local).  Pour
    que slowapi fonctionne, ``app.state.limiter`` doit etre defini et
    ``SlowAPIASGIMiddleware`` ajoute.
    """
    app = FastAPI()
    app.state.limiter = Limiter(key_func=get_remote_address)
    app.add_middleware(SlowAPIASGIMiddleware)

    if mock_db is not None:

        async def _override_get_db() -> AsyncGenerator[Any, None]:
            yield mock_db

        app.dependency_overrides[get_db] = _override_get_db

    app.include_router(router, prefix=_API_PREFIX)
    return app


def _build_resources_app(mock_db: Any) -> FastAPI:
    """Cree une app minimale pour le router resources avec le limiter global."""
    from gsie_api.core.limiter import limiter as global_limiter

    app = FastAPI()
    app.state.limiter = global_limiter
    app.add_middleware(SlowAPIASGIMiddleware)

    async def _override_get_db() -> AsyncGenerator[Any, None]:
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db
    app.include_router(resources_router, prefix=_API_PREFIX)
    return app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def resources_client() -> AsyncGenerator[AsyncClient, None]:
    """Client AsyncClient pour le router resources (DB mockee)."""
    mock_db = AsyncMock()
    app = _build_resources_app(mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def climate_client() -> AsyncGenerator[AsyncClient, None]:
    """Client AsyncClient pour le router climate.

    DB mockée : /query n'en a pas besoin (inchangé), mais
    /query-and-ingest en a besoin pour construire un KnowledgeEngine
    (Gate 5 — maillon amont ingestion→Evidence→Knowledge).
    """
    mock_db = AsyncMock()
    app = _build_engine_app(climate_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def botanical_client() -> AsyncGenerator[AsyncClient, None]:
    """Client AsyncClient pour le router botanical (DB mockee)."""
    mock_db = AsyncMock()
    app = _build_engine_app(botanical_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def gis_client() -> AsyncGenerator[AsyncClient, None]:
    """Client AsyncClient pour le router gis (DB mockee)."""
    mock_db = AsyncMock()
    app = _build_engine_app(gis_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def pedology_client() -> AsyncGenerator[AsyncClient, None]:
    """Client AsyncClient pour le router pedology.

    DB mockée : /query n'en a pas besoin (inchangé), mais
    /query-and-ingest en a besoin pour construire un KnowledgeEngine
    (Gate 5 — maillon amont ingestion→Evidence→Knowledge).
    """
    mock_db = AsyncMock()
    app = _build_engine_app(pedology_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def forest_dynamics_client() -> AsyncGenerator[AsyncClient, None]:
    """Client AsyncClient pour le router forest_dynamics (pas de DB)."""
    app = _build_engine_app(forest_dynamics_router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def diagnostic_client() -> AsyncGenerator[AsyncClient, None]:
    """Client AsyncClient pour le router diagnostic (DB mockee)."""
    mock_db = AsyncMock()
    app = _build_engine_app(diagnostic_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def knowledge_client() -> AsyncGenerator[AsyncClient, None]:
    """Client AsyncClient pour le router knowledge (DB mockee)."""
    mock_db = AsyncMock()
    app = _build_engine_app(knowledge_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def recommendation_client() -> AsyncGenerator[AsyncClient, None]:
    """Client AsyncClient pour le router recommendation (DB mockee)."""
    mock_db = AsyncMock()
    app = _build_engine_app(recommendation_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


# ===========================================================================
# 1. Resources Router — CRUD generique (auth, RBAC, validation 422)
# ===========================================================================


def _mock_resource_read() -> ResourceRead:
    """Construit un ResourceRead valide pour les mocks."""
    now = datetime.now(UTC)
    return ResourceRead(
        id=uuid4(),
        type="assertion",
        gsie_id="assertion:test:abcd1234",
        created_at=now,
        updated_at=now,
        data={"claim_kind": "relation", "lifecycle_status": "draft"},
    )


def _mock_revision_read() -> RevisionRead:
    """Construit un RevisionRead valide pour les mocks."""
    now = datetime.now(UTC)
    return RevisionRead(
        id=1,
        target_id=uuid4(),
        version=1,
        justification="Creation",
        valid_time_start=now,
        transaction_time=now,
        created_at=now,
    )


async def should_return_401_when_list_types_without_token(resources_client: AsyncClient):
    """La porte d'auth doit bloquer sans token (OWASP A01)."""
    response = await resources_client.get(f"{_API_PREFIX}/resources/types")
    assert response.status_code == 401


async def should_return_200_when_list_types_with_reader(resources_client: AsyncClient):
    """Un reader authentifie recupere la liste des types."""
    with patch.object(
        __import__("gsie_api.resources.service", fromlist=["ResourceService"]).ResourceService,
        "list_types",
        staticmethod(lambda: ["assertion", "observation"]),
    ):
        response = await resources_client.get(
            f"{_API_PREFIX}/resources/types", headers=_auth_headers(["reader"])
        )
    assert response.status_code == 200
    data = response.json()
    assert "assertion" in data["types"]
    assert data["count"] >= 1


async def should_return_403_when_list_types_without_reader_role(resources_client: AsyncClient):
    """Un JWT valide sans role reader/writer se voit refuse (403)."""
    response = await resources_client.get(
        f"{_API_PREFIX}/resources/types", headers=_auth_headers([])
    )
    assert response.status_code == 403


async def should_return_200_when_list_resources_with_reader(resources_client: AsyncClient):
    """Un reader recupere la liste paginee des resources."""
    from gsie_api.resources.service import ResourceService

    mock_response = ResourceListResponse(items=[], total=0, page=1, size=20)
    with patch.object(ResourceService, "list_resources", new=AsyncMock(return_value=mock_response)):
        response = await resources_client.get(
            f"{_API_PREFIX}/resources", headers=_auth_headers(["reader"])
        )
    assert response.status_code == 200
    assert response.json()["total"] == 0


async def should_return_200_when_list_resources_with_type_filter(resources_client: AsyncClient):
    """Le filtre par type passe la permission check sur ce type."""
    from gsie_api.resources.service import ResourceService

    mock_response = ResourceListResponse(
        items=[], total=0, page=1, size=20, type_filter="assertion"
    )
    with patch.object(ResourceService, "list_resources", new=AsyncMock(return_value=mock_response)):
        response = await resources_client.get(
            f"{_API_PREFIX}/resources?type=assertion", headers=_auth_headers(["reader"])
        )
    assert response.status_code == 200


async def should_return_403_when_list_resources_with_rgpd_type_without_role(
    resources_client: AsyncClient,
):
    """Un reader ne peut pas filtrer sur un type RGPD (consent)."""
    response = await resources_client.get(
        f"{_API_PREFIX}/resources?type=consent", headers=_auth_headers(["reader"])
    )
    assert response.status_code == 403


async def should_apply_rgpd_exclusion_when_type_filter_is_empty(
    resources_client: AsyncClient,
):
    """Un type vide (?type=) ne désactive pas l'exclusion RGPD.

    Le défaut d'origine : ``if type is not None`` traitait la chaîne vide
    comme un filtre explicite, sautant l'exclusion RGPD. Un simple reader
    pouvait alors lister consent et data_subject.
    """
    from gsie_api.resources.service import ResourceService

    # Arrange — mock du service pour capturer les arguments reçus
    mock_response = ResourceListResponse(items=[], total=0, page=1, size=20)
    mock_list = AsyncMock(return_value=mock_response)
    with patch.object(ResourceService, "list_resources", new=mock_list):
        response = await resources_client.get(
            f"{_API_PREFIX}/resources?type=", headers=_auth_headers(["reader"])
        )

    # Assert — l'exclusion RGPD doit rester active (excluded_types non vide)
    assert response.status_code == 200
    kwargs = mock_list.call_args.kwargs
    assert kwargs.get("excluded_types") != frozenset(), (
        "un type vide ne doit pas désactiver l'exclusion RGPD — "
        "un reader ne doit pas voir consent et data_subject"
    )


async def should_return_401_when_create_resource_without_token(resources_client: AsyncClient):
    """POST /resources sans token doit retourner 401."""
    response = await resources_client.post(
        f"{_API_PREFIX}/resources",
        json={"type": "assertion", "data": {"claim_kind": "relation", "lifecycle_status": "draft"}},
    )
    assert response.status_code == 401


async def should_return_201_when_create_resource_with_writer(resources_client: AsyncClient):
    """Un writer cree une resource avec succes (201)."""
    from gsie_api.resources.service import ResourceService

    mock_read = _mock_resource_read()
    with patch.object(ResourceService, "create", new=AsyncMock(return_value=mock_read)):
        response = await resources_client.post(
            f"{_API_PREFIX}/resources",
            json={
                "type": "assertion",
                "data": {"claim_kind": "relation", "lifecycle_status": "draft"},
            },
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 201
    assert response.json()["type"] == "assertion"


async def should_return_403_when_create_resource_with_reader_only(
    resources_client: AsyncClient,
):
    """Un reader ne peut pas ecrire (403)."""
    response = await resources_client.post(
        f"{_API_PREFIX}/resources",
        json={"type": "assertion", "data": {"claim_kind": "relation", "lifecycle_status": "draft"}},
        headers=_auth_headers(["reader"]),
    )
    assert response.status_code == 403


async def should_return_422_when_create_resource_validation_error(
    resources_client: AsyncClient,
):
    """Une erreur de validation metier retourne un 422 au corps stable."""
    from gsie_api.resources.service import ResourceService
    from gsie_api.resources.validators import ResourceValidationError

    error = ResourceValidationError("assertion", ["claim_kind invalide"])
    with patch.object(ResourceService, "create", new=AsyncMock(side_effect=error)):
        response = await resources_client.post(
            f"{_API_PREFIX}/resources",
            json={
                "type": "assertion",
                "data": {"claim_kind": "relation", "lifecycle_status": "draft"},
            },
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "resource_validation_failed"
    assert detail["resource_type"] == "assertion"


async def should_return_400_when_create_resource_unknown_type(resources_client: AsyncClient):
    """Un type inconnu du registre retourne 400 (ValueError)."""
    from gsie_api.resources.service import ResourceService

    with patch.object(
        ResourceService, "create", new=AsyncMock(side_effect=ValueError("Type inconnu"))
    ):
        response = await resources_client.post(
            f"{_API_PREFIX}/resources",
            json={"type": "unknown_type", "data": {}},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 400


async def should_return_404_when_get_resource_not_found(resources_client: AsyncClient):
    """GET /resources/{id} inexistant retourne 404."""
    from gsie_api.resources.service import ResourceService

    with patch.object(ResourceService, "get_type", new=AsyncMock(return_value=None)):
        response = await resources_client.get(
            f"{_API_PREFIX}/resources/{uuid4()}", headers=_auth_headers(["reader"])
        )
    assert response.status_code == 404


async def should_return_200_when_get_resource_found(resources_client: AsyncClient):
    """GET /resources/{id} existant retourne la resource."""
    from gsie_api.resources.service import ResourceService

    mock_read = _mock_resource_read()
    with (
        patch.object(ResourceService, "get_type", new=AsyncMock(return_value="assertion")),
        patch.object(ResourceService, "get", new=AsyncMock(return_value=mock_read)),
    ):
        response = await resources_client.get(
            f"{_API_PREFIX}/resources/{uuid4()}", headers=_auth_headers(["reader"])
        )
    assert response.status_code == 200
    assert response.json()["type"] == "assertion"


async def should_return_404_when_get_resource_found_then_deleted(resources_client: AsyncClient):
    """GET /resources/{id} — type trouve mais resource supprimee (get retourne None)."""
    from gsie_api.resources.service import ResourceService

    with (
        patch.object(ResourceService, "get_type", new=AsyncMock(return_value="assertion")),
        patch.object(ResourceService, "get", new=AsyncMock(return_value=None)),
    ):
        response = await resources_client.get(
            f"{_API_PREFIX}/resources/{uuid4()}", headers=_auth_headers(["reader"])
        )
    assert response.status_code == 404


async def should_return_403_when_get_resource_rgpd_without_role(resources_client: AsyncClient):
    """GET /resources/{id} sur un type RGPD sans rgpd_manager retourne 403."""
    from gsie_api.resources.service import ResourceService

    with patch.object(ResourceService, "get_type", new=AsyncMock(return_value="consent")):
        response = await resources_client.get(
            f"{_API_PREFIX}/resources/{uuid4()}", headers=_auth_headers(["reader"])
        )
    assert response.status_code == 403


async def should_return_404_when_update_resource_not_found(resources_client: AsyncClient):
    """PUT /resources/{id} inexistant retourne 404."""
    from gsie_api.resources.service import ResourceService

    with patch.object(ResourceService, "get_type", new=AsyncMock(return_value=None)):
        response = await resources_client.put(
            f"{_API_PREFIX}/resources/{uuid4()}",
            json={"data": {"claim_kind": "relation"}, "justification": "test"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 404


async def should_return_200_when_update_resource_success(resources_client: AsyncClient):
    """PUT /resources/{id} avec succes retourne la resource mise a jour."""
    from gsie_api.resources.service import ResourceService

    mock_read = _mock_resource_read()
    with (
        patch.object(ResourceService, "get_type", new=AsyncMock(return_value="assertion")),
        patch.object(ResourceService, "update", new=AsyncMock(return_value=mock_read)),
    ):
        response = await resources_client.put(
            f"{_API_PREFIX}/resources/{uuid4()}",
            json={"data": {"claim_kind": "relation"}, "justification": "test"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 200


async def should_return_422_when_update_resource_validation_error(
    resources_client: AsyncClient,
):
    """PUT /resources/{id} avec validation error retourne 422."""
    from gsie_api.resources.service import ResourceService
    from gsie_api.resources.validators import ResourceValidationError

    error = ResourceValidationError("assertion", ["champ invalide"])
    with (
        patch.object(ResourceService, "get_type", new=AsyncMock(return_value="assertion")),
        patch.object(ResourceService, "update", new=AsyncMock(side_effect=error)),
    ):
        response = await resources_client.put(
            f"{_API_PREFIX}/resources/{uuid4()}",
            json={"data": {"claim_kind": "relation"}, "justification": "test"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 422


async def should_return_400_when_update_resource_unknown_type(resources_client: AsyncClient):
    """PUT /resources/{id} — type inconnu du registre retourne 400."""
    from gsie_api.resources.service import ResourceService

    with (
        patch.object(ResourceService, "get_type", new=AsyncMock(return_value="assertion")),
        patch.object(
            ResourceService, "update", new=AsyncMock(side_effect=ValueError("Type inconnu"))
        ),
    ):
        response = await resources_client.put(
            f"{_API_PREFIX}/resources/{uuid4()}",
            json={"data": {"claim_kind": "relation"}, "justification": "test"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 400


async def should_return_404_when_update_resource_returns_none(resources_client: AsyncClient):
    """PUT /resources/{id} — type trouve mais update retourne None (404)."""
    from gsie_api.resources.service import ResourceService

    with (
        patch.object(ResourceService, "get_type", new=AsyncMock(return_value="assertion")),
        patch.object(ResourceService, "update", new=AsyncMock(return_value=None)),
    ):
        response = await resources_client.put(
            f"{_API_PREFIX}/resources/{uuid4()}",
            json={"data": {"claim_kind": "relation"}, "justification": "test"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 404


async def should_return_404_when_delete_resource_not_found(resources_client: AsyncClient):
    """DELETE /resources/{id} inexistant retourne 404."""
    from gsie_api.resources.service import ResourceService

    with patch.object(ResourceService, "get_type", new=AsyncMock(return_value=None)):
        response = await resources_client.delete(
            f"{_API_PREFIX}/resources/{uuid4()}", headers=_auth_headers(["writer"])
        )
    assert response.status_code == 404


async def should_return_204_when_delete_resource_success(resources_client: AsyncClient):
    """DELETE /resources/{id} avec succes retourne 204."""
    from gsie_api.resources.service import ResourceService

    with (
        patch.object(ResourceService, "get_type", new=AsyncMock(return_value="assertion")),
        patch.object(ResourceService, "delete", new=AsyncMock(return_value=True)),
    ):
        response = await resources_client.delete(
            f"{_API_PREFIX}/resources/{uuid4()}", headers=_auth_headers(["writer"])
        )
    assert response.status_code == 204


async def should_return_404_when_delete_resource_returns_false(resources_client: AsyncClient):
    """DELETE /resources/{id} — type trouve mais delete retourne False (404)."""
    from gsie_api.resources.service import ResourceService

    with (
        patch.object(ResourceService, "get_type", new=AsyncMock(return_value="assertion")),
        patch.object(ResourceService, "delete", new=AsyncMock(return_value=False)),
    ):
        response = await resources_client.delete(
            f"{_API_PREFIX}/resources/{uuid4()}", headers=_auth_headers(["writer"])
        )
    assert response.status_code == 404


async def should_return_403_when_delete_resource_with_reader_only(
    resources_client: AsyncClient,
):
    """Un reader ne peut pas supprimer (403 — action delete exige writer)."""
    from gsie_api.resources.service import ResourceService

    with patch.object(ResourceService, "get_type", new=AsyncMock(return_value="assertion")):
        response = await resources_client.delete(
            f"{_API_PREFIX}/resources/{uuid4()}", headers=_auth_headers(["reader"])
        )
    assert response.status_code == 403


async def should_return_404_when_list_revisions_not_found(resources_client: AsyncClient):
    """GET /resources/{id}/revisions inexistant retourne 404."""
    from gsie_api.resources.service import ResourceService

    with patch.object(ResourceService, "get_type", new=AsyncMock(return_value=None)):
        response = await resources_client.get(
            f"{_API_PREFIX}/resources/{uuid4()}/revisions", headers=_auth_headers(["reader"])
        )
    assert response.status_code == 404


async def should_return_200_when_list_revisions_found(resources_client: AsyncClient):
    """GET /resources/{id}/revisions existant retourne l'historique."""
    from gsie_api.resources.service import ResourceService

    mock_revisions = [_mock_revision_read()]
    with (
        patch.object(ResourceService, "get_type", new=AsyncMock(return_value="assertion")),
        patch.object(ResourceService, "list_revisions", new=AsyncMock(return_value=mock_revisions)),
    ):
        response = await resources_client.get(
            f"{_API_PREFIX}/resources/{uuid4()}/revisions", headers=_auth_headers(["reader"])
        )
    assert response.status_code == 200
    assert len(response.json()) == 1


async def should_return_403_when_list_revisions_rgpd_without_role(
    resources_client: AsyncClient,
):
    """GET /resources/{id}/revisions sur un type RGPD sans role retourne 403."""
    from gsie_api.resources.service import ResourceService

    with patch.object(ResourceService, "get_type", new=AsyncMock(return_value="consent")):
        response = await resources_client.get(
            f"{_API_PREFIX}/resources/{uuid4()}/revisions", headers=_auth_headers(["reader"])
        )
    assert response.status_code == 403


async def should_return_422_when_create_resource_missing_data_field(
    resources_client: AsyncClient,
):
    """POST /resources sans le champ data retourne 422 (validation Pydantic)."""
    response = await resources_client.post(
        f"{_API_PREFIX}/resources",
        json={"type": "assertion"},
        headers=_auth_headers(["writer"]),
    )
    assert response.status_code == 422


# ===========================================================================
# 2. Climate Router — observations Meteo-France
# ===========================================================================


async def should_return_200_when_climate_status(climate_client: AsyncClient):
    """GET /climate/status retourne 200 sans auth (info publique)."""
    response = await climate_client.get(f"{_API_PREFIX}/climate/status")
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "climate"
    assert data["status"] == "active"


async def should_return_200_when_climate_version(climate_client: AsyncClient):
    """GET /climate/version retourne la version du moteur."""
    response = await climate_client.get(f"{_API_PREFIX}/climate/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["backend"] == "synop"


async def should_return_401_when_climate_query_without_token(climate_client: AsyncClient):
    """POST /climate/query sans token retourne 401."""
    response = await climate_client.post(
        f"{_API_PREFIX}/climate/query",
        json={"station_id": "07510"},
    )
    assert response.status_code == 401


async def should_return_200_when_climate_query_success(climate_client: AsyncClient):
    """POST /climate/query avec succes retourne l'observation."""
    from gsie_api.engines.climate.engine import ClimateEngine
    from gsie_api.engines.climate.schemas import ObservationClimatique
    from gsie_api.engines.evidence.schemas import SourceReference, SourceType

    mock_obs = ObservationClimatique(
        requete_id=uuid4(),
        station_id="07510",
        nom_station="Toulouse",
        latitude=43.6,
        longitude=1.4,
        date_observation=datetime.now(UTC),
        temperature_c=25.0,
        source=SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Meteo-France",
            reference="https://meteofrance.fr",
        ),
    )
    with patch.object(ClimateEngine, "query", new=AsyncMock(return_value=mock_obs)):
        response = await climate_client.post(
            f"{_API_PREFIX}/climate/query",
            json={"station_id": "07510"},
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200


async def should_return_502_when_climate_query_engine_error(climate_client: AsyncClient):
    """POST /climate/query — ClimateEngineError retourne 502."""
    from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError

    with patch.object(
        ClimateEngine, "query", new=AsyncMock(side_effect=ClimateEngineError("API down"))
    ):
        response = await climate_client.post(
            f"{_API_PREFIX}/climate/query",
            json={"station_id": "07510"},
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 502


async def should_return_502_when_climate_danger_feux_error(climate_client: AsyncClient):
    """GET /climate/danger-feux — ClimateEngineError retourne 502."""
    from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError

    with patch.object(
        ClimateEngine, "get_danger_feux", new=AsyncMock(side_effect=ClimateEngineError("API down"))
    ):
        response = await climate_client.get(
            f"{_API_PREFIX}/climate/danger-feux",
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 502


async def should_return_200_when_climate_danger_feux_success(climate_client: AsyncClient):
    """GET /climate/danger-feux avec succes retourne la liste."""
    from gsie_api.engines.climate.engine import ClimateEngine

    with patch.object(ClimateEngine, "get_danger_feux", new=AsyncMock(return_value=[])):
        response = await climate_client.get(
            f"{_API_PREFIX}/climate/danger-feux",
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200


async def should_return_502_when_climate_climatologie_stations_error(
    climate_client: AsyncClient,
):
    """GET /climate/climatologie-stations — ClimateEngineError retourne 502."""
    from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError

    with patch.object(
        ClimateEngine,
        "list_stations_climatologie",
        new=AsyncMock(side_effect=ClimateEngineError("API down")),
    ):
        response = await climate_client.get(
            f"{_API_PREFIX}/climate/climatologie-stations?id_departement=31",
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 502


async def should_return_200_when_climate_climatologie_stations_success(
    climate_client: AsyncClient,
):
    """GET /climate/climatologie-stations avec succes retourne la liste."""
    from gsie_api.engines.climate.engine import ClimateEngine

    with patch.object(ClimateEngine, "list_stations_climatologie", new=AsyncMock(return_value=[])):
        response = await climate_client.get(
            f"{_API_PREFIX}/climate/climatologie-stations?id_departement=31",
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200


async def should_return_502_when_climate_climatologie_quotidienne_error(
    climate_client: AsyncClient,
):
    """POST /climate/climatologie-quotidienne — ClimateEngineError retourne 502."""
    from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError

    with patch.object(
        ClimateEngine,
        "get_climatologie_quotidienne",
        new=AsyncMock(side_effect=ClimateEngineError("API down")),
    ):
        response = await climate_client.post(
            f"{_API_PREFIX}/climate/climatologie-quotidienne",
            json={
                "id_station": "33042001",
                "date_deb_periode": "2026-01-01T00:00:00Z",
                "date_fin_periode": "2026-01-31T00:00:00Z",
            },
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 502


async def should_return_200_when_climate_climatologie_quotidienne_success(
    climate_client: AsyncClient,
):
    """POST /climate/climatologie-quotidienne avec succes retourne la liste."""
    from gsie_api.engines.climate.engine import ClimateEngine

    with patch.object(
        ClimateEngine, "get_climatologie_quotidienne", new=AsyncMock(return_value=[])
    ):
        response = await climate_client.post(
            f"{_API_PREFIX}/climate/climatologie-quotidienne",
            json={
                "id_station": "33042001",
                "date_deb_periode": "2026-01-01T00:00:00Z",
                "date_fin_periode": "2026-01-31T00:00:00Z",
            },
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200


async def should_return_502_when_climate_vigilance_error(climate_client: AsyncClient):
    """GET /climate/vigilance — ClimateEngineError retourne 502."""
    from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError

    with patch.object(
        ClimateEngine, "get_vigilance", new=AsyncMock(side_effect=ClimateEngineError("API down"))
    ):
        response = await climate_client.get(
            f"{_API_PREFIX}/climate/vigilance",
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 502


async def should_return_200_when_climate_vigilance_success(climate_client: AsyncClient):
    """GET /climate/vigilance avec succes retourne la liste."""
    from gsie_api.engines.climate.engine import ClimateEngine

    with patch.object(ClimateEngine, "get_vigilance", new=AsyncMock(return_value=[])):
        response = await climate_client.get(
            f"{_API_PREFIX}/climate/vigilance",
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200


async def should_return_502_when_climate_observations_horaires_error(
    climate_client: AsyncClient,
):
    """GET /climate/observations-horaires — ClimateEngineError retourne 502."""
    from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError

    with patch.object(
        ClimateEngine,
        "get_observations_horaires",
        new=AsyncMock(side_effect=ClimateEngineError("API down")),
    ):
        response = await climate_client.get(
            f"{_API_PREFIX}/climate/observations-horaires?id_departement=31",
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 502


async def should_return_200_when_climate_observations_horaires_success(
    climate_client: AsyncClient,
):
    """GET /climate/observations-horaires avec succes retourne la liste."""
    from gsie_api.engines.climate.engine import ClimateEngine

    with patch.object(ClimateEngine, "get_observations_horaires", new=AsyncMock(return_value=[])):
        response = await climate_client.get(
            f"{_API_PREFIX}/climate/observations-horaires?id_departement=31",
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200


async def should_return_502_when_climate_arome_temperature_error(climate_client: AsyncClient):
    """POST /climate/arome-temperature — ClimateEngineError retourne 502."""
    from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError

    with patch.object(
        ClimateEngine,
        "get_temperature_arome",
        new=AsyncMock(side_effect=ClimateEngineError("API down")),
    ):
        response = await climate_client.post(
            f"{_API_PREFIX}/climate/arome-temperature",
            json={
                "latitude": 43.6,
                "longitude": 1.4,
                "echeance": "2026-07-21T12:00:00Z",
            },
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 502


async def should_return_200_when_climate_arome_temperature_success(climate_client: AsyncClient):
    """POST /climate/arome-temperature avec succes retourne la temperature."""
    from gsie_api.engines.climate.engine import ClimateEngine
    from gsie_api.engines.climate.schemas import AromeTemperatureResult
    from gsie_api.engines.evidence.schemas import SourceReference, SourceType

    mock_result = AromeTemperatureResult(
        requete_id=uuid4(),
        latitude=43.6,
        longitude=1.4,
        echeance=datetime.now(UTC),
        temperature_c=25.0,
        run_modele="arome-france-1km",
        resolution_deg=0.01,
        source=SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Meteo-France",
            reference="https://meteofrance.fr",
        ),
    )
    with patch.object(
        ClimateEngine, "get_temperature_arome", new=AsyncMock(return_value=mock_result)
    ):
        response = await climate_client.post(
            f"{_API_PREFIX}/climate/arome-temperature",
            json={
                "latitude": 43.6,
                "longitude": 1.4,
                "echeance": "2026-07-21T12:00:00Z",
            },
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200


async def should_return_403_when_climate_query_without_reader_role(climate_client: AsyncClient):
    """POST /climate/query avec un JWT sans role reader retourne 403."""
    response = await climate_client.post(
        f"{_API_PREFIX}/climate/query",
        json={"station_id": "07510"},
        headers=_auth_headers([]),
    )
    assert response.status_code == 403


async def should_return_401_when_climate_query_and_ingest_without_token(
    climate_client: AsyncClient,
):
    """POST /climate/query-and-ingest sans token retourne 401."""
    response = await climate_client.post(
        f"{_API_PREFIX}/climate/query-and-ingest",
        json={"station_id": "07510"},
    )
    assert response.status_code == 401


async def should_return_502_when_climate_query_and_ingest_synop_fails(
    climate_client: AsyncClient,
):
    """POST /climate/query-and-ingest — SYNOP down retourne 502."""
    from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError

    with patch.object(
        ClimateEngine,
        "query_and_ingest",
        new=AsyncMock(side_effect=ClimateEngineError("SYNOP down")),
    ):
        response = await climate_client.post(
            f"{_API_PREFIX}/climate/query-and-ingest",
            json={"station_id": "07510"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 502


async def should_return_200_when_climate_query_and_ingest_success(
    climate_client: AsyncClient,
):
    """POST /climate/query-and-ingest avec succes retourne les resultats d'ingestion."""
    from gsie_api.engines.climate.engine import ClimateEngine
    from gsie_api.engines.climate.schemas import ClimateIngestResponse, ClimateIngestResult
    from gsie_api.engines.evidence.schemas import EvidenceLevel

    mock_response = ClimateIngestResponse(
        requete_id=uuid4(),
        station_id="07510",
        nom_station="BORDEAUX-MERIGNAC",
        date_observation=datetime.now(UTC),
        resultats=[
            ClimateIngestResult(
                nom="temperature_c",
                statut="quarantined",
                evidence_level=EvidenceLevel.D,
                connaissance_id=uuid4(),
                raison="Connaissance quarantine par l'Evidence Engine (niveau D)",
            )
        ],
    )
    with patch.object(ClimateEngine, "query_and_ingest", new=AsyncMock(return_value=mock_response)):
        response = await climate_client.post(
            f"{_API_PREFIX}/climate/query-and-ingest",
            json={"station_id": "07510"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 200
    body = response.json()
    assert body["resultats"][0]["nom"] == "temperature_c"
    assert body["resultats"][0]["statut"] == "quarantined"


async def should_return_200_when_climate_query_and_ingest_station_not_found(
    climate_client: AsyncClient,
):
    """POST /climate/query-and-ingest retourne null quand la station est introuvable."""
    from gsie_api.engines.climate.engine import ClimateEngine

    with patch.object(ClimateEngine, "query_and_ingest", new=AsyncMock(return_value=None)):
        response = await climate_client.post(
            f"{_API_PREFIX}/climate/query-and-ingest",
            json={"station_id": "99999"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 200
    assert response.json() is None


# ===========================================================================
# 3. Botanical Router — taxonomie GBIF/TAXREF
# ===========================================================================


async def should_return_200_when_botanical_status(botanical_client: AsyncClient):
    """GET /botanical/status retourne 200 sans auth."""
    response = await botanical_client.get(f"{_API_PREFIX}/botanical/status")
    assert response.status_code == 200
    assert response.json()["engine"] == "botanical"


async def should_return_200_when_botanical_version(botanical_client: AsyncClient):
    """GET /botanical/version retourne la version."""
    response = await botanical_client.get(f"{_API_PREFIX}/botanical/version")
    assert response.status_code == 200
    assert response.json()["backend"] == "postgresql"


async def should_return_401_when_botanical_query_without_token(botanical_client: AsyncClient):
    """POST /botanical/query sans token retourne 401."""
    response = await botanical_client.post(
        f"{_API_PREFIX}/botanical/query",
        json={"essence": "Quercus petraea"},
    )
    assert response.status_code == 401


async def should_return_502_when_botanical_query_engine_error(botanical_client: AsyncClient):
    """POST /botanical/query — BotanicalEngineError retourne 502."""
    from gsie_api.engines.botanical.engine import BotanicalEngine, BotanicalEngineError

    with patch.object(
        BotanicalEngine, "query", new=AsyncMock(side_effect=BotanicalEngineError("GBIF down"))
    ):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/query",
            json={"essence": "Quercus petraea"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 502


async def should_return_200_when_botanical_query_success(botanical_client: AsyncClient):
    """POST /botanical/query avec succes retourne les donnees botaniques."""
    from gsie_api.engines.botanical.engine import BotanicalEngine
    from gsie_api.engines.botanical.schemas import BotanicalData
    from gsie_api.engines.evidence.schemas import SourceReference, SourceType

    mock_data = BotanicalData(
        requete_id=uuid4(),
        especes=[],
        source=SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="GBIF",
            reference="https://gbif.org",
        ),
    )
    with patch.object(BotanicalEngine, "query", new=AsyncMock(return_value=mock_data)):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/query",
            json={"essence": "Quercus petraea"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 200


async def should_return_401_when_botanical_query_and_ingest_without_token(
    botanical_client: AsyncClient,
):
    """POST /botanical/query-and-ingest sans token retourne 401."""
    response = await botanical_client.post(
        f"{_API_PREFIX}/botanical/query-and-ingest",
        json={"essence": "Quercus petraea"},
    )
    assert response.status_code == 401


async def should_return_502_when_botanical_query_and_ingest_gbif_fails(
    botanical_client: AsyncClient,
):
    """POST /botanical/query-and-ingest — GBIF down retourne 502."""
    from gsie_api.engines.botanical.engine import BotanicalEngine, BotanicalEngineError

    with patch.object(
        BotanicalEngine,
        "query_and_ingest",
        new=AsyncMock(side_effect=BotanicalEngineError("GBIF down")),
    ):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/query-and-ingest",
            json={"essence": "Quercus petraea"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 502


async def should_return_200_when_botanical_query_and_ingest_success(
    botanical_client: AsyncClient,
):
    """POST /botanical/query-and-ingest avec succes retourne les resultats d'ingestion."""
    from gsie_api.engines.botanical.engine import BotanicalEngine
    from gsie_api.engines.botanical.schemas import BotanicalIngestResponse, BotanicalIngestResult
    from gsie_api.engines.evidence.schemas import EvidenceLevel

    mock_response = BotanicalIngestResponse(
        requete_id=uuid4(),
        resultats=[
            BotanicalIngestResult(
                nom_scientifique="Quercus petraea",
                statut="ingested",
                evidence_level=EvidenceLevel.B,
                connaissance_id=uuid4(),
                version=1,
            )
        ],
    )
    with patch.object(
        BotanicalEngine, "query_and_ingest", new=AsyncMock(return_value=mock_response)
    ):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/query-and-ingest",
            json={"essence": "Quercus petraea"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 200
    body = response.json()
    assert body["resultats"][0]["nom_scientifique"] == "Quercus petraea"
    assert body["resultats"][0]["statut"] == "ingested"


async def should_return_502_when_botanical_indigenat_error(botanical_client: AsyncClient):
    """POST /botanical/indigenat — BotanicalEngineError retourne 502."""
    from gsie_api.engines.botanical.engine import BotanicalEngine, BotanicalEngineError

    with patch.object(
        BotanicalEngine, "get_indigenat", side_effect=BotanicalEngineError("Dataset missing")
    ):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/indigenat",
            json={"cd_nom": 135, "code_ser": "A11"},
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 502


async def should_return_200_when_botanical_indigenat_success(botanical_client: AsyncClient):
    """POST /botanical/indigenat avec succes retourne le statut."""
    from gsie_api.engines.botanical.engine import BotanicalEngine
    from gsie_api.engines.botanical.schemas import (
        IndigenatResult,
        StatutIndigenatFrance,
        StatutIndigenatRegion,
    )
    from gsie_api.engines.evidence.schemas import SourceReference, SourceType

    mock_result = IndigenatResult(
        requete_id=uuid4(),
        nom_scientifique="Quercus petraea",
        statut_france=StatutIndigenatFrance.indigene,
        code_ser="A11",
        statut_ser=StatutIndigenatRegion.indigene,
        source=SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Bellifa et al. (2026)",
            reference="DOI 10.57745/DHJHGS",
        ),
    )
    with patch.object(BotanicalEngine, "get_indigenat", return_value=mock_result):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/indigenat",
            json={"cd_nom": 135, "code_ser": "A11"},
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200


async def should_return_502_when_botanical_taxref_error(botanical_client: AsyncClient):
    """POST /botanical/taxref — BotanicalEngineError retourne 502."""
    from gsie_api.engines.botanical.engine import BotanicalEngine, BotanicalEngineError

    with patch.object(
        BotanicalEngine,
        "resolve_taxref",
        new=AsyncMock(side_effect=BotanicalEngineError("TAXREF down")),
    ):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/taxref",
            json={"nom_scientifique": "Quercus petraea"},
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 502


async def should_return_200_when_botanical_taxref_success(botanical_client: AsyncClient):
    """POST /botanical/taxref avec succes retourne l'entree TAXREF."""
    from gsie_api.engines.botanical.engine import BotanicalEngine
    from gsie_api.engines.botanical.schemas import TaxonStatus, TaxrefResult
    from gsie_api.engines.evidence.schemas import SourceReference, SourceType

    mock_result = TaxrefResult(
        requete_id=uuid4(),
        cd_nom=135,
        nom_scientifique="Quercus petraea",
        nom_scientifique_complet="Quercus petraea (Matt.) Liebl.",
        statut=TaxonStatus.accepted,
        source=SourceReference(
            type_source=SourceType.referentiel_officiel,
            auteur="MNHN",
            reference="TAXREF v18.0",
        ),
    )
    with patch.object(BotanicalEngine, "resolve_taxref", new=AsyncMock(return_value=mock_result)):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/taxref",
            json={"nom_scientifique": "Quercus petraea"},
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200


async def should_return_401_when_botanical_taxref_and_ingest_without_token(
    botanical_client: AsyncClient,
):
    """POST /botanical/taxref-and-ingest sans token retourne 401."""
    response = await botanical_client.post(
        f"{_API_PREFIX}/botanical/taxref-and-ingest",
        json={"nom_scientifique": "Quercus petraea"},
    )
    assert response.status_code == 401


async def should_return_502_when_botanical_taxref_and_ingest_taxref_fails(
    botanical_client: AsyncClient,
):
    """POST /botanical/taxref-and-ingest — TAXREF down retourne 502."""
    from gsie_api.engines.botanical.engine import BotanicalEngine, BotanicalEngineError

    with patch.object(
        BotanicalEngine,
        "resolve_taxref_and_ingest",
        new=AsyncMock(side_effect=BotanicalEngineError("TAXREF down")),
    ):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/taxref-and-ingest",
            json={"nom_scientifique": "Quercus petraea"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 502


async def should_return_200_when_botanical_taxref_and_ingest_success(
    botanical_client: AsyncClient,
):
    """POST /botanical/taxref-and-ingest avec succes retourne le resultat d'ingestion."""
    from gsie_api.engines.botanical.engine import BotanicalEngine
    from gsie_api.engines.botanical.schemas import TaxrefIngestResponse, TaxrefIngestResult
    from gsie_api.engines.evidence.schemas import EvidenceLevel

    mock_response = TaxrefIngestResponse(
        requete_id=uuid4(),
        resultat=TaxrefIngestResult(
            cd_nom=135,
            nom_scientifique="Quercus petraea",
            statut="ingested",
            evidence_level=EvidenceLevel.B,
            connaissance_id=uuid4(),
            version=1,
        ),
    )
    with patch.object(
        BotanicalEngine, "resolve_taxref_and_ingest", new=AsyncMock(return_value=mock_response)
    ):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/taxref-and-ingest",
            json={"nom_scientifique": "Quercus petraea"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 200
    body = response.json()
    assert body["resultat"]["cd_nom"] == 135
    assert body["resultat"]["statut"] == "ingested"


async def should_return_200_when_botanical_taxref_and_ingest_finds_nothing(
    botanical_client: AsyncClient,
):
    """POST /botanical/taxref-and-ingest retourne resultat=null quand TAXREF ne trouve rien."""
    from gsie_api.engines.botanical.engine import BotanicalEngine
    from gsie_api.engines.botanical.schemas import TaxrefIngestResponse

    mock_response = TaxrefIngestResponse(requete_id=uuid4(), resultat=None)
    with patch.object(
        BotanicalEngine, "resolve_taxref_and_ingest", new=AsyncMock(return_value=mock_response)
    ):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/taxref-and-ingest",
            json={"nom_scientifique": "Taxon inexistant"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 200
    assert response.json()["resultat"] is None


async def should_return_401_when_botanical_identify_and_ingest_without_token(
    botanical_client: AsyncClient,
):
    """POST /botanical/identify-and-ingest sans token retourne 401."""
    response = await botanical_client.post(
        f"{_API_PREFIX}/botanical/identify-and-ingest",
        files={"file": ("test.jpg", b"\x89PNG fake", "image/jpeg")},
    )
    assert response.status_code == 401


async def should_return_400_when_botanical_identify_and_ingest_empty_file(
    botanical_client: AsyncClient,
):
    """POST /botanical/identify-and-ingest avec un fichier vide retourne 400."""
    response = await botanical_client.post(
        f"{_API_PREFIX}/botanical/identify-and-ingest",
        files={"file": ("test.jpg", b"", "image/jpeg")},
        headers=_auth_headers(["writer"]),
    )
    assert response.status_code == 400


async def should_return_400_when_botanical_identify_and_ingest_format_unsupported(
    botanical_client: AsyncClient,
):
    """POST /botanical/identify-and-ingest avec un format non supporté retourne 400."""
    response = await botanical_client.post(
        f"{_API_PREFIX}/botanical/identify-and-ingest",
        files={"file": ("test.gif", b"GIF89a", "image/gif")},
        headers=_auth_headers(["writer"]),
    )
    assert response.status_code == 400


async def should_return_502_when_botanical_identify_and_ingest_plantnet_fails(
    botanical_client: AsyncClient,
):
    """POST /botanical/identify-and-ingest — PlantNet down retourne 502."""
    from gsie_api.engines.botanical.engine import BotanicalEngine, BotanicalEngineError

    with patch.object(
        BotanicalEngine,
        "identify_and_ingest",
        new=AsyncMock(side_effect=BotanicalEngineError("PlantNet down")),
    ):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/identify-and-ingest",
            files={"file": ("test.jpg", b"\x89PNG fake", "image/jpeg")},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 502


async def should_return_200_when_botanical_identify_and_ingest_success(
    botanical_client: AsyncClient,
):
    """POST /botanical/identify-and-ingest avec succes retourne les resultats d'ingestion."""
    from gsie_api.engines.botanical.engine import BotanicalEngine
    from gsie_api.engines.botanical.schemas import PlantNetIngestResponse, PlantNetIngestResult
    from gsie_api.engines.evidence.schemas import EvidenceLevel

    mock_response = PlantNetIngestResponse(
        best_match="Quercus robur L.",
        resultats=[
            PlantNetIngestResult(
                nom_scientifique="Quercus robur",
                score=0.85,
                statut="quarantined",
                evidence_level=EvidenceLevel.D,
                connaissance_id=uuid4(),
                raison="Connaissance quarantine par l'Evidence Engine (niveau D)",
            )
        ],
    )
    with patch.object(
        BotanicalEngine, "identify_and_ingest", new=AsyncMock(return_value=mock_response)
    ):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/identify-and-ingest",
            files={"file": ("test.jpg", b"\x89PNG fake", "image/jpeg")},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 200
    body = response.json()
    assert body["resultats"][0]["nom_scientifique"] == "Quercus robur"
    assert body["resultats"][0]["statut"] == "quarantined"


async def should_return_200_when_botanical_identify_and_ingest_finds_nothing(
    botanical_client: AsyncClient,
):
    """POST /botanical/identify-and-ingest retourne null quand PlantNet ne trouve rien."""
    from gsie_api.engines.botanical.engine import BotanicalEngine

    with patch.object(BotanicalEngine, "identify_and_ingest", new=AsyncMock(return_value=None)):
        response = await botanical_client.post(
            f"{_API_PREFIX}/botanical/identify-and-ingest",
            files={"file": ("test.jpg", b"\x89PNG fake", "image/jpeg")},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 200
    assert response.json() is None


# ===========================================================================
# 4. GIS Router — cadastre + altitude IGN
# ===========================================================================


async def should_return_200_when_gis_status(gis_client: AsyncClient):
    """GET /gis/status retourne 200 sans auth."""
    response = await gis_client.get(f"{_API_PREFIX}/gis/status")
    assert response.status_code == 200
    assert response.json()["engine"] == "gis"


async def should_return_200_when_gis_version(gis_client: AsyncClient):
    """GET /gis/version retourne la version."""
    response = await gis_client.get(f"{_API_PREFIX}/gis/version")
    assert response.status_code == 200
    assert response.json()["backend"] == "postgis"


async def should_return_401_when_gis_cadastre_without_token(gis_client: AsyncClient):
    """POST /gis/cadastre/parcelle sans token retourne 401."""
    response = await gis_client.post(
        f"{_API_PREFIX}/gis/cadastre/parcelle",
        json={"code_insee": "31555", "section": "AH", "numero": "0040"},
    )
    assert response.status_code == 401


async def should_return_502_when_gis_cadastre_ign_error(gis_client: AsyncClient):
    """POST /gis/cadastre/parcelle — IGNClientError retourne 502."""
    from gsie_api.engines.gis.engine import GISEngine
    from gsie_api.engines.gis.ign_client import IGNClientError

    with patch.object(
        GISEngine,
        "get_parcelle_cadastre",
        new=AsyncMock(side_effect=IGNClientError("IGN down")),
    ):
        response = await gis_client.post(
            f"{_API_PREFIX}/gis/cadastre/parcelle",
            json={"code_insee": "31555", "section": "AH", "numero": "0040"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 502


async def should_return_200_when_gis_cadastre_success(gis_client: AsyncClient):
    """POST /gis/cadastre/parcelle avec succes retourne la parcelle."""
    from gsie_api.engines.evidence.schemas import SourceReference, SourceType
    from gsie_api.engines.gis.engine import GISEngine
    from gsie_api.engines.gis.schemas import GeoData

    mock_geodata = GeoData(
        requete_id=uuid4(),
        couches=[],
        source=SourceReference(
            type_source=SourceType.referentiel_officiel,
            auteur="IGN",
            reference="https://ign.fr/cadastre",
        ),
    )
    with patch.object(GISEngine, "get_parcelle_cadastre", new=AsyncMock(return_value=mock_geodata)):
        response = await gis_client.post(
            f"{_API_PREFIX}/gis/cadastre/parcelle",
            json={"code_insee": "31555", "section": "AH", "numero": "0040"},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 200


async def should_return_502_when_gis_altitude_engine_error(gis_client: AsyncClient):
    """POST /gis/altitude — GISEngineError retourne 502."""
    from gsie_api.engines.gis.engine import GISEngine, GISEngineError

    with patch.object(
        GISEngine, "get_altitude", new=AsyncMock(side_effect=GISEngineError("IGN down"))
    ):
        response = await gis_client.post(
            f"{_API_PREFIX}/gis/altitude",
            json={"latitude": 43.6, "longitude": 1.4},
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 502


async def should_return_200_when_gis_altitude_success(gis_client: AsyncClient):
    """POST /gis/altitude avec succes retourne l'altitude."""
    from gsie_api.engines.evidence.schemas import SourceReference, SourceType
    from gsie_api.engines.gis.engine import GISEngine
    from gsie_api.engines.gis.schemas import StationCharacteristics

    mock_alt = StationCharacteristics(
        requete_id=uuid4(),
        altitude_m=250.0,
        latitude=43.6,
        longitude=1.4,
        source=SourceReference(
            type_source=SourceType.referentiel_officiel,
            auteur="IGN",
            reference="https://ign.fr/altitude",
        ),
    )
    with patch.object(GISEngine, "get_altitude", new=AsyncMock(return_value=mock_alt)):
        response = await gis_client.post(
            f"{_API_PREFIX}/gis/altitude",
            json={"latitude": 43.6, "longitude": 1.4},
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200


# ===========================================================================
# 5. Pedology Router — SoilGrids
# ===========================================================================


async def should_return_200_when_pedology_status(pedology_client: AsyncClient):
    """GET /pedology/status retourne 200 sans auth."""
    response = await pedology_client.get(f"{_API_PREFIX}/pedology/status")
    assert response.status_code == 200
    assert response.json()["engine"] == "pedology"


async def should_return_200_when_pedology_version(pedology_client: AsyncClient):
    """GET /pedology/version retourne la version."""
    response = await pedology_client.get(f"{_API_PREFIX}/pedology/version")
    assert response.status_code == 200
    assert response.json()["backend"] == "soilgrids"


async def should_return_401_when_pedology_query_without_token(pedology_client: AsyncClient):
    """POST /pedology/query sans token retourne 401."""
    response = await pedology_client.post(
        f"{_API_PREFIX}/pedology/query",
        json={"latitude": 43.6, "longitude": 1.4},
    )
    assert response.status_code == 401


async def should_return_502_when_pedology_query_engine_error(pedology_client: AsyncClient):
    """POST /pedology/query — PedologyEngineError retourne 502."""
    from gsie_api.engines.pedology.engine import PedologyEngine, PedologyEngineError

    with patch.object(
        PedologyEngine, "query", new=AsyncMock(side_effect=PedologyEngineError("SoilGrids down"))
    ):
        response = await pedology_client.post(
            f"{_API_PREFIX}/pedology/query",
            json={"latitude": 43.6, "longitude": 1.4},
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 502


async def should_return_200_when_pedology_query_success(pedology_client: AsyncClient):
    """POST /pedology/query avec succes retourne les proprietes de sol."""
    from gsie_api.engines.evidence.schemas import SourceReference, SourceType
    from gsie_api.engines.pedology.engine import PedologyEngine
    from gsie_api.engines.pedology.schemas import PedologyData

    mock_data = PedologyData(
        requete_id=uuid4(),
        latitude=43.6,
        longitude=1.4,
        profondeur="0-5cm",
        caracteristiques=[],
        source=SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="ISRIC SoilGrids",
            reference="https://soilgrids.org",
        ),
    )
    with patch.object(PedologyEngine, "query", new=AsyncMock(return_value=mock_data)):
        response = await pedology_client.post(
            f"{_API_PREFIX}/pedology/query",
            json={"latitude": 43.6, "longitude": 1.4},
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200


async def should_return_401_when_pedology_query_and_ingest_without_token(
    pedology_client: AsyncClient,
):
    """POST /pedology/query-and-ingest sans token retourne 401."""
    response = await pedology_client.post(
        f"{_API_PREFIX}/pedology/query-and-ingest",
        json={"latitude": 43.6, "longitude": 1.4},
    )
    assert response.status_code == 401


async def should_return_502_when_pedology_query_and_ingest_soilgrids_fails(
    pedology_client: AsyncClient,
):
    """POST /pedology/query-and-ingest — SoilGrids down retourne 502."""
    from gsie_api.engines.pedology.engine import PedologyEngine, PedologyEngineError

    with patch.object(
        PedologyEngine,
        "query_and_ingest",
        new=AsyncMock(side_effect=PedologyEngineError("SoilGrids down")),
    ):
        response = await pedology_client.post(
            f"{_API_PREFIX}/pedology/query-and-ingest",
            json={"latitude": 43.6, "longitude": 1.4},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 502


async def should_return_200_when_pedology_query_and_ingest_success(
    pedology_client: AsyncClient,
):
    """POST /pedology/query-and-ingest avec succes retourne les resultats d'ingestion."""
    from gsie_api.engines.evidence.schemas import EvidenceLevel
    from gsie_api.engines.pedology.engine import PedologyEngine
    from gsie_api.engines.pedology.schemas import PedologyIngestResponse, PedologyIngestResult

    mock_response = PedologyIngestResponse(
        requete_id=uuid4(),
        latitude=43.6,
        longitude=1.4,
        profondeur="0-5cm",
        resultats=[
            PedologyIngestResult(
                nom="ph",
                statut="ingested",
                evidence_level=EvidenceLevel.B,
                connaissance_id=uuid4(),
                version=1,
            )
        ],
    )
    with patch.object(
        PedologyEngine, "query_and_ingest", new=AsyncMock(return_value=mock_response)
    ):
        response = await pedology_client.post(
            f"{_API_PREFIX}/pedology/query-and-ingest",
            json={"latitude": 43.6, "longitude": 1.4},
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 200
    body = response.json()
    assert body["resultats"][0]["nom"] == "ph"
    assert body["resultats"][0]["statut"] == "ingested"


# ===========================================================================
# 6. Forest Dynamics Router — dendrometrie geometrique
# ===========================================================================


async def should_return_200_when_forest_dynamics_status(forest_dynamics_client: AsyncClient):
    """GET /forest-dynamics/status retourne 200 sans auth."""
    response = await forest_dynamics_client.get(f"{_API_PREFIX}/forest-dynamics/status")
    assert response.status_code == 200
    assert response.json()["engine"] == "forest_dynamics"


async def should_return_200_when_forest_dynamics_version(forest_dynamics_client: AsyncClient):
    """GET /forest-dynamics/version retourne la version."""
    response = await forest_dynamics_client.get(f"{_API_PREFIX}/forest-dynamics/version")
    assert response.status_code == 200
    assert response.json()["backend"] == "geometrie"


async def should_return_401_when_forest_dynamics_dendrometrics_without_token(
    forest_dynamics_client: AsyncClient,
):
    """POST /forest-dynamics/dendrometrics sans token retourne 401."""
    response = await forest_dynamics_client.post(
        f"{_API_PREFIX}/forest-dynamics/dendrometrics",
        json={
            "etat_initial": {
                "essence_principale": "Quercus petraea",
                "age_moyen": 50,
                "densite_t_ha": 200,
                "diametre_moyen_cm": 30,
                "hauteur_moyenne_m": 20,
                "source_inventaire": _source_ref(),
            },
        },
    )
    assert response.status_code == 401


async def should_return_200_when_forest_dynamics_dendrometrics_success(
    forest_dynamics_client: AsyncClient,
):
    """POST /forest-dynamics/dendrometrics avec succes retourne les caracteristiques."""
    from gsie_api.engines.evidence.schemas import SourceReference, SourceType
    from gsie_api.engines.forest_dynamics.engine import ForestDynamicsEngine
    from gsie_api.engines.forest_dynamics.schemas import DendrometricResult

    mock_result = DendrometricResult(
        requete_id=uuid4(),
        peuplement_id=uuid4(),
        caracteristiques=[],
        source=SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Forest Dynamics Engine",
            reference="identite geometrique",
        ),
    )
    with patch.object(ForestDynamicsEngine, "compute_dendrometrics", return_value=mock_result):
        response = await forest_dynamics_client.post(
            f"{_API_PREFIX}/forest-dynamics/dendrometrics",
            json={
                "etat_initial": {
                    "essence_principale": "Quercus petraea",
                    "age_moyen": 50,
                    "densite_t_ha": 200,
                    "diametre_moyen_cm": 30,
                    "hauteur_moyenne_m": 20,
                    "source_inventaire": _source_ref(),
                },
            },
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200


# ===========================================================================
# 7. Diagnostic Router — diagnostic stationnel
# ===========================================================================


async def should_return_200_when_diagnostic_status(diagnostic_client: AsyncClient):
    """GET /diagnostic/status retourne 200 sans auth."""
    response = await diagnostic_client.get(f"{_API_PREFIX}/diagnostic/status")
    assert response.status_code == 200
    assert response.json()["engine"] == "diagnostic"


async def should_return_200_when_diagnostic_version(diagnostic_client: AsyncClient):
    """GET /diagnostic/version retourne la version."""
    response = await diagnostic_client.get(f"{_API_PREFIX}/diagnostic/version")
    assert response.status_code == 200
    assert response.json()["backend"] == "postgresql"


async def should_return_401_when_diagnostic_diagnostiquer_without_token(
    diagnostic_client: AsyncClient,
):
    """POST /diagnostic/diagnostiquer sans token retourne 401."""
    response = await diagnostic_client.post(
        f"{_API_PREFIX}/diagnostic/diagnostiquer",
        json=_minimal_diagnostic_request(),
    )
    assert response.status_code == 401


async def should_return_400_when_diagnostic_diagnostiquer_engine_error(
    diagnostic_client: AsyncClient,
):
    """POST /diagnostic/diagnostiquer — DiagnosticEngineError retourne 400."""
    from gsie_api.engines.diagnostic.engine import DiagnosticEngine, DiagnosticEngineError

    with patch.object(
        DiagnosticEngine,
        "diagnostiquer",
        new=AsyncMock(side_effect=DiagnosticEngineError("indiagnosticable")),
    ):
        response = await diagnostic_client.post(
            f"{_API_PREFIX}/diagnostic/diagnostiquer",
            json=_minimal_diagnostic_request(),
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 400


async def should_return_200_when_diagnostic_diagnostiquer_success(
    diagnostic_client: AsyncClient,
):
    """POST /diagnostic/diagnostiquer avec succes retourne le diagnostic."""
    from gsie_api.engines.diagnostic.engine import DiagnosticEngine
    from gsie_api.engines.diagnostic.schemas import Diagnostic
    from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
    from gsie_api.infrastructure.models.enums import (
        DiagnosticGlobalState,
        DiagnosticType,
        DiagnosticValidationStatus,
    )

    source = SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur="Rameau et al. (2008)",
        reference="Flore forestiere francaise, tome 1, IDF",
    )
    mock_diag = Diagnostic(
        statut_validation=DiagnosticValidationStatus.brouillon,
        diagnostic_id=uuid4(),
        requete_origine=uuid4(),
        station_id=uuid4(),
        type_diagnostic=DiagnosticType.stationnel,
        etat_global=DiagnosticGlobalState.vigueur_reduite,
        contraintes=[
            {
                "description": "pH acide",
                "domaine": "pedologique",
                "evidence_level": EvidenceLevel.B,
                "source": source,
            },
        ],
        atouts=[],
        risques=[],
        contradictions=[],
        confiance=0.8,
        etat_global_evidence_level=EvidenceLevel.B,
        evidence_level_plancher=EvidenceLevel.B,
        conclusions_source=[uuid4()],
        date_diagnostic=datetime.now(UTC),
    )
    with patch.object(DiagnosticEngine, "diagnostiquer", new=AsyncMock(return_value=mock_diag)):
        response = await diagnostic_client.post(
            f"{_API_PREFIX}/diagnostic/diagnostiquer",
            json=_minimal_diagnostic_request(),
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 200


def _minimal_diagnostic_request() -> dict[str, Any]:
    """Construit une requete de diagnostic valide minimale."""
    conclusion_id = str(uuid4())
    source = _source_ref()
    return {
        "requete_id": str(uuid4()),
        "station_id": str(uuid4()),
        "type_diagnostic": "stationnel",
        "conclusions": [
            {
                "conclusion_id": conclusion_id,
                "enonce": "Le pH de la station est dans la gamme du chene sessile.",
                "niveau_confiance": 0.8,
                "methode_confiance": "fournie_par_regle",
                "evidence_level_plancher": "B",
                "chaine_inference": [
                    {
                        "ordre": 1,
                        "regle_appliquee": "R_PH_CHENE_SESSILE",
                        "source_regle": source,
                        "premisses": ["pH <= 6.0"],
                        "conclusion_locale": (
                            "Le pH de la station est dans la gamme du chene sessile"
                        ),
                        "evidence_level": "B",
                    },
                ],
                "sources_utilisees": [source],
            },
        ],
        "qualifications": [
            {
                "conclusion_id": conclusion_id,
                "role": "contrainte",
                "domaine_element": "pedologique",
            },
        ],
        "etat_global": {
            "etat": "vigueur_reduite",
            "justification": "Contrainte pedologique.",
            "source": source,
            "evidence_level": "B",
        },
        "contradictions": [],
        "contexte": {
            "pedologie": {
                "source_moteur": "PEDOLOGY",
                "source": source,
                "evidence_level": "B",
                "valeurs": {"pH": 5.2},
            },
        },
    }


def _minimal_diagnostic_response() -> dict[str, Any]:
    """Construit une reponse de diagnostic valide minimale."""
    source = _source_ref()
    return {
        "statut_validation": "brouillon",
        "diagnostic_id": str(uuid4()),
        "requete_origine": str(uuid4()),
        "station_id": str(uuid4()),
        "type_diagnostic": "stationnel",
        "etat_global": "vigueur_reduite",
        "contraintes": [
            {
                "description": "pH acide",
                "domaine": "pedologique",
                "evidence_level": "B",
                "source": source,
            },
        ],
        "atouts": [],
        "risques": [],
        "contradictions": [],
        "confiance": 0.8,
        "evidence_level_plancher": "B",
        "conclusions_source": [str(uuid4())],
        "date_diagnostic": "2026-07-21T12:00:00Z",
    }


# ===========================================================================
# 8. Knowledge Router — graphe de connaissances
# ===========================================================================


async def should_return_200_when_knowledge_status(knowledge_client: AsyncClient):
    """GET /knowledge/status retourne 200 sans auth."""
    response = await knowledge_client.get(f"{_API_PREFIX}/knowledge/status")
    assert response.status_code == 200
    assert response.json()["engine"] == "knowledge"


async def should_return_200_when_knowledge_version(knowledge_client: AsyncClient):
    """GET /knowledge/version retourne la version."""
    response = await knowledge_client.get(f"{_API_PREFIX}/knowledge/version")
    assert response.status_code == 200
    assert response.json()["backend"] == "postgresql"


async def should_return_401_when_knowledge_ingest_without_token(knowledge_client: AsyncClient):
    """POST /knowledge/ingest sans token retourne 401."""
    response = await knowledge_client.post(
        f"{_API_PREFIX}/knowledge/ingest",
        json=_minimal_knowledge_ingest(),
    )
    assert response.status_code == 401


async def should_return_201_when_knowledge_ingest_success(knowledge_client: AsyncClient):
    """POST /knowledge/ingest avec succes retourne 201."""
    from gsie_api.engines.evidence.schemas import (
        EvidenceLevel,
        KnowledgeStatus,
        SourceReference,
        SourceType,
    )
    from gsie_api.engines.knowledge.engine import KnowledgeEngine
    from gsie_api.engines.knowledge.schemas import (
        DomaineScientifique,
        KnowledgeObject,
        KnowledgeType,
    )

    source = SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur="Test Author",
        reference="https://example.org/test",
    )
    mock_obj = KnowledgeObject(
        connaissance_id=uuid4(),
        type=KnowledgeType.concept,
        titre="Concept de test",
        description="Un concept de test pour la validation",
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
        contenu={"description": "test"},
        evidence_level=EvidenceLevel.B,
        source=source,
        statut=KnowledgeStatus.accepte,
        version=1,
        date_integration=datetime.now(UTC),
    )
    with patch.object(KnowledgeEngine, "ingest", new=AsyncMock(return_value=mock_obj)):
        response = await knowledge_client.post(
            f"{_API_PREFIX}/knowledge/ingest",
            json=_minimal_knowledge_ingest(),
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 201


async def should_return_400_when_knowledge_ingest_engine_error(knowledge_client: AsyncClient):
    """POST /knowledge/ingest — KnowledgeEngineError retourne 400."""
    from gsie_api.engines.knowledge.engine import KnowledgeEngine, KnowledgeEngineError

    with patch.object(
        KnowledgeEngine, "ingest", new=AsyncMock(side_effect=KnowledgeEngineError("deja present"))
    ):
        response = await knowledge_client.post(
            f"{_API_PREFIX}/knowledge/ingest",
            json=_minimal_knowledge_ingest(),
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 400


async def should_return_200_when_knowledge_query_success(knowledge_client: AsyncClient):
    """POST /knowledge/query avec succes retourne les resultats."""
    from gsie_api.engines.knowledge.engine import KnowledgeEngine
    from gsie_api.engines.knowledge.schemas import KnowledgeQueryResult

    mock_result = KnowledgeQueryResult(
        requete_id=uuid4(),
        connaissances=[],
        total=0,
        version_graph="1.0",
        page=1,
        page_size=20,
    )
    with patch.object(KnowledgeEngine, "query", new=AsyncMock(return_value=mock_result)):
        response = await knowledge_client.post(
            f"{_API_PREFIX}/knowledge/query",
            json={
                "requete_id": str(uuid4()),
                "type": "par_concept",
            },
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200


async def should_return_200_when_knowledge_revise_success(knowledge_client: AsyncClient):
    """POST /knowledge/revise avec succes retourne la connaissance revisee."""
    from gsie_api.engines.evidence.schemas import (
        EvidenceLevel,
        KnowledgeStatus,
        SourceReference,
        SourceType,
    )
    from gsie_api.engines.knowledge.engine import KnowledgeEngine
    from gsie_api.engines.knowledge.schemas import (
        DomaineScientifique,
        KnowledgeObject,
        KnowledgeType,
    )

    source = SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur="Test Author",
        reference="https://example.org/test",
    )
    mock_obj = KnowledgeObject(
        connaissance_id=uuid4(),
        type=KnowledgeType.concept,
        titre="Concept de test",
        description="Un concept de test pour la validation",
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
        contenu={"description": "test"},
        evidence_level=EvidenceLevel.B,
        source=source,
        statut=KnowledgeStatus.accepte,
        version=2,
        date_integration=datetime.now(UTC),
    )
    with patch.object(KnowledgeEngine, "revise", new=AsyncMock(return_value=mock_obj)):
        response = await knowledge_client.post(
            f"{_API_PREFIX}/knowledge/revise",
            json={
                "connaissance_id": str(uuid4()),
                "justification": "Mise a jour du contenu",
                "nouveau_contenu": {"cle": "valeur"},
            },
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 200


async def should_return_404_when_knowledge_revise_not_found(knowledge_client: AsyncClient):
    """POST /knowledge/revise — KnowledgeNotFoundError retourne 404."""
    from gsie_api.engines.knowledge.engine import KnowledgeEngine, KnowledgeNotFoundError

    with patch.object(
        KnowledgeEngine, "revise", new=AsyncMock(side_effect=KnowledgeNotFoundError("introuvable"))
    ):
        response = await knowledge_client.post(
            f"{_API_PREFIX}/knowledge/revise",
            json={
                "connaissance_id": str(uuid4()),
                "justification": "Mise a jour",
                "nouveau_contenu": {"cle": "valeur"},
            },
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 404


async def should_return_400_when_knowledge_revise_engine_error(knowledge_client: AsyncClient):
    """POST /knowledge/revise — KnowledgeEngineError retourne 400."""
    from gsie_api.engines.knowledge.engine import KnowledgeEngine, KnowledgeEngineError

    with patch.object(
        KnowledgeEngine,
        "revise",
        new=AsyncMock(side_effect=KnowledgeEngineError("aucun champ modifie")),
    ):
        response = await knowledge_client.post(
            f"{_API_PREFIX}/knowledge/revise",
            json={
                "connaissance_id": str(uuid4()),
                "justification": "Mise a jour",
                "nouveau_contenu": {"cle": "valeur"},
            },
            headers=_auth_headers(["writer"]),
        )
    assert response.status_code == 400


async def should_return_200_when_knowledge_stats_success(knowledge_client: AsyncClient):
    """GET /knowledge/stats avec succes retourne les statistiques."""
    from gsie_api.engines.knowledge.engine import KnowledgeEngine

    with patch.object(
        KnowledgeEngine, "stats", new=AsyncMock(return_value={"concept": 5, "regle": 3})
    ):
        response = await knowledge_client.get(
            f"{_API_PREFIX}/knowledge/stats",
            headers=_auth_headers(["reader"]),
        )
    assert response.status_code == 200
    assert response.json()["concept"] == 5


async def should_return_403_when_knowledge_ingest_with_reader_only(knowledge_client: AsyncClient):
    """POST /knowledge/ingest avec reader seul retourne 403 (write requis)."""
    response = await knowledge_client.post(
        f"{_API_PREFIX}/knowledge/ingest",
        json=_minimal_knowledge_ingest(),
        headers=_auth_headers(["reader"]),
    )
    assert response.status_code == 403


def _minimal_knowledge_ingest() -> dict[str, Any]:
    """Construit une requete d'ingestion de connaissance valide."""
    return {
        "connaissance_id": str(uuid4()),
        "contenu_normalise": {"description": "test"},
        "type": "concept",
        "titre": "Concept de test",
        "description": "Un concept de test pour la validation",
        "domaine_scientifique": "ecologie_forestiere_et_stationnelle",
        "evidence_level": "B",
        "source": _source_ref(),
        "statut": "accepte",
    }


def _minimal_knowledge_object() -> dict[str, Any]:
    """Construit un objet de connaissance valide pour les mocks."""
    return {
        "connaissance_id": str(uuid4()),
        "type": "concept",
        "titre": "Concept de test",
        "description": "Un concept de test pour la validation",
        "domaine_scientifique": "ecologie_forestiere_et_stationnelle",
        "contenu": {"description": "test"},
        "evidence_level": "B",
        "source": _source_ref(),
        "statut": "accepte",
        "version": 1,
        "date_integration": "2026-07-21T12:00:00Z",
    }


# ===========================================================================
# 9. Recommendation Router — refus du moteur en 400, pas 500
# ===========================================================================


async def should_return_400_when_recommendation_engine_raises(
    recommendation_client: AsyncClient,
):
    """Le refus d'un diagnostic introuvable remonte en 400, pas en 500.

    Un 500 dirait « panne » là où le refus est un jugement du moteur :
    l'appelant conclurait à un incident et réessaierait la même requête.
    """
    from gsie_api.engines.recommendation.engine import (
        RecommendationEngine,
        RecommendationEngineError,
    )

    # Arrange — le moteur lève une erreur métier (diagnostic introuvable)
    with patch.object(
        RecommendationEngine,
        "recommend",
        new=AsyncMock(side_effect=RecommendationEngineError("diagnostic introuvable")),
    ):
        response = await recommendation_client.post(
            f"{_API_PREFIX}/recommendation/recommend",
            json={
                "requete_id": str(uuid4()),
                "diagnostic_id": str(uuid4()),
                "objectif_forestier": "production",
            },
            headers=_auth_headers(["writer"]),
        )

    # Assert — 400 : le refus est un jugement, pas une panne
    assert response.status_code == 400, (
        "le refus du moteur est un jugement, pas une panne — "
        "un 500 ferait croire à un incident et masquerait le diagnostic manquant"
    )

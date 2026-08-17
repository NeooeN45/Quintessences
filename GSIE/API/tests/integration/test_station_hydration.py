"""Tests d'intégration — hydratation stationnelle sur PostgreSQL/PostGIS réel.

    GET  /api/v1/orchestration/stations/{station_id}/contexte
    POST /api/v1/orchestration/analyse   (contexte omis → hydraté, DEC-000072)

Ce que ces tests éprouvent, et qui est l'essentiel : la quarantaine est
étanche (une soumission non relue ne produit jamais un bloc), la provenance
est complète ou le bloc n'existe pas, et la preuve `analysis_run` conserve
le contexte exactement utilisé — rejouable, jamais recombiné.
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from geoalchemy2.elements import WKTElement
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.auth import create_access_token
from gsie_api.engines.evidence.schemas import EvidenceLevel
from gsie_api.engines.orchestration.hydration import (
    HydratationVideError,
    StationContexteHydrator,
    StationIntrouvableError,
)
from gsie_api.infrastructure.database import get_db
from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.infrastructure.models.enrichment import AnalysisRunModel
from gsie_api.infrastructure.models.field_intake import FieldIntakeModel
from gsie_api.infrastructure.models.spatial_temporal import PlaceModel
from tests.conftest import requires_docker

pytestmark = requires_docker

_TOKEN_WRITE = create_access_token(subject="test-hydration", claims={"roles": ["writer"]})
_TOKEN_READ = create_access_token(subject="test-hydration", claims={"roles": ["reader"]})
_HEADERS_WRITE = {"Authorization": f"Bearer {_TOKEN_WRITE}"}
_HEADERS_READ = {"Authorization": f"Bearer {_TOKEN_READ}"}

_SOURCE = {
    "type_source": "referentiel_officiel",
    "auteur": "INRAE (2008)",
    "date_publication": "2008",
    "reference": "Référentiel pédologique français, édition 2008",
}

_DATE = datetime(2026, 8, 16, 10, 0, tzinfo=UTC)


def _payload_station(*observations: dict) -> dict:
    return {
        "station": {
            "schema_version": "station_intake.v0.1",
            "context": {"parcelle": "farges"},
            "observations": list(observations),
        }
    }


def _observation(
    observation_type: str,
    value: float,
    *,
    unit: str,
    observed_at: datetime = _DATE,
) -> dict:
    return {
        "observation_type": observation_type,
        "value": value,
        "unit": unit,
        "method_id": "martelage-v1",
        "method_version": "1.0",
        "observed_at": observed_at.isoformat(),
    }


async def _creer_place(db_session: AsyncSession) -> UUID:
    """Place Lambert-93 réelle — le centroïde WGS84 est calculé par PostGIS."""
    place_id = uuid4()
    db_session.add(ResourceModel(id=place_id, type="place", gsie_id="PLC-FARGES-01"))
    db_session.add(
        PlaceModel(
            id=place_id,
            geometry=WKTElement("POINT(698000 6585000)", srid=2154),
            label="Parcelle de Farges",
            area_m2=18000.0,
        )
    )
    await db_session.flush()
    return place_id


def _intake(
    station_id: UUID,
    *,
    status: str,
    payload: dict,
    observed_at: datetime = _DATE,
    event: str = "evt-1",
) -> FieldIntakeModel:
    return FieldIntakeModel(
        id=uuid4(),
        submitted_by=uuid4(),
        application_key="geosylva-test",
        client_event_id=event,
        kind="observation",
        observed_at=observed_at,
        status=status,
        payload=payload,
        provenance={"application_key": "geosylva-test"},
        payload_hash="b" * 64,
        target_resource_id=station_id,
    )


def _corps_hydrate(station_id: UUID) -> dict:
    """Requête d'analyse sans contexte — la boucle visée par DEC-000072."""
    return {
        "requete_id": str(uuid4()),
        "station_id": str(station_id),
        "regles": [
            {
                "identifiant": "regle-densite-01",
                "condition": "peuplement_stems_per_ha > 200",
                "enonce_conclusion": "Le peuplement est dense.",
                "source": _SOURCE,
                "evidence_level": "B",
                "niveau_confiance": 0.85,
            }
        ],
        "qualifications": [
            {
                "identifiant_regle": "regle-densite-01",
                "role": "atout",
                "domaine_element": "sylvicole",
            }
        ],
        "etat_global": {
            "etat": "sain",
            "justification": "Peuplement suivi sur placette de Farges",
            "source": _SOURCE,
            "evidence_level": "B",
        },
        "question": "Quelle conduite sylvicole pour ce peuplement ?",
        "objectif_forestier": "production",
        "alternatives_demandees": True,
    }


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Client sur l'application réelle, session de test injectée."""
    from gsie_api.engines.orchestration.router import router

    async def _override() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# --- Hydrateur (service) ------------------------------------------------------


@pytest.mark.asyncio
async def should_hydrate_geographie_from_place_with_declared_level(
    db_session: AsyncSession,
) -> None:
    station_id = await _creer_place(db_session)

    resultat = await StationContexteHydrator(db_session).hydrate(
        station_id, niveaux_declares={"geographie": EvidenceLevel.E}
    )

    bloc = resultat.contexte.geographie
    assert bloc is not None
    assert bloc.valeurs["label"] == "Parcelle de Farges"
    assert bloc.valeurs["area_m2"] == 18000.0
    assert bloc.valeurs["longitude"] is not None
    assert bloc.valeurs["latitude"] is not None
    rapport = resultat.rapport
    assert rapport.ancre_place == station_id
    assert rapport.blocs_construits == ["geographie"]
    assert rapport.niveaux_declares_utilises == ["geographie"]


@pytest.mark.asyncio
async def should_refuse_unknown_station_with_named_identifier(
    db_session: AsyncSession,
) -> None:
    inconnu = uuid4()

    with pytest.raises(StationIntrouvableError, match=str(inconnu)):
        await StationContexteHydrator(db_session).hydrate(inconnu)


@pytest.mark.asyncio
async def should_refuse_place_without_declared_level_and_name_the_gap(
    db_session: AsyncSession,
) -> None:
    station_id = await _creer_place(db_session)

    with pytest.raises(HydratationVideError, match="geographie"):
        await StationContexteHydrator(db_session).hydrate(station_id)


@pytest.mark.asyncio
async def should_never_read_quarantined_intakes_for_values(
    db_session: AsyncSession,
) -> None:
    """La quarantaine est étanche : comptée, jamais lue pour ses valeurs."""
    station_id = await _creer_place(db_session)
    db_session.add(
        _intake(
            station_id,
            status="quarantined",
            payload=_payload_station(_observation("stems_per_ha", 300.0, unit="stems_per_ha")),
        )
    )
    await db_session.flush()

    # Sans niveau déclaré pour la géographie, aucun bloc n'est possible :
    # la soumission en quarantaine ne doit pas combler le manque.
    with pytest.raises(HydratationVideError):
        await StationContexteHydrator(db_session).hydrate(station_id)

    resultat = await StationContexteHydrator(db_session).hydrate(
        station_id, niveaux_declares={"geographie": EvidenceLevel.E}
    )
    assert resultat.rapport.soumissions_quarantaine_ignorees == 1
    assert resultat.contexte.peuplement is None


@pytest.mark.asyncio
async def should_hydrate_peuplement_from_most_recent_accepted_intake(
    db_session: AsyncSession,
) -> None:
    station_id = await _creer_place(db_session)
    db_session.add(
        _intake(
            station_id,
            status="accepted",
            event="evt-ancien",
            observed_at=datetime(2026, 3, 1, 9, 0, tzinfo=UTC),
            payload=_payload_station(_observation("stems_per_ha", 180.0, unit="stems_per_ha")),
        )
    )
    db_session.add(
        _intake(
            station_id,
            status="accepted",
            event="evt-recent",
            payload=_payload_station(_observation("stems_per_ha", 325.0, unit="stems_per_ha")),
        )
    )
    await db_session.flush()

    resultat = await StationContexteHydrator(db_session).hydrate(
        station_id,
        niveaux_declares={"peuplement": EvidenceLevel.E},
    )

    bloc = resultat.contexte.peuplement
    assert bloc is not None
    assert bloc.valeurs == {"stems_per_ha": 325.0}
    assert resultat.rapport.ancre_field_intake is not None


@pytest.mark.asyncio
async def should_report_non_compliant_station_payload(
    db_session: AsyncSession,
) -> None:
    station_id = await _creer_place(db_session)
    db_session.add(_intake(station_id, status="accepted", payload={"station": {"inattendu": True}}))
    await db_session.flush()

    with pytest.raises(HydratationVideError, match="station_intake.v0.1"):
        await StationContexteHydrator(db_session).hydrate(
            station_id,
            niveaux_declares={"peuplement": EvidenceLevel.E},
        )


# --- Endpoints -----------------------------------------------------------------


@pytest.mark.asyncio
async def should_preview_hydrated_contexte_over_http(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    station_id = await _creer_place(db_session)
    db_session.add(
        _intake(
            station_id,
            status="accepted",
            payload=_payload_station(
                _observation("stems_per_ha", 325.0, unit="stems_per_ha"),
                _observation("pH", 5.4, unit="pH"),
            ),
        )
    )
    await db_session.flush()

    reponse = await client.get(
        f"/api/v1/orchestration/stations/{station_id}/contexte",
        params={"niveau_geographie": "E", "niveau_peuplement": "E", "niveau_pedologie": "D"},
        headers=_HEADERS_READ,
    )

    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert corps["rapport"]["blocs_construits"] == ["geographie", "pedologie", "peuplement"]
    assert corps["contexte"]["peuplement"]["valeurs"] == {"stems_per_ha": 325.0}
    assert corps["contexte"]["pedologie"]["valeurs"] == {"pH": 5.4}


@pytest.mark.asyncio
async def should_return_404_when_previewing_unknown_station(client: AsyncClient) -> None:
    reponse = await client.get(
        f"/api/v1/orchestration/stations/{uuid4()}/contexte",
        headers=_HEADERS_READ,
    )

    assert reponse.status_code == 404


@pytest.mark.asyncio
async def should_return_400_when_preview_names_the_missing_provenance(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Station ancrée mais sans niveau déclaré : le refus nomme le manque."""
    station_id = await _creer_place(db_session)

    reponse = await client.get(
        f"/api/v1/orchestration/stations/{station_id}/contexte",
        headers=_HEADERS_READ,
    )

    assert reponse.status_code == 400
    assert "geographie" in reponse.json()["detail"]


@pytest.mark.asyncio
async def should_return_404_when_analysing_unknown_station(
    client: AsyncClient,
) -> None:
    corps = _corps_hydrate(uuid4())
    corps["niveaux_preuve_declares"] = {"peuplement": "E"}

    reponse = await client.post("/api/v1/orchestration/analyse", json=corps, headers=_HEADERS_WRITE)

    assert reponse.status_code == 404
    assert corps["station_id"] in reponse.json()["detail"]


@pytest.mark.asyncio
async def should_return_400_when_analyse_hydration_builds_no_block(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    station_id = await _creer_place(db_session)
    corps = _corps_hydrate(station_id)

    reponse = await client.post("/api/v1/orchestration/analyse", json=corps, headers=_HEADERS_WRITE)

    assert reponse.status_code == 400
    assert "aucun bloc constructible" in reponse.json()["detail"]


@pytest.mark.asyncio
async def should_reject_idempotency_key_different_from_requete_id(
    client: AsyncClient,
) -> None:
    reponse = await client.post(
        "/api/v1/orchestration/analyse",
        json=_corps_hydrate(uuid4()),
        headers={**_HEADERS_WRITE, "Idempotency-Key": str(uuid4())},
    )

    assert reponse.status_code == 400
    assert "Idempotency-Key" in reponse.json()["detail"]


@pytest.mark.asyncio
async def should_serve_status_and_version(client: AsyncClient) -> None:
    statut = await client.get("/api/v1/orchestration/status")
    version = await client.get("/api/v1/orchestration/version")

    assert statut.status_code == 200
    assert statut.json()["engine"] == "orchestration"
    assert version.status_code == 200
    assert version.json()["version"] != ""


@pytest.mark.asyncio
async def should_run_full_chain_with_hydrated_contexte_and_keep_proof(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """La boucle visée : GeoSylva n'envoie qu'un station_id et ses règles."""
    station_id = await _creer_place(db_session)
    db_session.add(
        _intake(
            station_id,
            status="accepted",
            payload=_payload_station(_observation("stems_per_ha", 325.0, unit="stems_per_ha")),
        )
    )
    await db_session.flush()

    corps_requete = _corps_hydrate(station_id)
    corps_requete["niveaux_preuve_declares"] = {"peuplement": "E"}

    reponse = await client.post(
        "/api/v1/orchestration/analyse", json=corps_requete, headers=_HEADERS_WRITE
    )

    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert corps["hydratation"]["blocs_construits"] == ["peuplement"]
    assert corps["hydratation"]["niveaux_declares_utilises"] == ["peuplement"]
    assert corps["inference"]["conclusions"], "la règle hydratée n'a pas conclu"

    preuve = await db_session.get(AnalysisRunModel, UUID(corps["analyse_id"]))
    assert preuve is not None
    assert preuve.contenu["hydratation"]["station_id"] == str(station_id)

    rejeu = await client.post(
        "/api/v1/orchestration/analyse", json=corps_requete, headers=_HEADERS_WRITE
    )
    assert rejeu.status_code == 200
    assert rejeu.json()["analyse_id"] == corps["analyse_id"]
    assert rejeu.json()["hydratation"] == corps["hydratation"]

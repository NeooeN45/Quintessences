"""Tests d'intégration — Botanical Engine (persistance PostgreSQL réelle).

Les appels à l'API GBIF sont mockés via respx avec les formes de
réponse réelles (vérifiées manuellement contre api.gbif.org le
2026-07-17) — pas de dépendance réseau dans les tests, mais pas de
donnée inventée : ces réponses sont des copies exactes d'appels réels.
"""

import pytest
import respx
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.botanical.engine import BotanicalEngine, BotanicalEngineError
from gsie_api.engines.botanical.gbif_client import (
    _SPECIES_MATCH_URL,
    _VERNACULAR_NAMES_URL_TEMPLATE,
    GBIFClient,
    GBIFClientError,
)
from gsie_api.engines.botanical.schemas import BotanicalQuery, TaxonStatus
from gsie_api.infrastructure.models.provenance import EntityAliasModel
from tests.conftest import requires_docker

pytestmark = requires_docker

# Réponses réelles capturées (api.gbif.org, 2026-07-17).
_MATCH_ACCEPTED = {
    "usageKey": 2880130,
    "scientificName": "Quercus petraea (Matt.) Liebl.",
    "canonicalName": "Quercus petraea",
    "rank": "SPECIES",
    "status": "ACCEPTED",
    "confidence": 99,
    "matchType": "EXACT",
    "family": "Fagaceae",
    "species": "Quercus petraea",
}

_MATCH_SYNONYM = {
    "usageKey": 2880250,
    "acceptedUsageKey": 7069116,
    "scientificName": "Quercus sessiliflora Salisb.",
    "canonicalName": "Quercus sessiliflora",
    "rank": "SPECIES",
    "status": "SYNONYM",
    "confidence": 97,
    "matchType": "EXACT",
    "family": "Fagaceae",
    "species": "Quercus petraea",
}

_MATCH_NONE = {"matchType": "NONE", "confidence": 0}

_VERNACULAR_RESPONSE = {
    "results": [{"taxonKey": 2880130, "vernacularName": "Chene sessile", "language": "fra"}]
}


def _vernacular_url(key: int) -> str:
    return _VERNACULAR_NAMES_URL_TEMPLATE.format(key=key)


@pytest.fixture
def engine(db_session: AsyncSession) -> BotanicalEngine:
    return BotanicalEngine(db_session, gbif_client=GBIFClient())


@respx.mock
async def test_query_accepted_taxon_persists_entity(
    engine: BotanicalEngine, db_session: AsyncSession
):
    """Un taxon accepté doit être résolu et persisté comme resource `entity`."""
    respx.get(_SPECIES_MATCH_URL).mock(return_value=Response(200, json=_MATCH_ACCEPTED))
    respx.get(_vernacular_url(2880130)).mock(return_value=Response(200, json=_VERNACULAR_RESPONSE))

    result = await engine.query(BotanicalQuery(essence="Quercus petraea"))

    assert len(result.especes) == 1
    espece = result.especes[0]
    assert espece.gbif_taxon_key == 2880130
    assert espece.nom_scientifique == "Quercus petraea"
    assert espece.nom_vernaculaire == "Chene sessile"
    assert espece.famille == "Fagaceae"
    assert espece.statut == TaxonStatus.accepted
    assert espece.synonymes == []
    assert espece.autecologie is None

    alias = (
        await db_session.execute(
            EntityAliasModel.__table__.select().where(EntityAliasModel.entity_id == espece.taxon_id)
        )
    ).first()
    assert alias is not None
    assert alias.namespace == "gbif"
    assert alias.external_id == "2880130"


@respx.mock
async def test_query_synonym_resolves_to_accepted_taxon(engine: BotanicalEngine):
    """Un synonyme doit être résolu vers le taxon accepté, avec le synonyme conservé."""
    respx.get(_SPECIES_MATCH_URL).mock(return_value=Response(200, json=_MATCH_SYNONYM))
    respx.get(_vernacular_url(7069116)).mock(return_value=Response(200, json={"results": []}))

    result = await engine.query(BotanicalQuery(essence="Quercus sessiliflora"))

    assert len(result.especes) == 1
    espece = result.especes[0]
    assert espece.gbif_taxon_key == 7069116
    assert espece.statut == TaxonStatus.synonym
    assert "Quercus sessiliflora Salisb." in espece.synonymes


@respx.mock
async def test_query_returns_empty_when_no_match(engine: BotanicalEngine):
    """Un nom sans correspondance GBIF doit retourner une liste vide — jamais un taxon inventé."""
    respx.get(_SPECIES_MATCH_URL).mock(return_value=Response(200, json=_MATCH_NONE))

    result = await engine.query(BotanicalQuery(essence="Nonexistus fakus"))

    assert result.especes == []


@respx.mock
async def test_query_raises_on_gbif_api_failure(engine: BotanicalEngine):
    """Une panne de l'API GBIF doit lever BotanicalEngineError, jamais une donnée par défaut."""
    respx.get(_SPECIES_MATCH_URL).mock(return_value=Response(503))

    with pytest.raises(BotanicalEngineError):
        await engine.query(BotanicalQuery(essence="Quercus petraea"))


@respx.mock
async def test_query_deduplicates_taxon_on_repeated_calls(
    engine: BotanicalEngine, db_session: AsyncSession
):
    """Interroger deux fois le même taxon ne doit pas créer deux entités (CON-010)."""
    respx.get(_SPECIES_MATCH_URL).mock(return_value=Response(200, json=_MATCH_ACCEPTED))
    respx.get(_vernacular_url(2880130)).mock(return_value=Response(200, json=_VERNACULAR_RESPONSE))

    first = await engine.query(BotanicalQuery(essence="Quercus petraea"))
    second = await engine.query(BotanicalQuery(essence="Quercus petraea"))

    assert first.especes[0].taxon_id == second.especes[0].taxon_id


def test_gbif_client_requires_no_api_key():
    """GBIFClient doit s'instancier sans configuration — API publique en lecture."""
    client = GBIFClient()
    assert client is not None


async def test_gbif_client_raises_on_network_error():
    """Une erreur HTTP doit lever GBIFClientError, pas une exception générique."""
    client = GBIFClient()
    with respx.mock:
        respx.get(_SPECIES_MATCH_URL).mock(return_value=Response(500))
        with pytest.raises(GBIFClientError):
            await client.match_species("Quercus petraea")


def test_return_engine_version():
    """version() doit retourner une chaîne non vide."""
    assert len(BotanicalEngine.version()) > 0

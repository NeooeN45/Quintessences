"""Tests unitaires — cas limites du Botanical Engine (couverture edge cases).

Cible les branches non couvertes par les suites existantes
(`test_botanical_indigenat.py`, `test_botanical_taxref.py`,
`tests/integration/test_botanical.py`) :

- statut GBIF/TAXREF inconnu du référentiel interne (repli `DOUBTFUL`,
  jamais une erreur — les valeurs de statut GBIF réelles sont plus
  nombreuses que `TaxonStatus`, ex. `HOMOTYPIC_SYNONYM`) ;
- panne de l'API GBIF sur la récupération du nom vernaculaire ;
- panne du dataset d'indigénat (fichier illisible) ;
- taxon absent du dataset d'indigénat ;
- valeurs de statut d'indigénat non conformes au référentiel interne.

Tests unitaires purs : aucune session PostgreSQL réelle, `AsyncSession`
et les clients HTTP (`GBIFClient`, `TaxrefClient`, `IndigenatLoader`)
sont mockés (`unittest.mock`).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest

from gsie_api.engines.botanical.engine import BotanicalEngine, BotanicalEngineError
from gsie_api.engines.botanical.gbif_client import GBIFClient, GBIFClientError
from gsie_api.engines.botanical.indigenat_loader import IndigenatLoader, IndigenatLoaderError
from gsie_api.engines.botanical.schemas import (
    BotanicalQuery,
    IndigenatQuery,
    TaxonStatus,
    TaxrefQuery,
)
from gsie_api.engines.botanical.taxref_client import TaxrefClient


class _NoOpSession:
    """Session factice — utilisée quand le chemin testé n'accède jamais à la base."""


def _make_session_with_existing_taxon(entity_id: object) -> MagicMock:
    """Session mockée simulant un taxon GBIF déjà persisté (`_get_or_create_taxon`).

    Évite de dépendre d'une vraie base PostgreSQL pour les tests qui
    doivent atteindre la fin de `BotanicalEngine.query()` : le taxon
    est trouvé dès la première requête `SELECT`, donc `add()`/`flush()`
    ne sont jamais appelés.
    """
    scalars_result = MagicMock()
    scalars_result.first.return_value = entity_id
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_result

    session = MagicMock()
    session.execute = AsyncMock(return_value=execute_result)
    return session


async def test_should_fallback_to_doubtful_status_when_gbif_status_is_unknown() -> None:
    """Un statut GBIF réel mais hors de `TaxonStatus` (ex. HOMOTYPIC_SYNONYM) doit devenir DOUBTFUL.

    GBIF Backbone Taxonomy retourne davantage de valeurs de statut
    (`HOMOTYPIC_SYNONYM`, `HETEROTYPIC_SYNONYM`, `MISAPPLIED`...) que
    le référentiel interne `TaxonStatus` (ACCEPTED/SYNONYM/DOUBTFUL) —
    jamais une exception, jamais un statut inventé (ADR-009).
    """
    entity_id = uuid4()
    gbif_client = AsyncMock(spec=GBIFClient)
    gbif_client.match_species.return_value = {
        "usageKey": 3040000,
        "canonicalName": "Quercus robur",
        "species": "Quercus robur",
        "scientificName": "Quercus robur L.",
        "status": "HOMOTYPIC_SYNONYM",
        "family": "Fagaceae",
        "confidence": 95,
        "matchType": "EXACT",
    }
    gbif_client.get_vernacular_name.return_value = "Chêne pédonculé"
    session = _make_session_with_existing_taxon(entity_id)
    engine = BotanicalEngine(session, gbif_client=gbif_client)  # type: ignore[arg-type]

    result = await engine.query(BotanicalQuery(essence="Quercus robur"))

    assert len(result.especes) == 1
    assert result.especes[0].statut == TaxonStatus.doubtful
    assert result.especes[0].taxon_id == entity_id


async def test_should_raise_botanical_engine_error_when_vernacular_name_fetch_fails() -> None:
    """Une panne GBIF sur la récupération du nom vernaculaire doit lever BotanicalEngineError.

    Doit être levée avant toute persistance (`_get_or_create_taxon`
    n'est jamais appelé) — pas de donnée partiellement écrite.
    """
    gbif_client = AsyncMock(spec=GBIFClient)
    gbif_client.match_species.return_value = {
        "usageKey": 2880130,
        "canonicalName": "Quercus petraea",
        "species": "Quercus petraea",
        "scientificName": "Quercus petraea (Matt.) Liebl.",
        "status": "ACCEPTED",
        "family": "Fagaceae",
        "confidence": 99,
        "matchType": "EXACT",
    }
    gbif_client.get_vernacular_name.side_effect = GBIFClientError("panne GBIF vernacularNames")
    engine = BotanicalEngine(_NoOpSession(), gbif_client=gbif_client)  # type: ignore[arg-type]

    with pytest.raises(BotanicalEngineError):
        await engine.query(BotanicalQuery(essence="Quercus petraea"))


def test_should_raise_botanical_engine_error_when_indigenat_dataset_unreadable() -> None:
    """Une panne du chargeur d'indigénat (fichier illisible) doit lever BotanicalEngineError."""
    loader = Mock(spec=IndigenatLoader)
    loader.find.side_effect = IndigenatLoaderError("dataset Bellifa et al. 2026 introuvable")
    engine = BotanicalEngine(_NoOpSession(), indigenat_loader=loader)  # type: ignore[arg-type]

    with pytest.raises(BotanicalEngineError):
        engine.get_indigenat(IndigenatQuery(requete_id=uuid4(), cd_nom=79319, code_ser="A11"))


def test_should_return_none_and_log_when_taxon_absent_from_indigenat_dataset() -> None:
    """Un taxon absent du dataset d'indigénat doit retourner None — jamais un statut approximé."""
    loader = Mock(spec=IndigenatLoader)
    loader.find.return_value = None
    engine = BotanicalEngine(_NoOpSession(), indigenat_loader=loader)  # type: ignore[arg-type]

    result = engine.get_indigenat(
        IndigenatQuery(
            requete_id=uuid4(), nom_scientifique="Taxon totalement inexistant", code_ser="A11"
        )
    )

    assert result is None


def test_should_raise_botanical_engine_error_when_indigenat_statut_values_are_invalid() -> None:
    """Un statut d'indigénat hors référentiel doit lever BotanicalEngineError.

    Le dataset Bellifa et al. 2026 est un TSV externe versionné —
    toute valeur de statut hors de `StatutIndigenatFrance` /
    `StatutIndigenatRegion` doit être signalée, jamais silencieusement
    ignorée ou approximée (ADR-009).
    """
    loader = Mock(spec=IndigenatLoader)
    loader.find.return_value = {
        "Nom_scientifique": "Fagus sylvatica L., 1753",
        "Nom_vernaculaire": "Hêtre commun",
        "Famille": "Fagaceae",
        "CD_NOM_TaxRefv18.0": "100282",
        "Indigenat FR": "VALEUR_NON_CONFORME",
        "A11": "1",
    }
    engine = BotanicalEngine(_NoOpSession(), indigenat_loader=loader)  # type: ignore[arg-type]

    with pytest.raises(BotanicalEngineError):
        engine.get_indigenat(IndigenatQuery(requete_id=uuid4(), cd_nom=100282, code_ser="A11"))


async def test_should_fallback_to_doubtful_status_when_taxref_status_is_unknown() -> None:
    """Une entrée TAXREF sans `taxonomicStatus` connu doit devenir DOUBTFUL, jamais planter.

    Le miroir GBIF de TAXREF (SCI-003) peut renvoyer des entrées sans
    champ `taxonomicStatus` exploitable — repli sur DOUBTFUL, jamais un
    statut inventé (ADR-009).
    """
    taxref_client = AsyncMock(spec=TaxrefClient)
    taxref_client.search.return_value = {
        "taxonID": "521658",
        "canonicalName": "Quercus petraea",
        "species": "Quercus petraea",
        "scientificName": "Quercus petraea (Matt.) Liebl., 1784",
        "family": "Fagaceae",
        "vernacularNames": [],
    }
    engine = BotanicalEngine(_NoOpSession(), taxref_client=taxref_client)  # type: ignore[arg-type]

    result = await engine.resolve_taxref(
        TaxrefQuery(requete_id=uuid4(), nom_scientifique="Quercus petraea")
    )

    assert result is not None
    assert result.statut == TaxonStatus.doubtful
    assert result.cd_nom == 521658


# ===========================================================================
# Couverture complémentaire — query() no-match, GBIFClientError, _inserer_taxon
# ===========================================================================


async def test_should_return_empty_especes_when_gbif_returns_none() -> None:
    """query() doit retourner une liste vide quand GBIF ne trouve aucune correspondance."""
    gbif_client = AsyncMock(spec=GBIFClient)
    gbif_client.match_species.return_value = None
    engine = BotanicalEngine(_NoOpSession(), gbif_client=gbif_client)  # type: ignore[arg-type]

    result = await engine.query(BotanicalQuery(requete_id=uuid4(), essence="Nonexistent species"))

    assert result.especes == []


async def test_should_raise_botanical_engine_error_when_gbif_match_fails() -> None:
    """query() doit lever BotanicalEngineError quand match_species lève GBIFClientError."""
    gbif_client = AsyncMock(spec=GBIFClient)
    gbif_client.match_species.side_effect = GBIFClientError("API indisponible")
    engine = BotanicalEngine(_NoOpSession(), gbif_client=gbif_client)  # type: ignore[arg-type]

    with pytest.raises(BotanicalEngineError, match="API indisponible"):
        await engine.query(BotanicalQuery(requete_id=uuid4(), essence="Quercus robur"))


async def test_should_include_synonym_when_status_is_synonym() -> None:
    """query() doit inclure le nom scientifique dans les synonymes quand statut=synonym."""
    entity_id = uuid4()
    gbif_client = AsyncMock(spec=GBIFClient)
    gbif_client.match_species.return_value = {
        "usageKey": 3040000,
        "acceptedUsageKey": 2878688,
        "canonicalName": "Quercus sessiliflora",
        "species": "Quercus sessiliflora",
        "scientificName": "Quercus sessiliflora Mert. & W.D.J.Koch",
        "status": "SYNONYM",
        "family": "Fagaceae",
        "matchType": "EXACT",
    }
    gbif_client.get_vernacular_name.return_value = "Chêne sessile"

    session = _make_session_with_existing_taxon(entity_id)
    engine = BotanicalEngine(session, gbif_client=gbif_client)  # type: ignore[arg-type]

    result = await engine.query(BotanicalQuery(requete_id=uuid4(), essence="Quercus sessiliflora"))

    assert len(result.especes) == 1
    assert result.especes[0].statut == TaxonStatus.synonym
    assert "Quercus sessiliflora" in result.especes[0].synonymes[0]


async def test_should_create_taxon_when_not_existing() -> None:
    """_get_or_create_taxon doit insérer un nouveau taxon quand aucun n'existe."""

    # Session mockée : première lecture retourne None, insertion réussit
    scalars_result_none = MagicMock()
    scalars_result_none.first.return_value = None
    execute_result_none = MagicMock()
    execute_result_none.scalars.return_value = scalars_result_none

    session = MagicMock()
    session.execute = AsyncMock(return_value=execute_result_none)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.begin_nested = MagicMock()

    # Mock begin_nested comme un context manager async
    class _FakeNested:
        async def __aenter__(self):
            return None

        async def __aexit__(self, *args):
            return False

    session.begin_nested.return_value = _FakeNested()

    gbif_client = AsyncMock(spec=GBIFClient)
    engine = BotanicalEngine(session, gbif_client=gbif_client)  # type: ignore[arg-type]

    result = await engine._get_or_create_taxon(2878688)

    # Un nouvel entity_id a été généré
    assert result is not None
    # session.add a été appelé (resource + entity + alias)
    assert session.add.call_count >= 3


async def test_should_use_concurrent_taxon_on_integrity_error() -> None:
    """_get_or_create_taxon doit récupérer le taxon créé par une requête concurrente."""
    from sqlalchemy.exc import IntegrityError

    concurrent_id = uuid4()

    # Session mockée : première lecture None, IntegrityError sur insert,
    # seconde lecture retourne le concurrent
    scalars_none = MagicMock()
    scalars_none.first.return_value = None
    scalars_concurrent = MagicMock()
    scalars_concurrent.first.return_value = concurrent_id
    execute_none = MagicMock()
    execute_none.scalars.return_value = scalars_none
    execute_concurrent = MagicMock()
    execute_concurrent.scalars.return_value = scalars_concurrent

    session = MagicMock()
    # Premier execute retourne None, second retourne concurrent
    session.execute = AsyncMock(side_effect=[execute_none, execute_concurrent])
    session.add = MagicMock()
    session.flush = AsyncMock(side_effect=IntegrityError("duplicate", {}, Exception()))

    # Mock begin_nested pour lever IntegrityError
    class _FakeNestedIntegrity:
        async def __aenter__(self):
            return None

        async def __aexit__(self, *args):
            raise IntegrityError("duplicate", {}, Exception())

    session.begin_nested.return_value = _FakeNestedIntegrity()

    gbif_client = AsyncMock(spec=GBIFClient)
    engine = BotanicalEngine(session, gbif_client=gbif_client)  # type: ignore[arg-type]

    result = await engine._get_or_create_taxon(2878688)

    assert result == concurrent_id


async def test_should_raise_when_integrity_error_without_concurrent() -> None:
    """_get_or_create_taxon doit lever si IntegrityError sans concurrent trouvé."""
    from sqlalchemy.exc import IntegrityError

    scalars_none = MagicMock()
    scalars_none.first.return_value = None
    execute_none = MagicMock()
    execute_none.scalars.return_value = scalars_none

    session = MagicMock()
    session.execute = AsyncMock(side_effect=[execute_none, execute_none])
    session.add = MagicMock()
    session.flush = AsyncMock()

    class _FakeNestedIntegrity:
        async def __aenter__(self):
            return None

        async def __aexit__(self, *args):
            raise IntegrityError("duplicate", {}, Exception())

    session.begin_nested.return_value = _FakeNestedIntegrity()

    gbif_client = AsyncMock(spec=GBIFClient)
    engine = BotanicalEngine(session, gbif_client=gbif_client)  # type: ignore[arg-type]

    with pytest.raises(IntegrityError):
        await engine._get_or_create_taxon(2878688)

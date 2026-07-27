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
        IndigenatQuery(requete_id=uuid4(), nom_scientifique="Taxon totalement inexistant", code_ser="A11")
    )

    assert result is None


def test_should_raise_botanical_engine_error_when_indigenat_statut_values_are_invalid() -> None:
    """Des valeurs de statut d'indigénat non conformes au référentiel doivent lever BotanicalEngineError.

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

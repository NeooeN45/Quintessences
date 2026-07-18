"""Tests unitaires — IndigenatLoader et BotanicalEngine.get_indigenat().

Utilise un échantillon réel (2 lignes extraites du dataset Bellifa et
al. 2026, DOI 10.57745/DHJHGS, `tests/fixtures/indigenat_sample.tab`)
— pas de donnée inventée. Un test dédié pointe vers le dataset complet
réel téléchargé dans `GSIE/DATASETS/` pour vérifier l'intégration de
bout en bout.
"""

from pathlib import Path
from uuid import uuid4

import pytest

from gsie_api.engines.botanical.engine import BotanicalEngine, BotanicalEngineError
from gsie_api.engines.botanical.indigenat_loader import (
    DEFAULT_DATASET_PATH,
    IndigenatLoader,
    IndigenatLoaderError,
)
from gsie_api.engines.botanical.schemas import (
    IndigenatQuery,
    StatutIndigenatFrance,
    StatutIndigenatRegion,
)

_FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "indigenat_sample.tab"


@pytest.fixture
def loader() -> IndigenatLoader:
    return IndigenatLoader(dataset_path=_FIXTURE_PATH)


def test_find_by_cd_nom(loader: IndigenatLoader):
    """Abies alba (cd_nom réel 79319) doit être retrouvé exactement."""
    row = loader.find(cd_nom=79319, nom_scientifique=None)

    assert row is not None
    assert row["Nom_scientifique"] == "Abies alba Mill., 1768"


def test_find_by_exact_full_name(loader: IndigenatLoader):
    """Le nom complet exact (avec citation d'auteur) doit être retrouvé."""
    row = loader.find(cd_nom=None, nom_scientifique="Quercus petraea (Matt.) Liebl., 1784")

    assert row is not None
    assert row["CD_NOM_TaxRefv18.0"] == "521658"


def test_find_by_binome_fallback(loader: IndigenatLoader):
    """Le binôme seul (« Quercus petraea », sans citation d'auteur) doit aboutir."""
    row = loader.find(cd_nom=None, nom_scientifique="Quercus petraea")

    assert row is not None
    assert row["CD_NOM_TaxRefv18.0"] == "521658"


def test_find_returns_none_for_unknown_taxon(loader: IndigenatLoader):
    """Un taxon absent doit retourner None — jamais une ligne approximée."""
    assert loader.find(cd_nom=None, nom_scientifique="Taxon inexistant") is None
    assert loader.find(cd_nom=999999, nom_scientifique=None) is None


def test_raises_on_missing_dataset_file():
    """Un chemin de dataset invalide doit lever IndigenatLoaderError, pas planter silencieusement."""
    loader = IndigenatLoader(dataset_path=Path("/chemin/inexistant.tab"))

    with pytest.raises(IndigenatLoaderError):
        loader.find(cd_nom=1, nom_scientifique=None)


class _NoOpSession:
    """Session factice — get_indigenat() n'accède jamais à la base."""


def test_engine_get_indigenat_returns_real_status(loader: IndigenatLoader):
    """BotanicalEngine.get_indigenat() doit renvoyer le vrai statut Abies alba / A11."""
    engine = BotanicalEngine(_NoOpSession(), indigenat_loader=loader)  # type: ignore[arg-type]

    result = engine.get_indigenat(
        IndigenatQuery(requete_id=uuid4(), cd_nom=79319, code_ser="A11")
    )

    assert result is not None
    assert result.nom_scientifique == "Abies alba Mill., 1768"
    assert result.nom_vernaculaire == "Sapin pectiné"
    assert result.famille == "Pinaceae"
    assert result.statut_france == StatutIndigenatFrance.indigene
    assert result.statut_ser == StatutIndigenatRegion.exogene_ou_absent  # A11 = "0" pour Abies alba
    assert result.source.auteur == "Bellifa M. et al. (2026)"


def test_engine_get_indigenat_quercus_petraea_probablement_indigene(loader: IndigenatLoader):
    """Quercus petraea en A11 doit renvoyer le statut réel « 1 » (indigène), pas approximé."""
    engine = BotanicalEngine(_NoOpSession(), indigenat_loader=loader)  # type: ignore[arg-type]

    result = engine.get_indigenat(
        IndigenatQuery(requete_id=uuid4(), nom_scientifique="Quercus petraea", code_ser="A11")
    )

    assert result is not None
    assert result.statut_ser == StatutIndigenatRegion.indigene


def test_engine_get_indigenat_returns_none_for_unknown_code_ser(loader: IndigenatLoader):
    """Un code SER absent des colonnes doit retourner None, pas lever d'exception."""
    engine = BotanicalEngine(_NoOpSession(), indigenat_loader=loader)  # type: ignore[arg-type]

    result = engine.get_indigenat(
        IndigenatQuery(requete_id=uuid4(), cd_nom=79319, code_ser="Z99")
    )

    assert result is None


def test_engine_get_indigenat_raises_when_taxon_and_ser_both_missing():
    """Requête invalide — cd_nom et nom_scientifique absents — doit être rejetée par le schéma."""
    with pytest.raises(ValueError):
        IndigenatQuery(requete_id=uuid4(), code_ser="A11")


def test_real_dataset_file_is_present_and_loadable():
    """Vérifie que le vrai dataset téléchargé (pas la fixture) est bien intégré au dépôt."""
    if not DEFAULT_DATASET_PATH.exists():
        pytest.skip(f"Dataset réel non présent localement : {DEFAULT_DATASET_PATH}")

    loader = IndigenatLoader()
    row = loader.find(cd_nom=79319, nom_scientifique=None)

    assert row is not None
    assert row["Nom_scientifique"] == "Abies alba Mill., 1768"

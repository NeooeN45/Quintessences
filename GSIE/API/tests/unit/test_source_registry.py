"""Tests unitaires — registre des sources scientifiques (SCI-001)."""

import pytest

from gsie_api.governance import (
    SCIENTIFIC_SOURCES,
    SourceIngestionForbiddenError,
    SourceLegalStatus,
    get_source,
    require_ingestible,
)


def test_get_source_returns_none_for_unknown_identifier():
    """Un identifiant inconnu doit retourner None, pas lever d'exception."""
    assert get_source("source-totalement-inconnue") is None


def test_require_ingestible_accepts_open_confirmed_source():
    """Une source OPEN_CONFIRMED (ex. Météo-France) doit passer la porte."""
    entry = require_ingestible("meteofrance-portail-api")

    assert entry.statut_juridique == SourceLegalStatus.open_confirmed


def test_require_ingestible_rejects_permission_required_source():
    """ClimEssences (PERMISSION_REQUIRED) ne doit jamais passer la porte automatiquement."""
    with pytest.raises(SourceIngestionForbiddenError):
        require_ingestible("climessences")


def test_require_ingestible_rejects_licensed_partner_source():
    """BioClimSol (LICENSED_PARTNER) ne doit jamais passer la porte automatiquement."""
    with pytest.raises(SourceIngestionForbiddenError):
        require_ingestible("bioclimsol")


def test_require_ingestible_rejects_unknown_source():
    """Une source absente du registre doit être bloquée, pas silencieusement acceptée."""
    with pytest.raises(SourceIngestionForbiddenError):
        require_ingestible("source-jamais-cataloguee")


def test_all_registered_sources_have_a_url_and_license():
    """Chaque entrée du registre doit porter au minimum une URL et une licence non vides."""
    assert len(SCIENTIFIC_SOURCES) > 0
    for identifiant, entry in SCIENTIFIC_SOURCES.items():
        assert entry.identifiant == identifiant
        assert entry.url
        assert entry.licence


def test_climessences_and_bioclimsol_are_not_ingestible_by_design():
    """Verrou juridique du corpus sylvicole SS3 : ces 2 sources doivent rester bloquées."""
    assert SCIENTIFIC_SOURCES["climessences"].statut_juridique == (
        SourceLegalStatus.permission_required
    )
    assert SCIENTIFIC_SOURCES["bioclimsol"].statut_juridique == (
        SourceLegalStatus.licensed_partner
    )

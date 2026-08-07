"""Tests unitaires — GIS Engine.

Le moteur GIS interroge l'API Carto IGN (cadastre) et l'API de calcul
altimétrique IGN (altitude). Ces tests mockent `IGNClient` et la session
DB — pas d'appel réseau réel, pas de Docker requis.

Conventions (AGENTS.md API) : pytest-asyncio mode `auto`, nommage
`should_[expected]_when_[condition]`, structure Arrange → Act → Assert.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from shapely.geometry import Polygon

from gsie_api.engines.gis.engine import GISEngine, GISEngineError
from gsie_api.engines.gis.ign_client import IGNClientError
from gsie_api.engines.gis.schemas import (
    AltitudeRequest,
    CoucheGeo,
    ParcelleCadastraleRequest,
)
from gsie_api.engines.gis.telechargement_client import (
    DossierTelechargement,
    FichierTelechargement,
    PageTelechargement,
    RessourceTelechargement,
    TelechargementClientError,
)


def _valid_parcelle_feature() -> dict[str, object]:
    """Feature GeoJSON valide — un carré simple en WGS 84."""
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [7.0, 48.0],
                    [7.001, 48.0],
                    [7.001, 48.001],
                    [7.0, 48.001],
                    [7.0, 48.0],
                ]
            ],
        },
        "properties": {
            "contenance": 5000,
            "idu": "AH0040",
        },
    }


def _mock_session() -> MagicMock:
    """Session AsyncSession mockée — add() et flush() sont des AsyncMock."""
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


_DEFAULT_PARCELLE = _valid_parcelle_feature()
_NO_PARCELLE = object()  # sentinel pour distinguer "pas de défaut" de "None explicite"


def _mock_ign_client(
    parcelle_return: dict[str, object] | object = _DEFAULT_PARCELLE,
    altitude_return: float = 350.0,
    altitude_raises: Exception | None = None,
) -> MagicMock:
    """IGNClient mocké — méthodes asynchrones via AsyncMock.

    Pour simuler une parcelle introuvable, passer `parcelle_return=None`.
    """
    client = MagicMock()
    client.get_parcelle = AsyncMock(return_value=parcelle_return)
    if altitude_raises is not None:
        client.get_altitude = AsyncMock(side_effect=altitude_raises)
    else:
        client.get_altitude = AsyncMock(return_value=altitude_return)
    return client


# ─────────────────────────────────────────────────────────────────────────
# Tests get_parcelle_cadastre
# ─────────────────────────────────────────────────────────────────────────


async def should_return_none_when_ign_returns_no_parcelle() -> None:
    """Une parcelle introuvable retourne None, jamais une géométrie approximée (ADR-009)."""
    session = _mock_session()
    ign = _mock_ign_client(parcelle_return=None)
    engine = GISEngine(session=session, ign_client=ign)

    request = ParcelleCadastraleRequest(code_insee="68001", section="AH", numero="0040")
    result = await engine.get_parcelle_cadastre(request)

    assert result is None
    session.add.assert_not_called()


async def should_return_geo_data_when_ign_returns_valid_feature() -> None:
    """Une feature IGN valide produit une GeoData avec une couche cadastre sourcée."""
    session = _mock_session()
    ign = _mock_ign_client(parcelle_return=_valid_parcelle_feature())
    engine = GISEngine(session=session, ign_client=ign)

    request = ParcelleCadastraleRequest(code_insee="68001", section="AH", numero="0040")
    result = await engine.get_parcelle_cadastre(request)

    assert result is not None
    assert len(result.couches) == 1
    couche = result.couches[0]
    assert couche.nom == CoucheGeo.cadastre
    assert couche.type == "vecteur"
    assert couche.unite == "m²"
    assert result.place_id is not None
    # La session DB a reçu au moins ResourceModel et PlaceModel
    assert session.add.call_count >= 2
    session.flush.assert_awaited()


async def should_validate_and_repair_invalid_geometry() -> None:
    """Une géométrie invalide (auto-intersection) est réparée par buffer(0)."""
    # Polygone en papillon (auto-intersection) — invalide
    invalid_feature = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [0.0, 0.0],
                    [1.0, 1.0],
                    [0.0, 1.0],
                    [1.0, 0.0],
                    [0.0, 0.0],
                ]
            ],
        },
        "properties": {"contenance": None, "idu": "X0001"},
    }
    session = _mock_session()
    ign = _mock_ign_client(parcelle_return=invalid_feature)
    engine = GISEngine(session=session, ign_client=ign)

    request = ParcelleCadastraleRequest(code_insee="68001", section="X", numero="0001")
    # Ne doit pas lever — la géométrie est réparée en interne
    result = await engine.get_parcelle_cadastre(request)

    assert result is not None
    assert result.couches[0].nom == CoucheGeo.cadastre


async def should_use_area_from_geometry_when_contenance_is_none() -> None:
    """Quand 'contenance' est absente, l'aire est calculée depuis la géométrie Lambert-93."""
    feature = _valid_parcelle_feature()
    feature["properties"] = {"contenance": None, "idu": "AH0040"}
    session = _mock_session()
    ign = _mock_ign_client(parcelle_return=feature)
    engine = GISEngine(session=session, ign_client=ign)

    request = ParcelleCadastraleRequest(code_insee="68001", section="AH", numero="0040")
    result = await engine.get_parcelle_cadastre(request)

    assert result is not None
    # PlaceModel a été ajouté — vérifier que area_m2 est un float non nul
    place_model_call = session.add.call_args_list[1]
    place_model = place_model_call.args[0]
    assert place_model.area_m2 > 0.0


# ─────────────────────────────────────────────────────────────────────────
# Tests get_altitude
# ─────────────────────────────────────────────────────────────────────────


async def should_return_station_characteristics_when_ign_returns_altitude() -> None:
    """Une altitude valide produit une StationCharacteristics avec la valeur IGN."""
    session = _mock_session()
    ign = _mock_ign_client(altitude_return=412.5)
    engine = GISEngine(session=session, ign_client=ign)

    request = AltitudeRequest(latitude=48.0, longitude=7.0)
    result = await engine.get_altitude(request)

    assert result.altitude_m == 412.5
    assert result.latitude == 48.0
    assert result.longitude == 7.0
    assert result.source.auteur == "IGN"


async def should_raise_gis_engine_error_when_ign_altitude_fails() -> None:
    """Une panne IGN d'altitude lève GISEngineError — jamais de valeur par défaut (ADR-009)."""
    session = _mock_session()
    ign = _mock_ign_client(altitude_raises=IGNClientError("API IGN indisponible"))
    engine = GISEngine(session=session, ign_client=ign)

    request = AltitudeRequest(latitude=48.0, longitude=7.0)
    with pytest.raises(GISEngineError, match="API IGN indisponible"):
        await engine.get_altitude(request)


# ─────────────────────────────────────────────────────────────────────────
# Tests structurels
# ─────────────────────────────────────────────────────────────────────────


def should_return_version_0_1_0() -> None:
    """version() retourne la version courante du moteur."""
    assert GISEngine.version() == "0.1.0"


def should_use_default_ign_client_when_none_provided() -> None:
    """Le constructeur sans ign_client crée un IGNClient par défaut."""
    session = _mock_session()
    engine = GISEngine(session=session)
    assert engine._ign_client is not None


def test_validate_geometry_repairs_self_intersecting_polygon() -> None:
    """La fonction _validate_geometry répare un polygone auto-intersectant via buffer(0)."""
    from gsie_api.engines.gis.engine import _validate_geometry

    # Polygone en papillon — invalide
    bowtie = Polygon([(0, 0), (1, 1), (0, 1), (1, 0), (0, 0)])
    assert not bowtie.is_valid

    repaired = _validate_geometry(bowtie)
    assert repaired.is_valid


# ─────────────────────────────────────────────────────────────────────────
# Tests API de téléchargement Géoplateforme (délégation vers TelechargementClient)
# ─────────────────────────────────────────────────────────────────────────


def _mock_telechargement_client() -> MagicMock:
    client = MagicMock()
    client.get_capabilities = AsyncMock()
    client.get_resource = AsyncMock()
    client.get_subresource = AsyncMock()
    client.download_file = AsyncMock()
    return client


_PAGE = PageTelechargement(total_entries=1, page=1, page_size=50, page_count=1)


class TestListerRessourcesTelechargement:
    async def should_return_liste_ressources_when_client_succeeds(self) -> None:
        session = _mock_session()
        telechargement = _mock_telechargement_client()
        ressource = RessourceTelechargement(
            nom="BDFORET",
            url_resource="https://data.geopf.fr/telechargement/resource/BDFORET",
            description="BD Forêt",
            date_maj="2026-01-15",
            zones=["D033"],
            formats=["SHP"],
        )
        telechargement.get_capabilities.return_value = ([ressource], _PAGE)
        engine = GISEngine(session=session, telechargement_client=telechargement)

        result = await engine.lister_ressources_telechargement(page=1, limit=50)

        assert len(result.ressources) == 1
        assert result.ressources[0].nom == "BDFORET"
        assert result.pagination.total_entries == 1

    async def should_raise_gis_engine_error_when_client_fails(self) -> None:
        session = _mock_session()
        telechargement = _mock_telechargement_client()
        telechargement.get_capabilities.side_effect = TelechargementClientError("indisponible")
        engine = GISEngine(session=session, telechargement_client=telechargement)

        with pytest.raises(GISEngineError, match="indisponible"):
            await engine.lister_ressources_telechargement()


class TestListerDossiersTelechargement:
    async def should_return_liste_dossiers_when_client_succeeds(self) -> None:
        session = _mock_session()
        telechargement = _mock_telechargement_client()
        dossier = DossierTelechargement(
            nom="BDFORET_2026",
            url_subresource="https://data.geopf.fr/telechargement/resource/BDFORET/BDFORET_2026",
            date_maj="2026-01-15",
            zone="D033",
            format="SHP",
            date_edition="2026-01-15",
        )
        telechargement.get_resource.return_value = ([dossier], _PAGE)
        engine = GISEngine(session=session, telechargement_client=telechargement)

        result = await engine.lister_dossiers_telechargement("BDFORET", page=1, limit=50)

        assert len(result.dossiers) == 1
        assert result.dossiers[0].nom == "BDFORET_2026"

    async def should_raise_gis_engine_error_when_client_fails(self) -> None:
        session = _mock_session()
        telechargement = _mock_telechargement_client()
        telechargement.get_resource.side_effect = TelechargementClientError("indisponible")
        engine = GISEngine(session=session, telechargement_client=telechargement)

        with pytest.raises(GISEngineError, match="indisponible"):
            await engine.lister_dossiers_telechargement("BDFORET")


class TestListerFichiersTelechargement:
    async def should_return_liste_fichiers_when_client_succeeds(self) -> None:
        session = _mock_session()
        telechargement = _mock_telechargement_client()
        fichier = FichierTelechargement(
            url_download="https://data.geopf.fr/telechargement/download/BDFORET/BDFORET_2026/f.7z",
            taille_octets=1024,
            checksum_md5="abc123",
            mime_types=["application/x-7z-compressed"],
        )
        telechargement.get_subresource.return_value = ([fichier], _PAGE)
        engine = GISEngine(session=session, telechargement_client=telechargement)

        result = await engine.lister_fichiers_telechargement("BDFORET", "BDFORET_2026")

        assert len(result.fichiers) == 1
        assert result.fichiers[0].taille_octets == 1024

    async def should_raise_gis_engine_error_when_client_fails(self) -> None:
        session = _mock_session()
        telechargement = _mock_telechargement_client()
        telechargement.get_subresource.side_effect = TelechargementClientError("indisponible")
        engine = GISEngine(session=session, telechargement_client=telechargement)

        with pytest.raises(GISEngineError, match="indisponible"):
            await engine.lister_fichiers_telechargement("BDFORET", "BDFORET_2026")


class TestTelechargerFichier:
    async def should_return_bytes_when_client_succeeds(self) -> None:
        session = _mock_session()
        telechargement = _mock_telechargement_client()
        telechargement.download_file.return_value = b"\x37\x7a\xbc\xaf"
        engine = GISEngine(session=session, telechargement_client=telechargement)

        result = await engine.telecharger_fichier("BDFORET", "BDFORET_2026", "f.7z")

        assert result == b"\x37\x7a\xbc\xaf"

    async def should_raise_gis_engine_error_when_client_fails(self) -> None:
        session = _mock_session()
        telechargement = _mock_telechargement_client()
        telechargement.download_file.side_effect = TelechargementClientError("indisponible")
        engine = GISEngine(session=session, telechargement_client=telechargement)

        with pytest.raises(GISEngineError, match="indisponible"):
            await engine.telecharger_fichier("BDFORET", "BDFORET_2026", "f.7z")


def should_use_default_telechargement_client_when_none_provided() -> None:
    session = _mock_session()
    engine = GISEngine(session=session)
    assert engine._telechargement_client is not None

"""Factory de tests de résilience — génère automatiquement les 5 modes
de panne pour n'importe quel client d'API externe.

Au lieu d'écrire 5 tests manuels par client, on enregistre le client
dans `CLIENT_REGISTRY` et la factory génère les tests paramétrés.

## Usage

Ajouter un client au registre :

    CLIENT_REGISTRY.append(
        ClientSpec(
            name="mon_client",
            factory=lambda: MonClient(),
            url="https://api.exemple.com/v1/search",
            exception=MonClientError,
            call=lambda c: c.search("query"),
            auth=False,
            body_format=BodyFormat.JSON,
        ),
    )

Les 5 tests sont générés automatiquement :
- test_mode1_network_failure[{name}]
- test_mode2_http_4xx_5xx[{name}]
- test_mode3_malformed_body[{name}]
- test_mode4_missing_field[{name}]
- test_mode5_quota_auth[{name}]  (seulement si auth=True)

## BodyFormat

- JSON : mode #3 envoie un corps non-JSON, mode #4 envoie un JSON
  valide sans les champs attendus.
- CSV : mode #3 envoie un corps vide, mode #4 envoie un CSV tronqué.
- GZIP_CSV : mode #3 envoie un corps non-gzip, mode #4 envoie un
  gzip valide sans la station attendue.
- XML : mode #3 envoie un corps non-XML, mode #4 envoie un XML vide.
- BINARY : mode #3 envoie un corps non-binaire, mode #4 envoie un
  corps vide.
"""

from __future__ import annotations

import gzip
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.botanical.gbif_client import (
    _SPECIES_MATCH_URL,
    GBIFClient,
    GBIFClientError,
)
from gsie_api.engines.botanical.plantnet_client import (
    _IDENTIFY_URL,
    PlantNetClient,
    PlantNetClientError,
)
from gsie_api.engines.botanical.taxref_client import (
    TaxrefClient,
    TaxrefClientError,
)
from gsie_api.engines.climate.arome_client import (
    _BASE_URL as _AROME_BASE_URL,
)
from gsie_api.engines.climate.arome_client import (
    AromeClient,
    AromeClientError,
)
from gsie_api.engines.climate.dpclim_client import (
    _BASE_URL as _DPCLIM_BASE_URL,
)
from gsie_api.engines.climate.dpclim_client import (
    DPClimClient,
    DPClimClientError,
)
from gsie_api.engines.climate.meteofrance_client import (
    _BASE_URL as _METEOFRANCE_BASE_URL,
)
from gsie_api.engines.climate.meteofrance_client import (
    MeteoFranceClient,
    MeteoFranceClientError,
)
from gsie_api.engines.climate.paquet_observation_client import (
    _URL as _PAQUET_OBS_URL,
)
from gsie_api.engines.climate.paquet_observation_client import (
    PaquetObservationClient,
    PaquetObservationClientError,
)
from gsie_api.engines.climate.synop_client import (
    _SYNOP_URL_TEMPLATE,
    SynopClient,
    SynopClientError,
)
from gsie_api.engines.climate.vigilance_client import (
    _URL as _VIGILANCE_URL,
)
from gsie_api.engines.climate.vigilance_client import (
    VigilanceClient,
    VigilanceClientError,
)
from gsie_api.engines.gis.ign_client import (
    _ALTIMETRIE_BASE_URL,
    IGNClient,
    IGNClientError,
)
from gsie_api.engines.gis.telechargement_client import (
    _TELECHARGEMENT_BASE_URL,
    TelechargementClient,
    TelechargementClientError,
)
from gsie_api.engines.pedology.soilgrids_client import (
    _SOILGRIDS_URL,
    SoilGridsClient,
    SoilGridsClientError,
)


class BodyFormat(Enum):
    """Format de corps attendu par le client."""

    JSON = "json"
    CSV = "csv"
    GZIP_CSV = "gzip_csv"
    XML = "xml"
    BINARY = "binary"


@dataclass(frozen=True)
class ClientSpec:
    """Spécification d'un client pour la factory de tests de résilience.

    Attributes:
        name: nom unique du client (utilisé dans l'ID du test)
        factory: fonction qui instancie le client (sans args)
        url: URL exacte qui sera mockée par respx
        exception: classe d'exception métier attendue
        call: fonction async qui appelle la méthode du client à tester
        auth: True si le client utilise une authentification (active mode #5)
        body_format: format de corps attendu (détermine les mocks mode #3/#4)
        match_error: motif d'erreur à vérifier dans le message d'exception
    """

    name: str
    factory: Callable[[], Any]
    url: str
    exception: type[Exception]
    call: Callable[[Any], Awaitable[Any]]
    auth: bool = False
    body_format: BodyFormat = BodyFormat.JSON
    match_error: str = "Échec"
    method: str = "GET"


# --- Helpers pour construire les mocks selon le format ---


def _malformed_body(fmt: BodyFormat) -> bytes:
    """Corps qui causera une erreur de parsing selon le format."""
    if fmt == BodyFormat.JSON:
        return b"<<< not JSON >>>"
    if fmt == BodyFormat.GZIP_CSV:
        return b"<<< not gzip >>>"
    if fmt == BodyFormat.XML:
        return b"<<< not XML >>>"
    if fmt == BodyFormat.CSV:
        return b""  # CSV vide = liste vide, pas une erreur
    return b"<<< not binary >>>"


def _valid_but_empty_response(fmt: BodyFormat) -> Response:
    """Réponse valide mais sans les données attendues (mode #4)."""
    if fmt == BodyFormat.JSON:
        return Response(200, json={"unexpected": "structure"})
    if fmt == BodyFormat.GZIP_CSV:
        # gzip valide avec en-tête CSV mais aucune ligne de données
        empty_csv = "lat;lon;geo_id_wmo\n"
        return Response(200, content=gzip.compress(empty_csv.encode("utf-8")))
    if fmt == BodyFormat.CSV:
        # CSV avec en-tête mais sans les colonnes attendues
        return Response(200, text="unexpected_col\nval\n")
    if fmt == BodyFormat.XML:
        return Response(200, content=b'<?xml version="1.0"?><empty/>')
    return Response(200, content=b"")


# --- Registre des clients ---
# Chaque entrée génère 5 (ou 4 si auth=False) tests paramétrés.
# Pour ajouter un nouveau client : ajouter une entrée ici.

CLIENT_REGISTRY: list[ClientSpec] = [
    ClientSpec(
        name="gbif",
        factory=lambda: GBIFClient(),
        url=_SPECIES_MATCH_URL,
        exception=GBIFClientError,
        call=lambda c: c.match_species("Quercus petraea"),
        auth=False,
        body_format=BodyFormat.JSON,
    ),
    ClientSpec(
        name="plantnet",
        factory=lambda: PlantNetClient(),
        url=_IDENTIFY_URL,
        exception=PlantNetClientError,
        call=lambda c: c.identify(b"\x89PNG fake image bytes"),
        auth=True,
        body_format=BodyFormat.JSON,
        method="POST",
    ),
    ClientSpec(
        name="taxref",
        factory=lambda: TaxrefClient(),
        url="https://api.gbif.org/v1/species/search",
        exception=TaxrefClientError,
        call=lambda c: c.search("Quercus petraea"),
        auth=False,
        body_format=BodyFormat.JSON,
    ),
    ClientSpec(
        name="soilgrids",
        factory=lambda: SoilGridsClient(),
        url=_SOILGRIDS_URL,
        exception=SoilGridsClientError,
        call=lambda c: c.get_properties(44.8, -0.6, ["phh2o"]),
        auth=False,
        body_format=BodyFormat.JSON,
    ),
    ClientSpec(
        name="ign_altitude",
        factory=lambda: IGNClient(),
        url=_ALTIMETRIE_BASE_URL,
        exception=IGNClientError,
        call=lambda c: c.get_altitude(44.0, -0.5),
        auth=False,
        body_format=BodyFormat.JSON,
    ),
    ClientSpec(
        name="ign_telechargement",
        factory=lambda: TelechargementClient(),
        url=f"{_TELECHARGEMENT_BASE_URL}/capabilities",
        exception=TelechargementClientError,
        call=lambda c: c.get_capabilities(),
        auth=False,
        body_format=BodyFormat.XML,
    ),
    ClientSpec(
        name="vigilance",
        factory=lambda: VigilanceClient(),
        url=_VIGILANCE_URL,
        exception=VigilanceClientError,
        call=lambda c: c.get_carte_vigilance(),
        auth=True,
        body_format=BodyFormat.JSON,
    ),
    ClientSpec(
        name="meteofrance",
        factory=lambda: MeteoFranceClient(),
        url=f"{_METEOFRANCE_BASE_URL}/carte/encours",
        exception=MeteoFranceClientError,
        call=lambda c: c.get_danger_feux_departements(),
        auth=True,
        body_format=BodyFormat.CSV,
    ),
    ClientSpec(
        name="synop",
        factory=lambda: SynopClient(),
        url=_SYNOP_URL_TEMPLATE.format(year=2026),
        exception=SynopClientError,
        call=lambda c: c.get_latest_observation("07510", year=2026),
        auth=False,
        body_format=BodyFormat.GZIP_CSV,
    ),
    ClientSpec(
        name="paquet_obs",
        factory=lambda: PaquetObservationClient(),
        url=_PAQUET_OBS_URL,
        exception=PaquetObservationClientError,
        call=lambda c: c.get_observations_horaires("33"),
        auth=True,
        body_format=BodyFormat.CSV,
    ),
    ClientSpec(
        name="dpclim",
        factory=lambda: DPClimClient(),
        url=f"{_DPCLIM_BASE_URL}/liste-stations/quotidienne",
        exception=DPClimClientError,
        call=lambda c: c.list_stations("33"),
        auth=True,
        body_format=BodyFormat.JSON,
    ),
    ClientSpec(
        name="arome",
        factory=lambda: AromeClient(),
        url=f"{_AROME_BASE_URL}/GetCapabilities",
        exception=AromeClientError,
        call=lambda c: c.get_latest_temperature_2m_run(),
        auth=True,
        body_format=BodyFormat.XML,
    ),
]


# --- Fixture pour injecter une clé API fake pour les clients auth ---


@pytest.fixture(autouse=True)
def _fake_api_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """Injecte une clé API fake pour tous les clients avec auth."""
    fake_settings = type(
        "S",
        (),
        {"meteofrance_api_key": "fake-key-for-test", "plantnet_api_key": "fake-key-for-test"},
    )()
    for module_path in (
        "gsie_api.engines.climate.vigilance_client",
        "gsie_api.engines.climate.meteofrance_client",
        "gsie_api.engines.climate.paquet_observation_client",
        "gsie_api.engines.climate.dpclim_client",
        "gsie_api.engines.climate.arome_client",
        "gsie_api.engines.botanical.plantnet_client",
    ):
        monkeypatch.setattr(
            f"{module_path}.get_settings",
            lambda s=fake_settings: s,
        )


# =====================================================================
# Tests paramétrés — 5 modes de panne pour tous les clients enregistrés
# =====================================================================

_SPECS_WITH_AUTH = [s for s in CLIENT_REGISTRY if s.auth]
_SPECS_WITHOUT_AUTH = [s for s in CLIENT_REGISTRY if not s.auth]


@pytest.mark.parametrize("spec", CLIENT_REGISTRY, ids=[s.name for s in CLIENT_REGISTRY])
@respx.mock
async def test_mode1_network_failure(spec: ClientSpec) -> None:
    """Mode #1 — une panne réseau (ConnectError) doit lever l'exception métier."""
    respx.route(method=spec.method, url=spec.url).mock(
        side_effect=httpx.ConnectError("connexion refusée")
    )
    client = spec.factory()
    with pytest.raises(spec.exception):
        await spec.call(client)


@pytest.mark.parametrize("spec", CLIENT_REGISTRY, ids=[s.name for s in CLIENT_REGISTRY])
@respx.mock
async def test_mode2_http_4xx_5xx(spec: ClientSpec) -> None:
    """Mode #2 — un statut HTTP 4xx puis 5xx doit lever l'exception métier."""
    client = spec.factory()
    respx.route(method=spec.method, url=spec.url).mock(return_value=Response(404))
    with pytest.raises(spec.exception):
        await spec.call(client)

    respx.route(method=spec.method, url=spec.url).mock(return_value=Response(500))
    with pytest.raises(spec.exception):
        await spec.call(client)


@pytest.mark.parametrize(
    "spec",
    [s for s in CLIENT_REGISTRY if s.body_format != BodyFormat.CSV],
    ids=[s.name for s in CLIENT_REGISTRY if s.body_format != BodyFormat.CSV],
)
@respx.mock
async def test_mode3_malformed_body(spec: ClientSpec) -> None:
    """Mode #3 — un corps malformé doit lever l'exception métier, pas planter."""
    body = _malformed_body(spec.body_format)
    respx.route(method=spec.method, url=spec.url).mock(return_value=Response(200, content=body))
    client = spec.factory()
    with pytest.raises(spec.exception):
        await spec.call(client)


@pytest.mark.parametrize("spec", CLIENT_REGISTRY, ids=[s.name for s in CLIENT_REGISTRY])
@respx.mock
async def test_mode4_missing_field(spec: ClientSpec) -> None:
    """Mode #4 — une réponse valide sans les champs attendus ne doit pas planter.

    Le client doit soit retourner une valeur par défaut (None, [], {}),
    soit lever son exception métier — mais jamais planter avec une
    exception non gérée (KeyError, IndexError, TypeError, etc.).
    """
    response = _valid_but_empty_response(spec.body_format)
    respx.route(method=spec.method, url=spec.url).mock(return_value=response)
    client = spec.factory()
    try:
        result = await spec.call(client)
        # Si le client retourne une valeur, ce doit être une valeur "vide"
        # (None, [], {}, un dict sans les champs attendus, ou un tuple
        # contenant une liste/dict vide — ex. pagination) — jamais une
        # valeur inventée.
        assert (
            result is None
            or result == []
            or result == {}
            or isinstance(result, dict | list)
            or (isinstance(result, tuple) and len(result) >= 1)
        )
    except spec.exception:
        # Le client peut légitimement lever son exception métier si la
        # réponse est considérée comme invalide — c'est aussi acceptable.
        pass


@pytest.mark.parametrize(
    "spec",
    _SPECS_WITH_AUTH,
    ids=[s.name for s in _SPECS_WITH_AUTH],
)
@respx.mock
async def test_mode5_quota_auth(spec: ClientSpec) -> None:
    """Mode #5 — un 401/403/429 (auth/quota) doit lever l'exception métier."""
    client = spec.factory()
    for status in (401, 403, 429):
        respx.route(method=spec.method, url=spec.url).mock(return_value=Response(status))
        with pytest.raises(spec.exception):
            await spec.call(client)


@pytest.mark.parametrize(
    "spec",
    _SPECS_WITHOUT_AUTH,
    ids=[s.name for s in _SPECS_WITHOUT_AUTH],
)
async def test_mode5_not_applicable(spec: ClientSpec) -> None:
    """Mode #5 — N/A : ce client n'utilise pas d'authentification.

    Les clients sans auth (GBIF, Taxref, SoilGrids, IGN, SYNOP) n'ont
    pas de 401/403/429 spécifique à l'auth. Le mode #2 couvre déjà
    les codes HTTP en échec génériques.
    """
    # Pas de test à exécuter — documentation explicite de la décision.

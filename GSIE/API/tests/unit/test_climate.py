"""Tests unitaires — Climate Engine (SYNOP Météo-France).

Les appels réseau sont mockés (monkeypatch de SynopClient) avec des
lignes CSV réelles capturées manuellement le 2026-07-17 (station
07510 Bordeaux-Mérignac, 00h et 03h UTC du 2026-01-01) — pas de
donnée inventée.
"""

import gzip

import httpx
import pytest

from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError
from gsie_api.engines.climate.schemas import ClimateQuery
from gsie_api.engines.climate.synop_client import SynopClient, SynopClientError

_HEADER = (
    "lat;lon;geo_id_wmo;geo_id_wigos;name;reference_time;insert_time;validity_time;pmer;tend;"
    "cod_tend;dd;ff;t;td;u;vv;ww;w1;w2;n;nbas;hbas;cl;cm;ch;pres;niv_bar;geop;tend24;tn12;tn24;"
    "tx12;tx24;tminsol;sw;tw;raf10;rafper;per;etat_sol;ht_neige;ssfrai;perssfrai;rr1;rr3;rr6;"
    "rr12;rr24;phenspe1;phenspe2;phenspe3;phenspe4;nnuage1;ctype1;hnuage1;nnuage2;ctype2;"
    "hnuage2;nnuage3;ctype3;hnuage3;nnuage4;ctype4;hnuage4"
)
# Ligne réelle 00h UTC (2026-01-01) — station 07510 Bordeaux-Mérignac.
_ROW_00H = (
    "44.830667;-0.691333;07510;0-20000-0-07510;BORDEAUX-MERIGNAC;2026-01-01T00:10:06Z;"
    "2026-01-01T00:02:31Z;2026-01-01T00:00:00Z;102150;-110;8;130;2.9;270.45;270.15;98;150;49;;;"
    "101;9;30;;;;101530;;;-310;;;;;269.05;;;4.4;4.4;-10;;0.0;;;0.0;0.0;0.0;0.0;0.2;;;;;0;0;;;;;;;;;;"
)
# Ligne réelle 03h UTC (2026-01-01) — la plus récente des deux, doit être retenue.
_ROW_03H = (
    "44.830667;-0.691333;07510;0-20000-0-07510;BORDEAUX-MERIGNAC;2026-01-01T03:10:05Z;"
    "2026-01-01T03:04:16Z;2026-01-01T03:00:00Z;102000;-140;7;150;2.7;270.95;270.65;98;180;49;;;"
    "101;9;30;;;;101390;;;-400;;;;;269.05;;;4.8;5.0;-10;0;0.0;;;0.0;0.0;0.0;0.0;0.2;;;;;0;0;;;;;;;;;;"
)


def _make_gzipped_csv(rows: list[str]) -> bytes:
    csv_text = "\n".join([_HEADER, *rows])
    return gzip.compress(csv_text.encode("utf-8"))


def _patch_transport(monkeypatch: pytest.MonkeyPatch, status_code: int, content: bytes) -> None:
    """Force tout httpx.AsyncClient créé pendant le test à répondre via ce transport mocké."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, content=content, request=request)

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def _patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", _patched_init)


@pytest.fixture
def engine(monkeypatch: pytest.MonkeyPatch) -> ClimateEngine:
    gz_bytes = _make_gzipped_csv([_ROW_00H, _ROW_03H])
    _patch_transport(monkeypatch, 200, gz_bytes)
    return ClimateEngine(synop_client=SynopClient())


async def test_query_returns_most_recent_observation(engine: ClimateEngine):
    """Entre deux observations réelles, la plus récente (03h, pas 00h) doit être retenue."""
    result = await engine.query(ClimateQuery(station_id="07510"))

    assert result is not None
    assert result.date_observation.hour == 3
    assert result.nom_station == "BORDEAUX-MERIGNAC"


async def test_query_converts_temperature_kelvin_to_celsius(engine: ClimateEngine):
    """t=270.95K (ligne 03h) doit être converti en 270.95 - 273.15 = -2.2°C exactement."""
    result = await engine.query(ClimateQuery(station_id="07510"))

    assert result.temperature_c == pytest.approx(270.95 - 273.15)


async def test_query_converts_pressure_pa_to_hpa(engine: ClimateEngine):
    """pmer=102000 Pa doit être converti en 1020.0 hPa exactement."""
    result = await engine.query(ClimateQuery(station_id="07510"))

    assert result.pression_hpa == pytest.approx(1020.0)


async def test_query_preserves_humidity_wind_precipitation_as_is(engine: ClimateEngine):
    """u, dd, ff, rr1 sont déjà dans l'unité cible — pas de conversion à appliquer."""
    result = await engine.query(ClimateQuery(station_id="07510"))

    assert result.humidite_pct == 98.0
    assert result.vent_direction_deg == 150.0
    assert result.vent_vitesse_ms == 2.7
    assert result.precipitations_1h_mm == 0.0


async def test_query_returns_none_for_unknown_station(engine: ClimateEngine):
    """Une station absente des données doit retourner None — jamais une observation inventée."""
    result = await engine.query(ClimateQuery(station_id="99999"))

    assert result is None


async def test_query_raises_on_network_failure(monkeypatch: pytest.MonkeyPatch):
    """Une panne réseau doit lever ClimateEngineError, jamais une observation par défaut."""
    _patch_transport(monkeypatch, 503, b"")
    engine = ClimateEngine()

    with pytest.raises(ClimateEngineError):
        await engine.query(ClimateQuery(station_id="07510"))


async def test_synop_client_raises_on_gzip_decode_failure(monkeypatch: pytest.MonkeyPatch):
    """Une réponse non-gzip doit lever SynopClientError, pas planter silencieusement."""
    _patch_transport(monkeypatch, 200, b"not gzip data")
    client = SynopClient()

    with pytest.raises(SynopClientError):
        await client.get_latest_observation("07510")


def test_return_engine_version():
    """version() doit retourner une chaîne non vide."""
    assert len(ClimateEngine.version()) > 0

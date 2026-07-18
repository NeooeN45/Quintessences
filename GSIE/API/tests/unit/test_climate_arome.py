"""Tests unitaires — Climate Engine / modèle AROME (API WCS, GRIB2 réel).

Le réseau est mocké : la réponse GetCapabilities reprend la structure
XML réelle (vérifiée le 2026-07-18, `xmlns:wcs="http://www.opengis.net/wcs/2.0"`,
élément `<wcs:CoverageId>`), réduite à 2 entrées. La réponse GetCoverage
utilise un vrai GRIB2 capturé (`tests/fixtures/arome_temperature_sample.grib2`,
421 octets, zone Bordeaux, échéance 2026-07-18T12:00Z, décodé et vérifié
manuellement : t2m = 30,25 °C).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from gsie_api.engines.climate.arome_client import AromeClient
from gsie_api.engines.climate.arome_grib_decoder import (
    AromeGribDecodeError,
    extract_nearest_temperature_celsius,
)
from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError
from gsie_api.engines.climate.schemas import AromeTemperatureQuery

_FIXTURE_GRIB2 = (
    Path(__file__).resolve().parents[1] / "fixtures" / "arome_temperature_sample.grib2"
).read_bytes()

_LATEST_RUN = "TEMPERATURE__SPECIFIC_HEIGHT_LEVEL_ABOVE_GROUND___2026-07-18T06.00.00Z"

# Structure XML réelle réduite à 2 CoverageId (le vrai GetCapabilities
# fait ~1,8 Mo et liste ~5700 couvertures).
_CAPABILITIES_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<wcs:Capabilities xmlns:wcs="http://www.opengis.net/wcs/2.0">
  <wcs:Contents>
    <wcs:CoverageSummary>
      <wcs:CoverageId>TEMPERATURE__SPECIFIC_HEIGHT_LEVEL_ABOVE_GROUND___2026-07-18T03.00.00Z</wcs:CoverageId>
    </wcs:CoverageSummary>
    <wcs:CoverageSummary>
      <wcs:CoverageId>{_LATEST_RUN}</wcs:CoverageId>
    </wcs:CoverageSummary>
  </wcs:Contents>
</wcs:Capabilities>"""


def _patch_arome_transport(
    monkeypatch: pytest.MonkeyPatch,
    capabilities_status: int = 200,
    capabilities_body: bytes | None = None,
    coverage_status: int = 200,
    coverage_body: bytes | None = None,
) -> None:
    capabilities_body = (
        _CAPABILITIES_XML.encode("utf-8") if capabilities_body is None else capabilities_body
    )
    coverage_body = _FIXTURE_GRIB2 if coverage_body is None else coverage_body

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/GetCapabilities"):
            return httpx.Response(capabilities_status, content=capabilities_body, request=request)
        if request.url.path.endswith("/GetCoverage"):
            return httpx.Response(coverage_status, content=coverage_body, request=request)
        raise AssertionError(f"Requête WCS non mockée : {request.url}")

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def _patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", _patched_init)
    monkeypatch.setattr(
        "gsie_api.engines.climate.arome_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": "fake-key-for-test"})(),
    )


def _make_request() -> AromeTemperatureQuery:
    return AromeTemperatureQuery(
        requete_id=uuid4(),
        latitude=44.8,
        longitude=-0.6,
        echeance=datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc),
    )


async def test_get_latest_run_picks_the_most_recent_coverage_id(
    monkeypatch: pytest.MonkeyPatch,
):
    """Parmi plusieurs runs réels, le plus récent (tri lexicographique = chronologique) doit être choisi."""
    _patch_arome_transport(monkeypatch)
    client = AromeClient()

    run = await client.get_latest_temperature_2m_run()

    assert run == _LATEST_RUN


async def test_get_temperature_arome_decodes_real_grib(monkeypatch: pytest.MonkeyPatch):
    """Le résultat doit reprendre la vraie température décodée du GRIB2 (30,25 °C)."""
    _patch_arome_transport(monkeypatch)
    engine = ClimateEngine(arome_client=AromeClient())

    result = await engine.get_temperature_arome(_make_request())

    assert result.temperature_c == pytest.approx(30.254449462890648)
    assert result.run_modele == _LATEST_RUN
    assert result.latitude == 44.8
    assert result.longitude == -0.6
    assert "AROME" in result.source.reference


async def test_get_temperature_arome_raises_without_api_key(monkeypatch: pytest.MonkeyPatch):
    """Sans clé configurée, doit lever ClimateEngineError avant tout appel réseau."""
    monkeypatch.setattr(
        "gsie_api.engines.climate.arome_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": None})(),
    )
    engine = ClimateEngine(arome_client=AromeClient())

    with pytest.raises(ClimateEngineError):
        await engine.get_temperature_arome(_make_request())


async def test_get_temperature_arome_raises_when_no_run_published(
    monkeypatch: pytest.MonkeyPatch,
):
    """Si GetCapabilities ne liste aucun run pour ce paramètre, doit lever ClimateEngineError."""
    empty_xml = b'<?xml version="1.0"?><wcs:Capabilities xmlns:wcs="http://www.opengis.net/wcs/2.0"/>'
    _patch_arome_transport(monkeypatch, capabilities_body=empty_xml)
    engine = ClimateEngine(arome_client=AromeClient())

    with pytest.raises(ClimateEngineError):
        await engine.get_temperature_arome(_make_request())


async def test_get_temperature_arome_raises_on_invalid_subsetting(
    monkeypatch: pytest.MonkeyPatch,
):
    """Une échéance hors du run (rejetée par l'API) doit lever ClimateEngineError, pas planter."""
    error_body = b'<?xml version="1.0"?><ns0:ExceptionReport xmlns:ns0="http://www.opengis.net/ows/1.1"/>'
    _patch_arome_transport(monkeypatch, coverage_status=404, coverage_body=error_body)
    engine = ClimateEngine(arome_client=AromeClient())

    with pytest.raises(ClimateEngineError):
        await engine.get_temperature_arome(_make_request())


def test_decoder_raises_on_non_grib_bytes():
    """Des octets qui ne sont pas un GRIB2 valide doivent lever AromeGribDecodeError."""
    with pytest.raises(AromeGribDecodeError):
        extract_nearest_temperature_celsius(b"not a grib file", 44.8, -0.6)


def test_decoder_extracts_real_fixture_temperature():
    """Le décodeur doit retrouver exactement la température réelle de la fixture GRIB2."""
    result = extract_nearest_temperature_celsius(_FIXTURE_GRIB2, 44.8, -0.6)

    assert result == pytest.approx(30.254449462890648)

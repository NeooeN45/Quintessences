"""Tests unitaires — TaxrefClient et BotanicalEngine.resolve_taxref() (SCI-003).

Réponse réelle capturée le 2026-07-18 (GBIF Species Search, miroir
TAXREF, `q=Quercus petraea`) — `tests/fixtures/taxref_search_sample.json`,
3 résultats réels : Quercus petraea (taxonID 521658, ACCEPTED),
Quercus petraea subsp. petraea (139584) et un hybride Quercus cerris x
petraea (611406).
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from gsie_api.engines.botanical.engine import BotanicalEngine, BotanicalEngineError
from gsie_api.engines.botanical.schemas import TaxonStatus, TaxrefQuery
from gsie_api.engines.botanical.taxref_client import TaxrefClient, TaxrefClientError

_FIXTURE_JSON = (
    Path(__file__).resolve().parents[1] / "fixtures" / "taxref_search_sample.json"
).read_text(encoding="utf-8")


class _NoOpSession:
    """Session factice — resolve_taxref() n'accède jamais à la base."""


def _patch_transport(monkeypatch: pytest.MonkeyPatch, status_code: int, content: bytes) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, content=content, request=request)

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def _patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", _patched_init)


async def test_taxref_client_returns_accepted_entry(monkeypatch: pytest.MonkeyPatch):
    """Sur 3 résultats réels, la première entrée ACCEPTED (Quercus petraea) doit être retenue."""
    _patch_transport(monkeypatch, 200, _FIXTURE_JSON.encode("utf-8"))
    client = TaxrefClient()

    result = await client.search("Quercus petraea")

    assert result is not None
    assert result["taxonID"] == "521658"
    assert result["taxonomicStatus"] == "ACCEPTED"


async def test_taxref_client_returns_none_when_no_results(monkeypatch: pytest.MonkeyPatch):
    """Aucun résultat réel ne doit produire None, jamais une entrée inventée."""
    _patch_transport(monkeypatch, 200, b'{"results": []}')
    client = TaxrefClient()

    result = await client.search("Taxon totalement inexistant")

    assert result is None


async def test_taxref_client_raises_on_network_failure(monkeypatch: pytest.MonkeyPatch):
    """Une panne réseau doit lever TaxrefClientError, pas planter silencieusement."""
    _patch_transport(monkeypatch, 503, b"")
    client = TaxrefClient()

    with pytest.raises(TaxrefClientError):
        await client.search("Quercus petraea")


async def test_engine_resolve_taxref_returns_real_cd_nom(monkeypatch: pytest.MonkeyPatch):
    """BotanicalEngine.resolve_taxref() doit renvoyer le vrai cd_nom (521658) et le bon statut."""
    _patch_transport(monkeypatch, 200, _FIXTURE_JSON.encode("utf-8"))
    engine = BotanicalEngine(_NoOpSession(), taxref_client=TaxrefClient())  # type: ignore[arg-type]

    result = await engine.resolve_taxref(
        TaxrefQuery(requete_id=uuid4(), nom_scientifique="Quercus petraea")
    )

    assert result is not None
    assert result.cd_nom == 521658
    assert result.nom_scientifique == "Quercus petraea"
    assert result.nom_scientifique_complet == "Quercus petraea (Matt.) Liebl., 1784"
    assert result.nom_vernaculaire == "Chêne sessile, Chêne rouvre, Chêne à trochets"
    assert result.famille == "Fagaceae"
    assert result.statut == TaxonStatus.accepted
    assert "TAXREF" in result.source.reference


async def test_engine_resolve_taxref_returns_none_for_unknown_taxon(
    monkeypatch: pytest.MonkeyPatch,
):
    """Un taxon absent du miroir TAXREF doit retourner None — jamais un cd_nom approximé."""
    _patch_transport(monkeypatch, 200, b'{"results": []}')
    engine = BotanicalEngine(_NoOpSession(), taxref_client=TaxrefClient())  # type: ignore[arg-type]

    result = await engine.resolve_taxref(
        TaxrefQuery(requete_id=uuid4(), nom_scientifique="Taxon inexistant")
    )

    assert result is None


async def test_engine_resolve_taxref_raises_on_client_error(monkeypatch: pytest.MonkeyPatch):
    """Une panne du miroir GBIF doit lever BotanicalEngineError, pas planter silencieusement."""
    _patch_transport(monkeypatch, 503, b"")
    engine = BotanicalEngine(_NoOpSession(), taxref_client=TaxrefClient())  # type: ignore[arg-type]

    with pytest.raises(BotanicalEngineError):
        await engine.resolve_taxref(
            TaxrefQuery(requete_id=uuid4(), nom_scientifique="Quercus petraea")
        )

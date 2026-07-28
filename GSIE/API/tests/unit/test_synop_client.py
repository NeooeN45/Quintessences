"""Tests unitaires — SynopClient (résilience aux pannes amont).

Couvre les 5 modes de panne pour le client SYNOP (Météo-France, data.gouv).
Aucune authentification requise — le mode #5 (quota/auth) est déclaré N/A.
"""

from __future__ import annotations

import gzip

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.climate.synop_client import (
    _SYNOP_URL_TEMPLATE,
    SynopClient,
    SynopClientError,
)

_YEAR = 2026
_URL = _SYNOP_URL_TEMPLATE.format(year=_YEAR)

# CSV minimal avec en-tête SYNOP et une ligne pour station 07510
_HEADER = "lat;lon;geo_id_wmo;validity_time;t;td;u;pmer;dd;ff;rr1"
_ROW = "44.83;-0.69;07510;2026-01-01T00:00:00Z;270.95;270.15;98;102000;130;2.9;0.0"


def _gzipped_csv(rows: list[str]) -> bytes:
    csv_text = "\n".join([_HEADER, *rows])
    return gzip.compress(csv_text.encode("utf-8"))


@respx.mock
async def test_should_raise_synop_client_error_when_connect_error() -> None:
    """Mode #1 — une panne réseau (ConnectError) doit lever SynopClientError."""
    respx.get(_URL).mock(side_effect=httpx.ConnectError("connexion refusée"))
    client = SynopClient()
    with pytest.raises(SynopClientError, match="Échec du téléchargement SYNOP"):
        await client.get_latest_observation("07510", year=_YEAR)


@respx.mock
async def test_should_raise_synop_client_error_when_http_4xx_then_5xx() -> None:
    """Mode #2 — un statut HTTP 4xx puis 5xx doit lever SynopClientError."""
    client = SynopClient()
    respx.get(_URL).mock(return_value=Response(404))
    with pytest.raises(SynopClientError):
        await client.get_latest_observation("07510", year=_YEAR)

    respx.get(_URL).mock(return_value=Response(500))
    with pytest.raises(SynopClientError):
        await client.get_latest_observation("07510", year=_YEAR)


@respx.mock
async def test_should_raise_synop_client_error_when_body_is_not_gzip() -> None:
    """Mode #3 — un corps non-gzip doit lever SynopClientError (gzip decode failure)."""
    respx.get(_URL).mock(return_value=Response(200, content=b"<<< pas du gzip >>>"))
    client = SynopClient()
    with pytest.raises(SynopClientError, match="illisible"):
        await client.get_latest_observation("07510", year=_YEAR)


@respx.mock
async def test_should_return_none_when_station_absent_from_csv() -> None:
    """Mode #4 — un CSV valide sans la station demandée doit retourner None.

    Le CSV est bien formé (gzip valide, en-tête correct) mais la station
    demandée n'y figure pas. Le client retourne None, jamais une
    observation inventée.
    """
    other_row = "48.85;2.35;07157;2026-01-01T00:00:00Z;283.15;278.15;60;101500;200;3.0;0.0"
    respx.get(_URL).mock(return_value=Response(200, content=_gzipped_csv([other_row])))
    client = SynopClient()
    result = await client.get_latest_observation("07510", year=_YEAR)
    assert result is None


@respx.mock
async def test_should_return_latest_observation_when_station_present() -> None:
    """Mode #4 (positif) — entre deux lignes, la plus récente doit être retenue."""
    row_00h = "44.83;-0.69;07510;2026-01-01T00:00:00Z;270.95;270.15;98;102000;130;2.9;0.0"
    row_03h = "44.83;-0.69;07510;2026-01-01T03:00:00Z;270.95;270.65;98;102000;150;2.7;0.0"
    respx.get(_URL).mock(return_value=Response(200, content=_gzipped_csv([row_00h, row_03h])))
    client = SynopClient()
    result = await client.get_latest_observation("07510", year=_YEAR)
    assert result is not None
    assert result["validity_time"] == "2026-01-01T03:00:00Z"
    assert result["geo_id_wmo"] == "07510"


async def test_mode5_quota_auth_not_applicable_for_synop() -> None:
    """Mode #5 — N/A : les archives SYNOP sont un bucket S3 public sans auth."""
    pass

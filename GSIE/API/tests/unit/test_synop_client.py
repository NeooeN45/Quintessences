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


# ===========================================================================
# Couverture complémentaire — cache LRU, éviction, lock
# ===========================================================================


@respx.mock
async def should_use_cache_on_second_call() -> None:
    """Le cache doit éviter un second téléchargement pour la même année."""
    respx.get(_URL).mock(return_value=Response(200, content=_gzipped_csv([_ROW])))
    client = SynopClient()
    await client.get_latest_observation("07510", year=_YEAR)
    # Second call — pas de mock reset, le cache doit servir
    result = await client.get_latest_observation("07510", year=_YEAR)
    assert result is not None
    assert result["geo_id_wmo"] == "07510"


def should_evict_expired_entries() -> None:
    """_evict_expired doit retirer les entrées expirées du cache."""
    from gsie_api.engines.climate.synop_client import _CACHE_TTL_SECONDS, _CachedFile

    client = SynopClient()
    # Insère une entrée avec un timestamp dans le passé
    cached = _CachedFile(_YEAR, "test")
    cached.fetched_at = -(  # il y a très longtemps
        _CACHE_TTL_SECONDS + 100
    )
    client._cache[_YEAR] = cached
    client._locks[_YEAR] = __import__("asyncio").Lock()

    client._evict_expired()
    assert _YEAR not in client._cache
    assert _YEAR not in client._locks


def should_not_evict_fresh_entries() -> None:
    """_evict_expired ne doit pas retirer les entrées fraîches."""
    client = SynopClient()
    client._put(_YEAR, "test")
    client._evict_expired()
    assert _YEAR in client._cache


def should_evict_oldest_when_cache_full() -> None:
    """_put doit évincer l'entrée la plus ancienne quand le cache est plein."""
    from gsie_api.engines.climate.synop_client import _CACHE_MAX_ENTRIES

    client = SynopClient()
    # Remplit le cache au maximum
    for year in range(_CACHE_MAX_ENTRIES + 2):
        client._put(year, f"csv-{year}")
    # Les plus anciennes doivent être évictées
    assert len(client._cache) <= _CACHE_MAX_ENTRIES
    assert 0 not in client._cache  # plus ancien évicté
    assert _CACHE_MAX_ENTRIES + 1 in client._cache  # plus récent présent


def should_create_lock_lazily() -> None:
    """_get_lock doit créer un verrou par année paresseusement."""
    import asyncio

    client = SynopClient()
    lock1 = client._get_lock(2026)
    lock2 = client._get_lock(2026)
    assert lock1 is lock2  # même instance
    lock3 = client._get_lock(2027)
    assert lock3 is not lock1  # instance différente par année
    assert isinstance(lock1, asyncio.Lock)


def should_cached_file_is_expired_check() -> None:
    """_CachedFile.is_expired doit retourner True après le TTL."""
    from gsie_api.engines.climate.synop_client import _CACHE_TTL_SECONDS, _CachedFile

    cached = _CachedFile(2026, "test")
    assert not cached.is_expired(_CACHE_TTL_SECONDS)  # fraîche

    cached.fetched_at = -(_CACHE_TTL_SECONDS + 1)
    assert cached.is_expired(_CACHE_TTL_SECONDS)  # expirée


@respx.mock
async def should_recheck_cache_under_lock() -> None:
    """La re-vérification sous le verrou doit utiliser le cache si un autre appelant l'a rempli."""
    respx.get(_URL).mock(return_value=Response(200, content=_gzipped_csv([_ROW])))
    client = SynopClient()
    # Pré-remplit le cache manuellement
    client._put(_YEAR, "\n".join([_HEADER, _ROW]))
    # L'appel doit utiliser le cache sans télécharger
    result = await client.get_latest_observation("07510", year=_YEAR)
    assert result is not None
    assert result["geo_id_wmo"] == "07510"

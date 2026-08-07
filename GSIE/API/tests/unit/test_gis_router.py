"""Tests unitaires — router GIS (engines/gis/router.py).

Complète tests/unit/test_gis_engine.py (moteur) et
tests/integration/test_gis.py (Docker). Ici la DB est mockée via
dependency_overrides — pas de Docker requis. Cible en particulier les
branches d'erreur 502 (GISEngineError/IGNClientError) de l'API de
téléchargement Géoplateforme, non couvertes par les tests d'intégration.

Conventions (AGENTS.md API) : pytest-asyncio mode ``auto``, nommage
``should_[expected]_when_[condition]``.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator  # noqa: TC003
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from slowapi import Limiter
from slowapi.middleware import SlowAPIASGIMiddleware
from slowapi.util import get_remote_address

from gsie_api.core.auth import create_access_token
from gsie_api.engines.gis.engine import GISEngineError
from gsie_api.engines.gis.ign_client import IGNClientError
from gsie_api.engines.gis.router import router as gis_router
from gsie_api.infrastructure.database import get_db

_API_PREFIX = "/api/v1"


def _auth_headers(roles: list[str] | None = None) -> dict[str, str]:
    if roles is None:
        roles = ["reader"]
    token = create_access_token(subject="test-user", claims={"roles": roles})
    return {"Authorization": f"Bearer {token}"}


def _writer_headers() -> dict[str, str]:
    return _auth_headers(roles=["writer"])


def _build_app(mock_db: Any) -> FastAPI:
    app = FastAPI()
    app.state.limiter = Limiter(key_func=get_remote_address)
    app.add_middleware(SlowAPIASGIMiddleware)

    async def _override_get_db() -> AsyncGenerator[Any, None]:
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db
    app.include_router(gis_router, prefix=_API_PREFIX)
    return app


@pytest.fixture
async def gis_client() -> AsyncGenerator[AsyncClient, None]:
    mock_db = AsyncMock()
    app = _build_app(mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


class TestStatusAndVersion:
    async def should_return_status_when_called(self, gis_client: AsyncClient) -> None:
        resp = await gis_client.get(f"{_API_PREFIX}/gis/status")
        assert resp.status_code == 200
        assert resp.json()["engine"] == "gis"

    async def should_return_version_when_called(self, gis_client: AsyncClient) -> None:
        resp = await gis_client.get(f"{_API_PREFIX}/gis/version")
        assert resp.status_code == 200
        assert resp.json()["backend"] == "postgis"


class TestCadastreParcelle:
    async def should_return_401_when_no_auth(self, gis_client: AsyncClient) -> None:
        resp = await gis_client.post(
            f"{_API_PREFIX}/gis/cadastre/parcelle",
            json={"code_insee": "68001", "section": "AH", "numero": "0040"},
        )
        assert resp.status_code == 401

    async def should_return_502_when_ign_client_fails(self, gis_client: AsyncClient) -> None:
        with patch("gsie_api.engines.gis.router.GISEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.get_parcelle_cadastre = AsyncMock(
                side_effect=IGNClientError("API Carto IGN indisponible")
            )
            resp = await gis_client.post(
                f"{_API_PREFIX}/gis/cadastre/parcelle",
                json={"code_insee": "68001", "section": "AH", "numero": "0040"},
                headers=_writer_headers(),
            )
        assert resp.status_code == 502
        assert "indisponible" in resp.json()["detail"]


class TestAltitude:
    async def should_return_401_when_no_auth(self, gis_client: AsyncClient) -> None:
        resp = await gis_client.post(
            f"{_API_PREFIX}/gis/altitude",
            json={"latitude": 48.0, "longitude": 7.0},
        )
        assert resp.status_code == 401

    async def should_return_502_when_engine_raises(self, gis_client: AsyncClient) -> None:
        with patch("gsie_api.engines.gis.router.GISEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.get_altitude = AsyncMock(
                side_effect=GISEngineError("API altimétrique IGN indisponible")
            )
            resp = await gis_client.post(
                f"{_API_PREFIX}/gis/altitude",
                json={"latitude": 48.0, "longitude": 7.0},
                headers=_auth_headers(),
            )
        assert resp.status_code == 502
        assert "indisponible" in resp.json()["detail"]


class TestTelechargementRessources:
    async def should_return_502_when_engine_raises(self, gis_client: AsyncClient) -> None:
        with patch("gsie_api.engines.gis.router.GISEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.lister_ressources_telechargement = AsyncMock(
                side_effect=GISEngineError("API de téléchargement IGN indisponible")
            )
            resp = await gis_client.get(
                f"{_API_PREFIX}/gis/telechargement/ressources",
                headers=_auth_headers(),
            )
        assert resp.status_code == 502
        assert "indisponible" in resp.json()["detail"]

    async def should_return_401_when_no_auth(self, gis_client: AsyncClient) -> None:
        resp = await gis_client.get(f"{_API_PREFIX}/gis/telechargement/ressources")
        assert resp.status_code == 401


class TestTelechargementDossiers:
    async def should_return_502_when_engine_raises(self, gis_client: AsyncClient) -> None:
        with patch("gsie_api.engines.gis.router.GISEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.lister_dossiers_telechargement = AsyncMock(
                side_effect=GISEngineError("API de téléchargement IGN indisponible")
            )
            resp = await gis_client.get(
                f"{_API_PREFIX}/gis/telechargement/ressources/BDFORET",
                headers=_auth_headers(),
            )
        assert resp.status_code == 502
        assert "indisponible" in resp.json()["detail"]


class TestTelechargementFichiers:
    async def should_return_502_when_engine_raises(self, gis_client: AsyncClient) -> None:
        with patch("gsie_api.engines.gis.router.GISEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.lister_fichiers_telechargement = AsyncMock(
                side_effect=GISEngineError("API de téléchargement IGN indisponible")
            )
            resp = await gis_client.get(
                f"{_API_PREFIX}/gis/telechargement/ressources/BDFORET/BDFORET_2026",
                headers=_auth_headers(),
            )
        assert resp.status_code == 502
        assert "indisponible" in resp.json()["detail"]


class TestTelechargementDownload:
    async def should_return_binary_content_when_engine_succeeds(
        self, gis_client: AsyncClient
    ) -> None:
        with patch("gsie_api.engines.gis.router.GISEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.telecharger_fichier = AsyncMock(return_value=b"\x37\x7a\xbc\xaf")
            resp = await gis_client.get(
                f"{_API_PREFIX}/gis/telechargement/telecharger/BDFORET/BDFORET_2026/f.7z",
                headers=_writer_headers(),
            )
        assert resp.status_code == 200
        assert resp.content == b"\x37\x7a\xbc\xaf"
        assert resp.headers["content-type"] == "application/octet-stream"

    async def should_return_502_when_engine_raises(self, gis_client: AsyncClient) -> None:
        with patch("gsie_api.engines.gis.router.GISEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.telecharger_fichier = AsyncMock(
                side_effect=GISEngineError("API de téléchargement IGN indisponible")
            )
            resp = await gis_client.get(
                f"{_API_PREFIX}/gis/telechargement/telecharger/BDFORET/BDFORET_2026/f.7z",
                headers=_writer_headers(),
            )
        assert resp.status_code == 502
        assert "indisponible" in resp.json()["detail"]

    async def should_return_401_when_no_auth(self, gis_client: AsyncClient) -> None:
        resp = await gis_client.get(
            f"{_API_PREFIX}/gis/telechargement/telecharger/BDFORET/BDFORET_2026/f.7z",
        )
        assert resp.status_code == 401

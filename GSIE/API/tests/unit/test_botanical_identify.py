"""Tests unitaires — endpoint POST /botanical/identify (API PlantNet).

RFC-0031 action 8 : identification de plantes par image (78 810 espèces).
Teste l'endpoint FastAPI avec PlantNetClient mocké — pas d'appel réseau réel.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.auth import router as auth_router

# Activer le dev login pour les tests (comme test_auth_coverage.py)
auth_router._settings.auth_dev_login_enabled = True
auth_router._settings.auth_dev_password = "changeme"

_FAKE_PLANTNET_RESPONSE = {
    "query": {
        "project": "all",
        "images": ["abc123"],
        "organs": ["auto"],
    },
    "bestMatch": "Quercus robur L.",
    "results": [
        {
            "score": 0.85,
            "species": {
                "scientificNameWithoutAuthor": "Quercus robur",
                "scientificNameAuthorship": "L.",
                "genus": {
                    "scientificNameWithoutAuthor": "Quercus",
                    "scientificName": "Quercus",
                },
                "family": {
                    "scientificNameWithoutAuthor": "Fagaceae",
                    "scientificName": "Fagaceae",
                },
                "commonNames": ["Chêne pédonculé", "Pedunculate Oak"],
                "scientificName": "Quercus robur L.",
            },
            "gbif": {"id": "2878688"},
        },
        {
            "score": 0.05,
            "species": {
                "scientificNameWithoutAuthor": "Quercus petraea",
                "scientificNameAuthorship": "Matt.",
                "genus": {
                    "scientificNameWithoutAuthor": "Quercus",
                    "scientificName": "Quercus",
                },
                "family": {
                    "scientificNameWithoutAuthor": "Fagaceae",
                    "scientificName": "Fagaceae",
                },
                "commonNames": ["Chêne sessile"],
                "scientificName": "Quercus petraea Matt.",
            },
            "gbif": {"id": "2878688"},
        },
    ],
}


def _auth_headers() -> dict[str, str]:
    """Génère un token JWT de test avec rôle admin."""
    from gsie_api.core.auth import create_access_token

    token = create_access_token(subject="test-user", claims={"roles": ["admin"]})
    return {"Authorization": f"Bearer {token}"}


def _mock_plantnet_identify(return_value: dict | None) -> AsyncMock:
    """Crée un mock pour PlantNetClient.identify."""
    mock = AsyncMock()
    mock.return_value = return_value
    return mock


def should_return_identification_when_plantnet_succeeds(mock_lifespan: object) -> None:
    """L'endpoint /identify doit retourner les résultats PlantNet formatés."""
    with patch("gsie_api.engines.botanical.router.PlantNetClient") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.identify = _mock_plantnet_identify(_FAKE_PLANTNET_RESPONSE)
        with TestClient(create_app()) as client:
            response = client.post(
                "/api/v1/botanical/identify",
                files={"file": ("test.jpg", b"\x89PNG fake", "image/jpeg")},
                headers=_auth_headers(),
            )
    assert response.status_code == 200
    data = response.json()
    assert data["best_match"] == "Quercus robur L."
    assert len(data["results"]) == 2
    assert data["results"][0]["score"] == 0.85
    assert data["results"][0]["scientific_name"] == "Quercus robur L."
    assert data["results"][0]["genus"] == "Quercus"
    assert data["results"][0]["family"] == "Fagaceae"
    assert "Chêne pédonculé" in data["results"][0]["common_names"]
    assert data["results"][0]["gbif_id"] == "2878688"


def should_return_null_when_plantnet_finds_nothing(mock_lifespan: object) -> None:
    """L'endpoint /identify doit retourner null quand PlantNet ne trouve rien."""
    with patch("gsie_api.engines.botanical.router.PlantNetClient") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.identify = _mock_plantnet_identify(None)
        with TestClient(create_app()) as client:
            response = client.post(
                "/api/v1/botanical/identify",
                files={"file": ("test.jpg", b"\x89PNG fake", "image/jpeg")},
                headers=_auth_headers(),
            )
    assert response.status_code == 200
    assert response.json() is None


def should_return_400_when_file_is_empty(mock_lifespan: object) -> None:
    """L'endpoint /identify doit retourner 400 quand le fichier est vide."""
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/botanical/identify",
            files={"file": ("test.jpg", b"", "image/jpeg")},
            headers=_auth_headers(),
        )
    assert response.status_code == 400
    assert "vide" in response.json()["detail"].lower()


def should_return_400_when_format_unsupported(mock_lifespan: object) -> None:
    """L'endpoint /identify doit retourner 400 pour un format non supporté."""
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/botanical/identify",
            files={"file": ("test.gif", b"GIF89a", "image/gif")},
            headers=_auth_headers(),
        )
    assert response.status_code == 400
    assert "gif" in response.json()["detail"].lower()


def should_return_502_when_plantnet_api_fails(mock_lifespan: object) -> None:
    """L'endpoint /identify doit retourner 502 quand l'API PlantNet échoue."""
    from gsie_api.engines.botanical.plantnet_client import PlantNetClientError

    with patch("gsie_api.engines.botanical.router.PlantNetClient") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.identify = AsyncMock(side_effect=PlantNetClientError("API indisponible"))
        with TestClient(create_app()) as client:
            response = client.post(
                "/api/v1/botanical/identify",
                files={"file": ("test.jpg", b"\x89PNG fake", "image/jpeg")},
                headers=_auth_headers(),
            )
    assert response.status_code == 502
    assert "API indisponible" in response.json()["detail"]


def should_return_401_when_no_auth(mock_lifespan: object) -> None:
    """L'endpoint /identify doit retourner 401 sans authentification."""
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/botanical/identify",
            files={"file": ("test.jpg", b"\x89PNG fake", "image/jpeg")},
        )
    assert response.status_code == 401

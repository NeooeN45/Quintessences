"""Client HTTP réel vers les API Géoplateforme IGN (aucune clé requise).

Deux endpoints, documentés dans GIS_ENGINE.md §8.2 et vérifiés
manuellement (réponses réelles, pas de données simulées — ADR-007) :

- API Carto — module Cadastre : https://apicarto.ign.fr/api/doc/cadastre
  GET /api/cadastre/parcelle?code_insee=...&section=...&numero=...
  → GeoJSON FeatureCollection (EPSG:4326)

- API de calcul altimétrique :
  https://geoplateforme.pages.gpf-tech.ign.fr/altimetrie/api-rest-calcul-altimetrique/
  GET /altimetrie/1.0/calcul/alti/rest/elevation.json?lon=...&lat=...
  → {"elevations": [<mètres>]}
"""

from __future__ import annotations

from typing import Any

import httpx

_CADASTRE_BASE_URL = "https://apicarto.ign.fr/api/cadastre/parcelle"
_ALTIMETRIE_BASE_URL = "https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json"
_DEFAULT_TIMEOUT = 30.0


class IGNClientError(Exception):
    """Erreur lors d'un appel aux API IGN (réseau, réponse inattendue)."""


class IGNClient:
    """Client HTTP pour les API Géoplateforme IGN — aucune authentification requise."""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    async def get_parcelle(
        self, code_insee: str, section: str, numero: str
    ) -> dict[str, Any] | None:
        """Récupère une parcelle cadastrale unique (GeoJSON Feature, EPSG:4326).

        Returns:
            Le Feature GeoJSON, ou None si aucune parcelle ne correspond.

        Raises:
            IGNClientError: en cas d'erreur réseau ou de réponse HTTP en échec.
        """
        params = {"code_insee": code_insee, "section": section, "numero": numero}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(_CADASTRE_BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise IGNClientError(f"Échec de l'appel API Carto Cadastre : {exc}") from exc

        features: list[dict[str, Any]] = data.get("features", [])
        if not features:
            return None
        return features[0]

    async def get_altitude(self, latitude: float, longitude: float) -> float:
        """Récupère l'altitude (mètres, RGE ALTI) pour un point WGS 84.

        Raises:
            IGNClientError: en cas d'erreur réseau, de réponse HTTP en échec,
                ou de réponse sans élévation exploitable.
        """
        params: dict[str, str | float] = {
            "lon": longitude,
            "lat": latitude,
            "resource": "ign_rge_alti_wld",
            "zonly": "true",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(_ALTIMETRIE_BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise IGNClientError(f"Échec de l'appel API de calcul altimétrique : {exc}") from exc

        elevations = data.get("elevations", [])
        if not elevations:
            raise IGNClientError(f"Réponse altimétrique sans élévation exploitable : {data}")
        return float(elevations[0])

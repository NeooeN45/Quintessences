"""Client HTTP réel vers l'API SoilGrids (ISRIC, aucune clé requise).

Endpoint vérifié manuellement le 2026-07-17 (pas de données simulées —
ADR-007) : GET https://rest.isric.org/soilgrids/v2.0/properties/query

Les valeurs brutes retournées sont mises à l'échelle par un
`d_factor` propre à chaque propriété (ex. pH*10, g/kg → %) — vérifié
empiriquement : clay=283 + sand=233 + silt=483 (d_factor=10 chacun)
donnent 28.3% + 23.3% + 48.3% ≈ 100%, confirmant la division par
d_factor pour obtenir la valeur réelle.

Référence scientifique du produit (peer-reviewed, plafond B — voir
docstring schemas.py) : Poggio, L. et al. (2021), *SoilGrids 2.0:
producing soil information for the globe with quantified spatial
uncertainty*, SOIL, 7, 217-240.
"""

from __future__ import annotations

from typing import Any

import httpx

_SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
_DEFAULT_TIMEOUT = 30.0

# Unités cibles après division par d_factor (SoilGrids §unit_measure).
_UNITS = {
    "phh2o": "pH",
    "clay": "%",
    "sand": "%",
    "silt": "%",
    "bdod": "kg/dm³",
    "soc": "g/kg",
}


class SoilGridsClientError(Exception):
    """Erreur lors d'un appel à l'API SoilGrids (réseau, réponse inattendue)."""


class SoilGridsClient:
    """Client HTTP pour l'API SoilGrids — aucune authentification requise."""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    async def get_properties(
        self, latitude: float, longitude: float, properties: list[str], depth: str = "0-5cm"
    ) -> dict[str, float]:
        """Récupère les propriétés de sol demandées pour un point et une profondeur.

        Returns:
            Un dict {nom_propriété: valeur_réelle} — les propriétés sans
            donnée disponible à ce point (mean=null, zones sans
            couverture) sont omises, jamais remplacées par une valeur
            par défaut (ADR-007).

        Raises:
            SoilGridsClientError: en cas d'erreur réseau ou de réponse HTTP en échec.
        """
        params: list[tuple[str, str | int | float | bool | None]] = [
            ("lon", longitude),
            ("lat", latitude),
            ("depth", depth),
            ("value", "mean"),
        ]
        params.extend(("property", prop) for prop in properties)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(_SOILGRIDS_URL, params=params)
                response.raise_for_status()
                data: dict[str, Any] = response.json()
        except httpx.HTTPError as exc:
            raise SoilGridsClientError(f"Échec de l'appel SoilGrids : {exc}") from exc

        layers: list[dict[str, Any]] = data.get("properties", {}).get("layers", [])
        results: dict[str, float] = {}
        for layer in layers:
            depths = layer.get("depths", [])
            if not depths:
                continue
            raw_mean = depths[0].get("values", {}).get("mean")
            if raw_mean is None:
                continue
            d_factor = layer.get("unit_measure", {}).get("d_factor", 1)
            results[layer["name"]] = raw_mean / d_factor

        return results

    @staticmethod
    def unit_for(property_name: str) -> str:
        """Retourne l'unité cible d'une propriété SoilGrids connue."""
        return _UNITS.get(property_name, "")

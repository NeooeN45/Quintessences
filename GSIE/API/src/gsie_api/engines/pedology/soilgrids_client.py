"""Client HTTP réel vers l'API SoilGrids (ISRIC, aucune clé requise).

Endpoint vérifié manuellement le 2026-07-17 (pas de données simulées —
ADR-009) : GET https://rest.isric.org/soilgrids/v2.0/properties/query

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

from gsie_api.shared.http_client import ResilientHttpClient

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


def _facteur_de_division(layer: dict[str, Any]) -> float:
    """Facteur d'échelle déclaré par la couche, refusé s'il est absent.

    SoilGrids renvoie des entiers mis à l'échelle : le pH arrive multiplié par
    dix, les teneurs en g/kg pour un résultat attendu en pourcentage. `d_factor`
    est le diviseur qui rétablit la valeur réelle — la docstring du module le
    vérifie empiriquement (clay 283 + sand 233 + silt 483, divisés par dix, font
    bien 100 %).

    Le code retombait sur `1` quand `unit_measure` manquait. Vérifié : une
    couche `phh2o` de moyenne 52 sans `unit_measure` ressortait à **pH 52**,
    hors de l'échelle physique 0–14. La règle `pedologie_pH < 5.5` évaluait
    alors `52 < 5.5` — Faux — et un sol acide se diagnostiquait basique, sans
    qu'aucune erreur ne soit levée.

    Un facteur absent ne vaut pas un : il signifie que **l'échelle est
    inconnue**. Supposer l'identité, c'est inventer une conversion, ce que
    `ADR-009` interdit — et l'inventer sur une grandeur qui fonde un diagnostic
    pédologique.

    `d_factor` valant explicitement `1` reste légitime : certaines propriétés
    sont déjà dans l'unité cible. C'est l'omission qui est refusée, pas la
    valeur.

    Raises:
        SoilGridsClientError: si `unit_measure.d_factor` est absent ou nul.
    """
    unit_measure = layer.get("unit_measure")
    facteur = unit_measure.get("d_factor") if isinstance(unit_measure, dict) else None
    if facteur is None:
        raise SoilGridsClientError(
            f"couche SoilGrids « {layer.get('name', '?')} » sans "
            "`unit_measure.d_factor` : l'échelle de la valeur est inconnue et "
            "ne peut pas être supposée"
        )
    if facteur == 0:
        raise SoilGridsClientError(
            f"couche SoilGrids « {layer.get('name', '?')} » avec un `d_factor` "
            "nul : division impossible"
        )
    return float(facteur)


class SoilGridsClient(ResilientHttpClient):
    """Client HTTP pour l'API SoilGrids — aucune authentification requise."""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        super().__init__(timeout)

    @property
    def exception_class(self) -> type[Exception]:
        return SoilGridsClientError

    @property
    def base_url(self) -> str:
        return "https://rest.isric.org/soilgrids/v2.0"

    async def get_properties(
        self, latitude: float, longitude: float, properties: list[str], depth: str = "0-5cm"
    ) -> dict[str, float]:
        """Récupère les propriétés de sol demandées pour un point et une profondeur.

        Returns:
            Un dict {nom_propriété: valeur_réelle} — les propriétés sans
            donnée disponible à ce point (mean=null, zones sans
            couverture) sont omises, jamais remplacées par une valeur
            par défaut (ADR-009).

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

        data: dict[str, Any] = await self._get_json(
            "/properties/query",
            params=params,
            error_label="de l'appel SoilGrids",
        )
        layers: list[dict[str, Any]] = data.get("properties", {}).get("layers", [])
        results: dict[str, float] = {}
        for layer in layers:
            depths = layer.get("depths", [])
            if not depths:
                continue
            raw_mean = depths[0].get("values", {}).get("mean")
            if raw_mean is None:
                continue
            results[layer["name"]] = raw_mean / _facteur_de_division(layer)

        return results

    @staticmethod
    def unit_for(property_name: str) -> str:
        """Retourne l'unité cible d'une propriété SoilGrids connue."""
        return _UNITS.get(property_name, "")

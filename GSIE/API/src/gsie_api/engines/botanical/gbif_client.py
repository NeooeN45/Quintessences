"""Client HTTP réel vers l'API GBIF (aucune clé requise pour la lecture).

Deux endpoints, vérifiés manuellement le 2026-07-17 (pas de données
simulées — ADR-009) :

- GBIF Species Match : https://www.gbif.org/developer/species
  GET /v1/species/match?name=...
  → meilleure correspondance taxonomique, résout les synonymes vers le
    taxon accepté (`acceptedUsageKey`), confirmé sur Quercus sessiliflora
    -> Quercus petraea.

- GBIF Vernacular Names : GET /v1/species/{key}/vernacularNames
  → noms vernaculaires par langue (ISO 639-2, ex. "fra").
"""

from __future__ import annotations

from typing import Any

from gsie_api.shared.http_client import ResilientHttpClient

_SPECIES_MATCH_URL = "https://api.gbif.org/v1/species/match"
_VERNACULAR_NAMES_URL_TEMPLATE = "https://api.gbif.org/v1/species/{key}/vernacularNames"
_DEFAULT_TIMEOUT = 30.0


class GBIFClientError(Exception):
    """Erreur lors d'un appel à l'API GBIF (réseau, réponse inattendue)."""


class GBIFClient(ResilientHttpClient):
    """Client HTTP pour l'API GBIF — aucune authentification requise en lecture."""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        super().__init__(timeout)

    @property
    def exception_class(self) -> type[Exception]:
        return GBIFClientError

    @property
    def base_url(self) -> str:
        return "https://api.gbif.org/v1"

    async def match_species(self, name: str) -> dict[str, Any] | None:
        """Résout un nom scientifique vers son meilleur taxon GBIF.

        Returns:
            Le résultat de correspondance, ou None si aucun taxon
            n'a pu être identifié (`matchType` == "NONE").

        Raises:
            GBIFClientError: en cas d'erreur réseau ou de réponse HTTP en échec.
        """
        data: dict[str, Any] = await self._get_json(
            "/species/match",
            params={"name": name},
            error_label="de l'appel GBIF Species Match",
        )
        if data.get("matchType") == "NONE" or "usageKey" not in data:
            return None
        return data

    async def get_vernacular_name(self, taxon_key: int, language: str = "fra") -> str | None:
        """Récupère le premier nom vernaculaire disponible pour une langue donnée.

        Raises:
            GBIFClientError: en cas d'erreur réseau ou de réponse HTTP en échec.
        """
        path = _VERNACULAR_NAMES_URL_TEMPLATE.format(key=taxon_key)
        data: dict[str, Any] = await self._get_json(
            path,
            params={"language": language},
            error_label="l'appel GBIF Vernacular Names",
        )
        results: list[dict[str, Any]] = data.get("results", [])
        if not results:
            return None
        return str(results[0]["vernacularName"])

"""Client HTTP réel vers TAXREF (référentiel taxonomique français, MNHN).

L'infrastructure officielle MNHN/INPN (`taxref.mnhn.fr`, `inpn.mnhn.fr`)
est dégradée depuis le piratage du Muséum de septembre 2025 (vérifié
manuellement le 2026-07-18 : redirection anormale sur l'endpoint de
recherche officiel). GBIF héberge un miroir complet du référentiel
TAXREF comme jeu de données propre (`datasetKey`
`0e61f8fe-7d25-4f81-ada7-d970bbb2c6d6`, cf.
https://www.gbif.org/dataset/0e61f8fe-7d25-4f81-ada7-d970bbb2c6d6) —
vérifié réel : `Quercus petraea` → `taxonID=521658`, identique au
CD_NOM du dataset d'indigénat (Bellifa et al. 2026) déjà ingéré.

Ce client interroge donc GBIF Species Search, filtré sur ce
`datasetKey`, plutôt que l'API MNHN directe — même contenu TAXREF,
infrastructure disponible.
"""

from __future__ import annotations

from typing import Any

from gsie_api.shared.http_client import ResilientHttpClient

_SPECIES_SEARCH_URL = "https://api.gbif.org/v1/species/search"
_TAXREF_DATASET_KEY = "0e61f8fe-7d25-4f81-ada7-d970bbb2c6d6"
_DEFAULT_TIMEOUT = 30.0


class TaxrefClientError(Exception):
    """Erreur lors d'un appel au miroir TAXREF (réseau, réponse inattendue)."""


class TaxrefClient(ResilientHttpClient):
    """Client TAXREF via le miroir GBIF — aucune authentification requise."""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        super().__init__(timeout)

    @property
    def exception_class(self) -> type[Exception]:
        return TaxrefClientError

    @property
    def base_url(self) -> str:
        return "https://api.gbif.org/v1"

    async def search(self, nom_scientifique: str) -> dict[str, Any] | None:
        """Résout un nom scientifique vers son entrée TAXREF réelle.

        Returns:
            Le meilleur résultat TAXREF (statut ACCEPTED priorisé), ou
            None si aucune entrée ne correspond — jamais un cd_nom
            inventé (ADR-009).

        Raises:
            TaxrefClientError: en cas d'erreur réseau ou de réponse HTTP en échec.
        """
        data: dict[str, Any] = await self._get_json(
            "/species/search",
            params={
                "q": nom_scientifique,
                "datasetKey": _TAXREF_DATASET_KEY,
                "limit": 20,
            },
            error_label="de l'appel au miroir GBIF de TAXREF",
        )
        results: list[dict[str, Any]] = data.get("results", [])
        if not results:
            return None

        accepted = [r for r in results if r.get("taxonomicStatus") == "ACCEPTED"]
        return accepted[0] if accepted else results[0]

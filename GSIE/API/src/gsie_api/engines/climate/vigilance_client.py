"""Client HTTP réel vers l'API Bulletin Vigilance (portail-api.meteofrance.fr).

Endpoint vérifié manuellement le 2026-07-18 (clé de compte requise,
souscription gratuite à l'API `DonneesPubliquesVigilance`, quota
60 req/min) :

  GET https://public-api.meteofrance.fr/public/DPVigilance/v1/cartevigilance/encours

Réponse JSON imbriquée (vérifiée réelle, 2026-07-18T04:00:13Z) :
`product.periods[]` (une par échéance J/J+1) contient
`timelaps.domain_ids[]` (un par domaine, `domain_id` = code
département/zone) avec `max_color_id` et `phenomenon_items[]`
(`phenomenon_id`, `phenomenon_max_color_id`). Les identifiants de
phénomène et de couleur sont des codes numériques Météo-France — leur
table de correspondance officielle (ex. 1=vert, 2=jaune, 3=orange,
4=rouge ; phénomènes vent/pluie/orage/etc.) n'est pas vérifiée ici et
n'est donc pas réinterprétée (ADR-007), seulement transmise brute.
"""

from __future__ import annotations

import httpx

from gsie_api.core.config import get_settings

_URL = "https://public-api.meteofrance.fr/public/DPVigilance/v1/cartevigilance/encours"
_DEFAULT_TIMEOUT = 30.0


class VigilanceClientError(Exception):
    """Erreur lors d'un appel à l'API Vigilance (réseau, auth, réponse inattendue)."""


class VigilanceClient:
    """Client pour l'API Bulletin Vigilance — nécessite METEOFRANCE_API_KEY (.env)."""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout
        self._api_key = get_settings().meteofrance_api_key

    async def get_carte_vigilance(self) -> dict:
        """Récupère la carte de vigilance réelle en cours (JSON brut Météo-France).

        Raises:
            VigilanceClientError: si la clé est absente, l'appel réseau
                échoue, ou la réponse HTTP est en échec.
        """
        if not self._api_key:
            raise VigilanceClientError(
                "METEOFRANCE_API_KEY absente — impossible d'appeler l'API Vigilance"
            )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(_URL, headers={"apikey": self._api_key})
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            raise VigilanceClientError(f"Échec de l'appel à l'API Vigilance : {exc}") from exc

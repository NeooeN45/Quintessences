"""Client HTTP réel vers l'API Météo des forêts (portail-api.meteofrance.fr).

Endpoint vérifié manuellement le 2026-07-18 (pas de données simulées —
ADR-007), clé de compte requise (souscription gratuite à l'API
`DonneesPubliquesMeteoForets`, quota 100 req/min) :

  GET https://public-api.meteofrance.fr/public/DPMeteoForets/v1/carte/encours

Réponse CSV point-virgule (vérifiée sur un échantillon réel, 2026-07-17) :
`reference_time;dep_code;niveau_j1;niveau_j2;dep_nom` — un niveau de
danger de feux de forêt (entier, échelle Météo-France) par département
français, pour J+1 et J+2.
"""

from __future__ import annotations

import csv
import io

import httpx

from gsie_api.core.config import get_settings

_BASE_URL = "https://public-api.meteofrance.fr/public/DPMeteoForets/v1"
_DEFAULT_TIMEOUT = 30.0


class MeteoFranceClientError(Exception):
    """Erreur lors d'un appel à l'API Météo des forêts (réseau, auth, réponse inattendue)."""


class MeteoFranceClient:
    """Client pour l'API Météo des forêts — nécessite METEOFRANCE_API_KEY (.env)."""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout
        self._api_key = get_settings().meteofrance_api_key

    async def get_danger_feux_departements(self) -> list[dict[str, str]]:
        """Récupère le niveau de danger de feux de forêt réel pour tous les départements.

        Returns:
            Une ligne par département : reference_time, dep_code,
            niveau_j1, niveau_j2, dep_nom.

        Raises:
            MeteoFranceClientError: si la clé est absente, l'appel réseau
                échoue, ou la réponse HTTP est en échec — jamais de
                niveau de danger approximé (ADR-007).
        """
        if not self._api_key:
            raise MeteoFranceClientError(
                "METEOFRANCE_API_KEY absente — impossible d'appeler l'API Météo des forêts"
            )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    f"{_BASE_URL}/carte/encours",
                    headers={"apikey": self._api_key},
                )
                response.raise_for_status()
                csv_text = response.text
        except httpx.HTTPError as exc:
            raise MeteoFranceClientError(
                f"Échec de l'appel à l'API Météo des forêts : {exc}"
            ) from exc

        reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")
        return list(reader)

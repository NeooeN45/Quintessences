"""Client HTTP réel vers l'API Météo des forêts (portail-api.meteofrance.fr).

Endpoint vérifié manuellement le 2026-07-18 (pas de données simulées —
ADR-009), clé de compte requise (souscription gratuite à l'API
`DonneesPubliquesMeteoForets`, quota 100 req/min) :

  GET https://public-api.meteofrance.fr/public/DPMeteoForets/v1/carte/encours

Réponse CSV point-virgule (vérifiée sur un échantillon réel, 2026-07-17) :
`reference_time;dep_code;niveau_j1;niveau_j2;dep_nom` — un niveau de
danger de feux de forêt (entier, échelle Météo-France) par département
français, pour J+1 et J+2.
"""

from __future__ import annotations

from gsie_api.core.config import get_settings
from gsie_api.shared.http_client import ResilientCsvClient

_BASE_URL = "https://public-api.meteofrance.fr/public/DPMeteoForets/v1"
_DEFAULT_TIMEOUT = 30.0


class MeteoFranceClientError(Exception):
    """Erreur lors d'un appel à l'API Météo des forêts (réseau, auth, réponse inattendue)."""


class MeteoFranceClient(ResilientCsvClient):
    """Client pour l'API Météo des forêts — nécessite METEOFRANCE_API_KEY (.env)."""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        super().__init__(timeout)

    @property
    def exception_class(self) -> type[Exception]:
        return MeteoFranceClientError

    @property
    def base_url(self) -> str:
        return "https://public-api.meteofrance.fr"

    def auth_headers(self) -> dict[str, str]:
        api_key = get_settings().meteofrance_api_key
        if not api_key:
            raise MeteoFranceClientError(
                "METEOFRANCE_API_KEY absente — impossible d'appeler l'API Météo des forêts"
            )
        return {"apikey": api_key}

    async def get_danger_feux_departements(self) -> list[dict[str, str | None]]:
        """Récupère le niveau de danger de feux de forêt réel pour tous les départements.

        Returns:
            Une ligne par département : reference_time, dep_code,
            niveau_j1, niveau_j2, dep_nom.

        Raises:
            MeteoFranceClientError: si la clé est absente, l'appel réseau
                échoue, ou la réponse HTTP est en échec — jamais de
                niveau de danger approximé (ADR-009).
        """
        return await self._get_csv(
            "/public/DPMeteoForets/v1/carte/encours",
            error_label="de l'appel à l'API Météo des forêts",
        )

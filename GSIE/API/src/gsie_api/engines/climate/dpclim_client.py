"""Client HTTP réel vers l'API Données Climatologiques (DPClim, portail-api.meteofrance.fr).

Endpoints vérifiés manuellement le 2026-07-18 (clé de compte requise,
souscription gratuite à l'API `DonneesPubliquesClimatologie`, quota
100 req/min). Flux en 3 étapes, confirmé par appels réels :

1. GET /public/DPClim/v1/liste-stations/{pas_de_temps}?id-departement=XX
   -> liste JSON des stations du département (postePublic, posteOuvert).
2. GET /public/DPClim/v1/commande-station/{pas_de_temps}
       ?id-station=XXXXXXXX&date-deb-periode=...&date-fin-periode=...
   -> 202, corps JSON {"elaboreProduitAvecDemandeResponse": {"return": "<id_cmde>"}}
      (traitement asynchrone côté Météo-France).
3. GET /public/DPClim/v1/commande/fichier?id-cmde=<id_cmde>
   -> 404 tant que la commande n'est pas prête (ou station sans donnée
      sur la période — même code, pas de distinction fiable), 201 avec
      le CSV (point-virgule, en-tête variable selon la station — voir
      schemas.py) une fois prête. Testé réel : prêt en 3-10s.

Nombres décimaux du CSV en notation française (virgule) — ex. "12,4"
pour 12.4°C — convertis par l'engine, pas ce client (rôle du client :
transport brut uniquement).
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, cast

import httpx

from gsie_api.core.config import get_settings

_BASE_URL = "https://public-api.meteofrance.fr/public/DPClim/v1"
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_POLL_INTERVAL_S = 3.0
_DEFAULT_MAX_POLL_ATTEMPTS = 10


class DPClimClientError(Exception):
    """Erreur lors d'un appel à l'API DPClim (réseau, auth, réponse inattendue)."""


class DPClimClient:
    """Client pour l'API Données Climatologiques — nécessite METEOFRANCE_API_KEY (.env)."""

    def __init__(
        self,
        timeout: float = _DEFAULT_TIMEOUT,
        poll_interval_s: float = _DEFAULT_POLL_INTERVAL_S,
        max_poll_attempts: int = _DEFAULT_MAX_POLL_ATTEMPTS,
    ) -> None:
        self._timeout = timeout
        self._poll_interval_s = poll_interval_s
        self._max_poll_attempts = max_poll_attempts
        self._api_key = get_settings().meteofrance_api_key

    def _require_api_key(self) -> str:
        if not self._api_key:
            raise DPClimClientError(
                "METEOFRANCE_API_KEY absente — impossible d'appeler l'API DPClim"
            )
        return self._api_key

    async def list_stations(
        self, id_departement: str, pas_de_temps: str = "quotidienne"
    ) -> list[dict[str, Any]]:
        """Liste réelle des stations d'un département pour un pas de temps donné.

        Raises:
            DPClimClientError: si la clé est absente ou l'appel échoue.
        """
        api_key = self._require_api_key()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    f"{_BASE_URL}/liste-stations/{pas_de_temps}",
                    params={"id-departement": id_departement},
                    headers={"apikey": api_key},
                )
                response.raise_for_status()
                return cast("list[dict[str, Any]]", response.json())
        except httpx.HTTPError as exc:
            raise DPClimClientError(f"Échec de liste-stations DPClim : {exc}") from exc

    async def get_donnees_quotidiennes(
        self, id_station: str, date_deb_periode: str, date_fin_periode: str
    ) -> str:
        """Exécute le flux complet (commande + polling + récupération) et retourne le CSV brut.

        Args:
            date_deb_periode / date_fin_periode : ISO 8601 avec heure
                (ex. "2026-06-01T00:00:00Z"), format exact requis par
                l'API (vérifié réel).

        Returns:
            Le contenu CSV brut (texte, point-virgule) de la commande.

        Raises:
            DPClimClientError: clé absente, échec réseau, ou commande
                jamais prête après `max_poll_attempts` tentatives —
                jamais de donnée climatologique approximée (ADR-007).
        """
        api_key = self._require_api_key()
        id_cmde = await self._commander(id_station, date_deb_periode, date_fin_periode, api_key)
        return await self._recuperer_fichier(id_cmde, api_key)

    async def _commander(
        self, id_station: str, date_deb_periode: str, date_fin_periode: str, api_key: str
    ) -> str:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    f"{_BASE_URL}/commande-station/quotidienne",
                    params={
                        "id-station": id_station,
                        "date-deb-periode": date_deb_periode,
                        "date-fin-periode": date_fin_periode,
                    },
                    headers={"apikey": api_key},
                )
                response.raise_for_status()
                body = json.loads(response.text)
        except httpx.HTTPError as exc:
            raise DPClimClientError(f"Échec de commande-station DPClim : {exc}") from exc
        except (json.JSONDecodeError, KeyError) as exc:
            raise DPClimClientError(f"Réponse commande-station DPClim illisible : {exc}") from exc

        try:
            return cast("str", body["elaboreProduitAvecDemandeResponse"]["return"])
        except KeyError as exc:
            raise DPClimClientError(
                f"Réponse commande-station DPClim sans numéro de commande : {body}"
            ) from exc

    async def _recuperer_fichier(self, id_cmde: str, api_key: str) -> str:
        last_error: httpx.HTTPStatusError | None = None
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for _attempt in range(self._max_poll_attempts):
                try:
                    response = await client.get(
                        f"{_BASE_URL}/commande/fichier",
                        params={"id-cmde": id_cmde},
                        headers={"apikey": api_key},
                    )
                    response.raise_for_status()
                    return response.text
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code != 404:
                        raise DPClimClientError(
                            f"Échec de commande/fichier DPClim : {exc}"
                        ) from exc
                    last_error = exc
                    await asyncio.sleep(self._poll_interval_s)
                except httpx.HTTPError as exc:
                    raise DPClimClientError(f"Échec de commande/fichier DPClim : {exc}") from exc

        raise DPClimClientError(
            f"Commande DPClim {id_cmde} jamais prête après "
            f"{self._max_poll_attempts} tentatives (dernière erreur : {last_error})"
        )

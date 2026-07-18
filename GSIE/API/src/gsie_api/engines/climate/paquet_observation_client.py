"""Client HTTP réel vers l'API Package Observations (portail-api.meteofrance.fr).

Endpoint vérifié manuellement le 2026-07-18 (clé de compte requise,
souscription gratuite à l'API `DonneesPubliquesPaquetObservation`,
quota 100 req/min) :

  GET https://public-api.meteofrance.fr/public/DPPaquetObs/v2/paquet/horaire
      ?id-departement=XX&format=csv

Réponse CSV point-virgule (vérifiée réelle, département 33, 2026-07-18) :
observations horaires des 24 dernières heures, toutes stations du
département — mêmes colonnes/unités que le flux SYNOP (t/td/tx/tn en
Kelvin, pmer en Pa, dd/ff/rr1 déjà en unité cible), voir engine.py pour
les conversions.
"""

from __future__ import annotations

import csv
import io

import httpx

from gsie_api.core.config import get_settings

_URL = "https://public-api.meteofrance.fr/public/DPPaquetObs/v2/paquet/horaire"
_DEFAULT_TIMEOUT = 30.0


class PaquetObservationClientError(Exception):
    """Erreur lors d'un appel à l'API Package Observations (réseau, auth, réponse inattendue)."""


class PaquetObservationClient:
    """Client pour l'API Package Observations — nécessite METEOFRANCE_API_KEY (.env)."""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout
        self._api_key = get_settings().meteofrance_api_key

    async def get_observations_horaires(self, id_departement: str) -> list[dict[str, str]]:
        """Récupère les observations horaires réelles des 24h, toutes stations d'un département.

        Raises:
            PaquetObservationClientError: si la clé est absente, l'appel
                réseau échoue, ou la réponse HTTP est en échec.
        """
        if not self._api_key:
            raise PaquetObservationClientError(
                "METEOFRANCE_API_KEY absente — impossible d'appeler l'API Package Observations"
            )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    _URL,
                    params={"id-departement": id_departement, "format": "csv"},
                    headers={"apikey": self._api_key},
                )
                response.raise_for_status()
                csv_text = response.text
        except httpx.HTTPError as exc:
            raise PaquetObservationClientError(
                f"Échec de l'appel à l'API Package Observations : {exc}"
            ) from exc

        reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")
        return list(reader)

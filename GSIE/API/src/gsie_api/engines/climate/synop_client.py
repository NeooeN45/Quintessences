"""Client HTTP réel vers les données SYNOP Météo-France (data.gouv.fr).

Endpoint vérifié manuellement le 2026-07-17 (pas de données simulées —
ADR-007), aucune clé requise :

  GET https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/OBS/SYNOP/synop_{year}.csv.gz

CSV point-virgule, une ligne par observation/station/horodatage. Colonnes
pertinentes v1 (vérifiées sur un échantillon réel, station 07510
Bordeaux-Mérignac, 2026-07-16T21:00Z) : `t`/`td` (température/point de
rosée, Kelvin), `u` (humidité, %), `pmer` (pression réduite au niveau de
la mer, Pa), `dd`/`ff` (direction °, vitesse m/s), `rr1` (précipitations
1h, mm). Champ vide = valeur non mesurée à cette station — omise, jamais
remplacée par une valeur par défaut.

Limite connue : télécharge le fichier annuel complet (~18 Mo compressés
pour l'année en cours) à chaque appel — pas de cache ni d'endpoint
temps réel plus léger identifié à ce jour. À améliorer si le volume
d'appels le justifie (cache local, endpoint horaire dédié).
"""

from __future__ import annotations

import csv
import gzip
import io
from datetime import UTC, datetime

import httpx

_SYNOP_URL_TEMPLATE = (
    "https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/OBS/SYNOP/synop_{year}.csv.gz"
)
_DEFAULT_TIMEOUT = 60.0


class SynopClientError(Exception):
    """Erreur lors d'un appel aux données SYNOP (réseau, réponse inattendue)."""


class SynopClient:
    """Client pour les archives SYNOP Météo-France — aucune authentification requise."""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    async def get_latest_observation(
        self, station_id: str, year: int | None = None
    ) -> dict[str, str] | None:
        """Récupère la dernière observation réelle d'une station SYNOP.

        Returns:
            La ligne CSV (dict colonne -> valeur brute) de l'observation
            la plus récente pour cette station, ou None si la station
            n'apparaît pas dans le fichier de l'année demandée.

        Raises:
            SynopClientError: en cas d'erreur réseau ou de réponse HTTP en échec.
        """
        year = year or datetime.now(UTC).year
        url = _SYNOP_URL_TEMPLATE.format(year=year)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                raw_bytes = response.content
        except httpx.HTTPError as exc:
            raise SynopClientError(f"Échec du téléchargement SYNOP {year} : {exc}") from exc

        try:
            csv_text = gzip.decompress(raw_bytes).decode("utf-8")
        except OSError as exc:
            raise SynopClientError(f"Réponse SYNOP {year} illisible (gzip) : {exc}") from exc

        reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")
        latest: dict[str, str] | None = None
        for row in reader:
            if row.get("geo_id_wmo") != station_id:
                continue
            if latest is None or row["validity_time"] > latest["validity_time"]:
                latest = row

        return latest

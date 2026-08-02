"""Client HTTP réel vers les données SYNOP Météo-France (data.gouv.fr).

Endpoint vérifié manuellement le 2026-07-17 (pas de données simulées —
ADR-009), aucune clé requise :

  GET https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/OBS/SYNOP/synop_{year}.csv.gz

CSV point-virgule, une ligne par observation/station/horodatage. Colonnes
pertinentes v1 (vérifiées sur un échantillon réel, station 07510
Bordeaux-Mérignac, 2026-07-16T21:00Z) : `t`/`td` (température/point de
rosée, Kelvin), `u` (humidité, %), `pmer` (pression réduite au niveau de
la mer, Pa), `dd`/`ff` (direction °, vitesse m/s), `rr1` (précipitations
1h, mm). Champ vide = valeur non mesurée à cette station — omise, jamais
remplacée par une valeur par défaut.

Cache : le fichier annuel (~18 Mo compressés) est téléchargé une fois
par année et conservé en mémoire pendant `_CACHE_TTL_SECONDS` (défaut
1h). Les appels suivants pour la même année servent depuis le cache,
évitant un téléchargement répété. Le cache est par instance de client ;
une instance par processus est recommandée.
"""

from __future__ import annotations

import csv
import gzip
import io
import time
from datetime import UTC, datetime

from gsie_api.shared.http_client import ResilientHttpClient

_SYNOP_URL_TEMPLATE = (
    "https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/OBS/SYNOP/synop_{year}.csv.gz"
)
_DEFAULT_TIMEOUT = 60.0
_CACHE_TTL_SECONDS = 3600  # 1 heure — le fichier annuel évolue peu


class SynopClientError(Exception):
    """Erreur lors d'un appel aux données SYNOP (réseau, réponse inattendue)."""


class _CachedFile:
    """Cache en mémoire d'un fichier SYNOP annuel décompressé."""

    __slots__ = ("year", "csv_text", "fetched_at")

    def __init__(self, year: int, csv_text: str) -> None:
        self.year = year
        self.csv_text = csv_text
        self.fetched_at = time.monotonic()

    def is_expired(self, ttl: float) -> bool:
        return (time.monotonic() - self.fetched_at) > ttl


class SynopClient(ResilientHttpClient):
    """Client pour les archives SYNOP Météo-France — aucune authentification requise.

    Cache en mémoire : le fichier annuel (~18 Mo) est téléchargé une fois
    et conservé pendant `_CACHE_TTL_SECONDS` (1h). Les appels suivants
    pour la même année servent depuis le cache.
    """

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        super().__init__(timeout)
        self._cache: dict[int, _CachedFile] = {}

    @property
    def exception_class(self) -> type[Exception]:
        return SynopClientError

    @property
    def base_url(self) -> str:
        return "https://meteofrance.s3.sbg.io.cloud.ovh.net"

    async def _fetch_year(self, year: int) -> str:
        """Télécharge et décompresse le fichier SYNOP d'une année, avec cache.

        Returns:
            Le contenu CSV décompressé (str).
        """
        cached = self._cache.get(year)
        if cached is not None and not cached.is_expired(_CACHE_TTL_SECONDS):
            return cached.csv_text

        url = _SYNOP_URL_TEMPLATE.format(year=year)
        raw_bytes = await self._get_bytes(
            url,
            error_label=f"du téléchargement SYNOP {year}",  # noqa: E501
        )

        try:
            csv_text = gzip.decompress(raw_bytes).decode("utf-8")
        except OSError as exc:
            raise SynopClientError(f"Réponse SYNOP {year} illisible (gzip) : {exc}") from exc

        self._cache[year] = _CachedFile(year, csv_text)
        return csv_text

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
        csv_text = await self._fetch_year(year)

        reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")
        latest: dict[str, str] | None = None
        for row in reader:
            if row.get("geo_id_wmo") != station_id:
                continue
            if latest is None or row["validity_time"] > latest["validity_time"]:
                latest = row

        return latest

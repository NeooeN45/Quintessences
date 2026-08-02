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

Cache : le fichier annuel (~18 Mo compressés, ~centaines de Mo décompressés)
est téléchargé une fois par année et conservé en mémoire pendant
`_CACHE_TTL_SECONDS` (défaut 24h — le fichier annuel évolue peu). Le cache
est borné par `_CACHE_MAX_ENTRIES` (LRU) pour éviter une croissance
non bornée sur des requêtes portant sur de nombreuses années. Un verrou
par année (``asyncio.Lock``) évite que dix requêtes concurrentes sur la
même année ne déclenchent dix téléchargements de 18 Mo avant que la
première n'ait rempli le cache.
"""

from __future__ import annotations

import asyncio
import csv
import gzip
import io
import time
from collections import OrderedDict
from datetime import UTC, datetime

from gsie_api.shared.http_client import ResilientHttpClient

_SYNOP_URL_TEMPLATE = (
    "https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/OBS/SYNOP/synop_{year}.csv.gz"
)
_DEFAULT_TIMEOUT = 60.0
_CACHE_TTL_SECONDS = 86400  # 24h — le fichier annuel évolue peu
_CACHE_MAX_ENTRIES = 5  # LRU : garde au plus 5 années en mémoire


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

    Cache LRU en mémoire : le fichier annuel (~18 Mo compressés) est
    téléchargé une fois et conservé pendant ``_CACHE_TTL_SECONDS`` (24h).
    Le cache est borné à ``_CACHE_MAX_ENTRIES`` entrées (éviction LRU)
    pour éviter une croissance non bornée. Un verrou par année empêche
    les téléchargements concurrents dupliqués.
    """

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        super().__init__(timeout)
        self._cache: OrderedDict[int, _CachedFile] = OrderedDict()
        self._locks: dict[int, asyncio.Lock] = {}

    @property
    def exception_class(self) -> type[Exception]:
        return SynopClientError

    @property
    def base_url(self) -> str:
        return "https://meteofrance.s3.sbg.io.cloud.ovh.net"

    def _get_lock(self, year: int) -> asyncio.Lock:
        """Retourne le verrou pour une année (création paresseuse)."""
        lock = self._locks.get(year)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[year] = lock
        return lock

    def _evict_expired(self) -> None:
        """Évince les entrées expirées (nettoyage à l'accès)."""
        expired = [y for y, cached in self._cache.items() if cached.is_expired(_CACHE_TTL_SECONDS)]
        for y in expired:
            self._cache.pop(y, None)
            self._locks.pop(y, None)

    def _put(self, year: int, csv_text: str) -> None:
        """Insère une entrée dans le cache LRU borné."""
        self._cache[year] = _CachedFile(year, csv_text)
        self._cache.move_to_end(year)
        while len(self._cache) > _CACHE_MAX_ENTRIES:
            evicted_year, _ = self._cache.popitem(last=False)
            self._locks.pop(evicted_year, None)

    async def _fetch_year(self, year: int) -> str:
        """Télécharge et décompresse le fichier SYNOP d'une année, avec cache.

        Returns:
            Le contenu CSV décompressé (str).
        """
        # Nettoyage des entrées expirées à chaque accès.
        self._evict_expired()

        cached = self._cache.get(year)
        if cached is not None and not cached.is_expired(_CACHE_TTL_SECONDS):
            self._cache.move_to_end(year)  # marque comme récemment utilisé (LRU)
            return cached.csv_text

        # Verrou par année : évite que N requêtes concurrentes sur la même
        # année ne déclenchent N téléchargements de 18 Mo avant que la
        # première n'ait rempli le cache.
        lock = self._get_lock(year)
        async with lock:
            # Re-vérification sous le verrou : un autre appelant a pu
            # remplir le cache pendant qu'on attendait.
            cached = self._cache.get(year)
            if cached is not None and not cached.is_expired(_CACHE_TTL_SECONDS):
                self._cache.move_to_end(year)
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

            self._put(year, csv_text)
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

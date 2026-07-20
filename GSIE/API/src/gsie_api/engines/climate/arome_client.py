"""Client HTTP réel vers le modèle AROME (API WCS, portail-api.meteofrance.fr).

Endpoint vérifié manuellement le 2026-07-18 (clé de compte requise,
souscription gratuite à l'API `Modèle AROME`, quota 100 req/min) :

  https://public-api.meteofrance.fr/public/arome/1.0/wcs/
      MF-NWP-HIGHRES-AROME-001-FRANCE-WCS/{GetCapabilities,DescribeCoverage,GetCoverage}

Service WCS (OGC Web Coverage Service 2.0.1), pas une API REST simple —
confirmé en explorant réellement le service : `GetCapabilities` liste
~5700 identifiants de couverture (`CoverageId`, un par paramètre × run
de modèle), `GetCoverage` renvoie un fichier GRIB2 réel (vérifié :
température 2 m, zone Bordeaux, 60 Ko, décodé avec succès par
cfgrib/eccodes — grille 151×201, `t2m` en Kelvin).

Périmètre v1 : un seul paramètre (température à 2 m au-dessus du sol,
`TEMPERATURE__SPECIFIC_HEIGHT_LEVEL_ABOVE_GROUND`), une seule
échéance à la fois, sur le run de modèle le plus récent disponible —
vertical slice au sens RFC-0015 §3.7, pas une intégration exhaustive
des 46 paramètres du service.

Axes de subsetting (vérifiés réels via DescribeCoverage, pas déduits) :
`long`, `lat` (degrés décimaux), `height` (mètres, `2` pour 2 m),
`time` (ISO 8601, sans guillemets dans la requête — testé : avec
guillemets l'API renvoie une erreur malgré une valeur listée comme
valide dans son propre message d'erreur).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import defusedxml.ElementTree as DefusedElementTree
import httpx

from gsie_api.core.config import get_settings

if TYPE_CHECKING:
    from datetime import datetime

_BASE_URL = (
    "https://public-api.meteofrance.fr/public/arome/1.0/wcs/MF-NWP-HIGHRES-AROME-001-FRANCE-WCS"
)
_DEFAULT_TIMEOUT = 60.0
_TEMPERATURE_2M_PREFIX = "TEMPERATURE__SPECIFIC_HEIGHT_LEVEL_ABOVE_GROUND"
_WCS_NS = {"wcs": "http://www.opengis.net/wcs/2.0"}


class AromeClientError(Exception):
    """Erreur lors d'un appel à l'API AROME.

    Réseau, authentification, run indisponible, ou subsetting invalide.
    """


class AromeClient:
    """Client pour le modèle AROME (WCS) — nécessite METEOFRANCE_API_KEY (.env)."""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout
        self._api_key = get_settings().meteofrance_api_key

    def _require_api_key(self) -> str:
        if not self._api_key:
            raise AromeClientError(
                "METEOFRANCE_API_KEY absente — impossible d'appeler l'API AROME"
            )
        return self._api_key

    async def get_latest_temperature_2m_run(self) -> str:
        """Identifie le run le plus récent réellement publié pour la température 2 m.

        Raises:
            AromeClientError: si l'appel réseau échoue ou qu'aucun run
                n'est publié pour ce paramètre.
        """
        api_key = self._require_api_key()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    f"{_BASE_URL}/GetCapabilities",
                    params={"service": "WCS", "version": "2.0.1"},
                    headers={"apikey": api_key},
                )
                response.raise_for_status()
                xml_text = response.text
        except httpx.HTTPError as exc:
            raise AromeClientError(f"Échec de GetCapabilities AROME : {exc}") from exc

        try:
            root = DefusedElementTree.fromstring(xml_text)
        except DefusedElementTree.ParseError as exc:
            raise AromeClientError(f"Réponse GetCapabilities AROME illisible : {exc}") from exc

        coverage_ids: list[str] = [
            element.text
            for element in root.iter(f"{{{_WCS_NS['wcs']}}}CoverageId")
            if element.text and element.text.startswith(_TEMPERATURE_2M_PREFIX)
        ]
        if not coverage_ids:
            raise AromeClientError(
                f"Aucun run publié pour le paramètre {_TEMPERATURE_2M_PREFIX}"
            )

        return max(coverage_ids)

    async def get_temperature_2m_grib(
        self, coverage_id: str, latitude: float, longitude: float, echeance: datetime
    ) -> bytes:
        """Télécharge le GRIB2 réel de température 2 m pour un point et une échéance.

        Le fichier couvre une petite zone (marge de 0,1° autour du
        point) plutôt qu'un point unique — le service WCS de
        Météo-France n'accepte pas un point exact sur cet axe
        (vérifié : nécessite un intervalle, pas une valeur ponctuelle
        pour long/lat).

        Raises:
            AromeClientError: échéance hors du run, coordonnées hors
                domaine AROME France, ou échec réseau — jamais un
                GRIB2 substitué.
        """
        api_key = self._require_api_key()
        echeance_str = echeance.strftime("%Y-%m-%dT%H:%M:%SZ")
        params: list[tuple[str, str | int | float | bool | None]] = [
            ("service", "WCS"),
            ("version", "2.0.1"),
            ("request", "GetCoverage"),
            ("coverageId", coverage_id),
            ("format", "application/wmo-grib"),
            ("subset", f"long({longitude - 0.05},{longitude + 0.05})"),
            ("subset", f"lat({latitude - 0.05},{latitude + 0.05})"),
            ("subset", "height(2)"),
            ("subset", f"time({echeance_str})"),
        ]
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    f"{_BASE_URL}/GetCoverage",
                    params=params,
                    headers={"apikey": api_key},
                )
                response.raise_for_status()
                return response.content
        except httpx.HTTPStatusError as exc:
            raise AromeClientError(
                f"Échec de GetCoverage AROME (échéance {echeance_str} hors run, ou "
                f"coordonnées hors domaine France) : {exc.response.text[:300]}"
            ) from exc
        except httpx.HTTPError as exc:
            raise AromeClientError(f"Échec réseau GetCoverage AROME : {exc}") from exc

"""Compatibilité historique vers le client SoilGrids WCS qualifié.

Le moteur pédologique a longtemps importé ce module. Le nom est conservé
pour les intégrations externes qui n'ont pas encore migré, mais il ne contient
plus de client REST : toute requête passe par le service WCS ISRIC et le
décodage GeoTIFF partagé.
"""

from __future__ import annotations

from gsie_api.data.soilgrids_wcs_client import (
    SoilGridsWcsClient,
    SoilGridsWcsClientError,
)
from gsie_api.data.soilgrids_wcs_policy import SOILGRIDS_WCS_ENDPOINT

_SOILGRIDS_URL = SOILGRIDS_WCS_ENDPOINT


class SoilGridsClientError(SoilGridsWcsClientError):
    """Erreur historique, conservée pour compatibilité des intégrations."""


class SoilGridsClient(SoilGridsWcsClient):
    """Alias de compatibilité dont le backend exclusif est le WCS qualifié."""

    @property
    def exception_class(self) -> type[Exception]:
        return SoilGridsClientError

    async def get_properties(
        self, latitude: float, longitude: float, properties: list[str], depth: str = "0-5cm"
    ) -> dict[str, float]:
        """Ancienne signature, déléguée au point d'entrée WCS."""

        try:
            return await self.query_properties(latitude, longitude, properties, depth)
        except SoilGridsWcsClientError as exc:
            raise SoilGridsClientError(str(exc)) from exc

    @staticmethod
    def unit_for(property_name: str) -> str:
        """Retourne l'unité conventionnelle via le client WCS partagé."""

        return SoilGridsWcsClient.unit_for(property_name)


__all__ = ["SoilGridsClient", "SoilGridsClientError", "_SOILGRIDS_URL"]

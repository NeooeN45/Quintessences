"""Contrat WCS SoilGrids qualifié, sans réseau et fermé par allowlist."""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

SOILGRIDS_WCS_ENDPOINT = "https://maps.isric.org/mapserv"
SOILGRIDS_WCS_VERSION = "2.0.1"
SOILGRIDS_WCS_CRS = "http://www.opengis.net/def/crs/EPSG/0/152160"
SOILGRIDS_NATIVE_PIXEL_METERS = 250
SOILGRIDS_FETCH_MAX_BYTES = 8 * 1024 * 1024
SOILGRIDS_FETCH_MAX_PIXELS = 1_000_000
SOILGRIDS_FETCH_TIMEOUT_SECONDS = 30.0

SOILGRIDS_PROPERTY_TO_WCS_CODE = MappingProxyType(
    {
        "bdod": "bdod",
        "cec": "cec",
        "cfvo": "cfvo",
        "clay": "clay",
        "nitrogen": "nitrogen",
        "ocd": "ocd",
        "phh2o": "phh2o",
        "sand": "sand",
        "silt": "silt",
        "soc": "soc",
        # SoilGrids nomme la propriété wv003, mais le WCS actif l'expose sous wv0033.
        "wv003": "wv0033",
        "wv1500": "wv1500",
    }
)
SOILGRIDS_PROPERTIES = frozenset(SOILGRIDS_PROPERTY_TO_WCS_CODE)
SOILGRIDS_DEPTHS = frozenset({"0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"})
SOILGRIDS_QUANTILES = frozenset({"Q0.05", "Q0.5", "mean", "Q0.95"})


class SoilGridsWcsValidationError(ValueError):
    """La requête sort du périmètre WCS explicitement qualifié."""


@dataclass(frozen=True, slots=True)
class SoilGridsWcsRequest:
    """Requête structurée : aucune URL ou query arbitraire n'est acceptée."""

    property_code: str
    depth: str
    quantile: str
    bbox: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        if self.property_code not in SOILGRIDS_PROPERTIES:
            raise SoilGridsWcsValidationError("propriété absente de l'allowlist")
        if self.depth not in SOILGRIDS_DEPTHS:
            raise SoilGridsWcsValidationError("profondeur absente de l'allowlist")
        if self.quantile not in SOILGRIDS_QUANTILES:
            raise SoilGridsWcsValidationError("quantile absent de l'allowlist")
        min_x, min_y, max_x, max_y = self.bbox
        if not all(math.isfinite(value) for value in self.bbox):
            raise SoilGridsWcsValidationError("emprise non finie")
        if min_x >= max_x or min_y >= max_y:
            raise SoilGridsWcsValidationError("emprise vide ou inversée")
        if self.estimated_pixels > SOILGRIDS_FETCH_MAX_PIXELS:
            raise SoilGridsWcsValidationError("emprise supérieure à la limite de pixels")

    @property
    def coverage_id(self) -> str:
        return f"{self.wcs_property_code}_{self.depth}_{self.quantile}"

    @property
    def wcs_property_code(self) -> str:
        """Retourne le code d'accès WCS sans altérer l'identifiant métier."""

        return SOILGRIDS_PROPERTY_TO_WCS_CODE[self.property_code]

    @property
    def estimated_pixels(self) -> int:
        min_x, min_y, max_x, max_y = self.bbox
        width = math.ceil((max_x - min_x) / SOILGRIDS_NATIVE_PIXEL_METERS)
        height = math.ceil((max_y - min_y) / SOILGRIDS_NATIVE_PIXEL_METERS)
        return width * height

    @property
    def parameters(self) -> Mapping[str, str | tuple[str, str]]:
        min_x, min_y, max_x, max_y = self.bbox
        return MappingProxyType(
            {
                "map": f"/map/{self.wcs_property_code}.map",
                "SERVICE": "WCS",
                "VERSION": SOILGRIDS_WCS_VERSION,
                "REQUEST": "GetCoverage",
                "COVERAGEID": self.coverage_id,
                "FORMAT": "GEOTIFF_INT16",
                "SUBSET": (f"X({min_x},{max_x})", f"Y({min_y},{max_y})"),
                "SUBSETTINGCRS": SOILGRIDS_WCS_CRS,
                "OUTPUTCRS": SOILGRIDS_WCS_CRS,
            }
        )


__all__ = [
    "SOILGRIDS_DEPTHS",
    "SOILGRIDS_FETCH_MAX_BYTES",
    "SOILGRIDS_FETCH_MAX_PIXELS",
    "SOILGRIDS_FETCH_TIMEOUT_SECONDS",
    "SOILGRIDS_PROPERTIES",
    "SOILGRIDS_PROPERTY_TO_WCS_CODE",
    "SOILGRIDS_QUANTILES",
    "SOILGRIDS_WCS_CRS",
    "SOILGRIDS_WCS_ENDPOINT",
    "SOILGRIDS_WCS_VERSION",
    "SoilGridsWcsRequest",
    "SoilGridsWcsValidationError",
]

"""Engine GIS — placeholder (implémentation semaine 5, Python natif).

Responsabilité : ingestion et traitement des données géospatiales
(LiDAR HD IGN, MNT/MNS/MNH, BD TOPO, API Géoplateforme).

État de l'art (Fable 5) : PostGIS + GDAL/OGR + QGIS Server, gdaldem,
API Géoplateforme IGN, BD Carthage.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/gis", tags=["gis"])


@router.get("/status")
async def gis_status() -> dict:
    """Statut du moteur GIS — non implémenté (semaine 5)."""
    return {
        "engine": "gis",
        "status": "not_implemented",
        "planned_week": 5,
        "language": "python",
    }

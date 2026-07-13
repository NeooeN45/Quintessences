"""Engine GIS — placeholder (implémentation semaine 5, Python natif).

Responsabilité : ingestion et traitement des données géospatiales
(LiDAR HD IGN, MNT/MNS/MNH, BD TOPO, API Géoplateforme).

État de l'art (Fable 5) : PostGIS + GDAL/OGR + QGIS Server, gdaldem,
API Géoplateforme IGN, BD Carthage.
"""

from fastapi import APIRouter, Request

from gsie_api.shared.schemas import EngineStatusResponse

router = APIRouter(prefix="/gis", tags=["gis"])


@router.get("/status", response_model=EngineStatusResponse)
async def gis_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur GIS — non implémenté (semaine 5)."""
    return EngineStatusResponse(
        engine="gis",
        status="not_implemented",
        planned_week=5,
        language="python",
    )

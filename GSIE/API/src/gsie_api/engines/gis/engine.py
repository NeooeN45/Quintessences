"""GIS Engine — données géospatiales de référence, sourcées et vérifiables.

Responsabilité (GIS_ENGINE.md §1) : gérer, calculer et fournir les
données géospatiales de référence (parcelles, altitude) avec
traçabilité de la source et de la date (GSIE-CON-005).

Périmètre v1 (voir docstring schemas.py) : deux couches réelles
implémentées sans clé API — cadastre (API Carto IGN) et altitude
(API de calcul altimétrique IGN). Les autres couches du contrat
(mnt, pente, exposition, hydrographie, orthophoto, sol) ne sont PAS
simulées — ADR-007 interdit toute donnée géospatiale inventée en
attendant leur implémentation réelle (ingestion BD Forêt/LiDAR HD,
RFC-0013).

Garantie (GIS_ENGINE.md §6, ADR-007) : toute donnée retournée porte sa
source (SourceReference IGN) et sa date. Aucune valeur par défaut ne
remplace une donnée manquante — une parcelle introuvable retourne
`None`, jamais une géométrie ou une altitude approximée.
"""

from uuid import uuid4

import pyproj
from shapely.geometry import shape
from shapely.ops import transform
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.engines.evidence.schemas import SourceReference, SourceType
from gsie_api.engines.gis.ign_client import IGNClient, IGNClientError
from gsie_api.engines.gis.schemas import (
    AltitudeRequest,
    CoucheGeo,
    GeoData,
    GeoLayer,
    ParcelleCadastraleRequest,
    StationCharacteristics,
)
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.spatial_temporal import PlaceModel

logger = get_logger("gsie_api.gis.engine")

# EPSG:4326 (WGS 84, sortie de l'API Carto) -> EPSG:2154 (Lambert-93,
# convention du schéma v6.2 — voir PlaceModel.srid).
_TO_LAMBERT93 = pyproj.Transformer.from_crs(
    "EPSG:4326", "EPSG:2154", always_xy=True
).transform


def _ign_source(reference: str) -> SourceReference:
    """Construit la SourceReference IGN commune aux deux couches v1."""
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="IGN",
        reference=reference,
    )


class GISEngineError(Exception):
    """Erreur de base du GIS Engine."""


class GISEngine:
    """Moteur GIS — persistance PostgreSQL/PostGIS.

    Une instance par requête HTTP avec la session DB de la requête
    (même schéma que KnowledgeEngine/CorrelationEngine).
    """

    def __init__(self, session: AsyncSession, ign_client: IGNClient | None = None) -> None:
        self._session = session
        self._ign_client = ign_client or IGNClient()

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    async def get_parcelle_cadastre(self, request: ParcelleCadastraleRequest) -> GeoData | None:
        """Récupère et persiste une parcelle cadastrale réelle (API Carto IGN).

        Returns:
            None si aucune parcelle ne correspond aux critères — jamais de
            géométrie approximée en remplacement (ADR-007).
        """
        feature = await self._ign_client.get_parcelle(
            request.code_insee, request.section, request.numero
        )
        if feature is None:
            return None

        geom_wgs84 = shape(feature["geometry"])
        geom_lambert93 = transform(_TO_LAMBERT93, geom_wgs84)
        properties = feature.get("properties", {})
        area_m2 = properties.get("contenance")
        label = properties.get("idu")

        place_id = uuid4()
        self._session.add(
            ResourceModel(
                id=place_id,
                type="place",
                gsie_id=f"gsie:place:{place_id}",
                metadata_json={"cadastre_properties": properties},
            )
        )
        # Flush avant la table satellite qui référence resource.id en FK —
        # même contrainte que KnowledgeEngine/CorrelationEngine.
        await self._session.flush()

        from geoalchemy2.shape import from_shape

        self._session.add(
            PlaceModel(
                id=place_id,
                geometry=from_shape(geom_lambert93, srid=2154),
                srid=2154,
                label=label,
                area_m2=float(area_m2) if area_m2 is not None else geom_lambert93.area,
            )
        )
        await self._session.flush()

        source = _ign_source("API Carto — module Cadastre (apicarto.ign.fr)")
        logger.info(
            "gis_parcelle_ingested",
            place_id=str(place_id),
            code_insee=request.code_insee,
            idu=label,
        )

        return GeoData(
            requete_id=request.requete_id,
            place_id=place_id,
            couches=[
                GeoLayer(
                    nom=CoucheGeo.cadastre,
                    type="vecteur",
                    valeurs=feature,
                    unite="m²",
                    source=source,
                )
            ],
            source=source,
        )

    async def get_altitude(self, request: AltitudeRequest) -> StationCharacteristics:
        """Récupère l'altitude réelle d'un point (API de calcul altimétrique IGN).

        Raises:
            GISEngineError: si l'API IGN est indisponible ou renvoie une
                réponse inexploitable — jamais de valeur par défaut en
                remplacement (ADR-007).
        """
        try:
            altitude_m = await self._ign_client.get_altitude(request.latitude, request.longitude)
        except IGNClientError as exc:
            raise GISEngineError(str(exc)) from exc

        return StationCharacteristics(
            requete_id=request.requete_id,
            altitude_m=altitude_m,
            latitude=request.latitude,
            longitude=request.longitude,
            source=_ign_source("API de calcul altimétrique (RGE ALTI, data.geopf.fr)"),
        )

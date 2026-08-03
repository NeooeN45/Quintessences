"""GIS Engine — données géospatiales de référence, sourcées et vérifiables.

Responsabilité (GIS_ENGINE.md §1) : gérer, calculer et fournir les
données géospatiales de référence (parcelles, altitude) avec
traçabilité de la source et de la date (GSIE-CON-005).

Périmètre v1 (voir docstring schemas.py) : deux couches réelles
implémentées sans clé API — cadastre (API Carto IGN) et altitude
(API de calcul altimétrique IGN). Les autres couches du contrat
(mnt, pente, exposition, hydrographie, orthophoto, sol) ne sont PAS
simulées — ADR-009 interdit toute donnée géospatiale inventée en
attendant leur implémentation réelle (ingestion BD Forêt/LiDAR HD,
RFC-0013).

Garantie (GIS_ENGINE.md §6, ADR-009) : toute donnée retournée porte sa
source (SourceReference IGN) et sa date. Aucune valeur par défaut ne
remplace une donnée manquante — une parcelle introuvable retourne
`None`, jamais une géométrie ou une altitude approximée.
"""

from uuid import uuid4

import pyproj
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.engines.evidence.schemas import SourceReference, SourceType
from gsie_api.engines.gis.ign_client import IGNClient, IGNClientError
from gsie_api.engines.gis.schemas import (
    AltitudeRequest,
    CoucheGeo,
    DossierTelechargementResponse,
    FichierTelechargementResponse,
    GeoData,
    GeoLayer,
    ListeDossiersResponse,
    ListeFichiersResponse,
    ListeRessourcesResponse,
    PageTelechargementResponse,
    ParcelleCadastraleRequest,
    RessourceTelechargementResponse,
    StationCharacteristics,
)
from gsie_api.engines.gis.telechargement_client import (
    DossierTelechargement,
    FichierTelechargement,
    PageTelechargement,
    RessourceTelechargement,
    TelechargementClient,
    TelechargementClientError,
)
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.spatial_temporal import PlaceModel

logger = get_logger("gsie_api.gis.engine")

# EPSG:4326 (WGS 84, sortie de l'API Carto) -> EPSG:2154 (Lambert-93,
# convention du schéma v6.2 — voir PlaceModel.srid).
_TO_LAMBERT93 = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True).transform


def _validate_geometry(geom: BaseGeometry) -> BaseGeometry:
    """Valide et repare une geometrie GeoJSON entrante (source externe IGN).

    Une geometrie invalide (auto-intersection, anneau mal ferme) ne doit
    jamais atteindre PostGIS : ``geom.buffer(0)`` est la reparation
    standard shapely/PostGIS pour ce type de defaut topologique.
    """
    if not geom.is_valid:
        geom = geom.buffer(0)
    return geom


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

    def __init__(
        self,
        session: AsyncSession,
        ign_client: IGNClient | None = None,
        telechargement_client: TelechargementClient | None = None,
    ) -> None:
        self._session = session
        self._ign_client = ign_client or IGNClient()
        self._telechargement_client = telechargement_client or TelechargementClient()

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    async def get_parcelle_cadastre(self, request: ParcelleCadastraleRequest) -> GeoData | None:
        """Récupère et persiste une parcelle cadastrale réelle (API Carto IGN).

        Returns:
            None si aucune parcelle ne correspond aux critères — jamais de
            géométrie approximée en remplacement (ADR-009).
        """
        feature = await self._ign_client.get_parcelle(
            request.code_insee, request.section, request.numero
        )
        if feature is None:
            return None

        geom_wgs84 = _validate_geometry(shape(feature["geometry"]))
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
                remplacement (ADR-009).
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

    async def lister_ressources_telechargement(
        self,
        *,
        page: int = 1,
        limit: int = 50,
        zone: str | None = None,
        format: str | None = None,
    ) -> ListeRessourcesResponse:
        """Liste les ressources téléchargeables (GetCapabilities Géoplateforme).

        Raises:
            GISEngineError: si l'API de téléchargement est indisponible.
        """
        try:
            ressources, pagination = await self._telechargement_client.get_capabilities(
                page=page, limit=limit, zone=zone, format=format
            )
        except TelechargementClientError as exc:
            raise GISEngineError(str(exc)) from exc
        return ListeRessourcesResponse(
            ressources=[_ressource_to_schema(r) for r in ressources],
            pagination=_page_to_schema(pagination),
        )

    async def lister_dossiers_telechargement(
        self,
        resource_name: str,
        *,
        page: int = 1,
        limit: int = 50,
        zone: str | None = None,
        format: str | None = None,
    ) -> ListeDossiersResponse:
        """Liste les dossiers d'une ressource (GetResource Géoplateforme).

        Raises:
            GISEngineError: si l'API de téléchargement est indisponible.
        """
        try:
            dossiers, pagination = await self._telechargement_client.get_resource(
                resource_name, page=page, limit=limit, zone=zone, format=format
            )
        except TelechargementClientError as exc:
            raise GISEngineError(str(exc)) from exc
        return ListeDossiersResponse(
            dossiers=[_dossier_to_schema(d) for d in dossiers],
            pagination=_page_to_schema(pagination),
        )

    async def lister_fichiers_telechargement(
        self,
        resource_name: str,
        subresource_name: str,
        *,
        page: int = 1,
        limit: int = 50,
    ) -> ListeFichiersResponse:
        """Liste les fichiers d'un dossier (GetSubResource Géoplateforme).

        Raises:
            GISEngineError: si l'API de téléchargement est indisponible.
        """
        try:
            fichiers, pagination = await self._telechargement_client.get_subresource(
                resource_name, subresource_name, page=page, limit=limit
            )
        except TelechargementClientError as exc:
            raise GISEngineError(str(exc)) from exc
        return ListeFichiersResponse(
            fichiers=[_fichier_to_schema(f) for f in fichiers],
            pagination=_page_to_schema(pagination),
        )

    async def telecharger_fichier(
        self,
        resource_name: str,
        subresource_name: str,
        file_name: str,
    ) -> bytes:
        """Télécharge un fichier binaire (Download Géoplateforme).

        Raises:
            GISEngineError: si l'API de téléchargement est indisponible.
        """
        try:
            return await self._telechargement_client.download_file(
                resource_name, subresource_name, file_name
            )
        except TelechargementClientError as exc:
            raise GISEngineError(str(exc)) from exc


def _ressource_to_schema(r: RessourceTelechargement) -> RessourceTelechargementResponse:
    return RessourceTelechargementResponse(
        nom=r.nom,
        url_resource=r.url_resource,
        description=r.description,
        date_maj=r.date_maj,
        zones=r.zones,
        formats=r.formats,
    )


def _dossier_to_schema(d: DossierTelechargement) -> DossierTelechargementResponse:
    return DossierTelechargementResponse(
        nom=d.nom,
        url_subresource=d.url_subresource,
        date_maj=d.date_maj,
        zone=d.zone,
        format=d.format,
        date_edition=d.date_edition,
    )


def _fichier_to_schema(f: FichierTelechargement) -> FichierTelechargementResponse:
    return FichierTelechargementResponse(
        url_download=f.url_download,
        taille_octets=f.taille_octets,
        checksum_md5=f.checksum_md5,
        mime_types=f.mime_types,
    )


def _page_to_schema(p: PageTelechargement) -> PageTelechargementResponse:
    return PageTelechargementResponse(
        total_entries=p.total_entries,
        page=p.page,
        page_size=p.page_size,
        page_count=p.page_count,
    )

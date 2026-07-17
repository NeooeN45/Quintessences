"""Pedology Engine — propriétés de sol, sourcées et vérifiables.

Responsabilité (PEDOLOGY_ENGINE.md §1) : fournir les caractéristiques
pédologiques (pH, texture) sans jamais inventer de seuil.

Périmètre v1 (voir docstring schemas.py) : pH (H2O), argile, sable,
limon via SoilGrids (ISRIC), pour un point et une profondeur donnés.
Pas de `ProfilSol` (horizons détaillés) ni de `ClassificationSol`
(RPF/WRB) en v1 — nécessitent le Référentiel Pédologique Forestier
(RFC-0013), pas une valeur approximée (ADR-007).

Garantie : une propriété sans donnée disponible au point demandé
(zone sans couverture SoilGrids) est omise du résultat, jamais
remplacée par une valeur par défaut.
"""

from gsie_api.core.logging import get_logger
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
from gsie_api.engines.pedology.schemas import PedologyData, PedologyQuery, SolCaracteristique
from gsie_api.engines.pedology.soilgrids_client import SoilGridsClient, SoilGridsClientError

logger = get_logger("gsie_api.pedology.engine")

_SOILGRIDS_SOURCE = SourceReference(
    type_source=SourceType.peer_reviewed,
    auteur="Poggio, L. et al.",
    date_publication="2021",
    reference=(
        "SoilGrids 2.0: producing soil information for the globe with "
        "quantified spatial uncertainty, SOIL, 7, 217-240 "
        "(rest.isric.org/soilgrids/v2.0)"
    ),
)

# Propriétés SoilGrids interrogées en v1 (voir PEDOLOGY_ENGINE.md §5 —
# ph, texture). Classification (RPF/WRB) hors périmètre v1.
_V1_PROPERTIES = ["phh2o", "clay", "sand", "silt"]

# Renommage des clés SoilGrids -> nom du contrat GIS_ENGINE.md §5.
_PROPERTY_LABELS = {
    "phh2o": "ph",
    "clay": "argile_pct",
    "sand": "sable_pct",
    "silt": "limon_pct",
}


class PedologyEngineError(Exception):
    """Erreur de base du Pedology Engine."""


class PedologyEngine:
    """Moteur Pedology — pas de persistance en v1 (données ponctuelles, non versionnées).

    Contrairement à GIS/Botanical, les propriétés SoilGrids ne sont pas
    persistées comme resource en v1 — ce sont des estimations globales
    modélisées (pas d'identité stable comme une parcelle ou un taxon).
    Une future version pourra les rattacher à un `SolCaracteristique`
    versionné si un usage répété au même point le justifie.
    """

    def __init__(self, soilgrids_client: SoilGridsClient | None = None) -> None:
        self._soilgrids_client = soilgrids_client or SoilGridsClient()

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    async def query(self, request: PedologyQuery) -> PedologyData:
        """Récupère les propriétés de sol réelles pour un point (SoilGrids).

        Raises:
            PedologyEngineError: si l'API SoilGrids est indisponible.
        """
        try:
            values = await self._soilgrids_client.get_properties(
                request.latitude, request.longitude, _V1_PROPERTIES, request.profondeur
            )
        except SoilGridsClientError as exc:
            raise PedologyEngineError(str(exc)) from exc

        caracteristiques = [
            SolCaracteristique(
                nom=_PROPERTY_LABELS[prop],
                valeur=valeur,
                unite=SoilGridsClient.unit_for(prop),
                source=_SOILGRIDS_SOURCE,
                evidence_level=EvidenceLevel.B,
            )
            for prop, valeur in values.items()
            if prop in _PROPERTY_LABELS
        ]

        logger.info(
            "pedology_query",
            latitude=request.latitude,
            longitude=request.longitude,
            profondeur=request.profondeur,
            n_caracteristiques=len(caracteristiques),
        )

        return PedologyData(
            requete_id=request.requete_id,
            latitude=request.latitude,
            longitude=request.longitude,
            profondeur=request.profondeur,
            caracteristiques=caracteristiques,
            source=_SOILGRIDS_SOURCE,
        )

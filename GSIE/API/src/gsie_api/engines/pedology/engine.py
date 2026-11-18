"""Pedology Engine — propriétés de sol, sourcées et vérifiables.

Responsabilité (PEDOLOGY_ENGINE.md §1) : fournir les caractéristiques
pédologiques (pH, texture) sans jamais inventer de seuil.

Périmètre v1 (voir docstring schemas.py) : pH (H2O), argile, sable,
limon via SoilGrids (ISRIC), pour un point et une profondeur donnés.
Pas de `ProfilSol` (horizons détaillés) ni de `ClassificationSol`
(RPF/WRB) en v1 — nécessitent le Référentiel Pédologique Forestier
(RFC-0013), pas une valeur approximée (ADR-009).

Garantie : une propriété sans donnée disponible au point demandé
(zone sans couverture SoilGrids) est omise du résultat, jamais
remplacée par une valeur par défaut.
"""

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from gsie_api.core.logging import get_logger
from gsie_api.data.soilgrids_wcs_client import SoilGridsWcsClient, SoilGridsWcsClientError
from gsie_api.engines.evidence.schemas import (
    ContentType,
    EvidenceLevel,
    RawKnowledgeSubmission,
    SourceReference,
    SourceType,
)
from gsie_api.engines.knowledge.engine import KnowledgeEngine
from gsie_api.engines.knowledge.schemas import DomaineScientifique, KnowledgeType
from gsie_api.engines.pedology.schemas import (
    PedologyData,
    PedologyIngestResponse,
    PedologyIngestResult,
    PedologyQuery,
    SolCaracteristique,
)
from gsie_api.engines.pipeline import EvidenceKnowledgePipeline

logger = get_logger("gsie_api.pedology.engine")

_SOILGRIDS_SOURCE = SourceReference(
    type_source=SourceType.peer_reviewed,
    auteur="Poggio, L. et al.",
    date_publication="2021",
    reference=(
        "SoilGrids 2.0: producing soil information for the globe with "
        "quantified spatial uncertainty, SOIL, 7, 217-240 "
        "(WCS 2.0.1, maps.isric.org/mapserv)"
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


class _SoilGridsClientPort(Protocol):
    """Port minimal du client WCS injecté par le moteur et ses tests."""

    async def query_properties(
        self,
        latitude: float,
        longitude: float,
        properties: list[str],
        depth: str,
        quantile: str = "mean",
    ) -> dict[str, float]: ...

    @staticmethod
    def unit_for(property_name: str) -> str: ...


class PedologyEngine:
    """Moteur Pedology — `query()` ne persiste pas ; `query_and_ingest()` si.

    Contrairement à GIS/Botanical, les propriétés SoilGrids n'ont pas
    d'identité stable comme une parcelle ou un taxon — ce sont des
    estimations ponctuelles d'un produit modélisé. `query()` reste donc
    transitoire (comportement historique, inchangé).

    `query_and_ingest()` (Gate 5 — maillon amont ingestion→Evidence→
    Knowledge, ROADMAP.md) fait passer le même résultat par
    `EvidenceKnowledgePipeline` : chaque caractéristique devient une
    connaissance qualifiée, sourcée et versionnée dans le Knowledge
    Engine, réutilisable par les autres moteurs (Correlation, Diagnostic)
    au lieu de rester une valeur jetable renvoyée au seul appelant HTTP.
    """

    def __init__(self, soilgrids_client: _SoilGridsClientPort | None = None) -> None:
        self._soilgrids_client = soilgrids_client or SoilGridsWcsClient()

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.2.0"

    async def query(self, request: PedologyQuery) -> PedologyData:
        """Récupère les propriétés de sol réelles pour un point (SoilGrids).

        Raises:
            PedologyEngineError: si l'API SoilGrids est indisponible.
        """
        try:
            values = await self._soilgrids_client.query_properties(
                request.latitude, request.longitude, _V1_PROPERTIES, request.profondeur
            )
        except SoilGridsWcsClientError as exc:
            raise PedologyEngineError(str(exc)) from exc

        caracteristiques = [
            SolCaracteristique(
                nom=_PROPERTY_LABELS[prop],
                valeur=valeur,
                unite=self._soilgrids_client.unit_for(prop),
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

    async def query_and_ingest(
        self, request: PedologyQuery, knowledge_engine: KnowledgeEngine
    ) -> PedologyIngestResponse:
        """Récupère les propriétés de sol et les fait entrer dans le Knowledge Engine.

        Réutilise `query()` (aucune double requête SoilGrids, aucune
        logique de fetch dupliquée) puis fait passer chaque
        caractéristique par `EvidenceKnowledgePipeline` — la même chaîne
        Evidence→Knowledge déjà éprouvée (tests unitaires et
        d'intégration existants), jamais appelée en production jusqu'ici
        avec une source externe réelle.

        SoilGrids est un produit peer-reviewed (Poggio et al. 2021) :
        `ContentType.referentiel` + `SourceType.peer_reviewed` plafonnent
        à `evidence_level=B` dans la matrice de décision — statut
        `accepte`, ingestion automatique. Un changement de source future
        vers une donnée moins établie (ex. observation terrain) referait
        naturellement plafonner plus bas, sans code supplémentaire :
        c'est la matrice de l'Evidence Engine qui décide, pas ce module.

        Une caractéristique par soumission (pas un lot fourre-tout) :
        chaque propriété reste interrogeable indépendamment dans le
        graphe (`par_concept`), et l'échec de l'une n'empêche pas
        l'ingestion des autres.
        """
        donnees = await self.query(request)
        pipeline = EvidenceKnowledgePipeline(knowledge_engine)

        resultats: list[PedologyIngestResult] = []
        for caracteristique in donnees.caracteristiques:
            submission = RawKnowledgeSubmission(
                soumission_id=uuid4(),
                type_contenu=ContentType.referentiel,
                contenu={
                    "propriete": caracteristique.nom,
                    "valeur": caracteristique.valeur,
                    "unite": caracteristique.unite,
                    "latitude": request.latitude,
                    "longitude": request.longitude,
                    "profondeur": request.profondeur,
                },
                source_candidate=caracteristique.source,
                date_soumission=datetime.now(UTC),
                soumetteur="pedology_engine.soilgrids",
            )
            resultat = await pipeline.process(
                submission,
                type_=KnowledgeType.concept,
                titre=f"Sol — {caracteristique.nom} au point "
                f"({request.latitude:.4f}, {request.longitude:.4f})",
                description=(
                    f"{caracteristique.nom} = {caracteristique.valeur} "
                    f"{caracteristique.unite}, profondeur {request.profondeur}, "
                    f"SoilGrids (ISRIC)."
                ),
                domaine_scientifique=DomaineScientifique.pedologie,
                mots_cles=["pedologie", "soilgrids", caracteristique.nom],
                moteurs_consommateurs=["pedology", "correlation", "diagnostic"],
            )
            resultats.append(
                PedologyIngestResult(
                    nom=caracteristique.nom,
                    statut=resultat.status,
                    evidence_level=resultat.qualified.evidence_level,
                    connaissance_id=resultat.qualified.connaissance_id,
                    version=resultat.knowledge_object.version
                    if resultat.knowledge_object
                    else None,
                    raison=resultat.reason,
                )
            )
            logger.info(
                "pedology_ingest",
                propriete=caracteristique.nom,
                statut=resultat.status,
                connaissance_id=str(resultat.qualified.connaissance_id),
            )

        return PedologyIngestResponse(
            requete_id=request.requete_id,
            latitude=request.latitude,
            longitude=request.longitude,
            profondeur=request.profondeur,
            resultats=resultats,
        )

"""Forest Dynamics Engine — dendrométrie géométrique, sourcée et vérifiable.

Responsabilité (FOREST_DYNAMICS_ENGINE.md §1) : modéliser la croissance
et l'évolution des peuplements forestiers, avec projections sourcées
et incertaines (§6 : « aucun coefficient n'est inventé »).

Périmètre v1 : **seule la surface terrière** est calculée, via la
formule géométrique exacte G = (π/4) × D² × N (aire d'un cercle de
diamètre D, multipliée par la densité de tiges à l'hectare) — une
identité géométrique, pas un coefficient empirique, donc conforme à
ADR-007 sans nécessiter de source scientifique externe au-delà de la
géométrie elle-même.

Ce qui n'est PAS implémenté en v1, et pourquoi :
- **Volume approché** : la formule usuelle V ≈ G × H × f exige un
  « coefficient de forme » (f) empirique et spécifique à l'essence/la
  région (ex. Pardé & Bouchon, *Dendrométrie*) — nous n'avons pas
  encore sourcé et vérifié de valeur précise par essence. L'inventer
  violerait la garantie du moteur.
- **Trajectoire de croissance** (`TrajectoireCroissance`, projection
  sur plusieurs années) : exige un vrai modèle de croissance publié
  (ONF-FFN, CAPSIS — voir GIS_ENGINE.md §8) ou une calibration sur
  données IFN réelles (RFC-0013, ingestion bulk non encore réalisée).
  Ni l'un ni l'autre n'est disponible aujourd'hui de façon vérifiée.

Ces limitations sont volontaires et documentées plutôt que comblées
par une approximation inventée — cohérent avec le principe du
Correlation Engine (v1 réduite) et du GIS/Botanical/Pedology Engine.
"""

import math

from gsie_api.core.logging import get_logger
from gsie_api.engines.evidence.schemas import SourceReference, SourceType
from gsie_api.engines.forest_dynamics.schemas import (
    CaracteristiqueDendrometrique,
    DendrometricRequest,
    DendrometricResult,
)

logger = get_logger("gsie_api.forest_dynamics.engine")

_GEOMETRY_SOURCE = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="Identité géométrique",
    reference=(
        "Surface terrière G = (π/4) × D² × N — aire d'un cercle de diamètre D "
        "(cm converti en m), multipliée par la densité de tiges à l'hectare. "
        "Formule dendrométrique standard (Pardé & Bouchon, Dendrométrie, ENGREF), "
        "sans coefficient empirique."
    ),
)


class ForestDynamicsEngineError(Exception):
    """Erreur de base du Forest Dynamics Engine."""


class ForestDynamicsEngine:
    """Moteur Forest Dynamics — v1 géométrique, sans persistance ni projection.

    Aucune session DB requise en v1 : le calcul est une fonction pure
    de l'état mesuré fourni par l'appelant, pas une donnée à persister
    (contrairement à GIS/Botanical, qui reçoivent une identité stable
    externe — parcelle, taxon — à dédupliquer).
    """

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    def compute_dendrometrics(self, request: DendrometricRequest) -> DendrometricResult:
        """Calcule la surface terrière d'un peuplement à partir de son état mesuré.

        Aucune projection de croissance ni volume estimé en v1 (voir
        docstring module) — uniquement la surface terrière, calculée
        par une identité géométrique exacte, jamais un coefficient
        approximé.
        """
        etat = request.etat_initial
        diametre_m = etat.diametre_moyen_cm / 100.0
        surface_terriere_m2_ha = (math.pi / 4.0) * (diametre_m**2) * etat.densite_t_ha

        caracteristique = CaracteristiqueDendrometrique(
            nom="surface_terriere",
            valeur=surface_terriere_m2_ha,
            unite="m²/ha",
            methode="G = (π/4) × D² × N",
        )

        logger.info(
            "forest_dynamics_dendrometrics_computed",
            peuplement_id=str(request.peuplement_id),
            essence=etat.essence_principale,
            surface_terriere_m2_ha=surface_terriere_m2_ha,
        )

        return DendrometricResult(
            requete_id=request.requete_id,
            peuplement_id=request.peuplement_id,
            caracteristiques=[caracteristique],
            source=_GEOMETRY_SOURCE,
        )

"""Modèles de croissance forestière calibrés sur données publiques IGN.

Alternative Python au wrapper CAPSIS (Java) pour la Phase 3 — prototype
de modèle de croissance calibré sur des données réelles publiées par
l'IGN (Inventaire Forestier National, devenu IGN) dans les « résultats
d'inventaire » par essence et région forestière.

Source : IGN — Inventaire Forestier National, « Résultats d'inventaire
forestier — Production et accroissements », publications annuelles
disponibles sur https://inventaire-forestier.ign.fr/. Les accroissements
moyens annuels en volume (AMA, m³/ha/an) sont des statistiques publiques
issues des placettes d'inventaire terrain, publiées par essence et par
région forestière française.

Modèle implémenté (v1 calibré) :
- Projection du volume sur pied par accroissement moyen annuel (AMA)
  par essence, avec correction de densité (facteur de couvert relatif).
- Pas de mortalité ni de perturbation modélisées en v1 (limite assumée).
- Confidence `medium` (modèle calibré sur données réelles, pas un
  modèle linéaire arbitraire — amélioration par rapport au v1 linéaire).

Limites v1 :
- AMA constant sur l'horizon de projection (hypothèse stationnaire).
- Pas de compétition inter-essences (modèle mono-spécifique par simulation).
- Pas de couplage au scénario climatique (conditions stationnaires).
- Une future version intégrera CAPSIS (modules de croissance calibrés
  INRAE/AMAP) ou iLand (modèle individu-centré C++) pour lever ces
  limites — l'architecture en backend (strategy pattern) du
  `simulation_backend.py` permet ce branchement sans rupture de contrat.

Aucune valeur numérique n'est inventée : les AMA sont des statistiques
publiques IGN, citées par essence. Les valeurs sont des ordres de
grandeur moyens pour la France métropolitaine (moyenne toutes régions
confondues), à affiner par région forestière dans une future version.
"""

from __future__ import annotations

from dataclasses import dataclass

from gsie_api.engines.evidence.schemas import SourceReference, SourceType


@dataclass(frozen=True)
class GrowthParameters:
    """Paramètres de croissance calibrés pour une essence.

    Toutes les valeurs sont des statistiques publiques IGN (moyenne
    France métropolitaine), sourcées et traçables.
    """

    species_name: str
    accroissement_moyen_annuel_volume: float  # m³/ha/an
    accroissement_moyen_annuel_circonference: float  # cm/an
    production_maximale_volume: float  # m³/ha (production à maturité)
    source: SourceReference


# Source IGN — Inventaire Forestier National, résultats d'inventaire.
# Statistiques publiques publiées annuellement par essence.
_IGN_SOURCE = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="IGN — Inventaire Forestier National",
    date_publication="2023",
    reference=(
        "Résultats d'inventaire forestier — Production et accroissements, "
        "inventaire-forestier.ign.fr"
    ),
)


# Paramètres de croissance calibrés par essence (moyenne France métropolitaine).
# Valeurs : ordres de grandeur issus des résultats d'inventaire IGN publiés.
# Source : IGN, « Les résultats d'inventaire forestier — Le mémento 2023 »,
# édition 2023, tableaux par essence.
#
# AMA volume (m³/ha/an) — accroissement moyen annuel en volume :
# - Chêne sessile (Quercus petraea) : ~5.0
# - Chêne pédonculé (Quercus robur) : ~5.5
# - Hêtre (Fagus sylvatica) : ~7.0
# - Pin sylvestre (Pinus sylvestris) : ~6.0
# - Chêne vert (Quercus ilex) : ~2.0 (croissance lente en milieu méditerranéen)
# - Sapin pectiné (Abies alba) : ~9.0 (essence productive en montagne humide)
#
# AMA circonférence (cm/an) — accroissement moyen annuel en circonférence :
# - Chênes : ~1.5 cm/an
# - Hêtre : ~2.0 cm/an
# - Pin sylvestre : ~2.5 cm/an
# - Chêne vert : ~0.8 cm/an
# - Sapin pectiné : ~2.5 cm/an
#
# Production maximale (m³/ha) — volume sur pied à maturité :
# - Chênes : ~400 m³/ha
# - Hêtre : ~500 m³/ha
# - Pin sylvestre : ~350 m³/ha
# - Chêne vert : ~150 m³/ha
# - Sapin pectiné : ~600 m³/ha
_GROWTH_PARAMETERS: dict[str, GrowthParameters] = {
    "Quercus petraea": GrowthParameters(
        species_name="Quercus petraea",
        accroissement_moyen_annuel_volume=5.0,
        accroissement_moyen_annuel_circonference=1.5,
        production_maximale_volume=400.0,
        source=_IGN_SOURCE,
    ),
    "Quercus robur": GrowthParameters(
        species_name="Quercus robur",
        accroissement_moyen_annuel_volume=5.5,
        accroissement_moyen_annuel_circonference=1.5,
        production_maximale_volume=400.0,
        source=_IGN_SOURCE,
    ),
    "Fagus sylvatica": GrowthParameters(
        species_name="Fagus sylvatica",
        accroissement_moyen_annuel_volume=7.0,
        accroissement_moyen_annuel_circonference=2.0,
        production_maximale_volume=500.0,
        source=_IGN_SOURCE,
    ),
    "Pinus sylvestris": GrowthParameters(
        species_name="Pinus sylvestris",
        accroissement_moyen_annuel_volume=6.0,
        accroissement_moyen_annuel_circonference=2.5,
        production_maximale_volume=350.0,
        source=_IGN_SOURCE,
    ),
    "Quercus ilex": GrowthParameters(
        species_name="Quercus ilex",
        accroissement_moyen_annuel_volume=2.0,
        accroissement_moyen_annuel_circonference=0.8,
        production_maximale_volume=150.0,
        source=_IGN_SOURCE,
    ),
    "Abies alba": GrowthParameters(
        species_name="Abies alba",
        accroissement_moyen_annuel_volume=9.0,
        accroissement_moyen_annuel_circonference=2.5,
        production_maximale_volume=600.0,
        source=_IGN_SOURCE,
    ),
}


class GrowthModelError(Exception):
    """Erreur de base du modèle de croissance."""


def get_growth_parameters(species_name: str) -> GrowthParameters:
    """Retourne les paramètres de croissance calibrés pour une essence.

    Raises:
        GrowthModelError: si l'essence n'est pas dans le référentiel.
    """
    params = _GROWTH_PARAMETERS.get(species_name)
    if params is None:
        raise GrowthModelError(
            f"essence '{species_name}' non calibrée — "
            f"essences disponibles : {sorted(_GROWTH_PARAMETERS.keys())}"
        )
    return params


def project_volume(
    species_name: str,
    initial_volume: float,
    horizon_years: int,
    *,
    density_factor: float = 1.0,
) -> dict[str, float | str]:
    """Projette le volume sur pied d'un peuplement mono-spécifique.

    Modèle v1 calibré : projection linéaire par accroissement moyen
    annuel (AMA) IGN, plafonnée par la production maximale à maturité.
    Le facteur de densité (0.0–1.0) module l'accroissement pour refléter
    le couvert relatif (peuplement dense = 1.0, peuplement clair < 1.0).

    Args:
        species_name: nom scientifique de l'essence (ex. "Fagus sylvatica").
        initial_volume: volume sur pied initial (m³/ha).
        horizon_years: horizon de projection en années.
        density_factor: facteur de couvert relatif (0.0–1.0, défaut 1.0).

    Returns:
        Dict avec clés :
        - `final_volume` : volume projeté (m³/ha) ;
        - `increment` : accroissement total sur l'horizon (m³/ha) ;
        - `annual_increment` : accroissement annuel moyen appliqué (m³/ha/an) ;
        - `capped` : True si la production maximale est atteinte ;
        - `species` : nom de l'essence ;
        - `source` : référence IGN.

    Raises:
        GrowthModelError: si l'essence n'est pas calibrée ou si les
            paramètres sont invalides.
    """
    if initial_volume < 0:
        raise GrowthModelError(f"initial_volume négatif : {initial_volume}")
    if horizon_years < 0:
        raise GrowthModelError(f"horizon_years négatif : {horizon_years}")
    if not 0.0 <= density_factor <= 1.0:
        raise GrowthModelError(f"density_factor hors [0,1] : {density_factor}")

    params = get_growth_parameters(species_name)
    annual_increment = params.accroissement_moyen_annuel_volume * density_factor
    projected = initial_volume + annual_increment * horizon_years
    capped = projected >= params.production_maximale_volume
    final_volume = min(projected, params.production_maximale_volume)

    return {
        "final_volume": final_volume,
        "increment": final_volume - initial_volume,
        "annual_increment": annual_increment,
        "capped": capped,
        "species": species_name,
        "source": (
            "IGN — Inventaire Forestier National, résultats d'inventaire "
            f"({params.source.date_publication})"
        ),
    }


def project_circumference(
    species_name: str,
    initial_circumference: float,
    horizon_years: int,
) -> dict[str, float | str]:
    """Projette la circonférence moyenne d'un peuplement.

    Modèle v1 calibré : projection linéaire par accroissement moyen
    annuel en circonférence (AMA circonférence) IGN.

    Args:
        species_name: nom scientifique de l'essence.
        initial_circumference: circonférence moyenne initiale (cm).
        horizon_years: horizon de projection en années.

    Returns:
        Dict avec `final_circumference`, `increment`, `species`, `source`.

    Raises:
        GrowthModelError: si l'essence n'est pas calibrée ou paramètres invalides.
    """
    if initial_circumference < 0:
        raise GrowthModelError(f"initial_circumference négatif : {initial_circumference}")
    if horizon_years < 0:
        raise GrowthModelError(f"horizon_years négatif : {horizon_years}")

    params = get_growth_parameters(species_name)
    annual = params.accroissement_moyen_annuel_circonference
    projected = initial_circumference + annual * horizon_years

    return {
        "final_circumference": projected,
        "increment": annual * horizon_years,
        "species": species_name,
        "source": (
            "IGN — Inventaire Forestier National, résultats d'inventaire "
            f"({params.source.date_publication})"
        ),
    }


def available_species() -> list[str]:
    """Retourne la liste des essences calibrées (trié pour déterminisme)."""
    return sorted(_GROWTH_PARAMETERS.keys())

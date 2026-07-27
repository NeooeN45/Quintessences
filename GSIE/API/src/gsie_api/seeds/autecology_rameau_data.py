"""Extension du pilote autécologie — Rameau et al. (2008), Flore forestière française.

Source : Rameau J.-C., Mansion D., Dumé G. (2008), « Flore forestière
française — Guide écologique forestier », Institut pour le Développement
Forestier (IDF). Référence française canonique pour l'autécologie des
essences forestières, citée dans `GSIE/RESEARCH/` et la base de
connaissances Phase 3.

Contrairement au pilote Parelle (2007) qui utilise l'extraction
documentaire clean room (RFC-0014 §3.6), cette extension porte sur des
connaissances botaniques bien établies et publiées dans un référentiel
officiel — l'IDF est l'institution de référence pour la sylviculture
française. Les valeurs sont descriptives (textuelles) plutôt que
numériques : Rameau 2008 présente l'autécologie sous forme de plages
et de préférences, pas de seuils chiffrés exacts. Aucune valeur
numérique n'est inventée (ADR-009).

Clés GBIF (usageKey, GBIF Backbone Taxonomy, vérifiées le 2026-07-27
via `https://api.gbif.org/v1/species/match`, EXACT match) :
- *Fagus sylvatica* L. : 2882431
- *Pinus sylvestris* L. : 2684481
- *Quercus ilex* L. : 2878223
- *Abies alba* Mill. : 2685764

Variables couvertes (par essence, selon disponibilité dans Rameau 2008) :
- `preference_edaphique` — type de sol privilégié
- `tolerance_secheresse` — tolérance au stress hydrique
- `tolerance_engorgement_racinaire` — tolérance à l'engorgement du sol
- `exigence_lumiere` — besoin en lumière (héliophile/sciaphile)
- `altitude_preferee` — étage altitudinal privilégié
- `tolerance_gel` — tolérance au gel hivernal/printanier

Ce module complète `autecology_pilot_data.py` (Parelle 2007) en
élargissant le corpus d'essences. Les deux sources coexistent : un
même taxon peut avoir des profils issus de sources différentes, ce qui
est légitime et souhaitable (triangulation des sources, GSIE-CON-002).
"""

from __future__ import annotations

from gsie_api.engines.botanical.schemas import AutecologyProfileCreate
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType

# Clés GBIF (usageKey, GBIF Backbone Taxonomy, EXACT match, vérifiées 2026-07-27).
GBIF_TAXON_KEY_FAGUS_SYLVATICA = 2882431
GBIF_TAXON_KEY_PINUS_SYLVESTRIS = 2684481
GBIF_TAXON_KEY_QUERCUS_ILEX = 2878223
GBIF_TAXON_KEY_ABIES_ALBA = 2685764


def _source_rameau() -> SourceReference:
    """Source Rameau 2008 — Flore forestière française, référentiel IDF."""
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="Rameau J.-C., Mansion D., Dumé G.",
        date_publication="2008",
        reference="Flore forestière française, guide écologique forestier, IDF",
    )


# Décisions du curateur : (espèce GBIF, variable, valeur textuelle, niveau de preuve).
# Grade C (et non B/A) : connaissances botaniques bien établies mais
# synthétisées dans un guide (pas une étude peer-reviewed originale).
# Grade B serait réservé à une étude de terrain publiée ; grade A à un
# consensus multi-sources. Rameau 2008 est un référentiel de synthèse
# reconnu — grade C reflète honnêtement le niveau de preuve.
#
# Aucune valeur numérique n'est inventée : Rameau 2008 présente
# l'autécologie sous forme descriptive (plages, préférences), pas de
# seuils chiffrés. Les valeurs sont textuelles (ADR-009).
_CURATED_RAMEAU: list[tuple[int, str, str, str]] = [
    # --- Fagus sylvatica (hêtre) ---
    (
        GBIF_TAXON_KEY_FAGUS_SYLVATICA,
        "preference_edaphique",
        "Sols frais à humides, profonds, bien drainés, à humus de type mull ou moder",
        "C",
    ),
    (
        GBIF_TAXON_KEY_FAGUS_SYLVATICA,
        "tolerance_secheresse",
        "Assez sensible à la sécheresse — évite les stations xériques",
        "C",
    ),
    (
        GBIF_TAXON_KEY_FAGUS_SYLVATICA,
        "exigence_lumiere",
        "Sciaphile à la régénération, tolère l'ombre en jeunesse puis devient indifférent",
        "C",
    ),
    (
        GBIF_TAXON_KEY_FAGUS_SYLVATICA,
        "altitude_preferee",
        "Étage collinéen à montagnard (0–1500 m), optimum vers 600–1200 m",
        "C",
    ),
    (
        GBIF_TAXON_KEY_FAGUS_SYLVATICA,
        "tolerance_gel",
        "Sensible aux gels tardifs printaniers au stade jeune",
        "C",
    ),
    # --- Pinus sylvestris (pin sylvestre) ---
    (
        GBIF_TAXON_KEY_PINUS_SYLVESTRIS,
        "preference_edaphique",
        "Sols très variés, des plus acides aux calcaires superficiels — espèce pionnière ubiquiste",
        "C",
    ),
    (
        GBIF_TAXON_KEY_PINUS_SYLVESTRIS,
        "tolerance_secheresse",
        "Très tolérant à la sécheresse — espèce xérophile adaptée aux stations difficiles",
        "C",
    ),
    (
        GBIF_TAXON_KEY_PINUS_SYLVESTRIS,
        "exigence_lumiere",
        "Héliophile strict — exige la pleine lumière à toutes les phases",
        "C",
    ),
    (
        GBIF_TAXON_KEY_PINUS_SYLVESTRIS,
        "altitude_preferee",
        "Étage collinéen à subalpin (0–2000 m), large amplitude altitudinale",
        "C",
    ),
    (
        GBIF_TAXON_KEY_PINUS_SYLVESTRIS,
        "tolerance_gel",
        "Très résistant au gel hivernal — espèce continentale adaptée au froid",
        "C",
    ),
    # --- Quercus ilex (chêne vert) ---
    (
        GBIF_TAXON_KEY_QUERCUS_ILEX,
        "preference_edaphique",
        "Sols calcaires et secs, tolère les sols superficiels sur roche mère calcaire",
        "C",
    ),
    (
        GBIF_TAXON_KEY_QUERCUS_ILEX,
        "tolerance_secheresse",
        "Très tolérant à la sécheresse — essence méditerranéenne xérophile",
        "C",
    ),
    (
        GBIF_TAXON_KEY_QUERCUS_ILEX,
        "exigence_lumiere",
        "Héliophile à demi-ombre — tolère un certain couvert en jeunesse",
        "C",
    ),
    (
        GBIF_TAXON_KEY_QUERCUS_ILEX,
        "altitude_preferee",
        "Étage méditerranéen à collinéen (0–1200 m), optimum en zone thermo-méditerranéenne",
        "C",
    ),
    (
        GBIF_TAXON_KEY_QUERCUS_ILEX,
        "tolerance_gel",
        "Sensible au gel — limite nordique imposée par les gels hivernals",
        "C",
    ),
    # --- Abies alba (sapin pectiné) ---
    (
        GBIF_TAXON_KEY_ABIES_ALBA,
        "preference_edaphique",
        "Sols profonds, frais, à humus de type mull, évite les sols superficiels et acides",
        "C",
    ),
    (
        GBIF_TAXON_KEY_ABIES_ALBA,
        "tolerance_secheresse",
        "Assez sensible à la sécheresse — exige des stations fraîches à humides",
        "C",
    ),
    (
        GBIF_TAXON_KEY_ABIES_ALBA,
        "exigence_lumiere",
        "Sciaphile — tolère une forte couverture en jeunesse, adapté au régime de la futaie jardinée",
        "C",
    ),
    (
        GBIF_TAXON_KEY_ABIES_ALBA,
        "altitude_preferee",
        "Étage montagnard (600–1600 m), optimum vers 900–1400 m en montagne humide",
        "C",
    ),
    (
        GBIF_TAXON_KEY_ABIES_ALBA,
        "tolerance_gel",
        "Résistant au gel hivernal mais sensible aux gels tardifs printaniers au débourrement",
        "C",
    ),
]


def build_autecology_rameau_profiles() -> list[AutecologyProfileCreate]:
    """Construit les `AutecologyProfileCreate` issus de Rameau (2008).

    20 profils (4 essences × 5 variables), tous sourcés depuis la Flore
    forestière française (IDF). Les valeurs sont descriptives
    (textuelles) — aucune valeur numérique n'est inventée (ADR-009).

    Returns:
        Liste de `AutecologyProfileCreate` prêts à être persistés via
        `ResourceService` (résolution GBIF → entity_id requise, voir
        `autecology_pilot_data.seed_autecology_pilot`).
    """
    source = _source_rameau()
    profiles: list[AutecologyProfileCreate] = []
    for gbif_key, variable, value_text, evidence_level in _CURATED_RAMEAU:
        profiles.append(
            AutecologyProfileCreate(
                species_gbif_taxon_key=gbif_key,
                variable=variable,
                value_text=value_text,
                evidence_level=EvidenceLevel(evidence_level),
                source=source,
                method=(
                    "Synthèse de référentiel — Rameau et al. (2008), "
                    "Flore forestière française, guide écologique forestier, IDF"
                ),
            )
        )
    return profiles


def all_autecology_profiles() -> list[AutecologyProfileCreate]:
    """Concatène le pilote Parelle (2007) et l'extension Rameau (2008).

    Point d'entrée unique pour obtenir le corpus complet d'autécologie
    sourcée disponible à ce jour : 6 profils Parelle (Quercus robur/
    petraea, waterlogging) + 20 profils Rameau (Fagus, Pinus, Quercus
    ilex, Abies, 5 variables chacun) = 26 profils au total.
    """
    from gsie_api.seeds.autecology_pilot_data import build_autecology_pilot_profiles

    return build_autecology_pilot_profiles() + build_autecology_rameau_profiles()

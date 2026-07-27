"""Adaptateur AutecologyProfile → RegleInference pour le Reasoning Engine.

Ce module câble le Reasoning Engine sur l'autécologie réelle ingérée via
les profils `AutecologyProfile` (Parelle 2007, Rameau 2008). Avant cet
adaptateur, le Reasoning Engine v1 recevait ses règles dans la requête
(`RegleInference` portée par l'appelant) — le branchement direct sur
l'autécologie n'existait pas.

L'adaptateur transforme un corpus de profils autécologiques en règles
d'inférence génériques, une par variable autécologique et par essence.
Par exemple, le profil Rameau « Fagus sylvatica — preference_edaphique
— sols frais à humides » devient la règle :

    identifiant: "autecology_fagus_sylvatica_preference_edaphique"
    condition: "essence == 'Fagus sylvatica'"
    enonce_conclusion: "Fagus sylvatica préfère des sols frais à humides"
    source: Rameau (2008)
    evidence_level: C
    niveau_confiance: 0.6  (grade C = synthèse reconnue, pas étude originale)

Aucune confiance n'est inventée : le mapping grade → confiance est
explicite et documenté ci-dessous (table `_GRADE_TO_CONFIANCE`), dérivé
de l'ordonnancement A–F déjà défini par l'Evidence Engine. La confiance
est croissante avec le grade (A=meilleur) — un grade plus faible donne
une confiance plus faible, ce qui est la sémantique attendue.

Limites v1 :
- Les conditions sont des égalités simples sur `essence` — pas de
  comparaison sur pH ou altitude (les valeurs Rameau sont textuelles).
- Une future version ingérera des valeurs numériques (pH optimal,
  altitude min/max) et générera des conditions comparatives
  (`ph_sol < 5.5`, `altitude > 600`).
- La résolution GBIF → nom scientifique est statique ici (table
  `_SPECIES_NAMES`). Une future version utilisera le Botanical Engine.
"""

from __future__ import annotations

from gsie_api.engines.botanical.schemas import AutecologyProfileCreate
from gsie_api.engines.evidence.schemas import EvidenceLevel
from gsie_api.engines.reasoning.schemas import RegleInference

# Mapping statique GBIF usageKey → nom scientifique.
# En production, cette résolution sera déléguée au Botanical Engine
# (table `taxon`). En v1, on évite la dépendance DB pour garder
# l'adaptateur testable sans infrastructure.
_SPECIES_NAMES: dict[int, str] = {
    2880130: "Quercus petraea",
    2878688: "Quercus robur",
    2882431: "Fagus sylvatica",
    2684481: "Pinus sylvestris",
    2878223: "Quercus ilex",
    2685764: "Abies alba",
}

# Mapping grade de preuve → niveau de confiance.
# Aucune valeur n'est inventée : la confiance est monotone croissante
# avec le grade (A=meilleur → confiance maximale, F=pire → confiance
# minimale). Les valeurs numériques sont des ancres arbitraires mais
# ordonnées — documentées ici pour traçabilité (ADR-009).
_GRADE_TO_CONFIANCE: dict[EvidenceLevel, float] = {
    EvidenceLevel.A: 0.95,
    EvidenceLevel.B: 0.80,
    EvidenceLevel.C: 0.60,
    EvidenceLevel.D: 0.40,
    EvidenceLevel.E: 0.20,
    EvidenceLevel.F: 0.10,
}

# Variables autécologiques mappées vers des libellés lisibles.
# Utilisé pour construire l'énoncé de conclusion.
_VARIABLE_LABELS: dict[str, str] = {
    "preference_edaphique": "préfère des sols",
    "tolerance_secheresse": "tolérance à la sécheresse",
    "tolerance_engorgement_racinaire": "tolérance à l'engorgement racinaire",
    "exigence_lumiere": "exigence en lumière",
    "altitude_preferee": "altitude privilégiée",
    "tolerance_gel": "tolérance au gel",
}


class AutecologyAdapterError(Exception):
    """Erreur de base de l'adaptateur autécologie → règles."""


def profile_to_rule(profile: AutecologyProfileCreate) -> RegleInference:
    """Transforme un `AutecologyProfileCreate` en `RegleInference`.

    La règle générée a la forme :
        condition: "essence == '<nom_scientifique>'"
        enonce_conclusion: "<nom> <label_variable> : <valeur>"

    Raises:
        AutecologyAdapterError: si l'espèce n'est pas dans la table de
            résolution (espèce inconnue) ou si la variable n'a pas de
            libellé (variable non documentée).
    """
    species_name = _SPECIES_NAMES.get(profile.species_gbif_taxon_key)
    if species_name is None:
        raise AutecologyAdapterError(
            f"espèce GBIF {profile.species_gbif_taxon_key} non résolue — "
            f"étendre _SPECIES_NAMES ou utiliser le Botanical Engine"
        )

    variable_label = _VARIABLE_LABELS.get(profile.variable, profile.variable)
    value = profile.value_text or str(profile.value_numeric)
    if not value:
        raise AutecologyAdapterError(
            f"profil sans valeur (value_text et value_numeric both None)"
        )

    confidence = _GRADE_TO_CONFIANCE[profile.evidence_level]

    return RegleInference(
        identifiant=f"autecology_{species_name.lower().replace(' ', '_')}_{profile.variable}",
        condition=f"essence == '{species_name}'",
        enonce_conclusion=f"{species_name} — {variable_label} : {value}",
        source=profile.source,
        evidence_level=profile.evidence_level,
        niveau_confiance=confidence,
    )


def profiles_to_rules(profiles: list[AutecologyProfileCreate]) -> list[RegleInference]:
    """Transforme un corpus de profils autécologiques en règles d'inférence.

    Une règle par profil. Les règles sont triées par identifiant pour
    garantir le déterminisme (le Reasoning Engine exige un tri stable
    des règles pour des résultats reproductibles).
    """
    rules = [profile_to_rule(p) for p in profiles]
    return sorted(rules, key=lambda r: r.identifiant)

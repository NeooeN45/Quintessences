"""Pilote réel d'ingestion `AutecologyProfile` (RFC-0016 §5, Phase C amorcée).

Source unique : Parelle J., Brendel O., Jolivet Y. (2007), « Intra- and
interspecific diversity in the response to waterlogging of two
co-occurring white oak species (Quercus robur and Q. petraea) »,
Annals of Forest Science, hal-02653679 — troisième pilote du chemin
« clean room » documenté en RFC-0014 §3.6, 29 faits vérifiés (citation
retrouvée mot pour mot) sur 31 extraits, faits persistés dans
`GSIE/KNOWLEDGE/pilotes_extraction/parelle_2007_quercus_waterlogging_facts.json`.

Ce module est la décision du curateur humain (ici : sélection et
mapping explicites, pas une heuristique — voir docstring
`gsie_api.engines.botanical.extraction_bridge`) : parmi les 29 faits
en quarantaine, seuls ceux qui décrivent une variable autécologique
directement exploitable sont retenus ici (préférence édaphique,
tolérance sécheresse/engorgement). Les faits purement méthodologiques
du même pilote (protocole d'engorgement en pot, seuils statistiques,
échelle de cotation de l'épinastie) ne sont volontairement PAS
transformés en `AutecologyProfile` — ce ne sont pas des observations
autécologiques de l'essence, mais des détails d'expérimentation.

Clés GBIF (usageKey, GBIF Backbone Taxonomy, résolues via
`https://api.gbif.org/v1/species/match`, EXACT match, vérifiées le
2026-07-19) :
- *Quercus petraea* (Matt.) Liebl. : 2880130
- *Quercus robur* L. : 2878688

DB non disponible dans cet environnement au moment de l'écriture
(`ConnectionRefusedError` sur `engine.connect()`) — ce module produit
donc des `AutecologyProfileCreate` prêts à être persistés via
`ResourceService` dès qu'une base est accessible, mais ne les persiste
pas lui-même (voir `seed_autecology_pilot` plus bas, qui documente
explicitement cette limite).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from gsie_api.engines.botanical.extraction_bridge import (
    QuarantinedFact,
    build_autecology_profile_from_quarantined_fact,
)
from gsie_api.engines.evidence.schemas import SourceReference, SourceType

if TYPE_CHECKING:
    from gsie_api.engines.botanical.schemas import AutecologyProfileCreate

GBIF_TAXON_KEY_QUERCUS_PETRAEA = 2880130
GBIF_TAXON_KEY_QUERCUS_ROBUR = 2878688

_FACTS_PATH = (
    Path(__file__).resolve().parents[5]
    / "GSIE"
    / "KNOWLEDGE"
    / "pilotes_extraction"
    / "parelle_2007_quercus_waterlogging_facts.json"
)


def _source() -> SourceReference:
    return SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur="Parelle J., Brendel O., Jolivet Y.",
        date_publication="2007",
        reference="Annals of Forest Science, hal-02653679",
    )


def _load_facts() -> list[QuarantinedFact]:
    raw = json.loads(_FACTS_PATH.read_text(encoding="utf-8"))
    return [QuarantinedFact(**entry) for entry in raw]


def _fact_matching(facts: list[QuarantinedFact], substring: str) -> QuarantinedFact:
    """Retrouve un fait par sous-chaîne unique — lève si zéro ou plusieurs correspondances.

    Volontairement strict : une correspondance ambiguë doit faire
    échouer la construction du pilote plutôt que sélectionner le
    mauvais fait silencieusement.
    """
    matches = [f for f in facts if substring in f.fait]
    if len(matches) != 1:
        raise ValueError(
            f"Attendu exactement 1 fait contenant {substring!r}, trouvé {len(matches)}"
        )
    return matches[0]


# Décisions du curateur : (substring du fait, espèce GBIF, variable, valeur, niveau de preuve).
# Grade B (et non A) : une seule étude, pas une synthèse de plusieurs
# sources indépendantes (EvidenceLevel A réservé à un consensus établi).
_CURATED_MAPPING: list[tuple[str, int, str, str, str]] = [
    (
        "Quercus robur est plus tolérant à l'engorgement",
        GBIF_TAXON_KEY_QUERCUS_ROBUR,
        "tolerance_engorgement_racinaire",
        "Plus tolérant à l'engorgement racinaire que Quercus petraea",
        "B",
    ),
    (
        "Quercus robur est plus tolérant à l'engorgement",
        GBIF_TAXON_KEY_QUERCUS_PETRAEA,
        "tolerance_engorgement_racinaire",
        "Moins tolérant à l'engorgement racinaire que Quercus robur",
        "B",
    ),
    (
        "Quercus petraea est plus tolérant à la sécheresse",
        GBIF_TAXON_KEY_QUERCUS_PETRAEA,
        "tolerance_secheresse",
        "Plus tolérant à la sécheresse que Quercus robur",
        "B",
    ),
    (
        "Quercus petraea est plus tolérant à la sécheresse",
        GBIF_TAXON_KEY_QUERCUS_ROBUR,
        "tolerance_secheresse",
        "Moins tolérant à la sécheresse que Quercus petraea",
        "B",
    ),
    (
        "Quercus petraea se trouve sur des sols acides",
        GBIF_TAXON_KEY_QUERCUS_PETRAEA,
        "preference_edaphique",
        "Sols acides profonds et bien drainés",
        "B",
    ),
    (
        "Quercus robur est plus commun sur des sols alluviaux",
        GBIF_TAXON_KEY_QUERCUS_ROBUR,
        "preference_edaphique",
        "Sols alluviaux profonds et fertiles",
        "B",
    ),
]


def build_autecology_pilot_profiles() -> list[AutecologyProfileCreate]:
    """Construit les `AutecologyProfileCreate` réels du pilote Quercus (2026-07-19).

    6 profils (2 essences × 3 variables), tous tracés jusqu'à leur
    citation exacte via `build_autecology_profile_from_quarantined_fact`
    — voir `_CURATED_MAPPING` pour les décisions du curateur.
    """
    facts = _load_facts()
    source = _source()
    profiles = []
    for substring, gbif_key, variable, value_text, evidence_level in _CURATED_MAPPING:
        fact = _fact_matching(facts, substring)
        profiles.append(
            build_autecology_profile_from_quarantined_fact(
                fact,
                species_gbif_taxon_key=gbif_key,
                variable=variable,
                evidence_level=evidence_level,
                source=source,
                value_text=value_text,
            )
        )
    return profiles


async def seed_autecology_pilot() -> list[AutecologyProfileCreate]:
    """Point d'entrée destiné à `run_seeds.py` — NON câblé pour persister.

    RFC-0016 exige que `species_gbif_taxon_key` soit résolu en
    `entity_id` réel (déduplication via `BotanicalEngine._get_or_create_taxon`)
    avant toute écriture en base — ce câblage nécessite une session DB
    async vivante (`gsie_api.infrastructure.database.async_session_factory`)
    indisponible dans cet environnement au moment de l'écriture
    (`ConnectionRefusedError`). Retourne donc les objets validés,
    prêts à être persistés par un appelant disposant d'une session DB,
    plutôt que d'échouer silencieusement ou d'inventer une persistance.
    """
    return build_autecology_pilot_profiles()

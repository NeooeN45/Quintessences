"""Garde anti-invention RFC-0014 — détection automatique des données AI-sourced.

RFC-0014 §3.2 : « L'IA assiste, ne décide jamais. » Les données
produites par un LLM (extraction, génération, synthèse) ne peuvent
pas être ingérées au même niveau de preuve qu'une source peer-reviewed
ou officielle. Elles doivent être :

1. Marquées `evidence_level = D` (Hypothèse — expert non identifié).
2. Mises en `quarantine` (validation humaine requise — CON-001).
3. Traçables : la source doit citer le modèle et la version utilisés.

Cette garde s'applique **avant** l'Evidence Engine : elle intercepte
les soumissions dont la provenance est AI-sourced et force le niveau
de preuve vers D, indépendamment de la matrice de décision. Sans elle,
une soumission `type_source = peer_reviewed` + `auteur = "Claude"`
recevrait le niveau B — contournant le garde-fou.

Détection (heuristique conservatrice — faux positifs préférés aux
faux négatifs) :
- `auteur` contient un nom de modèle LLM connu.
- `reference` contient un marqueur d'extraction AI.
- `version_source` contient un identifiant de modèle.

La liste des marqueurs est extensible via la configuration.
"""

from __future__ import annotations

import re
from typing import Final

from gsie_api.engines.evidence.schemas import (
    EvidenceLevel,
    KnowledgeStatus,
    QualifiedKnowledge,
    RawKnowledgeSubmission,
)

# Marqueurs d'origine AI — détection conservatrice (insensible à la casse).
# Tout match, même partiel, déclenche la garde. Faux positifs préférés :
# un humain peut toujours valider une donnée légitime marquée à tort.
_MARQUEURS_AI: Final[frozenset[str]] = frozenset(
    {
        "claude",
        "gpt",
        "chatgpt",
        "openai",
        "anthropic",
        "llm",
        "gemini",
        "llama",
        "mistral",
        "copilot",
        "ai-generated",
        "ai-extracted",
        "ai-sourced",
        "machine-generated",
        "silvi",  # Treekipedia (SilviProtocol) — extraction LLM
        "treekipedia",
    }
)

# Regex compilée une fois — recherche insensible à la casse.
_PATTERN_AI = re.compile(
    "|".join(re.escape(m) for m in _MARQUEURS_AI),
    re.IGNORECASE,
)


def est_ai_sourced(submission: RawKnowledgeSubmission) -> bool:
    """Détecte si une soumission provient d'une extraction IA.

    Heuristique conservatrice : tout marqueur AI dans l'auteur, la
    référence ou la version de la source déclenche la garde. Les faux
    positifs sont préférés aux faux négatifs : une donnée humaine
    marquée à tort sera validée par un humain (surcoût minimal), alors
    qu'une donnée AI non détectée serait ingérée au niveau B (risque
    scientifique maximal — violation de CON-002).

    Args:
        submission: Soumission de connaissance brute.

    Returns:
        True si la soumission est détectée comme AI-sourced.
    """
    source = submission.source_candidate
    champs_a_verifier = [
        source.auteur,
        source.reference,
        source.version_source or "",
    ]
    return any(_PATTERN_AI.search(champ) for champ in champs_a_verifier)


def appliquer_garde_anti_invention(
    submission: RawKnowledgeSubmission,
    qualified: QualifiedKnowledge,
) -> QualifiedKnowledge:
    """Applique la garde RFC-0014 sur une connaissance qualifiée.

    Si la soumission est AI-sourced, force :
    - `evidence_level = D` (Hypothèse — expert non identifié).
    - `statut = quarantine` (validation humaine requise — CON-001).

    La garde est appliquée **après** l'Evidence Engine : elle corrige
    le niveau si la matrice a attribué un niveau supérieur (B, C) à
    tort. Elle ne relève jamais le niveau — une donnée déjà à F reste
    à F (refusée), une donnée à D reste à D (quarantaine).

    Args:
        submission: Soumission originale (pour détecter l'origine AI).
        qualified: Connaissance qualifiée par l'Evidence Engine.

    Returns:
        Connaissance qualifiée corrigée si AI-sourced, inchangée sinon.
    """
    if not est_ai_sourced(submission):
        return qualified

    # Ne jamais relever le niveau : F reste F (refus), D/E restent D/E.
    # On ne corrige que si l'Evidence Engine a attribué un niveau
    # supérieur (A, B, C) à une source AI-sourced.
    if qualified.evidence_level in (EvidenceLevel.A, EvidenceLevel.B, EvidenceLevel.C):
        return QualifiedKnowledge(
            connaissance_id=qualified.connaissance_id,
            contenu_normalise=qualified.contenu_normalise,
            evidence_level=EvidenceLevel.D,
            source=qualified.source,
            version=qualified.version,
            date_qualification=qualified.date_qualification,
            conflits=qualified.conflits,
            statut=KnowledgeStatus.quarantine,
        )

    # Si déjà à D ou E, on force quand même quarantine (pas accepte).
    if qualified.statut == KnowledgeStatus.accepte:
        return QualifiedKnowledge(
            connaissance_id=qualified.connaissance_id,
            contenu_normalise=qualified.contenu_normalise,
            evidence_level=EvidenceLevel.D,
            source=qualified.source,
            version=qualified.version,
            date_qualification=qualified.date_qualification,
            conflits=qualified.conflits,
            statut=KnowledgeStatus.quarantine,
        )

    # Niveau F (refuse) — on ne change rien : la donnée est déjà refusée.
    return qualified

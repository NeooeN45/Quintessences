"""Garde de qualification humaine avant promotion d'un scénario Gold.

La fonction d'évaluation est pure et n'effectue aucune promotion. Elle rend
explicites les preuves manquantes afin que le Fondateur puisse décider.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

QualificationOutcome = Literal["pending", "qualified", "rejected"]


@dataclass(frozen=True, slots=True)
class ExpertReviewDecision:
    """Avis humain versionné, sans identité personnelle superflue."""

    reviewer_id: str
    expertise_scope: str
    independent: bool
    scientific_review_complete: bool
    rights_review_complete: bool
    claims_checked: tuple[str, ...]
    tolerances_defined: bool
    alternatives_defined: bool
    recommendation_vetoes_defined: bool
    decision: Literal["approve", "reject", "request_changes"]
    notes: str


@dataclass(frozen=True, slots=True)
class GoldQualificationResult:
    """Résultat de la garde, sans effet de bord."""

    outcome: QualificationOutcome
    reasons: tuple[str, ...]
    reviewer_ids: tuple[str, ...]


def assess_gold_qualification(
    reviews: tuple[ExpertReviewDecision, ...],
    *,
    required_claims: tuple[str, ...],
) -> GoldQualificationResult:
    """Évalue si un scénario peut être proposé à la qualification Gold.

    Il faut deux relectures indépendantes, couvrant science et droits, avec
    les mêmes revendications contrôlées, des tolérances et des vetos définis.
    L'absence d'une preuve retourne ``pending`` ; un avis de rejet retourne
    ``rejected``. Aucun statut de scénario n'est modifié par cette fonction.
    """

    reasons: list[str] = []
    reviewer_ids = tuple(review.reviewer_id for review in reviews)
    if len(reviews) < 2:
        reasons.append("Deux relectures expertes indépendantes sont nécessaires")
    if len(set(reviewer_ids)) != len(reviewer_ids):
        reasons.append("Les relecteurs doivent être distincts")
    if any(not review.independent for review in reviews):
        reasons.append("Chaque relecture doit déclarer son indépendance")
    if any(review.decision == "reject" for review in reviews):
        reasons.append("Au moins un relecteur a rejeté le scénario")
    if any(review.decision == "request_changes" for review in reviews):
        reasons.append("Des corrections sont demandées par un relecteur")
    if any(not review.scientific_review_complete for review in reviews):
        reasons.append("La relecture scientifique est incomplète")
    if any(not review.rights_review_complete for review in reviews):
        reasons.append("La qualification des droits est incomplète")
    expected_claims = set(required_claims)
    if any(expected_claims - set(review.claims_checked) for review in reviews):
        reasons.append("Toutes les revendications requises ne sont pas vérifiées")
    if any(not review.tolerances_defined for review in reviews):
        reasons.append("Les tolérances de mesure ou de score ne sont pas fixées")
    if any(not review.alternatives_defined for review in reviews):
        reasons.append("Les réponses alternatives acceptables ne sont pas définies")
    if any(not review.recommendation_vetoes_defined for review in reviews):
        reasons.append("Les vetos de recommandation ne sont pas définis")
    if reasons:
        outcome: QualificationOutcome = (
            "rejected" if any(review.decision == "reject" for review in reviews) else "pending"
        )
        return GoldQualificationResult(outcome, tuple(dict.fromkeys(reasons)), reviewer_ids)
    return GoldQualificationResult("qualified", (), reviewer_ids)


__all__ = [
    "ExpertReviewDecision",
    "GoldQualificationResult",
    "assess_gold_qualification",
]

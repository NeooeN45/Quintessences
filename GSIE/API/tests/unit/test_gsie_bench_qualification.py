"""Tests de la garde humaine avant qualification Gold."""

from gsie_api.benchmark import ExpertReviewDecision, assess_gold_qualification

REQUIRED_CLAIMS = ("dendrometry", "sampling", "rights")


def _review(reviewer_id: str, **overrides: object) -> ExpertReviewDecision:
    values: dict[str, object] = {
        "reviewer_id": reviewer_id,
        "expertise_scope": "dendrométrie forestière",
        "independent": True,
        "scientific_review_complete": True,
        "rights_review_complete": True,
        "claims_checked": REQUIRED_CLAIMS,
        "tolerances_defined": True,
        "alternatives_defined": True,
        "recommendation_vetoes_defined": True,
        "decision": "approve",
        "notes": "Relecture documentée.",
    }
    values.update(overrides)
    return ExpertReviewDecision(**values)  # type: ignore[arg-type]


def should_keep_gold_qualification_pending_without_two_experts() -> None:
    result = assess_gold_qualification((), required_claims=REQUIRED_CLAIMS)
    assert result.outcome == "pending"
    assert "Deux relectures" in result.reasons[0]


def should_reject_gold_qualification_after_expert_rejection() -> None:
    result = assess_gold_qualification(
        (_review("expert-a", decision="reject"), _review("expert-b")),
        required_claims=REQUIRED_CLAIMS,
    )
    assert result.outcome == "rejected"


def should_qualify_only_two_complete_independent_reviews() -> None:
    result = assess_gold_qualification(
        (_review("expert-a"), _review("expert-b")),
        required_claims=REQUIRED_CLAIMS,
    )
    assert result.outcome == "qualified"
    assert result.reasons == ()


def should_keep_qualification_pending_when_rights_are_missing() -> None:
    result = assess_gold_qualification(
        (_review("expert-a"), _review("expert-b", rights_review_complete=False)),
        required_claims=REQUIRED_CLAIMS,
    )
    assert result.outcome == "pending"
    assert "droits" in " ".join(result.reasons)

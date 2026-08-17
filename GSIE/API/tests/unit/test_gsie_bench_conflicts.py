"""Tests du scénario de contradiction dendrométrique en quarantaine."""

from gsie_api.benchmark import NaiveBaseline, build_dendrometry_conflict_catalog


def should_keep_dendrometry_conflict_out_of_gold() -> None:
    scenario = build_dendrometry_conflict_catalog()[0]
    assert scenario.level == "silver"
    assert scenario.visibility == "quarantine"
    assert scenario.qualification_status == "pending_expert_review"
    assert scenario.variation_kind == "contradictory_dendrometry"
    assert scenario.inputs["peuplement"]["diametre_moyen_cm"] == 53


def should_make_naive_baseline_abstain_on_dendrometry_conflict() -> None:
    scenario = build_dendrometry_conflict_catalog()[0]
    prediction = NaiveBaseline().predict(scenario)
    assert prediction.abstained is True
    assert prediction.warnings

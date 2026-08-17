"""Tests contractuels de la première tranche GSIE-Bench v0.1."""

from dataclasses import replace

import pytest

from gsie_api.benchmark import (
    CandidatePrediction,
    DeterministicRunner,
    NaiveBaseline,
    QualificationRequiredError,
    RuleBaseline,
    ScenarioIntegrityError,
    build_gold_catalog,
)
from gsie_api.benchmark.catalog import rich_scenario_sections


def should_build_three_gold_parents_and_thirty_variations() -> None:
    catalog = build_gold_catalog()

    assert len(catalog) == 30
    assert len({scenario.parent_scenario_id for scenario in catalog}) == 3
    assert all(scenario.level == "gold" for scenario in catalog)
    assert all(scenario.qualification_status == "pending_expert_review" for scenario in catalog)
    assert len({scenario.checksum for scenario in catalog}) == 30
    for parent_id in {scenario.parent_scenario_id for scenario in catalog}:
        children = [scenario for scenario in catalog if scenario.parent_scenario_id == parent_id]
        assert len(children) == 10
    assert all(len(rich_scenario_sections(scenario)) == 11 for scenario in catalog)
    assert {scenario.parent_scenario_id for scenario in catalog} == {
        "gold.longeyroux.001",
        "gold.hetre.002",
        "gold.vergne.003",
    }


def should_refuse_closed_run_before_calling_candidate() -> None:
    class FailingCandidate(RuleBaseline):
        def predict(self, scenario):  # type: ignore[no-untyped-def]
            raise AssertionError("Le candidat ne doit pas être appelé")

    with pytest.raises(QualificationRequiredError):
        DeterministicRunner().run(FailingCandidate(), build_gold_catalog())


def should_score_rule_baseline_on_a_qualified_complete_case() -> None:
    scenario = next(
        item for item in build_gold_catalog() if item.scenario_id == "gold.hetre.002.complete"
    )
    qualified = replace(scenario, qualification_status="qualified", checksum="")

    result = DeterministicRunner().run(RuleBaseline(), (qualified,))

    assert result.status == "GO"
    assert result.metrics["scenario_pass_rate"] == 1.0
    assert result.evaluations[0].metrics["f1"] == 1.0


def should_keep_naive_baseline_non_promotable_on_complete_case() -> None:
    scenario = next(
        item for item in build_gold_catalog() if item.scenario_id == "gold.longeyroux.001.complete"
    )
    qualified = replace(scenario, qualification_status="qualified", checksum="")

    result = DeterministicRunner().run(NaiveBaseline(), (qualified,))

    assert result.status == "INCONCLUSIVE"
    assert result.evaluations[0].passed is False


def should_not_expose_private_answers_to_candidate() -> None:
    scenario = next(
        item for item in build_gold_catalog() if item.scenario_id == "gold.longeyroux.001.complete"
    )
    qualified = replace(scenario, qualification_status="qualified", checksum="")
    observed: list[object] = []

    class InspectingCandidate:
        candidate_id = "test.blind"
        candidate_version = "0.1.0"
        candidate_kind = "deterministic_rule"

        def predict(self, candidate_scenario):  # type: ignore[no-untyped-def]
            observed.append(candidate_scenario)
            assert not hasattr(candidate_scenario, "expected_labels")
            assert not hasattr(candidate_scenario, "required_factors")
            assert not hasattr(candidate_scenario, "forbidden_recommendations")
            assert not hasattr(candidate_scenario, "qualification_status")
            return CandidatePrediction(scenario_id=candidate_scenario.scenario_id, abstained=True)

    result = DeterministicRunner().run(InspectingCandidate(), (qualified,))

    assert result.status == "INCONCLUSIVE"
    assert len(observed) == 1


def should_reject_tampered_scenario_checksum_before_calling_candidate() -> None:
    scenario = next(
        item for item in build_gold_catalog() if item.scenario_id == "gold.hetre.002.complete"
    )
    qualified = replace(
        scenario,
        qualification_status="qualified",
        inputs={**scenario.inputs, "tampered": True},
        checksum=scenario.checksum,
    )

    with pytest.raises(ScenarioIntegrityError):
        DeterministicRunner().run(RuleBaseline(), (qualified,))


def should_keep_candidate_inputs_immutable() -> None:
    scenario = next(
        item for item in build_gold_catalog() if item.scenario_id == "gold.vergne.003.complete"
    )
    qualified = replace(scenario, qualification_status="qualified", checksum="")

    class MutatingCandidate:
        candidate_id = "test.mutating"
        candidate_version = "0.1.0"
        candidate_kind = "deterministic_rule"

        def predict(self, candidate_scenario):  # type: ignore[no-untyped-def]
            with pytest.raises(TypeError):
                candidate_scenario.inputs["peuplement"]["surface_terriere_m2_ha"] = 99
            return CandidatePrediction(scenario_id=candidate_scenario.scenario_id, abstained=True)

    DeterministicRunner().run(MutatingCandidate(), (qualified,))


def should_emit_a_reproducible_immutable_run_manifest() -> None:
    scenario = next(
        item for item in build_gold_catalog() if item.scenario_id == "gold.hetre.002.complete"
    )
    qualified = replace(scenario, qualification_status="qualified", checksum="")
    runner = DeterministicRunner()

    first = runner.run(RuleBaseline(), (qualified,))
    second = runner.run(RuleBaseline(), (qualified,))

    assert first.manifest is not None
    assert first.manifest.run_id == first.run_id
    assert first.manifest.scenario_ids == (qualified.scenario_id,)
    assert first.manifest.scenario_checksums == (qualified.checksum,)
    assert first.manifest.prediction_checksums == (first.predictions[0].compute_checksum(),)
    assert first.manifest.manifest_checksum == first.manifest.compute_checksum()
    assert first.manifest.manifest_checksum == second.manifest.manifest_checksum
    assert first.manifest.evaluation_checksums
    with pytest.raises(TypeError):
        first.manifest.artifact_checksums["unexpected"] = "tampered"

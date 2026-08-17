"""Tests de la suite Open/Silver synthétique GSIE-Bench."""

from dataclasses import replace

import pytest

from gsie_api.benchmark import (
    DeterministicRunner,
    RuleBaseline,
    RunPolicy,
    build_open_silver_catalog,
)


def should_build_a_qualified_open_silver_suite() -> None:
    scenarios = build_open_silver_catalog()

    assert len(scenarios) == 3
    assert all(scenario.level == "silver" for scenario in scenarios)
    assert all(scenario.visibility == "open" for scenario in scenarios)
    assert all(scenario.qualification_status == "qualified" for scenario in scenarios)
    assert all(scenario.rights_status == "synthetic_internal" for scenario in scenarios)


def should_run_rule_baseline_on_open_silver_without_gold_access() -> None:
    result = DeterministicRunner(RunPolicy.open_silver()).run(
        RuleBaseline(), build_open_silver_catalog()
    )

    assert result.status == "GO"
    assert result.metrics["scenario_pass_rate"] == 1.0
    assert result.manifest is not None


def should_reject_gold_scenarios_in_open_silver_policy() -> None:
    gold_like = build_open_silver_catalog()[0].with_qualification("qualified")
    gold_like = replace(gold_like, level="gold", visibility="closed", checksum="")

    with pytest.raises(ValueError, match="niveau"):
        DeterministicRunner(RunPolicy.open_silver()).run(RuleBaseline(), (gold_like,))

"""Tests du registre et de l'adaptateur des 14 moteurs GSIE."""

import pytest

from gsie_api.benchmark.adapters import (
    ENGINE_CONTRACTS,
    EngineBenchmarkAdapter,
    engine_contract_catalog,
)
from gsie_api.benchmark.models import CandidatePrediction, CandidateScenario


def should_register_the_fourteen_gsie_engines_once() -> None:
    catalog = engine_contract_catalog()

    assert len(catalog) == 14
    assert len({contract.engine_id for contract in catalog}) == 14
    assert tuple(contract.engine_id for contract in catalog) == tuple(
        contract.engine_id for contract in ENGINE_CONTRACTS
    )
    assert {contract.execution_mode for contract in catalog} == {"sync", "async"}


def should_adapt_an_injected_engine_without_instantiating_dependencies() -> None:
    calls: list[str] = []

    def predictor(scenario):  # type: ignore[no-untyped-def]
        calls.append(scenario.scenario_id)
        return CandidatePrediction(
            scenario_id=scenario.scenario_id,
            diagnostic_labels=("synthetic",),
        )

    adapter = EngineBenchmarkAdapter("diagnostic", predictor, version="test")
    scenario = CandidateScenario(
        scenario_id="silver.synthetic.001",
        scenario_version="0.1.0",
        suite_version="0.1.0",
        territory="synthetic",
        period="2026",
        inputs={"schema_version": "synthetic.v1"},
    )

    result = adapter.predict(scenario)

    assert result.diagnostic_labels == ("synthetic",)
    assert calls == ["silver.synthetic.001"]
    assert adapter.candidate_id == "engine.diagnostic"
    assert adapter.candidate_kind == "gsie_engine"


def should_reject_unknown_engine_contract() -> None:
    with pytest.raises(ValueError, match="inconnu"):
        EngineBenchmarkAdapter("unknown", lambda scenario: CandidatePrediction(scenario_id="x"))

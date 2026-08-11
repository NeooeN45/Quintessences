"""Tests de la politique de couverture multicouche GSIE."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from types import ModuleType


CI_WORKFLOW = Path(__file__).resolve().parents[4] / ".github" / "workflows" / "ci.yml"


def _load_script() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "check_coverage_policy.py"
    spec = importlib.util.spec_from_file_location("check_coverage_policy", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _summary(covered: int, statements: int) -> dict[str, int | float]:
    return {
        "covered_lines": covered,
        "num_statements": statements,
        "percent_covered": covered / statements * 100,
    }


def _report(
    *,
    total_percent: float = 98.0,
    contract: tuple[int, int] = (10, 10),
    business: tuple[int, int] = (9, 10),
    infrastructure: tuple[int, int] = (6, 10),
) -> dict[str, Any]:
    contract_covered, contract_statements = contract
    business_covered, business_statements = business
    infrastructure_covered, infrastructure_statements = infrastructure
    return {
        "totals": {"percent_covered": total_percent},
        "files": {
            "src\\gsie_api\\resources\\router.py": {
                "summary": _summary(contract_covered, contract_statements)
            },
            "src/gsie_api/engines/reasoning/engine.py": {
                "summary": _summary(business_covered, business_statements)
            },
            "src/gsie_api/infrastructure/database.py": {
                "summary": _summary(infrastructure_covered, infrastructure_statements)
            },
        },
    }


def should_accept_a_report_that_meets_every_layer() -> None:
    module = _load_script()

    assert module.evaluate_coverage_policy(_report()) == []


def should_reject_a_global_regression_below_the_ratchet() -> None:
    module = _load_script()

    violations = module.evaluate_coverage_policy(_report(total_percent=97.09))

    assert any("globale" in violation and "97.10" in violation for violation in violations)


def should_require_every_public_router_and_schema_at_one_hundred_percent() -> None:
    module = _load_script()

    violations = module.evaluate_coverage_policy(_report(contract=(9, 10)))

    assert any(
        "resources/router.py" in violation and "100.00" in violation for violation in violations
    )


def should_require_business_and_infrastructure_minimums() -> None:
    module = _load_script()

    violations = module.evaluate_coverage_policy(_report(business=(7, 10), infrastructure=(5, 10)))

    assert any("métier" in violation and "80.00" in violation for violation in violations)
    assert any("infrastructure" in violation and "60.00" in violation for violation in violations)


def should_reject_an_empty_or_malformed_coverage_report() -> None:
    module = _load_script()

    violations = module.evaluate_coverage_policy({"files": {}, "totals": {}})

    assert any("inexploitable" in violation for violation in violations)


@pytest.mark.parametrize("total_percent", [float("nan"), float("inf"), -1.0, 101.0])
def should_reject_a_non_finite_or_out_of_range_global_percentage(
    total_percent: float,
) -> None:
    module = _load_script()

    violations = module.evaluate_coverage_policy(_report(total_percent=total_percent))

    assert any("inexploitable" in violation for violation in violations)


def should_reject_booleans_as_coverage_counts() -> None:
    module = _load_script()
    report = _report()
    report["files"]["src/gsie_api/engines/reasoning/engine.py"]["summary"]["covered_lines"] = True

    violations = module.evaluate_coverage_policy(report)

    assert any("inexploitable" in violation for violation in violations)


def should_wire_combined_coverage_into_the_mandatory_ci_gate() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "  python-coverage:" in workflow
    assert "coverage combine tests/perf/results/coverage-input" in workflow
    assert "scripts/check_coverage_policy.py" in workflow
    assert "python-coverage: ${{ needs.python-coverage.result }}" in workflow


def should_emit_a_success_message_compatible_with_windows_cp1252(
    tmp_path: Path, capsys: Any
) -> None:
    module = _load_script()
    report_path = tmp_path / "coverage.json"
    report_path.write_text(json.dumps(_report()), encoding="utf-8")

    assert module.main(["--report", str(report_path)]) == 0

    output = capsys.readouterr().out
    assert ">= 97.10%" in output
    output.encode("cp1252")

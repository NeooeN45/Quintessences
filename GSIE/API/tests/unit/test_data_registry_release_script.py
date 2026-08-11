"""Tests du harnais reproductible de clôture Data Registry."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType


def _load_script() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "validate_data_registry_release.py"
    spec = importlib.util.spec_from_file_location("validate_data_registry_release", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_extract_pytest_counts_reads_final_summary() -> None:
    module = _load_script()

    assert module.extract_pytest_counts("collecting...\n136 passed in 4.12s") == (136, None)
    assert module.extract_pytest_counts("70 passed, 1 failed in 2.00s") == (70, 1)
    assert module.extract_pytest_counts("Success: no issues found") == (None, None)


def test_build_commands_contains_the_three_reference_campaigns() -> None:
    module = _load_script()

    commands = dict(module.build_commands())

    assert {"data_registry", "p0_p1", "infrastructure_lifespan"} <= commands.keys()
    assert "tests/integration/test_dataset_manifest_application.py" in commands["data_registry"]
    assert commands["data_registry"][-4:] == ["--no-cov", "-n", "0", "-q"]

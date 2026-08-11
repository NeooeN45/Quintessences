"""Reproduit les preuves de clôture de la tranche Data Registry.

Le script exécute les trois campagnes de référence ainsi que les contrôles
statiques, puis écrit un rapport JSON horodaté exploitable localement et en CI.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_DIR = API_ROOT / "tests" / "perf" / "results"


@dataclass(frozen=True)
class CommandResult:
    """Résultat sérialisable d'une commande de validation."""

    name: str
    command: list[str]
    return_code: int
    duration_seconds: float
    passed: int | None
    failed: int | None
    output: str

    @property
    def succeeded(self) -> bool:
        return self.return_code == 0


def _pytest_command(*targets: str) -> list[str]:
    return [sys.executable, "-m", "pytest", *targets, "--no-cov", "-n", "0", "-q"]


def build_commands() -> list[tuple[str, list[str]]]:
    """Construit les commandes exactes et stables constituant la preuve."""

    campaign_registry = _pytest_command(
        "tests/integration/test_dataset_manifest_application.py",
        "tests/unit/test_data_registry_adapters.py",
        "tests/unit/test_data_registry_bootstrap.py",
        "tests/unit/test_data_registry_contracts.py",
        "tests/unit/test_data_registry_health_scheduler.py",
        "tests/unit/test_data_registry_imports.py",
        "tests/unit/test_data_registry_infrastructure_smoke_script.py",
        "tests/unit/test_data_registry_models.py",
        "tests/unit/test_data_registry_release_script.py",
        "tests/unit/test_data_registry_resolver.py",
        "tests/unit/test_data_registry_router.py",
        "tests/unit/test_data_registry_service.py",
        "tests/unit/test_data_registry_validators.py",
        "tests/unit/test_dataset_manifest.py",
        "tests/unit/test_fetch_policy.py",
        "tests/unit/test_object_storage.py",
        "tests/unit/test_autecology_adapter.py",
        "tests/unit/test_gbif_adapter.py",
        "tests/unit/test_ign_adapter.py",
        "tests/unit/test_meteofrance_adapter.py",
        "tests/unit/test_soilgrids_adapter.py",
    )
    campaign_p0_p1 = _pytest_command(
        "tests/unit/test_migration_contract.py",
        "tests/unit/test_resources.py",
        "tests/unit/test_data_registry_imports.py",
        "tests/unit/test_object_storage.py",
        "tests/integration/test_dataset_manifest_application.py",
    )
    campaign_infrastructure = _pytest_command(
        "tests/unit/test_app.py",
        "tests/unit/test_infra_coverage.py",
    )
    return [
        ("data_registry", campaign_registry),
        ("p0_p1", campaign_p0_p1),
        ("infrastructure_lifespan", campaign_infrastructure),
        (
            "ruff",
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "src/gsie_api/data",
                "scripts/validate_data_registry_release.py",
            ],
        ),
        ("mypy_strict", [sys.executable, "-m", "mypy", "src/gsie_api/data"]),
    ]


def extract_pytest_counts(output: str) -> tuple[int | None, int | None]:
    """Extrait les compteurs pytest sans rendre le succès dépendant du format."""

    passed_matches = re.findall(r"(\d+) passed", output)
    failed_matches = re.findall(r"(\d+) failed", output)
    passed = int(passed_matches[-1]) if passed_matches else None
    failed = int(failed_matches[-1]) if failed_matches else None
    return passed, failed


def run_command(name: str, command: list[str]) -> CommandResult:
    """Exécute une commande sans shell et conserve sa sortie complète."""

    print(f"\n=== {name} ===", flush=True)
    print(" ".join(command), flush=True)
    started = time.monotonic()
    completed = subprocess.run(  # noqa: S603 - commande interne, sans entrée utilisateur
        command,
        cwd=API_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    duration = time.monotonic() - started
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
    print(output, flush=True)
    passed, failed = extract_pytest_counts(output)
    return CommandResult(
        name=name,
        command=command,
        return_code=completed.returncode,
        duration_seconds=round(duration, 3),
        passed=passed,
        failed=failed,
        output=output,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="Chemin du rapport JSON (par défaut : tests/perf/results horodaté).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started_at = datetime.now(UTC)
    results = [run_command(name, command) for name, command in build_commands()]
    finished_at = datetime.now(UTC)
    succeeded = all(result.succeeded for result in results)
    output_path = args.output or (
        DEFAULT_RESULTS_DIR
        / f"data_registry_validation_{started_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    if not output_path.is_absolute():
        output_path = API_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": "1.0",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "python": sys.version,
        "platform": sys.platform,
        "succeeded": succeeded,
        "commands": [{**asdict(result), "succeeded": result.succeeded} for result in results],
    }
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nRapport : {output_path}", flush=True)
    print(f"Verdict : {'SUCCÈS' if succeeded else 'ÉCHEC'}", flush=True)
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())

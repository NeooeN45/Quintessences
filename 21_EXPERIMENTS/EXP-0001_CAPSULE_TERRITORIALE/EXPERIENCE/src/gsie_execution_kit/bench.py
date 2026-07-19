"""Golden Bench minimal : reproductibilité numérique et gouvernance scientifique."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gsie_execution_kit.json_utils import StrictJsonError, loads_strict

CASE_SCHEMA_VERSION = "1.0.0"
REVIEW_STATUSES = {"draft", "needs_domain_review", "reviewed", "approved", "deprecated"}
REVIEW_GATE_STATUSES = {"reviewed", "approved"}
PRODUCTION_REVIEW_STATUSES = {"approved"}


class BenchError(RuntimeError):
    """Signale un cas Golden Bench invalide ou impossible à exécuter."""


@dataclass(frozen=True, slots=True)
class AlgorithmResult:
    value: float
    unit: str


@dataclass(frozen=True, slots=True)
class BenchCaseResult:
    case_id: str
    title: str
    algorithm: str
    algorithm_version: str
    expected: float
    observed: float
    unit: str
    absolute_tolerance: float
    absolute_error: float
    numeric_status: str
    scientific_review_status: str
    production_eligible: bool
    source_file: str


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_finite_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise BenchError(f"{field} doit être un nombre")
    number = float(value)
    if not math.isfinite(number):
        raise BenchError(f"{field} doit être fini")
    return number


def _basal_area_m2_v1(inputs: dict[str, Any]) -> AlgorithmResult:
    raw_diameters = inputs.get("diameters_cm")
    if not isinstance(raw_diameters, list):
        raise BenchError("inputs.diameters_cm doit être une liste")
    diameters: list[float] = []
    for index, value in enumerate(raw_diameters):
        diameter = _as_finite_number(value, f"diameters_cm[{index}]")
        if diameter <= 0:
            raise BenchError("Chaque diamètre mesuré doit être strictement positif")
        diameters.append(diameter)
    value = math.fsum(math.pi * (diameter / 200.0) ** 2 for diameter in diameters)
    return AlgorithmResult(value=value, unit="m2")


ALGORITHMS: dict[tuple[str, str], Callable[[dict[str, Any]], AlgorithmResult]] = {
    ("basal_area_m2", "1.0.0"): _basal_area_m2_v1,
}


def _load_case(path: Path) -> dict[str, Any]:
    try:
        raw = loads_strict(path.read_bytes())
    except (OSError, StrictJsonError) as exc:
        raise BenchError(f"Cas JSON invalide {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise BenchError(f"Le cas {path} doit contenir un objet JSON")
    return raw


def _require_string(case: dict[str, Any], field: str) -> str:
    value = case.get(field)
    if not isinstance(value, str) or not value.strip():
        raise BenchError(f"Champ obligatoire absent ou invalide : {field}")
    return value


def _execute_case(case: dict[str, Any], source_file: Path) -> BenchCaseResult:
    if case.get("case_schema_version") != CASE_SCHEMA_VERSION:
        raise BenchError(f"Version de cas non supportée dans {source_file}")
    case_id = _require_string(case, "case_id")
    title = _require_string(case, "title")
    _require_string(case, "domain")
    algorithm = _require_string(case, "algorithm")
    algorithm_version = _require_string(case, "algorithm_version")
    inputs = case.get("inputs")
    expected = case.get("expected")
    provenance = case.get("provenance")
    applicability = case.get("applicability")
    review = case.get("scientific_review")
    if not isinstance(inputs, dict):
        raise BenchError(f"{case_id}: inputs doit être un objet")
    if not isinstance(expected, dict):
        raise BenchError(f"{case_id}: expected doit être un objet")
    if not isinstance(provenance, dict) or not isinstance(provenance.get("sources"), list):
        raise BenchError(f"{case_id}: provenance.sources est obligatoire")
    if not provenance["sources"]:
        raise BenchError(f"{case_id}: au moins une source est obligatoire")
    if not isinstance(applicability, dict) or not applicability:
        raise BenchError(f"{case_id}: le domaine d'applicabilité est obligatoire")
    if not isinstance(review, dict):
        raise BenchError(f"{case_id}: scientific_review est obligatoire")
    review_status = review.get("status")
    reviewers = review.get("reviewers")
    if review_status not in REVIEW_STATUSES:
        raise BenchError(f"{case_id}: état de revue inconnu : {review_status!r}")
    if not isinstance(reviewers, list):
        raise BenchError(f"{case_id}: scientific_review.reviewers doit être une liste")
    if review_status in REVIEW_GATE_STATUSES and not reviewers:
        raise BenchError(f"{case_id}: un cas revu doit identifier au moins un relecteur")
    if review_status == "approved" and len(reviewers) < 2:
        raise BenchError(f"{case_id}: un cas approuvé exige deux relecteurs indépendants")

    algorithm_function = ALGORITHMS.get((algorithm, algorithm_version))
    if algorithm_function is None:
        raise BenchError(f"{case_id}: algorithme inconnu {algorithm}@{algorithm_version}")
    observed = algorithm_function(inputs)
    expected_value = _as_finite_number(expected.get("value"), f"{case_id}.expected.value")
    tolerance = _as_finite_number(
        expected.get("absolute_tolerance"), f"{case_id}.expected.absolute_tolerance"
    )
    if tolerance < 0:
        raise BenchError(f"{case_id}: la tolérance doit être positive ou nulle")
    expected_unit = expected.get("unit")
    if expected_unit != observed.unit:
        raise BenchError(
            f"{case_id}: unité attendue {expected_unit!r}, unité produite {observed.unit!r}"
        )
    absolute_error = abs(observed.value - expected_value)
    numeric_status = "passed" if absolute_error <= tolerance else "failed"
    return BenchCaseResult(
        case_id=case_id,
        title=title,
        algorithm=algorithm,
        algorithm_version=algorithm_version,
        expected=expected_value,
        observed=observed.value,
        unit=observed.unit,
        absolute_tolerance=tolerance,
        absolute_error=absolute_error,
        numeric_status=numeric_status,
        scientific_review_status=review_status,
        production_eligible=review_status in PRODUCTION_REVIEW_STATUSES,
        source_file=source_file.name,
    )


def run_bench(cases_dir: Path, *, require_reviewed: bool = False) -> dict[str, Any]:
    """Exécute tous les cas JSON et produit un rapport sérialisable."""

    if not cases_dir.is_dir():
        raise BenchError(f"Dossier de cas introuvable : {cases_dir}")
    case_paths = sorted(cases_dir.glob("*.json"))
    if not case_paths:
        raise BenchError(f"Aucun cas JSON dans {cases_dir}")

    results = [_execute_case(_load_case(path), path) for path in case_paths]
    case_ids = [result.case_id for result in results]
    if len(case_ids) != len(set(case_ids)):
        raise BenchError("Le Golden Bench contient des case_id dupliqués")

    numeric_failures = sum(result.numeric_status != "passed" for result in results)
    review_pending = sum(
        result.scientific_review_status not in REVIEW_GATE_STATUSES for result in results
    )
    production_eligible = sum(result.production_eligible for result in results)
    numeric_success = numeric_failures == 0
    review_gate_success = review_pending == 0
    success = numeric_success and (review_gate_success or not require_reviewed)
    if not numeric_success:
        status = "failed"
    elif require_reviewed and not review_gate_success:
        status = "failed_review_gate"
    elif not review_gate_success:
        status = "passed_with_review_pending"
    else:
        status = "passed"

    return {
        "bench_schema_version": "1.0.0",
        "generated_at": _iso_now(),
        "status": status,
        "success": success,
        "numeric_success": numeric_success,
        "scientific_review_gate_required": require_reviewed,
        "scientific_review_gate_success": review_gate_success,
        "summary": {
            "case_count": len(results),
            "numeric_passed": len(results) - numeric_failures,
            "numeric_failed": numeric_failures,
            "production_eligible": production_eligible,
            "review_pending": review_pending,
        },
        "cases": [asdict(result) for result in results],
    }

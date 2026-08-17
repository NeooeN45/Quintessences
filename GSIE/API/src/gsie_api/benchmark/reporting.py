"""Sérialisation publique et stable des résultats GSIE-Bench."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import BenchmarkRunResult


def run_result_to_dict(result: BenchmarkRunResult) -> dict[str, Any]:
    """Construit un rapport JSON sans référence privée de scoring."""

    manifest = result.manifest
    return {
        "run_id": result.run_id,
        "candidate_id": result.candidate_id,
        "candidate_version": result.candidate_version,
        "status": result.status,
        "metrics": dict(result.metrics),
        "veto_codes": list(result.veto_codes),
        "predictions": [
            {
                "scenario_id": prediction.scenario_id,
                "diagnostic_labels": list(prediction.diagnostic_labels),
                "factors": list(prediction.factors),
                "recommendations": list(prediction.recommendations),
                "evidence_ids": list(prediction.evidence_ids),
                "warnings": list(prediction.warnings),
                "veto_codes": list(prediction.veto_codes),
                "abstained": prediction.abstained,
                "confidence": prediction.confidence,
                "checksum": prediction.compute_checksum(),
            }
            for prediction in result.predictions
        ],
        "evaluations": [
            {
                "scenario_id": evaluation.scenario_id,
                "passed": evaluation.passed,
                "metrics": dict(evaluation.metrics),
                "veto_codes": list(evaluation.veto_codes),
                "reasons": list(evaluation.reasons),
                "prediction_checksum": evaluation.prediction_checksum,
                "checksum": evaluation.compute_checksum(),
            }
            for evaluation in result.evaluations
        ],
        "manifest": (
            {
                "run_id": manifest.run_id,
                "candidate_id": manifest.candidate_id,
                "candidate_version": manifest.candidate_version,
                "candidate_kind": manifest.candidate_kind,
                "suite_id": manifest.suite_id,
                "suite_version": manifest.suite_version,
                "status": manifest.status,
                "scenario_ids": list(manifest.scenario_ids),
                "scenario_checksums": list(manifest.scenario_checksums),
                "prediction_checksums": list(manifest.prediction_checksums),
                "evaluation_checksums": list(manifest.evaluation_checksums),
                "artifact_checksums": dict(manifest.artifact_checksums),
                "manifest_checksum": manifest.manifest_checksum,
            }
            if manifest is not None
            else None
        ),
    }


__all__ = ["run_result_to_dict"]

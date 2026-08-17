"""Runner déterministe, aveugle et fail-closed de GSIE-Bench v0.1."""

from __future__ import annotations

from hashlib import sha256
from json import dumps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

from .metrics import classification_metrics
from .models import (
    BenchmarkCandidate,
    BenchmarkRunManifest,
    BenchmarkRunResult,
    CandidatePrediction,
    GateStatus,
    RunPolicy,
    ScenarioEvaluation,
    ScenarioSpec,
)


class QualificationRequiredError(RuntimeError):
    """Une référence ou un scénario n'est pas qualifié pour cette suite."""


class ScenarioIntegrityError(RuntimeError):
    """Le manifeste d'un scénario ne correspond plus à son checksum."""


class DeterministicRunner:
    """Exécute un candidat sans accès aux réponses privées de référence."""

    def __init__(self, policy: RunPolicy | None = None) -> None:
        self.policy = policy or RunPolicy()

    @classmethod
    def open_silver(cls) -> DeterministicRunner:
        """Construit le runner public Silver/Bronze sans accès Gold."""

        return cls(RunPolicy.open_silver())

    def run(
        self,
        candidate: BenchmarkCandidate,
        scenarios: Iterable[ScenarioSpec],
    ) -> BenchmarkRunResult:
        ordered = tuple(sorted(scenarios, key=lambda scenario: scenario.scenario_id))
        self._validate_selection(ordered)
        predictions = tuple(candidate.predict(scenario.candidate_view()) for scenario in ordered)
        evaluations = tuple(
            self._evaluate(scenario, prediction)
            for scenario, prediction in zip(ordered, predictions, strict=True)
        )
        veto_codes = tuple(
            sorted({code for evaluation in evaluations for code in evaluation.veto_codes})
        )
        passed = sum(evaluation.passed for evaluation in evaluations)
        metrics = {
            "scenario_count": float(len(evaluations)),
            "scenario_pass_rate": passed / len(evaluations),
            "veto_count": float(len(veto_codes)),
        }
        status: GateStatus = (
            "NO-GO" if veto_codes else "GO" if passed == len(evaluations) else "INCONCLUSIVE"
        )
        run_payload = {
            "candidate_id": candidate.candidate_id,
            "candidate_version": candidate.candidate_version,
            "candidate_kind": candidate.candidate_kind,
            "suite_id": self.policy.suite_id,
            "suite_version": self.policy.suite_version,
            "scenario_checksums": [scenario.checksum for scenario in ordered],
        }
        run_id = sha256(dumps(run_payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
        evaluation_checksums = tuple(evaluation.compute_checksum() for evaluation in evaluations)
        prediction_checksums = tuple(prediction.compute_checksum() for prediction in predictions)
        result_payload = {
            "run_id": run_id,
            "status": status,
            "metrics": metrics,
            "veto_codes": veto_codes,
            "prediction_checksums": prediction_checksums,
            "evaluation_checksums": evaluation_checksums,
        }
        result_canonical = dumps(result_payload, sort_keys=True, default=str).encode("utf-8")
        manifest = BenchmarkRunManifest(
            run_id=run_id,
            candidate_id=candidate.candidate_id,
            candidate_version=candidate.candidate_version,
            candidate_kind=candidate.candidate_kind,
            suite_id=self.policy.suite_id,
            suite_version=self.policy.suite_version,
            status=status,
            scenario_ids=tuple(scenario.scenario_id for scenario in ordered),
            scenario_checksums=tuple(scenario.checksum for scenario in ordered),
            prediction_checksums=prediction_checksums,
            evaluation_checksums=evaluation_checksums,
            artifact_checksums={
                "predictions": sha256(
                    dumps(prediction_checksums, sort_keys=True).encode("utf-8")
                ).hexdigest(),
                "run_result": sha256(result_canonical).hexdigest(),
            },
        )
        return BenchmarkRunResult(
            run_id=run_id,
            candidate_id=candidate.candidate_id,
            candidate_version=candidate.candidate_version,
            status=status,
            evaluations=evaluations,
            metrics=metrics,
            veto_codes=veto_codes,
            manifest=manifest,
            predictions=predictions,
        )

    def _validate_selection(self, scenarios: tuple[ScenarioSpec, ...]) -> None:
        if not scenarios:
            raise ValueError("La suite GSIE-Bench ne peut pas être vide")
        ids = [scenario.scenario_id for scenario in scenarios]
        if len(ids) != len(set(ids)):
            raise ValueError("Les identifiants de scénario doivent être uniques")
        for scenario in scenarios:
            if scenario.compute_checksum() != scenario.checksum:
                raise ScenarioIntegrityError(
                    f"Le checksum du scénario {scenario.scenario_id} ne correspond pas au manifeste"
                )
            if scenario.suite_version != self.policy.suite_version:
                raise ValueError("La version de suite du scénario ne correspond pas à la politique")
            if scenario.level not in self.policy.allowed_levels:
                raise ValueError("Le niveau du scénario n'est pas autorisé par la suite")
            if (
                self.policy.require_qualified_references
                and scenario.qualification_status != "qualified"
            ):
                raise QualificationRequiredError(
                    f"{scenario.scenario_id} n'est pas qualifié pour l'exécution Closed"
                )

    @staticmethod
    def _evaluate(scenario: ScenarioSpec, prediction: CandidatePrediction) -> ScenarioEvaluation:
        if prediction.scenario_id != scenario.scenario_id:
            raise ValueError("Le candidat a retourné un scénario différent de celui demandé")
        veto_codes = set(prediction.veto_codes)
        reasons: list[str] = []
        expected = set(scenario.expected_labels)
        actual = set(prediction.diagnostic_labels)
        metrics = classification_metrics(expected, actual)
        if set(scenario.forbidden_recommendations) & set(prediction.recommendations):
            veto_codes.add("UNSAFE_SPECIES_RECOMMENDATION")
            reasons.append("Une recommandation interdite a été produite")
        if not prediction.abstained and not set(scenario.required_factors).issubset(
            prediction.factors
        ):
            veto_codes.add("CRITICAL_LIMITING_FACTOR_OMITTED")
            reasons.append("Un facteur attendu est absent de la sortie")
        if scenario.expected_behavior == "exact":
            passed = actual == expected and not veto_codes
        else:
            passed = bool(prediction.abstained or prediction.warnings) and not veto_codes
            if not passed:
                veto_codes.add("HIGH_CONFIDENCE_WITH_CRITICAL_MISSING_DATA")
                reasons.append("Le candidat ne s'est pas abstenu face à une preuve insuffisante")
        return ScenarioEvaluation(
            scenario_id=scenario.scenario_id,
            passed=passed,
            metrics=metrics,
            veto_codes=tuple(sorted(veto_codes)),
            reasons=tuple(reasons),
            prediction_checksum=prediction.compute_checksum(),
        )

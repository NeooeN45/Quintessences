"""Modèles immuables du contrat d'exécution GSIE-Bench v0.1."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from hashlib import sha256
from json import dumps
from types import MappingProxyType
from typing import Any, Literal, Protocol

ScenarioLevel = Literal["gold", "silver", "bronze"]
ScenarioVisibility = Literal["open", "closed", "quarantine"]
QualificationStatus = Literal[
    "pending_expert_review",
    "qualified",
    "rejected",
]
ExpectedBehavior = Literal["exact", "abstain_or_warn", "out_of_domain"]
GateStatus = Literal["GO", "NO-GO", "INCONCLUSIVE"]


def _freeze(value: Any) -> Any:
    """Fige récursivement une charge de scénario avant de l'exposer."""

    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set | frozenset):
        return frozenset(_freeze(item) for item in value)
    return value


def _jsonable(value: Any) -> Any:
    """Convertit une charge figée en structure JSON canonique."""

    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_jsonable(item) for item in value]
    if isinstance(value, set | frozenset):
        return sorted((_jsonable(item) for item in value), key=repr)
    return value


@dataclass(frozen=True, slots=True)
class ReferenceRef:
    """Référence scientifique sans copie implicite d'octets."""

    reference_id: str
    citation: str
    uri: str
    evidence_level: str
    rights_status: str

    def __post_init__(self) -> None:
        if not self.reference_id or not self.citation or not self.uri:
            raise ValueError("Une référence GSIE-Bench doit être identifiable et citable")
        if not self.evidence_level or not self.rights_status:
            raise ValueError("Le niveau de preuve et le régime de droits sont obligatoires")


@dataclass(frozen=True, slots=True)
class CandidateScenario:
    """Vue aveugle d'un scénario transmise à un candidat.

    Les réponses attendues, les facteurs obligatoires, les veto et le statut de
    qualification restent dans ``ScenarioSpec`` et ne franchissent jamais la
    frontière candidat.
    """

    scenario_id: str
    scenario_version: str
    suite_version: str
    territory: str
    period: str
    inputs: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.scenario_id or not self.scenario_version or not self.suite_version:
            raise ValueError("L'identité de la vue candidat est obligatoire")
        if not self.territory or not self.period or not self.inputs:
            raise ValueError("La vue candidat doit conserver le contexte et les entrées")
        object.__setattr__(self, "inputs", _freeze(self.inputs))


@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    """Scénario versionné transmis au candidat et à l'évaluateur."""

    scenario_id: str
    scenario_version: str
    suite_version: str
    level: ScenarioLevel
    visibility: ScenarioVisibility
    qualification_status: QualificationStatus
    territory: str
    period: str
    variation_kind: str
    parent_scenario_id: str
    inputs: Mapping[str, Any]
    expected_labels: tuple[str, ...]
    required_factors: tuple[str, ...]
    forbidden_recommendations: tuple[str, ...]
    expected_behavior: ExpectedBehavior
    references: tuple[ReferenceRef, ...]
    rights_status: str
    checksum: str = field(default="", compare=True)

    def __post_init__(self) -> None:
        if not self.scenario_id or not self.scenario_version or not self.suite_version:
            raise ValueError("L'identité du scénario est obligatoire")
        if not self.territory or not self.period or not self.variation_kind:
            raise ValueError("Le territoire, la période et la variation sont obligatoires")
        if not self.parent_scenario_id:
            raise ValueError("Un scénario doit référencer son scénario parent")
        if not self.references or not self.rights_status:
            raise ValueError("Une référence et un régime de droits sont obligatoires")
        if self.level == "gold" and self.visibility not in {"closed", "quarantine"}:
            raise ValueError("Un scénario Gold v0.1 doit rester Closed ou en quarantaine")
        if not self.inputs:
            raise ValueError("Les entrées du scénario ne peuvent pas être vides")
        if self.checksum and len(self.checksum) != 64:
            raise ValueError("Le checksum du scénario doit être un SHA-256 hexadécimal")
        object.__setattr__(self, "inputs", _freeze(self.inputs))
        if not self.checksum:
            object.__setattr__(self, "checksum", self.compute_checksum())

    def checksum_payload(self) -> dict[str, Any]:
        """Retourne la charge canonique, hors checksum calculé."""

        return {
            "scenario_id": self.scenario_id,
            "scenario_version": self.scenario_version,
            "suite_version": self.suite_version,
            "level": self.level,
            "visibility": self.visibility,
            "qualification_status": self.qualification_status,
            "territory": self.territory,
            "period": self.period,
            "variation_kind": self.variation_kind,
            "parent_scenario_id": self.parent_scenario_id,
            "inputs": _jsonable(self.inputs),
            "expected_labels": self.expected_labels,
            "required_factors": self.required_factors,
            "forbidden_recommendations": self.forbidden_recommendations,
            "expected_behavior": self.expected_behavior,
            "references": [
                {
                    "reference_id": reference.reference_id,
                    "citation": reference.citation,
                    "uri": reference.uri,
                    "evidence_level": reference.evidence_level,
                    "rights_status": reference.rights_status,
                }
                for reference in self.references
            ],
            "rights_status": self.rights_status,
        }

    def compute_checksum(self) -> str:
        """Calcule un checksum stable pour la version du scénario."""

        canonical = dumps(
            self.checksum_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return sha256(canonical.encode("utf-8")).hexdigest()

    def candidate_view(self) -> CandidateScenario:
        """Retourne uniquement les données autorisées au candidat."""

        return CandidateScenario(
            scenario_id=self.scenario_id,
            scenario_version=self.scenario_version,
            suite_version=self.suite_version,
            territory=self.territory,
            period=self.period,
            inputs=self.inputs,
        )

    def with_qualification(self, status: QualificationStatus) -> ScenarioSpec:
        """Retourne une nouvelle version logique avec un statut explicite."""

        return replace(self, qualification_status=status, checksum="")


@dataclass(frozen=True, slots=True)
class CandidatePrediction:
    """Sortie minimale et explicable d'un candidat."""

    scenario_id: str
    diagnostic_labels: tuple[str, ...] = ()
    factors: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    veto_codes: tuple[str, ...] = ()
    abstained: bool = False
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("Une prédiction doit identifier son scénario")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("La confiance doit être comprise entre 0 et 1")

    def compute_checksum(self) -> str:
        """Calcule l'empreinte de la sortie brute du candidat."""

        payload = {
            "scenario_id": self.scenario_id,
            "diagnostic_labels": self.diagnostic_labels,
            "factors": self.factors,
            "recommendations": self.recommendations,
            "evidence_ids": self.evidence_ids,
            "warnings": self.warnings,
            "veto_codes": self.veto_codes,
            "abstained": self.abstained,
            "confidence": self.confidence,
        }
        canonical = dumps(
            _jsonable(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return sha256(canonical.encode("utf-8")).hexdigest()


class BenchmarkCandidate(Protocol):
    """Interface commune aux baselines et moteurs comparés."""

    candidate_id: str
    candidate_version: str
    candidate_kind: str

    def predict(self, scenario: CandidateScenario) -> CandidatePrediction:
        """Produit une sortie pour un seul scénario, sans accès au Gold privé."""


@dataclass(frozen=True, slots=True)
class RunPolicy:
    """Politique d'exécution déterministe et fail-closed."""

    suite_id: str = "gsie-closed"
    suite_version: str = "0.1.0"
    require_qualified_references: bool = True
    allowed_levels: tuple[ScenarioLevel, ...] = ("gold",)

    @classmethod
    def open_silver(cls) -> RunPolicy:
        """Retourne la politique publique Silver/Bronze sans accès Gold."""

        return cls(
            suite_id="gsie-open-silver",
            suite_version="0.1.0",
            require_qualified_references=True,
            allowed_levels=("silver", "bronze"),
        )


@dataclass(frozen=True, slots=True)
class ScenarioEvaluation:
    scenario_id: str
    passed: bool
    metrics: Mapping[str, float]
    veto_codes: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    prediction_checksum: str = ""

    def compute_checksum(self) -> str:
        """Calcule l'empreinte de l'évaluation publique du scénario."""

        payload = {
            "scenario_id": self.scenario_id,
            "passed": self.passed,
            "metrics": self.metrics,
            "veto_codes": self.veto_codes,
            "reasons": self.reasons,
            "prediction_checksum": self.prediction_checksum,
        }
        canonical = dumps(
            _jsonable(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class BenchmarkRunManifest:
    """Manifeste immuable et rejouable d'une exécution de benchmark."""

    run_id: str
    candidate_id: str
    candidate_version: str
    candidate_kind: str
    suite_id: str
    suite_version: str
    status: GateStatus
    scenario_ids: tuple[str, ...]
    scenario_checksums: tuple[str, ...]
    prediction_checksums: tuple[str, ...]
    evaluation_checksums: tuple[str, ...]
    artifact_checksums: Mapping[str, str] = field(default_factory=dict)
    manifest_checksum: str = ""

    def __post_init__(self) -> None:
        if not self.run_id or not self.candidate_id or not self.candidate_version:
            raise ValueError("L'identité du manifeste de run est obligatoire")
        if len(self.scenario_ids) != len(self.scenario_checksums):
            raise ValueError("Chaque scénario doit avoir un checksum")
        if len(self.scenario_ids) != len(self.prediction_checksums):
            raise ValueError("Chaque scénario doit avoir une prédiction")
        if len(self.scenario_ids) != len(self.evaluation_checksums):
            raise ValueError("Chaque scénario doit avoir une évaluation")
        object.__setattr__(self, "artifact_checksums", _freeze(self.artifact_checksums))
        if self.manifest_checksum and len(self.manifest_checksum) != 64:
            raise ValueError("Le checksum du manifeste doit être un SHA-256 hexadécimal")
        if not self.manifest_checksum:
            object.__setattr__(self, "manifest_checksum", self.compute_checksum())

    def checksum_payload(self) -> dict[str, Any]:
        """Retourne les éléments couverts par le checksum du manifeste."""

        return {
            "run_id": self.run_id,
            "candidate_id": self.candidate_id,
            "candidate_version": self.candidate_version,
            "candidate_kind": self.candidate_kind,
            "suite_id": self.suite_id,
            "suite_version": self.suite_version,
            "status": self.status,
            "scenario_ids": self.scenario_ids,
            "scenario_checksums": self.scenario_checksums,
            "prediction_checksums": self.prediction_checksums,
            "evaluation_checksums": self.evaluation_checksums,
            "artifact_checksums": _jsonable(self.artifact_checksums),
        }

    def compute_checksum(self) -> str:
        """Calcule le checksum canonique du manifeste hors checksum lui-même."""

        canonical = dumps(
            _jsonable(self.checksum_payload()),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class BenchmarkRunResult:
    run_id: str
    candidate_id: str
    candidate_version: str
    status: GateStatus
    evaluations: tuple[ScenarioEvaluation, ...]
    metrics: Mapping[str, float]
    veto_codes: tuple[str, ...] = ()
    manifest: BenchmarkRunManifest | None = None
    predictions: tuple[CandidatePrediction, ...] = ()

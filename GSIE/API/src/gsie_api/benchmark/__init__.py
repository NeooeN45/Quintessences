"""Contrat et runner déterministe de GSIE-Bench v0.1.

Le package est volontairement indépendant des modèles IA et ne déclenche
aucune ingestion de données. Les scénarios non qualifiés sont refusés par le
runner.
"""

from .adapters import (
    ENGINE_CONTRACTS,
    EngineBenchmarkAdapter,
    EngineContract,
    engine_contract_catalog,
)
from .baselines import NaiveBaseline, RuleBaseline
from .catalog import build_gold_catalog, build_open_silver_catalog
from .conflicts import build_dendrometry_conflict_catalog
from .metrics import (
    classification_metrics,
    latency_percentiles,
    ranking_metrics,
    relative_degradation,
)
from .models import (
    BenchmarkRunManifest,
    BenchmarkRunResult,
    CandidatePrediction,
    CandidateScenario,
    ReferenceRef,
    RunPolicy,
    ScenarioSpec,
)
from .qualification import ExpertReviewDecision, GoldQualificationResult, assess_gold_qualification
from .reporting import run_result_to_dict
from .runner import DeterministicRunner, QualificationRequiredError, ScenarioIntegrityError

__all__ = [
    "BenchmarkRunResult",
    "BenchmarkRunManifest",
    "CandidatePrediction",
    "CandidateScenario",
    "ENGINE_CONTRACTS",
    "EngineBenchmarkAdapter",
    "EngineContract",
    "DeterministicRunner",
    "NaiveBaseline",
    "QualificationRequiredError",
    "ScenarioIntegrityError",
    "ReferenceRef",
    "RuleBaseline",
    "RunPolicy",
    "ScenarioSpec",
    "build_gold_catalog",
    "build_open_silver_catalog",
    "build_dendrometry_conflict_catalog",
    "ExpertReviewDecision",
    "GoldQualificationResult",
    "assess_gold_qualification",
    "classification_metrics",
    "latency_percentiles",
    "ranking_metrics",
    "relative_degradation",
    "run_result_to_dict",
    "engine_contract_catalog",
]

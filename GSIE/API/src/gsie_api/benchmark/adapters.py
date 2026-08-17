"""Registre des contrats et adaptateur injecté des moteurs GSIE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from .models import CandidatePrediction, CandidateScenario


@dataclass(frozen=True, slots=True)
class EngineContract:
    """Décrit le contrat benchmark d'un moteur sans l'instancier."""

    engine_id: str
    display_name: str
    family: str
    input_contract: str
    output_contract: str
    execution_mode: str


ENGINE_CONTRACTS: tuple[EngineContract, ...] = (
    EngineContract(
        "evidence",
        "Evidence Engine",
        "transverse",
        "RawKnowledgeSubmission",
        "QualifiedKnowledge",
        "sync",
    ),
    EngineContract(
        "knowledge",
        "Knowledge Engine",
        "transverse",
        "KnowledgeQuery",
        "KnowledgeQueryResult",
        "async",
    ),
    EngineContract(
        "correlation",
        "Correlation Engine",
        "transverse",
        "CorrelationComputeRequest",
        "CorrelationResult",
        "async",
    ),
    EngineContract(
        "reasoning", "Reasoning Engine", "chaine", "ReasoningRequest", "InferenceResult", "async"
    ),
    EngineContract(
        "diagnostic", "Diagnostic Engine", "chaine", "DiagnosticRequest", "Diagnostic", "sync"
    ),
    EngineContract(
        "recommendation",
        "Recommendation Engine",
        "chaine",
        "RecommendationRequest",
        "RecommendationSet",
        "async",
    ),
    EngineContract(
        "validation", "Validation Engine", "chaine", "ValidationRequest", "ValidationResult", "sync"
    ),
    EngineContract(
        "gis", "GIS Engine", "domaine", "AltitudeRequest", "StationCharacteristics", "async"
    ),
    EngineContract(
        "climate", "Climate Engine", "domaine", "ClimateQuery", "ObservationClimatique", "async"
    ),
    EngineContract(
        "pedology", "Pedology Engine", "domaine", "PedologyQuery", "PedologyData", "async"
    ),
    EngineContract(
        "botanical", "Botanical Engine", "domaine", "BotanicalQuery", "BotanicalData", "async"
    ),
    EngineContract(
        "forest_dynamics",
        "Forest Dynamics Engine",
        "domaine",
        "DendrometricRequest",
        "DendrometricResult",
        "sync",
    ),
    EngineContract(
        "learning", "Learning Engine", "transverse", "LearningSignal", "LearningOutput", "async"
    ),
    EngineContract(
        "simulation",
        "Simulation Engine",
        "transverse",
        "ScenarioSimulation",
        "SimulationResult",
        "async",
    ),
)

_CONTRACT_BY_ID = {contract.engine_id: contract for contract in ENGINE_CONTRACTS}


def engine_contract_catalog() -> tuple[EngineContract, ...]:
    """Retourne le registre immuable des 14 contrats moteur."""

    return ENGINE_CONTRACTS


class EngineBenchmarkAdapter:
    """Adapte un moteur injecté au contrat candidat GSIE-Bench.

    L'adaptateur n'instancie ni session DB, ni client réseau, ni boucle
    événementielle. Pour un moteur asynchrone, l'appelant fournit explicitement
    un pont déterministe adapté à son environnement de test.
    """

    candidate_kind = "gsie_engine"

    def __init__(
        self,
        engine_id: str,
        predictor: Callable[[CandidateScenario], CandidatePrediction],
        *,
        version: str = "0.1.0",
    ) -> None:
        contract = _CONTRACT_BY_ID.get(engine_id)
        if contract is None:
            raise ValueError(f"Contrat moteur inconnu : {engine_id}")
        if not version:
            raise ValueError("La version du moteur est obligatoire")
        self.contract = contract
        self._predictor = predictor
        self.candidate_id = f"engine.{engine_id}"
        self.candidate_version = version

    def predict(self, scenario: CandidateScenario) -> CandidatePrediction:
        """Exécute uniquement la fonction injectée et vérifie son identité."""

        prediction = self._predictor(scenario)
        if prediction.scenario_id != scenario.scenario_id:
            raise ValueError("Le moteur adapté a retourné un scénario différent")
        return prediction


__all__ = [
    "ENGINE_CONTRACTS",
    "EngineBenchmarkAdapter",
    "EngineContract",
    "engine_contract_catalog",
]

"""Learning Engine — amélioration continue des modèles et calibrations.

Voir `GSIE/ENGINES/LEARNING_ENGINE/LEARNING_ENGINE.md`.

Le moteur est subordonné aux règles expertes (§6) : il propose des
révisions qui doivent être validées, jamais appliquées automatiquement.
L'IA assiste, elle ne décide pas (GSIE-CON-001).
"""

from gsie_api.engines.learning.engine import LearningEngine, LearningEngineError
from gsie_api.engines.learning.schemas import (
    LearningOutput,
    LearningSignal,
    LearningSignalType,
    LearningOutputType,
    LearningStatut,
    PatternEmergent,
    RetourForestier,
)

__all__ = [
    "LearningEngine",
    "LearningEngineError",
    "LearningOutput",
    "LearningOutputType",
    "LearningSignal",
    "LearningSignalType",
    "LearningStatut",
    "PatternEmergent",
    "RetourForestier",
]

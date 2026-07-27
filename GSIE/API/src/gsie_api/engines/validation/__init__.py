"""Validation Engine — contrôle final avant présentation à l'utilisateur.

Voir `GSIE/ENGINES/VALIDATION_ENGINE/VALIDATION_ENGINE.md`.

Le moteur ne produit pas de contenu — il valide et filtre (§6). Il
vérifie la cohérence, la conformité constitutionnelle et la complétude
des diagnostics et recommandations avant leur présentation, en bloquant
toute sortie non conforme.
"""

from gsie_api.engines.validation.engine import ValidationEngine, ValidationEngineError
from gsie_api.engines.validation.schemas import (
    CauseBlocage,
    ControleResultat,
    TypeCauseBlocage,
    ValidationRequest,
    ValidationResult,
    ValidationStatut,
)

__all__ = [
    "CauseBlocage",
    "ControleResultat",
    "TypeCauseBlocage",
    "ValidationEngine",
    "ValidationEngineError",
    "ValidationRequest",
    "ValidationResult",
    "ValidationStatut",
]

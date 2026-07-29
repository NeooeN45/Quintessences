"""Session minimale rendant un diagnostic connu, pour les tests de mapping.

Le Recommendation Engine doit désormais **lire** le diagnostic qu'il invoque :
il citait auparavant `diagnostic_id` dans sa justification sans jamais le
consulter, et un identifiant inexistant produisait un conseil sylvicole
complet, assorti d'une confiance, citant une référence vide.

Les tests qui portent sur le mapping objectif → action n'ont pas besoin d'une
base pour cela. Ce stub leur en évite une.

L'exigence réelle — un diagnostic absent fait refuser — est vérifiée sur
PostgreSQL par `tests/integration/test_recommendation_diagnostic.py`. Sans ce
test-là, le stub masquerait précisément ce qu'il simplifie.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID  # noqa: TC003 — annotation evaluee par SQLAlchemy

from gsie_api.infrastructure.models.diagnostic import DiagnosticModel

__all__ = ["CONFIANCE_DIAGNOSTIC_FICTIF", "SessionDiagnosticFictif"]

CONFIANCE_DIAGNOSTIC_FICTIF = 0.7


class SessionDiagnosticFictif:
    """Rend un `DiagnosticModel` non persisté, quel que soit l'identifiant."""

    def __init__(self, confiance: float = CONFIANCE_DIAGNOSTIC_FICTIF) -> None:
        self._confiance = confiance

    async def get(self, modele: type[Any], identifiant: UUID) -> Any:
        if modele is not DiagnosticModel:
            return None
        return DiagnosticModel(id=identifiant, confiance=self._confiance)

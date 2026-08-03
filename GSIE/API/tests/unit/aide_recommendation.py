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
from gsie_api.infrastructure.models.enums import DiagnosticGlobalState
from gsie_api.infrastructure.models.reasoning import RecommendationModel

__all__ = ["CONFIANCE_DIAGNOSTIC_FICTIF", "SessionDiagnosticFictif"]

CONFIANCE_DIAGNOSTIC_FICTIF = 0.7


class SessionDiagnosticFictif:
    """Rend un `DiagnosticModel` non persisté, quel que soit l'identifiant.

    `etat_global` vaut `sain` par défaut, et non `None` : le moteur lit désormais
    l'état du peuplement, et un état absent n'existe pas en base — la colonne est
    NOT NULL. Un stub qui le laissait vide aurait fait passer les tests par une
    branche impossible en production.

    Le paramètre reste ouvert pour que les tests unitaires exercent aussi l'état
    dégradé, pour lequel le mapping v1 ne propose plus d'intervention.
    """

    def __init__(
        self,
        confiance: float = CONFIANCE_DIAGNOSTIC_FICTIF,
        etat_global: DiagnosticGlobalState = DiagnosticGlobalState.sain,
        recommandation_existe: bool = True,
    ) -> None:
        self._confiance = confiance
        self._etat_global = etat_global
        self._recommandation_existe = recommandation_existe

    async def get(self, modele: type[Any], identifiant: UUID) -> Any:
        if modele is DiagnosticModel:
            return DiagnosticModel(
                id=identifiant,
                confiance=self._confiance,
                etat_global=self._etat_global,
            )
        if modele is RecommendationModel:
            # `recommandation_existe=False` permet d'exercer le refus sans base.
            if not self._recommandation_existe:
                return None
            return RecommendationModel(id=identifiant, confidence=self._confiance)
        # Tout autre modele est absent : c'est ce qui fait materialiser les
        # Agents, comme sur une base vierge.
        return None

    # --- Ecritures avalees : la persistance se verifie sur PostgreSQL ---
    #
    # `recommend` persiste desormais ce qu'il produit. Ces trois methodes
    # acceptent l'ecriture sans rien conserver, pour que les tests de mapping
    # objectif -> action restent sans base.
    #
    # Elles rendent donc la persistance **invisible** ici : c'est
    # `tests/integration/test_recommendation_persistance.py` qui l'etablit, sur
    # une base reelle avec ses cles etrangeres. Sans ce test-la, ce stub
    # masquerait exactement ce qu'il simplifie — l'erreur deja commise dans ce
    # depot, ou des tests SQLite laissaient passer des violations de cle que
    # PostgreSQL refusait.

    def add(self, instance: Any) -> None:
        """Accepte l'objet sans le conserver."""

    async def flush(self) -> None:
        """Ne fait rien : aucune contrainte n'est evaluee."""

    async def execute(self, *args: Any, **kwargs: Any) -> None:
        """Avale les insertions dans les tables de jonction."""


class SessionEspion(SessionDiagnosticFictif):
    """Session fictive qui **enregistre** les écritures au lieu de les avaler.

    Utilisée pour tuer les mutations de persistance du Recommendation Engine
    en mode unitaire : le harnais de mutation ne joue que `tests/unit`, et la
    `SessionDiagnosticFictif` de base avale les `add`/`execute` — rendant
    invisibles les suppressions de persistance.

    Cette variante enregistre chaque objet passé à `add` et chaque `insert`
    passé à `execute`, permettant aux tests d'assertionner que les
    recommandations, alternatives et jonctions sont bien écrites.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.ajouts: list[Any] = []
        self.insertions: list[Any] = []

    def add(self, instance: Any) -> None:
        self.ajouts.append(instance)

    async def execute(self, *args: Any, **kwargs: Any) -> None:
        self.insertions.append(args[0] if args else None)

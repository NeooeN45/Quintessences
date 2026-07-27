"""Learning Engine — amélioration continue des modèles et calibrations.

Responsabilité (LEARNING_ENGINE.md §1) : améliorer les modèles et
calibrations de GSIE à partir des données terrain validées et des
retours d'expérience du forestier, en restant subordonné aux règles
expertes et en garantissant l'explicabilité de toute sortie.

Le moteur ne remplace jamais le Knowledge Engine ni le Reasoning
Engine (séparation des responsabilités, §6). Il propose des révisions
qui doivent être validées — jamais appliquées automatiquement.

Périmètre v1 :
- Traitement des `LearningSignal` de type `retour_forestier` et
  `pattern_emergent` (les types `sortie_bloquee` et
  `observation_terrain` nécessitent l'intégration avec Validation
  Engine et un pipeline d'observations terrain, hors v1).
- Détection de patterns de refus répétés sur un contexte donné
  (ex. : hêtre systématiquement refusé en plaine).
- Production de `LearningOutput` de type `proposition_revision`
  avec justification et confiance, jamais validée automatiquement.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from gsie_api.core.logging import get_logger
from gsie_api.engines.learning.schemas import (
    LearningOutput,
    LearningOutputType,
    LearningSignal,
    LearningSignalType,
    LearningStatut,
    RetourForestier,
)

logger = get_logger("gsie_api.learning.engine")

# Seuil minimal d'occurrences pour qu'un pattern de refus soit signalé.
# En dessous, un refus isolé ne justifie pas une proposition de
# révision — ce serait sur-réagir à une préférence individuelle
# (GSIE-CON-001 : le forestier décide).
_SEUIL_PATTERN_REFUS = 5


class LearningEngineError(Exception):
    """Erreur de base du Learning Engine."""


class LearningEngine:
    """Moteur d'apprentissage — stateless en v1.

    Le moteur ne persiste pas directement les propositions : il les
    retourne à l'appelant, qui les transmet au Knowledge Engine pour
    validation. Une future version pourra persister les propositions
    pour audit (§6 — propositions rejetées archivées).
    """

    # Cache en mémoire des signaux accumulés par contexte station.
    # En v1, ce cache est par-instance (non persistant). Une version
    # future utilisera une table dédiée pour accumuler les signaux
    # across-restarts.
    _signaux_accumules: dict[UUID, list[RetourForestier]]

    def __init__(self) -> None:
        self._signaux_accumules = {}

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    async def process(self, signal: LearningSignal) -> LearningOutput | None:
        """Traite un signal d'apprentissage.

        Retourne un `LearningOutput` si le signal déclenche une
        proposition de révision, ou `None` si le signal est accumulé
        sans déclencher de proposition (pattern en cours de
        constitution, signal isolé).

        Raises:
            LearningEngineError: si le type de signal n'est pas géré en v1.
        """
        if signal.type == LearningSignalType.retour_forestier:
            return await self._traiter_retour_forestier(signal)
        if signal.type == LearningSignalType.pattern_emergent:
            return await self._traiter_pattern_emergent(signal)
        if signal.type in (LearningSignalType.sortie_bloquee, LearningSignalType.observation_terrain):
            raise LearningEngineError(
                f"Type de signal '{signal.type.value}' non géré en v1 — "
                "nécessite l'intégration avec Validation/Observations Engine."
            )
        raise LearningEngineError(f"Type de signal inconnu : {signal.type}")

    async def _traiter_retour_forestier(
        self, signal: LearningSignal
    ) -> LearningOutput | None:
        """Traite un retour forestier et détecte les patterns de refus.

        Accumule les retours par contexte station. Quand le nombre de
        refus pour une même recommandation dépasse le seuil, produit
        une proposition de révision du niveau de confiance.
        """
        try:
            retour = RetourForestier(**signal.contenu)
        except Exception as exc:
            raise LearningEngineError(f"Contenu de retour_forestier invalide : {exc}") from exc

        contexte = retour.contexte_station
        self._signaux_accumules.setdefault(contexte, []).append(retour)

        refus = [r for r in self._signaux_accumules[contexte] if r.decision == "refuse"]
        if len(refus) < _SEUIL_PATTERN_REFUS:
            logger.info(
                "learning_retour_accumule",
                contexte=str(contexte),
                n_refus=len(refus),
                seuil=_SEUIL_PATTERN_REFUS,
            )
            return None

        # Pattern détecté : proposer une révision du niveau de confiance
        justification = [
            f"{len(refus)} refus accumulés sur le contexte {contexte}",
            f"Seuil de détection : {_SEUIL_PATTERN_REFUS} refus minimum",
            "Proposition de révision du niveau de confiance — à valider par le Knowledge Engine.",
        ]
        confidence = min(0.5 + 0.1 * (len(refus) - _SEUIL_PATTERN_REFUS), 0.95)

        logger.info(
            "learning_pattern_refus_detecte",
            contexte=str(contexte),
            n_refus=len(refus),
            confidence=confidence,
        )

        return LearningOutput(
            output_id=uuid4(),
            type=LearningOutputType.proposition_revision,
            description=(
                f"Révision du niveau de confiance pour le contexte "
                f"{contexte} — {len(refus)} refus accumulés"
            ),
            justification=justification,
            confidence=confidence,
            connaissances_concernees=[retour.recommandation_id],
            date_output=datetime.now(UTC),
            statut=LearningStatut.propose,
        )

    async def _traiter_pattern_emergent(
        self, signal: LearningSignal
    ) -> LearningOutput | None:
        """Traite un pattern émergent détecté par le Correlation Engine.

        Produit une proposition de `pattern_confirme` si la confiance
        du pattern émergent est suffisante (>= 0.7). En dessous, le
        pattern est jugé trop faible pour une proposition.
        """
        contenu = signal.contenu
        confiance = contenu.get("confiance", 0.0)
        description = contenu.get("description", "")

        if confiance < 0.7:
            logger.info(
                "learning_pattern_faible_ignore",
                confiance=confiance,
                description=description[:200],
            )
            return None

        justification = [
            f"Pattern émergent détecté : {description}",
            f"Confiance du pattern : {confiance:.2f}",
            "Proposition de confirmation — à valider par le Knowledge Engine.",
        ]

        logger.info(
            "learning_pattern_confirme_propose",
            confiance=confiance,
            description=description[:200],
        )

        return LearningOutput(
            output_id=uuid4(),
            type=LearningOutputType.pattern_confirme,
            description=f"Pattern confirmé : {description[:500]}",
            justification=justification,
            confidence=confiance,
            date_output=datetime.now(UTC),
            statut=LearningStatut.propose,
        )

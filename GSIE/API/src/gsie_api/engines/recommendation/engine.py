"""Recommendation Engine — propositions sylvicoles justifiées et contournables.

Responsabilité (RECOMMENDATION_ENGINE.md §1) : produire des
recommandations sylvicoles contournables à partir des diagnostics et
des simulations, en proposant systématiquement des alternatives
justifiées et en documentant les refus du forestier.

Garanties encodées (§6) :
- Toute recommandation est contournable (GSIE-CON-001) — encodé dans
  le schéma `Recommendation.contournable` (computed_field, toujours
  vrai).
- Plusieurs alternatives sont systématiquement proposées (principe
  fondateur) — le moteur produit au moins une alternative quand
  `alternatives_demandees=True`.
- Chaque recommandation est justifiée par le diagnostic, les
  connaissances et les règles sous-jacentes (GSIE-CON-004).
- Aucune recommandation n'est étiquetée comme « décision »
  (GSIE-CON-001) — le vocabulaire de la décision appartient à
  `ForestierDecision`.

Périmètre v1 :
- Génération de recommandations à partir d'un diagnostic **lu en base**.
  Le moteur ne reconstitue pas le raisonnement du diagnostic, mais il
  refuse d'en invoquer un qui n'existe pas : il citait auparavant
  `diagnostic_id` dans sa justification sans jamais le consulter, et un
  identifiant inexistant produisait un conseil sylvicole complet — type
  d'action, prélèvement chiffré, confiance — dont la référence ne
  renvoyait à rien. La confiance annoncée est celle du diagnostic, jamais
  un nombre propre au moteur.
- Les règles sylvicoles sont encodées sous forme de règles
  déclaratives simples en v1. Une future version les récupérera du
  Knowledge Engine.
- Pas de persistance en v1 — les recommandations sont retournées à
  l'appelant. Une future version les persistera pour traçabilité
  et alimentation du Learning Engine (§3 — retours d'expérience).
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.engines.evidence.schemas import SourceReference, SourceType
from gsie_api.engines.recommendation.schemas import (
    ForestierDecision,
    JustificationRecommandation,
    ObjectifForestier,
    Recommendation,
    RecommendationRequest,
    RecommendationSet,
    TypeAction,
)
from gsie_api.infrastructure.models.diagnostic import DiagnosticModel

logger = get_logger("gsie_api.recommendation.engine")

# Source abstraite pour les règles sylvicoles en v1.
# Une future version référencera le Knowledge Engine réel.
_V1_SOURCE_REGLES = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="GSIE Knowledge Engine (v1 — règles déclaratives)",
    reference="KNOWLEDGE_ENGINE.md §5 — règles sylvicoles",
    version_source="0.1.0",
)


class RecommendationEngineError(Exception):
    """Erreur de base du Recommendation Engine."""


class DiagnosticIntrouvableError(RecommendationEngineError):
    """La recommandation invoque un diagnostic qui n'existe pas.

    Refuser est le seul comportement acceptable. Une recommandation qui cite
    un diagnostic jamais consulte porte une justification decorative : le
    forestier lit une reference verifiable en apparence, qui ne renvoie a
    rien (`GSIE-CON-004`, `ADR-009`).
    """


class RecommendationEngine:
    """Moteur de recommandation — lit le diagnostic, n'écrit rien en v1.

    Le moteur ne persiste pas les recommandations en v1 : chaque
    requête est indépendante. Une future version persistera les
    recommandations et les décisions du forestier pour traçabilité
    et alimentation du Learning Engine (§3).

    Il **lit** en revanche le diagnostic invoqué : c'est ce qui rend sa
    justification vérifiable, et ce qui borne sa confiance à celle du
    diagnostic. D'où la session en dépendance de construction.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.2.0"

    async def _diagnostic(self, diagnostic_id: UUID) -> DiagnosticModel:
        """Charge le diagnostic invoque, ou refuse.

        Le moteur etait sans etat : il citait `diagnostic_id` dans sa
        justification sans jamais lire le diagnostic correspondant. Un
        identifiant inexistant produisait donc un conseil sylvicole complet,
        assorti d'une confiance, citant une reference vide.
        """
        diagnostic = await self._session.get(DiagnosticModel, diagnostic_id)
        if diagnostic is None:
            raise DiagnosticIntrouvableError(
                f"diagnostic {diagnostic_id} introuvable : une recommandation ne "
                "peut pas se justifier par un diagnostic qui n'existe pas"
            )
        return diagnostic

    async def recommend(self, request: RecommendationRequest) -> RecommendationSet:
        """Génère un ensemble de recommandations à partir d'un diagnostic.

        La confiance annoncée est **celle du diagnostic**, jamais un nombre
        propre au moteur : une recommandation ne peut pas être plus assurée que
        le diagnostic sur lequel elle repose. Le Diagnostic Engine pose déjà la
        règle — « le moteur n'invente aucune table de conversion » (`ADR-009`).

        Raises:
            DiagnosticIntrouvableError: si le diagnostic invoqué n'existe pas.
        """
        diagnostic = await self._diagnostic(request.diagnostic_id)
        confiance = float(diagnostic.confiance)
        recommandations: list[Recommendation] = []

        # Recommandation principale — dérivée de l'objectif forestier.
        # En v1, la logique est déclarative et simple. Une future version
        # l'enrichira via Knowledge Engine + Forest Dynamics Engine.
        principale = self._generer_recommandation_principale(request, confiance)
        recommandations.append(principale)

        # Alternatives — systématiquement proposées si demandées
        if request.alternatives_demandees:
            alternatives = self._generer_alternatives(request, principale, confiance)
            principale_avec_alts = principale.model_copy(update={"alternatives": alternatives})
            recommandations[0] = principale_avec_alts

        # Recommandation de fallback — attente/surveillance si aucune
        # action fondée n'est possible. Le contrat §5 interdit un
        # ensemble vide : l'absence d'action se dit par
        # `attente_surveillance`.
        if not recommandations:
            recommandations.append(self._generer_attente_surveillance(request, confiance))

        logger.info(
            "recommendation_complete",
            requete_id=str(request.requete_id),
            objectif=request.objectif_forestier.value,
            n_recommandations=len(recommandations),
            n_alternatives=len(recommandations[0].alternatives) if recommandations else 0,
        )

        return RecommendationSet(
            ensemble_id=uuid4(),
            requete_origine=request.requete_id,
            diagnostic_source=request.diagnostic_id,
            recommandations=recommandations,
            date_generation=datetime.now(UTC),
        )

    async def record_decision(self, decision: ForestierDecision) -> dict[str, Any]:
        """Reçoit la décision du forestier sans encore la persister.

        Le statut retourné était `enregistre` alors que la méthode ne persiste
        rien : le forestier qui refuse une recommandation lisait un accusé de
        conservation pour une trace qui n'existait que dans une ligne de log.
        `GSIE-CON-005` exige la traçabilité, et « aucune décision perdue » n'est
        pas satisfait par un message qui l'affirme.

        Tant que la persistance n'est pas là, le statut le dit —
        `recu_non_persiste` — plutôt que de laisser croire l'inverse. Le champ
        `avertissement` porte la conséquence en clair, car un code de statut se
        lit rarement.

        Une future version persistera la décision pour traçabilité
        (`GSIE-CON-005`) et alimentation du Learning Engine (§3) ; ce statut
        deviendra alors `enregistre`, et il sera vrai.

        Raises:
            RecommendationEngineError: si la décision est invalide.
        """
        logger.info(
            "recommendation_decision_received_not_persisted",
            recommandation_id=str(decision.recommandation_id),
            decision=decision.decision.value,
        )
        return {
            "recommandation_id": str(decision.recommandation_id),
            "decision": decision.decision.value,
            "date_decision": decision.date_decision.isoformat(),
            "statut": "recu_non_persiste",
            "avertissement": (
                "Décision reçue et validée, non conservée : la persistance des "
                "décisions n'est pas implémentée en v1. Conservez votre trace "
                "hors GSIE."
            ),
        }

    # --- Génération des recommandations ---

    def _generer_recommandation_principale(
        self, request: RecommendationRequest, confiance: float
    ) -> Recommendation:
        """Génère la recommandation principale selon l'objectif forestier.

        Logique v1 : mapping déclaratif objectif → type d'action.
        Une future version utilisera le diagnostic réel et les règles
        du Knowledge Engine.
        """
        # L'essence est facultative : seul le reboisement en désigne une. Le
        # type le dit explicitement — `essence_concernee` est `str | None` dans
        # le schéma de sortie, et proposer une essence par défaut ailleurs
        # serait une invention (GSIE-CON-002).
        mapping_objectif: dict[ObjectifForestier, tuple[TypeAction, str, str | None]] = {
            ObjectifForestier.REBOISEMENT: (
                TypeAction.PLANTATION,
                "Planter une essence adaptée à la station, densité 1100 t/ha.",
                "chêne sessile",
            ),
            ObjectifForestier.PRODUCTION: (
                TypeAction.ECLAIRCIE,
                "Éclaircie modérée (prélèvement 25 %) pour favoriser la croissance.",
                None,
            ),
            ObjectifForestier.PROTECTION: (
                TypeAction.PROTECTION,
                "Mettre en place une protection des peuplements contre les dégâts.",
                None,
            ),
            ObjectifForestier.BIODIVERSITE: (
                TypeAction.REGENERATION,
                "Favoriser la régénération naturelle et le mélange d'essences.",
                None,
            ),
            ObjectifForestier.MIXTE: (
                TypeAction.ECLAIRCIE,
                "Éclaircie sélective favorisant le mélange production/biodiversité.",
                None,
            ),
        }

        type_action, description, essence = mapping_objectif.get(
            request.objectif_forestier,
            (TypeAction.ATTENTE_SURVEILLANCE, "Aucune action fondée — observer.", None),
        )

        justification = JustificationRecommandation(
            diagnostic_ref=request.diagnostic_id,
            connaissances_utilisees=[],  # En v1, vide — future version : Knowledge Engine
            regles_appliquees=[f"Règle v1 : objectif={request.objectif_forestier.value}"],
            sources=[_V1_SOURCE_REGLES],
            facteurs_limitants=[
                "Modèle v1 déclaratif — pas de diagnostic réel exploité.",
                "Les règles sylvicoles sont abstraites en v1.",
            ],
            moteurs_solicites=["recommendation"],
        )

        return Recommendation(
            recommandation_id=uuid4(),
            type_action=type_action,
            description=description,
            essence_concernee=essence,
            parametres=(
                {"densite": "1100", "unite": "t/ha"} if type_action == TypeAction.PLANTATION else {}
            ),
            justification=justification,
            niveau_confiance=confiance,
        )

    def _generer_alternatives(
        self, request: RecommendationRequest, principale: Recommendation, confiance: float
    ) -> list[Recommendation]:
        """Génère des alternatives à la recommandation principale.

        En v1, deux alternatives sont générées systématiquement :
        - Une alternative conservatrice (attente/surveillance) ;
        - Une alternative plus interventionniste (si applicable).
        """
        alternatives: list[Recommendation] = []

        # Alternative 1 — attente/surveillance (toujours disponible)
        alt_attente = Recommendation(
            recommandation_id=uuid4(),
            type_action=TypeAction.ATTENTE_SURVEILLANCE,
            description=(
                "Surveiller l'évolution du peuplement avant intervention — "
                "recommandé si les données sont insuffisantes."
            ),
            justification=JustificationRecommandation(
                diagnostic_ref=request.diagnostic_id,
                regles_appliquees=["Règle v1 : alternative conservatrice"],
                sources=[_V1_SOURCE_REGLES],
                facteurs_limitants=[
                    "L'attente prolongée peut laisser évoluer défavorablement le peuplement.",
                ],
                moteurs_solicites=["recommendation"],
            ),
            niveau_confiance=confiance,
        )
        alternatives.append(alt_attente)

        # Alternative 2 — intervention plus marquée (si la principale n'est pas déjà attente)
        if principale.type_action != TypeAction.ATTENTE_SURVEILLANCE:
            alt_forte = Recommendation(
                recommandation_id=uuid4(),
                type_action=principale.type_action,
                description=(
                    f"Version renforcée : {principale.description.lower()} "
                    "avec intensité accrue."
                ),
                justification=JustificationRecommandation(
                    diagnostic_ref=request.diagnostic_id,
                    regles_appliquees=["Règle v1 : alternative interventionniste"],
                    sources=[_V1_SOURCE_REGLES],
                    facteurs_limitants=[
                        "Intensité accrue — risque de déstabilisation du peuplement.",
                    ],
                    moteurs_solicites=["recommendation"],
                ),
                niveau_confiance=confiance,
            )
            alternatives.append(alt_forte)

        return alternatives

    def _generer_attente_surveillance(
        self, request: RecommendationRequest, confiance: float
    ) -> Recommendation:
        """Génère une recommandation d'attente/surveillance (fallback).

        Le contrat §5 interdit un ensemble vide : si aucune action
        fondée n'est possible, `attente_surveillance` est un conseil
        honnête, pas une absence de réponse.
        """
        return Recommendation(
            recommandation_id=uuid4(),
            type_action=TypeAction.ATTENTE_SURVEILLANCE,
            description=(
                "Les connaissances disponibles ne permettent pas de proposer "
                "une intervention fondée. Surveiller et réévaluer."
            ),
            justification=JustificationRecommandation(
                diagnostic_ref=request.diagnostic_id,
                regles_appliquees=["Règle v1 : fallback — données insuffisantes"],
                sources=[_V1_SOURCE_REGLES],
                facteurs_limitants=[
                    "L'attente prolongée sans réévaluation régulière est un risque.",
                ],
                moteurs_solicites=["recommendation"],
            ),
            niveau_confiance=confiance,
        )

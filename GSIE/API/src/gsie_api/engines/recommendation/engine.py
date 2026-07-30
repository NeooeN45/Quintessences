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
- Les recommandations **et** les décisions du forestier sont persistées.
  Le métamodèle le prévoyait depuis l'origine — types `recommendation` et
  `decision` (`ADR-002`), jonction `decision_recommendation` — sans qu'aucun
  code l'emprunte : `record_decision` répondait « enregistré » en n'écrivant
  rien. `GSIE-CON-005` exige la traçabilité, et « aucune décision perdue »
  n'est pas satisfait par un message qui l'affirme.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4, uuid5

from sqlalchemy import insert
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
from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.infrastructure.models.diagnostic import DiagnosticModel
from gsie_api.infrastructure.models.enums import AgentType, DiagnosticGlobalState
from gsie_api.infrastructure.models.junctions import decision_recommendation
from gsie_api.infrastructure.models.prov import AgentModel
from gsie_api.infrastructure.models.reasoning import DecisionModel, RecommendationModel

logger = get_logger("gsie_api.recommendation.engine")

# Espace de noms des identifiants d'agents derives. Fixe : la trace d'une
# decision doit rester relisible d'une execution a l'autre.
_NAMESPACE_AGENTS = UUID("6f1d2a3b-4c5d-6e7f-8a9b-0c1d2e3f4a5b")

# Source abstraite pour les règles sylvicoles en v1.
# Une future version référencera le Knowledge Engine réel.
_V1_SOURCE_REGLES = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="GSIE Knowledge Engine (v1 — règles déclaratives)",
    reference="KNOWLEDGE_ENGINE.md §5 — règles sylvicoles",
    version_source="0.1.0",
)


# États de peuplement que le mapping objectif → action de la v1 ne couvre pas.
#
# Ce mapping dérive l'action du seul objectif forestier ; il présuppose donc un
# peuplement dont l'état permet l'intervention. Sur un peuplement dépérissant ou
# critique, le présupposé est faux et l'action proposée ne repose sur rien.
#
# `vigueur_reduite` n'y figure pas volontairement : une éclaircie sanitaire sur
# un peuplement de vigueur réduite est une intervention sylvicole réelle, et
# l'exclure supposerait un seuil que ce moteur n'a pas le droit de fixer
# (`ADR-009`). Ce cas reste au forestier, qui dispose du diagnostic.
#
# Élargir cet ensemble, ou proposer une intervention pour ces états, suppose une
# règle sourcée passant par le Knowledge Engine — jamais un ajout ici.
_ETATS_HORS_MAPPING_V1: frozenset[DiagnosticGlobalState] = frozenset(
    {
        DiagnosticGlobalState.deperissement,
        DiagnosticGlobalState.critique,
    }
)


class RecommendationEngineError(Exception):
    """Erreur de base du Recommendation Engine."""


class RecommandationIntrouvableError(RecommendationEngineError):
    """La décision répond à une recommandation qui n'existe pas.

    Refuser vaut mieux qu'enregistrer : une décision citant une recommandation
    introuvable produirait une trace inexploitable — on saurait qu'un forestier
    a refusé quelque chose, sans pouvoir dire quoi (`GSIE-CON-005`).
    """


def _rationale(decision: ForestierDecision) -> str:
    """Motif à consigner, sans jamais en inventer un.

    `decision.rationale` est NOT NULL en base, alors que
    `ForestierDecision.justification_forestier` est **délibérément facultatif** :
    « exiger une explication du forestier reviendrait à lui demander de se
    justifier devant l'outil ».

    Les deux exigences se concilient en consignant un fait, pas une raison :
    l'absence de justification est enregistrée comme telle. Écrire une
    explication plausible à la place serait exactement l'invention que `ADR-009`
    interdit — et elle serait relue comme la parole du forestier.

    Les modifications déclarées sont reprises telles quelles : c'est le forestier
    qui les a formulées.
    """
    morceaux: list[str] = []
    if decision.justification_forestier:
        morceaux.append(decision.justification_forestier)
    else:
        morceaux.append(
            "Aucune justification fournie par le forestier — non exigée " "(GSIE-CON-001)."
        )
    if decision.modifications:
        details = "; ".join(
            f"{cle} = {valeur}" for cle, valeur in sorted(decision.modifications.items())
        )
        morceaux.append(f"Modifications déclarées : {details}.")
    return " ".join(morceaux)


class DiagnosticIntrouvableError(RecommendationEngineError):
    """La recommandation invoque un diagnostic qui n'existe pas.

    Refuser est le seul comportement acceptable. Une recommandation qui cite
    un diagnostic jamais consulte porte une justification decorative : le
    forestier lit une reference verifiable en apparence, qui ne renvoie a
    rien (`GSIE-CON-004`, `ADR-009`).
    """


class RecommendationEngine:
    """Moteur de recommandation — lit le diagnostic, écrit la trace.

    Il **lit** le diagnostic invoqué : c'est ce qui rend sa justification
    vérifiable, et ce qui borne sa confiance à celle du diagnostic. Il **écrit**
    les recommandations produites et la décision du forestier : sans elles, la
    suite donnée à un conseil sylvicole ne se relit pas, et le Learning Engine
    n'a rien à apprendre (§3).

    D'où la session en dépendance de construction.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.3.0"

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

        L'**état du peuplement** est également lu. Il ne l'était pas : le moteur
        dérivait l'action du seul objectif forestier, si bien qu'un peuplement
        diagnostiqué `critique` recevait mot pour mot le conseil du peuplement
        sain — « éclaircie modérée, prélèvement 25 % ». Vérifié, reproduit.

        Le moteur n'arbitre pas pour autant quelle intervention convient à un
        peuplement dégradé : ce serait une table de conversion inventée, donc
        interdite (`ADR-009`). Il constate que son mapping v1 ne couvre pas le
        cas et le dit — `attente_surveillance`, dont `TypeAction` précise qu'elle
        est « un conseil honnête, pas une absence de réponse ». Le forestier
        garde la décision (`GSIE-CON-001`), avec le motif sous les yeux.

        Raises:
            DiagnosticIntrouvableError: si le diagnostic invoqué n'existe pas.
        """
        diagnostic = await self._diagnostic(request.diagnostic_id)
        confiance = float(diagnostic.confiance)
        recommandations: list[Recommendation] = []

        if diagnostic.etat_global in _ETATS_HORS_MAPPING_V1:
            # Aucune regle sourcee ne couvre ce cas : le moteur le declare
            # plutot que d'appliquer le mapping objectif -> action, qui
            # presuppose un peuplement en etat d'etre exploite.
            logger.info(
                "recommendation_etat_hors_mapping",
                requete_id=str(request.requete_id),
                etat_global=diagnostic.etat_global.value,
            )
            recommandations.append(
                self._generer_attente_surveillance(request, confiance, diagnostic.etat_global)
            )
        else:
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

        # Persistance : une decision du forestier doit pouvoir citer la
        # recommandation a laquelle elle repond. `decision_recommendation`
        # porte une cle etrangere vers `resource(id)` — sans la ligne
        # `recommendation`, la trace de la decision est impossible a etablir.
        await self._persister_recommandations(recommandations)

        logger.info(
            "recommendation_complete",
            requete_id=str(request.requete_id),
            objectif=request.objectif_forestier.value,
            etat_global=diagnostic.etat_global.value,
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

    async def record_decision(
        self, decision: ForestierDecision, *, forestier_id: UUID | None = None
    ) -> dict[str, Any]:
        """Enregistre la décision du forestier — et le statut dit vrai.

        Le statut valait `enregistre` alors que rien n'était persisté : le
        forestier qui refuse une recommandation lisait un accusé de conservation
        pour une trace n'existant que dans une ligne de log. Il a valu
        `recu_non_persiste` le temps que la persistance arrive. Elle est là :
        `GSIE-CON-005` exige la traçabilité, et « aucune décision perdue » n'est
        pas satisfait par un message qui l'affirme.

        Le métamodèle prévoyait cette écriture depuis l'origine — type
        `decision` (`ADR-002`) et table de jonction `decision_recommendation` —
        sans qu'aucun code l'emprunte. Rien n'est donc ajouté au métamodèle.

        La recommandation citée doit exister. Enregistrer une décision qui
        répond à une recommandation introuvable produirait une trace
        inexploitable : on saurait qu'un forestier a refusé quelque chose, sans
        pouvoir dire quoi.

        Args:
            decision: la suite donnée par le forestier.
            forestier_id: identité de l'auteur, matérialisée en Agent. `None`
                est accepté et enregistré comme tel — voir
                `_agent_forestier`.

        Raises:
            RecommandationIntrouvableError: si la recommandation citée n'existe pas.
        """
        recommandation = await self._session.get(RecommendationModel, decision.recommandation_id)
        if recommandation is None:
            raise RecommandationIntrouvableError(
                f"recommandation {decision.recommandation_id} introuvable : une "
                "décision qui ne cite aucune recommandation existante ne se "
                "relit pas"
            )

        auteur_id = await self._agent_forestier(forestier_id)
        decision_id = uuid4()
        self._session.add(
            ResourceModel(
                id=decision_id,
                type="decision",
                gsie_id=f"decision:{decision_id}",
            )
        )
        await self._session.flush()
        self._session.add(
            DecisionModel(
                id=decision_id,
                decided_by=auteur_id,
                decision_text=decision.decision.value,
                rationale=_rationale(decision),
                decided_at=decision.date_decision,
            )
        )
        await self._session.flush()
        await self._session.execute(
            insert(decision_recommendation).values(
                decision_id=decision_id,
                recommendation_id=decision.recommandation_id,
            )
        )
        await self._session.flush()

        logger.info(
            "recommendation_decision_persisted",
            decision_id=str(decision_id),
            recommandation_id=str(decision.recommandation_id),
            decision=decision.decision.value,
        )
        return {
            "decision_id": str(decision_id),
            "recommandation_id": str(decision.recommandation_id),
            "decision": decision.decision.value,
            "date_decision": decision.date_decision.isoformat(),
            "statut": "enregistre",
        }

    # --- Persistance ---

    async def _persister_recommandations(self, recommandations: list[Recommendation]) -> None:
        """Écrit chaque recommandation, alternatives comprises.

        Les alternatives sont persistées au même titre que la principale : le
        forestier peut retenir une alternative, et sa décision doit pouvoir la
        citer. N'écrire que la principale rendrait ce choix-là intraçable —
        alors que proposer des alternatives est un principe fondateur.

        Le moteur est l'agent recommandant. Il est matérialisé en Agent de type
        `software`, car `recommendation.recommended_by` est une clé étrangère
        vers `resource(id)` : le métamodèle veut un agent nommé, pas un
        identifiant flottant.
        """
        moteur_id = await self._agent_moteur()
        aplaties = [
            candidate for reco in recommandations for candidate in (reco, *reco.alternatives)
        ]
        for reco in aplaties:
            self._session.add(
                ResourceModel(
                    id=reco.recommandation_id,
                    type="recommendation",
                    gsie_id=f"recommendation:{reco.recommandation_id}",
                )
            )
        await self._session.flush()
        for reco in aplaties:
            self._session.add(
                RecommendationModel(
                    id=reco.recommandation_id,
                    recommended_by=moteur_id,
                    # `type_action` et `description` sont deux informations
                    # distinctes, et `recommendation_text` est la seule colonne
                    # de texte : les perdre l'une ou l'autre rendrait la relecture
                    # ambigue.
                    recommendation_text=f"[{reco.type_action.value}] {reco.description}",
                    confidence=reco.niveau_confiance,
                )
            )
        await self._session.flush()
        logger.info("recommendations_persisted", nombre=len(aplaties))

    async def _agent_moteur(self) -> UUID:
        """Matérialise l'Agent représentant ce moteur, une seule fois.

        Identifiant déterministe (`uuid5`) : deux appels concurrents ne créent
        pas deux agents pour le même moteur, et la trace reste stable d'une
        exécution à l'autre — condition d'une relecture (`GSIE-CON-005`).
        """
        return await self._agent(
            uuid5(_NAMESPACE_AGENTS, "recommendation-engine"),
            nom="GSIE Recommendation Engine",
            type_agent=AgentType.software,
        )

    async def _agent_forestier(self, forestier_id: UUID | None) -> UUID:
        """Matérialise l'Agent du forestier, ou l'agent anonyme déclaré.

        `decision.decided_by` est NOT NULL. Quand l'appelant ne transmet pas
        d'identité, on n'en invente pas : un agent nommé « forestier non
        identifié » l'enregistre pour ce qu'il est. Attribuer la décision à
        quelqu'un serait pire que l'anonymat — la trace désignerait une personne
        qui n'a rien décidé.
        """
        if forestier_id is not None:
            return await self._agent(
                forestier_id, nom=str(forestier_id), type_agent=AgentType.person
            )
        return await self._agent(
            uuid5(_NAMESPACE_AGENTS, "forestier-non-identifie"),
            nom="Forestier non identifié",
            type_agent=AgentType.person,
        )

    async def _agent(self, agent_id: UUID, *, nom: str, type_agent: AgentType) -> UUID:
        """Crée l'Agent et sa ligne `resource` s'ils manquent, puis retourne l'id."""
        if await self._session.get(ResourceModel, agent_id) is not None:
            return agent_id
        self._session.add(ResourceModel(id=agent_id, type="agent", gsie_id=f"agent:{agent_id}"))
        await self._session.flush()
        self._session.add(AgentModel(id=agent_id, name=nom, type=type_agent))
        await self._session.flush()
        return agent_id

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
        self,
        request: RecommendationRequest,
        confiance: float,
        etat_global: DiagnosticGlobalState,
    ) -> Recommendation:
        """Génère une recommandation d'attente/surveillance faute de règle fondée.

        Ce générateur était **inatteignable** : la branche qui l'appelait
        testait `if not recommandations` après y avoir déjà ajouté la
        recommandation principale. Le contrat §5 interdit un ensemble vide, ce
        qui rendait la garde vraie par construction — donc morte.

        Il est désormais appelé sur la condition qui le justifie : un état de
        peuplement que le mapping v1 ne couvre pas. `TypeAction` le dit —
        « lorsque les connaissances disponibles ne permettent pas de proposer
        une intervention, ne rien faire et observer est un conseil honnête, pas
        une absence de réponse ».
        """
        return Recommendation(
            recommandation_id=uuid4(),
            type_action=TypeAction.ATTENTE_SURVEILLANCE,
            description=(
                f"Peuplement diagnostiqué « {etat_global.value} ». Aucune règle "
                "sylvicole sourcée ne couvre ce cas en v1 : le moteur ne propose "
                "pas d'intervention. Surveiller, et faire évaluer le peuplement "
                "par un forestier."
            ),
            justification=JustificationRecommandation(
                diagnostic_ref=request.diagnostic_id,
                regles_appliquees=[
                    f"Aucune : l'état « {etat_global.value} » n'est couvert par le "
                    "mapping objectif → action de la v1"
                ],
                sources=[_V1_SOURCE_REGLES],
                facteurs_limitants=[
                    f"État du peuplement : {etat_global.value}.",
                    "Le mapping v1 dérive l'action du seul objectif forestier. Il "
                    "présuppose un peuplement dont l'état permet l'intervention — "
                    "présupposé faux ici.",
                    "L'attente prolongée sans réévaluation régulière est un risque, "
                    "d'autant plus sur un peuplement dégradé.",
                ],
                moteurs_solicites=["recommendation"],
            ),
            niveau_confiance=confiance,
        )

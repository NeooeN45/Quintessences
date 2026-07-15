"""Pipeline intégré — Evidence → Knowledge.

Chaîne complète de la tranche verticale prioritaire (ROADMAP.md Semaine 4) :
1. Soumission de connaissance brute → Evidence Engine (qualification A-F)
2. Si statut « accepte » → Knowledge Engine (ingestion dans le graphe)
3. Requête sur le graphe → KnowledgeQueryResult
4. Révision possible → versionnement CON-010

Ce module orchestre les deux moteurs sans logique métier supplémentaire :
il respecte la séparation des responsabilités (CON-007) et ne fait que
connecter les sorties de l'un aux entrées de l'autre.

Validation humaine (CON-001) : les connaissances en quarantaine ou refusées
sont retournées à l'appelant pour décision humaine — elles ne sont pas
ingérées automatiquement.
"""

from uuid import UUID

from gsie_api.core.logging import get_logger
from gsie_api.engines.evidence.schemas import (
    KnowledgeStatus,
    QualifiedKnowledge,
    RawKnowledgeSubmission,
)
from gsie_api.engines.evidence.wrapper import evaluate
from gsie_api.engines.knowledge.engine import (
    KnowledgeEngine,
    KnowledgeEngineError,
)
from gsie_api.engines.knowledge.schemas import (
    DomaineScientifique,
    KnowledgeIngestRequest,
    KnowledgeObject,
    KnowledgeQuery,
    KnowledgeQueryResult,
    KnowledgeRevisionRequest,
    KnowledgeType,
)

logger = get_logger("gsie_api.pipeline")


class PipelineResult:
    """Résultat du pipeline Evidence → Knowledge.

    Contient la connaissance qualifiée ET l'objet de connaissance
    (si ingéré). Si la connaissance a été refusée ou mise en quarantaine,
    l'objet n'est pas créé (validation humaine requise — CON-001).
    """

    def __init__(
        self,
        qualified: QualifiedKnowledge,
        knowledge_object: KnowledgeObject | None = None,
        ingested: bool = False,
        reason: str | None = None,
    ) -> None:
        self.qualified = qualified
        self.knowledge_object = knowledge_object
        self.ingested = ingested
        self.reason = reason

    @property
    def status(self) -> str:
        """Statut du pipeline : ingested | quarantined | refused."""
        if self.ingested:
            return "ingested"
        if self.qualified.statut == KnowledgeStatus.quarantine:
            return "quarantined"
        return "refused"


class EvidenceKnowledgePipeline:
    """Pipeline intégré Evidence → Knowledge.

    Orchestre la qualification (Evidence Engine) puis l'ingestion
    (Knowledge Engine) en une seule opération. Les connaissances
    non acceptées sont retournées pour validation humaine.
    """

    def __init__(self, knowledge_engine: KnowledgeEngine) -> None:
        self._knowledge = knowledge_engine

    def process(
        self,
        submission: RawKnowledgeSubmission,
        type_: KnowledgeType,
        titre: str,
        description: str,
        domaine_scientifique: DomaineScientifique,
        mots_cles: list[str] | None = None,
        moteurs_consommateurs: list[str] | None = None,
    ) -> PipelineResult:
        """Traite une soumission de bout en bout : Evidence → Knowledge.

        Args:
            submission: Soumission de connaissance brute (entrée Evidence).
            type_: Type de connaissance (concept, seuil, regle, etc.).
            titre: Titre court descriptif.
            description: Description en français.
            domaine_scientifique: Domaine S-6.
            mots_cles: Mots-clés pour la recherche (optionnel).
            moteurs_consommateurs: Moteurs qui utiliseront cette connaissance.

        Returns:
            PipelineResult avec la connaissance qualifiée et l'objet ingéré
            (si statut « accepte »).
        """
        # Étape 1 : qualification par l'Evidence Engine
        qualified = evaluate(submission)
        logger.info(
            "pipeline_evidence_qualified",
            soumission_id=str(submission.soumission_id),
            evidence_level=qualified.evidence_level.value,
            statut=qualified.statut.value,
        )

        # Étape 2 : ingestion dans le Knowledge Engine si acceptée
        if qualified.statut != KnowledgeStatus.accepte:
            reason = (
                f"Connaissance {qualified.statut.value} par l'Evidence Engine "
                f"(niveau {qualified.evidence_level.value}) — "
                f"validation humaine requise (CON-001)"
            )
            logger.info(
                "pipeline_knowledge_not_ingested",
                statut=qualified.statut.value,
                reason=reason,
            )
            return PipelineResult(
                qualified=qualified,
                ingested=False,
                reason=reason,
            )

        # Construire la requête d'ingestion
        ingest_req = KnowledgeIngestRequest(
            connaissance_id=qualified.connaissance_id,
            contenu_normalise=qualified.contenu_normalise,
            type=type_,
            titre=titre,
            description=description,
            domaine_scientifique=domaine_scientifique,
            evidence_level=qualified.evidence_level,
            source=qualified.source,
            statut=qualified.statut,
            mots_cles=mots_cles or [],
            moteurs_consommateurs=moteurs_consommateurs or [],
            conflits=qualified.conflits,
        )

        try:
            knowledge_obj = self._knowledge.ingest(ingest_req)
            logger.info(
                "pipeline_knowledge_ingested",
                connaissance_id=str(knowledge_obj.connaissance_id),
                version=knowledge_obj.version,
            )
            return PipelineResult(
                qualified=qualified,
                knowledge_object=knowledge_obj,
                ingested=True,
            )
        except KnowledgeEngineError as exc:
            logger.error(
                "pipeline_ingestion_failed",
                error=str(exc),
            )
            return PipelineResult(
                qualified=qualified,
                ingested=False,
                reason=f"Échec d'ingestion : {exc}",
            )

    def query(self, query: KnowledgeQuery) -> KnowledgeQueryResult:
        """Interroge le graphe de connaissances (délègue au Knowledge Engine)."""
        return self._knowledge.query(query)

    def revise(
        self,
        connaissance_id: UUID,
        justification: str,
        nouveau_contenu: dict[str, object] | None = None,
    ) -> KnowledgeObject:
        """Révise une connaissance (délègue au Knowledge Engine, CON-010)."""
        revision = KnowledgeRevisionRequest(
            connaissance_id=connaissance_id,
            justification=justification,
            nouveau_contenu=nouveau_contenu,
        )
        return self._knowledge.revise(revision)

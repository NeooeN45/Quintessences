"""Tests d'intégration — pipeline Evidence → Knowledge (persistance réelle).

Teste la tranche verticale prioritaire : soumission → qualification →
ingestion → requête → révision, contre une base PostgreSQL réelle
(testcontainers, fixture partagée dans tests/conftest.py).

Les tests E2E via l'API HTTP (TestClient) restent dans
tests/unit/test_pipeline.py — ils nécessitent en plus de brancher la
session DB de test sur l'app FastAPI (dependency override), non encore fait.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.evidence.schemas import (
    ContentType,
    EvidenceLevel,
    RawKnowledgeSubmission,
    SourceReference,
    SourceType,
)
from gsie_api.engines.knowledge.engine import KnowledgeEngine
from gsie_api.engines.knowledge.schemas import (
    DomaineScientifique,
    KnowledgeQuery,
    KnowledgeType,
    QueryType,
)
from gsie_api.engines.pipeline import EvidenceKnowledgePipeline, PipelineResult
from tests.conftest import requires_docker

pytestmark = requires_docker


@pytest.fixture
def pipeline(db_session: AsyncSession) -> EvidenceKnowledgePipeline:
    """Pipeline adossé à une session Postgres réelle et vide (isolation)."""
    return EvidenceKnowledgePipeline(KnowledgeEngine(db_session))


def _make_submission(
    source_type: SourceType = SourceType.peer_reviewed,
    content_type: ContentType = ContentType.publication,
) -> RawKnowledgeSubmission:
    """Crée une soumission valide pour les tests du pipeline."""
    return RawKnowledgeSubmission(
        soumission_id=uuid4(),
        type_contenu=content_type,
        contenu={
            "definition": "Réserve utile en eau (RUM)",
            "valeur": "80 mm minimum pour le hêtre",
        },
        source_candidate=SourceReference(
            type_source=source_type,
            auteur="Rameau et al. (2008)",
            date_publication="2008",
            reference="Flore forestière française, tome 1, IDF",
        ),
        date_soumission=datetime.now(UTC),
        soumetteur="test_pipeline",
    )


async def should_ingest_when_evidence_accepts(pipeline: EvidenceKnowledgePipeline):
    """Le pipeline doit ingérer quand l'Evidence Engine accepte (niveau B)."""
    sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
    result = await pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="RUM du hêtre",
        description="Réserve utile en eau minimale pour le hêtre.",
        domaine_scientifique=DomaineScientifique.pedologie,
        mots_cles=["hêtre", "RUM", "eau"],
    )
    assert result.ingested
    assert result.status == "ingested"
    assert result.knowledge_object is not None
    assert result.knowledge_object.version == 1
    assert result.qualified.evidence_level == EvidenceLevel.B


async def should_not_ingest_when_evidence_refuses(pipeline: EvidenceKnowledgePipeline):
    """Le pipeline ne doit pas ingérer quand l'Evidence refuse (niveau F)."""
    sub = _make_submission(SourceType.observation_terrain, ContentType.observation)
    result = await pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="Test refuse",
        description="Description test.",
        domaine_scientifique=DomaineScientifique.pedologie,
    )
    assert not result.ingested
    assert result.status == "refused"
    assert result.knowledge_object is None
    assert result.reason is not None


async def should_not_ingest_when_evidence_quarantines(pipeline: EvidenceKnowledgePipeline):
    """Le pipeline ne doit pas ingérer quand l'Evidence met en quarantaine (D)."""
    sub = _make_submission(SourceType.expert_identifie, ContentType.expert)
    result = await pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="Test quarantine",
        description="Description test.",
        domaine_scientifique=DomaineScientifique.pedologie,
    )
    assert not result.ingested
    assert result.status == "quarantined"
    assert result.knowledge_object is None


async def should_allow_query_after_pipeline_ingest(pipeline: EvidenceKnowledgePipeline):
    """Après ingestion via le pipeline, la requête doit trouver la connaissance."""
    sub = _make_submission(SourceType.referentiel_officiel, ContentType.referentiel)
    await pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="pH optimal du chêne",
        description="Le chêne sessile préfère les sols acides.",
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
        mots_cles=["chêne", "pH"],
    )

    query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_concept)
    result = await pipeline.query(query)
    assert result.total >= 1
    assert result.connaissances[0].titre == "pH optimal du chêne"


async def should_allow_revision_after_pipeline_ingest(pipeline: EvidenceKnowledgePipeline):
    """Après ingestion, la révision doit créer une version 2 (CON-010)."""
    sub = _make_submission(SourceType.referentiel_officiel, ContentType.referentiel)
    result = await pipeline.process(
        sub,
        type_=KnowledgeType.seuil,
        titre="Seuil pH chêne",
        description="pH 4,5-6,5 pour le chêne sessile.",
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
    )
    assert result.ingested
    assert result.knowledge_object is not None

    revised = await pipeline.revise(
        connaissance_id=result.knowledge_object.connaissance_id,
        justification="Nouvelle étude 2028 élargit la gamme à 4,0-7,0",
        nouveau_contenu={"parametre": "pH", "minimum": 4.0, "maximum": 7.0},
    )
    assert revised.version == 2
    assert len(revised.historique) == 1


async def should_preserve_evidence_level_in_knowledge(pipeline: EvidenceKnowledgePipeline):
    """Le niveau de preuve de l'Evidence doit être préservé dans le Knowledge."""
    sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
    result = await pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="Test préservation evidence",
        description="Description test.",
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
    )
    assert result.ingested
    assert result.knowledge_object is not None
    assert result.knowledge_object.evidence_level == result.qualified.evidence_level


async def should_preserve_source_in_knowledge(pipeline: EvidenceKnowledgePipeline):
    """La source de l'Evidence doit être préservée dans le Knowledge."""
    sub = _make_submission()
    result = await pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="Test préservation source",
        description="Description test.",
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
    )
    assert result.ingested
    assert result.knowledge_object is not None
    assert result.knowledge_object.source == result.qualified.source


async def should_return_pipeline_result_type(pipeline: EvidenceKnowledgePipeline):
    """Le pipeline doit retourner un PipelineResult."""
    sub = _make_submission()
    result = await pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="Test type",
        description="Description test.",
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
    )
    assert isinstance(result, PipelineResult)

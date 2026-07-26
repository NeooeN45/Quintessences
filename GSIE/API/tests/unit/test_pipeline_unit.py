"""Tests unitaires — pipeline.py (Evidence -> Knowledge).

Couvre les chemins non testés par tests/integration/test_pipeline.py
(qui nécessite Docker). Ici on mock le KnowledgeEngine pour tester
l'orchestration du pipeline sans DB.

Cibles de couverture :
- process() chemin accepte -> ingest success
- process() chemin accepte -> ingest failure (KnowledgeEngineError)
- process() chemin refuse (early return, pas d'ingest)
- process() chemin quarantine (early return, pas d'ingest)
- query() delegation
- revise() delegation
- PipelineResult.status property (ingested/quarantined/refused)
"""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from gsie_api.engines.evidence.schemas import (
    ContentType,
    EvidenceLevel,
    KnowledgeStatus,
    QualifiedKnowledge,
    RawKnowledgeSubmission,
    SourceReference,
    SourceType,
)
from gsie_api.engines.knowledge.engine import KnowledgeEngineError
from gsie_api.engines.knowledge.schemas import (
    DomaineScientifique,
    KnowledgeObject,
    KnowledgeQuery,
    KnowledgeQueryResult,
    KnowledgeType,
    QueryType,
)
from gsie_api.engines.pipeline import EvidenceKnowledgePipeline, PipelineResult


def _make_submission(
    source_type: SourceType = SourceType.peer_reviewed,
    content_type: ContentType = ContentType.publication,
) -> RawKnowledgeSubmission:
    """Crée une soumission valide (niveau B par défaut)."""
    return RawKnowledgeSubmission(
        soumission_id=uuid4(),
        type_contenu=content_type,
        contenu={"definition": "RUM 80 mm minimum pour le hetre"},
        source_candidate=SourceReference(
            type_source=source_type,
            auteur="Rameau et al. (2008)",
            date_publication="2008",
            reference="Flore forestiere francaise, tome 1, IDF",
        ),
        date_soumission=datetime.now(UTC),
        soumetteur="test_pipeline_unit",
    )


def _make_qualified(
    statut: KnowledgeStatus = KnowledgeStatus.accepte,
    level: EvidenceLevel = EvidenceLevel.B,
) -> QualifiedKnowledge:
    """Crée un QualifiedKnowledge sans passer par evaluate()."""
    return QualifiedKnowledge(
        connaissance_id=uuid4(),
        contenu_normalise={"valeur": "80 mm"},
        evidence_level=level,
        statut=statut,
        version=1,
        date_qualification=datetime.now(UTC),
        source=SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Test",
            reference="doi:10.0000/test",
        ),
        conflits=[],
    )


def _make_knowledge_object(connaissance_id: Any = None) -> KnowledgeObject:
    """Crée un KnowledgeObject de retour simulé du KnowledgeEngine."""
    return KnowledgeObject(
        connaissance_id=connaissance_id or uuid4(),
        type=KnowledgeType.concept,
        titre="RUM du hetre",
        description="Reserve utile en eau minimale pour le hetre.",
        domaine_scientifique=DomaineScientifique.pedologie,
        contenu={"valeur": "80 mm"},
        evidence_level=EvidenceLevel.B,
        source=SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Test",
            reference="doi:10.0000/test",
        ),
        statut=KnowledgeStatus.accepte,
        version=1,
        date_integration=datetime.now(UTC),
        historique=[],
        domaines_validite=[],
        moteurs_consommateurs=[],
        relations=[],
        mots_cles=[],
        conflits=[],
    )


@pytest.fixture
def mock_knowledge_engine() -> MagicMock:
    """Mock du KnowledgeEngine — ingest/query/revise sont des AsyncMock."""
    engine = MagicMock()
    engine.ingest = AsyncMock()
    engine.query = AsyncMock()
    engine.revise = AsyncMock()
    return engine


@pytest.fixture
def pipeline(mock_knowledge_engine: MagicMock) -> EvidenceKnowledgePipeline:
    return EvidenceKnowledgePipeline(mock_knowledge_engine)


class TestProcessAccepted:
    """Chemin accepte -> ingest."""

    async def should_ingest_and_return_knowledge_when_evidence_accepts(
        self,
        pipeline: EvidenceKnowledgePipeline,
        mock_knowledge_engine: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Arrange : force evaluate() a retourner un statut accepte
        qualified = _make_qualified(KnowledgeStatus.accepte, EvidenceLevel.B)
        monkeypatch.setattr(
            "gsie_api.engines.pipeline.evaluate", lambda sub: qualified
        )
        expected_obj = _make_knowledge_object(qualified.connaissance_id)
        mock_knowledge_engine.ingest.return_value = expected_obj

        # Act
        result = await pipeline.process(
            _make_submission(),
            type_=KnowledgeType.concept,
            titre="RUM du hetre",
            description="Reserve utile en eau minimale pour le hetre.",
            domaine_scientifique=DomaineScientifique.pedologie,
        )

        # Assert
        assert result.ingested is True
        assert result.status == "ingested"
        assert result.knowledge_object is expected_obj
        assert result.knowledge_object is not None
        assert result.knowledge_object.version == 1
        mock_knowledge_engine.ingest.assert_awaited_once()

    async def should_return_failure_when_ingest_raises(
        self,
        pipeline: EvidenceKnowledgePipeline,
        mock_knowledge_engine: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Arrange
        qualified = _make_qualified(KnowledgeStatus.accepte, EvidenceLevel.A)
        monkeypatch.setattr(
            "gsie_api.engines.pipeline.evaluate", lambda sub: qualified
        )
        mock_knowledge_engine.ingest.side_effect = KnowledgeEngineError("DB down")

        # Act
        result = await pipeline.process(
            _make_submission(),
            type_=KnowledgeType.seuil,
            titre="Seuil pH chene",
            description="pH 4,5-6,5 pour le chene sessile.",
            domaine_scientifique=DomaineScientifique.ecologie_forestiere,
        )

        # Assert
        assert result.ingested is False
        assert result.status == "refused"
        assert result.knowledge_object is None
        assert result.reason is not None
        assert "DB down" in result.reason


class TestProcessRefused:
    """Chemin refuse -> early return, pas d'appel a ingest."""

    async def should_not_ingest_when_evidence_refuses(
        self,
        pipeline: EvidenceKnowledgePipeline,
        mock_knowledge_engine: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Arrange : observation_terrain -> niveau F -> refuse
        monkeypatch.setattr(
            "gsie_api.engines.pipeline.evaluate",
            lambda sub: _make_qualified(KnowledgeStatus.refuse, EvidenceLevel.F),
        )

        # Act
        result = await pipeline.process(
            _make_submission(SourceType.observation_terrain, ContentType.observation),
            type_=KnowledgeType.concept,
            titre="Test refuse",
            description="Description test.",
            domaine_scientifique=DomaineScientifique.pedologie,
        )

        # Assert
        assert result.ingested is False
        assert result.status == "refused"
        assert result.knowledge_object is None
        assert result.reason is not None
        assert "refuse" in result.reason
        mock_knowledge_engine.ingest.assert_not_awaited()


class TestProcessQuarantine:
    """Chemin quarantine -> early return, pas d'appel a ingest."""

    async def should_not_ingest_when_evidence_quarantines(
        self,
        pipeline: EvidenceKnowledgePipeline,
        mock_knowledge_engine: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Arrange : expert_identifie -> niveau D -> quarantine
        monkeypatch.setattr(
            "gsie_api.engines.pipeline.evaluate",
            lambda sub: _make_qualified(KnowledgeStatus.quarantine, EvidenceLevel.D),
        )

        # Act
        result = await pipeline.process(
            _make_submission(SourceType.expert_identifie, ContentType.expert),
            type_=KnowledgeType.concept,
            titre="Test quarantine",
            description="Description test.",
            domaine_scientifique=DomaineScientifique.pedologie,
        )

        # Assert
        assert result.ingested is False
        assert result.status == "quarantined"
        assert result.knowledge_object is None
        assert result.reason is not None
        assert "quarantine" in result.reason
        mock_knowledge_engine.ingest.assert_not_awaited()


class TestQueryDelegation:
    """query() delegue au KnowledgeEngine."""

    async def should_delegate_query_to_knowledge_engine(
        self,
        pipeline: EvidenceKnowledgePipeline,
        mock_knowledge_engine: MagicMock,
    ) -> None:
        # Arrange
        query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_concept)
        expected = KnowledgeQueryResult(
            requete_id=query.requete_id,
            connaissances=[],
            total=0,
            version_graph="0.2.0",
            page=1,
            page_size=50,
        )
        mock_knowledge_engine.query.return_value = expected

        # Act
        result = await pipeline.query(query)

        # Assert
        assert result is expected
        mock_knowledge_engine.query.assert_awaited_once_with(query)


class TestReviseDelegation:
    """revise() delegue au KnowledgeEngine."""

    async def should_delegate_revise_to_knowledge_engine(
        self,
        pipeline: EvidenceKnowledgePipeline,
        mock_knowledge_engine: MagicMock,
    ) -> None:
        # Arrange
        connaissance_id = uuid4()
        expected = _make_knowledge_object(connaissance_id)
        expected.version = 2
        mock_knowledge_engine.revise.return_value = expected

        # Act
        result = await pipeline.revise(
            connaissance_id=connaissance_id,
            justification="Nouvelle etude 2028 elargit la gamme a 4,0-7,0",
            nouveau_contenu={"parametre": "pH", "minimum": 4.0, "maximum": 7.0},
        )

        # Assert
        assert result is expected
        assert result.version == 2
        mock_knowledge_engine.revise.assert_awaited_once()
        # Verifier que le KnowledgeRevisionRequest passe a revise() porte les bons champs
        call_args = mock_knowledge_engine.revise.call_args
        revision_req = call_args.args[0]
        assert revision_req.connaissance_id == connaissance_id
        assert revision_req.nouveau_contenu == {
            "parametre": "pH",
            "minimum": 4.0,
            "maximum": 7.0,
        }


class TestPipelineResultStatus:
    """PipelineResult.status property."""

    def should_return_ingested_when_ingested_true(self) -> None:
        result = PipelineResult(qualified=_make_qualified(), ingested=True)
        assert result.status == "ingested"

    def should_return_quarantined_when_not_ingested_and_statut_quarantine(self) -> None:
        result = PipelineResult(
            qualified=_make_qualified(KnowledgeStatus.quarantine, EvidenceLevel.D),
            ingested=False,
        )
        assert result.status == "quarantined"

    def should_return_refused_when_not_ingested_and_statut_refuse(self) -> None:
        result = PipelineResult(
            qualified=_make_qualified(KnowledgeStatus.refuse, EvidenceLevel.F),
            ingested=False,
        )
        assert result.status == "refused"

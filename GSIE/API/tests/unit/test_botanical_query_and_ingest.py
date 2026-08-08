"""Tests unitaires — Botanical Engine `query_and_ingest` et `resolve_taxref_and_ingest`.

Couvre le maillon amont Gate 5 (ROADMAP.md) pour les deux connecteurs
référentiels : GBIF (query_and_ingest) et TAXREF (resolve_taxref_and_ingest).
Les deux doivent produire des connaissances `accepte` (evidence_level=B)
car ce sont des référentiels officiels consultés directement.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from gsie_api.engines.botanical.engine import BotanicalEngine
from gsie_api.engines.botanical.schemas import (
    BotanicalData,
    BotanicalQuery,
    EspeceData,
    TaxonStatus,
    TaxrefQuery,
    TaxrefResult,
)
from gsie_api.engines.evidence.schemas import (
    EvidenceLevel,
    KnowledgeStatus,
    QualifiedKnowledge,
    SourceReference,
    SourceType,
)
from gsie_api.engines.pipeline import PipelineResult


def _make_source() -> SourceReference:
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="GBIF",
        reference="https://www.gbif.org/",
    )


def _make_espece(nom: str = "Quercus petraea") -> EspeceData:
    return EspeceData(
        taxon_id=uuid4(),
        gbif_taxon_key=2878689,
        nom_scientifique=nom,
        nom_vernaculaire="Chêne sessile",
        synonymes=[],
        famille="Fagaceae",
        statut=TaxonStatus.accepted,
        source=_make_source(),
    )


def _make_botanical_data(especes: list[EspeceData] | None = None) -> BotanicalData:
    return BotanicalData(
        requete_id=uuid4(),
        especes=especes if especes is not None else [_make_espece()],
        source=_make_source(),
        date_donnees=datetime.now(UTC),
    )


def _make_taxref_result() -> TaxrefResult:
    return TaxrefResult(
        requete_id=uuid4(),
        cd_nom=141066,
        nom_scientifique="Quercus petraea",
        nom_scientifique_complet="Quercus petraea (Matt.) Liebl.",
        nom_vernaculaire="Chêne sessile",
        famille="Fagaceae",
        statut=TaxonStatus.accepted,
        source=_make_source(),
    )


def _make_qualified(statut: KnowledgeStatus = KnowledgeStatus.accepte) -> QualifiedKnowledge:
    return QualifiedKnowledge(
        connaissance_id=uuid4(),
        contenu_normalise={},
        evidence_level=EvidenceLevel.B,
        source=_make_source(),
        version=1,
        date_qualification=datetime.now(UTC),
        statut=statut,
        conflits=[],
    )


def _make_pipeline_result(
    statut: KnowledgeStatus = KnowledgeStatus.accepte,
    with_knowledge_object: bool = True,
) -> PipelineResult:
    from gsie_api.engines.knowledge.schemas import (
        DomaineScientifique,
        KnowledgeObject,
        KnowledgeType,
    )

    qualified = _make_qualified(statut)
    knowledge_object = None
    ingested = False
    if with_knowledge_object and statut == KnowledgeStatus.accepte:
        knowledge_object = KnowledgeObject(
            connaissance_id=qualified.connaissance_id,
            type=KnowledgeType.concept,
            titre="Test",
            description="Test",
            domaine_scientifique=DomaineScientifique.botanique,
            contenu={},
            evidence_level=qualified.evidence_level,
            source=qualified.source,
            statut=qualified.statut,
            version=1,
            date_integration=datetime.now(UTC),
            historique=[],
            domaines_validite=[],
            moteurs_consommateurs=[],
            relations=[],
            mots_cles=[],
            conflits=[],
        )
        ingested = True
    return PipelineResult(
        qualified=qualified,
        knowledge_object=knowledge_object,
        ingested=ingested,
        reason=None if statut == KnowledgeStatus.accepte else "Non accepté",
    )


def _make_engine() -> BotanicalEngine:
    return BotanicalEngine(session=MagicMock())


# ---------------------------------------------------------------------------
# query_and_ingest
# ---------------------------------------------------------------------------


class TestQueryAndIngest:
    """BotanicalEngine.query_and_ingest — maillon amont GBIF → Evidence → Knowledge."""

    async def should_ingest_species_when_gbif_returns_result(self) -> None:
        engine = _make_engine()
        mock_knowledge = MagicMock()
        request = BotanicalQuery(essence="Quercus petraea")
        botanical_data = _make_botanical_data([_make_espece("Quercus petraea")])

        with (
            patch.object(engine, "query", new=AsyncMock(return_value=botanical_data)),
            patch(
                "gsie_api.engines.botanical.engine.EvidenceKnowledgePipeline"
            ) as mock_pipeline_cls,
        ):
            mock_pipeline = mock_pipeline_cls.return_value
            mock_pipeline.process = AsyncMock(
                return_value=_make_pipeline_result(KnowledgeStatus.accepte)
            )

            response = await engine.query_and_ingest(request, mock_knowledge)

        assert response.requete_id == request.requete_id
        assert len(response.resultats) == 1
        assert response.resultats[0].statut == "ingested"
        assert response.resultats[0].evidence_level == EvidenceLevel.B
        assert response.resultats[0].version == 1
        mock_pipeline.process.assert_awaited_once()

    async def should_return_empty_results_when_gbif_finds_nothing(self) -> None:
        engine = _make_engine()
        mock_knowledge = MagicMock()
        request = BotanicalQuery(essence="NonExistent species")

        with (
            patch.object(engine, "query", new=AsyncMock(return_value=_make_botanical_data([]))),
            patch(
                "gsie_api.engines.botanical.engine.EvidenceKnowledgePipeline"
            ) as mock_pipeline_cls,
        ):
            mock_pipeline = mock_pipeline_cls.return_value
            mock_pipeline.process = AsyncMock(
                return_value=_make_pipeline_result(KnowledgeStatus.accepte)
            )

            response = await engine.query_and_ingest(request, mock_knowledge)

        assert response.requete_id == request.requete_id
        assert len(response.resultats) == 0
        mock_pipeline.process.assert_not_awaited()

    async def should_quarantine_species_when_evidence_rejects(self) -> None:
        engine = _make_engine()
        mock_knowledge = MagicMock()
        request = BotanicalQuery(essence="Quercus petraea")

        with (
            patch.object(engine, "query", new=AsyncMock(return_value=_make_botanical_data())),
            patch(
                "gsie_api.engines.botanical.engine.EvidenceKnowledgePipeline"
            ) as mock_pipeline_cls,
        ):
            mock_pipeline = mock_pipeline_cls.return_value
            mock_pipeline.process = AsyncMock(
                return_value=_make_pipeline_result(
                    KnowledgeStatus.quarantine, with_knowledge_object=False
                )
            )

            response = await engine.query_and_ingest(request, mock_knowledge)

        assert len(response.resultats) == 1
        assert response.resultats[0].statut == "quarantined"
        assert response.resultats[0].version is None
        assert response.resultats[0].raison is not None

    async def should_propagate_botanical_error_when_gbif_fails(self) -> None:
        from gsie_api.engines.botanical.engine import BotanicalEngineError

        engine = _make_engine()
        mock_knowledge = MagicMock()
        request = BotanicalQuery(essence="Quercus petraea")

        with (
            patch.object(
                engine, "query", new=AsyncMock(side_effect=BotanicalEngineError("GBIF down"))
            ),
            patch("gsie_api.engines.botanical.engine.EvidenceKnowledgePipeline"),
            pytest.raises(BotanicalEngineError, match="GBIF down"),
        ):
            await engine.query_and_ingest(request, mock_knowledge)


# ---------------------------------------------------------------------------
# resolve_taxref_and_ingest
# ---------------------------------------------------------------------------


class TestResolveTaxrefAndIngest:
    """BotanicalEngine.resolve_taxref_and_ingest — maillon amont TAXREF → Evidence → Knowledge."""

    async def should_ingest_taxref_entry_when_found(self) -> None:
        engine = _make_engine()
        mock_knowledge = MagicMock()
        request = TaxrefQuery(nom_scientifique="Quercus petraea")
        taxref_result = _make_taxref_result()

        with (
            patch.object(engine, "resolve_taxref", new=AsyncMock(return_value=taxref_result)),
            patch(
                "gsie_api.engines.botanical.engine.EvidenceKnowledgePipeline"
            ) as mock_pipeline_cls,
        ):
            mock_pipeline = mock_pipeline_cls.return_value
            mock_pipeline.process = AsyncMock(
                return_value=_make_pipeline_result(KnowledgeStatus.accepte)
            )

            response = await engine.resolve_taxref_and_ingest(request, mock_knowledge)

        assert response.requete_id == request.requete_id
        assert response.resultat is not None
        assert response.resultat.cd_nom == 141066
        assert response.resultat.statut == "ingested"
        assert response.resultat.evidence_level == EvidenceLevel.B
        assert response.resultat.version == 1
        mock_pipeline.process.assert_awaited_once()

    async def should_return_none_when_taxref_not_found(self) -> None:
        engine = _make_engine()
        mock_knowledge = MagicMock()
        request = TaxrefQuery(nom_scientifique="NonExistent species")

        with (
            patch.object(engine, "resolve_taxref", new=AsyncMock(return_value=None)),
            patch(
                "gsie_api.engines.botanical.engine.EvidenceKnowledgePipeline"
            ) as mock_pipeline_cls,
        ):
            mock_pipeline = mock_pipeline_cls.return_value
            mock_pipeline.process = AsyncMock(
                return_value=_make_pipeline_result(KnowledgeStatus.accepte)
            )

            response = await engine.resolve_taxref_and_ingest(request, mock_knowledge)

        assert response.requete_id == request.requete_id
        assert response.resultat is None
        mock_pipeline.process.assert_not_awaited()

    async def should_quarantine_when_evidence_rejects_taxref(self) -> None:
        engine = _make_engine()
        mock_knowledge = MagicMock()
        request = TaxrefQuery(nom_scientifique="Quercus petraea")
        taxref_result = _make_taxref_result()

        with (
            patch.object(engine, "resolve_taxref", new=AsyncMock(return_value=taxref_result)),
            patch(
                "gsie_api.engines.botanical.engine.EvidenceKnowledgePipeline"
            ) as mock_pipeline_cls,
        ):
            mock_pipeline = mock_pipeline_cls.return_value
            mock_pipeline.process = AsyncMock(
                return_value=_make_pipeline_result(
                    KnowledgeStatus.quarantine, with_knowledge_object=False
                )
            )

            response = await engine.resolve_taxref_and_ingest(request, mock_knowledge)

        assert response.resultat is not None
        assert response.resultat.statut == "quarantined"
        assert response.resultat.version is None
        assert response.resultat.raison is not None

    async def should_propagate_botanical_error_when_taxref_fails(self) -> None:
        from gsie_api.engines.botanical.engine import BotanicalEngineError

        engine = _make_engine()
        mock_knowledge = MagicMock()
        request = TaxrefQuery(nom_scientifique="Quercus petraea")

        with (
            patch.object(
                engine,
                "resolve_taxref",
                new=AsyncMock(side_effect=BotanicalEngineError("TAXREF down")),
            ),
            patch("gsie_api.engines.botanical.engine.EvidenceKnowledgePipeline"),
            pytest.raises(BotanicalEngineError, match="TAXREF down"),
        ):
            await engine.resolve_taxref_and_ingest(request, mock_knowledge)

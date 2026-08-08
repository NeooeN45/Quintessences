"""Tests unitaires — Botanical Engine `query_and_ingest`/`resolve_taxref_and_ingest`.

Couvre les connecteurs GBIF → Evidence → Knowledge et TAXREF → Evidence →
Knowledge (Gate 5 — maillon amont). Contrairement à PlantNet, GBIF et
TAXREF sont des référentiels taxonomiques officiels consultés directement
(pas une inférence ML) : ils plafonnent à evidence_level=B et s'ingèrent
automatiquement, comme SoilGrids. Les clients GBIF/TAXREF sont mockés.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from gsie_api.engines.botanical.engine import BotanicalEngine, BotanicalEngineError
from gsie_api.engines.botanical.gbif_client import GBIFClientError
from gsie_api.engines.botanical.schemas import BotanicalQuery, TaxrefQuery
from gsie_api.engines.botanical.taxref_client import TaxrefClientError
from gsie_api.engines.evidence.schemas import (
    EvidenceLevel,
    KnowledgeStatus,
    SourceReference,
    SourceType,
)
from gsie_api.engines.knowledge.engine import KnowledgeEngineError
from gsie_api.engines.knowledge.schemas import DomaineScientifique, KnowledgeObject, KnowledgeType

_GBIF_MATCH = {
    "usageKey": 2878688,
    "canonicalName": "Quercus robur",
    "species": "Quercus robur",
    "scientificName": "Quercus robur L.",
    "status": "ACCEPTED",
    "family": "Fagaceae",
    "confidence": 99,
    "matchType": "EXACT",
}

_TAXREF_RESULT = {
    "taxonID": "135",
    "canonicalName": "Quercus petraea",
    "species": "Quercus petraea",
    "scientificName": "Quercus petraea (Matt.) Liebl.",
    "taxonomicStatus": "ACCEPTED",
    "family": "Fagaceae",
    "vernacularNames": [{"vernacularName": "Chêne sessile", "language": "fra"}],
}


def _session_with_existing_taxon(entity_id: object) -> MagicMock:
    """Session mockée simulant un taxon GBIF déjà persisté (SELECT trouve d'emblée)."""
    scalars_result = MagicMock()
    scalars_result.first.return_value = entity_id
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_result
    session = MagicMock()
    session.execute = AsyncMock(return_value=execute_result)
    return session


def _make_gbif_engine(match: dict | None = _GBIF_MATCH) -> BotanicalEngine:
    gbif_client = MagicMock()
    gbif_client.match_species = AsyncMock(return_value=match)
    gbif_client.get_vernacular_name = AsyncMock(return_value="Chêne pédonculé")
    session = _session_with_existing_taxon(uuid4())
    return BotanicalEngine(session=session, gbif_client=gbif_client)


def _make_taxref_engine(result: dict | None = _TAXREF_RESULT) -> BotanicalEngine:
    taxref_client = MagicMock()
    taxref_client.search = AsyncMock(return_value=result)
    session = MagicMock()
    return BotanicalEngine(session=session, taxref_client=taxref_client)


def _make_knowledge_object(connaissance_id, titre: str) -> KnowledgeObject:
    return KnowledgeObject(
        connaissance_id=connaissance_id,
        type=KnowledgeType.concept,
        titre=titre,
        description=titre,
        domaine_scientifique=DomaineScientifique.botanique,
        contenu={},
        evidence_level=EvidenceLevel.B,
        source=SourceReference(
            type_source=SourceType.referentiel_officiel,
            auteur="GBIF",
            reference="GBIF Backbone Taxonomy",
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
    """Mock du KnowledgeEngine — ingest délègue vers un KnowledgeObject synthétique."""
    engine = MagicMock()

    async def _ingest(request):
        return _make_knowledge_object(request.connaissance_id, request.titre)

    engine.ingest = AsyncMock(side_effect=_ingest)
    return engine


class TestBotanicalEngineQueryAndIngest:
    """Couverture de query_and_ingest (GBIF) — maillon amont Gate 5 (ROADMAP.md)."""

    async def should_ingest_taxon_when_gbif_and_knowledge_succeed(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        engine = _make_gbif_engine()

        response = await engine.query_and_ingest(
            BotanicalQuery(essence="Quercus robur"), mock_knowledge_engine
        )

        assert len(response.resultats) == 1
        resultat = response.resultats[0]
        assert resultat.nom_scientifique == "Quercus robur"
        # GBIF est un referentiel officiel -> referentiel + officiel plafonne
        # a B -> accepte (comme SoilGrids), ingestion automatique.
        assert resultat.statut == "ingested"
        assert resultat.evidence_level == EvidenceLevel.B
        assert resultat.version == 1
        mock_knowledge_engine.ingest.assert_awaited_once()

    async def should_return_empty_resultats_when_gbif_finds_nothing(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        engine = _make_gbif_engine(match=None)

        response = await engine.query_and_ingest(
            BotanicalQuery(essence="Taxon inexistant"), mock_knowledge_engine
        )

        assert response.resultats == []
        mock_knowledge_engine.ingest.assert_not_awaited()

    async def should_raise_botanical_error_when_gbif_fails(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        gbif_client = MagicMock()
        gbif_client.match_species = AsyncMock(side_effect=GBIFClientError("API indisponible"))
        engine = BotanicalEngine(session=MagicMock(), gbif_client=gbif_client)

        with pytest.raises(BotanicalEngineError, match="API indisponible"):
            await engine.query_and_ingest(
                BotanicalQuery(essence="Quercus robur"), mock_knowledge_engine
            )

        mock_knowledge_engine.ingest.assert_not_awaited()

    async def should_report_refused_when_knowledge_engine_ingest_fails(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        engine = _make_gbif_engine()
        mock_knowledge_engine.ingest = AsyncMock(
            side_effect=KnowledgeEngineError("DB indisponible")
        )

        response = await engine.query_and_ingest(
            BotanicalQuery(essence="Quercus robur"), mock_knowledge_engine
        )

        assert len(response.resultats) == 1
        assert response.resultats[0].statut == "refused"
        assert response.resultats[0].version is None
        assert "DB indisponible" in (response.resultats[0].raison or "")


class TestBotanicalEngineResolveTaxrefAndIngest:
    """Couverture de resolve_taxref_and_ingest — maillon amont Gate 5 (ROADMAP.md)."""

    async def should_ingest_entry_when_taxref_and_knowledge_succeed(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        engine = _make_taxref_engine()

        response = await engine.resolve_taxref_and_ingest(
            TaxrefQuery(nom_scientifique="Quercus petraea"), mock_knowledge_engine
        )

        assert response.resultat is not None
        assert response.resultat.cd_nom == 135
        assert response.resultat.nom_scientifique == "Quercus petraea"
        # TAXREF est un referentiel officiel -> plafond B -> accepte.
        assert response.resultat.statut == "ingested"
        assert response.resultat.evidence_level == EvidenceLevel.B
        mock_knowledge_engine.ingest.assert_awaited_once()

    async def should_return_none_when_taxref_finds_nothing(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        engine = _make_taxref_engine(result=None)

        response = await engine.resolve_taxref_and_ingest(
            TaxrefQuery(nom_scientifique="Taxon inexistant"), mock_knowledge_engine
        )

        assert response.resultat is None
        mock_knowledge_engine.ingest.assert_not_awaited()

    async def should_raise_botanical_error_when_taxref_fails(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        taxref_client = MagicMock()
        taxref_client.search = AsyncMock(side_effect=TaxrefClientError("API indisponible"))
        engine = BotanicalEngine(session=MagicMock(), taxref_client=taxref_client)

        with pytest.raises(BotanicalEngineError, match="API indisponible"):
            await engine.resolve_taxref_and_ingest(
                TaxrefQuery(nom_scientifique="Quercus petraea"), mock_knowledge_engine
            )

        mock_knowledge_engine.ingest.assert_not_awaited()

"""Tests unitaires — Pedology Engine (couverture 70% → 100%).

Couvre la méthode `query` qui appelle SoilGridsClient et construit
les caractéristiques du sol. Le client est mocké.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from gsie_api.engines.evidence.schemas import (
    EvidenceLevel,
    KnowledgeStatus,
    SourceReference,
    SourceType,
)
from gsie_api.engines.knowledge.engine import KnowledgeEngineError
from gsie_api.engines.knowledge.schemas import DomaineScientifique, KnowledgeObject, KnowledgeType
from gsie_api.engines.pedology.engine import PedologyEngine, PedologyEngineError
from gsie_api.engines.pedology.schemas import PedologyQuery
from gsie_api.engines.pedology.soilgrids_client import SoilGridsClientError


def _make_query() -> PedologyQuery:
    return PedologyQuery(
        latitude=45.0,
        longitude=0.5,
        profondeur="15",
    )


class TestPedologyEngineQuery:
    """Couverture de la méthode query (lignes 76-103)."""

    async def should_return_caracteristiques_when_soilgrids_succeeds(self) -> None:
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.get_properties = AsyncMock(
            return_value={"phh2o": 5.5, "clay": 30.0, "sand": 40.0, "silt": 30.0}
        )
        mock_client.unit_for = MagicMock(
            side_effect=lambda prop: {
                "phh2o": "pH",
                "clay": "%",
                "sand": "%",
                "silt": "%",
            }.get(prop, "")
        )

        engine = PedologyEngine(soilgrids_client=mock_client)
        result = await engine.query(_make_query())

        assert result.latitude == 45.0
        assert result.longitude == 0.5
        assert len(result.caracteristiques) == 4
        noms = {c.nom for c in result.caracteristiques}
        assert noms == {"ph", "argile_pct", "sable_pct", "limon_pct"}
        assert all(c.evidence_level == EvidenceLevel.B for c in result.caracteristiques)

    async def should_filter_unknown_properties(self) -> None:
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.get_properties = AsyncMock(return_value={"phh2o": 5.5, "unknown_prop": 42.0})
        mock_client.unit_for = MagicMock(return_value="unit")

        engine = PedologyEngine(soilgrids_client=mock_client)
        result = await engine.query(_make_query())

        # unknown_prop n'est pas dans _PROPERTY_LABELS → filtré
        assert len(result.caracteristiques) == 1
        assert result.caracteristiques[0].nom == "ph"

    async def should_return_empty_caracteristiques_when_no_data(self) -> None:
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.get_properties = AsyncMock(return_value={})
        mock_client.unit_for = MagicMock(return_value="unit")

        engine = PedologyEngine(soilgrids_client=mock_client)
        result = await engine.query(_make_query())

        assert len(result.caracteristiques) == 0

    async def should_raise_pedology_error_when_soilgrids_fails(self) -> None:
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.get_properties = AsyncMock(side_effect=SoilGridsClientError("API indisponible"))

        engine = PedologyEngine(soilgrids_client=mock_client)
        with pytest.raises(PedologyEngineError, match="API indisponible"):
            await engine.query(_make_query())

    def should_return_version_0_1_0(self) -> None:
        assert PedologyEngine.version() == "0.1.0"


def _make_soilgrids_engine() -> PedologyEngine:
    """PedologyEngine avec un client SoilGrids mocké (4 propriétés standard)."""
    mock_client = MagicMock()
    mock_client.get_properties = AsyncMock(
        return_value={"phh2o": 5.5, "clay": 30.0, "sand": 40.0, "silt": 30.0}
    )
    mock_client.unit_for = MagicMock(
        side_effect=lambda prop: {
            "phh2o": "pH",
            "clay": "%",
            "sand": "%",
            "silt": "%",
        }.get(prop, "")
    )
    return PedologyEngine(soilgrids_client=mock_client)


def _make_knowledge_object(connaissance_id, titre: str) -> KnowledgeObject:
    from datetime import UTC, datetime

    return KnowledgeObject(
        connaissance_id=connaissance_id,
        type=KnowledgeType.concept,
        titre=titre,
        description=titre,
        domaine_scientifique=DomaineScientifique.pedologie,
        contenu={},
        evidence_level=EvidenceLevel.B,
        source=SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Poggio, L. et al.",
            reference="SoilGrids 2.0",
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


class TestPedologyEngineQueryAndIngest:
    """Couverture de query_and_ingest — maillon amont Gate 5 (ROADMAP.md)."""

    async def should_ingest_every_characteristic_when_soilgrids_and_knowledge_succeed(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        engine = _make_soilgrids_engine()

        response = await engine.query_and_ingest(_make_query(), mock_knowledge_engine)

        assert response.latitude == 45.0
        assert response.longitude == 0.5
        assert len(response.resultats) == 4
        noms = {r.nom for r in response.resultats}
        assert noms == {"ph", "argile_pct", "sable_pct", "limon_pct"}
        # SoilGrids est peer_reviewed + referentiel -> plafond B -> accepte
        for resultat in response.resultats:
            assert resultat.statut == "ingested"
            assert resultat.evidence_level == EvidenceLevel.B
            assert resultat.version == 1
            assert resultat.raison is None
        assert mock_knowledge_engine.ingest.await_count == 4

    async def should_report_per_characteristic_result_without_stopping_on_failure(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        """Une caractéristique en échec d'ingestion n'empêche pas les autres."""
        engine = _make_soilgrids_engine()
        calls = {"n": 0}

        async def _ingest_first_fails(request):
            calls["n"] += 1
            if calls["n"] == 1:
                raise KnowledgeEngineError("DB indisponible")
            return _make_knowledge_object(request.connaissance_id, request.titre)

        mock_knowledge_engine.ingest = AsyncMock(side_effect=_ingest_first_fails)

        response = await engine.query_and_ingest(_make_query(), mock_knowledge_engine)

        assert len(response.resultats) == 4
        statuts = [r.statut for r in response.resultats]
        assert statuts.count("refused") == 1
        assert statuts.count("ingested") == 3
        refuse = next(r for r in response.resultats if r.statut == "refused")
        assert refuse.raison is not None
        assert "DB indisponible" in refuse.raison
        assert refuse.version is None

    async def should_raise_pedology_error_when_soilgrids_fails(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        """query_and_ingest propage l'échec SoilGrids comme query() (même garde)."""
        mock_client = MagicMock()
        mock_client.get_properties = AsyncMock(side_effect=SoilGridsClientError("API indisponible"))
        engine = PedologyEngine(soilgrids_client=mock_client)

        with pytest.raises(PedologyEngineError, match="API indisponible"):
            await engine.query_and_ingest(_make_query(), mock_knowledge_engine)

        mock_knowledge_engine.ingest.assert_not_awaited()

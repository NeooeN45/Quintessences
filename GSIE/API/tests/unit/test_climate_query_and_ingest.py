"""Tests unitaires — Climate Engine `query_and_ingest` (Gate 5 — maillon amont).

Couvre le connecteur SYNOP → Evidence → Knowledge : chaque paramètre mesuré
(température, humidité, pression, vent, précipitations) doit devenir une
connaissance qualifiée, sourcée et versionnée. Le SynopClient est mocké.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from gsie_api.engines.climate.engine import ClimateEngine, ClimateEngineError
from gsie_api.engines.climate.schemas import ClimateQuery
from gsie_api.engines.climate.synop_client import SynopClientError
from gsie_api.engines.evidence.schemas import (
    EvidenceLevel,
    KnowledgeStatus,
    SourceReference,
    SourceType,
)
from gsie_api.engines.knowledge.engine import KnowledgeEngineError
from gsie_api.engines.knowledge.schemas import DomaineScientifique, KnowledgeObject, KnowledgeType

_RAW_OBSERVATION = {
    "name": "BORDEAUX-MERIGNAC",
    "lat": "44.83",
    "lon": "-0.69",
    "validity_time": "2026-07-16T21:00:00Z",
    "t": "297.15",
    "u": "60",
    "pmer": "101690",
    "dd": "180",
    "ff": "3.5",
    "rr1": "0.0",
}


def _make_query() -> ClimateQuery:
    return ClimateQuery(station_id="07510")


def _make_synop_engine(raw: dict[str, str] | None = _RAW_OBSERVATION) -> ClimateEngine:
    mock_client = MagicMock()
    mock_client.get_latest_observation = AsyncMock(return_value=raw)
    return ClimateEngine(synop_client=mock_client)


def _make_knowledge_object(connaissance_id, titre: str) -> KnowledgeObject:
    return KnowledgeObject(
        connaissance_id=connaissance_id,
        type=KnowledgeType.concept,
        titre=titre,
        description=titre,
        domaine_scientifique=DomaineScientifique.climatologie,
        contenu={},
        evidence_level=EvidenceLevel.D,
        source=SourceReference(
            type_source=SourceType.referentiel_officiel,
            auteur="Météo-France",
            reference="SYNOP",
        ),
        statut=KnowledgeStatus.quarantine,
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


class TestClimateEngineQueryAndIngest:
    """Couverture de query_and_ingest — maillon amont Gate 5 (ROADMAP.md)."""

    async def should_quarantine_every_parameter_when_synop_and_knowledge_succeed(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        engine = _make_synop_engine()

        response = await engine.query_and_ingest(_make_query(), mock_knowledge_engine)

        assert response is not None
        assert response.station_id == "07510"
        assert response.nom_station == "BORDEAUX-MERIGNAC"
        assert len(response.resultats) == 6
        noms = {r.nom for r in response.resultats}
        assert noms == {
            "temperature_c",
            "humidite_pct",
            "pression_hpa",
            "vent_direction_deg",
            "vent_vitesse_ms",
            "precipitations_1h_mm",
        }
        # SYNOP est une observation brute -> referentiel_officiel + observation
        # plafonne à D -> quarantine (validation humaine requise, CON-001).
        for resultat in response.resultats:
            assert resultat.statut == "quarantined"
            assert resultat.evidence_level == EvidenceLevel.D
        assert mock_knowledge_engine.ingest.await_count == 0

    async def should_omit_missing_parameters(self, mock_knowledge_engine: MagicMock) -> None:
        """Un paramètre SYNOP absent (champ CSV vide) n'est jamais soumis (ADR-009)."""
        raw = dict(_RAW_OBSERVATION)
        raw["u"] = ""
        raw["rr1"] = ""
        engine = _make_synop_engine(raw)

        response = await engine.query_and_ingest(_make_query(), mock_knowledge_engine)

        assert response is not None
        noms = {r.nom for r in response.resultats}
        assert "humidite_pct" not in noms
        assert "precipitations_1h_mm" not in noms
        assert len(response.resultats) == 4

    async def should_return_none_when_station_not_found(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        engine = _make_synop_engine(raw=None)

        response = await engine.query_and_ingest(_make_query(), mock_knowledge_engine)

        assert response is None
        mock_knowledge_engine.ingest.assert_not_awaited()

    async def should_raise_climate_error_when_synop_fails(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        """query_and_ingest propage l'échec SYNOP comme query() (même garde)."""
        mock_client = MagicMock()
        mock_client.get_latest_observation = AsyncMock(
            side_effect=SynopClientError("API indisponible")
        )
        engine = ClimateEngine(synop_client=mock_client)

        with pytest.raises(ClimateEngineError, match="API indisponible"):
            await engine.query_and_ingest(_make_query(), mock_knowledge_engine)

        mock_knowledge_engine.ingest.assert_not_awaited()

    async def should_never_call_knowledge_engine_ingest_since_synop_always_quarantines(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        """SYNOP plafonne toujours à D (quarantine) : ingest() n'est jamais appelé.

        Contrairement à Pedology (SoilGrids, B, accepté), une observation
        SYNOP ne peut jamais atteindre `statut=accepte` avec la matrice de
        décision actuelle — `KnowledgeEngine.ingest` reste donc invoqué
        zéro fois quel que soit son comportement.
        """
        engine = _make_synop_engine()
        mock_knowledge_engine.ingest = AsyncMock(
            side_effect=KnowledgeEngineError("DB indisponible")
        )

        response = await engine.query_and_ingest(_make_query(), mock_knowledge_engine)

        assert response is not None
        assert len(response.resultats) == 6
        for resultat in response.resultats:
            assert resultat.statut == "quarantined"
        mock_knowledge_engine.ingest.assert_not_awaited()

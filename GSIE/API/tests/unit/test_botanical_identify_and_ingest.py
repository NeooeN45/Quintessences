"""Tests unitaires — Botanical Engine `identify_and_ingest` (Gate 5 — maillon amont).

Couvre le connecteur PlantNet → Evidence → Knowledge : chaque espèce
candidate doit devenir une connaissance qualifiée, sourcée et versionnée
(en quarantaine — validation humaine requise, CON-001). Le PlantNetClient
est mocké.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from gsie_api.engines.botanical.engine import BotanicalEngine, BotanicalEngineError
from gsie_api.engines.botanical.plantnet_client import PlantNetClientError
from gsie_api.engines.evidence.schemas import (
    EvidenceLevel,
    KnowledgeStatus,
    SourceReference,
    SourceType,
)
from gsie_api.engines.knowledge.engine import KnowledgeEngineError
from gsie_api.engines.knowledge.schemas import DomaineScientifique, KnowledgeObject, KnowledgeType

_FAKE_PLANTNET_RESPONSE = {
    "bestMatch": "Quercus robur L.",
    "results": [
        {
            "score": 0.85,
            "species": {
                "scientificName": "Quercus robur L.",
                "scientificNameWithoutAuthor": "Quercus robur",
                "genus": {"scientificNameWithoutAuthor": "Quercus"},
                "family": {"scientificNameWithoutAuthor": "Fagaceae"},
                "commonNames": ["Chêne pédonculé"],
            },
            "gbif": {"id": "2878688"},
        },
        {
            "score": 0.05,
            "species": {
                "scientificName": "Quercus petraea Matt.",
                "scientificNameWithoutAuthor": "Quercus petraea",
                "genus": {"scientificNameWithoutAuthor": "Quercus"},
                "family": {"scientificNameWithoutAuthor": "Fagaceae"},
                "commonNames": ["Chêne sessile"],
            },
            "gbif": {"id": "2878689"},
        },
    ],
}


def _make_botanical_engine(response: dict | None = _FAKE_PLANTNET_RESPONSE) -> BotanicalEngine:
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_client.identify = AsyncMock(return_value=response)
    return BotanicalEngine(session=mock_session, plantnet_client=mock_client)


def _make_knowledge_object(connaissance_id, titre: str) -> KnowledgeObject:
    return KnowledgeObject(
        connaissance_id=connaissance_id,
        type=KnowledgeType.concept,
        titre=titre,
        description=titre,
        domaine_scientifique=DomaineScientifique.botanique,
        contenu={},
        evidence_level=EvidenceLevel.D,
        source=SourceReference(
            type_source=SourceType.referentiel_officiel,
            auteur="PlantNet",
            reference="https://my.plantnet.org/",
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


class TestBotanicalEngineIdentifyAndIngest:
    """Couverture de identify_and_ingest — maillon amont Gate 5 (ROADMAP.md)."""

    async def should_quarantine_every_candidate_when_plantnet_succeeds(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        engine = _make_botanical_engine()

        response = await engine.identify_and_ingest(
            b"\x89PNG fake", "test.jpg", mock_knowledge_engine
        )

        assert response is not None
        assert response.best_match == "Quercus robur L."
        assert len(response.resultats) == 2
        noms = {r.nom_scientifique for r in response.resultats}
        assert noms == {"Quercus robur", "Quercus petraea"}
        # PlantNet est une inference ML sur une photo -> referentiel_officiel
        # + observation plafonne à D -> quarantine (CON-001).
        for resultat in response.resultats:
            assert resultat.statut == "quarantined"
            assert resultat.evidence_level == EvidenceLevel.D
        assert mock_knowledge_engine.ingest.await_count == 0

    async def should_return_none_when_plantnet_finds_nothing(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        engine = _make_botanical_engine(response=None)

        response = await engine.identify_and_ingest(
            b"\x89PNG fake", "test.jpg", mock_knowledge_engine
        )

        assert response is None
        mock_knowledge_engine.ingest.assert_not_awaited()

    async def should_raise_botanical_error_when_plantnet_fails(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_client.identify = AsyncMock(side_effect=PlantNetClientError("API indisponible"))
        engine = BotanicalEngine(session=mock_session, plantnet_client=mock_client)

        with pytest.raises(BotanicalEngineError, match="API indisponible"):
            await engine.identify_and_ingest(b"\x89PNG fake", "test.jpg", mock_knowledge_engine)

        mock_knowledge_engine.ingest.assert_not_awaited()

    async def should_never_call_knowledge_engine_ingest_since_plantnet_always_quarantines(
        self, mock_knowledge_engine: MagicMock
    ) -> None:
        engine = _make_botanical_engine()
        mock_knowledge_engine.ingest = AsyncMock(
            side_effect=KnowledgeEngineError("DB indisponible")
        )

        response = await engine.identify_and_ingest(
            b"\x89PNG fake", "test.jpg", mock_knowledge_engine
        )

        assert response is not None
        assert len(response.resultats) == 2
        for resultat in response.resultats:
            assert resultat.statut == "quarantined"
        mock_knowledge_engine.ingest.assert_not_awaited()

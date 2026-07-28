"""Tests unitaires — Knowledge Engine (méthodes pures + ingest/revise avec mock).

Etend tests/unit/test_knowledge_engine.py (qui ne couvre que _to_knowledge_object).
Couvre ici :
- version() statique
- _build_metadata() (tous champs)
- _filter_by_query_type() (tous QueryType)
- _filter_by_custom_filters() (connaissance_id, mots_cles, titre, domaine)
- ingest() : refuse, quarantine, doublon (early returns, pas de flush)
- revise() : not found, aucun champ modifie (erreurs)
- stats() avec mock session

Aucune DB reelle — la session est un MagicMock.
"""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from gsie_api.engines.evidence.schemas import (
    EvidenceLevel,
    KnowledgeStatus,
    SourceReference,
    SourceType,
)
from gsie_api.engines.knowledge.engine import (
    KnowledgeEngine,
    KnowledgeEngineError,
    KnowledgeNotFoundError,
)
from gsie_api.engines.knowledge.schemas import (
    DomaineScientifique,
    DomaineValidite,
    KnowledgeIngestRequest,
    KnowledgeObject,
    KnowledgeQuery,
    KnowledgeRevisionRequest,
    KnowledgeType,
    QueryType,
)


def _make_source() -> SourceReference:
    return SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur="Rameau et al. (2008)",
        date_publication="2008",
        reference="doi:10.0000/test",
    )


def _make_ingest_request(
    statut: KnowledgeStatus = KnowledgeStatus.accepte,
    connaissance_id: Any = None,
) -> KnowledgeIngestRequest:
    return KnowledgeIngestRequest(
        connaissance_id=connaissance_id or uuid4(),
        contenu_normalise={"valeur": "80 mm"},
        type=KnowledgeType.concept,
        titre="RUM du hetre",
        description="Reserve utile en eau minimale pour le hetre.",
        domaine_scientifique=DomaineScientifique.pedologie,
        evidence_level=EvidenceLevel.B,
        source=_make_source(),
        statut=statut,
        mots_cles=["hetre", "RUM"],
        moteurs_consommateurs=["reasoning"],
        conflits=[],
    )


def _make_knowledge_object(
    type_: KnowledgeType = KnowledgeType.concept,
    domaine: DomaineScientifique = DomaineScientifique.pedologie,
    mots_cles: list[str] | None = None,
    domaines_validite: list[DomaineValidite] | None = None,
    titre: str = "Titre test",
) -> KnowledgeObject:
    return KnowledgeObject(
        connaissance_id=uuid4(),
        type=type_,
        titre=titre,
        description="Description test.",
        domaine_scientifique=domaine,
        contenu={},
        evidence_level=EvidenceLevel.B,
        source=_make_source(),
        statut=KnowledgeStatus.accepte,
        version=1,
        date_integration=datetime.now(UTC),
        historique=[],
        domaines_validite=domaines_validite or [],
        moteurs_consommateurs=[],
        relations=[],
        mots_cles=mots_cles or [],
        conflits=[],
    )


def _make_mock_session() -> MagicMock:
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.execute = AsyncMock()
    return session


class TestVersion:
    def should_return_version_string(self) -> None:
        assert KnowledgeEngine.version() == "0.2.0"


class TestBuildMetadata:
    """_build_metadata — tous champs présents."""

    def should_build_metadata_with_all_fields(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        request = _make_ingest_request()
        metadata = engine._build_metadata(request)

        assert metadata["type"] == "concept"
        assert metadata["statut"] == "accepte"
        assert metadata["titre"] == "RUM du hetre"
        assert metadata["domaine_scientifique"] == "pedologie"
        assert metadata["contenu"] == {"valeur": "80 mm"}
        assert metadata["source"]["type_source"] == "peer_reviewed"
        assert metadata["mots_cles"] == ["hetre", "RUM"]
        assert metadata["moteurs_consommateurs"] == ["reasoning"]
        assert metadata["domaines_validite"] == []
        assert metadata["relations"] == []
        assert metadata["conflits"] == []

    def should_serialize_source_as_json_dict(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        request = _make_ingest_request()
        metadata = engine._build_metadata(request)

        # source doit etre un dict (model_dump mode json), pas un SourceReference
        assert isinstance(metadata["source"], dict)
        assert "auteur" in metadata["source"]


class TestFilterByQueryType:
    """_filter_by_query_type — tous les QueryType."""

    def should_filter_concepts_when_par_concept(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        concept = _make_knowledge_object(KnowledgeType.concept)
        relation = _make_knowledge_object(KnowledgeType.relation)
        query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_concept)

        result = engine._filter_by_query_type([concept, relation], query)

        assert result == [concept]

    def should_filter_relations_when_par_relation(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        concept = _make_knowledge_object(KnowledgeType.concept)
        relation = _make_knowledge_object(KnowledgeType.relation)
        query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_relation)

        result = engine._filter_by_query_type([concept, relation], query)

        assert result == [relation]

    def should_filter_by_domaine_when_par_domaine_with_filter(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        pedo = _make_knowledge_object(domaine=DomaineScientifique.pedologie)
        eco = _make_knowledge_object(domaine=DomaineScientifique.ecologie_forestiere)
        query = KnowledgeQuery(
            requete_id=uuid4(),
            type=QueryType.par_domaine,
            filtres={"domaine_scientifique": "pedologie"},
        )

        result = engine._filter_by_query_type([pedo, eco], query)

        assert result == [pedo]

    def should_return_all_when_par_domaine_without_filter(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        pedo = _make_knowledge_object(domaine=DomaineScientifique.pedologie)
        eco = _make_knowledge_object(domaine=DomaineScientifique.ecologie_forestiere)
        query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_domaine)

        result = engine._filter_by_query_type([pedo, eco], query)

        assert len(result) == 2

    def should_filter_by_essence_when_par_essence_with_filter(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        hetre = _make_knowledge_object(mots_cles=["hetre", "RUM"])
        chene = _make_knowledge_object(mots_cles=["chene", "pH"])
        query = KnowledgeQuery(
            requete_id=uuid4(),
            type=QueryType.par_essence,
            filtres={"essence": "HETRE"},
        )

        result = engine._filter_by_query_type([hetre, chene], query)

        assert result == [hetre]

    def should_filter_by_station_when_par_station(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        with_station = _make_knowledge_object(
            domaines_validite=[DomaineValidite(parametre="station pH")]
        )
        without_station = _make_knowledge_object(
            domaines_validite=[DomaineValidite(parametre="altitude")]
        )
        query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_station)

        result = engine._filter_by_query_type([with_station, without_station], query)

        assert result == [with_station]


class TestFilterByCustomFilters:
    """_filter_by_custom_filters — tous les filtres."""

    def should_return_all_when_no_filters(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        obj1 = _make_knowledge_object(titre="A")
        obj2 = _make_knowledge_object(titre="B")

        result = engine._filter_by_custom_filters([obj1, obj2], {})

        assert len(result) == 2

    def should_filter_by_connaissance_id(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        target_id = uuid4()
        obj1 = _make_knowledge_object()
        obj1.connaissance_id = target_id
        obj2 = _make_knowledge_object()
        obj2.connaissance_id = uuid4()

        result = engine._filter_by_custom_filters([obj1, obj2], {"connaissance_id": str(target_id)})

        assert result == [obj1]

    def should_filter_by_mots_cles_list(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        hetre = _make_knowledge_object(mots_cles=["hetre", "RUM"])
        chene = _make_knowledge_object(mots_cles=["chene", "pH"])

        result = engine._filter_by_custom_filters([hetre, chene], {"mots_cles": ["HETRE"]})

        assert result == [hetre]

    def should_filter_by_titre_substring(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        obj1 = _make_knowledge_object(titre="RUM du hetre")
        obj2 = _make_knowledge_object(titre="pH du chene")

        result = engine._filter_by_custom_filters([obj1, obj2], {"titre": "RUM"})

        assert result == [obj1]

    def should_filter_by_domaine_scientifique(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        pedo = _make_knowledge_object(domaine=DomaineScientifique.pedologie)
        eco = _make_knowledge_object(domaine=DomaineScientifique.ecologie_forestiere)

        result = engine._filter_by_custom_filters(
            [pedo, eco], {"domaine_scientifique": "pedologie"}
        )

        assert result == [pedo]


class TestIngestErrors:
    """ingest() — early returns sur statut refuse/quarantine/doublon."""

    async def should_raise_when_statut_refuse(self) -> None:
        session = _make_mock_session()
        engine = KnowledgeEngine(session)
        request = _make_ingest_request(statut=KnowledgeStatus.refuse)

        with pytest.raises(KnowledgeEngineError, match="refus"):
            await engine.ingest(request)

        session.flush.assert_not_awaited()

    async def should_raise_when_statut_quarantine(self) -> None:
        session = _make_mock_session()
        engine = KnowledgeEngine(session)
        request = _make_ingest_request(statut=KnowledgeStatus.quarantine)

        with pytest.raises(KnowledgeEngineError, match="quarantaine"):
            await engine.ingest(request)

        session.flush.assert_not_awaited()

    async def should_raise_when_knowledge_already_exists(self) -> None:
        session = _make_mock_session()
        # Mock get() retourne un ResourceModel existant
        session.get = AsyncMock(return_value=MagicMock())
        engine = KnowledgeEngine(session)
        request = _make_ingest_request()

        with pytest.raises(KnowledgeEngineError, match="existe d"):
            await engine.ingest(request)

        session.flush.assert_not_awaited()


class TestReviseErrors:
    """revise() — erreurs not found et aucun champ modifie."""

    async def should_raise_not_found_when_resource_missing(self) -> None:
        session = _make_mock_session()
        session.get = AsyncMock(return_value=None)
        engine = KnowledgeEngine(session)
        request = KnowledgeRevisionRequest(
            connaissance_id=uuid4(),
            justification="Test",
            nouveau_contenu={"v": 1},
        )

        with pytest.raises(KnowledgeNotFoundError, match="introuvable"):
            await engine.revise(request)

    async def should_raise_when_no_field_modified(self) -> None:
        session = _make_mock_session()
        # resource et assertion existent
        session.get = AsyncMock(return_value=MagicMock())
        engine = KnowledgeEngine(session)
        request = KnowledgeRevisionRequest(
            connaissance_id=uuid4(),
            justification="Test sans modification",
        )

        with pytest.raises(KnowledgeEngineError, match="Aucun champ modifi"):
            await engine.revise(request)


class TestStatsWithMock:
    """stats() avec session mockee."""

    async def should_return_stats_dict(self) -> None:
        session = _make_mock_session()
        result_mock = MagicMock()
        result_mock.all.return_value = [
            (MagicMock(value="classification"), {"type": "concept"}),
            (MagicMock(value="rule"), {"type": "regle"}),
        ]
        session.execute.return_value = result_mock
        engine = KnowledgeEngine(session)

        stats = await engine.stats()

        assert stats["total_objects"] == 2
        assert stats["type_concept"] == 1
        assert stats["type_regle"] == 1

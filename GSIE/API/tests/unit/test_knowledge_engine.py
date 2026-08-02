"""Tests unitaires — KnowledgeEngine._to_knowledge_object.

Pas de DB requise : `_to_knowledge_object` ne touche jamais
`self._session`, un mock suffit pour instancier `KnowledgeEngine`.

Couvre la correction du 2026-07-20 : un `metadata_json` corrompu ou
incomplet (clé `type`/`domaine_scientifique` absente ou `null`) doit
lever une `KnowledgeEngineError` explicite plutôt qu'une `ValueError`
Pydantic opaque (`KnowledgeType(None)` levait auparavant un message
« None is not a valid KnowledgeType », sans dire quelle connaissance
ni quel champ est en cause).
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from gsie_api.engines.knowledge.engine import KnowledgeEngine, KnowledgeEngineError


def _valid_metadata() -> dict[str, object]:
    return {
        "type": "concept",
        "titre": "Titre de test",
        "description": "Description de test",
        "domaine_scientifique": "botanique",
        "contenu": {},
        "source": {
            "type_source": "peer_reviewed",
            "auteur": "Auteur Test",
            "reference": "doi:10.0000/test",
        },
        "statut": "accepte",
    }


class TestToKnowledgeObject:
    """Reconstruction d'un KnowledgeObject depuis resource.metadata_json."""

    def _engine(self) -> KnowledgeEngine:
        return KnowledgeEngine(session=Mock())

    def test_should_build_object_when_metadata_complete(self) -> None:
        engine = self._engine()
        result = engine._to_knowledge_object(
            connaissance_id=uuid4(),
            metadata=_valid_metadata(),
            evidence_level=None,
            version=1,
            date_integration=datetime.now(UTC),
            historique=None,
        )
        assert result.type.value == "concept"
        assert result.domaine_scientifique.value == "botanique"

    def test_should_raise_when_type_missing(self) -> None:
        metadata = _valid_metadata()
        del metadata["type"]
        engine = self._engine()
        with pytest.raises(KnowledgeEngineError, match="type"):
            engine._to_knowledge_object(
                connaissance_id=uuid4(),
                metadata=metadata,
                evidence_level=None,
                version=1,
                date_integration=datetime.now(UTC),
                historique=None,
            )

    def test_should_raise_when_type_is_null(self) -> None:
        metadata = _valid_metadata()
        metadata["type"] = None
        engine = self._engine()
        with pytest.raises(KnowledgeEngineError, match="type"):
            engine._to_knowledge_object(
                connaissance_id=uuid4(),
                metadata=metadata,
                evidence_level=None,
                version=1,
                date_integration=datetime.now(UTC),
                historique=None,
            )

    def test_should_raise_when_domaine_scientifique_missing(self) -> None:
        metadata = _valid_metadata()
        del metadata["domaine_scientifique"]
        engine = self._engine()
        with pytest.raises(KnowledgeEngineError, match="domaine_scientifique"):
            engine._to_knowledge_object(
                connaissance_id=uuid4(),
                metadata=metadata,
                evidence_level=None,
                version=1,
                date_integration=datetime.now(UTC),
                historique=None,
            )


class TestReglesApplicables:
    """Couverture de regles_applicables — gardes géographiques et de citation.

    Ces tests vérifient que la requête SQL construite par le moteur contient
    bien les filtres ST_Contains (containment géographique) et citation_role
    = primary (citation sourcée). Sans ces gardes, une règle hors domaine
    ou non sourcée serait retournée, produisant une conclusion fausse citant
    une source réelle — invisible.
    """

    async def should_filter_by_st_contains_when_querying_rules(self) -> None:
        # Arrange — session mockée : territoire trouvé, requête capturée
        captured_queries: list = []

        async def _capture_execute(query, *args, **kwargs):
            captured_queries.append(query)
            result = Mock()
            result.all = Mock(return_value=[])
            return result

        session = AsyncMock()
        session.get = AsyncMock(return_value=Mock())  # PlaceModel trouvé
        session.execute = AsyncMock(side_effect=_capture_execute)

        engine = KnowledgeEngine(session)

        # Act
        await engine.regles_applicables(uuid4(), variables_connues={})

        # Assert — la requête doit contenir ST_Contains
        assert len(captured_queries) >= 1
        sql = str(
            captured_queries[0].compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )
        assert "ST_Contains" in sql, (
            "la requête doit filtrer par containment géographique — "
            "sans ST_Contains, une règle hors domaine serait retournée"
        )

    async def should_filter_by_primary_citation_role_when_querying_rules(self) -> None:
        # Arrange — session mockée : territoire trouvé, requête capturée
        captured_queries: list = []

        async def _capture_execute(query, *args, **kwargs):
            captured_queries.append(query)
            result = Mock()
            result.all = Mock(return_value=[])
            return result

        session = AsyncMock()
        session.get = AsyncMock(return_value=Mock())  # PlaceModel trouvé
        session.execute = AsyncMock(side_effect=_capture_execute)

        engine = KnowledgeEngine(session)

        # Act
        await engine.regles_applicables(uuid4(), variables_connues={})

        # Assert — la requête doit filtrer par citation_role = primary
        assert len(captured_queries) >= 1
        sql = str(
            captured_queries[0].compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )
        assert "citation_role" in sql, (
            "la requête doit filtrer par citation_role = primary — "
            "sans ce filtre, une citation de role secondaire suffirait "
            "à faire sortir une règle non sourcée"
        )
        assert "primary" in sql, (
            "la requête doit exiger citation_role = primary — "
            "une règle citée « en passant » ne vaut pas une règle sourcée"
        )

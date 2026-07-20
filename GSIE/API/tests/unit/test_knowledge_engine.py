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
from unittest.mock import Mock
from uuid import uuid4

import pytest

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

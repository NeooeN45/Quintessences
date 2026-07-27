"""Tests unitaires — cas limites du Knowledge Engine (couverture ciblée).

Complète tests/unit/test_knowledge_engine.py et
tests/unit/test_knowledge_engine_extended.py en couvrant les branches
restantes de `src/gsie_api/engines/knowledge/engine.py` :
- revise() : révision de la source, des domaines de validité, ajout d'une
  référence RFC, et création d'une nouvelle EvidenceAssessment quand le
  niveau de preuve est révisé (avec ou sans evidence antérieure)
- _filter_by_query_type() : cas limites (essence vide, type de requête
  inconnu ne correspondant à aucune branche)

Aucune DB réelle — la session AsyncSession est simulée avec des Mock,
suivant le même patron que test_knowledge_engine_extended.py.
"""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from gsie_api.engines.evidence.schemas import (
    EvidenceLevel,
    KnowledgeStatus,
    SourceReference,
    SourceType,
)
from gsie_api.engines.knowledge.engine import KnowledgeEngine
from gsie_api.engines.knowledge.schemas import (
    DomaineScientifique,
    DomaineValidite,
    KnowledgeObject,
    KnowledgeQuery,
    KnowledgeRevisionRequest,
    KnowledgeType,
    QueryType,
)


def _make_source(auteur: str = "Rameau et al. (2008)") -> SourceReference:
    """Source réelle — flore forestière française (Rameau et al., 2008)."""
    return SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur=auteur,
        date_publication="2008",
        reference="doi:10.0000/rameau-2008",
    )


def _make_source_metadata() -> dict[str, Any]:
    """Metadata initiale valide pour la resource révisée (ONF)."""
    return {
        "type": "seuil",
        "titre": "RUM minimale pour le hêtre (Fagus sylvatica)",
        "description": (
            "Réserve utile en eau minimale sous laquelle la station est "
            "défavorable au hêtre."
        ),
        "domaine_scientifique": "pedologie",
        "contenu": {"valeur": "80 mm"},
        "source": _make_source("ONF").model_dump(mode="json"),
        "statut": "accepte",
        "domaines_validite": [],
        "moteurs_consommateurs": [],
        "relations": [],
        "mots_cles": ["hetre", "RUM"],
        "conflits": [],
    }


def _make_evidence_result(evidence: Any) -> MagicMock:
    """Résultat mocké pour la requête EvidenceAssessmentModel.scalars().first()."""
    result = MagicMock()
    result.scalars.return_value.first.return_value = evidence
    return result


def _make_revision_result(rows: list[Any] | None = None) -> MagicMock:
    """Résultat mocké pour la requête RevisionModel.scalars().all()."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows or []
    return result


def _make_resource_assertion_pair(
    metadata: dict[str, Any], version: int = 1
) -> tuple[MagicMock, MagicMock]:
    """Construit une paire (ResourceModel, AssertionModel) mockée pour revise()."""
    resource = MagicMock()
    resource.metadata_json = metadata
    assertion = MagicMock()
    assertion.version = version
    return resource, assertion


def _make_revision_request(
    connaissance_id: Any = None,
    justification: str = "Révision suite à mise à jour ONF",
    rfc_reference: str | None = None,
    nouveau_contenu: dict[str, Any] | None = None,
    nouveau_evidence_level: EvidenceLevel | None = None,
    nouvelle_source: SourceReference | None = None,
    nouveaux_domaines_validite: list[DomaineValidite] | None = None,
) -> KnowledgeRevisionRequest:
    return KnowledgeRevisionRequest(
        connaissance_id=connaissance_id or uuid4(),
        justification=justification,
        rfc_reference=rfc_reference,
        nouveau_contenu=nouveau_contenu,
        nouveau_evidence_level=nouveau_evidence_level,
        nouvelle_source=nouvelle_source,
        nouveaux_domaines_validite=nouveaux_domaines_validite,
    )


def _make_knowledge_object(
    type_: KnowledgeType = KnowledgeType.concept,
    domaine: DomaineScientifique = DomaineScientifique.pedologie,
    mots_cles: list[str] | None = None,
) -> KnowledgeObject:
    return KnowledgeObject(
        connaissance_id=uuid4(),
        type=type_,
        titre="Titre test",
        description="Description test.",
        domaine_scientifique=domaine,
        contenu={},
        evidence_level=EvidenceLevel.B,
        source=_make_source(),
        statut=KnowledgeStatus.accepte,
        version=1,
        date_integration=datetime.now(UTC),
        historique=[],
        domaines_validite=[],
        moteurs_consommateurs=[],
        relations=[],
        mots_cles=mots_cles or [],
        conflits=[],
    )


class _QueryTypeInconnu:
    """Simule un objet KnowledgeQuery dont le type ne correspond à aucun QueryType.

    Utilisé uniquement pour exercer la branche de repli finale de
    `_filter_by_query_type` (`return objects`), qui n'est normalement pas
    atteignable via un vrai QueryType (StrEnum exhaustif) puisque Pydantic
    valide `KnowledgeQuery.type` à la construction.
    """

    def __init__(self) -> None:
        self.type = "type_de_requete_inconnu"
        self.filtres: dict[str, Any] = {}


class TestReviseSourceEtDomainesValidite:
    """revise() — mise à jour ciblée de la source et des domaines de validité."""

    async def should_update_source_when_nouvelle_source_provided(self) -> None:
        # Arrange — une source ONF est remplacée par une source Rameau et al. (2008)
        metadata = _make_source_metadata()
        resource, assertion = _make_resource_assertion_pair(metadata)
        session = MagicMock()
        session.get = AsyncMock(side_effect=[resource, assertion])
        session.flush = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[_make_evidence_result(None), _make_revision_result()]
        )
        engine = KnowledgeEngine(session)
        nouvelle_source = _make_source("Rameau et al. (2008)")
        request = _make_revision_request(nouvelle_source=nouvelle_source)

        # Act
        result = await engine.revise(request)

        # Assert — la nouvelle source remplace l'ancienne dans le résultat reconstruit
        assert result.source.auteur == "Rameau et al. (2008)"

    async def should_update_domaines_validite_when_provided(self) -> None:
        # Arrange — ajout d'un domaine de validité altitudinal (IGN)
        metadata = _make_source_metadata()
        resource, assertion = _make_resource_assertion_pair(metadata)
        session = MagicMock()
        session.get = AsyncMock(side_effect=[resource, assertion])
        session.flush = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[_make_evidence_result(None), _make_revision_result()]
        )
        engine = KnowledgeEngine(session)
        nouveaux_domaines = [
            DomaineValidite(parametre="altitude", minimum=200.0, maximum=800.0, unite="m")
        ]
        request = _make_revision_request(nouveaux_domaines_validite=nouveaux_domaines)

        # Act
        result = await engine.revise(request)

        # Assert — le domaine de validité est bien reconstruit
        assert len(result.domaines_validite) == 1
        assert result.domaines_validite[0].parametre == "altitude"

    async def should_append_rfc_reference_to_justification_when_provided(self) -> None:
        # Arrange — révision gouvernée par une RFC
        metadata = _make_source_metadata()
        resource, assertion = _make_resource_assertion_pair(metadata)
        session = MagicMock()
        session.get = AsyncMock(side_effect=[resource, assertion])
        session.flush = AsyncMock()
        added_models: list[Any] = []
        session.add = MagicMock(side_effect=added_models.append)
        session.execute = AsyncMock(
            side_effect=[_make_evidence_result(None), _make_revision_result()]
        )
        engine = KnowledgeEngine(session)
        request = _make_revision_request(
            justification="Mise à jour du seuil pédologique",
            rfc_reference="RFC-0011",
            nouveau_contenu={"valeur": "90 mm"},
        )

        # Act
        await engine.revise(request)

        # Assert — la justification de la RevisionModel contient la référence RFC
        revisions = [m for m in added_models if type(m).__name__ == "RevisionModel"]
        assert len(revisions) == 1
        assert "RFC-0011" in revisions[0].justification


class TestReviseEvidenceLevel:
    """revise() — révision du niveau de preuve, avec ou sans évaluation antérieure."""

    async def should_create_new_evidence_assessment_when_previous_evidence_exists(self) -> None:
        # Arrange — une EvidenceAssessment antérieure existe déjà pour cette connaissance
        metadata = _make_source_metadata()
        resource, assertion = _make_resource_assertion_pair(metadata)
        session = MagicMock()
        session.get = AsyncMock(side_effect=[resource, assertion])
        session.flush = AsyncMock()
        added_models: list[Any] = []
        session.add = MagicMock(side_effect=added_models.append)
        evidence_anterieure = MagicMock()
        session.execute = AsyncMock(
            side_effect=[_make_evidence_result(evidence_anterieure), _make_revision_result()]
        )
        engine = KnowledgeEngine(session)
        request = _make_revision_request(nouveau_evidence_level=EvidenceLevel.A)

        # Act
        result = await engine.revise(request)

        # Assert — une nouvelle EvidenceAssessmentModel a été ajoutée à la session
        assert result.evidence_level == EvidenceLevel.A
        evidence_models = [
            m for m in added_models if type(m).__name__ == "EvidenceAssessmentModel"
        ]
        assert len(evidence_models) == 1
        assert evidence_models[0].method == "knowledge_engine_revise"

    async def should_not_create_evidence_assessment_when_no_previous_evidence(self) -> None:
        # Arrange — aucune EvidenceAssessment antérieure trouvée (cas dégradé)
        metadata = _make_source_metadata()
        resource, assertion = _make_resource_assertion_pair(metadata)
        session = MagicMock()
        session.get = AsyncMock(side_effect=[resource, assertion])
        session.flush = AsyncMock()
        added_models: list[Any] = []
        session.add = MagicMock(side_effect=added_models.append)
        session.execute = AsyncMock(
            side_effect=[_make_evidence_result(None), _make_revision_result()]
        )
        engine = KnowledgeEngine(session)
        request = _make_revision_request(nouveau_evidence_level=EvidenceLevel.C)

        # Act
        result = await engine.revise(request)

        # Assert — le niveau de preuve du résultat est bien mis à jour malgré
        # l'absence d'EvidenceAssessment antérieure à réviser
        assert result.evidence_level == EvidenceLevel.C
        evidence_models = [
            m for m in added_models if type(m).__name__ == "EvidenceAssessmentModel"
        ]
        assert len(evidence_models) == 0


class TestFilterByQueryTypeEdgeCases:
    """_filter_by_query_type() — cas limites non couverts par les tests standards."""

    def should_return_all_objects_when_par_essence_without_essence_filter(self) -> None:
        engine = KnowledgeEngine(session=MagicMock())
        hetre = _make_knowledge_object(mots_cles=["hetre"])
        chene = _make_knowledge_object(mots_cles=["chene"])
        query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_essence, filtres={})

        result = engine._filter_by_query_type([hetre, chene], query)

        assert result == [hetre, chene]

    def should_return_all_objects_when_query_type_matches_no_branch(self) -> None:
        # Cas de repli défensif — non atteignable via un vrai QueryType (StrEnum
        # exhaustif validé par Pydantic), exercé ici directement au niveau de
        # la méthode interne pour couvrir la ligne de retour par défaut.
        engine = KnowledgeEngine(session=MagicMock())
        objets = [_make_knowledge_object(), _make_knowledge_object()]

        result = engine._filter_by_query_type(objets, _QueryTypeInconnu())

        assert result == objets


class TestReviseConserveEvidenceLevelReconstruit:
    """revise() — vérifie que le niveau de preuve du résultat suit la demande."""

    async def should_keep_reconstructed_evidence_level_when_no_new_level_requested(self) -> None:
        # Arrange — révision du contenu seul, sans changement d'evidence_level
        metadata = _make_source_metadata()
        resource, assertion = _make_resource_assertion_pair(metadata)
        session = MagicMock()
        session.get = AsyncMock(side_effect=[resource, assertion])
        session.flush = AsyncMock()
        evidence_existante = MagicMock()
        evidence_existante.level.value = "B"
        session.execute = AsyncMock(
            side_effect=[_make_evidence_result(evidence_existante), _make_revision_result()]
        )
        engine = KnowledgeEngine(session)
        request = _make_revision_request(nouveau_contenu={"valeur": "85 mm"})

        # Act
        result = await engine.revise(request)

        # Assert — le niveau de preuve reconstruit depuis l'évaluation existante est conservé
        assert result.evidence_level == EvidenceLevel.B

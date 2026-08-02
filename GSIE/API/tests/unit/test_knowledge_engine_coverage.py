"""Tests unitaires — couverture résiduelle de Knowledge Engine.

Complète les trois fichiers de tests existants en couvrant les lignes
restantes de `src/gsie_api/engines/knowledge/engine.py` :
- `_source_reference` (152-173) : SourceIncitableError sur auteur/date/nature
  manquants, et chemins de fallback de la référence (doi → url → title).
- `ingest` (224-286) : création complète de resource + assertion + evidence
  + revision, et reconstruction du KnowledgeObject.
- `query` (306-362) : requête DB avec window function, filtre evidence_min,
  pagination, et chargement d'historique.
- `_load_historique` (591) : retour anticipé quand current_version <= 1.
- `regles_applicables` (719-810) : territoire inconnu, résultat vide, règle
  écartée par le plancher de preuve, règle non dérivable, règle retenue.
- `_qualificateurs_par_assertion` (816-829) : chargement groupé des
  qualificateurs.

Aucune DB réelle — la session AsyncSession est simulée avec AsyncMock,
suivant le même patron que test_knowledge_engine_edge_cases.py.
"""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from gsie_api.engines.evidence.schemas import (
    EvidenceLevel,
    KnowledgeStatus,
    SourceReference,
    SourceType,
)
from gsie_api.engines.knowledge.engine import (
    KnowledgeEngine,
    SourceIncitableError,
    TerritoireInconnuError,
    _source_reference,
)
from gsie_api.engines.knowledge.schemas import (
    DomaineScientifique,
    KnowledgeIngestRequest,
    KnowledgeQuery,
    KnowledgeRevisionRequest,
    KnowledgeType,
    QueryType,
)
from gsie_api.infrastructure.models.enums import SourceNature

# --- Helpers ---------------------------------------------------------------


def _make_source_model(
    auteur: str | None = "Rameau et al. (2008)",
    date_publication: str | None = "2008",
    source_nature: SourceNature = SourceNature.reference,
    doi: str | None = "doi:10.0000/rameau-2008",
    url: str | None = None,
    title: str | None = "Flore forestière française",
) -> MagicMock:
    """Construit un SourceModel mocké avec les attributs attendus par _source_reference."""
    source = MagicMock()
    source.id = uuid4()
    source.auteur = auteur
    source.date_publication = date_publication
    source.source_nature = source_nature
    source.doi = doi
    source.url = url
    source.title = title
    return source


def _make_ingest_request(
    connaissance_id: UUID | None = None,
) -> KnowledgeIngestRequest:
    return KnowledgeIngestRequest(
        connaissance_id=connaissance_id or uuid4(),
        contenu_normalise={"valeur": "80 mm"},
        type=KnowledgeType.seuil,
        titre="RUM minimale pour le hetre",
        description="Reserve utile en eau minimale pour le hetre.",
        domaine_scientifique=DomaineScientifique.pedologie,
        evidence_level=EvidenceLevel.B,
        source=SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Rameau et al. (2008)",
            date_publication="2008",
            reference="doi:10.0000/test",
        ),
        statut=KnowledgeStatus.accepte,
        mots_cles=["hetre", "RUM"],
        moteurs_consommateurs=["reasoning"],
        conflits=[],
    )


def _make_valid_metadata() -> dict[str, Any]:
    """Metadata valide pour _to_knowledge_object (reconstruction)."""
    return {
        "type": "seuil",
        "titre": "RUM minimale pour le hetre",
        "description": "Reserve utile en eau minimale pour le hetre.",
        "domaine_scientifique": "pedologie",
        "contenu": {"valeur": "80 mm"},
        "source": {
            "type_source": "peer_reviewed",
            "auteur": "Rameau et al. (2008)",
            "date_publication": "2008",
            "reference": "doi:10.0000/test",
        },
        "statut": "accepte",
        "domaines_validite": [],
        "moteurs_consommateurs": ["reasoning"],
        "relations": [],
        "mots_cles": ["hetre", "RUM"],
        "conflits": [],
    }


def _make_mock_session() -> MagicMock:
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.execute = AsyncMock()
    return session


def _make_evidence_mock(level: str = "B") -> MagicMock:
    """EvidenceAssessmentModel mocké avec .level.value exploitable."""
    evidence = MagicMock()
    evidence.level.value = level
    return evidence


def _make_query_result_row(
    metadata: dict[str, Any] | None = None,
    version: int = 1,
    evidence_level: str = "B",
    updated_at: datetime | None = None,
) -> tuple[MagicMock, MagicMock, MagicMock]:
    """Construit un tuple (resource, assertion, evidence) tel que renvoyé par query()."""
    resource = MagicMock()
    resource.id = uuid4()
    resource.metadata_json = metadata or _make_valid_metadata()
    resource.updated_at = updated_at or datetime.now(UTC)
    assertion = MagicMock()
    assertion.version = version
    evidence = _make_evidence_mock(evidence_level)
    return resource, assertion, evidence


def _make_revision_row(version: int, justification: str) -> MagicMock:
    row = MagicMock()
    row.version = version
    row.valid_time_start = datetime.now(UTC)
    row.justification = justification
    return row


# --- _source_reference (lignes 152-173) ------------------------------------


class TestSourceReference:
    """_source_reference — construction de la citation depuis une SourceModel."""

    def should_raise_when_auteur_missing(self) -> None:
        # Arrange — source sans auteur, date présente
        source = _make_source_model(auteur=None)

        # Act + Assert
        with pytest.raises(SourceIncitableError, match="auteur"):
            _source_reference(source)

    def should_raise_when_date_publication_missing(self) -> None:
        # Arrange — source avec auteur, sans date
        source = _make_source_model(date_publication=None)

        # Act + Assert
        with pytest.raises(SourceIncitableError, match="date_publication"):
            _source_reference(source)

    def should_raise_when_both_auteur_and_date_missing(self) -> None:
        # Arrange — source sans auteur ni date
        source = _make_source_model(auteur=None, date_publication=None)

        # Act + Assert
        with pytest.raises(SourceIncitableError, match="auteur, date_publication"):
            _source_reference(source)

    def should_raise_when_source_nature_not_in_mapping(self) -> None:
        # Arrange — nature non couverte par _NATURE_VERS_TYPE_SOURCE
        source = MagicMock()
        source.id = uuid4()
        source.auteur = "ONF"
        source.date_publication = "2020"
        source.source_nature = MagicMock()
        source.source_nature.value = "nature_inconnue"
        source.doi = None
        source.url = None
        source.title = "Guide"

        # Act + Assert
        with pytest.raises(SourceIncitableError, match="nature"):
            _source_reference(source)

    def should_use_doi_as_reference_when_doi_present(self) -> None:
        # Arrange — doi présent, url et title ignorés
        source = _make_source_model(
            doi="doi:10.0000/rameau", url="https://example.com", title="Titre"
        )

        # Act
        ref = _source_reference(source)

        # Assert
        assert ref.reference == "doi:10.0000/rameau"
        assert ref.type_source == SourceType.referentiel_officiel

    def should_use_url_as_reference_when_doi_absent(self) -> None:
        # Arrange — doi absent, url présente
        source = _make_source_model(doi=None, url="https://example.com", title="Titre")

        # Act
        ref = _source_reference(source)

        # Assert
        assert ref.reference == "https://example.com"

    def should_use_title_as_reference_when_doi_and_url_absent(self) -> None:
        # Arrange — ni doi ni url, fallback sur title
        source = _make_source_model(doi=None, url=None, title="Flore forestiere francaise")

        # Act
        ref = _source_reference(source)

        # Assert
        assert ref.reference == "Flore forestiere francaise"

    def should_map_expert_statement_to_expert_identifie(self) -> None:
        # Arrange
        source = _make_source_model(source_nature=SourceNature.expert_statement)

        # Act
        ref = _source_reference(source)

        # Assert
        assert ref.type_source == SourceType.expert_identifie

    def should_map_model_output_to_observation_terrain(self) -> None:
        # Arrange
        source = _make_source_model(source_nature=SourceNature.model_output)

        # Act
        ref = _source_reference(source)

        # Assert
        assert ref.type_source == SourceType.observation_terrain


# --- ingest (lignes 224-286) -----------------------------------------------


class TestIngestSuccess:
    """ingest() — création complète (resource + assertion + evidence + revision)."""

    async def should_create_and_return_knowledge_object_when_statut_accepte(self) -> None:
        # Arrange
        session = _make_mock_session()
        session.get = AsyncMock(return_value=None)
        added_models: list[Any] = []
        session.add = MagicMock(side_effect=added_models.append)
        engine = KnowledgeEngine(session)
        request = _make_ingest_request()

        # Act
        result = await engine.ingest(request)

        # Assert — le KnowledgeObject reconstruit porte les bonnes valeurs
        assert result.type == KnowledgeType.seuil
        assert result.version == 1
        assert result.domaine_scientifique == DomaineScientifique.pedologie
        # Au moins 4 modèles ajoutés : 2 resource, 1 assertion, 1 evidence, 1 revision
        types_ajoutes = {type(m).__name__ for m in added_models}
        assert "ResourceModel" in types_ajoutes
        assert "AssertionModel" in types_ajoutes
        assert "EvidenceAssessmentModel" in types_ajoutes
        assert "RevisionModel" in types_ajoutes
        # Deux flush appelés (avant assertion/evidence, et final)
        assert session.flush.await_count == 2


# --- query (lignes 306-362) ------------------------------------------------


class TestQuery:
    """query() — requête DB avec window function, filtres, pagination, historique."""

    async def should_return_paginated_results_when_objects_exist(self) -> None:
        # Arrange — une ligne retournée par la DB
        session = _make_mock_session()
        row = _make_query_result_row()
        result_mock = MagicMock()
        result_mock.all.return_value = [row]
        session.execute.return_value = result_mock
        engine = KnowledgeEngine(session)
        query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_domaine)

        # Act
        result = await engine.query(query)

        # Assert
        assert result.total == 1
        assert len(result.connaissances) == 1
        assert result.connaissances[0].type == KnowledgeType.seuil
        assert result.version_graph == KnowledgeEngine.version()

    async def should_filter_by_evidence_min_when_provided(self) -> None:
        # Arrange — un objet A (retenu) et un objet F (écarté)
        session = _make_mock_session()
        row_a = _make_query_result_row(evidence_level="A")
        row_f = _make_query_result_row(evidence_level="F")
        result_mock = MagicMock()
        result_mock.all.return_value = [row_a, row_f]
        session.execute.return_value = result_mock
        engine = KnowledgeEngine(session)
        query = KnowledgeQuery(
            requete_id=uuid4(),
            type=QueryType.par_domaine,
            evidence_min=EvidenceLevel.B,
        )

        # Act
        result = await engine.query(query)

        # Assert — seul l'objet de niveau A passe le filtre
        assert result.total == 1
        assert result.connaissances[0].evidence_level == EvidenceLevel.A

    async def should_paginate_when_page_size_smaller_than_total(self) -> None:
        # Arrange — 3 objets, page_size=2, page=1
        session = _make_mock_session()
        rows = [
            _make_query_result_row(evidence_level="A"),
            _make_query_result_row(evidence_level="B"),
            _make_query_result_row(evidence_level="C"),
        ]
        result_mock = MagicMock()
        result_mock.all.return_value = rows
        session.execute.return_value = result_mock
        engine = KnowledgeEngine(session)
        query = KnowledgeQuery(
            requete_id=uuid4(),
            type=QueryType.par_domaine,
            page=1,
            page_size=2,
        )

        # Act
        result = await engine.query(query)

        # Assert — total=3 mais seulement 2 objets sur la page
        assert result.total == 3
        assert len(result.connaissances) == 2

    async def should_return_empty_when_no_objects_match(self) -> None:
        # Arrange — aucune ligne retournée
        session = _make_mock_session()
        result_mock = MagicMock()
        result_mock.all.return_value = []
        session.execute.return_value = result_mock
        engine = KnowledgeEngine(session)
        query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_concept)

        # Act
        result = await engine.query(query)

        # Assert
        assert result.total == 0
        assert result.connaissances == []

    async def should_load_historique_for_page_objects(self) -> None:
        # Arrange — un objet version 2, _load_historique doit être appelé
        session = _make_mock_session()
        row = _make_query_result_row(version=2, evidence_level="B")
        result_mock = MagicMock()
        result_mock.all.return_value = [row]
        # session.execute est appelé deux fois : la requête query, puis _load_historique
        revision_result = MagicMock()
        revision_result.scalars.return_value.all.return_value = [
            _make_revision_row(1, "Ingestion initiale"),
            _make_revision_row(2, "Révision du seuil"),
        ]
        session.execute = AsyncMock(side_effect=[result_mock, revision_result])
        engine = KnowledgeEngine(session)
        query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_domaine)

        # Act
        result = await engine.query(query)

        # Assert — l'historique est chargé pour l'objet de la page
        assert len(result.connaissances) == 1
        assert len(result.connaissances[0].historique) == 1


# --- _load_historique (ligne 591) ------------------------------------------


class TestLoadHistorique:
    """_load_historique — retour anticipé quand current_version <= 1."""

    async def should_return_empty_list_when_current_version_is_one(self) -> None:
        # Arrange
        session = _make_mock_session()
        engine = KnowledgeEngine(session)

        # Act
        result = await engine._load_historique(uuid4(), current_version=1)

        # Assert — pas de requête DB, retour immédiat
        assert result == []
        session.execute.assert_not_awaited()


# --- regles_applicables (lignes 719-810) -----------------------------------


def _make_assertion_row(
    assertion_id: UUID | None = None,
    niveau: str = "B",
) -> tuple[MagicMock, MagicMock, MagicMock]:
    """Construit un tuple (assertion, niveau, source) tel que retourné par la requête."""
    assertion = MagicMock()
    assertion.id = assertion_id or uuid4()
    niveau_mock = MagicMock()
    niveau_mock.value = niveau
    source = _make_source_model()
    return assertion, niveau_mock, source


class TestReglesApplicables:
    """regles_applicables — récupération des règles par contexte territorial."""

    async def should_raise_territoire_inconnu_when_place_not_found(self) -> None:
        # Arrange — session.get retourne None pour le territoire
        session = _make_mock_session()
        session.get = AsyncMock(return_value=None)
        engine = KnowledgeEngine(session)

        # Act + Assert
        with pytest.raises(TerritoireInconnuError, match="territoire"):
            await engine.regles_applicables(
                uuid4(),
                variables_connues={},
            )

    async def should_return_empty_lists_when_no_rules_match(self) -> None:
        # Arrange — territoire trouvé mais aucune ligne retournée
        session = _make_mock_session()
        session.get = AsyncMock(return_value=MagicMock())
        result_mock = MagicMock()
        result_mock.all.return_value = []
        session.execute.return_value = result_mock
        engine = KnowledgeEngine(session)

        # Act
        regles, ecartees = await engine.regles_applicables(
            uuid4(),
            variables_connues={},
        )

        # Assert
        assert regles == []
        assert ecartees == []

    async def should_return_rule_when_derivation_succeeds(self) -> None:
        # Arrange — une assertion avec qualificateurs complets et source citable
        assertion_id = uuid4()
        session = _make_mock_session()
        session.get = AsyncMock(return_value=MagicMock())
        assertion_row = _make_assertion_row(assertion_id=assertion_id, niveau="B")
        result_mock = MagicMock()
        result_mock.all.return_value = [assertion_row]
        # _qualificateurs_par_assertion : deuxième appel à execute
        qualif_result = MagicMock()
        qualif_result.all.return_value = [
            (assertion_id, "variable", "reserve_utile_mm"),
            (assertion_id, "operateur", "<"),
            (assertion_id, "valeur", "80"),
            (assertion_id, "enonce_conclusion", "Station defavorable au hetre"),
            (assertion_id, "niveau_confiance", "0.8"),
        ]
        session.execute = AsyncMock(side_effect=[result_mock, qualif_result])
        engine = KnowledgeEngine(session)

        # Act
        regles, ecartees = await engine.regles_applicables(
            uuid4(),
            variables_connues={"reserve_utile_mm": "pedology_reserve_utile_mm"},
        )

        # Assert — une règle dérivée et retenue
        assert len(regles) == 1
        assert regles[0].identifiant == str(assertion_id)
        assert regles[0].evidence_level == EvidenceLevel.B
        assert ecartees == []

    async def should_exclude_rule_when_evidence_below_threshold(self) -> None:
        # Arrange — règle de niveau F, plancher B demandé
        assertion_id = uuid4()
        session = _make_mock_session()
        session.get = AsyncMock(return_value=MagicMock())
        assertion_row = _make_assertion_row(assertion_id=assertion_id, niveau="F")
        result_mock = MagicMock()
        result_mock.all.return_value = [assertion_row]
        session.execute.return_value = result_mock
        engine = KnowledgeEngine(session)

        # Act
        regles, ecartees = await engine.regles_applicables(
            uuid4(),
            variables_connues={},
            evidence_min=EvidenceLevel.B,
        )

        # Assert — la règle est écartée, aucune retenue
        assert regles == []
        assert len(ecartees) == 1
        assert "F" in ecartees[0]

    async def should_exclude_rule_when_derivation_fails(self) -> None:
        # Arrange — assertion avec qualificateurs incomplets (opérateur absent)
        assertion_id = uuid4()
        session = _make_mock_session()
        session.get = AsyncMock(return_value=MagicMock())
        assertion_row = _make_assertion_row(assertion_id=assertion_id, niveau="A")
        result_mock = MagicMock()
        result_mock.all.return_value = [assertion_row]
        # _qualificateurs_par_assertion : qualificateurs incomplets
        qualif_result = MagicMock()
        qualif_result.all.return_value = [
            (assertion_id, "variable", "reserve_utile_mm"),
            (assertion_id, "valeur", "80"),
            (assertion_id, "enonce_conclusion", "Station defavorable"),
            (assertion_id, "niveau_confiance", "0.8"),
            # operateur absent → DerivationImpossibleError
        ]
        session.execute = AsyncMock(side_effect=[result_mock, qualif_result])
        engine = KnowledgeEngine(session)

        # Act
        regles, ecartees = await engine.regles_applicables(
            uuid4(),
            variables_connues={"reserve_utile_mm": "pedology_reserve_utile_mm"},
        )

        # Assert — la règle est écartée pour qualificateur manquant
        assert regles == []
        assert len(ecartees) == 1
        assert "operateur" in ecartees[0]


# --- _qualificateurs_par_assertion (lignes 816-829) ------------------------


class TestQualificateursParAssertion:
    """_qualificateurs_par_assertion — chargement groupé des qualificateurs."""

    async def should_group_qualifiers_by_assertion_id(self) -> None:
        # Arrange — deux assertions, chacune avec deux qualificateurs
        session = _make_mock_session()
        id_a = uuid4()
        id_b = uuid4()
        result_mock = MagicMock()
        result_mock.all.return_value = [
            (id_a, "variable", "rum"),
            (id_a, "operateur", "<"),
            (id_b, "variable", "ph"),
            (id_b, "valeur", "5.5"),
        ]
        session.execute.return_value = result_mock
        engine = KnowledgeEngine(session)

        # Act
        result = await engine._qualificateurs_par_assertion([id_a, id_b])

        # Assert — chaque assertion a son dictionnaire de qualificateurs
        assert result[id_a] == {"variable": "rum", "operateur": "<"}
        assert result[id_b] == {"variable": "ph", "valeur": "5.5"}

    async def should_return_empty_dict_when_no_qualifiers(self) -> None:
        # Arrange — aucune ligne retournée
        session = _make_mock_session()
        result_mock = MagicMock()
        result_mock.all.return_value = []
        session.execute.return_value = result_mock
        engine = KnowledgeEngine(session)

        # Act
        result = await engine._qualificateurs_par_assertion([uuid4()])

        # Assert
        assert result == {}


# --- revise (lignes 719-810 via _source_reference indirect) ----------------
# Les lignes 719-810 correspondent à regles_applicables, déjà couvertes ci-dessus.
# La ligne 591 (_load_historique early return) est aussi exercée par revise()
# quand new_version == 2 et que l'historique contient une seule révision.


class TestReviseLoadHistoriqueEarlyReturn:
    """revise() — _load_historique retourne [] quand la version courante est 1.

    Le chemin revise() appelle _load_historique(connaissance_id, new_version).
    Quand new_version == 2 et qu'une seule Revision existe (version 1), la
    boucle `range(1, 2)` produit un seul élément mais `by_version[2]` n'existe
    pas → l'historique est vide. Ce test couvre aussi la ligne 591 via le
    chemin de revise().
    """

    async def should_return_empty_historique_when_only_one_revision_exists(self) -> None:
        # Arrange
        metadata = _make_valid_metadata()
        resource = MagicMock()
        resource.metadata_json = metadata
        assertion = MagicMock()
        assertion.version = 1
        session = MagicMock()
        session.get = AsyncMock(side_effect=[resource, assertion])
        session.flush = AsyncMock()
        session.add = MagicMock()
        evidence_mock = _make_evidence_mock("B")
        evidence_result = MagicMock()
        evidence_result.scalars.return_value.first.return_value = evidence_mock
        # _load_historique : une seule révision (version 1)
        revision_result = MagicMock()
        revision_result.scalars.return_value.all.return_value = [
            _make_revision_row(1, "Ingestion initiale"),
        ]
        session.execute = AsyncMock(side_effect=[evidence_result, revision_result])
        engine = KnowledgeEngine(session)
        request = KnowledgeRevisionRequest(
            connaissance_id=uuid4(),
            justification="Révision du contenu",
            nouveau_contenu={"valeur": "90 mm"},
        )

        # Act
        result = await engine.revise(request)

        # Assert — version incrémentée, historique vide (pas de version 2 en base)
        assert result.version == 2
        assert result.historique == []

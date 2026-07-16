"""Tests unitaires — Knowledge Engine (legacy v6.1).

TDD : tests écrits avant l'implémentation.
Couvre : ingestion, requête, versionnement, révision (CON-010), filtres.

NOTE : Ces tests référencent l'ancien schéma v6.1 (KnowledgeObject).
La migration v6.2 (RFC-0012, DEC-000023) remplace KnowledgeObject par
Assertion (type 9). Ces tests seront réécrits en Vague 2 quand le
Knowledge Engine sera migré vers le nouveau schéma.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Schéma v6.1 legacy — migration v6.2 (RFC-0012) remplace KnowledgeObject par Assertion")

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
    KnowledgeQueryResult,
    KnowledgeRevisionRequest,
    KnowledgeType,
    QueryType,
)

# --- Fixtures ---

def _make_source(
    type_source: SourceType = SourceType.referentiel_officiel,
    auteur: str = "Rameau et al. (2008)",
    reference: str = "Flore forestière française, tome 1, IDF",
) -> SourceReference:
    return SourceReference(
        type_source=type_source,
        auteur=auteur,
        date_publication="2008",
        reference=reference,
    )


def _make_ingest_request(
    type_: KnowledgeType = KnowledgeType.concept,
    titre: str = "Autécologie du chêne sessile",
    description: str = (
        "Le chêne sessile (Quercus petraea) est une essence post-pionnière de demi-ombre."
    ),
    evidence_level: EvidenceLevel = EvidenceLevel.B,
    statut: KnowledgeStatus = KnowledgeStatus.accepte,
    connaissance_id: None = None,
) -> KnowledgeIngestRequest:
    return KnowledgeIngestRequest(
        connaissance_id=connaissance_id or uuid4(),
        contenu_normalise={
            "parametre": "pH",
            "minimum": 4.5,
            "maximum": 6.5,
            "unite": "unité pH",
        },
        type=type_,
        titre=titre,
        description=description,
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
        evidence_level=evidence_level,
        source=_make_source(),
        statut=statut,
        domaines_validite=[
            DomaineValidite(parametre="pH", minimum=4.5, maximum=6.5, unite="unité pH"),
        ],
        moteurs_consommateurs=["Pedology", "Diagnostic", "Recommendation"],
        mots_cles=["chêne sessile", "pH", "seuil", "acidité"],
    )


@pytest.fixture
def engine() -> KnowledgeEngine:
    """Engine vide pour chaque test (isolation)."""
    return KnowledgeEngine()


# --- Tests d'ingestion ---

def should_ingest_knowledge_when_valid_request(engine: KnowledgeEngine):
    """L'ingestion d'une requête valide doit retourner un KnowledgeObject."""
    req = _make_ingest_request()
    result = engine.ingest(req)
    assert isinstance(result, KnowledgeObject)
    assert result.connaissance_id == req.connaissance_id
    assert result.type == KnowledgeType.concept
    assert result.version == 1
    assert result.historique == []
    assert result.date_integration is not None


def should_raise_error_when_ingesting_duplicate(engine: KnowledgeEngine):
    """L'ingestion d'un UUID déjà présent doit lever une erreur."""
    req = _make_ingest_request()
    engine.ingest(req)
    with pytest.raises(KnowledgeEngineError, match="existe déjà"):
        engine.ingest(req)


def should_raise_error_when_ingesting_refused_knowledge(engine: KnowledgeEngine):
    """L'ingestion d'une connaissance refusée par Evidence doit être rejetée."""
    req = _make_ingest_request(statut=KnowledgeStatus.refuse)
    with pytest.raises(KnowledgeEngineError, match="refusée"):
        engine.ingest(req)


def should_raise_error_when_ingesting_quarantine_knowledge(engine: KnowledgeEngine):
    """L'ingestion d'une connaissance en quarantaine doit être rejetée."""
    req = _make_ingest_request(statut=KnowledgeStatus.quarantine)
    with pytest.raises(KnowledgeEngineError, match="quarantaine"):
        engine.ingest(req)


# --- Tests de requête ---

def should_return_empty_result_when_graph_is_empty(engine: KnowledgeEngine):
    """Une requête sur un graphe vide doit retourner un résultat vide."""
    query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_concept)
    result = engine.query(query)
    assert isinstance(result, KnowledgeQueryResult)
    assert result.connaissances == []
    assert result.total == 0


def should_return_knowledge_when_querying_by_concept(engine: KnowledgeEngine):
    """Une requête par_concept doit retourner les connaissances de type concept."""
    # Ingest un concept et un seuil
    concept_req = _make_ingest_request(
        type_=KnowledgeType.concept, titre="Autécologie du chêne sessile"
    )
    seuil_req = _make_ingest_request(
        type_=KnowledgeType.seuil, titre="pH optimal du chêne sessile"
    )
    engine.ingest(concept_req)
    engine.ingest(seuil_req)

    query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_concept)
    result = engine.query(query)
    assert result.total == 1
    assert result.connaissances[0].type == KnowledgeType.concept
    assert result.connaissances[0].titre == "Autécologie du chêne sessile"


def should_filter_by_evidence_min_when_provided(engine: KnowledgeEngine):
    """Le filtre evidence_min doit exclure les connaissances de niveau inférieur."""
    # Ingest B et D
    req_b = _make_ingest_request(evidence_level=EvidenceLevel.B, titre="Connaissance niveau B")
    req_d = _make_ingest_request(evidence_level=EvidenceLevel.D, titre="Connaissance niveau D")
    engine.ingest(req_b)
    engine.ingest(req_d)

    # Requête avec evidence_min=B → ne doit retourner que B (B > D)
    query = KnowledgeQuery(
        requete_id=uuid4(),
        type=QueryType.par_concept,
        evidence_min=EvidenceLevel.B,
    )
    result = engine.query(query)
    # A=6, B=5, C=4, D=3, E=2, F=1
    # evidence_min=B (rank 5) → seulement B (rank 5) et au-dessus
    assert result.total == 1
    assert result.connaissances[0].evidence_level == EvidenceLevel.B


def should_filter_by_mots_cles_when_par_concept_with_filter(engine: KnowledgeEngine):
    """Le filtre par mots-clés doit restreindre les résultats."""
    req1 = _make_ingest_request(titre="pH chêne", )
    req2 = _make_ingest_request(titre="Altitude hêtre")
    req2.mots_cles = ["hêtre", "altitude"]
    engine.ingest(req1)
    engine.ingest(req2)

    query = KnowledgeQuery(
        requete_id=uuid4(),
        type=QueryType.par_concept,
        filtres={"mots_cles": ["hêtre"]},
    )
    result = engine.query(query)
    assert result.total == 1
    assert "hêtre" in result.connaissances[0].mots_cles


def should_paginate_results_when_page_size_exceeded(engine: KnowledgeEngine):
    """La pagination doit retourner seulement la page demandée."""
    for i in range(5):
        req = _make_ingest_request(titre=f"Connaissance {i}")
        engine.ingest(req)

    query = KnowledgeQuery(
        requete_id=uuid4(),
        type=QueryType.par_concept,
        page=1,
        page_size=2,
    )
    result = engine.query(query)
    assert result.total == 5
    assert len(result.connaissances) == 2
    assert result.page == 1
    assert result.page_size == 2


# --- Tests de révision (CON-010) ---

def should_create_new_version_when_revising(engine: KnowledgeEngine):
    """La révision doit incrémenter la version et archiver l'ancienne (CON-010)."""
    req = _make_ingest_request()
    original = engine.ingest(req)

    revision = KnowledgeRevisionRequest(
        connaissance_id=req.connaissance_id,
        justification="Nouvelle publication 2028 invalide le seuil -20°C",
        nouveau_contenu={"parametre": "pH", "minimum": 4.0, "maximum": 6.0, "unite": "unité pH"},
    )
    revised = engine.revise(revision)

    assert revised.version == 2
    assert len(revised.historique) == 1
    assert revised.historique[0].version == 1
    assert revised.historique[0].justification == (
        "Nouvelle publication 2028 invalide le seuil -20°C"
    )
    assert revised.contenu != original.contenu


def should_raise_not_found_when_revising_unknown_knowledge(engine: KnowledgeEngine):
    """La révision d'un UUID inexistant doit lever KnowledgeNotFoundError."""
    revision = KnowledgeRevisionRequest(
        connaissance_id=uuid4(),
        justification="Test",
        nouveau_contenu={"test": True},
    )
    with pytest.raises(KnowledgeNotFoundError):
        engine.revise(revision)


def should_raise_error_when_revising_without_changes(engine: KnowledgeEngine):
    """La révision sans aucun changement doit lever une erreur."""
    req = _make_ingest_request()
    engine.ingest(req)

    revision = KnowledgeRevisionRequest(
        connaissance_id=req.connaissance_id,
        justification="Test sans changement",
    )
    with pytest.raises(KnowledgeEngineError, match="Aucun champ modifié"):
        engine.revise(revision)


def should_preserve_history_across_multiple_revisions(engine: KnowledgeEngine):
    """L'historique doit accumuler toutes les versions (CON-010)."""
    req = _make_ingest_request()
    engine.ingest(req)

    for i in range(3):
        revision = KnowledgeRevisionRequest(
            connaissance_id=req.connaissance_id,
            justification=f"Révision {i + 1}",
            nouveau_contenu={"version": i + 1},
        )
        engine.revise(revision)

    # Version 4, historique de 3 entrées (v1, v2, v3)
    query = KnowledgeQuery(
        requete_id=uuid4(),
        type=QueryType.par_concept,
        filtres={"connaissance_id": str(req.connaissance_id)},
    )
    result = engine.query(query)
    assert result.total == 1
    ko = result.connaissances[0]
    assert ko.version == 4
    assert len(ko.historique) == 3


# --- Tests du graphe ---

def should_return_graph_version_when_queried(engine: KnowledgeEngine):
    """Le résultat doit contenir une version de graphe non vide."""
    query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_concept)
    result = engine.query(query)
    assert len(result.version_graph) > 0


def should_return_correct_count_when_multiple_types_ingested(engine: KnowledgeEngine):
    """Le total doit refléter le nombre exact de correspondances."""
    for type_ in KnowledgeType:
        req = _make_ingest_request(type_=type_, titre=f"Test {type_.value}")
        engine.ingest(req)

    query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_concept)
    result = engine.query(query)
    # par_concept filtre par type=concept
    assert result.total == 1


def should_retrieve_by_id_when_filtering(engine: KnowledgeEngine):
    """Le filtre connaissance_id doit retourner la connaissance exacte."""
    req = _make_ingest_request()
    engine.ingest(req)

    query = KnowledgeQuery(
        requete_id=uuid4(),
        type=QueryType.par_concept,
        filtres={"connaissance_id": str(req.connaissance_id)},
    )
    result = engine.query(query)
    assert result.total == 1
    assert result.connaissances[0].connaissance_id == req.connaissance_id


def should_return_engine_version():
    """engine_version doit retourner une version non vide."""
    assert len(KnowledgeEngine.version()) > 0


def should_return_object_count_when_stats_called(engine: KnowledgeEngine):
    """stats doit retourner le nombre d'objets dans le graphe."""
    assert engine.stats()["total_objects"] == 0
    engine.ingest(_make_ingest_request())
    assert engine.stats()["total_objects"] == 1


def should_reject_empty_justification_in_revision(engine: KnowledgeEngine):
    """La justification ne peut pas être vide (validée par Pydantic)."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        KnowledgeRevisionRequest(
            connaissance_id=uuid4(),
            justification="",
            nouveau_contenu={"test": True},
        )

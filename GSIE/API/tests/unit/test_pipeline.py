"""Tests d'intégration — pipeline Evidence → Knowledge (Semaine 4).

Teste la tranche verticale prioritaire : soumission → qualification →
ingestion → requête → révision. Valide que les deux moteurs s'enchaînent
correctement et que les garanties constitutionnelles sont respectées.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.engines.evidence.schemas import (
    ContentType,
    EvidenceLevel,
    RawKnowledgeSubmission,
    SourceReference,
    SourceType,
)
from gsie_api.engines.knowledge.engine import KnowledgeEngine
from gsie_api.engines.knowledge.schemas import (
    DomaineScientifique,
    KnowledgeQuery,
    KnowledgeType,
    QueryType,
)
from gsie_api.engines.pipeline import EvidenceKnowledgePipeline, PipelineResult

app = create_app()
client = TestClient(app)

_ACCESS_TOKEN = create_access_token(subject="test-pipeline")
_AUTH_HEADERS = {"Authorization": f"Bearer {_ACCESS_TOKEN}"}


@pytest.fixture
def pipeline() -> EvidenceKnowledgePipeline:
    """Pipeline frais pour chaque test (isolation)."""
    return EvidenceKnowledgePipeline(KnowledgeEngine())


def _make_submission(
    source_type: SourceType = SourceType.peer_reviewed,
    content_type: ContentType = ContentType.publication,
) -> RawKnowledgeSubmission:
    """Crée une soumission valide pour les tests du pipeline."""
    return RawKnowledgeSubmission(
        soumission_id=uuid4(),
        type_contenu=content_type,
        contenu={
            "definition": "Réserve utile en eau (RUM)",
            "valeur": "80 mm minimum pour le hêtre",
        },
        source_candidate=SourceReference(
            type_source=source_type,
            auteur="Rameau et al. (2008)",
            date_publication="2008",
            reference="Flore forestière française, tome 1, IDF",
        ),
        date_soumission=datetime.now(UTC),
        soumetteur="test_pipeline",
    )


# --- Tests du pipeline (niveau engine) ---

def should_ingest_when_evidence_accepts(pipeline: EvidenceKnowledgePipeline):
    """Le pipeline doit ingérer quand l'Evidence Engine accepte (niveau B)."""
    sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
    result = pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="RUM du hêtre",
        description="Réserve utile en eau minimale pour le hêtre.",
        domaine_scientifique=DomaineScientifique.pedologie,
        mots_cles=["hêtre", "RUM", "eau"],
    )
    assert result.ingested
    assert result.status == "ingested"
    assert result.knowledge_object is not None
    assert result.knowledge_object.version == 1
    assert result.qualified.evidence_level == EvidenceLevel.B


def should_not_ingest_when_evidence_refuses(pipeline: EvidenceKnowledgePipeline):
    """Le pipeline ne doit pas ingérer quand l'Evidence refuse (niveau F)."""
    sub = _make_submission(SourceType.observation_terrain, ContentType.observation)
    result = pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="Test refuse",
        description="Description test.",
        domaine_scientifique=DomaineScientifique.pedologie,
    )
    assert not result.ingested
    assert result.status == "refused"
    assert result.knowledge_object is None
    assert result.reason is not None


def should_not_ingest_when_evidence_quarantines(pipeline: EvidenceKnowledgePipeline):
    """Le pipeline ne doit pas ingérer quand l'Evidence met en quarantaine (D)."""
    sub = _make_submission(SourceType.expert_identifie, ContentType.expert)
    result = pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="Test quarantine",
        description="Description test.",
        domaine_scientifique=DomaineScientifique.pedologie,
    )
    assert not result.ingested
    assert result.status == "quarantined"
    assert result.knowledge_object is None


def should_allow_query_after_pipeline_ingest(pipeline: EvidenceKnowledgePipeline):
    """Après ingestion via le pipeline, la requête doit trouver la connaissance."""
    sub = _make_submission(SourceType.referentiel_officiel, ContentType.referentiel)
    pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="pH optimal du chêne",
        description="Le chêne sessile préfère les sols acides.",
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
        mots_cles=["chêne", "pH"],
    )

    query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_concept)
    result = pipeline.query(query)
    assert result.total >= 1
    assert result.connaissances[0].titre == "pH optimal du chêne"


def should_allow_revision_after_pipeline_ingest(pipeline: EvidenceKnowledgePipeline):
    """Après ingestion, la révision doit créer une version 2 (CON-010)."""
    sub = _make_submission(SourceType.referentiel_officiel, ContentType.referentiel)
    result = pipeline.process(
        sub,
        type_=KnowledgeType.seuil,
        titre="Seuil pH chêne",
        description="pH 4,5-6,5 pour le chêne sessile.",
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
    )
    assert result.ingested
    assert result.knowledge_object is not None

    revised = pipeline.revise(
        connaissance_id=result.knowledge_object.connaissance_id,
        justification="Nouvelle étude 2028 élargit la gamme à 4,0-7,0",
        nouveau_contenu={"parametre": "pH", "minimum": 4.0, "maximum": 7.0},
    )
    assert revised.version == 2
    assert len(revised.historique) == 1


def should_preserve_evidence_level_in_knowledge(pipeline: EvidenceKnowledgePipeline):
    """Le niveau de preuve de l'Evidence doit être préservé dans le Knowledge."""
    sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
    result = pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="Test préservation evidence",
        description="Description test.",
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
    )
    assert result.ingested
    assert result.knowledge_object is not None
    assert result.knowledge_object.evidence_level == result.qualified.evidence_level


def should_preserve_source_in_knowledge(pipeline: EvidenceKnowledgePipeline):
    """La source de l'Evidence doit être préservée dans le Knowledge."""
    sub = _make_submission()
    result = pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="Test préservation source",
        description="Description test.",
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
    )
    assert result.ingested
    assert result.knowledge_object is not None
    assert result.knowledge_object.source == result.qualified.source


def should_return_pipeline_result_type(pipeline: EvidenceKnowledgePipeline):
    """Le pipeline doit retourner un PipelineResult."""
    sub = _make_submission()
    result = pipeline.process(
        sub,
        type_=KnowledgeType.concept,
        titre="Test type",
        description="Description test.",
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
    )
    assert isinstance(result, PipelineResult)


# --- Tests E2E via l'API ---

def should_complete_full_pipeline_via_api():
    """Le pipeline complet doit fonctionner via les endpoints API.

    Étapes :
    1. POST /evidence/evaluate → qualification (B, accepte)
    2. POST /knowledge/ingest → ingestion dans le graphe
    3. POST /knowledge/query → vérifier que la connaissance est présente
    """
    # Reset l'engine
    from gsie_api.engines.knowledge.router import _engine
    _engine._store.clear()

    # Étape 1 : qualification par l'Evidence Engine
    sub = RawKnowledgeSubmission(
        soumission_id=uuid4(),
        type_contenu=ContentType.publication,
        contenu={"definition": "RUM du hêtre", "minimum": 80},
        source_candidate=SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Rameau et al. (2008)",
            date_publication="2008",
            reference="Flore forestière française, tome 1, IDF",
        ),
        date_soumission=datetime.now(UTC),
        soumetteur="test_e2e",
    )
    evidence_resp = client.post(
        "/api/v1/evidence/evaluate",
        json=sub.model_dump(mode="json"),
        headers=_AUTH_HEADERS,
    )
    assert evidence_resp.status_code == 200
    evidence_data = evidence_resp.json()
    assert evidence_data["statut"] == "accepte"
    assert evidence_data["evidence_level"] == "B"

    # Étape 2 : ingestion dans le Knowledge Engine
    ingest_payload = {
        "connaissance_id": evidence_data["connaissance_id"],
        "contenu_normalise": evidence_data["contenu_normalise"],
        "type": "concept",
        "titre": "RUM du hêtre",
        "description": "Réserve utile en eau minimale pour le hêtre (80 mm).",
        "domaine_scientifique": "pedologie",
        "evidence_level": evidence_data["evidence_level"],
        "source": evidence_data["source"],
        "statut": evidence_data["statut"],
        "mots_cles": ["hêtre", "RUM", "eau"],
    }
    ingest_resp = client.post(
        "/api/v1/knowledge/ingest",
        json=ingest_payload,
        headers=_AUTH_HEADERS,
    )
    assert ingest_resp.status_code == 201
    ingest_data = ingest_resp.json()
    assert ingest_data["version"] == 1

    # Étape 3 : requête sur le graphe
    query_payload = {
        "requete_id": str(uuid4()),
        "type": "par_concept",
    }
    query_resp = client.post(
        "/api/v1/knowledge/query",
        json=query_payload,
        headers=_AUTH_HEADERS,
    )
    assert query_resp.status_code == 200
    query_data = query_resp.json()
    assert query_data["total"] >= 1
    found = [k for k in query_data["connaissances"] if k["titre"] == "RUM du hêtre"]
    assert len(found) == 1
    assert found[0]["evidence_level"] == "B"


def should_complete_full_pipeline_with_revision_via_api():
    """Pipeline complet avec révision : evaluate → ingest → revise → query v2."""
    from gsie_api.engines.knowledge.router import _engine
    _engine._store.clear()

    # Étape 1 : qualification
    sub = RawKnowledgeSubmission(
        soumission_id=uuid4(),
        type_contenu=ContentType.referentiel,
        contenu={"parametre": "pH", "minimum": 4.5, "maximum": 6.5},
        source_candidate=SourceReference(
            type_source=SourceType.referentiel_officiel,
            auteur="INRAE (2008)",
            reference="Référentiel pédologique français",
        ),
        date_soumission=datetime.now(UTC),
        soumetteur="test_e2e_revision",
    )
    evidence_resp = client.post(
        "/api/v1/evidence/evaluate",
        json=sub.model_dump(mode="json"),
        headers=_AUTH_HEADERS,
    )
    evidence_data = evidence_resp.json()

    # Étape 2 : ingestion
    ingest_payload = {
        "connaissance_id": evidence_data["connaissance_id"],
        "contenu_normalise": evidence_data["contenu_normalise"],
        "type": "seuil",
        "titre": "pH optimal chêne sessile",
        "description": "pH 4,5-6,5 pour le chêne sessile.",
        "domaine_scientifique": "ecologie_forestiere_et_stationnelle",
        "evidence_level": evidence_data["evidence_level"],
        "source": evidence_data["source"],
        "statut": evidence_data["statut"],
    }
    ingest_resp = client.post(
        "/api/v1/knowledge/ingest",
        json=ingest_payload,
        headers=_AUTH_HEADERS,
    )
    assert ingest_resp.status_code == 201
    connaissance_id = ingest_resp.json()["connaissance_id"]

    # Étape 3 : révision (CON-010)
    revision_payload = {
        "connaissance_id": str(connaissance_id),
        "justification": "Nouvelle étude 2028 élargit la gamme à 4,0-7,0",
        "nouveau_contenu": {"parametre": "pH", "minimum": 4.0, "maximum": 7.0},
    }
    revise_resp = client.post(
        "/api/v1/knowledge/revise",
        json=revision_payload,
        headers=_AUTH_HEADERS,
    )
    assert revise_resp.status_code == 200
    revised_data = revise_resp.json()
    assert revised_data["version"] == 2
    assert len(revised_data["historique"]) == 1
    assert revised_data["historique"][0]["version"] == 1

    # Étape 4 : requête — doit trouver la version 2
    query_payload = {
        "requete_id": str(uuid4()),
        "type": "par_domaine",
        "filtres": {
            "connaissance_id": str(connaissance_id),
            "domaine_scientifique": "ecologie_forestiere_et_stationnelle",
        },
    }
    query_resp = client.post(
        "/api/v1/knowledge/query",
        json=query_payload,
        headers=_AUTH_HEADERS,
    )
    assert query_resp.status_code == 200
    query_data = query_resp.json()
    assert query_data["total"] == 1
    assert query_data["connaissances"][0]["version"] == 2
    assert query_data["connaissances"][0]["contenu"]["minimum"] == 4.0


def should_not_ingest_refused_knowledge_via_api():
    """Une connaissance refusée par Evidence ne doit pas être ingérée."""
    from gsie_api.engines.knowledge.router import _engine
    _engine._store.clear()

    # Soumission qui sera refusée (observation terrain → F → refuse)
    sub = RawKnowledgeSubmission(
        soumission_id=uuid4(),
        type_contenu=ContentType.observation,
        contenu={"observation": "Test"},
        source_candidate=SourceReference(
            type_source=SourceType.observation_terrain,
            auteur="Observateur test",
            reference="Obs-2026-001",
        ),
        date_soumission=datetime.now(UTC),
        soumetteur="test_e2e_refuse",
    )
    evidence_resp = client.post(
        "/api/v1/evidence/evaluate",
        json=sub.model_dump(mode="json"),
        headers=_AUTH_HEADERS,
    )
    evidence_data = evidence_resp.json()
    assert evidence_data["statut"] == "refuse"

    # Tenter d'ingérer → doit échouer
    ingest_payload = {
        "connaissance_id": evidence_data["connaissance_id"],
        "contenu_normalise": evidence_data["contenu_normalise"],
        "type": "concept",
        "titre": "Test refuse",
        "description": "Description test.",
        "domaine_scientifique": "ecologie_forestiere_et_stationnelle",
        "evidence_level": evidence_data["evidence_level"],
        "source": evidence_data["source"],
        "statut": evidence_data["statut"],
    }
    ingest_resp = client.post(
        "/api/v1/knowledge/ingest",
        json=ingest_payload,
        headers=_AUTH_HEADERS,
    )
    assert ingest_resp.status_code == 400

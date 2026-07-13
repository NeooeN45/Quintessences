"""Engine Knowledge — placeholder (implémentation semaine 3, Rust + pyo3).

Responsabilité : centraliser, structurer et versionner les connaissances
scientifiques qualifiées dans un graphe interrogeable.

État de l'art (Fable 5) : Neo4j, Apache Jena/Fuseki, Protégé/OWL 2,
W3C PROV-O, RDF2Vec, GraphRAG.
"""

from fastapi import APIRouter, Request

from gsie_api.shared.schemas import EngineStatusResponse

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/status", response_model=EngineStatusResponse)
async def knowledge_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Knowledge — non implémenté (semaine 3)."""
    return EngineStatusResponse(
        engine="knowledge",
        status="not_implemented",
        planned_week=3,
        language="rust+pyo3",
    )

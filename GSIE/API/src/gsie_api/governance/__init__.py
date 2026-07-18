"""Registre transverse de gouvernance scientifique (RFC-0014/0015, corpus sylvicole SCI-001)."""

from gsie_api.governance.source_registry import (
    SCIENTIFIC_SOURCES,
    ScientificSourceEntry,
    SourceIngestionForbiddenError,
    SourceLegalStatus,
    get_source,
    require_ingestible,
)

__all__ = [
    "SCIENTIFIC_SOURCES",
    "ScientificSourceEntry",
    "SourceIngestionForbiddenError",
    "SourceLegalStatus",
    "get_source",
    "require_ingestible",
]

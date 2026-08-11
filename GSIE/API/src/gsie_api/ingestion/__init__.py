"""Module d'ingestion en lot — pipeline bulk pour données externes.

Ce module contient les services d'ingestion massive :
- `BulkIngestService` : création de N resources en une transaction.
- `DatasetManifest` : porte locale et juridique avant toute copie.
- (futur) `BulkEvidencePipeline` : qualification + ingestion en lot.

L'ingestion unitaire reste disponible via `ResourceService.create`.
"""

from gsie_api.ingestion.manifest import (
    MANIFEST_VERSION,
    DatasetManifest,
    DatasetManifestEntry,
    ManifestDistribution,
    ManifestOperation,
    load_manifest,
    manifest_preview,
)

__all__ = [
    "MANIFEST_VERSION",
    "DatasetManifest",
    "DatasetManifestEntry",
    "ManifestDistribution",
    "ManifestOperation",
    "load_manifest",
    "manifest_preview",
]

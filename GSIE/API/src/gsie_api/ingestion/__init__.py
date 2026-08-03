"""Module d'ingestion en lot — pipeline bulk pour données externes.

Ce module contient les services d'ingestion massive :
- `BulkIngestService` : création de N resources en une transaction.
- (futur) `BulkEvidencePipeline` : qualification + ingestion en lot.

L'ingestion unitaire reste disponible via `ResourceService.create`.
"""

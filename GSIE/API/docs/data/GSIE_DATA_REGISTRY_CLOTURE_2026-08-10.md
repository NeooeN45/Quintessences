# Clôture technique de la tranche Data Registry

**Date :** 10 août 2026

**Statut :** prête techniquement, scheduler installé mais non activé

**Révision PostgreSQL :** `20260810_0047`

## Portes clôturées

1. `scripts/validate_data_registry_release.py` reproduit les trois campagnes
   de référence et produit une preuve JSON horodatée.
2. Le job CI `Data Registry (PostgreSQL + MinIO)` construit l'image de base
   réelle, migre une base jetable et conserve les rapports comme artefacts.
3. `DataRegistryHealthScheduler` exécute des contrôles bornés, sous verrou
   Redis distribué, et persiste l'historique sans remplacer les observations.
4. `FETCH_QUALIFICATION.json` porte une décision explicite pour GBIF, IGN,
   SoilGrids et Météo-France. Les quatre décisions sont actuellement fermées.
5. Les images `api-db`, `api-api` et `api-outbox-worker` ont été reconstruites,
   puis API et outbox ont été recréées sans suppression des volumes.
6. Le smoke réel a confirmé `/health`, `/ready`, le head Alembic, le rejeu
   idempotent du manifeste et un round-trip MinIO avec nettoyage.

## Preuve locale finale

| Contrôle | Résultat |
|---|---:|
| Data Registry | 151/151 |
| P0/P1 | 103/103 |
| Infrastructure/lifespan | 121/121 |
| Ruff | aucune erreur |
| mypy strict `gsie_api/data` | aucune erreur |
| API `/health` et `/ready` | `healthy` |
| Manifeste réel | 4 entrées, rejeu 0 création/0 mise à jour |
| MinIO réel | 77 octets, SHA-256 identique, objet supprimé |
| `FETCH` fournisseur | aucun téléchargement brut activé |

Le rapport de smoke local est volontairement ignoré par Git : la CI produit
la preuve durable correspondante à chaque exécution. La configuration secrète
reste chiffrée après les opérations Docker.

## Activation opérateur du scheduler

Le code est prêt, mais l'activation déclenche des requêtes périodiques vers des
services tiers. Elle reste donc une décision opérateur distincte :

```text
GSIE_DATA_REGISTRY_HEALTH_SCHEDULER_ENABLED=true
```

Avant activation sur serveur, vérifier la cadence, les quotas fournisseurs,
la confiance TLS et les alertes Prometheus. Le verrou Redis garantit qu'un
seul worker persiste une campagne, même avec plusieurs workers Gunicorn.

## Tranche suivante

- calcul et persistance de `QualityAssessment` ;
- levée documentée des blocages `FETCH`, source par source ;
- worker de téléchargement avec allowlist, timeout, taille maximale et arrêt
  anticipé ;
- checksum SHA-256, création du `RAW DataAsset`, puis normalisation traçable ;
- aucun passage en production sans preuve CI PostgreSQL/MinIO reproductible.

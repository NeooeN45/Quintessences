# Manifeste d'ingestion Data Registry — Phase 6

**Statut :** validation et application transactionnelle livrées, sans copie d'octets

**Date :** 2026-08-10
**Contrat :** RFC-0038 v1.2.0 / DEC-000059 / SCI-001

## 1. Rôle

`GSIE/DATASETS/REGISTRY_MANIFEST.json` est le point d'entrée contrôlé du
catalogue Data Registry. Il décrit les datasets déjà consommés par les
adapters GBIF, IGN, SoilGrids et Météo-France. La version actuelle contient
uniquement des entrées `metadata_only` : sa validation n'appelle aucun
fournisseur et ne télécharge aucun fichier. Son application explicite crée
désormais les métadonnées de catalogue en base, sans copier d'octets.

Le manifeste est donc rejouable et vérifiable même lorsque Docker ou le réseau
externe sont indisponibles.

## 2. Portes appliquées

Le modèle `gsie_api.ingestion.manifest.DatasetManifest` impose :

- une identité `slug`/`version` unique dans le document ;
- le vocabulaire de domaines versionné de RFC-0038 ;
- une source connue de `SCIENTIFIC_SOURCES` (SCI-001) ;
- une licence non vide et strictement identique à celle du registre juridique ;
- des URLs HTTPS sans identifiant, query, fragment ou adresse IP privée ;
- un statut de découverte/qualification, sans promotion silencieuse en
  `validated`, `staging` ou `production` ;
- une copie (`archive_copy`) uniquement si `require_ingestible` autorise
  effectivement le régime `OPEN_COPY` ;
- un pack hors ligne uniquement si la copie et la redistribution hors ligne
  sont autorisées par la source.

Une source ONF/CNPF ou ClimEssences peut donc être décrite en
`metadata_only`, mais ne peut pas franchir la porte `archive_copy` sans
évolution juridique explicite du registre.

## 3. Validation reproductible

Depuis `GSIE/API` :

```powershell
.\.venv\Scripts\python.exe scripts\validate_dataset_manifest.py `
  ..\DATASETS\REGISTRY_MANIFEST.json
```

La commande est en lecture seule et produit un aperçu normalisé. Pour une
sortie machine :

```powershell
.\.venv\Scripts\python.exe scripts\validate_dataset_manifest.py `
  ..\DATASETS\REGISTRY_MANIFEST.json --json
```

Les tests `tests/unit/test_dataset_manifest.py` couvrent les doublons, les
URLs dangereuses, la dérive de licence, les sources restreintes, les domaines
inconnus et les règles de pack offline. Aucun test n'ouvre le réseau.

## 4. Application et suite

Le service d'application explicite, idempotent et auditable est livré avec un
`dry-run` par défaut. Il crée la provenance, les droits, le dataset, sa
version, sa distribution et sa citation. Les contrôles réels des quatre
adapters peuvent être persistés dans `DatasetHealth` par un fichier séparé.

Cette application reste distincte d'une ingestion d'octets. Un `DataAsset`
n'est accepté que pour `archive_copy`, après archivage, taille et checksum
explicitement fournis. Les quatre sources restent `metadata_only` tant que la
capacité `FETCH` et les droits de copie ne sont pas qualifiés. Procédure et
preuves : `GSIE_DATA_REGISTRY_MANIFEST_APPLICATION_2026-08-10.md`.

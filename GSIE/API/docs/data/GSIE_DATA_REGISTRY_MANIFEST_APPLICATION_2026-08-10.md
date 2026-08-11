# Application transactionnelle du manifeste Data Registry

**Date :** 10 août 2026

**Statut :** implémentée et vérifiée sur PostgreSQL/MinIO réels

**Contrat :** RFC-0038 v1.2.0 / DEC-000059 / SCI-001

## Résultat livré

Le manifeste `GSIE/DATASETS/REGISTRY_MANIFEST.json` peut désormais être
prévisualisé puis appliqué de manière transactionnelle et idempotente. Pour
chaque entrée, le service projette la chaîne suivante :

`Agent → Source → EntityAlias → DataRightsStatement → Dataset → DatasetVersion → Distribution → Citation`

Les identifiants GSIE sont dérivés d'identités stables et chaque création
passe par la table racine `resource` et une révision v1. Une seconde
application du même document ne crée ni ressource, ni révision, ni contrôle de
santé supplémentaire.

Le paquet `gsie_api.data` reste volontairement sans réexport. Les dépendances
sont importées depuis leurs modules explicites, ce qui garantit que
`ResourceService` peut être chargé avant le Data Registry sans cycle.

## Commandes opérateur

Depuis `GSIE/API`, le mode par défaut est sans écriture :

```powershell
.\.venv\Scripts\python.exe scripts\apply_dataset_manifest.py `
  ..\DATASETS\REGISTRY_MANIFEST.json --json
```

L'écriture nécessite l'option explicite `--apply` :

```powershell
.\.venv\Scripts\python.exe scripts\apply_dataset_manifest.py `
  ..\DATASETS\REGISTRY_MANIFEST.json --apply --json
```

La santé réelle des quatre fournisseurs est collectée séparément. Le fichier
produit ne contient aucun secret et peut être inspecté avant persistance :

```powershell
.\.venv\Scripts\python.exe scripts\collect_manifest_health.py `
  ..\DATASETS\REGISTRY_MANIFEST.json `
  --output manifest-health.json

.\.venv\Scripts\python.exe scripts\apply_dataset_manifest.py `
  ..\DATASETS\REGISTRY_MANIFEST.json `
  --health-json manifest-health.json --apply --json
```

Sous inspection TLS d'entreprise, `SSL_CERT_FILE` doit désigner l'autorité de
confiance approuvée. La validation TLS n'est jamais désactivée.

## Invariants de sûreté

- `dry-run` est le comportement par défaut ; l'application réelle tient dans
  une transaction portée par l'appelant ;
- une réapplication ne rétrograde jamais une `DatasetVersion` déjà qualifiée ;
- les champs immuables d'une version ou d'un actif divergent provoquent un
  échec, pas un écrasement ;
- `DatasetHealth` est append-only, mais le rejeu du même snapshot est
  dédupliqué par une identité stable incluant distribution et observation ;
- une entrée `metadata_only` refuse tout `DataAsset` et ne copie aucun octet ;
- `archive_copy` exige un actif déjà archivé, avec taille, URI, horodatage et
  checksum explicitement fournis ;
- les droits et licences viennent de SCI-001 ; aucune permission de copie,
  redistribution ou entraînement IA n'est déduite ;
- aucun appel fournisseur ni téléchargement implicite n'est réalisé par le
  service d'application.

Le backend S3 réutilise maintenant un client aiobotocore et son pool HTTP par
instance. Le singleton applicatif est fermé au shutdown FastAPI. Les fichiers
temporaires locaux et S3 sont fermés sur toute erreur, et l'appelant reste
responsable de fermer un fichier retourné avec succès.

## Preuves du 10 août 2026

- première application : 4 entrées et 32 ressources créées ;
- rejeu du manifeste : 0 création, 0 mise à jour ;
- contrôle réel : GBIF, IGN, Météo-France et SoilGrids `healthy` ;
- rejeu E2E après mutualisation S3 : 4/4, round-trip checksum réussi,
  `cleanup=ok` et fermeture explicite du client ;
- persistance : 4 lignes `DatasetHealth`, rejeu identique à 0 création ;
- migration active : `20260810_0047`, enums `dataset_status` et
  `dataset_health_status` dans `public` ;
- base jetable : `upgrade head → downgrade 20260809_0044 → upgrade head`
  réussi, puis base supprimée ;
- tests : campagne Data Registry élargie 151/151, campagne P0/P1 103/103,
  cycle de vie/infrastructure 121/121 ;
- Ruff et mypy strict : aucune erreur sur le code neuf et corrigé.

La commande unique ci-dessous reproduit ces trois campagnes et écrit leur
sortie, durée, environnement et verdict dans un rapport JSON horodaté :

```powershell
uv run python scripts/validate_data_registry_release.py
```

La CI possède en plus le job obligatoire `Data Registry (PostgreSQL + MinIO)`.
Il migre une base PostgreSQL/PostGIS/AGE jetable, démarre MinIO, rejoue les
campagnes, applique deux fois le manifeste et vérifie un round-trip S3 avec
SHA-256 et suppression finale. Les deux rapports JSON sont conservés trente
jours comme artefacts GitHub Actions.

## Limites et prochaine tranche

Les quatre entrées actuelles restent `metadata_only`. Le registre
`GSIE/DATASETS/FETCH_QUALIFICATION.json` documente désormais leur décision
source par source et `fetch_policy.py` ferme l'accès par défaut. Aucune source
n'est activée : GBIF attend la résolution de la licence du jeu constitutif,
IGN et SoilGrids leurs bornes techniques, Météo-France ses produits, secrets
et quotas. Une future activation exigera hôtes, types MIME, taille maximale,
SHA-256 et revue humaine horodatée.

Le scheduler de santé est livré avec verrou Redis propriétaire, TTL,
concurrence bornée, métriques Prometheus et historique `DatasetHealth`. Il est
désactivé par défaut et n'a pas été activé implicitement lors du redéploiement.
La prochaine tranche porte donc sur les évaluations complètes
`QualityAssessment`, puis seulement sur un worker `FETCH` borné pour les
sources dont tous les blocages auront été levés.

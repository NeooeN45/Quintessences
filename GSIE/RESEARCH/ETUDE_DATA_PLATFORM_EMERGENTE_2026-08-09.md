# Étude des technologies émergentes pour la plateforme de données GSIE — [GSIE-DATA-RESEARCH-0001] [v1.0.0]

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-DATA-RESEARCH-0001 |
| **Statut** | Draft |
| **Version** | 1.0.0 |
| **Date** | 2026-08-09 |
| **Périmètre** | Ingestion, catalogue, stockage, normalisation et distribution de données environnementales |
| **Dépôts concernés** | `GSIE/API/` et `Forge/` |
| **Document complété** | `GSIE/API/docs/data/GSIE_DATA_ARCHITECTURE_AUDIT.md` |
| **Décision** | Aucune adoption automatique ; qualification avant RFC-0038 |

## 1. Résumé exécutif

La veille externe confirme que la meilleure stratégie pour GSIE n’est pas de choisir un moteur unique, mais de composer une plateforme de données ouverte autour de standards interopérables : **STAC, COG, GeoParquet, COPC, Zarr et Apache Parquet**.

Les technologies les plus prometteuses sont complémentaires : **S3/MinIO** pour les octets, **PostgreSQL/PostGIS** pour le registre et les requêtes métier, **DuckDB ou DataFusion** pour l’analytique fichier, **Iceberg** pour le versionnement de tables analytiques à grande échelle, **Pangeo/Xarray/Zarr** pour les cubes spatio-temporels et **cuDF/Dask-cuDF/cuSpatial** pour l’accélération GPU optionnelle.

Aucune solution externe ne doit devenir une seconde source de vérité. GSIE conserve l’identité, la licence, la provenance, l’Evidence Level A–F et le statut de publication ; les catalogues STAC et les tables analytiques sont des projections spécialisées.

## 2. Méthode et critères

Les solutions ont été recherchées dans :

- dépôts GitHub officiels ou maintenus par des organisations reconnues ;
- documentations officielles ;
- retours d’architecture d’organisations manipulant des archives géospatiales massives ;
- outils déjà compatibles avec Python, Rust, PostgreSQL, S3, Arrow ou les standards OGC.

Critères de qualification :

| Critère | Question |
|---|---|
| Maturité | Le projet est-il exploitable ou seulement expérimental ? |
| Interopérabilité | Peut-il coexister avec PostgreSQL, S3, Python et Rust ? |
| Géospatial | Gère-t-il CRS, emprises, rasters, vecteurs, LiDAR et temps ? |
| Versionnement | Les versions et snapshots sont-ils reproductibles ? |
| Performance | Lit-il seulement les colonnes, tuiles ou partitions utiles ? |
| Gouvernance | Les licences et droits sont-ils compatibles avec GSIE ? |
| Exploitation | L’équipe peut-elle l’opérer sans créer une plateforme disproportionnée ? |
| Réversibilité | Peut-on le retirer sans réécrire les datasets ? |

## 3. Trouvailles prioritaires

### 3.1 STAC — standard de découverte géospatiale

**STAC** décrit des actifs spatio-temporels : images satellite, orthophotos, LiDAR, rasters, vidéos et données dérivées. Il sépare :

- le catalogue ;
- les collections ;
- les items ;
- les assets ;
- l’API de recherche.

**Pertinence GSIE : très élevée.**

STAC doit devenir la projection géospatiale du Data Registry. Il ne doit pas remplacer le registre GSIE, car il ne porte pas à lui seul toutes les règles de licence, d’Evidence Level, de qualité scientifique ou d’usage métier.

Architecture recommandée :

```text
GSIE Dataset Registry
        │
        └── projection STAC Catalog / STAC API
                │
                ├── COG
                ├── GeoParquet
                ├── COPC / LAZ
                ├── Zarr
                └── autres assets
```

**Référence :** STAC est utilisé par Microsoft Planetary Computer, Element84 Earth Search, NASA et de nombreux catalogues Earth Observation.

### 3.2 COG, GeoParquet et COPC — formats cloud-native

#### COG

Le Cloud Optimized GeoTIFF permet des lectures par fenêtres et plages HTTP. GSIE peut donc servir une tuile ou une emprise sans rapatrier un raster complet.

Usage recommandé :

- MNT/MNS/MNH ;
- Sentinel ;
- indices de végétation ;
- humidité des sols ;
- cartes de danger ;
- sorties raster dérivées.

#### GeoParquet

GeoParquet combine les avantages de Parquet avec une géométrie et des métadonnées géospatiales. Les colonnes, partitions et statistiques de row groups peuvent être filtrées avant décodage complet.

Une évolution récente de DuckDB propose un mécanisme de colonne `bbox` et de pruning des row groups pour les requêtes spatiales. Le benchmark public associé rapporte des gains très importants lorsque les row groups sont spatialement triés et qu’une requête ne touche qu’une petite zone.

Usage recommandé :

- parcelles ;
- peuplements ;
- occurrences ;
- hydrographie ;
- routes et infrastructures ;
- observations terrain ;
- résultats de normalisation.

#### COPC / LAZ

Pour le LiDAR, conserver les nuages sous forme LAZ/COPC dans l’Object Storage et stocker dans GSIE :

- emprise ;
- CRS ;
- densité ;
- classes ;
- résolution ;
- checksum ;
- URL de l’asset ;
- métadonnées STAC.

Il ne faut pas transformer chaque point LiDAR en ligne `resource` du métamodèle.

**Verdict : adoption recommandée immédiatement.**

### 3.3 Apache Iceberg — tables analytiques versionnées

Iceberg apporte :

- snapshots ;
- évolution de schéma ;
- partitionnement indépendant du nom de fichier ;
- rollback ;
- lecture cohérente ;
- maintenance de tables sur Object Storage.

Des projets comme `nasa-itslive/earthcatalog` utilisent un catalogue STAC, des fichiers GeoParquet spatialement partitionnés, H3 et Apache Iceberg pour rendre de grands inventaires interrogeables depuis S3.

**Pertinence GSIE : élevée, mais différée.**

Iceberg est probablement utile pour :

- observations météorologiques massives ;
- occurrences biodiversité ;
- historiques d’incendies ;
- inventaires temporels ;
- catalogues de tuiles ou scènes satellite.

Il ne faut pas l’utiliser pour :

- les métadonnées de gouvernance GSIE ;
- les comptes utilisateurs ;
- les décisions ;
- les connaissances atomiques ;
- les petites tables transactionnelles.

Décision proposée : commencer sans Iceberg sur le premier dataset pilote, puis l’évaluer lorsqu’une table analytique dépasse les capacités opérationnelles de Parquet partitionné et des métadonnées GSIE.

### 3.4 DuckDB Spatial — analytique locale et fichiers S3

DuckDB est particulièrement intéressant pour GSIE car il peut :

- lire Parquet et GeoParquet ;
- interroger des fichiers sur Object Storage ;
- utiliser des extensions spatiales ;
- faire du pushdown de colonnes et de filtres ;
- fonctionner sans serveur séparé ;
- s’intégrer facilement à Python et Forge.

**Pertinence GSIE : très élevée pour le premier niveau analytique.**

DuckDB peut devenir le moteur de préparation et d’exploration de Forge, tandis que PostgreSQL/PostGIS reste l’autorité transactionnelle.

Pattern recommandé :

```text
S3/MinIO → DuckDB → validation/profilage → Parquet/GeoParquet → PostGIS ou publication
```

DuckDB ne doit pas devenir le registre métier GSIE.

### 3.5 Apache DataFusion — option Rust pour le hot path analytique

DataFusion est un moteur SQL analytique Rust basé sur Arrow. Il sait lire des données sur Object Storage, appliquer du pruning Parquet et exposer des chemins de lecture ciblés par row groups.

**Pertinence GSIE : moyenne à élevée, mais après mesure.**

DataFusion est un candidat sérieux pour :

- un worker analytique Rust ;
- un service de requête léger ;
- les traitements où Python devient le goulot ;
- les conversions Parquet parallélisées ;
- un futur Data Broker très performant.

Il ne faut pas l’introduire dès la première implémentation S3. La bonne stratégie est : Python/Polars/DuckDB d’abord, DataFusion seulement sur un hot path démontré par profilage.

### 3.6 Pangeo, Xarray, Zarr et Kerchunk

Cette famille est très pertinente pour Climate, Hydro et Simulation.

#### Zarr

Zarr stocke des tableaux multidimensionnels chunkés dans Object Storage. Il est adapté aux :

- cubes temps × latitude × longitude ;
- modèles climatiques ;
- réanalyses ;
- séries météo ;
- sorties de simulation ;
- données multi-variables.

#### Xarray

Xarray fournit les dimensions, coordonnées, unités et attributs scientifiques nécessaires à la manipulation de ces cubes.

#### Kerchunk

Kerchunk permet de produire une couche de références qui rend des fichiers existants — NetCDF, GRIB ou archives similaires — lisibles comme des datasets cloud-native sans recopier immédiatement tous les octets.

**Pertinence GSIE : très élevée pour les données climatiques et hydrologiques.**

Il faut différencier :

```text
Donnée source intacte → Kerchunk pour accès rapide sans copie
Donnée à normaliser → Zarr consolidé
Donnée à servir en raster → COG
```

### 3.7 TileDB — candidat spécialisé pour cubes et nuages de points

TileDB propose un modèle de stockage multidimensionnel et des primitives d’ingestion raster, géométrie et nuages de points. La documentation TileDB expose notamment des DAGs d’ingestion géospatiale et des paramètres de tuile, fragment et chunk.

**Pertinence GSIE : moyenne.**

TileDB est intéressant si les besoins suivants deviennent prioritaires :

- cubes multidimensionnels très denses ;
- requêtes par fragments ;
- accès simultané à des sous-régions ;
- gestion avancée des arrays ;
- workloads difficiles à représenter proprement en Zarr.

Il introduirait cependant un modèle supplémentaire. Il doit rester un POC comparatif, pas une décision de base.

### 3.8 SedonaDB / Apache Sedona

Apache Sedona offre :

- traitements spatiaux distribués avec Spark/Flink ;
- GeoParquet ;
- SQL spatial ;
- SedonaDB pour l’analytique mono-nœud ;
- SpatialBench pour comparer plusieurs moteurs.

**Pertinence GSIE : moyenne à élevée.**

Sedona est plus intéressant que Spark seul pour les très grandes jointures spatiales distribuées. SedonaDB peut concurrencer DuckDB Spatial sur certains workloads.

Recommandation : utiliser SpatialBench ou un benchmark interne GSIE pour comparer :

```text
PostGIS
DuckDB Spatial
SedonaDB
cuSpatial/cuDF
Apache Sedona + Spark
```

Ne pas choisir avant d’avoir mesuré les requêtes réellement nécessaires aux moteurs GSIE.

### 3.9 MinIO, SeaweedFS et Ceph

#### MinIO

MinIO reste le meilleur choix pour le premier incrément :

- API S3 standard ;
- intégration Docker simple ;
- bonne compatibilité avec les outils existants ;
- cohérent avec ADR-006 ;
- adapté au développement et aux environnements contrôlés.

#### SeaweedFS

SeaweedFS est intéressant pour :

- plusieurs milliards de fichiers ;
- très nombreux petits objets ;
- tiering local/cloud ;
- stockage S3 et filesystem.

Il mérite un benchmark si GSIE accumule de très nombreux petits assets, vignettes ou tuiles. Il ne doit pas remplacer MinIO maintenant.

#### Ceph

Ceph est adapté à une infrastructure de stockage complète : objet, bloc et filesystem, avec réplication, erasure coding et intégration HPC/Kubernetes.

Son coût opérationnel est important. Ceph ne doit être retenu que si Quintessences administre réellement un cluster de stockage dédié.

**Verdict :** MinIO maintenant ; SeaweedFS/Ceph en alternatives d’exploitation, pas en dépendances de code.

### 3.10 Orchestration et qualité

#### Forge actuel

Forge possède déjà :

- connecteurs ;
- plugins ;
- checkpoints ;
- workers RQ ;
- rate limiting ;
- manifeste de provenance ;
- pipeline YAML.

Il est donc inutile d’ajouter immédiatement Airflow, Spark et Kubernetes pour le premier pilote.

#### Dagster

Dagster est intéressant pour un modèle centré sur les assets, la lineage, les schedules, les sensors et les matérialisations.

**Pertinence : élevée à moyen terme.**

#### Prefect

Prefect est plus léger et proche d’une orchestration Python classique.

**Pertinence : moyenne à élevée.**

#### Argo Workflows

Argo est adapté lorsque les traitements sont déjà déployés sur Kubernetes et que chaque étape doit être un conteneur indépendant.

**Pertinence : différée.**

Recommandation : conserver RQ/Forge pour le pilote S3, concevoir les jobs comme des assets idempotents, puis évaluer Dagster avant d’adopter une plateforme plus lourde.

## 4. Architecture finale recommandée

```text
                         GSIE CONTROL PLANE
┌──────────────────────────────────────────────────────────────┐
│ PostgreSQL/PostGIS                                           │
│                                                              │
│ Dataset Registry                                             │
│ Provider / Source                                            │
│ DatasetVersion                                               │
│ DataAsset                                                     │
│ Licence / Rights / Evidence A-F                              │
│ Coverage / Quality / Health                                  │
│ Activity / Lineage / IngestionJob                            │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              │ STAC projection
                              ▼
                    STAC Catalog / STAC API
                              │
                              ▼
                         DATA PLANE
┌──────────────────────────────────────────────────────────────┐
│ MinIO/S3                                                     │
│                                                              │
│ RAW        → fichiers originaux immuables                    │
│ NORMALIZED → Parquet, GeoParquet, COG, Zarr, COPC            │
│ DERIVED    → produits GSIE                                   │
│ QUARANTINE → fichiers non validés                            │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
                       PROCESSING PLANE
┌──────────────────────────────────────────────────────────────┐
│ Forge Workers                                                │
│                                                              │
│ CPU : Polars / PyArrow / DuckDB / GDAL                       │
│ GPU : cuDF / Dask-cuDF / cuSpatial                          │
│ Climate : Xarray / Zarr / Kerchunk                          │
│ Images : DALI                                                │
│ Hot path éventuel : Rust/DataFusion                          │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
                       SERVING PROJECTIONS
┌──────────────────────────────────────────────────────────────┐
│ PostGIS métier · caches · tuiles · Data Broker               │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
                 Moteurs GSIE et applications clientes
```

## 5. Recommandation par niveau d’adoption

### Adoption immédiate

- MinIO/S3 standard ;
- upload multipart et reprise ;
- STAC comme projection géospatiale ;
- COG, GeoParquet, COPC, Zarr ;
- DuckDB Spatial ;
- Polars/PyArrow pour la baseline CPU ;
- manifests, checksums et lineage ;
- quarantine/staging/production.

### Adoption après le premier pilote

- cuDF pour les transformations tabulaires lourdes ;
- Dask-CUDA/Dask-cuDF pour multi-GPU ;
- cuSpatial pour les jointures spatiales lourdes ;
- Pangeo/Xarray pour Climate et Hydro ;
- Dagster si le nombre de pipelines justifie un orchestrateur asset-centric ;
- Iceberg pour les tables analytiques versionnées à forte volumétrie.

### POC conditionnel

- cuObject pour S3/RDMA ;
- cuFile/GPUDirect Storage pour filesystem GPU ;
- DataFusion pour un hot path Rust mesuré ;
- TileDB pour cubes ou fragments spécialisés ;
- SeaweedFS pour très grand nombre de petits objets ;
- Ceph pour un cluster de stockage auto-opéré.

### À ne pas adopter maintenant

- Spark uniquement parce que les datasets sont volumineux ;
- Kafka sans flux événementiel justifié ;
- Kubernetes pour le premier pilote ;
- une seconde base de métadonnées ;
- un format propriétaire obligatoire ;
- cuObject sans stockage RDMA compatible ;
- Rust ou C++ sans profilage démontrant un hot path ;
- NIM ou LLM dans le chemin critique de transfert des octets.

## 6. Plan final avant implémentation

### Phase 1 — Object Storage fiable

- implémenter MinIO/S3 ;
- ajouter `storage_uri` à `DataAsset` ;
- ajouter upload multipart, streaming, range GET et checksums ;
- ajouter configuration `.env.example` ;
- ajouter MinIO au Compose de développement ;
- ajouter tests unitaires, tests de sécurité et tests d’idempotence.

### Phase 2 — Publication Forge → GSIE

- créer un manifeste de publication ;
- stocker RAW, NORMALIZED et DERIVED ;
- enregistrer `DatasetVersion`, `DataAsset`, `Activity` et lineage ;
- ajouter les états `quarantine`, `staging` et `production` ;
- garder GSIE comme autorité des droits et de la provenance.

### Phase 3 — Formats et catalogue spatial

- générer COG pour les rasters ;
- générer GeoParquet avec emprise et ordre spatial ;
- générer COPC pour les nuages de points ;
- produire une projection STAC ;
- tester les lectures partielles sur S3/MinIO.

### Phase 4 — Premier dataset réel

Pilote recommandé : **SoilGrids ou un dataset IGN de taille contrôlée**.

Critères de sortie :

- reprise après interruption ;
- checksum reproductible ;
- licence vérifiée ;
- couverture contrôlée ;
- normalisation des CRS et unités ;
- provenance complète ;
- lecture partielle sans téléchargement intégral ;
- rollback de publication.

### Phase 5 — Benchmark CPU/GPU

Comparer sur les mêmes fixtures et les mêmes sorties :

```text
Polars/PyArrow
DuckDB Spatial
cuDF
Dask-cuDF
cuSpatial
SedonaDB
PostGIS
```

Mesurer :

- débit de lecture ;
- débit de transformation ;
- débit d’écriture ;
- mémoire CPU ;
- mémoire GPU ;
- coût réseau ;
- nombre de fichiers/row groups lus ;
- latence p50/p95/p99 ;
- reproductibilité des résultats.

### Phase 6 — Accélération spécialisée

- activer cuDF/Dask-cuDF si le benchmark le justifie ;
- tester cuFile si un filesystem compatible est disponible ;
- tester cuObject uniquement sur une infrastructure RDMA réelle ;
- intégrer DataFusion seulement si un hot path Rust est confirmé.

## 7. Risques et contre-mesures

| Risque | Contre-mesure |
|---|---|
| Multiplication des technologies | Standards ouverts et adoption par paliers |
| Deux registres concurrents | GSIE Registry autoritaire, STAC en projection |
| Explosion du nombre de petits fichiers | Partitionnement, compaction, row groups contrôlés |
| GPU plus lent que CPU sur petits lots | Seuils de taille et benchmark obligatoire |
| Résultats GPU différents du CPU | Fixtures de parité, tolérances et golden outputs |
| S3 indisponible | MinIO local, cache, reprise et dernier snapshot valide |
| Dataset malveillant | Quarantine, limites d’archive, magic bytes, scan et isolation |
| Licence incorrecte | Porte `require_ingestible`, blocage par défaut |
| Dépendance à un fournisseur | Interfaces S3/STAC/Arrow et adapters remplaçables |
| Orchestrateur trop lourd | RQ/Forge au départ, Dagster ou Argo seulement après mesure |

## 8. Verdict

La pépite principale n’est pas un produit isolé : c’est la combinaison **STAC + formats cloud-native + Object Storage + moteur analytique fichier + projections PostGIS**.

Pour GSIE, la meilleure architecture est donc :

```text
GSIE Registry
+ STAC projection
+ MinIO/S3
+ COG / GeoParquet / COPC / Zarr
+ Forge workers
+ DuckDB/Polars baseline
+ cuDF/Dask-cuDF optionnels
+ PostGIS serving authority
```

Cette architecture permet de commencer sur une machine de développement et de monter progressivement vers plusieurs nœuds, sans rendre le fonctionnement dépendant d’un GPU NVIDIA, d’un cloud particulier ou d’un orchestrateur unique.

## 9. Sources et références

### Sources internes

- `GSIE/API/docs/data/GSIE_DATA_ARCHITECTURE_AUDIT.md` — audit Phase 0 ;
- `GSIE/ARCHITECTURE/ADR-006-object-storage.md` — décision MinIO/S3 ;
- `GSIE/DATASETS/NOMENCLATURE_SOURCES.md` — licences, grain et archivage ;
- `GSIE/RESEARCH/VEILLE_NVIDIA_DEV_BLOG_2026-08-08.md` — veille NVIDIA récente ;
- `Forge/docs/ARCHITECTURE.md` — usine de données et plugins ;
- `Forge/docs/DATA_STRATEGY.md` — provenance, validation et formats.

### Standards et projets externes

- STAC Specification — <https://stacspec.org/> ;
- STAC GeoParquet — <https://github.com/stac-utils/stac-geoparquet> ;
- NASA EarthCatalog — <https://github.com/nasa-itslive/earthcatalog> ;
- Element84 Earth Search — <https://github.com/element84/earth-search> ;
- Apache Iceberg — <https://iceberg.apache.org/> ;
- DuckDB Spatial — <https://duckdb.org/docs/stable/core_extensions/spatial/overview> ;
- Apache DataFusion — <https://github.com/apache/datafusion> ;
- Apache Sedona / SedonaDB — <https://github.com/apache/sedona> ;
- Pangeo Forge — <https://pangeo-forge.readthedocs.io/> ;
- Pangeo Cloud Datastore — <https://github.com/pangeo-data/pangeo-datastore> ;
- TileDB geospatial ingestion — <https://tiledb-inc.github.io/TileDB-Cloud-Py/reference/geospatial.ingestion.html> ;
- SeaweedFS — <https://github.com/seaweedfs/seaweedfs> ;
- Ceph — <https://github.com/ceph/ceph> ;
- cuDF/Dask-cuDF — <https://docs.rapids.ai/api/dask-cudf/stable/> ;
- cuSpatial — <https://docs.rapids.ai/api/cuspatial/stable/> ;
- NVIDIA GPUDirect Storage / cuObject — <https://docs.nvidia.com/gpudirect-storage/cuobject/> ;
- NVIDIA DALI — <https://docs.nvidia.com/deeplearning/dali/user-guide/docs/>.

## 10. Historique des modifications

| Version | Date | Modification |
|---|---|---|
| 1.0.0 | 2026-08-09 | Étude externe initiale et plan final proposé. |

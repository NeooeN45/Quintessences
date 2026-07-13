# CHANGELOG — Quintessences / GSIE

Format : `## [version] - YYYY-MM-DD`

---

## [PHASE 3 CLÔTURÉE — PHASE 4 LANCÉE] - 2026-07-13

### Validation des 10 livrables Phase 3 (DEC-000017)

Le Fondateur valide les 10 livrables Phase 3 (`Review` → `Validated`) et
clôture officiellement la Phase 3 — Connaissance.

- 10 livrables (301-310) passés en `Validated`
- `GSIE-DIR-0007` amendé v1.2 (CLOS)
- `GSIE-DIR-0011` créée — lancement Phase 4 Implémentation
- `DEC-000017` tracée
- `ROADMAP.md` : Phase 3 → Clôturée ✅, Phase 4 → Active 🚀
- `PROJECT_MEMORY.md` : Phase courante → 4 — Implémentation

### Fiche recherche LiDAR HD IGN

Source : `DC_LiDAR_HD_1-0.pdf` (IGN, descriptif de contenu officiel).

- `GSIE/RESEARCH/LIDAR_HD_SPECIFICATIONS.md` créée (236 lignes) :
  - 11 classes de classification (8 ASPRS + 3 IGN) détaillées
  - Correspondance strates Ignis ↔ classes LiDAR (3↔4→strate 1, 5→2/3)
  - Pipeline IGN officiel : PDAL → GDAL → PostGIS (ST_Tile, ST_SummaryStats, ST_DumpAsPolygon)
  - Bibliothèque `IGN_LIDAR_HD_DATASET` v4.1.2 (GPU/CUDA, 35-45 features, LOD2/LOD3)
  - Implications Unreal/Cesium : MNT 50cm → Cesium 3D Terrain, MNH → PCG végétation par strate
  - 8 recommandations Phase 4 priorisées
- `DATASET_CATALOG.md` DS-002 enrichi : 11 classes, pipeline, bibliothèque, correspondance strates

---

## [SPECS HUB + IGNIS + GEOSYLVA COMPLÈTES] - 2026-07-13

### 5 nouvelles spécifications Draft (HUB-003, IGNIS-002, IGNIS-003, GEO-002, GEO-003)

Complétion du plan `HUB_AND_APPS_PLAN.md` : les 9 spécifications P0/P1
sont désormais rédigées.

- **HUB-003** — Fiches détaillées des 25 couches du Hub (22 apps + 3
  globales). 14 champs par fiche (layer_id, geometry_type, canal,
  datasets, moteur, état, priorité P4). Matrice de compatibilité +
  priorités P0/P1/P2.
- **IGNIS-002** — Spec non fonctionnelle Ignis : performance (latence
  par flux, capacité), résilience (T-10), sécurité (JWT, TLS, rôles,
  RGPD), interopérabilité, souveraineté, explicabilité (CON-004),
  garde-fous RFC-0004 §8, scalabilité.
- **IGNIS-003** — Matrice de traçabilité Ignis : F-01→F-26, NF-01→NF-10,
  datasets (DS-001/002/009/010/022/023/024), moteurs (GIS, Climate,
  Simulation, Correlation, Learning), idées registre (P/J/V/G/S/D),
  couches Hub (ignis.*), garde-fous RFC-0004 §8.
- **GEO-002** — Spec non fonctionnelle GeoSylva : performance (mobile +
  Hub + segmentation), offline-first (RFC-0003, cache < 2 GB),
  résilience (ZICAD), sécurité, interopérabilité (app Android Kotlin),
  souveraineté, accessibilité mobile (terrain).
- **GEO-003** — Matrice de traçabilité GeoSylva : F-01→F-23,
  NF-01→NF-12, datasets (DS-001/002/003/025/026), moteurs (GIS, Forest
  Dyn., Botanical, Diagnostic, Recommendation, Simulation), ontologie
  S-6 (DOM-ECO/DEN/SYL/DYN), couches Hub (geosylva.*), précédents
  opérationnels (ONF, SDIS 63, Arbonaut).

Mémoire synchronisée : `PROJECT_MEMORY.md`, `ROADMAP.md`.

---

## [PHASE 3 — LIVRABLES 301-310 EN REVIEW] - 2026-07-13

### Passage des 10 livrables Phase 3 de `Draft` à `Review`

Les 10 livrables de la Phase 3 (301-310) passent en **Review** : contenu
rédigé, en attente de validation du Fondateur.

- Statut mis à jour (en-tête + pied) dans les 10 fichiers :
  `RESEARCH_METHOD`, `KNOWLEDGE_METHOD`, `FOREST_ONTOLOGY`,
  `KNOWLEDGE_GRAPH_SPECIFICATION`, `DATASET_CATALOG`, `EVIDENCE_FRAMEWORK`,
  `SOURCING_PLAN`, `KNOWLEDGE_BASE_SEED`, `ENCYCLOPEDIA_DATABASE_SCHEMA`,
  `ENGINE_DATA_SOCLE`.
- `ROADMAP.md` : table Phase 3 → tous en Review.
- `PROJECT_MEMORY.md` : section « Prochaine étape » actualisée.
- La validation `Review → Validated` relève du Fondateur (CON-001).

---

## [VAULT OBSIDIAN IGNORÉ — NON CANONIQUE] - 2026-07-13

### Vault Obsidian `Quintessences/Quintessences/` exclu du dépôt

Un vault Obsidian personnel (33 fichiers `.md`) dupliquait la gouvernance
dans une arborescence parallèle, avec un contenu **périmé et contradictoire**
(titres d'articles CON-002 à CON-007 erronés, statuts Locked incorrects,
CON-008/009/010 absents).

- Ajout de `/Quintessences/` au `.gitignore` (ancré à la racine).
- Le vault reste un **outil de navigation personnel local**, explicitement
  **non canonique**. La source de vérité de la gouvernance reste les
  dossiers numérotés (`00_CONSTITUTION/`, `03_DECISIONS/`, etc.).
- Aucun contenu constitutionnel faux n'entrera dans le dépôt.

---

## [PHASE 3 ÉTENDUE À 10 LIVRABLES] - 2026-07-13

### Extension du périmètre Phase 3 (8 → 10) — DEC-000016

Les livrables **309** (Schéma DB Encyclopédie) et **310** (Socle données
14 moteurs + liens apps), créés hors périmètre, sont rattachés
formellement à la Phase 3.

- `GSIE-DIR-0007` amendé (v1.0 → v1.1) — section « Amendement 2026-07-13 »
  ajoutée, texte d'origine (8 livrables) conservé (CON-010).
- `ROADMAP.md` : table Phase 3 étendue à 309-310, note de périmètre.
- `PROJECT_MEMORY.md` : périmètre mis à jour (10 livrables), DEC-000016
  ajoutée.
- Conciliation DEC-000012 : 309-310 sont des **spécifications** (aucun
  code) ; l'implémentation de l'Encyclopédie reste en Phase 4.

---

## [RFC-0002 ADOPTÉ — UNIFICATION DES ARTICLES] - 2026-07-13

### Adoption de RFC-0002 (Option A) — DEC-000015

Les fichiers `GSIE-CON-0XX.md` deviennent la **source de vérité unique**
du corpus d'articles constitutionnels.

- Suppression des 100 fichiers vides `ARTICLE_001.md` → `ARTICLE_100.md`
  (0 octet chacun, vérifiés avant suppression).
- Création de `00_CONSTITUTION/ARTICLES_INDEX.md` (index de renvoi).
- `00_CONSTITUTION/README.md` : section « Ce qui peut y être ajouté »
  corrigée (numérotation `GSIE-CON-0XX` non plafonnée à 100).
- `02_RFC/RFC-0002.md` passé en **Adopté** (section 9 ajoutée).
- `ROADMAP.md` : livrable 010 repointé, mention du gabarit `ARTICLE_0xx`
  retirée.
- `GSIE-CON-000.md` (Locked) non modifié.

### Mémoire du fondateur

- `22_PROJECT_MEMORY/FOUNDER_JOURNAL.md` : entrée du 2026-07-13 ajoutée
  (DEC-000011 à DEC-000015).

---

## [SPECS HUB + AUDIT PHASE 3] - 2026-07-13

### Spécifications créées (05_SPECIFICATIONS/)

- **HUB_001_SPECIFICATION.md** créé : spec fonctionnelle du Centre de
  Commandement (26 exigences : HUB-F-01 à HUB-F-26, HUB-NF-01 à
  HUB-NF-13). 3 cas d'usage (surveillance incendie, diagnostic
  sylvicole, exploration recherche). Matrice de traçabilité exigence →
  source. 13 couches Hub définies.
- **HUB_002_INTERFACE_CONTRACT.md** créé : contrat d'interface Hub ↔
  Apps. 22 couches initiales (geosylva.*, ignis.*, hydro.*, flora.*,
  artemis.*). Format payload temps réel (WebSocket/JSON) et volumineux
  (3D Tiles, GeoTIFF). Métadonnées requises (CON-005). Convention état
  réel vs simulé. Cycle de vie d'une couche. Version 1.0.0 du contrat.
- **IGNIS_001_SPECIFICATION.md** créé : spec fonctionnelle Ignis (357
  lignes, 26 exigences IGNIS-F-01 à F-26 en 8 sections : détection,
  combustible, météo, propagation, drones, visualisation Hub, garde-fous,
  données synthétiques. 10 exigences non fonctionnelles. 3 cas d'usage.
  Traçabilité : 7 datasets (DS-001/002/009/010/022/023/024), 30+ idées
  registre (P/J/V/C/G/D/S/M), garde-fous RFC-0004 §8, contrat HUB-002.
- **GEO_001_SPECIFICATION.md** créé : spec fonctionnelle GeoSylva (432
  lignes, 23 exigences GEO-F-01 à F-23 en 7 sections : inventaire,
  peuplements, biomasse, diagnostic, visualisation Hub, app mobile,
  état réel/simulé). 12 exigences non fonctionnelles. 3 cas d'usage.
  Traçabilité : 5 datasets (DS-001/002/003/025/026), ontologie forestière
  (livrable 303), gradient de fidélité (livrable 212 §1), précédents
  ONF/SDIS/Arbonaut (livrable 212 §3.3), contrat HUB-002.

### Audit Phase 3 (livrables 301-308)

- **Résultat : tous les 8 livrables sont complets et non stubs.**
- 301 RESEARCH_METHOD (~261 lignes) — pipeline 10 étapes ✅
- 302 KNOWLEDGE_METHOD (~358 lignes) — cycle de vie complet ✅
- 303 FOREST_ONTOLOGY (~803 lignes) — 10 domaines S-6 ✅
- 304 KNOWLEDGE_GRAPH_SPEC (~917 lignes) — raisonnement multi-échelle ✅
- 305 DATASET_CATALOG (~889 lignes) — 26 datasets (critère: ≥10) ✅
- 306 EVIDENCE_FRAMEWORK (~579 lignes) — 6 niveaux + exemples 10 domaines ✅
- 307 SOURCING_PLAN (~337 lignes) — 6 vagues alignées moteurs ✅
- 308 KNOWLEDGE_BASE_SEED (~668 lignes) — 25 connaissances (critère: ≥20) ✅
- **La Phase 3 peut passer en Review.**

---

## [SOURCES 3D + PLAN HUB] - 2026-07-13

### Enrichissement des sources de données (DATASET_CATALOG, livrable 305)

- **DS-002 (LiDAR HD IGN)** enrichi : MNT/MNS/MNH 50 cm, 84 % publié
  (juillet 2026), 9 cas d'usage IGN, précédents validés (SDIS 63, ONF,
  Arbonaut SaniLidar), webinaire IGN oct. 2025, restriction ZICAD.
- **DS-025 (GEDI L4A/L4B NASA)** créé : biomasse aérienne spatiale,
  footprint 25 m, grille 1 km, v3 publiée juin 2026.
- **DS-026 (ESA Biomass CCI v7)** créé : cartes globales AGB 2005-2024,
  1 ha, v7 publiée mai 2026 (Sentinel-1 + ALOS-2 + ICESat-2 + GEDI).
- Priorité d'ingestion mise à jour (vague 4 — Forest Dynamics).

### Mise à jour des précédents scientifiques (UNREAL_ENGINE_PRECEDENTS)

- **Cesium 3D Gaussian Splats** (avril 2026) : support production-ready
  dans Cesium for Unreal avec LOD hiérarchique, standardisation glTF
  (KHR_gaussian_splatting + SPZ -90 %), pipeline bout-en-bout Cesium ion.
- **SegmentAnyTreeV2** (2026) : foundation model segmentation d'arbres,
  F1 85 %, zero-shot cross-domain, code ouvert (Open Forest Observatory).
- **Crown-BERT** (2026) : classification d'essences par fusion LiDAR +
  hyperspectral drone, 83-91 % OA, 0.9 M params.

### Mise à jour des livrables d'architecture (Phase 2)

- **Livrable 211 (COMMAND_CENTER_UNREAL.md)** v2.1.0 : brique 5 Gaussian
  Splatting passée de « à tester » → « ✅ validé » (pipeline Cesium ion
  confirmé avril 2026). Section §2 enrichie avec la validation.
- **Livrable 212 (GEOSYLVA_UNREAL_ARCHITECTURE.md)** v1.1.0 : ajout de
  SegmentAnyTreeV2 et Crown-BERT au tableau §3.2, nouvelle section §3.3
  « Précédents opérationnels validés » (ONF, SDIS 63, Arbonaut).

### Veille partenariat (20_PARTNERSHIPS)

- **JUNN_VEILLE.md** créé : veille stratégique sur le programme JUNN
  (Jumeau Numérique National, IGN/Cerema/Inria, France 2030, 25 M€,
  14 partenaires). Alignement quasi 1:1 avec l'architecture Quintessences.
  Pas un partenariat actif — veille uniquement.

### Plan Hub + specs apps (05_SPECIFICATIONS)

- **HUB_AND_APPS_PLAN.md** créé : plan de production du Hub (Centre de
  Commandement) puis des spécifications de chaque app. Ordre : Hub (P0,
  bloquant) → Ignis (P1) → GeoSylva (P1) → Hydro/Flora (P2) →
  Artemis/QGISIA (P3). Exigences fonctionnelles et non fonctionnelles
  structurées (HUB-F-01 à HUB-F-10, HUB-NF-01 à HUB-NF-08, IGNIS-F-01 à
  IGNIS-F-10, GEO-F-01 à GEO-F-12). Contrat d'interface Hub ↔ Apps
  défini. Calendrier indicatif Phase 3 → Phase 4.

---

## [INTÉGRATION REPOS EXTERNES] - 2026-07-13

### Déplacement des repos externes dans la structure Quintessences

| Ancien chemin | Nouveau chemin | Repo git |
|---|---|---|
| `A:\GeoSylva\` | `apps/GeoSylva/` | GitHub: NeooeN45/GeoSylva |
| `A:\QGISIA\` | `apps/QGISIA/` | GitHub: NeooeN45/QGISIAPRO |
| `A:\GSIE-Dataset-Forge\` | `Forge/` | Pas de remote |

Ces repos gardent leur propre `.git` — ils sont indépendants du repo
parent Quintessences. Le `.gitignore` du parent les ignore.

### Fichiers de notes rangés

| Ancien chemin | Nouveau chemin |
|---|---|
| `A:\profile-readme.md` | `22_PROJECT_MEMORY/notes/profile-readme.md` |
| `A:\possible changement de noms.txt` | `22_PROJECT_MEMORY/notes/possible_changement_de_noms.txt` |
| `A:\modification a faire Architecture g.txt` | `22_PROJECT_MEMORY/notes/modification_architecture_globale.txt` |

### Nettoyage

- Stubs `apps/GeoSylva/README.md` et `apps/QGISIA/README.md` supprimés
  (remplacés par les vrais repos)
- `tmp_commit_msg.txt` supprimé

### À noter

- `apps/Artemis/` reste un stub (README.md seulement) — le code sera
  créé en Phase 4
- Le disque `A:\` est désormais propre : seulement `$RECYCLE.BIN` et
  `GSIE/` (qui sera renommé en `Quintessences/` par le Fondateur)

---

## [RÉORGANISATION ARBORESCENCE] - 2026-07-13

### Réorganisation du dépôt (DEC-000014, GSIE-DIR-0010)

Le Fondateur acte la réorganisation de l'arborescence du dépôt en trois
niveaux : **racine** (transverse), **GSIE/** (moteur), **apps/**
(applications clientes).

**13 dossiers déplacés vers GSIE/** :
- `04_ARCHITECTURE/` → `GSIE/ARCHITECTURE/`
- `06_RESEARCH/` → `GSIE/RESEARCH/`
- `07_KNOWLEDGE/` → `GSIE/KNOWLEDGE/`
- `08_DATASETS/` → `GSIE/DATASETS/`
- `09_ENGINES/` → `GSIE/ENGINES/`
- `10_ALGORITHMS/` → `GSIE/ALGORITHMS/`
- `11_MODELS/` → `GSIE/MODELS/`
- `12_APPLICATIONS/` → `GSIE/APPLICATIONS/`
- `13_API/` → `GSIE/API/`
- `14_SDK/` → `GSIE/SDK/`
- `15_TESTS/` → `GSIE/TESTS/`
- `16_TOOLS/` → `GSIE/TOOLS/`
- `17_DOCUMENTATION/` → `GSIE/DOCUMENTATION/`

**6 dossiers apps/ créés** :
- `apps/GeoSylva/` (forêt) — README créé
- `apps/Artemis/` (faune) — README créé
- `apps/Ignis/` (incendies) — déménagé depuis `22_PROJECT_MEMORY/Ignis/`
- `apps/Hydro/` (eau) — README créé
- `apps/Flora/` (végétation) — README créé
- `apps/QGISIA/` (plugin QGIS) — README créé

**454 remplacements de chemins** dans 73 fichiers.
**CLAUDE.md** entièrement réécrit avec la nouvelle arborescence.

### Documents créés

- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0010.md` — directive réorganisation
- `03_DECISIONS/DEC-000014.md` — décision réorganisation

---

## [RESTRUCTURATION ÉCOSYSTÈME] - 2026-07-13

### Restructuration Quintessences (DEC-000013, GSIE-DIR-0009)

Le Fondateur acte une restructuration majeure de l'écosystème
Quintessences :

**Renommages** :
- Myhunt → **Artemis** (faune — comptages, pièges photo, empreintes,
  observations, populations)
- GSIE-Ignis → **Ignis** (incendies — DFCI, prévention, simulation,
  gestion de crise)

**Nouvelles applications** :
- **Hydro** (eau) — réseau hydrographique, zones humides, régimes
  hydriques. Moteurs : GIS, Climate, Knowledge, Correlation. Datasets :
  BD Carthage, BD TOPAGE, Sandre.
- **Flora** (végétation) — flore, taxonomie, cartographie végétale,
  phénologie. Moteurs : Botanical, Knowledge, GIS, Climate. Datasets :
  GBIF, Tela Botanica, BDNFF, INPN.

**QGISIA** : reste comme plugin QGIS de l'écosystème Quintessences.

**Centre de Commandement GSIE** (Unreal Engine 5.8) : repositionnement
majeur. UE n'est plus une simple visionneuse 3D — c'est un poste de
pilotage immersif où toutes les données convergent (GeoSylva, Artemis,
Ignis, Hydro, Flora). Mélange ArcGIS Pro + QGIS + Cesium + Flight
Simulator + Microsoft Digital Twins + moteur de jeu.

**Architecture cible** :
```
Quintessences → GSIE (moteur) → GeoSylva, Artemis, Ignis, Hydro, Flora, QGISIA
```

**Applications futures réservées** : Terra, Atmos, Atlas, Aether,
Chronos, Nexus…

### Fichiers renommés

| Ancien nom | Nouveau nom |
|---|---|
| `22_PROJECT_MEMORY/GSIE-Ignis/` | `apps/Ignis/` |
| `22_PROJECT_MEMORY/GSIE-Ignis.md` | `apps/Ignis/REGISTRE.md` |
| `GSIE/ARCHITECTURE/GSIE_IGNIS_ARCHITECTURE.md` | `GSIE/ARCHITECTURE/IGNIS_ARCHITECTURE.md` |
| `GSIE/ARCHITECTURE/GSIE_IGNIS_DATA_PIPELINE.md` | `GSIE/ARCHITECTURE/IGNIS_DATA_PIPELINE.md` |
| `GSIE/ARCHITECTURE/GSIE_IGNIS_DRONE_ARCHITECTURE.md` | `GSIE/ARCHITECTURE/IGNIS_DRONE_ARCHITECTURE.md` |
| `GSIE/ARCHITECTURE/GSIE_IGNIS_GCS_CINEMA_UNREAL.md` | `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` |

### Documents mis à jour

- 58 fichiers : remplacement Myhunt→Artemis et GSIE-Ignis→Ignis
- `GSIE/ARCHITECTURE/ENGINE_DATA_SOCLE.md` : +Hydro, +Flora, matrice 6 apps
- `GSIE/ARCHITECTURE/GSIE_MASTER_ARCHITECTURE.md` : +Centre de Commandement
- `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` : repositionnement GCS→Centre de Commandement
- `README.md` : architecture + Hydro + Flora + Centre de Commandement

### Documents créés

- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0009.md` — directive restructuration
- `03_DECISIONS/DEC-000013.md` — décision restructuration

---

## [SCHÉMA DB + SOCLE MOTEURS] - 2026-07-13

### Livrables 309-310 — socle technique de l'Encyclopédie

**Livrable 309 — Encyclopédie Database Schema** (677 lignes) :
- 16 tables PostgreSQL/PostGIS avec DDL complet (sources, datasets,
  connaissances_meta, connaissances_versions, conflits,
  domaines_validite, taxons, types_sol, habitats, pathologies,
  insectes, modeles, moteurs_consommateurs, relations_meta,
  ingestion_logs, utilisateurs)
- Schéma Neo4j (labels, relations, contraintes, exemples Cypher)
- Index Elasticsearch (mapping full-text)
- Schéma RDF/OWL (préfixes, classes, propriétés, alignement LOD)
- Règles de génération d'identifiants uniques stables
- Mapping KnowledgeObject → PostgreSQL/Neo4j/RDF
- Pipeline d'ingestion, sécurité et accès

**Livrable 310 — Engine Data Socle** (768 lignes) :
- Socle de données détaillé pour les 14 moteurs (consomme/produit,
  domaines, datasets, entités, requêtes, dépendances, volumes)
- Liens vers les 4 apps externes (GeoSylva, Ignis, Artemis, QGISIA)
- Matrice moteur × app
- Priorité d'alimentation alignée sur l'ordre de développement (204)

### Documents créés

- `GSIE/ARCHITECTURE/ENCYCLOPEDIA_DATABASE_SCHEMA.md` — livrable 309
- `GSIE/ARCHITECTURE/ENGINE_DATA_SOCLE.md` — livrable 310

---

## [ENCYCLOPÉDIE DE L'ÉCOSYSTÈME] - 2026-07-13

### L'Encyclopédie de l'Écosystème (DEC-000012, GSIE-DIR-0008)

Le Fondateur acte la création de l'**Encyclopédie de l'Écosystème** :
la plus grande base de données structurée, sourcée et traçable sur tout
ce qui touche à l'écosystème. Cette encyclopédie est **le produit
principal** de GSIE, pas un sous-produit des moteurs.

**Échelle visée** : million d'entrées minimum.

**Périmètre** : flore, faune, sols, climat, hydrologie, pathologies,
entomologie, mycologie, interactions trophiques, dynamiques,
sylviculture, biodiversité, incendie.

**Architecture cible** (Phase 4) :
- Base graphe (Neo4j ou équivalent) — 10M+ nœuds
- Identifiants uniques stables et citables (GSIE-K-XXXXXXXXXX)
- Triple store sémantique (RDF/OWL, SPARQL)
- Pipelines d'ingestion automatisés (Airflow + NLP + LLM)
- 10 classificateurs (source, preuve, domaine, type, entités, relations,
  seuils, conflits, doublons, conformité)
- API GraphQL + REST + interface web
- Licence ouverte maximale

**Positionnement unique** : la seule base combinant taxonomie +
autécologie + pédologie + climat + interactions + modèles +
sylviculture, sourcé, versionné et interrogeable.

Le livrable 308 (25 connaissances) devient l'**amorce** de
l'Encyclopédie, pas le produit final.

---

## [PHASE 3 — CONNAISSANCE] - 2026-07-13

### Lancement officiel Phase 3 (DEC-000011, GSIE-DIR-0007)

Le Fondateur acte l'entrée en **Phase 3 — Connaissance**. La Phase 3
transforme les fondations scientifiques (Phase 1) et l'architecture
(Phase 2) en une **base de connaissances structurée, sourcée et
versionnée** — le véritable produit de GSIE (CON-003).

### 8 livrables Phase 3 (301-308)

| # | Livrable | Lignes | Description |
|---|---|---|---|
| 301 | Research Method | 261 | Pipeline 10 étapes avec critères opérationnels, articulation moteurs |
| 302 | Knowledge Method | 358 | Cycle de vie KnowledgeObject, 6 types, versionnement, domaines de validité |
| 303 | Forest Ontology | 803 | 10 domaines S-6, concepts, propriétés, relations, référentiels, échelles |
| 304 | Knowledge Graph Spec | 917 | Nœuds, arêtes, requêtes, versioning, graphe vivant DIR-0006, conflits S-3 |
| 305 | Dataset Catalog | 837 | 24 datasets (IGN, Météo-France, INRAE, GBIF, Copernicus, Prométhée) |
| 306 | Evidence Framework | 579 | Niveaux A-F, matrice de décision, 10 exemples par domaine, upgrade/downgrade |
| 307 | Sourcing Plan | 337 | 7 vagues alignées sur moteurs, 64 sources, critères de complétude |
| 308 | Knowledge Base Seed | 668 | 25 connaissances validées (5 essences + pédologie + croissance + taxonomie) |

### Documents créés

- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0007.md` — Directive Phase 3
- `03_DECISIONS/DEC-000011.md` — Décision d'ouverture Phase 3
- `GSIE/RESEARCH/RESEARCH_METHOD.md` — détaillage (stub → 261 lignes)
- `GSIE/RESEARCH/EVIDENCE_FRAMEWORK.md` — nouveau
- `GSIE/RESEARCH/SOURCING_PLAN.md` — nouveau
- `GSIE/KNOWLEDGE/KNOWLEDGE_METHOD.md` — détaillage (stub → 358 lignes)
- `GSIE/KNOWLEDGE/FOREST_ONTOLOGY.md` — détaillage (stub → 803 lignes)
- `GSIE/KNOWLEDGE/KNOWLEDGE_GRAPH_SPECIFICATION.md` — détaillage (stub → 917 lignes)
- `GSIE/KNOWLEDGE/KNOWLEDGE_BASE_SEED.md` — nouveau
- `GSIE/DATASETS/DATASET_CATALOG.md` — nouveau

### Connaissances initiales (livrable 308)

25 KnowledgeObjects validés :
- Autécologie : chêne sessile (K-001 à K-004), hêtre (K-005 à K-007),
  douglas (K-008 à K-010), sapin pectiné (K-011, K-012), pin sylvestre
  (K-013, K-014)
- Pédologie : classes RUM, classes pH, profondeur, Alocrisol, Brunisol
  (K-015 à K-019)
- Croissance : ONF-FFN douglas, chêne, hêtre (K-020 à K-022)
- Taxonomie : Quercus petraea, Fagus sylvatica, Pseudotsuga menziesii
  (K-023 à K-025)
- 1 conflit bibliographique documenté (S-3) : gel du sapin pectiné
  (-20°C vs -15°C selon provenance)

---

## [UNREAL ENGINE — JUMEAU NUMÉRIQUE 3D] - 2026-07-12

### Adoption Unreal Engine 5.8 + Cesium (DEC-000010)

Le Fondateur acte l'adoption d'**Unreal Engine 5.8 + Cesium for Unreal**
comme moteur 3D du jumeau numérique vivant (DIR-0005). Cette décision
réalise l'ADR-001 du livrable 208 (moteur 3D interchangeable) et ouvre
deux nouveaux livrables Phase 2.

### Nouveaux livrables

- **Livrable 211 — GCS-Cinéma Unreal Engine (Ignis)** : architecture du
  poste de commandement 3D. UE 5.8 + Cesium (terrain géoréférencé, 3D
  Tiles, Gaussian Splats) + WebSockets natifs (ingestion temps réel) +
  Niagara (feu/fumée pilotés par données, façon FIRETWIN). Précédents
  scientifiques : FIRETWIN (NASA/NSF 2025), FIRE-VLM (2026), IVSR (2026).
  Prototype WebSocket en cours.
- **Livrable 212 — GeoSylva-Unreal Architecture** : pipeline LiDAR HD IGN
  → arbres individuels (PyCrown), génération procédurale scientifique
  (PCG + landscape data layers), gradient de fidélité (contexte /
  procédural / haute fidélité), synchronisation réel/simulé (CON-010).
  **En attente volontaire** jusqu'à MVP Ignis (règle S-08).

### Documents créés

- `GSIE/ARCHITECTURE/GSIE_IGNIS_GCS_CINEMA_UNREAL.md` (livrable 211)
- `GSIE/ARCHITECTURE/GEOSYLVA_UNREAL_ARCHITECTURE.md` (livrable 212)
- `03_DECISIONS/DEC-000010.md` (adoption UE 5.8 + Cesium)
- `GSIE/RESEARCH/UNREAL_ENGINE_PRECEDENTS.md` (fiches FIRETWIN, FIRE-VLM, IVSR)

### Documents mis à jour

- `GSIE/ARCHITECTURE/GSIE_IGNIS_ARCHITECTURE.md` (208) : ajout référence 211
- `GSIE/ARCHITECTURE/TECHNOLOGY_STACK.md` (202) : ajout ADR-0007 (UE 5.8 +
  Cesium), matrice de compatibilité étendue C++/UE
- `PROJECT_MEMORY.md` : DEC-000010 ajouté, documents d'architecture étendus
- `ROADMAP.md` : livrables 211 et 212 ajoutés

### Architecture partagée Ignis ↔ GeoSylva-Unreal

| Partagé (plugin commun) | Séparé (logique propre) |
|---|---|
| Cesium (terrain géoréférencé) | Niagara feu/fumée (Ignis) |
| WebSockets + JSON natif | PCG végétation (GeoSylva) |
| Conventions de données | Mode d'usage (temps réel vs planification) |

Recommandation : un seul projet Unreal en plugins internes (CON-007).

---

## [PHASE 2 — QUICK WINS] - 2026-07-12

### Audit global des 10 livrables Phase 2

Audit parallèle des 10 livrables (201-210) + 14 moteurs contre les critères
de complétude Phase 2. Scores : 201 (8→9), 202 (7), 203 (6), 204 (8.5→9),
205 (8→9), 206 (5 — point faible), 207 (97/100→100), 208 (6), 209 (6.5),
210 (5.5).

### Corrections apportées (4 quick wins initiaux)

- **Livrable 201 — Master Architecture** (524→717 lignes) : ajout des
  références sources scientifiques (mapping domaine → `GSIE/RESEARCH/` /
  `GSIE/DATASETS/`), liaison explicite des principes constitutionnels
  (CON-001 à CON-010), section modes dégradés (hors-ligne vs en ligne par
  moteur), esquisse des contrats d'interface (table inputs/outputs).
- **Livrable 204 — Development Order** (365→416 lignes) : en-tête complété
  (CON-004, CON-005, T-7), incohérence graphe Climate↔GIS corrigée, note
  de cohérence avec livrable 206, positionnement explicite des moteurs
  transverses (Forest Dynamics, Simulation, Learning), colonne Catégorie
  dans le tableau synthétique.
- **Livrable 205 — Scientific Data Model** (797→1179 lignes) : entité
  Peuplement (Stand) ajoutée, entités Forest Dynamics (GrowthModel,
  ForestProjection) ajoutées, entités de sortie spécifiées
  (DiagnosticReport, RecommendationSet, SimulationResult), section
  contraintes d'intégrité (règles de validation par domaine), diagramme
  et cardinalités mis à jour.
- **Livrable 207 — Simulation Engine** : format dépendances harmonisé
  (Type | Cible | Nature), contrat d'interface harmonisé (notation
  `champ : type`), titres cas d'usage standardisés (« Cas 1 — », « Cas 2 — »).

### Corrections apportées (vague 2 — complétion)

- **Livrable 202 — Technology Stack** : audit confirmé — ADR-0002/0003/0004
  déjà complets (Python, Rust, Go, TypeScript). Aucune modification nécessaire.
- **Livrable 203 — Communication Protocol** (6→8/10) : ajout §6.5
  priorisation des messages (critique/important/normal), §6.6 limites et
  mode dégradé (taille de file, comportement sur dépassement), §6.7 codes
  d'erreur offline, lien CON-003.
- **Livrable 206 — Interface Contracts** (5→9/10, 140→1223 lignes) :
  en-tête complété, types communs (SourceReference, EvidenceLevel,
  ConfidenceLevel, EmpriseGeographique, PeriodeTemporelle, IntervalleConfiance,
  IntervalleValeur), schémas formels des 14 moteurs (entrée + sortie +
  messages transverses), garanties de service par interaction (mode, latence,
  retry, timeout, idempotence), codes d'erreur par moteur, versioning SemVer
  des contrats, tests d'interface (conformité schéma, contrat comportemental,
  intégration inter-moteurs).
- **Livrable 208 — Ignis Architecture** (6→9/10, 549→847 lignes) :
  alignement DIR-0005 (§2bis — jumeau numérique vivant : terrain comme
  interface, zoom progressif, ADR-001 moteur 3D interchangeable, trois
  usages d'un socle, immersion), alignement DIR-0006 (§2ter — moteur
  cognitif : assimilation probabiliste, observateurs, graphe vivant,
  raisonnement multi-échelle/temporel/probabiliste, intelligence distribuée,
  IA collaborative, mémoire, explicabilité, auto-évaluation, curiosité
  artificielle sous supervision humaine, anticipation « signale et propose »,
  moteur scientifique), garde-fous RFC-0004 §8 référencés (non dupliqués).
- **Livrable 209 — Ignis Data Pipeline** (6.5→9/10, 569→829 lignes) :
  alignement DIR-0006 (§10 assimilation probabiliste multi-observateurs avec
  tableau de 16 observateurs, §11 raisonnement multi-échelle pixel→pays,
  §12 auto-évaluation + curiosité artificielle sous supervision humaine),
  alignement DIR-0005 (§13 présentation immersive du jumeau numérique,
  terrain comme interface, moteur 3D interchangeable, zoom progressif,
  interactions contextuelles), références DIR-0005/0006 ajoutées.
- **Livrable 210 — Drone Architecture** (5.5→8.5/10, 506→642 lignes) :
  alignement DIR-0006 (§11.1 drone comme observateur avec tableau capteurs,
  §11.2 intelligence distribuée, §11.3 curiosité artificielle sous supervision
  humaine), alignement DIR-0005 (§11.5 alimentation du jumeau numérique vivant,
  interactions au clic drone), sources externes (IGN, Météo-France, Copernicus),
  garde-fous RFC-0004 §8 référencés via §5.2 et §7.5 existants.

### Bilan Phase 2

Tous les livrables Phase 2 (201-210) sont maintenant Draft avec un niveau
de complétude suffisant pour passage en Review. Les 10 livrables respectent
les directives fondatrices DIR-0005/0006 et les garde-fous RFC-0004 §8.

---

## [GSIE-IGNIS — VISION MOTEUR COGNITIF] - 2026-07-12

### DEC-000009 — GSIE-DIR-0006 : le moteur cognitif Ignis

- **GSIE-DIR-0006** — Directive fondatrice compagnon de DIR-0005. Fixe la
  vision du **moteur cognitif** Ignis (le cerveau serveur).
- **Articulation** : DIR-0005 = « Le moteur graphique montre le monde. » ;
  DIR-0006 = « Le moteur cognitif le comprend. »
- **Principes** : le serveur n'est pas un backend mais un système
  d'intelligence (scientifique : collecte, compare, doute, vérifie, corrige,
  prédit, explique, apprend) ; assimilation permanente par fusion
  probabiliste multi-source ; monde comme graphe vivant de relations ;
  raisonnement multi-échelle, temporel et probabiliste ; simulation
  permanente même sans utilisateur ; intelligence distribuée (agents
  spécialisés) et IA collaborative (orchestration de modèles) ; mémoire
  versionnée ; explicabilité, auto-évaluation, curiosité artificielle,
  anticipation ; moteur scientifique (test de théories/IA/simulations).
- **Vision à long terme** : le feu n'est que le premier domaine ; architecture
  conçue pour s'étendre (santé des forêts, biodiversité, tempêtes, sécheresses,
  risques naturels, logistique de crise, gestion des territoires). Rejoint la
  vocation du moteur GSIE et de l'écosystème Quintessences.
- **Cadrage explicite** : curiosité artificielle et anticipation produisent
  des **propositions** sous supervision humaine — jamais de déclenchement
  automatique de mission, d'alerte ou d'intervention (RFC-0004 §8.3/§8.4,
  GSIE-CON-001). Agents = responsabilité unique, fusion explicable
  (GSIE-CON-007, GSIE-CON-004). Apprentissage versionné (GSIE-CON-010).
- **Statut** : `Draft` (en attente de validation du Fondateur).
- **Traçabilité** : `DEC-000009` acte l'adoption ; `PROJECT_MEMORY.md`,
  `ROADMAP.md` synchronisés.
- **Impact** : oriente les livrables Phase 2 n°208-210 (architecture
  Ignis) et les moteurs Reasoning / Correlation / Learning / Simulation.

---

## [GSIE-IGNIS — DIRECTIVE FONDATRICE GCS] - 2026-07-12

### DEC-000008 — GSIE-DIR-0005 : jumeau numérique vivant

- **GSIE-DIR-0005** — Directive fondatrice Ignis (GCS / Ground Control
  System). Fixe la vision produit : Ignis est un **jumeau numérique
  vivant** des opérations de lutte contre les incendies, pas un logiciel de
  cartographie, de drones ou de simulation.
- **Principes** : le terrain devient l'interface unique ; le moteur 3D
  (Unreal Engine ou successeur) est **interchangeable** et ne contient
  **aucune logique métier** (l'intelligence reste dans GSIE) ; un seul socle,
  trois usages (Opération, Formation, Recherche).
- **Cadrage explicite de l'autonomie** : la section « Autonomie » (intention
  vs commande) est cadrée par référence prioritaire à RFC-0004 §8.3/§8.4 —
  l'autonomie d'intention porte sur la sélection des moyens d'observation et
  la navigation ; la décision d'alerte, l'intervention et le commandement
  restent humains (COS / CODIS) ; reprise manuelle toujours possible ;
  aucune alerte directe à la population (FR-Alert).
- **Statut** : `Draft` (en attente de validation du Fondateur).
- **Traçabilité** : `DEC-000008` acte l'adoption ; `PROJECT_MEMORY.md`,
  `ROADMAP.md` synchronisés.
- **Impact** : oriente les livrables Phase 2 n°208-210 (architecture
  Ignis) et les futures spécifications.

---

## [GSIE-IGNIS — BANC DE SIMULATION] - 2026-07-12

### Premier vol drone réussi + 4 tests de vol avancés

- **PX4 SITL v1.18.0-beta1 + Gazebo Harmonic 8.14.0** opérationnels en
  headless sur WSL2
- **Diagnostic et résolution** du blocage au décollage (modèle x500_base
  sans plugins moteurs + setpoint de position insuffisant → setpoint de
  vélocité)
- **Test 1 — Premier vol** : décollage → 34 m → stabilisation → atterrissage ✓
- **Test 2 — Vol waypoint** : navigation 5 waypoints GPS (carré 100 m) ✓
- **Test 3 — Pattern carré** : surveillance 200 m × 200 m à 8 m/s ✓
- **Test 4 — Return-to-Home** : décollage + 150 m Nord + RTL (partiel :
  RTL activé mais atterrissage non complété en 60 s)
- **Test 5 — Surveillance incendie** : pattern lawnmower 4 lignes × 200 m
  avec capture de positions GPS (simulation observation front de feu)
- Scripts : `premier_vol.py`, `vol_waypoint.py`, `vol_pattern_carre.py`,
  `vol_rth.py`, `vol_surveillance_incendie.py`, `run_test.sh`
- ForeFire : compilation + démo propagation.png (Étape 2 validée)

---

## [PHASE 2 — DÉMARRAGE EFFECTIF] - 2026-07-12

### Production de l'architecture (10 livrables)

Démarrage effectif de la Phase 2 (Architecture) avec 3 axes en parallèle :

1. **Architecture des 14 moteurs** — contrats d'interface, entrées/sorties,
   dépendances, garanties, cas d'usage pour chaque moteur + matrice
   d'interactions croisée.
2. **Architecture technique globale** — stack technologique (ADR), protocole
   de communication offline-first, ordre de développement, modèle de données
   scientifique, architecture globale enrichie.
3. **Architecture Ignis** — pipeline de données (ForeFire, drone, GCS),
   architecture drone (PX4, MAVSDK, YOLO), intégration avec les 14 moteurs,
   garde-fous DEC-000003.

ROADMAP.md enrichi avec 10 livrables Phase 2 (201-210) et critères de
complétude.

README réécrit au niveau enterprise : badges, problem statement, tableau
comparatif avec la concurrence, architecture visuelle, gouvernance
constitutionnelle, roadmap, contributing.

---

## [RESTRUCTURATION IDENTITÉ] - 2026-07-12

### DEC-000006 — Quintessences, GSIE, GeoSylva

- **Quintessences** devient l'**écosystème** (marque umbrella) regroupant
  toutes les spécialisations environnementales.
- **GSIE** est redéfini : **General System Intelligence Engine** (avant :
  GeoSylva Intelligence Engine). C'est le **moteur** spécialisable par
  domaine, au cœur de Quintessences.
- **GeoSylva** est repositionné comme **app forestière** (première
  spécialisation de GSIE), au même titre que Ignis (spécialisation
  incendie). GeoSylva garde son nom historique.
- Architecture : `Quintessences > GSIE > GeoSylva / Ignis / futures`.
- README, PROJECT_MEMORY, ROADMAP, CHANGELOG, LICENSE mis à jour.
- La Constitution, les 14 moteurs, la gouvernance et la traçabilité
  restent valables — GSIE est généralisé, pas remplacé.

---

## [PHASE 2 — Architecture] - 2026-07-12

### DEC-000005 — Amendement : archivage du code du banc Ignis

- Le Fondateur **amende** DEC-000003 et DEC-000004 pour autoriser
  l'archivage du code du banc de simulation (Jalon 0) dans
  `apps/Ignis/`.
- Périmètre : `premier_vol.py`, `plot_front.py`, scripts `*.sh` du banc.
- Statut : **artefacts d'archive**, pas du code métier des 14 moteurs.
- Le banc opérationnel reste dans `~/Ignis/` (WSL2) ; le dépôt n'en
  conserve qu'une archive versionnée pour reproductibilité et traçabilité.
- L'interdiction de code métier GSIE dans le dépôt (Phase 4) reste entière.

### DEC-000004 — Entrée en Phase 2

- **Phase 1 clôturée** — tous les livrables Validated (9/12) ou Locked
  (3/12).
- **Phase 2 (Architecture) activée** par le Fondateur.
- Autorise : architecture détaillée des moteurs, spécifications
  techniques, RFC d'architecture, banc de simulation Ignis.
- N'autorise pas encore : code métier dans le dépôt GSIE (Phase 4).

### Banc de simulation Ignis — démarrage

- `.wslconfig` créé (20GB RAM, 6 CPU, 8GB swap).
- État WSL constaté : Ubuntu 24.04.3 LTS, Python 3.12.3, 8 threads,
  948 Go dispo sur E:.
- Installation du socle logiciel en cours (cmake, build-essential,
  libnetcdf-dev).
- Prochaines étapes : ForeFire (compilation + démo Aullène), PX4 SITL
  + Gazebo, structure projet `~/Ignis/`.

---

## [PHASE 1 CLÔTURÉE] - 2026-07-12

### Tous les livrables Validated ou Locked

La Phase 1 (Foundation) est **clôturée**. Les 12 livrables sont
dans un statut terminal :

| Statut | Count | Livrables |
|---|---|---|
| Validated | 9 / 12 | 001, 005, 006, 007, 008, 009, 010, 011, 012 |
| Locked | 3 / 12 | 002, 003, 004 |

### Livrable 011 — Documentation (Validated)

- `CODING_STANDARDS.md` : enrichi (11 → 82 lignes) — conventions nommage,
  structure fonctions, gestion d'erreurs, tests, typage, imports.
- `DEVELOPMENT_PLAYBOOK.md` : enrichi (17 → 68 lignes) — cycle de vie
  Spec→Impl→Tests→Review→Merge, commits conventionnels, ADR.
- `MASTER_ROADMAP.md` : enrichi (20 → 55 lignes) — aligné sur ROADMAP.md
  racine, 5 phases avec jalons et critères de succès.
- `PROJECT_EXECUTION_PLAN.md` : enrichi (16 → 64 lignes) — 9 étapes,
  6 jalons (M1-M6), dépendances entre livrables.
- `CONTRIBUTING_GUIDE.md`, `DOCUMENTATION_SYSTEM.md`,
  `WRITING_GUIDELINES.md` : statuts normalisés → Validated.
- `ENGINEERING_HANDBOOK_TOME_I_CHAPTER_1.md` : en-tête de statut ajouté.
- `MASTER_IMPLEMENTATION_GUIDE.md` : `Statut : Validated` ajouté
  (contenu non touché, v0.6.1 préservée).
- `ENGINEERING_HANDBOOK_TOME_I_CHAPTER_1.docx` : **supprimé** (le .md est
  la source de vérité, pas de binaire dans le dépôt).

### Livrable 010 — Articles CON-001 à CON-010 (Validated)

Les 10 articles constitutionnels ont été mis en conformité avec le
template RFC-0001 (ADOPTÉ) et validés :

- `GSIE-CON-001.md` à `GSIE-CON-010.md` : enrichis avec sections
  Exemple, Contre-exemple, Références, Historique, Statut.
- CON-008 (20 → 74 lignes) et CON-009 (21 → 70 lignes) : enrichis
  avec Conséquences, Exemple, Contre-exemple, Références.
- Tous passent de `Draft (À valider)` à `Validated`.

### Livrable 012 — Mémoire (Validated)

- `FOUNDER_JOURNAL.md` : enrichi (23 → 112 lignes) — 6 entrées datées
  (2026-07-01 à 2026-07-12) au format Décisions/Motivations/Impact.
- `CONTEXT_SNAPSHOT_001.md` : statut clarifié → `Draft — en attente du
  10e Directive`.
- `README.md` (`22_PROJECT_MEMORY/`) : `Ignis.md` et sous-dossier
  `Ignis/` ajoutés à la liste des fichiers autorisés.

### Prochaine étape

Le projet peut entrer en **Phase 2 (Architecture)** après décision du
Fondateur. Le banc de simulation Ignis (`~/Ignis/` WSL2) peut
démarrer indépendamment — il vit hors du dépôt GSIE.

---

## [Livrable 012 Validated] - 2026-07-12

### Mémoire du projet — livrable 012 passé en Validated

Le livrable 012 (Mémoire du projet et snapshots) passe de `Draft` à
`Validated` après audit et enrichissement :

- **`FOUNDER_JOURNAL.md`** : enrichi avec les entrées manquantes
  (2026-07-01 à 2026-07-12). Six entrées datées au format
  Décisions / Motivations / Impact, retraçant la fondation, l'outillage
  Claude Code, l'audit de conformité, l'ouverture des RFC-0002/0003/0004,
  la validation des livrables 005-009 et des articles CON-001 à 010.
- **`CONTEXT_SNAPSHOT_001.md`** : statut « Réservé » remplacé par
  « Draft — en attente du 10e Directive (non atteint) ». Note explicite
  ajoutée : le snapshot sera déclenché à la 10e Directive.
- **`README.md`** (`22_PROJECT_MEMORY/`) : `Ignis.md` et le sous-dossier
  `Ignis/` ajoutés à la liste des fichiers autorisés.

### Avancement Phase 1

- **Validated** : 8 / 12 (001, 005, 006, 007, 008, 009, 010, 012)
- **Locked** : 3 / 12 (002, 003, 004)
- **Draft** : 1 / 12 (011)

### Mémoire synchronisée

- `ROADMAP.md` : livrable 012 → Validated, avancement global mis à jour.
- `PROJECT_MEMORY.md` (racine) : avancement et prochaine étape mis à jour.

---

## [RFC-0004 Ignis — Registre d'idées] - 2026-07-11

### Registre d'idées opérationnelles

- Création de `apps/Ignis/REGISTRE.md` : registre vivant des idées
  Ignis structuré en 8 domaines (Perception, Jumeau numérique, Vol,
  Communications, GCS, Données, Stratégie) + feuille de route + backlog
  de questions ouvertes. Chaque idée est classée par maturité
  (💡/🔍/✅/⏸️/❌), priorité et notes opérationnelles.

### Mémoire synchronisée

- `PROJECT_MEMORY.md` : RFC-0004 référence désormais le registre
  `apps/Ignis/REGISTRE.md`.
- `02_RFC/RFC-0004.md` : étape 3 des prochaines étapes actionnables
  marquée comme réalisée (registre d'idées ouvert).

---

## [RFC-0004 Ignis] - 2026-07-11

### RFC ouvert

- **RFC-0004** — Ignis : Système autonome de surveillance et d'analyse des
  incendies. Proposition d'une nouvelle branche fonctionnelle dédiée au risque
  incendie, positionnée comme application cliente des 14 moteurs GSIE.
  (`02_RFC/RFC-0004.md`)

### Contenu du RFC

- Vision : détection précoce par drones, caractérisation de l'événement, jumeau
  numérique opérationnel du feu, analyse d'enjeux pour le COS / CODIS, autonomie
  drone sous supervision humaine.
- Exigences : sourçage scientifique, métriques domaine (rappel, faux positifs,
  latence, XAI), cadre réglementaire (EASA, SORA, BVLOS, DGAC, RGPD), injection
  de la connaissance métier forestière / DFCI.
- Écosystème : Pyronear, ForeFire, SDIS / CODIS, Prométhée ; datasets Pyro-SDIS,
  FLAME, D-Fire, FASDD, FIgLib, WildfireSpreadTS ; financements ANR, Horizon
  Europe, DGSCGC, CIFRE.
- Jalon : démonstrateur sans drone sur l'incendie de Landiras (Gironde, 2022).
- Points de vigilance : flou organisationnel (entreprise vs fondation), danger
  de la sortie « cause probable », limite du terme « autonome », interdiction
  d'alerte directe à la population, contrainte Phase 1 (pas de code métier).
- Recommandation : approche hybride — Ignis comme application, extensions
  ciblées des moteurs existants, moteur dédié éventuel réservé à un second RFC.

### Mémoire synchronisée

- `PROJECT_MEMORY.md` : date, RFC-0004 tracé.
- `ROADMAP.md` : RFC-0004 ajouté aux RFC ouverts.

---

## [Ignis gouvernance] - 2026-07-12

### Livrables 005-009 validés (Phase 1)

Les 5 livrables passent de `Review` à `Validated` après audit et
enrichissement par le Fondateur :

- **Livrable 005** — `PACT_FOR_AI_AGENTS.md` : enrichi (18 → 113 lignes).
  Ajout : Objectif, distinction des rôles (dev vs production), cas concrets,
  procédure de violation, anti-patterns, conséquences, historique,
  validation. Conformité template RFC-0001.
- **Livrable 006** — `GSIE-DESIGN-PHILOSOPHY.md` : enrichi (29 → 137
  lignes). Ajout : Objectif, principes numérotés et justifiés, exemples de
  décisions guidées par la philosophie (ForeFire GPL, 14 moteurs, Phase 1),
  cas limites, anti-patterns, conséquences, historique, validation.
- **Livrable 007** — `SCIENTIFIC_CONSTITUTION.md` : sections Historique +
  Validation ajoutées. Contenu inchangé (déjà solide, 168 → 184 lignes).
- **Livrable 008** — `TECHNICAL_CONSTITUTION.md` : sections Historique +
  Validation ajoutées. Contenu inchangé (173 → 190 lignes).
- **Livrable 009** — `AI_CONSTITUTION.md` : sections Historique +
  Validation ajoutées. Contenu inchangé (168 → 184 lignes).

### Avancement Phase 1

- **Validated** : 6 / 12 (001, 005, 006, 007, 008, 009)
- **Locked** : 3 / 12 (002, 003, 004)
- **Draft** : 3 / 12 (010, 011, 012)

### Reste à traiter pour clôturer Phase 1

- **Livrable 010** : articles CON-001 à CON-010 — aucun ne suit le template
  RFC-0001 (manquent Références + Historique). CON-008 et CON-009 (20-21
  lignes) sont très incomplets. À enrichir.
- **Livrable 011** : documentation et guides contributeurs — à évaluer.
- **Livrable 012** : mémoire complète — à évaluer.

### RFC-0004 ADOPTÉ

- **DEC-000003** tracée : adoption du RFC-0004 par le Fondateur. Ignis
  devient officiellement une branche fonctionnelle de GSIE, positionnée comme
  application cliente. Approche hybride retenue (Option C).
- RFC-0004 passe au statut **ADOPTÉ**.

### Registre d'idées Ignis

- `apps/Ignis/REGISTRE.md` : registre vivant créé par le Fondateur
  (version 0.7.x, 60+ idées en 9 sections : perception, jumeau numérique, vol
  drone, communications, GCS, données, stratégie, modèles IA, veille
  concurrentielle).
- `apps/Ignis/` : sous-dossier de livrables du Jalon 0
  (comparatif moteurs de simulation, contexte agent, guide d'installation banc).

### Pack contexte agent archivé

- `Ignis_pack_contexte_agent.zip` : lu et extrait. Contenu :
  `AGENTS.md` (contexte maître session), `LISEZMOI.md`, `Ignis_registre_idees.md`
  (v0.7.2), `Ignis_Phase0_comparatif_moteurs_simulation.md`,
  `Ignis_guide_installation_banc.md`.
- `AGENTS_contexte_session.md` et `guide_installation_banc.md` archivés dans
  `apps/Ignis/` avec note de gouvernance (le code du banc vit
  hors dépôt GSIE, dans `~/Ignis/` WSL2).
- Le zip reste ignoré par git (`.gitignore : *.zip`).

### Corrections de gouvernance appliquées

- **Statut ✅** : redéfini de « validée (intégrée à l'architecture) » en
  « principe accepté (intégration prévue en Phase 2+) » — aucune architecture
  n'est finalisée en Phase 1.
- **Phases renommées** : « Phase 0-6 » → « Ignis Jalon 0-6 » pour éviter la
  collision avec les phases GSIE globales (Phase 1-4). Note de rappel ajoutée.
- **RFC-0004** : §12 « Documents liés » ajouté (référence au registre et au
  sous-dossier Jalon 0).
- `PROJECT_MEMORY.md` : section « Branche Ignis (RFC-0004) » + DEC-000003.
- `ROADMAP.md` : RFC-0004 marqué ADOPTÉ.
- `.gitignore` : `*.zip` ajouté (le pack contexte agent binaire n'est pas
  versionné).

---

## [RFC-0003 + Review 005-009] - 2026-07-07

### RFC ouvert

- **RFC-0003** — Architecture distribuée GSIE-Net : capture la vision du
  Fondateur sur l'architecture offline-first, multi-couches, distribuée et
  orientée données. Activé en Phase 2. (`02_RFC/RFC-0003.md`)

### Livrables passés en Review

Cinq livrables passent du statut `Draft` au statut `Review` — soumis à la
validation du Fondateur :

- Livrable 005 — `PACT_FOR_AI_AGENTS.md`
- Livrable 006 — `GSIE-DESIGN-PHILOSOPHY.md`
- Livrable 007 — `SCIENTIFIC_CONSTITUTION.md`
- Livrable 008 — `TECHNICAL_CONSTITUTION.md`
- Livrable 009 — `AI_CONSTITUTION.md`

### Mémoire synchronisée

- `PROJECT_MEMORY.md` mis à jour : avancement Review 5/12, RFC-0003 tracé.
- `ROADMAP.md` mis à jour : statuts livrables + RFC-0003 + prochaine étape.

---

## [Conformité] - 2026-07-06

### Audit de l'état réel

- Cartographie complète du dépôt (277 fichiers `.md`) confrontée au ROADMAP et
  à la mémoire. Écarts de traçabilité et de conformité identifiés.

### Conformité des statuts (livrables 005, 006, 010)

- Ajout des champs `Statut : À valider` et `Classification : Loi Fondamentale
  (Immuable)` aux articles `GSIE-CON-005` à `GSIE-CON-010` (en-têtes non
  conformes au cycle de vie).
- Ajout d'en-têtes (édition, version, statut) à `PACT_FOR_AI_AGENTS.md` (005)
  et `GSIE-DESIGN-PHILOSOPHY.md` (006).
- Aucun document `Locked` modifié.

### Traçabilité

- `GSIE-DIR-0004` (GSIE Genesis Directive, ACTIVE) désormais tracée dans
  `PROJECT_MEMORY.md` (racine et `22_`). Elle en était absente.

### RFC

- **RFC-0002** ouvert : « Unification du système d'articles constitutionnels »
  (double système `ARTICLE_0xx` vides / `GSIE-CON-0xx` rédigés). Statut
  *Proposé*, en attente de validation du Fondateur. Aucune suppression exécutée.
- `RFC-0003` à `RFC-0010` : coquilles vides remplacées par des en-têtes
  « Réservé — non ouvert » (traçabilité conservée, aucun RFC supprimé).

### Livrables 011 et 012

- Rédaction des fichiers vides de `GSIE/DOCUMENTATION/` : `WRITING_GUIDELINES.md`,
  `DOCUMENTATION_SYSTEM.md`, `CONTRIBUTING_GUIDE.md`, `ADR_TEMPLATE.md` (Draft).
- `CONTEXT_SNAPSHOT_001.md` : en-tête de réservation ajouté (déclenchement prévu
  à la 10ᵉ Directive — non atteint, snapshot volontairement en attente).

### ROADMAP

- Livrable 010 repointé vers la source réelle (`GSIE-CON-0xx`) avec renvoi au
  RFC-0002.
- Requalification honnête des 14 moteurs (3 fichiers dédiés, 11 README de
  cadrage ; documentation complète = Phase 2).
- Mention des dossiers hors 12 livrables (`18_FINANCING`, `23_QUALITY_MANAGEMENT`)
  et de leur statut de gouvernance à statuer.

### Reste à la main du Fondateur

- Choix d'une option pour RFC-0002 (A / B / C).
- Levée ou confirmation de la réserve sur le `Locked` de `GSIE-CON-000`
  (« LOCKED sous réserve de validation du Fondateur »).
- Rattachement de `18_FINANCING` et `23_QUALITY_MANAGEMENT` aux livrables.

---

## [Outillage] - 2026-07-03

### Configuration Claude Code

- Initialisation du dépôt git + `.gitignore`
- `CLAUDE.md` racine (gouvernance opérationnelle pour les agents IA)
- `.claude/` : `settings.json`, hook `guard-locked` (protection des `Locked`),
  6 commandes métier, 3 sous-agents, skill projet `gsie-governance`
- Skills : installation vendorisée et épinglée de `mermaid` (MIT, commit
  `8ab1815`, provenance tracée) ; création de la skill `skill-management`
- `.claude/SKILLS_GSIE.md` : sélection des meilleures skills (internes,
  officielles et communautaires) par phase

---

## [0.0.1] - 2026-07-01

### Fondation

- Création de l'arborescence officielle (22 dossiers numérotés)
- Création de la Constitution : 6 documents transverses + 100 articles
  vides
- Création des RFC-0001 à RFC-0010 (RFC-0001 rédigée)
- Création des décisions DEC-000001 et DEC-000002
- Création de la Directive fondatrice GSIE-DIR-0001
- Création de la mémoire du projet (6 fichiers dans 22_PROJECT_MEMORY)
- Création des README de chaque dossier
- Création des fichiers racine : README, PROJECT_MEMORY, CHANGELOG,
  ROADMAP

### Décisions

- DEC-000001 : GSIE est une Fondation scientifique
- DEC-000002 : Phase 1 — Fondation, aucun développement métier

## [0.0.2] - 2026-07-01

### Documents fondateurs de la Constitution

- Création de `CONSTITUTIONAL_PREAMBLE.md` — autorité, portée,
  classification des lois (Immuables / Évolutives) et hiérarchie
  documentaire
- Création de `PHILOSOPHICAL_PREAMBLE.md` — vision, valeurs et
  convictions fondatrices
- Création de `ARTICLE_000.md` — Primauté de la Constitution (Loi
  Immutable, ADOPTÉ)

### Évolutions de RFC

- RFC-0001 : passage de BROUILLON à ADOPTÉ
- RFC-0001 : ajout des 4 décisions fondatrices
  - D1 : distinction Préambule constitutionnel / Préambule philosophique
  - D2 : introduction de l'Article 000 « Primauté de la Constitution »
  - D3 : classification des lois (Immuables et Évolutives)
  - D4 : hiérarchie documentaire officielle (Vision → Code)

### Mémoire du projet

- Mise à jour de `PROJECT_MEMORY.md` et `DECISION_HISTORY.md` avec les
  décisions fondatrices de RFC-0001

## [0.0.3] - 2026-07-01

### Lancement officiel Phase 1 Foundation (GSIE-DIR-0003)

- Création de la Directive `GSIE-DIR-0003` (ACTIVE)
- Définition des **12 livrables obligatoires** de la Phase 1
- La **documentation devient le produit principal** de la phase
- Aucun développement métier avant validation des 12 livrables

### Fichiers créés

- `GSIE/DOCUMENTATION/CONTRIBUTING_GUIDE.md` (vide — livrable 011)
- `GSIE/DOCUMENTATION/DOCUMENTATION_SYSTEM.md` (vide — livrable 011)
- `GSIE/DOCUMENTATION/ADR_TEMPLATE.md` (vide — livrable 011)
- `GSIE/DOCUMENTATION/WRITING_GUIDELINES.md` (vide — livrable 011)
- `22_PROJECT_MEMORY/CONTEXT_SNAPSHOT_001.md` (vide — livrable 012)

### Fichiers mis à jour

- `ROADMAP.md` — ajout de la Foundation Roadmap (12 livrables + statuts)
- `PROJECT_MEMORY.md` — entrée sur la documentation comme produit principal
- `22_PROJECT_MEMORY/PROJECT_MEMORY.md` — avancement des 12 livrables
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — 3 nouvelles décisions DIR-0003
- `22_PROJECT_MEMORY/VISION_HISTORY.md` — Vision V1.1
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée Phase 1 Foundation

### Décisions

- DIR-0003-D1 : La documentation devient le cœur du projet
- DIR-0003-D2 : 12 livrables obligatoires, produits dans l'ordre
- DIR-0003-D3 : Aucun développement métier avant validation des 12 livrables

## [0.0.4] - 2026-07-01

### Verrouillage officiel des préambules fondateurs

- Rangement de `GSIE-FND-001.md` (Préambule Philosophique) dans
  `00_CONSTITUTION/` — LOCKED, v1.0, Première Édition
- Rangement de `GSIE-FND-002.md` (Préambule Constitutionnel) dans
  `00_CONSTITUTION/` — LOCKED, v1.0, Première Édition
- Suppression des drafts `PHILOSOPHICAL_PREAMBLE.md` et
  `CONSTITUTIONAL_PREAMBLE.md` (remplacés par les éditions officielles)
- Suppression de `PREAMBLE.md` (vide, hérité de l'ancienne structure)

### Avancement des livrables

- Livrable 002 (Préambule Constitutionnel) : Draft → **Locked**
- Livrable 003 (Préambule Philosophique) : Draft → **Locked**
- Total : 2 Validated, 2 Locked, 8 Draft

### Fichiers mis à jour

- `ROADMAP.md` — statuts 002 et 003 → Locked, avancement global
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — références et
  avancement
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — entrées FND-001, FND-002
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée verrouillage
- `02_RFC/RFC-0001.md` — références aux nouveaux noms de fichiers

## [0.0.5] - 2026-07-01

### Articles constitutionnels officiels

- Rangement de `GSIE-CON-000.md` dans `00_CONSTITUTION/` — La Primauté
  de la Constitution (LOCKED, Loi Fondamentale Immuable, v1.0)
- Rangement de `GSIE-CON-003.md` — La Connaissance avant le Code
  (Draft, à valider)
- Rangement de `GSIE-CON-004.md` — Toute décision doit être explicable
  (Draft, à valider)
- Rangement de `GSIE-CON-005.md` — Toute connaissance doit être
  traçable (Draft, à valider)
- Suppression du draft `ARTICLE_000.md` (remplacé par l'édition
  officielle `GSIE-CON-000.md`)

### Avancement des livrables

- Livrable 004 (Article 000) : Validated → **Locked** (édition officielle)
- Livrable 010 (Articles 001-100) : 3 articles rédigés (003, 004, 005)
  en attente de validation
- Total : 1 Validated, 3 Locked, 8 Draft

### Fichiers mis à jour

- `ROADMAP.md` — livrable 004 → Locked, tableau des articles rédigés
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — références et
  avancement
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — entrées CON-000, 003, 004, 005
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée articles officiels

## [0.0.6] - 2026-07-01

### Articles constitutionnels supplémentaires

- Rangement de `GSIE-CON-006.md` — La Documentation fait partie du
  Produit (Draft)
- Rangement de `GSIE-CON-007.md` — La Modularité est obligatoire (Draft)
- Rangement de `GSIE-CON-008.md` — Le Projet appartient à sa Vision
  (Draft)
- Rangement de `GSIE-CON-009.md` — GSIE est un patrimoine scientifique
  vivant (Draft)
- Rangement de `GSIE-CON-010.md` — Toute connaissance doit pouvoir
  évoluer sans perdre son historique (Draft)

### Documents transverses (livrables 005 et 006)

- Rangement de `PACT_FOR_AI_AGENTS.md` dans `00_CONSTITUTION/` — Pacte
  des Agents IA (a remplacé le fichier vide — livrable 005)
- Rangement de `GSIE-DESIGN-PHILOSOPHY.md` dans `00_CONSTITUTION/` —
  Design Philosophy (a remplacé le `DESIGN_PHILOSOPHY.md` vide —
  livrable 006)

### Documents méthodologiques

- Rangement de `ARCHITECTURE_PRINCIPLES.md` dans `GSIE/ARCHITECTURE/`
- Rangement de `RESEARCH_METHOD.md` dans `GSIE/RESEARCH/`
- Rangement de `KNOWLEDGE_METHOD.md` dans `GSIE/KNOWLEDGE/`

### Avancement des livrables

- Livrable 005 (Pacte IA) : rédigé, à valider
- Livrable 006 (Design Philosophy) : rédigé, à valider
- Livrable 010 (Articles) : 9 articles rédigés (000, 003 à 010)
- Total : 1 Validated, 3 Locked, 8 Draft (dont 2 rédigés à valider)

### Fichiers mis à jour

- `ROADMAP.md` — statuts 005/006, tableau des articles (9 rédigés),
  documents transverses et méthodologiques
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — articles, documents,
  avancement, prochaine étape
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — 11 nouvelles entrées
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée second lot

## [0.0.7] - 2026-07-01

### Documents d'architecture

- Rangement de `GSIE_MASTER_ARCHITECTURE.md` dans `GSIE/ARCHITECTURE/` —
  architecture globale en couches
- Rangement de `GSIE_CORE_BLUEPRINT.md` dans `GSIE/ARCHITECTURE/` —
  blueprint du cœur système (chaîne de moteurs)
- Rangement de `GSIE_DATA_FLOW.md` dans `GSIE/ARCHITECTURE/` — flux
  officiel des données

### Moteurs documentés

- Recréation de `GSIE/ENGINES/KNOWLEDGE_ENGINE/` — README + définition
  (`KNOWLEDGE_ENGINE.md`)
- Recréation de `GSIE/ENGINES/CORRELATION_ENGINE/` — README + définition
  (`CORRELATION_ENGINE.md`)
- Création de `GSIE/ENGINES/EVIDENCE_ENGINE/` — nouveau moteur, README +
  définition (`EVIDENCE_ENGINE.md`)

### Fichiers mis à jour

- `ROADMAP.md` — documents d'architecture et moteurs documentés
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — nouvelles sections
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée architecture et moteurs

## [0.0.8] - 2026-07-02

### Genesis Directive (GSIE-DIR-0004)

- Création de la Directive `GSIE-DIR-0004` (ACTIVE, Priorité ABSOLUE,
  Classification FONDATION) dans `01_DIRECTIVES/ACTIVE/`
- Formalisation de l'identité, du rôle de l'agent, de la méthode de
  travail, des qualités prioritaires, des interdictions et de la
  philosophie modulaire
- Liste officielle des **14 moteurs GSIE**
- Liste officielle des **9 bases spécialisées**
- Décision : conservation de l'arborescence existante (22 dossiers),
  la directive s'intègre sans restructurer

### Articles constitutionnels manquants

- Création de `GSIE-CON-001.md` — Le forestier reste le décideur
  (Draft, Loi Fondamentale Immuable). Toute sortie est contournable,
  explicable, non-contraignante. Interdiction de décision automatique.
- Création de `GSIE-CON-002.md` — La science avant tout (Draft, Loi
  Fondamentale Immuable). Aucune connaissance sans source, niveau de
  preuve, traçabilité et révisabilité.

La Constitution compte désormais **11 articles** (CON-000 à CON-010),
tous rédigés.

### Nouveaux moteurs documentés

- Création de `GSIE/ENGINES/FOREST_DYNAMICS_ENGINE/` — dynamique des
  peuplements (nouveau, DIR-0004)
- Création de `GSIE/ENGINES/LEARNING_ENGINE/` — apprentissage (nouveau,
  DIR-0004, subordonné à CON-001 et CON-004)
- Création de `GSIE/ENGINES/SIMULATION_ENGINE/` — simulation de
  scénarios (nouveau, DIR-0004)

`GSIE/ENGINES/` contient désormais **6 moteurs documentés** sur 14.

### Analyse d'architecture

- 7 points de friction identifiés (contradiction Evidence Engine,
  pipeline linéaire, constitutions vides, absence de contrat
  d'interface, stratégie hors-ligne, README racine non aligné)
- Recommandation : ne pas verrouiller les documents d'architecture
  tant que les contradictions ne sont pas résolues

### Fichiers mis à jour

- `ROADMAP.md` — articles 001 et 002, 3 nouveaux moteurs
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — articles et
  moteurs
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — section 2026-07-02,
  6 nouvelles décisions
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée Genesis Directive

### Décisions

- DIR-0004-D1 : Genesis Directive officielle
- DIR-0004-D2 : Liste officielle des 14 moteurs GSIE
- DIR-0004-D3 : Liste officielle des 9 bases spécialisées
- DIR-0004-D4 : Conservation de l'arborescence existante
- CON-001 : Le forestier reste le décideur
- CON-002 : La science avant tout

## [0.0.9] - 2026-07-02

### Constitutions sectorielles (livrables 007, 008, 009)

- Rédaction de `SCIENTIFIC_CONSTITUTION.md` — 7 articles : sources
  acceptées (5 catégories), 6 niveaux de preuve (A-F), conflits
  bibliographiques, révision par RFC, incertitude explicite, 10
  domaines, patrimoine versionné
- Rédaction de `TECHNICAL_CONSTITUTION.md` — 10 articles : modularité,
  couplage faible, subordination code→connaissance, anti-duplication,
  tests obligatoires, versionnement, gestion d'erreurs, **hors-ligne
  (T-8)**, sécurité, dépendances
- Rédaction de `AI_CONSTITUTION.md` — 8 articles : rôle assistant,
  explicabilité, anti-boîte noire, apprentissage encadré, désaccord
  humain, biais affichés, agents IA soumis aux règles, pas de décision
  automatique

### Résolution de la contradiction Evidence Engine (ARCH-D1)

- `GSIE_DATA_FLOW.md` corrigé : Evidence Engine repositionné **avant**
  Knowledge Graph
- `GSIE_CORE_BLUEPRINT.md` corrigé : Evidence Engine repositionné
  **avant** Knowledge Engine
- Cohérence rétablie entre les 3 documents (Data Flow, Core Blueprint,
  README Evidence Engine)

### 14/14 moteurs documentés (ARCH-D2)

Création des 8 moteurs restants avec README (périmètre, principe,
frontières, position) :
- `REASONING_ENGINE/` — raisonnement sur connaissances
- `DIAGNOSTIC_ENGINE/` — diagnostics stationnels
- `RECOMMENDATION_ENGINE/` — recommandations contournables
- `VALIDATION_ENGINE/` — validation des sorties
- `GIS_ENGINE/` — données géospatiales
- `CLIMATE_ENGINE/` — données climatiques
- `PEDOLOGY_ENGINE/` — données pédologiques
- `BOTANICAL_ENGINE/` — flore et taxonomie

### README racine mis à jour

- Section « État du projet » reflète l'état réel (11 articles, 3
  constitutions sectorielles, 14 moteurs)
- Ajout section « Moteurs GSIE » : tableau des 14 moteurs + chaîne
  principale
- Ajout section « Bases spécialisées » : tableau des 9 bases

### Fichiers mis à jour

- `README.md` — sections moteurs et bases, état du projet
- `ROADMAP.md` — 14 moteurs, livrables 007-009 rédigés
- `PROJECT_MEMORY.md` (racine et 22_PROJECT_MEMORY) — constitutions,
  14 moteurs, architecture corrigée
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — 5 nouvelles décisions
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md` — entrée constitutions +
  résolution Evidence Engine + 14 moteurs

### Décisions

- SCI-CON : Constitution Scientifique (livrable 007)
- TECH-CON : Constitution Technique (livrable 008)
- AI-CON : Constitution IA (livrable 009)
- ARCH-D1 : Evidence Engine repositionné en amont de Knowledge Engine
- ARCH-D2 : 14/14 moteurs officiels documentés

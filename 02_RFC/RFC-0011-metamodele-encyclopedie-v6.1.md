# RFC-0011 — Métamodèle v6.1 de l'Encyclopédie de l'Écosystème

| Champ | Valeur |
|---|---|
| **ID** | RFC-0011 |
| **Statut** | Proposé |
| **Phase** | 4 — Implémentation |
| **Créé le** | 2026-07-15 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Impact** | `GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md` (livrable 213), `GSIE/KNOWLEDGE/KNOWLEDGE_METHOD.md` (302), `GSIE/KNOWLEDGE/KNOWLEDGE_GRAPH_SPECIFICATION.md` (304), `GSIE/ARCHITECTURE/ENCYCLOPEDIA_DATABASE_SCHEMA.md` (309), `GSIE/ARCHITECTURE/ENGINE_DATA_SOCLE.md` (310), `01_DIRECTIVES/ACTIVE/GSIE-DIR-0008.md`, `03_DECISIONS/DEC-000012.md`, `03_DECISIONS/DEC-000019.md`, `03_DECISIONS/DEC-000020.md`, `ROADMAP.md` |
| **Lois fondatrices** | GSIE-CON-000 (primauté), GSIE-CON-002 (science), GSIE-CON-003 (connaissance avant code), GSIE-CON-005 (traçabilité), GSIE-CON-010 (historique) |
| **Décision liée** | DEC-000022 (Proposé) |
| **Annexes** | `02_RFC/annexes/annexe-302.md`, `annexe-304.md`, `annexe-309.md`, `annexe-310.md`, `annexe-dir0008.md`, `annexe-dec012-019-020.md`, `annexe-205.md` |

---

## 1. Objet

Cette RFC propose l'adoption du **métamodèle v6.1 de l'Encyclopédie de
l'Écosystème** (livrable 213) en remplacement de la structure
`KnowledgeObject` à 6 types définie par les livrables 302 et 304, et du
schéma de base de données à 4 couches (Neo4j + PostgreSQL + Elasticsearch
+ Jena) défini par le livrable 309.

Le métamodèle v6.2 introduit un **noyau universel de 73 types** organisés
en cinq niveaux (noyau, profils, projections, infrastructure, vision),
avec PostgreSQL 16 + PostGIS comme vérité canonique unique. Les
technologies Neo4j, Elasticsearch, Jena et GraphQL deviennent des
**projections différées**, conditionnées à des besoins mesurés et à un
benchmark Apache AGE en Vague 1.

La v6.2 enrichit la v6.1 (42 types) avec 18 types issus de la passe
écologique du Fondateur : ScaleContext, Phenomenon, EcologicalProcess,
RelationType, SamplingEvent, TraitDefinition, TraitValue, Feature,
FeatureSet, Inference, Question, Hypothesis, Decision, Recommendation,
Scenario, Correlation, EcosystemService, Capability — plus 1 type pour
le GSIE Temporal & Provenance Engine (ResourceDiff, type 61), portant
le noyau à 73 types.

Cette RFC **supersède explicitement** trois livrables Validated (302,
309, 310) et **amende** une directive Active (GSIE-DIR-0008) et trois
décisions (DEC-000012, DEC-000019, DEC-000020) via la décision unique
DEC-000022.

---

## 2. Contexte et motivation

### 2.1 Origine

Le Fondateur a exprimé l'intention de construire non pas une simple base
de données, mais une **mémoire scientifique du fonctionnement des
écosystèmes** (session 2026-07-15, archivée dans
`22_PROJECT_MEMORY/sessions/`). Une première proposition v5 (110 classes,
8 couches, 6 registres) a été produite par un agent puis **archivée comme
non adoptée** après audit critique : sur-ingénierie, mélange de
niveaux, FK polymorphes, absence de bitemporalité, non-représentation
des absences et des données sensibles.

Une convergence v6.1 a été produite et auditée. L'audit a identifié
**19 corrections** (5 P0, 8 P1, 6 P2) et **3 contradictions P0** avec des
livrables Validated existants. Tous les arbitrages ont été tranchés par
le Fondateur (voir §5).

### 2.2 Problèmes résolus

| Problème | Source | Solution v6.1 |
|---|---|---|
| `KnowledgeObject` à 6 types trop limité | Livrable 302 | Noyau 73 types avec `Assertion` unifiée |
| `evidence_level` direct sur KnowledgeObject | Livrable 302, code actuel | `EvidenceAssessment` multiples (type 13) |
| 4 couches de stockage (Neo4j+PG+ES+Jena) prématurées | Livrable 309 | PostgreSQL 16 canonique, autres différés |
| Pas de bitemporalité | Audit F-P1-02 | `TemporalContext` + **GSIE Temporal & Provenance Engine** (Revision + Snapshot + ResourceDiff + PROV-O, ADR-002) |
| Pas de représentation des absences | Audit F-P0-05 | `Result.value_type='absence'` + `sampling_effort` |
| Pas de confidentialité / données sensibles | Audit F-P1-05 | 4 types (37-40) + RLS + propagation |
| FK polymorphes `target_type/target_id` | Audit F-P1-03 | Racine `Resource` unique, FK fortes |
| Pas de distinction data_provider / knowledge_provider | Audit F-P1-10 | `Source.source_nature` (6 valeurs) |
| Pas de canal d'ingestion typé | Audit F-P1-09 | `Distribution.access_method` (11 valeurs, 6 niveaux) |
| Conflits Assertion↔Assertion non représentés | Audit F-P2-05 | `ConflictCluster` (type 42) |
| Pas de versionnement de dataset | Audit F-P1-06 | `Dataset` + `DatasetVersion` + `Distribution` + `DataAsset` |
| Pas de versionnement de modèle | Audit F-P1-07 | `ModelVersion` (type 41) |
| `claim_kind` fusionné avec `lifecycle_status` | Audit F-P1-01 | Séparation en deux enums |
| Indépendance API non modélisée | Arbitrage Fondateur | `DataAsset.archived_from` + checksum + original_uri |

### 2.3 Pourquoi pas v6.2 ?

L'audit a conclu qu'une nouvelle convergence n'est pas nécessaire. Les
19 corrections sont **locales et intégrables** dans RFC-0011. La
structure fondamentale de la v6.1 (cinq niveaux, Assertion unifiée,
Concept versionné, Citation locator, Outbox/Inbox différés, PG16
canonique) est saine et compatible avec la Constitution.

---

## 3. Solution proposée

### 3.1 Métamodèle v6.1 (livrable 213)

Le métamodèle complet est défini dans
`GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md` (73 types noyau v6.2). Cette
RFC en propose l'adoption.

**Cinq niveaux** :
- **A — Noyau universel** (73 types) : indépendant du domaine
- **B — Profils métier** (différés) : spécialisations par domaine
- **C — Projections standards** (différées) : STAC, OGC, Darwin Core, PROV-O
- **D — Infrastructure** (spécifiée, implémentation différée) : ConnectorRegistry, Outbox, object storage
- **E — Vision long terme** (différée) : services écosystémiques, jumeaux numériques

**73 types du noyau** (détail dans ECOSYSTEM_METAMODEL.md §3) :
1-8 : Identité + référentiels (Entity, EntityAlias, Concept, ConceptVersion, Vocabulary, VocabularyRelease, ControlledTerm, Instance)
9-13 : Assertions (Assertion, AssertionParticipant, AssertionQualifier, Predicate, EvidenceAssessment)
14-19 : Observations (Observation, Result, Method, Instrument, Uncertainty, QualityAssessment)
20-24 : Provenance (Activity, ProvEntity, Agent, Source, Citation)
25-28 : Contextes (Unit, Place, TemporalContext, Media)
29-30 : Versionnement (Revision, Snapshot)
31-32, 41 : Modèles (Model, ModelRun, ModelVersion)
33-36 : Datasets (Dataset, DatasetVersion, DataAsset, Distribution)
37-40 : Confidentialité (RightsStatement, AccessPolicy, SensitivityClassification, SpatialDisclosurePolicy)
42 : Conflits (ConflictCluster)
43 : Échelle (ScaleContext)
44-45 : Phénomènes + processus (Phenomenon, EcologicalProcess)
46 : Typologie des relations (RelationType)
47 : Échantillonnage (SamplingEvent)
48-49 : Traits fonctionnels (TraitDefinition, TraitValue)
50-52 : IA/ML (Feature, FeatureSet, Inference)
53-57 : Raisonnement (Question, Hypothesis, Decision, Recommendation, Scenario)
58 : Corrélations (Correlation)
59 : Services écosystémiques (EcosystemService)
60 : Orchestration (Capability)
61 : Diff de révision (ResourceDiff) — GSIE Temporal & Provenance Engine
62 : Échantillon physique (Sample) — mapping SOSA/SSN
63-64 : RGPD (Consent + DataSubject) — conformité art. 6 + 9.2.j
65 : Identifiants persistants (PersistentIdentifier) — FAIR F1 (DOI, PURL, ORCID)
66 : Flux écologiques (Flow) — carbone, eau, nutriments, énergie, graines, gènes, pathogènes
67 : Graphe de confiance (ConfidenceGraph) — propagation d'incertitude
68-69 : Objectifs + contraintes (Goal + Constraint) — orientent et limitent les décisions
70 : Lignage de connaissance (KnowledgeLineage) — DAG explicite A → B → Recommendation → Decision
71 : Expériences scientifiques (Experiment) — série de ModelRuns avec comparaison
72 : Missions terrain (TerrainSession) — mission GeoSylva (météo, GPS, martelage, inventaire)
73 : État écologique (EcologicalState) — santé, vitalité, risque, résilience synthétiques

### 3.2 Architecture technique

| Couche | Technologie | Statut |
|---|---|---|
| Relationnel | PostgreSQL 16 + PostGIS 3.4 | **Vérité canonique** (Vague 1) |
| Bitemporalité | **GSIE Temporal & Provenance Engine** (moteur métier) | Vague 1 (ADR-002) |
| Graphe | Apache AGE (extension PG) | Benchmark Vague 1 (ADR-003) |
| Graphe natif | Neo4j | **Différé** — si AGE ne passe pas le seuil |
| Recherche full-text | Elasticsearch / OpenSearch | **Différé** — PG trigram + GIN en Vague 1 |
| Sémantique | Apache Jena (RDF/OWL) | **Différé** — projection régénérable |
| API | REST (FastAPI) | Vague 1 |
| API | GraphQL | **Différé** — pas de besoin en Vague 1 |
| Object storage | MinIO (dev) / S3 (prod) | Différé (ADR-006) |

### 3.3 Séquencement

| Vague | Durée | Contenu |
|---|---|---|
| 0 | ~2 semaines | RFC + DEC + 6 ADR + tests contractuels Evidence + contrats interface + audit migration |
| 1 | ~4 semaines | 73 types implémentés + migration schéma + benchmark AGE + Essence 360° |
| 2+ | — | Profils métier + ingestion massive + projections standards |

---

## 4. Superseding et amendements

Cette RFC supersède ou amende les documents suivants. Chaque
superseding est détaillé dans une **annexe séparée** (voir §8). Le
contenu historique des documents supersédés est **conservé intact**
(principe d'archivage, pas de suppression).

### 4.1 Livrables supersédés

| Livrable | Titre | Statut | Action | Annexe |
|---|---|---|---|---|
| 302 | Knowledge Method | Validated | **Supersédé** — structure KnowledgeObject remplacée par Assertion + EvidenceAssessment | `annexe-302.md` |
| 304 | Knowledge Graph Specification | Validated | **Supersédé** — topologie Neo4j remplacée par tables PG + AGE | `annexe-304.md` |
| 309 | Encyclopedia Database Schema | Validated | **Supersédé** — 4 couches (Neo4j+PG+ES+Jena) remplacées par PG canonique | `annexe-309.md` |
| 310 | Engine Data Socle | Validated | **Supersédé** — contrats moteurs basés sur KnowledgeObject 6 types → Assertion claim_kind | `annexe-310.md` |

### 4.2 Directive amendée

| Directive | Section | Action | Annexe |
|---|---|---|---|
| GSIE-DIR-0008 | §2.1 (Neo4j recommandé) | **Amendée** — PG canonique, Neo4j différé | `annexe-dir0008.md` |
| GSIE-DIR-0008 | §2.3 (Jena RDF/OWL) | **Amendée** — Jena différé, projection régénérable | `annexe-dir0008.md` |
| GSIE-DIR-0008 | §2.4 (GraphQL + REST) | **Amendée** — REST seul en Vague 1, GraphQL différé | `annexe-dir0008.md` |

### 4.3 Décisions amendées

| Décision | Sujet | Action | Annexe |
|---|---|---|---|
| DEC-000012 | Encyclopédie (ADR Neo4j/Jena/ES/GraphQL) | **Amendée** — ADR remplacés par ADR-001 à ADR-006 | `annexe-dec012-019-020.md` |
| DEC-000019 | Architecture Phase 4 (plan 24 semaines) | **Amendée** — Vague 0 ajoutée, Vague 1 étendue (73 types) | `annexe-dec012-019-020.md` |
| DEC-000020 | Knowledge Engine (Python in-memory) | **Amendée** — transition vers schéma v6.1 en Vague 0/1 | `annexe-dec012-019-020.md` |
| DEC-000021 | Pipeline intégré Evidence→Knowledge | **Amendée** — pipeline adapté au schéma v6.1 (KnowledgeObject → Assertion, adaptateur Rust+Python) | `annexe-dec012-019-020.md` |

### 4.4 Livrable Draft annoté

| Livrable | Titre | Statut | Action | Annexe |
|---|---|---|---|---|
| 205 | Scientific Data Model | Draft | **Annoté** — `evidence_level` direct → EvidenceAssessment, entités → Resource | `annexe-205.md` |

### 4.5 Livrables non supersédés (valides)

| Livrable | Raison |
|---|---|
| 305 (Dataset Catalog) | Catalogue de datasets — toujours valide, alimente `Dataset` (type 33) |
| 306 (Evidence Framework) | Niveaux A-F — toujours valide, utilisé par `EvidenceAssessment` (type 13) |
| 308 (Knowledge Base Seed) | 25 connaissances — à migrer vers le schéma v6.1 (ADR-004) |

---

## 5. Arbitrages Fondateur (19 corrections + 4 arbitrages additionnels)

Tous les arbitrages ont été tranchés par le Fondateur lors de la session
du 2026-07-15. Ils sont intégrés dans le métamodèle v6.1 et dans cette
RFC.

### 5.1 Corrections P0 (5)

| # | Correction | Arbitrage | Intégré dans |
|---|---|---|---|
| 1 | Cartographier superseding (302, 304, 309, 310, DIR-0008) | RFC-0011 + DEC-000022 unique | §4 + annexes + DEC-000022 |
| 2 | Ajouter FeatureOfInterest | Sous-type d'Entity (`type='feature_of_interest'`) — pas de nouveau type | ECOSYSTEM_METAMODEL §3.2 type 1 + type 14 |
| 3 | Représentation des absences | `Result.value_type='absence'` + `sampling_effort`/`detection_probability` sur Observation | ECOSYSTEM_METAMODEL §3.2 type 14-15 + §3.5 |
| 4 | Séparer claim_kind de lifecycle_status | `claim_kind` (7 valeurs) + `lifecycle_status` (6 valeurs) | ECOSYSTEM_METAMODEL §3.3 + §3.4 |
| 5 | Compléter TemporalContext bitemporel | **GSIE Temporal & Provenance Engine** (Revision + Snapshot + ResourceDiff, ADR-002) | ECOSYSTEM_METAMODEL §3.2 type 27 + §5 + ADR-002 |

### 5.2 Corrections P1 (8)

| # | Correction | Arbitrage | Intégré dans |
|---|---|---|---|
| 6 | Supprimer FK polymorphes (QualityAssessment, Citation) | Racine `Resource` unique, FK vers `resource.id` | ECOSYSTEM_METAMODEL §3.1 + §6 + ADR-001 |
| 7 | Ajouter sampling_effort + detection_probability | Sur Observation (pas de nouveau type) | ECOSYSTEM_METAMODEL §3.2 type 14 |
| 8 | Ajouter RightsStatement, AccessPolicy, SensitivityClassification, SpatialDisclosurePolicy | 4 types au noyau (37-40) | ECOSYSTEM_METAMODEL §3.2 types 37-40 + §11 |
| 9 | Ajouter Dataset, DatasetVersion, Distribution, DataAsset | 4 types au noyau (33-36) | ECOSYSTEM_METAMODEL §3.2 types 33-36 |
| 10 | Trancher ModelVersion | Entité versionnée (type 41, comme ConceptVersion) | ECOSYSTEM_METAMODEL §3.2 type 41 |
| 11 | Trancher AssertionRevision vs Revision générique | Revision générique (type 29) | ECOSYSTEM_METAMODEL §3.2 type 29 |
| 12 | Distribution.access_method typé (6 niveaux) | Enum 11 valeurs (§3.7) | ECOSYSTEM_METAMODEL §3.2 type 36 + §3.7 |
| 13 | Source.source_nature (6 valeurs) | Enum (§3.6) | ECOSYSTEM_METAMODEL §3.2 type 23 + §3.6 |

### 5.3 Corrections P2 (6)

| # | Correction | Arbitrage | Intégré dans |
|---|---|---|---|
| 14 | ADR ConnectorRegistry : knowledge_extractor | Type de connecteur dans ADR-005 | ECOSYSTEM_METAMODEL §9.1 |
| 15 | DataAsset.archived_from + checksum + original_uri | Champs sur DataAsset (type 35) | ECOSYSTEM_METAMODEL §3.2 type 35 |
| 16 | Prédicat contredit ou ConflictCluster | ConflictCluster (type 42) | ECOSYSTEM_METAMODEL §3.2 type 42 |
| 17 | Propagation restrictions vers dérivés | Règle : dérivés héritent des restrictions des inputs | ECOSYSTEM_METAMODEL §11.2 |
| 18 | Amendement ROADMAP.md après adoption | Vague 0 (post-adoption) | §7 + todo mise à jour mémoire |
| 19 | Documenter écart engine.py ↔ knowledge_models.py | ADR-004 (audit migration Vague 0) | ADR-004 |

### 5.4 Arbitrages structurels additionnels

| # | Sujet | Arbitrage | Intégré dans |
|---|---|---|---|
| A1 | Superseding | RFC-0011 + DEC-000022 unique (un seul vote) | §4 + DEC-000022 |
| A2 | Noyau 73 types (42 v6.1 + 18 v6.2) | Accepté, chacun justifié | ECOSYSTEM_METAMODEL §14 |
| A3 | Racine relationnelle | Table `resource` unique, class-table inheritance | ECOSYSTEM_METAMODEL §3.1 + ADR-001 |
| A4 | Subagents sources | 10 domaines + 10 types (parallèle, autre agent) | Hors périmètre RFC — voir SOURCES_CATALOG.md |
| T1 | Bitemporalité | GSIE Temporal & Provenance Engine (Revision + Snapshot + ResourceDiff + PROV-O) | ADR-002 |
| T2 | AGE | Benchmark Vague 1 | ADR-003 |
| T3 | Vague 1 scope | 73 types dès le départ | ECOSYSTEM_METAMODEL §13 |
| T4 | Evidence adapter | Rust évalue (A-F) + Python enrichit | ADR-004 + §6.2 |
| P1 | RFC structure | Principal + annexes séparées | Cette RFC + §8 |
| P2 | Vague 0 | RFC + 6 ADR + tests contractuels + contrats interface | ECOSYSTEM_METAMODEL §13 |
| P4 | Source.source_nature | 6 valeurs | ECOSYSTEM_METAMODEL §3.6 |

---

## 6. Impact

### 6.1 Documents modifiés

| Document | Impact | Type |
|---|---|---|
| ECOSYSTEM_METAMODEL.md (livrable 213) | **Créé** (v6.1, 654 lignes) | Nouveau |
| KNOWLEDGE_METHOD.md (302) | **Supersédé** — contenu conservé, en-tête annoté | Annexe-302 |
| KNOWLEDGE_GRAPH_SPECIFICATION.md (304) | **Supersédé** — contenu conservé, en-tête annoté | Annexe-304 |
| ENCYCLOPEDIA_DATABASE_SCHEMA.md (309) | **Supersédé** — contenu conservé, en-tête annoté | Annexe-309 |
| ENGINE_DATA_SOCLE.md (310) | **Supersédé** — contenu conservé, en-tête annoté | Annexe-310 |
| GSIE-DIR-0008 | **Amendée** §2.1/§2.3/§2.4 — contenu conservé, amendement annoté | Annexe-dir0008 |
| DEC-000012 | **Amendée** — ADR remplacés | Annexe-dec012-019-020 |
| DEC-000019 | **Amendée** — Vague 0 ajoutée | Annexe-dec012-019-020 |
| DEC-000020 | **Amendée** — transition schéma v6.1 | Annexe-dec012-019-020 |
| SCIENTIFIC_DATA_MODEL.md (205) | **Annoté** — evidence_level → EvidenceAssessment | Annexe-205 |
| ROADMAP.md | **À amender** après adoption (Vague 0) | Post-adoption |
| PROJECT_MEMORY.md | **À mettre à jour** après adoption | Post-adoption |
| CHANGELOG.md | **À mettre à jour** après adoption | Post-adoption |

### 6.2 Contrats d'interface affectés

| Contrat | Impact | Migration |
|---|---|---|
| Evidence Engine → Knowledge Engine | `evidence_level` direct → `EvidenceAssessment` | Adaptateur : Rust évalue (A-F), Python enrichit (évaluateur, méthode, date, scope). 67 tests Rust préservés. |
| Knowledge Engine → 14 moteurs | `KnowledgeObject` 6 types → `Assertion` claim_kind | Mapping 1:1 (§3.3 du métamodèle) + claim_kind élargi |
| KnowledgeQuery (livrable 206) | `type` enum 6 valeurs → `claim_kind` enum 7 valeurs | ADR-004 + amendement livrable 206 |
| API endpoints `/api/v1/knowledge/*` | Schéma Pydantic `KnowledgeObject` → `Assertion` | Vague 0/1 |

### 6.3 Risques

| Risque | Sévérité | Mitigation |
|---|---|---|
| PostgreSQL seul pour million d'assertions | Moyen | Benchmark AGE Vague 1 (ADR-003) ; Neo4j différé mais pas exclu |
| 73 types = sur-ingénierie | Moyen | Justification par type (§14) ; stratégie de réduction si confirmée |
| Migration 25 connaissances seed | Faible | ADR-004, migration scriptée, tests avant/après |
| AGE inerte (aucune requête Cypher existante) | Moyen | Benchmark Vague 1 sur données réelles avant décision |
| Contrats moteurs cassés | Moyen | Adaptateur + mapping 1:1 + claim_kind élargi couvre les 6 types |
| Append-only sur 20 ans | Faible | Partitionnement par temps (ADR futur) |

---

## 7. Alternatives considérées

### 7.1 Garder le schéma actuel (Neo4j + PG + ES + Jena)

**Rejeté**. Le schéma 309 prescrit 4 couches de stockage dès le départ,
sans benchmark prouvant le besoin. Neo4j, ES et Jena ajoutent une
complexité opérationnelle majeure (3 services supplémentaires à
maintenir, synchroniser et monitorer) pour une Vague 1 qui n'a pas
encore de données à l'échelle du million. L'approche v6.1 (PG canonique,
autres différés) respecte YAGNI tout en gardant la possibilité d'ajouter
ces technologies si le benchmark le justifie.

### 7.2 Garder KnowledgeObject 6 types

**Rejeté**. Les 6 types (concept, relation, regle, seuil, modele,
classification) ne couvrent pas les observations (mesures de terrain),
les absences, les prédictions de simulation, les hypothèses, ni les
conflits entre assertions. L'audit a montré que 3 scénarios sur 10
échouent avec le schéma actuel (absence, donnée sensible,
reproductibilité). Le noyau 73 types corrige ces lacunes.

### 7.3 Noyau réduit (24-32 types)

**Rejeté par le Fondateur**. La cible initiale 24-32 types ne couvre pas
les 4 types de confidentialité (scénario D), les 4 types de dataset
(scénario E, H), ModelVersion (reproductibilité), ConflictCluster
(scénario B). Le Fondateur a arbitré : 73 types acceptés (42 v6.1 + 18 v6.2), chacun
justifié. Une stratégie de réduction est prévue si l'usage confirme la
sur-ingénierie de certains types.

### 7.4 Single-table inheritance

**Rejeté**. Une table unique avec 42+ colonnes sparse (la plupart NULL
pour chaque ligne) est inadaptée : indexation inefficace, contraintes
de CHECK complexes, migration difficile. Class-table inheritance (une
table par type, FK vers `resource`) garantit l'intégrité référentielle
et la clarté du schéma (ADR-001).

### 7.5 v6.2 (nouvelle convergence)

**Rejeté par l'audit**. Les 19 corrections sont locales et intégrables
dans RFC-0011. La structure fondamentale de la v6.1 est saine. Une
nouvelle convergence ajouterait du délai sans valeur.

---

## 8. Annexes

Chaque annexe est un fichier séparé dans `02_RFC/annexes/`. Elles
détaillent le superseding/amendement de chaque document, avec le
contenu historique conservé intact et un en-tête explicite.

| Annexe | Document | Action |
|---|---|---|
| `annexe-302.md` | Livrable 302 — Knowledge Method | Superseding : KnowledgeObject → Assertion + EvidenceAssessment |
| `annexe-304.md` | Livrable 304 — Knowledge Graph Specification | Superseding : topologie Neo4j → tables PG + AGE |
| `annexe-309.md` | Livrable 309 — Encyclopedia Database Schema | Superseding : 4 couches → PG canonique |
| `annexe-310.md` | Livrable 310 — Engine Data Socle | Superseding : contrats moteurs KnowledgeObject → Assertion |
| `annexe-dir0008.md` | GSIE-DIR-0008 | Amendement : §2.1/§2.3/§2.4 |
| `annexe-dec012-019-020.md` | DEC-000012, DEC-000019, DEC-000020 | Amendement : ADR + plan + transition |
| `annexe-205.md` | Livrable 205 — Scientific Data Model | Annotation : evidence_level → EvidenceAssessment |

---

## 9. ADR produits par cette RFC

| ADR | Sujet | Fichier |
|---|---|---|
| ADR-001 | Racine Resource (class-table inheritance, FK fortes) | `GSIE/ARCHITECTURE/ADR-001-racine-resource.md` |
| ADR-002 | GSIE Temporal & Provenance Engine (Revision + Snapshot + ResourceDiff + PROV-O) | `GSIE/ARCHITECTURE/ADR-002-pg-temporal.md` |
| ADR-003 | AGE benchmark (stratégie d'évaluation Vague 1) | `GSIE/ARCHITECTURE/ADR-003-age-benchmark.md` |
| ADR-004 | Migration schéma (knowledge_objects → v6.1) | `GSIE/ARCHITECTURE/ADR-004-migration-schema.md` |
| ADR-005 | Outbox/Inbox (transactional outbox) | `GSIE/ARCHITECTURE/ADR-005-outbox-inbox.md` |
| ADR-006 | Object storage (MinIO/S3, interface put/get/delete) | `GSIE/ARCHITECTURE/ADR-006-object-storage.md` |

---

## 10. Processus d'adoption

1. **RFC-0011 Proposé** (ce document) — soumise au Fondateur pour Review
2. **DEC-000022 Proposé** — décision d'adoption, référencant cette RFC
3. **6 ADR Proposés** — décisions d'architecture, référençant cette RFC
4. **Review Fondateur** — examen des documents, arbitrages finaux
5. **Validation** — DEC-000022 passe à `Validated`, RFC-0011 à `Adopté`,
   ADR à `Accepté`
6. **Vague 0** — tests contractuels, contrats interface, audit migration
7. **Vague 1** — implémentation 73 types + Essence 360°

**Gate documentaire** : aucune implémentation de code ne démarre avant
l'étape 6. C'est l'application de CON-003 (connaissance avant code) et
de l'arbitrage Fondateur (stabilisation avant code).

---

## 11. Conformité constitutionnelle

| Loi | Conformité |
|---|---|
| CON-000 (primauté) | Cette RFC ne contredit aucun article constitutionnel |
| CON-001 (décideur humain) | Les EvidenceAssessment sont des recommandations, pas des décisions |
| CON-002 (science) | Toute assertion porte un EvidenceAssessment (A-F) |
| CON-003 (connaissance avant code) | Métamodèle avant implémentation (gate Vague 0) |
| CON-004 (explicabilité) | Assertion → Citation → Source + EvidenceAssessment + Qualifiers |
| CON-005 (traçabilité) | Activity + ProvEntity + Agent + Citation locator |
| CON-006 (documentation) | Cette RFC + métamodèle + 6 ADR + 7 annexes |
| CON-007 (modularité) | 5 niveaux séparés, noyau indépendant des profils |
| CON-008 (vision) | Sert l'Encyclopédie de l'Écosystème (GSIE-DIR-0008) |
| CON-009 (patrimoine vivant) | Revision append-only + Concept versionné par release |
| CON-010 (historique) | Bitemporalité + Revision + Snapshot immuables |

---

## 12. Catalogue de sources (intégration future)

Un catalogue de sources prioritaires est en cours de constitution par
des subagents de recherche (20 subagents : 10 domaines scientifiques +
10 types de sources). Le catalogue consolidé sera produit dans
`GSIE/RESEARCH/SOURCES/SOURCES_CATALOG.md`.

Ce catalogue alimente les types `Source` (23), `Dataset` (33),
`Distribution` (36) et `DataAsset` (35) du métamodèle. Il n'est pas
bloquant pour l'adoption de cette RFC — il est un input pour la Vague 1
(ingestion Essence 360°).

---

## 13. Conclusion

Le métamodèle v6.1 est structurellement sain, constitutionnellement
conforme, et corrige les 19 lacunes identifiées par l'audit. Les
contradictions avec les livrables Validated (302, 309, 310) et la
directive DIR-0008 sont traitées par superseding explicite via DEC-000022
— c'est précisément le rôle d'une RFC.

La Vague 0 (gouvernance + RFC + ADR + audit) précède toute
implémentation. La Vague 1 implémente les 73 types complets dès le
départ, avec l'Essence 360° comme tranche verticale.

**Recommandation** : adopter cette RFC et DEC-000022, puis démarrer la
Vague 0.

---

> Cette RFC est **Proposée**. Elle devient **Adoptée** après validation
> du Fondateur via DEC-000022. Aucune implémentation ne démarre avant
> le gate documentaire de la Vague 0.

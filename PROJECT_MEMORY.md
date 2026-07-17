# PROJECT_MEMORY — Vue courante du projet Quintessences

| Champ | Valeur |
|---|---|
| **Écosystème** | Quintessences |
| **Moteur** | GSIE (General System Intelligence Engine) |
| **Phase** | 4 — Implémentation |
| **Directive courante** | GSIE-DIR-0011 (Lancement Phase 4) |
| **Dernière mise à jour** | 2026-07-16 (CI 100% verte — 8/8 jobs passent : Governance + Lint + Rust + Python + Integration PostGIS/Redis + Docker build + CI Gate. 194 tests, 84% couverture, ruff + mypy --strict verts. Docker reproductible rustc 1.85 + maturin 1.9.6) |

---

## État

**Quintessences** est un écosystème d'applications environnementales
fondé sur le moteur **GSIE** (General System Intelligence Engine).
Spécialisations : GeoSylva (forêt), Artemis (faune), Ignis (incendies),
Hydro (eau), Flora (végétation), QGISIA (plugin QGIS). Centre de
Commandement GSIE (Unreal Engine 5.8) — poste de pilotage immersif où
toutes les données convergent.

Repos externes intégrés : `apps/GeoSylva/` (GitHub: NeooeN45/GeoSylva),
`apps/QGISIA/` (GitHub: NeooeN45/QGISIAPRO), `Forge/` (usine de données,
pas de remote). Ces repos ont leur propre `.git` et sont ignorés par le
repo parent.

Le projet est en **Phase 4 : Implémentation**, lancée officiellement par
**DEC-000017** (GSIE-DIR-0011) le 2026-07-13. La Phase 1 (Foundation)
est **clôturée** — les 12 livrables sont Validated (9/12) ou Locked
(3/12). La Phase 2 (Architecture) a produit 12 livrables Draft
(201-212). La Phase 3 (Connaissance) est **clôturée** — les 10 livrables
(301-310) sont Validated, 29 datasets catalogués, 25 connaissances
validées, 9 spécifications Draft produites pour la Phase 4.

La Phase 4 transforme les fondations, l'architecture et la base de
connaissances en **code métier opérationnel** : les 14 moteurs GSIE,
l'API GSIE, le Hub (Centre de Commandement Unreal Engine 5.8) et les
applications clientes (GeoSylva, Ignis en priorité). Le code métier,
interdit en Phase 3 (CON-003), est désormais autorisé.

### Vague 1 — Fondations (semaines 1-4)

- **Semaine 1** (livrée) : structure FastAPI + Docker Compose, auth JWT,
  health/readiness, rate limiting, observabilité (Prometheus/OpenTelemetry).
- **Semaine 2** (livrée) : Evidence Engine — cœur Rust + bindings PyO3,
  matrice de décision A-F, détection de conflits, versionnement, 122 tests
  Python + 41 tests Rust, couverture 100%.
- **Semaine 3** (livrée) : Knowledge Engine — implémentation Python
  (DEC-000020), ingestion de connaissances qualifiées (statut « accepte »
  uniquement), requêtes typées (par_concept, par_relation, par_domaine,
  par_essence, par_station), versionnement CON-010 (historique immuable),
  révision avec archivage, filtre par niveau de preuve, pagination.
  33 nouveaux tests (19 unitaires + 14 API), 155 tests au total.
- **Semaine 4** (livrée) : pipeline intégré Evidence → Knowledge
  (DEC-000021). Module `pipeline.py` chainant les deux moteurs :
  soumission → qualification A-F → ingestion (si accepte) → requête →
  révision (CON-010). 11 tests d'intégration E2E (8 engine + 3 API),
  166 tests au total. Tranche verticale prioritaire validée.

### Centre de Commandement GSIE — configuration environnement (2026-07-13)

Environnement Unreal Engine 5.8 configuré sur `E:\GSIE-Centre-Commandement`
(DEC-000010, livrable 211). Composants installés : UE 5.8.0, Cesium for
Unreal v2.28.0 (globe 3D géoréférencé), Unreal MCP v2.2.0 (pilotage IA
éditeur), Twinmotion 2026.1, RealityScan 2.2. Plugins natifs vérifiés :
GeoReferencing (PROJ/EPSG), Niagara, PythonScriptPlugin. Plugins source
clonés : UE-GeoViewer (GIS overlay), LandscapeGen (veille, UE 4.25).
Configuration système : registre Windows, 8 variables d'environnement,
3 raccourcis bureau, scripts utilitaires (Tools/), config Cesium ion
template (Landiras — zone de test Ignis). Plugins Fab à installer
manuellement : BlueprintWebSocket (gratuit), FluidFlux ($349.99, Hydro).
Voir `CHANGELOG.md` pour le détail complet.

### Métamodèle de l'Écosystème — statut courant (2026-07-17)

Le métamodèle v6.2 de l'Encyclopédie de l'Écosystème a été rédigé et
adopté via RFC-0011 (Adopté) + DEC-000022 (**Validated**, validation
rétroactive du 2026-07-16). Les 6 ADR (ADR-001 à ADR-006) sont
**Accepté**/Validated. Il définit un noyau universel de **73 types** organisés en 5 niveaux (noyau,
profils, projections, infrastructure, vision), avec PostgreSQL 16 +
PostGIS comme vérité canonique. Neo4j, Elasticsearch, Jena et GraphQL
sont différés (projections régénérables, benchmark AGE en Vague 1).

La v6.2 enrichit la v6.1 (42 types) avec 18 types issus de la passe
écologique du Fondateur : ScaleContext (multi-échelle), Phenomenon +
EcologicalProcess (phénomènes et processus écologiques), RelationType
(classification des prédicats), SamplingEvent (hiérarchie
d'échantillonnage), TraitDefinition + TraitValue (traits fonctionnels),
Feature + FeatureSet + Inference (IA/ML), Question + Hypothesis +
Decision + Recommendation + Scenario (couche raisonnement), Correlation
(objet de connaissance versionné), EcosystemService (concept différé),
Capability (orchestration moteurs/apps). Plus 2 champs : Assertion.rule_subtype
et Dataset.purpose.

**Documents produits** :
- `GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md` (livrable 213 v6.2, 73 types noyau)
- `02_RFC/RFC-0011-metamodele-encyclopedie-v6.1.md` (RFC principale, 430 lignes)
- `02_RFC/annexes/annexe-302.md` à `annexe-310.md`, `annexe-dir0008.md`,
  `annexe-dec012-019-020.md`, `annexe-205.md` (7 annexes)
- `03_DECISIONS/DEC-000022.md` (décision d'adoption, Validated)
- `GSIE/ARCHITECTURE/ADR-001-racine-resource.md` à `ADR-006-object-storage.md`
  (6 ADR, tous Accepté/Validated)

**Superseding** : livrables 302, 304, 309, 310 (Validated → Supersédé,
contenu conservé). Amendement : GSIE-DIR-0008 (§2.1/§2.3/§2.4),
DEC-000012, DEC-000019, DEC-000020. Annotation : livrable 205 (Draft).

**Arbitrages Fondateur** (19 corrections + 11 arbitrages v6.1 + 12 propositions v6.2) :
73 types acceptés (42 v6.1 + 18 v6.2 écologique + 1 Temporal Engine + 4 FAIR/RGPD/SOSA), racine `resource` unique (class-table inheritance),
`claim_kind` séparé de `lifecycle_status`, bitemporalité via **GSIE Temporal & Provenance Engine** (Revision + Snapshot + ResourceDiff + PROV-O, ADR-002),
benchmark AGE en Vague 1, adaptateur Evidence Rust évalue + Python
enrichit, Vague 0 (gouvernance + RFC + ADR + audit) avant Vague 1
(73 types + Essence 360° + FAIR + RGPD + SOSA/SSN). Passe écologique v6.2 : ScaleContext,
Phenomenon, EcologicalProcess, RelationType, SamplingEvent, TraitDefinition,
TraitValue, Feature, FeatureSet, Inference, Question, Hypothesis, Decision,
Recommendation, Scenario, Correlation, EcosystemService, Capability.
Audit FAIR/RGPD/SOSA : Sample (62), Consent (63), DataSubject (64),
PersistentIdentifier (65). Conformité FAIR §15.1 (4/15 OK → cible 10/15 Vague 1, 15/15 Vague 2).
Conformité RGPD §15.2 (art. 6 + 9.2.j). Mapping SOSA/SSN §15.3.
Passe dynamiques écologiques : Flow (66), ConfidenceGraph (67), Goal (68),
Constraint (69), KnowledgeLineage (70), Experiment (71), TerrainSession (72),
EcologicalState (73). Document orchestration Knowledge OS §9.4 (à rédiger Vague 0).
Roadmap Vague 2 exhaustive : 16 actions P1 + 20 actions P2.

**Catalogue de sources** : en cours de constitution par subagents (20
subagents : 10 domaines + 10 types, 7/20 terminés au 2026-07-15).
Consolidation prévue dans `GSIE/RESEARCH/SOURCES/SOURCES_CATALOG.md`.

La proposition v5 reste archivée comme ressource non normative
(`22_PROJECT_MEMORY/SUPERSEDED_DRAFTS/`). Aucune architecture issue du
brainstorming v5 n'est adoptée.

### Avancement des livrables

- **Validated** : 9 / 12 (001, 005, 006, 007, 008, 009, 010, 011, 012)
- **Locked** : 3 / 12 (002 — Préambule Constitutionnel, 003 — Préambule Philosophique, 004 — Article 000)
- **Draft** : 0 / 12

### Articles constitutionnels rédigés

- `GSIE-CON-000.md` — La Primauté de la Constitution (Locked, Loi Fondamentale Immuable)
- `GSIE-CON-001.md` — Le forestier reste le décideur (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-002.md` — La science avant tout (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-003.md` — La Connaissance avant le Code (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-004.md` — Toute décision doit être explicable (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-005.md` — Toute connaissance doit être traçable (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-006.md` — La Documentation fait partie du Produit (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-007.md` — La Modularité est obligatoire (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-008.md` — Le Projet appartient à sa Vision (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-009.md` — GSIE est un patrimoine scientifique vivant (Validated, Loi Fondamentale Immuable)
- `GSIE-CON-010.md` — Toute connaissance doit pouvoir évoluer sans perdre son historique (Validated, Loi Fondamentale Immuable)

### Documents transverses et méthodologiques rédigés

- `PACT_FOR_AI_AGENTS.md` — Pacte des Agents IA (livrable 005, Validated)
- `GSIE-DESIGN-PHILOSOPHY.md` — Design Philosophy (livrable 006, Validated)
- `SCIENTIFIC_CONSTITUTION.md` — Constitution Scientifique (livrable 007, Validated)
- `TECHNICAL_CONSTITUTION.md` — Constitution Technique (livrable 008, Validated)
- `AI_CONSTITUTION.md` — Constitution IA (livrable 009, Validated)
- `GSIE/ARCHITECTURE/ARCHITECTURE_PRINCIPLES.md` — Architecture Principles
- `GSIE/RESEARCH/RESEARCH_METHOD.md` — GSIE Research Method (livrable 301, détaillé Phase 3)
- `GSIE/RESEARCH/EVIDENCE_FRAMEWORK.md` — Evidence Framework (livrable 306, Phase 3)
- `GSIE/RESEARCH/SOURCING_PLAN.md` — Sourcing Plan (livrable 307, Phase 3)
- `GSIE/KNOWLEDGE/KNOWLEDGE_METHOD.md` — GSIE Knowledge Method (livrable 302, détaillé Phase 3)
- `GSIE/KNOWLEDGE/FOREST_ONTOLOGY.md` — Forest Ontology (livrable 303, Phase 3)
- `GSIE/KNOWLEDGE/KNOWLEDGE_GRAPH_SPECIFICATION.md` — Knowledge Graph Spec (livrable 304, Phase 3)
- `GSIE/KNOWLEDGE/KNOWLEDGE_BASE_SEED.md` — Knowledge Base Seed (livrable 308, 25 connaissances)
- `GSIE/DATASETS/DATASET_CATALOG.md` — Dataset Catalog (livrable 305, 29 datasets — DS-001 à DS-029)
- `GSIE/ARCHITECTURE/ENCYCLOPEDIA_DATABASE_SCHEMA.md` — Schéma DB Encyclopédie (livrable 309, PostgreSQL + Neo4j + ES + Jena)
- `GSIE/ARCHITECTURE/ENGINE_DATA_SOCLE.md` — Socle données 14 moteurs + liens apps (livrable 310)

### Documents d'architecture rédigés

- `GSIE/ARCHITECTURE/GSIE_MASTER_ARCHITECTURE.md` — Architecture globale
- `GSIE/ARCHITECTURE/GSIE_CORE_BLUEPRINT.md` — Blueprint du cœur système (Evidence Engine repositionné en amont)
- `GSIE/ARCHITECTURE/GSIE_DATA_FLOW.md` — Flux de données officiel (Evidence Engine repositionné en amont)
- `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` — Centre de Commandement UE 5.8 (livrable 211, v2.2.0 — Gaussian Splatting validé (DEC-000010) + §9 compléments de recherche : UE5.8, Cesium post-avril 2026, précédents multi-domaines, plugin Unreal MCP, publications 2026)
- `GSIE/ARCHITECTURE/GEOSYLVA_UNREAL_ARCHITECTURE.md` — GeoSylva-Unreal (livrable 212, v1.1.0 — SegmentAnyTreeV2 + Crown-BERT + précédents ONF/SDIS/Arbonaut, en attente MVP Ignis)
- `GSIE/RESEARCH/UNREAL_ENGINE_PRECEDENTS.md` — Fiches scientifiques FIRETWIN, FIRE-VLM, IVSR, Cesium Gaussian Splats, SegmentAnyTreeV2, Crown-BERT
- `GSIE/RESEARCH/LIDAR_HD_SPECIFICATIONS.md` — Fiche LiDAR HD IGN (11 classes ASPRS+IGN, pipeline PDAL→GDAL→PostGIS, correspondance strates Ignis, bibliothèque IGN_LIDAR_HD_DATASET v4.1.2, implications Unreal/Cesium)
- `GSIE/RESEARCH/VEILLE_2026-07-15.md` — Veille technologique (6 domaines) : ForestFormer3D, SelectAnyTree, SAGStree, ForestSplat (3DGS forestier), ForeFire (citation JOSS officielle), PostGIS 3.6.x, Cesium for Unreal v2.28.0 (UE 5.8), TorchGeo 0.9.0, limites LLM en écologie (cf. CON-002/CON-004). Aucune connaissance ingérée — bibliographie brute non qualifiée A-F.

### Branche Ignis (RFC-0004)

- `apps/Ignis/REGISTRE.md` — Registre d'idées vivant (60+ idées, 9
  sections : perception, jumeau numérique, vol drone, communications, GCS,
  données, stratégie, modèles IA, veille concurrentielle). Version 0.7.x.
- `apps/Ignis/` — Livrables du Jalon 0 (comparatifs sourcés).
- **Banc de simulation Ignis** (WSL2, hors dépôt) :
  - ForeFire compilé + démo propagation.png ✓
  - PX4 SITL v1.18.0-beta1 + Gazebo Harmonic 8.14.0 opérationnels ✓
  - **5 tests de vol réussis** : premier vol (34 m), waypoint (carré 100 m),
    pattern carré (200 m × 200 m), RTH (partiel), surveillance incendie
    (pattern lawnmower + 15 captures GPS)
  - Scripts : `premier_vol.py`, `vol_waypoint.py`, `vol_pattern_carre.py`,
    `vol_rth.py`, `vol_surveillance_incendie.py`, `run_test.sh`
  - Visualisation : `trajectoire_surveillance.png`

### Moteurs documentés (14/14 — architecture + état de l'art sourcé)

> Les 14 moteurs ont chacun un fichier d'architecture dédié (livrable 207,
> Phase 2 : responsabilité, entrées/sorties, dépendances, contrat
> d'interface, garanties, cas d'usage). Enrichissement 2026-07-13 (recherche
> sourcée multi-agents) : chaque fichier reçoit désormais une section
> supplémentaire **« État de l'art et pistes de recherche sourcées »**
> (technologies, algorithmes, bibliothèques, précédents scientifiques —
> pistes pour la Phase 4, aucun contrat d'interface modifié). Statut
> `Draft` inchangé pour les 14 fichiers. Détail : `ROADMAP.md`.

- `GSIE/ENGINES/EVIDENCE_ENGINE/` — Evidence Engine (filtre amont)
- `GSIE/ENGINES/KNOWLEDGE_ENGINE/` — Knowledge Engine
- `GSIE/ENGINES/CORRELATION_ENGINE/` — Correlation Engine
- `GSIE/ENGINES/REASONING_ENGINE/` — Reasoning Engine
- `GSIE/ENGINES/DIAGNOSTIC_ENGINE/` — Diagnostic Engine
- `GSIE/ENGINES/RECOMMENDATION_ENGINE/` — Recommendation Engine
- `GSIE/ENGINES/VALIDATION_ENGINE/` — Validation Engine
- `GSIE/ENGINES/GIS_ENGINE/` — GIS Engine
- `GSIE/ENGINES/CLIMATE_ENGINE/` — Climate Engine
- `GSIE/ENGINES/PEDOLOGY_ENGINE/` — Pedology Engine
- `GSIE/ENGINES/BOTANICAL_ENGINE/` — Botanical Engine
- `GSIE/ENGINES/FOREST_DYNAMICS_ENGINE/` — Forest Dynamics Engine
- `GSIE/ENGINES/LEARNING_ENGINE/` — Learning Engine
- `GSIE/ENGINES/SIMULATION_ENGINE/` — Simulation Engine

## RFC ouverts

- **RFC-0003** — Architecture distribuée GSIE-Net (Proposé — 2026-07-07) :
  capture la vision fondateur sur l'architecture offline-first, distribuée,
  multi-couches et orientée données. Activé en Phase 2.
- **RFC-0004** — Ignis : Système autonome de surveillance et d'analyse
  des incendies (**ADOPTÉ** — 2026-07-12, DEC-000003) : nouvelle branche
  fonctionnelle dédiée au risque incendie, positionnée comme application
  cliente de GSIE. Registre d'idées dans `apps/Ignis/REGISTRE.md` ;
  livrables Jalon 0 dans `apps/Ignis/`. Aucun développement
  métier en Phase 1. Voir `02_RFC/RFC-0004.md`.

---

## Décisions actives

- **DEC-000001** — GSIE est une Fondation scientifique
- **DEC-000002** — Phase 1 : Fondation, aucun développement métier
- **RFC-0001-D1** — Distinction Préambule constitutionnel / philosophique
- **RFC-0001-D2** — Article 000 « Primauté de la Constitution »
- **RFC-0001-D3** — Classification des lois (Immuables / Évolutives)
- **RFC-0001-D4** — Hiérarchie documentaire officielle (Vision → Code)
- **DIR-0003-D1** — La documentation devient le cœur du projet
- **DIR-0003-D2** — 12 livrables obligatoires, produits dans l'ordre
- **DIR-0003-D3** — Aucun développement métier avant validation des 12 livrables
- **DEC-000003** — Adoption RFC-0004 : branche fonctionnelle Ignis (application cliente)
- **DEC-000004** — Entrée en Phase 2 : Architecture (Phase 1 clôturée)
- **DEC-000005** — Amendement DEC-000003/000004 : archivage du code du banc Ignis (Jalon 0)
- **DEC-000006** — Restructuration identité : Quintessences (écosystème) > GSIE (moteur) > GeoSylva (app forestière)
- **DEC-000007** — Extension écosystème : Artemis + QGISIA (ancien Myhunt, renommé par DEC-000013)
- **DEC-000008** — Directive fondatrice Ignis (GCS / jumeau numérique vivant) — GSIE-DIR-0005
- **DEC-000009** — Vision du Moteur Cognitif Ignis — GSIE-DIR-0006
- **DEC-000010** — Adoption Unreal Engine 5.8 + Cesium comme moteur 3D du jumeau numérique
- **DEC-000011** — Entrée en Phase 3 : Connaissance (GSIE-DIR-0007)
- **DEC-000012** — L'Encyclopédie de l'Écosystème : la plus grande base de connaissances écologiques du marché (GSIE-DIR-0008)
- **DEC-000013** — Restructuration écosystème : Myhunt→Artemis, GSIE-Ignis→Ignis, +Hydro, +Flora, Centre de Commandement GSIE (GSIE-DIR-0009)
- **DEC-000014** — Réorganisation arborescence : GSIE/ + apps/ (GSIE-DIR-0010)
- **DEC-000015** — Unification des articles constitutionnels : `GSIE-CON-0XX` source unique, 100 fichiers `ARTICLE_0XX` vides supprimés (RFC-0002 Option A)
- **DEC-000016** — Extension Phase 3 : 8 → 10 livrables (309-310 rattachés, amendement GSIE-DIR-0007 v1.1)
- **DEC-000017** — Validation 10 livrables Phase 3 + clôture Phase 3 + lancement Phase 4 (GSIE-DIR-0011)
- **DEC-000018** — Stratégie IA IGN : adoption geocontext MCP + capitalisation datasets IA (CoSIA, OCS GE, apprentissage LiDAR HD)
- **DEC-000019** — Validation architecture Phase 4 + plan révisé 24 semaines (Python+Rust+Go différé, FastAPI+PostGIS+Redis, 6 vagues)
- **DEC-000020** — Knowledge Engine Semaine 3 : implémentation Python (ingest, query, revise, versionnement CON-010)
- **DEC-000021** — Semaine 4 : pipeline intégré Evidence → Knowledge (tranche verticale prioritaire)

## Documents structurants

- **GSIE-DIR-0001** — Directive fondatrice (ACTIVE)
- **GSIE-DIR-0003** — Lancement officiel Phase 1 Foundation (ACTIVE)
- **GSIE-DIR-0004** — GSIE Genesis Directive (ACTIVE)
- **GSIE-DIR-0005** — Directive fondatrice Ignis (GCS / jumeau numérique vivant) (Draft — DEC-000008)
- **GSIE-DIR-0006** — Vision du Moteur Cognitif Ignis (Draft — DEC-000009)
- **GSIE-DIR-0007** — Lancement officiel Phase 3 Connaissance (ACTIVE — DEC-000011)
- **GSIE-DIR-0008** — L'Encyclopédie de l'Écosystème (ACTIVE — DEC-000012)
- **GSIE-DIR-0009** — Restructuration écosystème : apps, Centre de Commandement, organisation (ACTIVE — DEC-000013)
- **GSIE-DIR-0010** — Réorganisation arborescence : GSIE/ + apps/ (ACTIVE — DEC-000014)
- **GSIE-DIR-0011** — Lancement officiel Phase 4 Implémentation (ACTIVE — DEC-000017)
- **RFC-0001** — Méthodologie de rédaction de la Constitution (ADOPTÉ)
- **RFC-0002** — Unification du système d'articles constitutionnels (**Adopté** — Option A, DEC-000015, 2026-07-13)
- **RFC-0003** — Architecture distribuée GSIE-Net (Proposé)
- **RFC-0004** — Branche fonctionnelle Ignis (ADOPTÉ — DEC-000003)
- **RFC-0005 à RFC-0010** — Réservés, non ouverts

## Veille partenariat et planification

- `20_PARTNERSHIPS/JUNN_VEILLE.md` — Veille JUNN (Jumeau Numérique National, IGN/Cerema/Inria, France 2030, 25 M€). Alignement stratégique avec Quintessences. Pas un partenariat actif.
- `05_SPECIFICATIONS/HUB_AND_APPS_PLAN.md` — Plan de production du Hub (Centre de Commandement) + specs apps. Ordre : Hub (P0) → Ignis (P1) → GeoSylva (P1) → Hydro/Flora (P2) → Artemis/QGISIA (P3).
- `05_SPECIFICATIONS/HUB/HUB_001_SPECIFICATION.md` — Spec fonctionnelle Hub (26 exigences, 3 cas d'usage, 13 couches).
- `05_SPECIFICATIONS/HUB/HUB_002_INTERFACE_CONTRACT.md` — Contrat d'interface Hub↔Apps (22 couches, format payload, métadonnées, v1.0.0).
- `05_SPECIFICATIONS/IGNIS/IGNIS_001_SPECIFICATION.md` — Spec fonctionnelle Ignis (26 exigences, 8 sections, 3 cas d'usage, traçabilité registre/datasets/RFC-0004).
- `05_SPECIFICATIONS/IGNIS/IGNIS_002_NON_FUNCTIONAL.md` — Spec non fonctionnelle Ignis (performance, résilience, sécurité, interop, souveraineté, explicabilité, garde-fous RFC-0004 §8).
- `05_SPECIFICATIONS/IGNIS/IGNIS_003_TRACEABILITY.md` — Matrice de traçabilité Ignis (F-01→F-26, NF-01→NF-10, datasets, moteurs, registre, couches Hub, garde-fous).
- `05_SPECIFICATIONS/GEOSYLVA/GEO_001_SPECIFICATION.md` — Spec fonctionnelle GeoSylva (23 exigences, 7 sections, 3 cas d'usage, couverture app mobile + Hub).
- `05_SPECIFICATIONS/GEOSYLVA/GEO_002_NON_FUNCTIONAL.md` — Spec non fonctionnelle GeoSylva (performance, offline-first RFC-0003, sécurité, interop, souveraineté, accessibilité mobile).
- `05_SPECIFICATIONS/GEOSYLVA/GEO_003_TRACEABILITY.md` — Matrice de traçabilité GeoSylva (F-01→F-23, NF-01→NF-12, datasets, moteurs, ontologie S-6, couches Hub, précédents ONF/SDIS/Arbonaut).
- `05_SPECIFICATIONS/HUB/HUB_003_LAYER_SHEETS.md` — Fiches détaillées des 25 couches du Hub (22 apps + 3 globales, 14 champs par fiche, matrice de compatibilité, priorités P0/P1/P2 Phase 4).

## Documents fondateurs de la Constitution

- `GSIE-FND-002.md` — Préambule Constitutionnel (Locked — livrable 002)
- `GSIE-FND-001.md` — Préambule Philosophique (Locked — livrable 003)
- `GSIE-CON-000.md` — La Primauté de la Constitution (Locked — livrable 004)

## Vision courante

**Quintessences** = écosystème d'intelligence environnementale (marque
umbrella). **GSIE** = General System Intelligence Engine, le moteur
spécialisable par domaine. **GeoSylva** = app forestière (première
spécialisation). La connaissance est le véritable produit.

**Durant la Phase 1**, la documentation est le produit principal. Le
code viendra en son temps, subordonné aux fondations.

## Prochaine étape

**Phase 4 — Implémentation (active — DEC-000017 / GSIE-DIR-0011,
2026-07-13).** La Phase 3 est clôturée (10/10 livrables Validated). Le
plan révisé à 24 semaines / 6 vagues (DEC-000019) est en cours
d'exécution :

- **Vague 1 — Fondations (semaines 1-4, Python + Rust)** : **clôturée**
  (DEC-000021). Knowledge Engine reconnecté sur PostgreSQL v6.2
  (2026-07-17, remplace le stockage en mémoire de la Vague 1).
- **Hub (Centre de Commandement GSIE, UE 5.8)** : environnement
  configuré (voir ci-dessus, livrable 211). Le projet Unreal réel vit
  hors dépôt (`E:\GSIE-Centre-Commandement`, dépôt GitHub
  `NeooeN45/Hub` privé) et est en cours de constitution ;
  `apps/Hub/README.md` sert de pointeur documentaire dans ce dépôt.
- **Vague 2 (démarrée, 2026-07-17)** :
  - **Correlation Engine** — codé (v1 réduite, périmètre documenté
    RFC-0014 §1.1) : pearson/spearman/kendall (scipy), persistance
    `resource(type=correlation)`, 10 tests.
  - **GIS Engine** — sorti du placeholder : cadastre (API Carto IGN)
    et altitude (API de calcul altimétrique IGN), données réelles
    vérifiables sans clé API, géométrie persistée en Lambert-93
    (`place`, PostGIS), 7 tests.
  - **Botanical Engine** — codé : résolution taxonomique GBIF Backbone
    Taxonomy (species/match, aucune clé), synonymes résolus vers le
    taxon accepté, déduplication `entity`/`entity_alias`. Pas
    d'autécologie en v1 (nécessite Rameau et al. non encore ingéré).
    8 tests.
  - **Pedology Engine** — codé : pH + texture via SoilGrids ISRIC
    (aucune clé), evidence_level=B (source unique peer-reviewed,
    plafond selon EVIDENCE_FRAMEWORK.md). Pas de persistance v1. 6 tests.
  - **RFC-0014** (Adopté) + **ADR-007** (Accepté) : garde-fou
    transverse anti-invention de données, applicable à tous les
    moteurs de raisonnement (Correlation, GIS, Botanical, Pedology, et
    futurs Reasoning/Diagnostic/Recommendation).
  - 6/14 moteurs GSIE codés (Evidence, Knowledge, Correlation, GIS,
    Botanical, Pedology). Reste : Climate (nécessite une clé API
    Météo-France), Forest Dynamics (données bulk IFN), puis la chaîne
    Reasoning/Diagnostic/Recommendation/Validation, puis Learning/
    Simulation.
  - Pipeline d'extraction documentaire sourcée (`Forge/src/dataset_forge/
    documents/extraction.py`) : pilote réussi sur un document réel
    (Lettre du DSF n°61) — 8 faits vérifiés, tous en quarantine.
  - Reste à démarrer : Climate, Pedology, Botanical, Forest Dynamics
    (P0/P1 — voir feuille de route RFC-0014 §3.4).

Rappel Phase 2 : les 12 livrables (201-212) sont Draft complets, prêts
pour Review.

> La mémoire détaillée vit dans `22_PROJECT_MEMORY/`.
> La roadmap complète vit dans `ROADMAP.md`.

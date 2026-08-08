# PROJECT_MEMORY — Vue courante du projet Quintessences

| Champ | Valeur |
|---|---|
| **Écosystème** | Quintessences |
| **Moteur** | GSIE (General System Intelligence Engine) |
| **Phase** | 4 — Implémentation |
| **Directive courante** | GSIE-DIR-0011 (Lancement Phase 4) |
| **Dernière mise à jour** | 2026-08-08 — **Gate 6 Performance — benchmark charge concurrente** (`GSIE/API/docs/LOAD_TEST_CONCURRENT_2026-08-08.md`, `scripts/load_test_concurrent.py`). Pool DB (`DEC-000037`) validé empiriquement pour la première fois : dégradation gracieuse à 24 sessions contre une capacité de 14, zéro erreur. Rate limiting confirmé sous rafale concurrente. **Trouvaille critique non corrigée** : le conteneur `api` (limite 768M) tourne à 94,5% de sa mémoire au repos, sans charge — marge quasi nulle, risque d'OOM-kill. Décision d'infrastructure à prendre (augmenter la limite ou réduire `GSIE_GUNICORN_WORKERS`). Latences absolues non transposables (artefact Docker Desktop/Windows, à re-mesurer sur l'hôte Linux de production). Voir aussi **MFA administrateur obligatoire implémenté** (gate Sécurité, ROADMAP §3). Un compte avec le rôle `admin` sans MFA actif ne reçoit plus jamais de token complet — jeton restreint `mfa_setup_required` (15 min, `core/auth.py`), rejeté partout sauf `/mfa/setup`+`/mfa/verify` (`get_current_user_or_mfa_setup`), jamais de blocage du compte. Enforcement centralisé dans `_issue_tokens` (choke point unique, tous fournisseurs). Guide `GSIE/API/docs/GOOGLE_OAUTH_PRODUCTION_SETUP.md` produit pour l'étape humaine restante (Google Cloud Console). 100% couverture maintenue (13 194 stmts), 2555 tests, ruff/mypy verts. Voir aussi **P0-1 Sauvegardes DB pgBackRest + WAL archiving implémenté et validé en direct** sur la base de dev réelle (52 MB, 151 tables) : stanza-create online, archivage WAL, sauvegarde complète chiffrée AES-256-CBC (52→5,8 MB), restauration isolée avec promotion et parité exacte. 2 bugs corrigés dans le template DEC-000037 (`pg1-host` SSH au lieu de `pg1-socket-path` local ; rôle `gsie_migrator` jamais câblé au lieu de `gsie` réel) et 1 dans la config (`repo1-cipher-pass=${VAR}` non interprété — passphrase lue depuis l'environnement). Reste : rebuild `Dockerfile.db` pour figer pgbackrest dans l'image (bloqué ponctuellement par un problème réseau sans lien avec pgBackRest), repo2 S3. Voir `GSIE/API/docs/BACKUP_RESTORE.md` et `GSIE/DOCUMENTATION/DR-RESTAURATION.md` §3.5. Voir aussi **Tests unitaires 100 % coverage + master test**. La suite `tests/unit` couvre désormais 100 % de `src/gsie_api` (13 170 statements). Garde-fous ajoutés : `tool.coverage.report.fail_under = 100` dans `pyproject.toml`, `scripts/run-master-tests.ps1/.sh` (lint + mypy + tests 100 % + mutation optionnelle), `cov-fail-under=100` dans `.github/workflows/ci.yml`. Voir aussi **Pentest authentification/connexion — clos** (`PENTEST_AUTH_CONNEXION_2026-08-07.md`) : 3 constats Moyens corrigés (IP réelle via `get_client_address()`, lockout par compte, nonce OIDC générique). 2545 tests unitaires passants, 63 skipped. Voir aussi **Pentest défensif post-déploiement** (`SECURITY_AUDIT_2026-08-07.md`) : CAA, HSTS preload (pending), Worker rate-limiter, `/metrics` protégé. |

### GSIE Environmental Digital Twin Platform — cadrage fédérateur (2026-08-06)

**RFC-0037** et `GSIE/ARCHITECTURE/GSIE_ENVIRONMENTAL_DIGITAL_TWIN_PLATFORM.md`
formalisent GSIE comme un **jumeau numérique environnemental fédéré**.
GeoSylva, Ignis, Hydro, Flora et Artemis sont des projections métier
spécialisées du même jumeau ; QGISIA fournit une projection SIG et
analytique ; les Hubs Unreal sont les environnements immersifs permettant
d'explorer, simuler et interagir sous contrôle humain. Le contrat HUB-002
est étendu en version Draft 1.1.0 avec les états réel/dérivé/prévision/
simulé/proposé/décidé, les scénarios branchés, la provenance, la fraîcheur
et les `ActionRequest` contrôlées. Aucun contrat de commande physique,
migration de schéma ou décision d'adoption n'est créé par RFC-0037 à ce
stade. Le catalogue `GSIE/ARCHITECTURE/GSIE_ENVIRONMENTAL_DIGITAL_TWIN_USE_CASES.md`
recense six cas d'usage réels (post-incendie, scolytes, SITAC, crues,
biodiversité, tempêtes) pour valider la fédération et prioriser les tranches
verticales.

### Hub Unreal — stack technologique (2026-08-07)

`GSIE/ARCHITECTURE/HUB_UNREAL_TECHNOLOGY_STACK.md` (Draft) dresse une
présentation architecturale des langages et technologies autour du Hub Unreal.
Quatre catégories : fondamentaux (C++, Rust, Python, Kotlin, PostGIS),
stratégiques (Elixir, Julia, WebAssembly), accélérateurs spécialisés
(Futhark, Taichi, Mojo) et recherche/validation (P, Dafny, Pony, Unison,
MoonBit, Zig). Le document respecte les décisions validées (DEC-000010,
DEC-000019, DEC-000053), définit les frontières entre Unreal, les moteurs et
les services, et conserve le principe : **GSIE State ≠ Unreal World**.

### Documentation GeoSylva 3.0 (GEOSYLVA-003)

Le cahier fonctionnel et scientifique issu du brainstorming validé est disponible
dans `apps/GeoSylva/GEOSYLVA_3_SPECIFICATION_FONCTIONNELLE.md` (statut Frozen,
version 0.9.1). Il fixe la hiérarchie Projet → Forêt → Parcelle → Placette →
Martelage, l’exigence de base locale transactionnelle et la doctrine de calcul
scientifique : sources, unités, incertitudes, qualité du bois, état sanitaire et
contexte des parcelles voisines doivent être modélisés et testés avant activation.

---

## État

**Quintessences** est un écosystème d'applications environnementales
fondé sur le moteur **GSIE** (General System Intelligence Engine).
Spécialisations : GeoSylva (forêt), Artemis (faune), Ignis (incendies),
Hydro (eau), Flora (végétation), QGISIA (plugin QGIS). Centre de
Commandement GSIE (Unreal Engine 5.8) — poste de pilotage immersif où
toutes les données convergent.

Repos externes intégrés : `apps/GeoSylva/` (GitHub: NeooeN45/GeoSylva),
`apps/QGISIA/` (GitHub: NeooeN45/QGISIAPRO), `Forge/`
(GitHub: NeooeN45/Forge). Ces repos ont leur propre `.git` et sont ignorés par le
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

**Veille geoOrchestra (2026-07-26)** : geoOrchestra est enregistré comme
source géospatiale externe potentielle future pour le GIS Engine, en
priorité 3 (veille). Le rôle envisagé est strictement celui d'une source
fédérée accessible par connecteur OGC/API et catalogue de métadonnées.
geoOrchestra n'est ni adopté comme composant du socle, ni considéré comme
source de vérité ; disponibilité, provenance et licence seront qualifiées
jeu par jeu et instance par instance avant toute ingestion.

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

- `GSIE/ARCHITECTURE/GSIE_MASTER_ARCHITECTURE.md` — Architecture globale, alignée sur RFC-0037
- `GSIE/ARCHITECTURE/GSIE_ENVIRONMENTAL_DIGITAL_TWIN_PLATFORM.md` — Architecture fédératrice des projections métier et Hubs spécialisés (RFC-0037)
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
- **RFC-0015** — Environmental Model Fabric (**ADOPTÉ** — 2026-07-18,
  DEC-000026) : étend ADR-009/RFC-0014 (garde-fou anti-invention des
  données) aux modèles scientifiques. Registre de modèles
  (`ModelRegistry`/`ModelArtifact`/`LicenseRecord`/
  `ApplicabilityDomain`/`ValidationRun`), LLM orchestrateur non
  autoritaire, vocabulaire imposé (observation/estimation/simulation/
  recommandation ; association/hypothèse causale/effet estimé),
  Correlation Engine v2 (pipeline causal 8 étapes), packs offline
  signés GeoSylva, progression par vertical slices. Issue de l'étude
  `GSIE/RESEARCH/ETUDE_MODELES_OPEN_SOURCE_QUINTESSENCES_2026-07-18.md`.
  Voir `02_RFC/RFC-0015-environmental-model-fabric.md`.
- **RFC-0016** — Schéma forestier spécialisé (**ADOPTÉ** — 2026-07-18,
  DEC-000027) : applique RFC-0014/RFC-0015 au domaine sylvicole. 10
  entités (AutecologyProfile, StationType/StationObservation,
  SiteIndexModel/FertilityClass, SilviculturalSystem/SilviculturalRule/
  Intervention, ProvenanceMaterial, DiagnosticProtocol/HealthRisk,
  EvidenceStatement/ConflictRecord), chaîne de décision en 10 étapes,
  passeport de décision à 5 catégories (observé/calculé/modélisé/
  documenté/incertain). Principe non négociable : une classe de
  fertilité n'est jamais universelle (essence+modèle+âge+région+source
  obligatoires). Pilote proposé : Nouvelle-Aquitaine, 12-20 essences.
  SCI-001 (registre des sources) et SCI-003 (TAXREF canonique) déjà
  implémentés — voir `gsie_api.governance.source_registry` et
  `BotanicalEngine.resolve_taxref`. Issue de
  `GSIE/RESEARCH/CORPUS_SYLVICOLE_SCIENTIFIQUE_QUINTESSENCES_2026-07-18.md`.
  **Phase A (schéma de données) complète le 2026-07-19** — voir détail
  dans « Vague 2 » ci-dessous et `DEC-000027`. **Phase B (intégration
  Botanical/Forest Dynamics Engine, passeport à 5 catégories) également
  complète le 2026-07-19** — voir détail dans « Vague 2 » ci-dessous et
  `DEC-000027`. Seule la Phase C (pilote Nouvelle-Aquitaine) reste à
  faire.
  Voir `02_RFC/RFC-0016-schema-forestier-specialise.md`.
- **RFC-0017** — Veille technologique : Pl@ntNet (identification
  botanique) et NVIDIA NIM (couche IA serveur) (**ADOPTÉ comme
  cadrage** — 2026-07-20, DEC-000029, **scindé** en RFC-0018 et
  RFC-0019) : formalisait deux pistes issues d'une veille externe.
  Reste la référence de priorisation (§2.2/§5) mais n'autorise plus
  d'implémentation directe — voir les deux RFC d'exécution ci-dessous.
  Issue de
  `GSIE/RESEARCH/VEILLE_PLANTNET_NVIDIA_NIM_QUINTESSENCES_2026-07-20.md`.
  Voir `02_RFC/RFC-0017-veille-plantnet-nvidia-nim.md`.
- **RFC-0018** — Identification botanique assistée (Pl@ntNet) et
  extension du Botanical Engine (**ADOPTÉ** — 2026-07-20, DEC-000030,
  volet en ligne §5 uniquement) : cycle `SUGGESTION_IA` →
  `VALIDEE_UTILISATEUR`, jamais de valeur automatique déclenchante
  (GSIE-CON-001). Architecture GeoSylva→serveur GSIE→Pl@ntNet→
  normalisation→validation humaine, clé API jamais côté client,
  métadonnées GPS retirées avant envoi. Extension satellite
  d'`AutecologyProfile` (RFC-0016) sur validation uniquement. Volet
  modèle embarqué offline maintenu « à l'étude » (hors périmètre de
  DEC-000030). Préalable bloquant avant tranche 2 : confirmation
  écrite de Pl@ntNet sur les conditions commerciales. Spécification
  fonctionnelle : `GEO-004` (16 exigences GEO-ID-01 à GEO-ID-16) — voir
  `05_SPECIFICATIONS/GEOSYLVA/GEO_004_IDENTIFICATION_BOTANIQUE_PLANTNET.md`.
  **Tranche 1/N (schéma de données) complète le 2026-07-20** : 3
  nouvelles tables (`botanical_identification_request/result/decision`),
  registre de types 86→89, 339 tests unitaires (0 échec). Reste à
  faire : client Pl@ntNet serveur (tranche 2, bloqué par la
  confirmation commerciale), routes serveur (tranche 3), intégration
  app mobile (tranche 4).
  Voir `02_RFC/RFC-0018-identification-botanique-plantnet.md`.
- **RFC-0019** — `gsie-ai-gateway` : couche IA serveur transverse
  (**Draft** — 2026-07-20) : périmètre P0 = RAG scientifique
  (`/ai/embed`, `/ai/rerank`, `/ai/research`), garde-fou, banc d'essai
  `GSIE-Eval-FR` (Recall@10 ≥ 85 %, précision citations ≥ 95 %,
  abstention si preuve insuffisante). PostgreSQL/PostGIS/AGE reste la
  vérité canonique, aucun LLM/VLM n'est autoritaire. Pas
  d'auto-hébergement NIM en production sur le matériel actuel
  (Windows, GPU insuffisant) — endpoints hébergés + Brev pour
  prototyper, plafond d'heures GPU par expérience. P1/P2/P3 (AI-Q,
  Earth2Studio, cuOpt, Parakeet, vision/vidéo, Hub UE5.8) explicitement
  hors périmètre de ce RFC. Issu de DEC-000029 (scission de RFC-0017).
  Aucune implémentation avant Review puis décision propre.
  Voir `02_RFC/RFC-0019-gsie-ai-gateway-nvidia-nim.md`.
- **RFC-0020** — Carte de l'ignorance : première implémentation du
  Reasoning Engine, périmètre forestier (**Draft** — 2026-07-20) :
  score d'incertitude explicable + recommandation de la prochaine
  mesure la plus utile, par sujet (`StationObservation`/
  `AutecologyProfile`). Barème de poids déterministe (pas de modèle
  statistique/bayésien pour ce premier RFC), réutilise
  `ModelModel`/`ModelVersionModel` (RFC-0015) — jamais présenté avec
  une confiance uniforme, chaque poids sourcé ou marqué
  `heuristique_non_sourcee`, `human_validator` requis pour passer
  `accepted` (même pattern que `SilviculturalRule`, RFC-0016). Mix
  serveur/local retenu après brainstorming : GSIE = source de vérité
  du barème (packs offline signés, RFC-0015), GeoSylva = calcul local
  sans réseau à partir du même barème. Plan en 3 tranches (schéma →
  premier barème réel 2-3 variables → export pack offline). Issu de
  `GSIE/RESEARCH/VEILLE_INNOVATIONS_QUINTESSENCES_2026-07-20.md` §2.1
  (piste retenue comme prioritaire). Aucune implémentation avant
  Review puis décision.
  Voir `02_RFC/RFC-0020-carte-ignorance-reasoning-engine.md`.

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
- **DEC-000024** — Ingestion des données forestières ONF/CNPF/IGN (Review, 2026-07-16, RFC-0013). Module `gsie_api.ingestion`, datasets P0 (BD Forêt v2, IFN, catalogues stations CNPF) en Vague 2, P1 (RPF/RPFR, BDAT, LiDAR HD) en Vague 3. Mapping métamodèle v6.2, traçabilité CON-010.
- **DEC-000028** — Incrément démontrable « territoire + capsule + Golden Bench » (Review, 2026-07-18, ADR-008, EXP-0001). Première tranche verticale hors-ligne de GSIE sous forme de capsule territoriale signée. Renuméroté depuis DEC-000025 (collision d'ID).
- **DEC-000026** — Adoption RFC-0015 : Environmental Model Fabric — registre de modèles scientifiques, LLM orchestrateur non autoritaire, Correlation Engine v2, packs offline signés
- **DEC-000027** — Adoption RFC-0016 : Schéma forestier spécialisé — 10 entités, chaîne de décision en 10 étapes, passeport de décision à 5 catégories, pilote Nouvelle-Aquitaine. **Phase A (schéma de données) complète le 2026-07-19** : 10/10 entités du §3.1 couvertes (10 nouvelles tables satellite + 3 entités réutilisées sans duplication — Intervention, EvidenceStatement, ConflictRecord) sur 6 tranches, registre de types 76→86, 364 tests (304 passed/60 skipped). Phases B et C restent à faire. **Audit qualité du 2026-07-20** (0 P0, aucune valeur non sourcée détectée, ADR-009 respecté) a identifié des P1/P2 de cohérence — corrigés le même jour : typage enum strict sur 6 DTO Pydantic (str → StrEnum), 4 règles métier conditionnelles répliquées dans `resources/validators.py` (reflètent des CheckConstraint SQL déjà en place), index sur les 10 FK `source_id` (désormais intégrés à la baseline `20260726_0001`). 347 tests unitaires (0 échec).
- **DEC-000029** — Adoption du cadrage RFC-0017 (veille Pl@ntNet/NVIDIA NIM) et scission en RFC-0018 (identification botanique Pl@ntNet) et RFC-0019 (`gsie-ai-gateway`). N'autorise aucun code métier — RFC-0018 et RFC-0019 doivent chacun être adoptés séparément avant tout développement.
- **DEC-000030** — Adoption de RFC-0018 (identification botanique Pl@ntNet), volet en ligne uniquement (§5), par tranches verticales. **Tranche 1/N (schéma de données) complète le 2026-07-20** : `BotanicalIdentificationRequest`/`Result`/`Decision`, registre de types 86→89, 339 tests (0 échec). Tranches 2-4 (client Pl@ntNet, routes serveur, app mobile) restent à faire, tranche 2 bloquée par la confirmation écrite Pl@ntNet sur les conditions commerciales.
- **DEC-000031** — Socle de fiabilité d'entreprise
- **DEC-000032** — Orchestration contrôlée des agents IA
- **DEC-000033** — Orientation de la refondation constitutionnelle (décision d'orientation, **non** décision d'adoption)
- **DEC-000034** — Réassignation de l'orchestration des agents IA (Review, 2026-07-25). Amende DEC-000032 (orchestration contrôlée) — RFC-0022 Adopté. Décision d'organisation sans effet constitutionnel : Codex conserve l'orchestration technique, le Fondateur l'autorité finale.
- **DEC-000035** — Rust devient un critère de pertinence mesuré, non un plan de vague
- **DEC-000036** — Baseline Alembic v6.2 unique, lignée locale 0001-0013 remplacée
- **DEC-000037** — Stratégie de fiabilisation et de sécurisation de la base de données GSIE
- **DEC-000038** — Persistance des règles d'inférence (adoption `RFC-0028`). Une règle est une Assertion (`claim_kind` `rule`/`threshold`), aucune table nouvelle. La condition exécutable est **dérivée** du fait sourcé, jamais stockée — une chaîne persistée pourrait diverger du seuil qu'elle traduit et appliquer l'ancienne valeur en citant la source révisée. **Un domaine de validité non renseigné vaut « nulle part »** : le silence ne vaut pas universalité, et une conclusion fausse portant une citation vérifiable est pire qu'une absence de réponse. Corollaire : territoire obligatoire sur `silvicultural_rule` et `autecology_profile`, comme il l'est déjà sur `station_type`, `fertility_class` et `provenance_material`. Aucun plancher de preuve par défaut mais `evidence_level_plancher` obligatoire en réponse ; une source invalidée sort la règle du service **et** rend énumérables les conclusions passées qui la citaient. Premier lot : chêne sessile, réserve utile maximale, un territoire, de bout en bout.
- **DEC-000040** — Tables transverses laissées dans `public` (Draft, 2026-07-31, RFC-0029). Décision d'architecture de données : les tables transverses (junctions, outbox, temporal_engine, enrichment) restent dans le schéma `public` plutôt que d'être éclatées par moteur. Préserve DEC-000019 (PostgreSQL+PostGIS+AGE) et GSIE-PROMPT-0027 (schémas de domaine). Référencée dans CHANGELOG l.365 (mapping Treekipedia).
- **DEC-000041** — Ingestion bulk + pgvector + garde anti-invention automatisée. Pipeline bulk (POST /resources/bulk, 1000 items/lot, 600 req/min), migration `20260731_0024` pgvector (extension vector + colonne embedding(1536) + index IVFFlat), garde anti-invention RFC-0014 automatisée (détection AI-sourced → evidence_level=D + quarantine), rate limiting différencié. Dockerfile.db installe `postgresql-16-pgvector`. Modèle `EntityModel` déclare `embedding` (Vector(1536)). 1346 tests unitaires + 9 tests d'intégration.
- **DEC-000043** — Phase de stabilisation : ralentir pour prouver (Validé, 2026-08-02). Décision directe du Fondateur après diagnostic : qualité technique 8/10, qualité produit 6,5/10. Trois livrables : S1 restauration DB prouvée, S2 tranche verticale réelle terrain→recommandation, S3 validation scientifique + performance. Nouveaux endpoints/moteurs/migrations suspendus. Gates 4/5/6 de la ROADMAP passent à ❌ (bloqués par S2/S3).
- **DEC-000044** — Identité Quintessences multi-fournisseurs (Validé,
  2026-08-03, RFC-0032). Un compte canonique est partagé par GeoSylva,
  Ignis, Hydro, Artemis, Flora, le web, le poste tout-en-un et le Centre
  de Commandement. Connexion locale et Google OIDC livrées côté serveur ;
  les fournisseurs professionnels OIDC/SAML restent explicitement
  « En développement ». Aucun rapprochement de comptes par e-mail seul.
- **DEC-000045** — Parcours compte et diagnostic développeur GeoSylva
  (Validé, 2026-08-03, RFC-0032). Trois surfaces Compose distinctes :
  connexion, espace compte et diagnostic local en lecture seule. Huit
  pressions sur la version activent les options développeur sans créer de
  rôle ; toute future commande Fondateur devra être autorisée côté serveur.
- **DEC-000046** — Cycle complet du compte local Quintessences (Validé,
  2026-08-03, RFC-0032). Profil, vérification e-mail et récupération sont
  livrés avec codes Argon2id à usage unique de quinze minutes, réponse
  anti-énumération, SMTP chiffré en production et révocation des sessions
  antérieures après changement de mot de passe.
- **DEC-000047** — Cloudflare comme bordure Zero Trust de GSIE (Validé,
  2026-08-03). Tunnel sortant, origine non exposée, séparation des flux
  publics, M2M et contrôle. Cloudflare protège l'accès réseau ; JWT, rôles et
  révocation GSIE restent l'autorité métier.
- **DEC-000048** — Synchronisation hors ligne des parcelles GeoSylva
  (Validé, 2026-08-03, RFC-0032). File mobile chiffrée, WorkManager,
  opérations idempotentes, versions optimistes, tombstones et RLS par compte.
  La première transmission nécessite une action explicite ; aucun conflit ne
  remplace silencieusement la donnée locale.
- **DEC-000049** — Contrats d'interface GeoSylva ↔ moteurs GSIE (Validé,
  2026-08-03, RFC-0033).
- **DEC-000050** — IA forestière on-device et multi-tier (Validé, 2026-08-03,
  RFC-0034).
- **DEC-000051** — Système de développement assisté par IA Quintessences v1
  (Validé, 2026-08-05). Les idées et ressources sont capturées dans les
  registres canoniques, le WIP Fondateur est limité à `1+1+1`, et les skills
  Devin d'intake restent propositionnelles par défaut. Le pilote est la
  synchronisation multi-client GeoSylva. `IDEA-0003` consigne IGNIS-FOLD comme
  recherche future, sans autoriser son implémentation.

## Système de développement assisté par IA v1

- **Idées** : `/ingestion-idee` → `22_PROJECT_MEMORY/IDEA_BACKLOG.md`.
- **Ressources** : `/ingestion-ressource` → `GSIE/RESEARCH/`,
  `GSIE/DATASETS/`, `GSIE/KNOWLEDGE/`, `21_EXPERIMENTS/` ou `19_LEGAL/`.
- **Pilotage** : `/pilotage-wip`, sans registre parallèle.
- **Qualité de l'outillage** : `/audit-skills-devin`.
- **Limite WIP** : une tranche produit, une recherche et une correction urgente.
- **Pilote** : parcours de synchronisation GeoSylva jusqu'au second client,
  aux conflits et à l'audit.

## Documents structurants

- **GSIE-DIR-0001** — Directive fondatrice (ACTIVE)
- **GSIE-DIR-0003** — Lancement officiel Phase 1 Foundation (ACTIVE)
- **GSIE-DIR-0004** — GSIE Genesis Directive (ACTIVE)
- **GSIE-DIR-0005** — Directive fondatrice Ignis (GCS / jumeau numérique vivant) (Review — DEC-000008, passage Draft→Review 2026-08-02 : livrables en pilote actif)
- **GSIE-DIR-0006** — Vision du Moteur Cognitif Ignis (Review — DEC-000009, passage Draft→Review 2026-08-02 : livrables en pilote actif)
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

- `GSIE/RESEARCH/VISION_LLM_SPECIALISES_GSIE_CORE_2026-07-20.md` —
  Vision long terme (non actionnable) : famille de LLM spécialisés par
  adaptateurs LoRA sur un modèle de base partagé, orchestrateur central
  qui coordonne sans jamais calculer lui-même, futur `GSIE-Core`
  (modèle natif transformant une demande en plan scientifique traçable,
  jamais autorité finale — GSIE gouverne, le modèle coordonne).
  Confirme et prolonge les principes déjà posés par RFC-0019 (aucun
  LLM autoritaire, calculs dans des moteurs déterministes) sans en
  changer le périmètre P0. Inclut une évaluation d'une instance GPU
  L40S 48 Go pour du fine-tuning LoRA/QLoRA (bon jusqu'à 14B, faible
  au-delà, irréaliste pour un préentraînement complet) et une
  stratégie d'entraînement en 5 étapes (`GSIE-Eval-FR` d'abord, modèle
  de base 8-14B, dataset propre 1000-5000 exemples, LoRA, évaluation
  comparative). À rouvrir formellement (RFC dédié) seulement quand
  RFC-0019 aura démontré son socle en usage réel.
- `GSIE/RESEARCH/VEILLE_INNOVATIONS_QUINTESSENCES_2026-07-20.md` —
  14 pistes d'innovation (non actionnables) classées par rupture
  potentielle : carte de l'ignorance + valeur de l'information, IA
  auto-réfutante (`GSIE-Contradictor`) + connaissances à validité
  conditionnelle, moteur de risques en cascade (`GSIE-Cascade`) —
  retenues comme les 3 prioritaires par l'échange source. Concept
  fédérateur proposé : « GSIE Scientific Autonomy Loop » (observer →
  cartographier l'ignorance → choisir la prochaine mesure → formuler
  → réfuter → simuler → proposer une expérience réversible → mesurer
  → mettre à jour les preuves). Aucun RFC ouvert, aucune brevetabilité
  établie (réserve explicite de la source).
- `GSIE/RESEARCH/VEILLE_AUDIT_CONCURRENTIEL_GEOSYLVA_2026-07-20.md` —
  Audit concurrentiel externe (Marteloscope ONF, PLATEXFOR, QField,
  Open Foris Ground, Forest Metrix, TRESTIMA/KATAM/Arboreal) avec
  pistes d'intégration priorisées (paquet de mission hors ligne,
  adaptateurs matériel Bluetooth, mode martelage étendu, connecteurs
  Pl@ntNet/Ignis/Hydro). **Signale aussi des points à vérifier sur le
  code réel de `apps/GeoSylva`** (non confirmés par un audit GSIE :
  usage de `GlobalScope`, IBP potentiellement en retard sur la v3.2
  CNPF, export GeoJSON en Lambert-93 non conforme RFC 7946, **licence
  AGPL-3.0 contradictoire avec « forks not allowed » — point le plus
  prioritaire à vérifier vu l'implication légale**). Lecture externe
  du README/changelog public, pas un audit du dépôt par l'agent —
  chaque point reste à confirmer avant correction.
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

**Durant la Phase 4**, le code métier et la documentation évoluent ensemble,
toujours subordonnés aux fondations, aux sources scientifiques et aux portes
qualité.

**DEC-000033 (2026-07-24)** trace l'orientation multi-domaines de
Quintessences et le rang de la future Vision. Il s'agit d'une décision
d'**orientation**, pas d'adoption : les textes constitutionnels actuels —
`GSIE-FND-001`, `GSIE-FND-002`, `GSIE-CON-000` à `GSIE-CON-010`,
`AI_CONSTITUTION.md`, `SCIENTIFIC_CONSTITUTION.md` et
`TECHNICAL_CONSTITUTION.md` — **restent intégralement applicables** jusqu'à
l'adoption puis la publication de nouvelles éditions. Toute divergence entre
l'orientation et un texte en vigueur se résout en faveur du texte en vigueur.

## Prochaine étape

### Inventaire sources élargi — GSIE-PROMPT-0025 (2026-07-30)

Extension de l'inventaire des sources de données à un état viable 5 ans.
**Branche `feat/inventaire-sources-elargi`** — 2 commits locaux, non poussés (en attente d'autorisation).

- 9 domaines thématiques traités (A-I), 68 URLs testées (82% succès)
- 48 entrées vérifiées (YAML conformes RFC-0029 §11.3) dans `_staging_0025/`
- 26 nouvelles sources ajoutées à `SOURCES_DONNEES_EXHAUSTIVES.md` §6.10
- 34 sources à vérifier identifiées
- 5 corrections critiques : Prométhée→BDIFF (DS-022 obsolète, DS-022b ajouté), INPN cyberattaque, ERA5T payant, donneespubliques.meteofrance.fr fermeture, CDSE STAC endpoint
- Nouveau total : ~205 sources vérifiées + 34 à vérifier = ~239 potentielles (+33%)
- **Action requise** : pousser la branche et créer la PR quand autorisé

### P0 technique — Persistance des diagnostics (chantier cadré le 2026-07-26)

Bloque la tranche R2 du Recommendation Engine. Analyse déjà faite, à ne pas
refaire.

**Le problème.** `RECOMMENDATION_ENGINE.md` §5 définit
`RecommendationRequest` avec un simple `diagnostic_id : UUID`, tandis que le
§2 déclare que l'entrée est le `Diagnostic` lui-même. Or le Diagnostic
Engine est sans persistance en v1 (« aucun effet de bord sur la base ») :
aucun `diagnostic_id` n'est résolvable contre quoi que ce soit. Un moteur
écrit sur ce contrat échouerait systématiquement.

**Arbitrage du Fondateur (2026-07-26).** Implémenter la persistance plutôt
que de faire porter le `Diagnostic` par la requête. L'option écartée aurait
suivi le précédent de Correlation, Reasoning et Diagnostic, au prix d'un
écart supplémentaire au contrat écrit.

**Faux amis identifiés — ne pas réutiliser.** Le métamodèle contient déjà
`inference`, `recommendation` et `diagnostic_protocol`, qui ne sont pas les
objets de nos moteurs :

| Type existant | Ce qu'il représente | Champs requis |
|---|---|---|
| `inference` | Prédiction d'un **modèle IA** | `model_version_id`, `feature_set_id`, `confidence` |
| `recommendation` | Recommandation générique d'un acteur | `recommended_by`, `recommendation_text` |
| `diagnostic_protocol` | Un **protocole**, pas un résultat | — |

Confondre l'`InferenceResult` du Reasoning Engine avec le type `inference`
rendrait indistinguables en base une conclusion tracée par règles explicites
et une prédiction statistique opaque — ce que `GSIE-CON-004` interdit.

**Périmètre, dans l'ordre.**

1. ✅ **Fait (2026-07-26)** — type de ressource `diagnostic` :
   `GSIE/API/src/gsie_api/infrastructure/models/diagnostic.py`,
   `register_type("diagnostic")`, entrée de validateur. Registre à
   **90 types**. Aucun faux ami réutilisé.
2. ✅ **Intégrée à la baseline v6.2** — table `diagnostic` et 3 enums inclus
   dans `20260726_0001`. **Réversibilité globale exécutée et verte** :
   `tests/integration/test_migration_baseline.py` joue base vierge →
   `upgrade head` → `downgrade base` → `upgrade head` sur PostgreSQL 16,
   PostGIS et Apache AGE, puis vérifie la dérive du schéma.
3. ✅ **Fait** — `DiagnosticEngine.diagnostiquer` écrit son résultat. Le
   moteur n'est plus pur ; le changement de contrat est documenté dans
   `GSIE/ENGINES/DIAGNOSTIC_ENGINE/DIAGNOSTIC_ENGINE.md` (§5, sous-section
   « Persistance ») et dans la docstring du moteur.
4. **Reste à faire** — chargement par `diagnostic_id` côté Recommendation,
   avec le cas « diagnostic introuvable ». La tranche R2 est débloquée.
   R1 est livrée (`ebf6d84`).

**Défauts de la chaîne de migrations résolus par DEC-000036.** La lignée
locale non publiée `0001`-`0013`, qui sautait du DDL et dupliquait les index
`source_id`, est remplacée par `20260726_0001`. Cette baseline autonome ne
réimporte pas les modèles à l'exécution, contient exactement les 116 tables
v6.2 et exclut les 12 tables v6.1 archivées. Aucune donnée historique n'étant
à préserver, les anciennes bases locales ne sont pas converties : elles sont
recréées. La CI construit l'image PostgreSQL/PostGIS/AGE et interdit désormais
que le test de migration spécialisé soit ignoré.

**Dérivation de `diagnostic_id` corrigée (2026-07-26).** Elle couvre
désormais `requete_id`, `station_id`, `type_diagnostic`, les
`conclusion_id`, **les qualifications** et **l'état global déclaré**
(justification et source comprises), sous forme de sérialisation JSON
canonique — non de concaténation par séparateur, qu'un champ de texte libre
pourrait imiter. Requalifier une contrainte en atout, ou passer de
« vigueur réduite » à « critique », produit bien un identifiant différent.
Vérifié comme régression réelle : avec l'ancienne formule, 5 des 6
nouveaux tests échouent.

⚠️ **Les identifiants émis avant cette correction ne sont plus
reproductibles.** Aucun diagnostic n'ayant été persisté avant elle
(la persistance et la correction sont du même jour), l'impact est nul en
base ; il ne le serait plus à l'avenir.

**Risque résiduel restant.** Les **contradictions déclarées** n'entrent pas
dans la dérivation : deux requêtes identiques par ailleurs mais déclarant
des contradictions différentes dérivent encore le même identifiant. Le
moteur refuse et nomme le conflit (`DiagnosticConflitError`) plutôt que
d'écraser. Les inclure est une ligne à ajouter dans `_cle_derivation` —
non fait faute de demande, et cela changerait à nouveau les identifiants.

### P0 — Refondation constitutionnelle (corrections appliquées, EN_REVUE)

1. Les corrections des **3 P0** sont appliquées dans `RFC-0023` et
   `RFC-0024`. Leur clôture formelle reste soumise au nouveau contre-audit.
2. `RFC-0025` et `RFC-0026` portent la future procédure des textes cibles.
   Elles restent `Brouillon`, sans texte constitutionnel cible et avec
   adoption interdite.
3. Traiter les **7 P1 encore ouverts** : C-05, C-08, C-09, C-10, C-11, C-12
   et C-13. C-04, C-06 et C-07 sont traités avec le lot P0.
4. Refaire un **contre-audit indépendant** ; aucun P0 résiduel n'est
   acceptable avant présentation au Fondateur.
5. **Ne modifier aucun document `Locked`** avant adoption formelle : ni
   `GSIE-FND-001`, ni `GSIE-FND-002`, ni `GSIE-CON-000`.

Ce jalon n'autorise aucune autonomie R3-R5, aucune licence finale de
composant et aucune création de `VISION.md` canonique.

**Phase 4 — Implémentation (active — DEC-000017 / GSIE-DIR-0011,
2026-07-13).** La Phase 3 est clôturée (10/10 livrables Validated). Le
plan révisé à 24 semaines / 6 vagues (DEC-000019) est en cours
d'exécution :

- **Vague 1 — Fondations (semaines 1-4, Python + Rust)** : **clôturée**
  (DEC-000021). Knowledge Engine reconnecté sur PostgreSQL v6.2
  (2026-07-17, remplace le stockage en mémoire de la Vague 1).
  - **Outbox worker opérationnel** (persistance asynchrone des
    événements, voir ADR-005 et `docs/OUTBOX_EXPLOITATION.md`).
  - **API Resources exposée** (endpoints CRUD sur les ressources
    scientifiques, voir ADR-001).
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
  - **RFC-0014** (Adopté) + **ADR-009** (Accepté) : garde-fou
    transverse anti-invention de données, applicable à tous les
    moteurs de raisonnement (Correlation, GIS, Botanical, Pedology, et
    futurs Reasoning/Diagnostic/Recommendation).
  - **Forest Dynamics Engine** — codé, périmètre volontairement
    restreint à la surface terrière (identité géométrique G = π/4×D²×N,
    aucun coefficient empirique) — volume et projection de croissance
    hors périmètre (coefficients de forme/modèles publiés pas encore
    sourcés). 6 tests.
  - **Climate Engine** — codé : dernière observation SYNOP Météo-France
    (data.gouv.fr, aucune clé), conversions Kelvin→Celsius et Pa→hPa
    vérifiées. Pas de projection climatique (DRIAS/RCP) — nécessite la
    clé API portail Météo-France (en attente). 8 tests.
  - **14/14 moteurs GSIE implémentés** (Evidence, Knowledge, Correlation,
    GIS, Botanical, Pedology, Forest Dynamics, Climate, Reasoning,
    Diagnostic, Recommendation, Validation, Learning, Simulation). Les 4
    moteurs manquants (Recommendation engine.py+router.py, Validation,
    Learning, Simulation) ont été implémentés en v1 déclarative le
    2026-07-27 (commit 4c64bcd) — modèles v1 simplifiés, explicitement
    marqués `confidence=low` ou `propose` (jamais validés automatiquement,
    GSIE-CON-001). 44 nouveaux tests unitaires + 31 tests du meta-test de
    conformité. Total : 992 tests unitaires passent.
  - **Enrichissement v1 sur données réelles** (2026-07-27, commit 4930aa1) :
    * **Pipeline cross-moteurs Validation + Learning** :
      `engines/validation_pipeline.py` câble le Validation Engine sur de
      vrais `Diagnostic` + `RecommendationSet` + `Conclusion` (pas des
      dicts abstraits). Le Learning Engine gère maintenant `sortie_bloquee`
      (accumulation par type de cause, proposition de calibration au-delà
      du seuil). `run_validation_pipeline()` orchestre la chaîne complète.
    * **Autécologie Rameau (2008)** : `seeds/autecology_rameau_data.py`
      ajoute 20 profils autécologiques sourcés (Flore forestière française,
      IDF) pour 4 essences (Fagus sylvatica, Pinus sylvestris, Quercus
      ilex, Abies alba), 5 variables par essence. Corpus combiné : 26
      profils (6 Parelle + 20 Rameau). `engines/autecology_adapter.py`
      transforme les profils en `RegleInference` pour le Reasoning Engine.
    * **Simulation calibrée IGN** : `engines/growth_models.py` (modèles de
      croissance calibrés sur données publiques IGN, 6 essences) +
      `engines/simulation_backend.py` (architecture strategy pattern :
      LinearGrowthBackend v1, CalibratedGrowthBackend v1 calibré
      confidence=medium, CapsisBackend futur NotImplementedError).
    * 43 nouveaux tests. Total : 1035 tests unitaires passent.
  - **Test E2E parcours GeoSylva + fiabilisation** (2026-07-27, commit
    bb96dca) : `tests/unit/test_e2e_geosylva.py` simule le parcours
    complet d'un forestier (Evidence → Reasoning → Diagnostic →
    Recommendation → Validation → Learning → Simulation) sur données
    réelles Rameau + IGN. 2 bugs corrigés : (1) `autecology_adapter.py`
    générait `essence == '...'` au lieu de `peuplement_essence_cible ==
    '...'` (KeyError Reasoning) ; (2) conflit de type `EvidenceLevel`
    (infrastructure.models.enums vs evidence.schemas). mypy + ruff
    passent. **1191 tests au total passent** (1039 unitaires + 152
    intégration PostgreSQL/PostGIS via testcontainers), 0 échec.
  - **Tests E2E larges GeoSylva** (2026-07-27, commit c2de4d1) :
    `tests/unit/test_e2e_large.py` ajoute 34 tests couvrant 9
    catégories de scénarios réalistes : multi-essences, contradictions
    Parelle/Rameau, risques climatiques, chemins d'erreur (6 tests),
    stress test (26 règles < 2s), simulation comparative 4 essences,
    calibration Learning (seuil 5), parcours API HTTP (12 endpoints
    + sécurité + 404 RFC 7807), parcours complet récapitulatif. 3 bugs
    découverts et corrigés (RisqueDiagnostic.domaine, plafonnement
    Quercus ilex, endpoints /status nouveaux moteurs). **1225 tests au
    total passent** (1073 unitaires + 152 intégration), 0 échec.
  - **Consortium d'agents GSIE** (2026-07-28) : mise en place du
    système de boucle poussée adaptative pour GLM 5.2 High. 3 fichiers
    créés : (1) `.devin/skills/consortium-agents/SKILL.md` — skill
    formel avec déclenchement adaptatif 3 niveaux (léger <5 fichiers /
    standard 5-15 / lourd >15 ou migration ou breaking ou sécurité), 9
    phases (qualification → reconnaissance → plan avec confiance 80%
    → implémentation incrémentale → diagnostic cause racine → tests
    pyramide → revue adversariale → PR dossier de preuve →
    capitalisation), 4 rôles séparés (architecte read-only /
    implémenteur / testeur adversarial / reviewer) mappés sur les
    profils subagent existants ; (2) `.devin/playbooks/feature.devin.md`
    — prompt maître complet activable manuellement ; (3)
    `.devin/rules/consortium-gating.md` — règle always-on avec arbre de
    décision. Intègre AI_AGENT_ORCHESTRATION.md (RACI, états, portes)
    sans le dupliquer. AGENTS.md mis à jour avec références.
  - **Pipeline cross-moteurs démontré réel** (2026-07-17) : 8 zones
    françaises réelles → occurrences GBIF (Botanical) + pH SoilGrids
    (Pedology) → Correlation Engine (spearman) → persisté en base.
    Résultat honnête : coefficient 0,24, non significatif (p=0,57,
    n=8) — démontre la chaîne fonctionnelle sans sur-interpréter un
    échantillon trop petit et un proxy (comptage brut d'occurrences)
    biaisé par l'effort d'observation.
  - **Constat Reasoning/Diagnostic/Recommendation** : leur contrat
    exige de raisonner sur l'autécologie des essences (optimum pH,
    tolérance gel), absente de Botanical Engine v1. Les construire
    maintenant forcerait soit un moteur vide, soit l'invention de
    règles — reporté jusqu'à l'ingestion réelle (Rameau et al., RFC-0014
    §3.2) ou une décision explicite du Fondateur.
  - **Pipeline d'extraction documentaire sourcée** (`Forge/src/dataset_forge/
    documents/extraction.py`) : pilote réussi sur un document réel
    (Lettre du DSF n°61) — 8 faits vérifiés, tous en quarantine.
  - **GeoSylva** (`apps/GeoSylva`, repo externe) : `CLAUDE.md` créé
    (articulation réseau GSIE serveur/Bluetooth/LoRa, RFC-0003). Bug
    trouvé et corrigé : `ExpertForestryCalculator.getSchumacherHallParameters()`
    utilisait 3 coefficients inventés alors que `SylvicultureDatabase.kt`
    contient déjà 30 essences sourcées (Vallet et al. 2006) jamais
    appelées — branché. Non vérifié par build réel (TLS/JVM local
    bloqué) — à valider.
  - **RFC-0016 Phase A — schéma forestier spécialisé, complète
    (2026-07-19)** : les 10 entités du §3.1 sont implémentées en 6
    tranches successives (`9a87d98` à `f1cb482`, branche
    `handoff/audit-2026-07-19`) :
    1. `AutecologyProfile`, `SiteIndexModel`, `FertilityClass`
    2. `StationType`, `StationObservation`
    3. `SilviculturalSystem`, `SilviculturalRule` (`Intervention` réutilisée, déjà existante)
    4. `ProvenanceMaterial`
    5. `DiagnosticProtocol`, `HealthRisk`
    6. `EvidenceStatement`/`ConflictRecord` — aucune nouvelle table,
       réutilisation documentée de `AssertionModel`/
       `EvidenceAssessmentModel`/`ConflictClusterModel` déjà existants,
       + schéma Pydantic dédié `EvidenceStatementCreate`/`Record`
       (`evidence/schemas.py`) imposant `page_or_table` obligatoire.
    Bilan : 10 nouvelles tables satellite (`autecology_profile`,
    `site_index_model`, `fertility_class`, `station_type`,
    `station_observation`, `silvicultural_system`,
    `silvicultural_rule`, `provenance_material`, `diagnostic_protocol`,
    `health_risk`) + 3 entités réutilisées sans duplication
    (`Intervention`, `EvidenceStatement`, `ConflictRecord`). Registre de
    types resources 76→86. 364 tests unitaires (304 passed, 60
    skipped), `check_governance_consistency.py` OK après chaque
    commit. Fichiers modifiés : `GSIE/API/src/gsie_api/infrastructure/
    models/forestry.py` (nouveau, 10 modèles SQLAlchemy),
    `infrastructure/models/enums.py` (nouveaux enums :
    `SilviculturalSystemCategory`, `MaterielBaseCategory`,
    `HealthRiskSeverity`), schéma forestier désormais intégré à la baseline
    `20260726_0001` (les révisions historiques `0006` à `0010` ont été
    absorbées par DEC-000036), `engines/forest_dynamics/schemas.py`,
    `engines/botanical/schemas.py` (AutecologyProfile),
    `engines/evidence/schemas.py` (EvidenceStatement),
    `tests/unit/test_forestry_schemas.py` (nouveau, ~50 tests),
    `tests/unit/test_resources.py`.
  - **RFC-0016 Phase B — intégration Botanical/Forest Dynamics Engine,
    complète (2026-07-19)** : les 3 points de la Phase B sont
    implémentés sur la branche `handoff/audit-2026-07-19` :
    1. `f0abd6c` — fermeture d'un trou de la Phase A : les 10 types de
       resource forestiers n'avaient aucune entrée dans le validateur
       générique `resources/validators.py` (champs obligatoires + enums
       ajoutés pour les 10 types) ; dans le même commit, démarrage du
       point 6 (passeport de décision) : `DecisionPassportCategory`/
       `DecisionPassportItem`/`DecisionPassport`
       (`shared/schemas.py`, cross-engine), 5 catégories (observe,
       calcule, modelise, documente_recommande, incertain) chacune avec
       justification obligatoire imposée par `model_post_init`.
    2. `3afd358` — point 5 : `DendrometricRequest`/`Result` du Forest
       Dynamics Engine portent désormais `station_observation_id`
       optionnel (passthrough, pas de résolution DB — moteur reste une
       fonction pure v1) ; nouvelle méthode
       `ForestDynamicsEngine.to_decision_passport_items()` connectant ce
       moteur au passeport de décision (catégorie `calcule`).
    3. `948802b` — point 4 : nouveau module
       `gsie_api.engines.botanical.extraction_bridge`
       (`QuarantinedFact`, `build_autecology_profile_from_quarantined_fact()`)
       reliant le pipeline d'extraction documentaire (RFC-0014 §3.2,
       `KnowledgeExtractor` dans `Forge/`) à `autecology_profile` — le
       curateur humain fournit toujours `variable`/valeur, seul `method`
       (citation + page + référence) est construit automatiquement à
       partir d'un fait déjà vérifié ; refuse tout fait dont
       `statut != "quarantine"`. Testé sur les 29 faits réels du 3e
       pilote RFC-0014 §3.6 (Quercus robur/petraea, waterlogging,
       Parelle 2007).
    Bilan : 387 tests unitaires (327 passed, 60 skipped),
    `check_governance_consistency.py` OK après chaque commit. Fichiers
    modifiés : `GSIE/API/src/gsie_api/resources/validators.py`,
    `shared/schemas.py`, `engines/forest_dynamics/schemas.py`,
    `engines/forest_dynamics/engine.py`,
    `engines/botanical/extraction_bridge.py` (nouveau),
    `tests/unit/test_decision_passport.py` (nouveau),
    `tests/unit/test_forest_dynamics.py`,
    `tests/unit/test_extraction_bridge.py` (nouveau),
    `tests/unit/test_resources.py`. Seule **Phase C (pilote
    Nouvelle-Aquitaine)** reste à faire — voir `DEC-000027`.

Rappel Phase 2 : les 12 livrables (201-212) sont Draft complets, prêts
pour Review.

### Session 2026-08-01 — Visualisation DB + SDK + Tableau de contrôle

#### Outils de visualisation de base de données

Stack open-source self-hosted déployée via `GSIE/docker-compose.viz.yml`
(veille `GSIE/RESEARCH/VEILLE_OUTILS_VISUALISATION_DB_2026-07-31.md`) :

| Outil | Rôle | URL | Conteneur |
|---|---|---|---|
| Metabase | BI self-service (non-tech) | http://localhost:3030 | `gsie-metabase` |
| Apache Superset | BI avancée (SQL Lab, dashboards) | http://localhost:8088 | `gsie-superset` |
| Dekart | Carto web Kepler.gl (PostGIS) | http://localhost:8089 | `gsie-dekart` |

**Sécurité** :
- Migration Alembic `20260801_0025` appliquée — crée le groupe
  `gsie_viz_lecture` (NOLOGIN) avec `SELECT` sur `public` + 7 schémas de
  domaine, `REVOKE ALL` explicite sur `gsie_rgpd` et
  `gsie_rgpd_identites`.
- Comptes de connexion créés via `docker/comptes-de-connexion.sql` :
  `gsie_api` (LOGIN, NOSUPERUSER, NOBYPASSRLS) pour l'API, `gsie_viz`
  (LOGIN, NOSUPERUSER) pour les outils de visualisation.
- Vérifié : `gsie_viz` peut lire `spatial_ref_sys` (8500 lignes) mais est
  bloqué sur `gsie_rgpd_identites.data_subject` (permission denied).
- Profil `viz` dans le compose : les conteneurs ne démarrent pas sans
  `--profile viz` (audit sécurité, constat D).
- Ports liés à `127.0.0.1` (pas d'exposition externe).
- `MB_ENCRYPTION_SECRET_KEY` et `SUPERSET_SECRET_KEY` configurées.
- `DEKART_CORS_ORIGIN` restreint à `localhost:8089`.

**Dekart** : configuration corrigée — séparation stockage SQLite embarqué
(sans licence) / datasource PostGIS via
`DEKART_POSTGRES_DATASOURCE_CONNECTION`. Les variables
`DEKART_POSTGRES_*` (DB/USER/PASSWORD/HOST/PORT) sont pour le backend de
métadonnées Postgres qui exige une licence — non utilisées.

**Metabase** : initialisé via API `/api/setup` — compte admin créé
depuis `GSIE_METABASE_ADMIN_EMAIL`/`GSIE_METABASE_ADMIN_PASSWORD`, DB
« GSIE PostGIS » connectée (sync complète, PG 16.14 détecté), sample DB
supprimée, locale fr.

**Superset** : initialisé via CLI — `superset db upgrade`, `superset fab
create-admin` (depuis `GSIE_SUPERSET_ADMIN_PASSWORD`), `superset init`,
connexion DB « GSIE PostGIS » créée via `superset set-database-uri`.

**SchemaSpy → script SQL+Python** : SchemaSpy incompatible PG16
(`datlastsysoid` supprimé en PG15) et tbls incompatible avec l'héritage
class-table de PostgreSQL. Remplacés par `GSIE/TOOLS/generate_schema_doc.sql`
+ `generate_schema_doc.py` qui génèrent `GSIE/DOCUMENTATION/SCHEMA_DB.md`
(120 tables, 2122 colonnes, 7 schémas avec types, contraintes,
commentaires et tailles).

**Documentation** : `GSIE/DOCUMENTATION/VISUALISATION_DB_ACCES.md`
(URLs, credentials, commandes Docker, architecture réseau, sécurité)
+ `GSIE/DOCUMENTATION/SCHEMA_DB.md` (doc du schéma DB).

#### SDK Python GSIE

SDK minimal créé dans `GSIE/SDK/python/` (P0-3 première moitié) :
- Client async `httpx` avec authentification JWT RS256 et refresh
  automatique des tokens.
- Wrappers pour les moteurs GSIE : diagnostic, recommendation,
  validation, simulation.
- Exceptions typées (`GSIEAuthError`, `GSIEAPIError`, `GSIEConnectionError`).
- Tests unitaires avec `respx` (mock réseau) + `pytest-asyncio`.
- Validation : `ruff check` OK, `mypy --strict` OK, tous tests passent.
- `pyproject.toml` configure le package `gsie_sdk` avec dépendances
  minimales (`httpx`, `pyjwt[crypto]`).

#### Tableau de contrôle admin GSIE

Dashboard web créé dans `GSIE/ADMIN_WEB/` (Astro 5 + React 19 Islands +
Tailwind CSS 4 + TypeScript). **Design calqué sur Tabler** (dashboard
open-source Bootstrap 5, reproduit en Tailwind 4 sans dépendance
Bootstrap) : sidebar gauche groupée par sections + topbar sticky avec
search/notifications/user menu + cards avec header + stat cards avec
icône/trend + badges semi-transparents + tables borderless avec hover.

| Page | URL | Contenu |
|---|---|---|
| Vue d'ensemble | `/` | 4 stat cards (icône + trend) + santé système (DB, API, disque, mémoire, alertes) |
| Moteurs | `/engines` | 14 moteurs avec filtres (core/domain/transverse), statut, uptime, latence |
| Utilisateurs | `/users` | Tableau avec recherche + filtres par rôle (admin, forestier, chercheur, lecteur) |
| Données | `/data` | Catalogue datasets avec filtres par source (Treekipedia, IGN, Météo-France, GBIF, SoilGrids) |

**Architecture** :
- Hydratation sélective : sidebar, topbar et stat cards en HTML statique
  (0 JS), seuls les tableaux/grids interactifs sont des React Islands
  (`client:load`).
- Client API hybride (`lib/api.ts`) : mock data par défaut, détection
  auto de l'API GSIE sur `localhost:8000/health` — bascule sans
  modification de l'UI.
- Types partagés (`lib/types.ts`) compatibles avec l'API FastAPI.
- Build de production : 4 pages, 0 erreur, islands 3.5-4.5 KB chacun.
- `astro check` : 0 erreur, 0 warning, 0 hint (17 fichiers).
- Port 4000 (évite conflits avec API :8000 et viz :3030/:8088/:8089).

**Préparation version serveur** : l'architecture est découplée —
`lib/api.ts` centralise les appels, les composants consomment uniquement
les types. Quand la version serveur GSIE sera déployée, définir
`GSIE_API_URL` dans `.env` — aucune modification de l'UI.

#### Audit concurrentielle — corrections

L'analyse concurrentielle (`22_PROJECT_MEMORY/analyses/ANALYSE_CONCURRENTIELLE_2026-07-31.md`)
a été corrigée sur deux P0 invalides :
- **P0-4 « 3 moteurs stubs »** : incorrect — les moteurs Recommendation,
  Validation et Simulation sont implémentés avec tests.
- **P0-5 « autécologie absente »** : incorrect — l'adapter autecology
  existe dans Botanical Engine (RFC-0016 Phase A, 10 tables forestières).

#### P0 restants (après cette session)

| ID | Description | Statut |
|---|---|---|
| P0-1 | Sauvegardes DB (pgBackRest + WAL archiving) | **À faire** |
| P0-3 (2e moitié) | SDK Kotlin pour GeoSylva | **En cours — première tranche parcelles livrée ; pull et conflits à compléter** |
| AUTH-2 | Vérification e-mail + récupération de mot de passe | **Terminé — DEC-000046** |
| AUTH-3 | Écrans de compte web/GeoSylva + configuration OAuth Google | **GeoSylva livré ; Web et configuration publique à faire** |
| P1-8 | Intégration GeoSylva/QGISIA ↔ GSIE via SDK | **GeoSylva parcelles partiel ; QGISIA et SDK partagé à faire** |

### Session 2026-08-02 (soir) — Consolidation + diagnostic Fondateur + DEC-000043

#### État réel mesuré (chiffres vérifiés, non estimés)

| Métrique | Valeur | Source |
|---|---|---|
| Moteurs implémentés | 14 + orchestration | `src/gsie_api/engines/` (16 dirs) |
| Migrations Alembic | 31 | `alembic/versions/` |
| Tables SQLAlchemy | 126 | `Base.metadata.tables` |
| Schémas PostgreSQL | 7 | public, gsie_botanique, gsie_foret, gsie_gouvernance, gsie_rgpd, gsie_rgpd_identites, gsie_synchronisation |
| Routes API | 97 | `create_app().routes` |
| Tests API — dernière campagne globale terminée | 1 936 passed, 63 skipped, 0 failed | `pytest` ; campagne suivante limitée à 10 min |
| Couverture API — dernière campagne globale terminée | 99 % (9 580/9 702 statements) | `pytest --cov=gsie_api` |
| Domaine identité actuel | 170 passed ; cycle, dépôt et e-mail à 100 % | campagne ciblée du 2026-08-03 |
| GeoSylva Android | 518 passed, 0 skipped, 0 failed ; Lint 0 erreur | rapports Gradle |
| Synchronisation parcelles | 19 tests ciblés API/DB/Android ; compilation Android verte | campagnes du 2026-08-03 |
| Score mutation | 67/67 (100%) | `tests/mutation/harnais.py` |
| Lint | ruff OK | `ruff check src/ tests/` |
| Typage | mypy OK | `mypy src/gsie_api/` |

#### 63 skipped — analyse catégorielle

| Catégorie | Count | Raison | Action |
|---|---|---|---|
| Seeds v6.1 legacy | 46 | Migration v6.1 → v6.2 (RFC-0012) Vague 2 | Réactiver après migration |
| Schéma KnowledgeObject → Assertion | 14 | RFC-0012 | Réactiver après migration |
| Rust Evidence Engine absent | 3 | Wheel Rust non construite sur Windows | CI Linux |

#### Diagnostic Fondateur (2026-08-02)

> Le code est plus mature que le produit intégré.

Rapidité 9/10, qualité technique 8/10, qualité produit 6,5-7/10.
Il manque la preuve complète : terrain → données réelles → preuve
scientifique → diagnostic → recommandation → validation humaine →
application cliente/Hub.

#### Phase de stabilisation (DEC-000043) — CLÔTURÉE ✅

Trois livrables produits et validés :

1. **S1 — Restauration DB prouvée** ✅ (commit `74b1b59`) : backup →
   restore → vérification d'intégrité (127 tables, 327 FK, 475 index,
   parité source ✓). Scripts : `test_restauration_db.sh` (bash),
   `test_restauration_db.py` (Python CI). Document :
   `DR-RESTAURATION.md`.
2. **S2 — Tranche verticale réelle** ✅ (commit `b6b61f6`) : chaîne
   complète Reasoning→Diagnostic→Recommendation→Validation sur pilote
   Parelle 2007 (Quercus robur vs petraea), 0.15s, diagnostic persisté,
   recommandation produite, validation `valide`. Script :
   `tranche_verticale.py`. Document : `TRANCHE_VERTICALE.md`.
3. **S3 — Validation scientifique + benchmark** ✅ (commit `56d4ba5`) :
   3/3 scénarios ground truth validés (18/18 checks), latence moyenne
   32ms, p95 34.68ms, mémoire 0.25 MB. Script :
   `validation_benchmark.py`. Document : `VALIDATION_SCIENTIFIQUE.md`.

**Gates 4/5/6 rouvrables** : la preuve de chaîne complète est faite,
les prédictions sont cohérentes avec la littérature, les performances
sont mesurées et reproductibles.

> La mémoire détaillée vit dans `22_PROJECT_MEMORY/`.
> La roadmap complète vit dans `ROADMAP.md`.

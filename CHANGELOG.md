# CHANGELOG — Quintessences / GSIE

Format : `## [version] - YYYY-MM-DD`

---

## [DEC-000029 — SCISSION RFC-0017 EN RFC-0018 / RFC-0019] - 2026-07-20

### Veille technologique et scission en RFC d'exécution

- `GSIE/RESEARCH/VEILLE_PLANTNET_NVIDIA_NIM_QUINTESSENCES_2026-07-20.md` —
  veille externe (Pl@ntNet, NVIDIA NIM/Blueprints/Skills/Brev) versée
  pour traçabilité.
- `RFC-0017` ouvert puis adopté comme cadrage (DEC-000029), aussitôt
  scindé en deux RFC d'exécution indépendants, tous deux en `Draft` —
  aucun code métier autorisé avant leur propre décision :
  - `RFC-0018` — identification botanique assistée Pl@ntNet (cycle
    `SUGGESTION_IA` → `VALIDEE_UTILISATEUR`, extension satellite
    d'`AutecologyProfile`, volet modèle embarqué offline à l'étude).
  - `RFC-0019` — `gsie-ai-gateway`, couche IA serveur transverse
    (périmètre P0 : RAG scientifique, garde-fou, `GSIE-Eval-FR`).
- `PROJECT_MEMORY.md` synchronisé (RFC ouverts, décisions actives).

## [PHASE 4 — RFC-0016 SCHÉMA FORESTIER SPÉCIALISÉ — PHASE B COMPLÈTE] - 2026-07-19

### RFC-0016 Phase B (intégration Botanical/Forest Dynamics Engine) — 3/3 points implémentés

- 3 commits successifs sur la branche `handoff/audit-2026-07-19`,
  faisant suite à la Phase A :
  1. `f0abd6c` — fermeture d'un trou de la Phase A : les 10 types de
     resource forestiers n'avaient aucune entrée dans le validateur
     générique `resources/validators.py` — un appel direct à l'API
     générique `POST /resources` pouvait contourner la règle déjà
     imposée par les schémas Pydantic (champs obligatoires + enums
     ajoutés pour les 10 types). Dans le même commit, démarrage du
     point 6 (passeport de décision) : `DecisionPassportCategory`/
     `DecisionPassportItem`/`DecisionPassport`
     (`shared/schemas.py`, cross-engine, pas spécifique à un moteur),
     5 catégories (observe, calcule, modelise,
     documente_recommande, incertain), chacune avec justification
     obligatoire imposée par `model_post_init`.
  2. `3afd358` — point 5 : extension du Forest Dynamics Engine.
     `DendrometricRequest`/`Result` portent désormais
     `station_observation_id` optionnel (passthrough, pas de
     résolution DB — le moteur reste une fonction pure v1). Ajout de
     `ForestDynamicsEngine.to_decision_passport_items()` construisant
     des `DecisionPassportItem` (catégorie `calcule`) à partir d'un
     résultat dendrométrique — connecte ce moteur au passeport de
     décision.
  3. `948802b` — point 4 : nouveau module
     `gsie_api.engines.botanical.extraction_bridge`
     (`QuarantinedFact`,
     `build_autecology_profile_from_quarantined_fact()`). Fait le pont
     entre le pipeline d'extraction documentaire (RFC-0014 §3.2,
     `KnowledgeExtractor` dans `Forge/`) et la table
     `autecology_profile` (RFC-0016 tranche 1/10). Ne dérive jamais
     `variable`/valeur par heuristique — le curateur humain fournit
     toujours ces champs explicitement ; seul le champ `method`
     (citation + page + référence) est construit automatiquement à
     partir d'un fait déjà vérifié. Refuse tout fait dont
     `statut != "quarantine"`. Testé directement sur les 29 faits réels
     du 3e pilote RFC-0014 §3.6
     (`GSIE/KNOWLEDGE/pilotes_extraction/parelle_2007_quercus_waterlogging_facts.json`,
     Quercus robur/petraea, waterlogging).
- Bilan : les 3 points de la Phase B (points 4, 5, 6 du RFC-0016 §5)
  sont désormais couverts. 387 tests unitaires (327 passed, 60
  skipped), `tools/check_governance_consistency.py` OK après chaque
  commit.
- Fichiers principaux : `GSIE/API/src/gsie_api/resources/validators.py`,
  `shared/schemas.py`, `engines/forest_dynamics/schemas.py`,
  `engines/forest_dynamics/engine.py`,
  `engines/botanical/extraction_bridge.py` (nouveau),
  `tests/unit/test_decision_passport.py` (nouveau),
  `tests/unit/test_forest_dynamics.py`,
  `tests/unit/test_extraction_bridge.py` (nouveau),
  `tests/unit/test_resources.py`.
- **Reste à faire** : Phase C (pilote Nouvelle-Aquitaine — constitution
  du corpus 12-20 essences, 50 cas « or » validés par un forestier
  référent, premier pack offline signé) — non commencée. Voir
  `02_RFC/RFC-0016-schema-forestier-specialise.md` et
  `03_DECISIONS/DEC-000027.md`.

---

## [PHASE 4 — RFC-0016 SCHÉMA FORESTIER SPÉCIALISÉ — PHASE A COMPLÈTE] - 2026-07-19

### RFC-0016 Phase A (schéma de données) — 10/10 entités implémentées

- 6 tranches successives sur la branche `handoff/audit-2026-07-19` :
  1. `9a87d98` — `AutecologyProfile`, `SiteIndexModel`, `FertilityClass`.
  2. `1807670` — `StationType`, `StationObservation`.
  3. `0995cb5` — `SilviculturalSystem`, `SilviculturalRule`
     (`Intervention` réutilisée, déjà existante).
  4. `0ca7d1a` — `ProvenanceMaterial`.
  5. `635b8af` — `DiagnosticProtocol`, `HealthRisk`.
  6. `f1cb482` — `EvidenceStatement`/`ConflictRecord` : aucune nouvelle
     table, réutilisation documentée de `AssertionModel`/
     `EvidenceAssessmentModel`/`ConflictClusterModel` déjà existants,
     + nouveau schéma Pydantic `EvidenceStatementCreate`/`Record`
     (`evidence/schemas.py`) imposant `page_or_table` obligatoire.
- Bilan : les 10 entités du §3.1 du RFC-0016 sont désormais toutes
  couvertes — 10 nouvelles tables satellite (`autecology_profile`,
  `site_index_model`, `fertility_class`, `station_type`,
  `station_observation`, `silvicultural_system`, `silvicultural_rule`,
  `provenance_material`, `diagnostic_protocol`, `health_risk`) + 3
  entités réutilisées sans duplication (`Intervention`,
  `EvidenceStatement`, `ConflictRecord`).
- Registre de types resources : 76 → 86 types.
- Nouveaux enums : `SilviculturalSystemCategory`,
  `MaterielBaseCategory`, `HealthRiskSeverity`
  (`infrastructure/models/enums.py`).
- 5 migrations Alembic (`0006` à `0010`).
- 364 tests unitaires (304 passed, 60 skipped),
  `tools/check_governance_consistency.py` OK après chaque commit.
- Fichiers principaux : `GSIE/API/src/gsie_api/infrastructure/models/
  forestry.py` (nouveau), `engines/forest_dynamics/schemas.py`,
  `engines/botanical/schemas.py`, `engines/evidence/schemas.py`,
  `tests/unit/test_forestry_schemas.py` (nouveau), `tests/unit/
  test_resources.py`.
- **Reste à faire** : Phase B (intégration Botanical/Forest Dynamics
  Engine, passeport de décision à 5 catégories) et Phase C (pilote
  Nouvelle-Aquitaine) — non commencées. Voir `02_RFC/
  RFC-0016-schema-forestier-specialise.md` et `03_DECISIONS/
  DEC-000027.md`.

---

## [PHASE 4 — RFC-0015 ENVIRONMENTAL MODEL FABRIC + CLIMATE ENGINE ÉTENDU] - 2026-07-18

### RFC-0015 adoptée (DEC-000026)

- Étend ADR-007/RFC-0014 (garde-fou anti-invention des données) aux
  modèles scientifiques : registre de modèles (`ModelRegistry`/
  `ModelArtifact`/`LicenseRecord`/`ApplicabilityDomain`/
  `ValidationRun`), LLM strictement orchestrateur non autoritaire,
  vocabulaire imposé (observation/estimation/simulation/
  recommandation ; association/hypothèse causale/effet estimé),
  Correlation Engine v2 (pipeline causal 8 étapes, candidats DoWhy/
  Tigramite/PyMC/MAPIE), packs offline signés GeoSylva, progression
  par vertical slices mesurables.
- Issue de l'étude externe versée
  `GSIE/RESEARCH/ETUDE_MODELES_OPEN_SOURCE_QUINTESSENCES_2026-07-18.md`.
- Voir `02_RFC/RFC-0015-environmental-model-fabric.md`,
  `03_DECISIONS/DEC-000026.md`.

### Climate Engine — 4 nouvelles sources réelles Météo-France (portail API)

- Météo des forêts (danger feux J+1/J+2), DPClim (climatologie
  quotidienne, flux 3 étapes commande/polling/fichier), Vigilance
  (carte de vigilance J/J+1), Package Observations (24h glissantes) —
  en plus du flux SYNOP déjà en place. 21 tests, formes de réponse
  réelles capturées.

### Forge — audit et corrections réelles

- Identité git configurée (blocage de commit résolu).
- Recherche documentaire (`documents search`) : agrégation réelle
  HAL + OpenAlex + arXiv au lieu d'arXiv seul (bug de pertinence
  corrigé — requêtes françaises renvoyaient des résultats hors sujet).
  Correction du paramètre OpenAlex (`query` retiré par l'API,
  remplacé par `search`).
- Scraping (`scrape`) : branchement des 5 connecteurs jusqu'ici
  inutilisés (Flickr, Wikimedia, Zenodo, Roboflow, images web), en
  plus de Hugging Face.
- 105 tests passent, mypy --strict propre.

---

## [PHASE 4 — BOTANICAL ENGINE + PEDOLOGY ENGINE] - 2026-07-17

### Nouveaux moteurs — Botanical (GBIF) et Pedology (SoilGrids)

- **Botanical Engine** : résolution taxonomique via GBIF Backbone
  Taxonomy (`species/match`, aucune clé API), résolution de synonymes
  vers le taxon accepté (vérifié : *Quercus sessiliflora* → *Quercus
  petraea*), déduplication par clé GBIF (`entity` + `entity_alias`,
  CON-010). Pas d'autécologie en v1 — nécessite des connaissances
  sourcées (Rameau et al.) pas encore ingérées (RFC-0014). 8 tests.
- **Pedology Engine** : pH (H2O) + texture (argile/sable/limon) via
  SoilGrids (ISRIC, aucune clé), valeurs mises à l'échelle par
  `d_factor` (vérifié empiriquement : argile+sable+limon ≈ 100%).
  `evidence_level=B` — source unique peer-reviewed (Poggio et al.,
  2021), jamais A sans convergence multi-sources
  (EVIDENCE_FRAMEWORK.md). Pas de persistance en v1 (estimation
  ponctuelle sans identité stable). 6 tests.
- **Fix checker de gouvernance** : la règle 3 (ADR-007) signalait à
  tort une `SourceReference(...)` contenant "v2.0" dans une URL comme
  valeur non sourcée — une SourceReference EST déjà la citation
  structurée, désormais exclue explicitement.

### Métriques

- 6/14 moteurs GSIE codés (Evidence, Knowledge, Correlation, GIS,
  Botanical, Pedology). 255 tests passent, 0 échec, 60 skipped, 86%
  couverture. ruff + mypy --strict verts.

---

## [PHASE 4 — GARDE-FOU ANTI-INVENTION + GIS ENGINE] - 2026-07-17

### Gouvernance — RFC-0014, ADR-007

- **RFC-0014** (Adopté) : garde-fou anti-invention de données + pipeline
  d'ingestion de littérature scientifique non structurée, en réponse à
  une exigence explicite du Fondateur (aucune fausse donnée, corrélations
  basées uniquement sur des sources scientifiques réelles).
- **ADR-007** (Accepté) : formalise le garde-fou en décision opposable —
  tout moteur de raisonnement doit justifier source, evidence_level et
  chaîne de provenance pour chaque valeur produite.
- **Checker de gouvernance** : règle 3 ajoutée — détection best-effort de
  constantes numériques (seuils, coefficients) sans citation détectable
  dans les moteurs (`engines/*/engine.py`). 7 tests.
- Lien vers `GSIE/DATASETS/SOURCES_DONNEES_EXHAUSTIVES.md` (catalogue de
  ~179 sources avec méthodes d'accès concrètes) depuis RFC-0013/RFC-0014.

### Pipeline d'extraction sourcée (Forge)

- `Forge/src/dataset_forge/documents/extraction.py` — `KnowledgeExtractor` :
  extraction de faits scientifiques via NVIDIA NIM sous contrainte de
  citation exacte, vérifiée automatiquement contre le texte source,
  statut `quarantine`/`rejete` uniquement (jamais `accepte` automatique).
- Pilote réussi sur un document réel (*Lettre du DSF n°61*, sept. 2024,
  agriculture.gouv.fr) : 8 faits extraits, tous vérifiés.
- Corrections apportées en cours de route : fix venv Forge (chemin
  obsolète après renommage), fix TLS (`truststore`, interception réseau
  locale), modèle `deepseek-v4-flash` préféré à un modèle de raisonnement
  qui épuisait son budget de tokens, parsing JSON tolérant.

### Nouveau moteur — GIS Engine (sort du placeholder)

- Cadastre (API Carto IGN) et altitude (API de calcul altimétrique IGN) —
  données réelles vérifiables sans clé API, géométrie persistée en
  Lambert-93 (`place`, PostGIS). 7 tests (respx, réponses réelles).

### Métriques

- 241 tests API GSIE passent, 0 échec, 60 skipped, 85% couverture
- ruff + mypy --strict verts

---

## [PHASE 4 — CORRELATION ENGINE (v1 réduite)] - 2026-07-17

### Nouveau moteur — Correlation Engine

- `GSIE/API/src/gsie_api/engines/correlation/` (schemas.py, engine.py,
  router.py) — 3e moteur codé après Evidence et Knowledge.
- Calcule pearson/spearman/kendall (scipy) + p-valeur, classe la force
  selon l'échelle Evans (1996), persiste comme `resource(type=correlation)`
  + `CorrelationModel` (schéma v6.2 déjà en place, jusque-là orphelin).
- **Périmètre v1 assumé et documenté** (voir docstring `schemas.py`) :
  contrairement à CORRELATION_ENGINE.md §5, les valeurs sont fournies
  directement dans la requête (les moteurs domaine GIS/Climate/Pedology/
  Botanical/Forest Dynamics n'existent pas encore — seul GIS a un
  placeholder), et une seule paire de variables par requête (pas de
  matrice N×N). Le contrat de sortie respecte la forme cible pour une
  extension future sans rupture.
- 4 endpoints : `/correlation/{status,version,compute,stats}`, branchés
  dans `app.py`.
- 10 tests d'intégration (`tests/integration/test_correlation.py`),
  tous verts, contre Postgres réel.
- Dépendance ajoutée : `scipy==1.15.3`.

---

## [PHASE 4 — GOUVERNANCE : ADOPTION RFC-0011 / ADR-001-006 + FIX MIGRATION] - 2026-07-17

### Gouvernance

- **RFC-0011** : Proposé → Adopté (validation Fondateur)
- **ADR-001, ADR-002, ADR-003, ADR-005, ADR-006** : Proposé → Accepté
  (ADR-004 déjà Validated). Les 6 ADR adoptés par DEC-000022 (déjà
  Validated depuis le 2026-07-16) affichaient encore leur statut
  d'origine — décalage détecté par `tools/check_governance_consistency.py`
  (5 findings « implémentation prématurée »), résolu par mise à jour des
  statuts propres des ADR/RFC pour refléter la décision déjà prise.
- Checker de gouvernance : 0 incohérence (5 → 0)

### Migration 0002 — bug de tables manquantes corrigé

- `alembic/versions/0002_metamodel_v6.2_resource_73types.py` n'important
  pas le module `business.py`, les 7 tables métier ONF/CNPF
  (`management_plan`, `intervention`, `economic_scenario`, `regulation`,
  `compliance_check`, `outcome_tracking`, `administrative_unit`)
  n'étaient jamais créées par `alembic upgrade head` sur une vraie base,
  bien qu'exposées via le CRUD générique (`RESOURCE_TYPES`). Corrigé en
  ajoutant l'import `business` dans `upgrade()` et `downgrade()`.
  Vérifié empiriquement (upgrade réel contre Postgres/AGE/PostGIS,
  les 7 tables sont créées).

### Tests E2E API — mismatch de boucle asyncio résolu

- `tests/integration/test_pipeline_api.py` : remplacement de
  `TestClient` (synchrone) par `httpx.AsyncClient(transport=ASGITransport(...))`
  — supprime le mismatch de boucle événementielle qui bloquait les 2
  tests d'écriture réelle en base. Les 3 tests E2E (pipeline complet,
  pipeline avec révision, rejet connaissance refusée) passent désormais
  réellement, plus aucun skip sur ce fichier.

### Métriques

- 224 tests passent, 0 échec, 60 skipped, 85% couverture
- ruff clean

---

## [PHASE 4 — CI 100% VERTE] - 2026-07-16

### CI GitHub Actions — tous jobs passent

- **Governance Guard** — DEC-000019/020/021/023 : ajout champ Décideur manquant
- **Python lint + type + test** — ruff 0.8.4 (pin CI), mypy override gsie_evidence,
  aiosqlite dev dep, skip tests Rust fallback sans wheel, server_default JSONB
  portable (retiré du modèle, gardé dans Alembic)
- **Python integration tests** — drop postgis_tiger_geocoder extension (conflit
  table place avec PlaceModel)
- **Docker build** — rustc 1.80→1.85 (edition2024 dépendances transitives),
  maturin 1.9.6 pin (compatible rustc 1.85)
- **CI Gate** — bloque merge si un job échoue

### Métriques

- 194 tests unitaires passent, 79 skipped, 84% couverture
- 9 tests integration PostGIS/Redis passent (testcontainers)
- ruff + mypy --strict verts
- Docker build reproductible (rustc 1.85 + maturin 1.9.6)

---

## [PHASE 4 — VAGUE 1 : STABILISATION DOCKER + AUTH + TESTS POSTGIS] - 2026-07-16

### Gate 2 — Docker reproductible

- **Fix docker-compose.yml** — context=project root (le Dockerfile COPY depuis
  `GSIE/API/` et `GSIE/ENGINES/EVIDENCE_ENGINE/rust/`, le context doit être la
  racine du projet, pas `GSIE/API/`)
- **.dockerignore racine** — exclut `apps/`, `Forge/`, `.git/`, dossiers
  gouvernance, caches Python/Rust, secrets
- **entrypoint.sh** — lance `alembic upgrade head` avant Gunicorn (fail fast si
  migration échoue)
- **Dockerfile** — copie `alembic/`, `alembic.ini`, `docker/` dans l'image
- **docker-compose.yml** — monte `keys/` en lecture seule pour JWT RS256
- **generate-jwt-keys.sh** — script génération paire RSA 2048 bits (openssl)

### Gate 3 — Auth production

- **Audit trail** — IP + User-Agent tracés sur `login_success` et `login_failed`
  (CON-005, OWASP A09)
- **Refresh token** — `jti` tracé pour corrélation
- **.env.example** — documentation procédure production (4 étapes)
- **README** — démarrage rapide mis à jour (clés JWT, migrations auto, curl login)

### Gate 4 — Tests PostGIS/Redis réels

- **9 tests d'intégration testcontainers** (PostgreSQL/PostGIS + Redis) :
  - Connexion PostgreSQL + PostGIS (extension vérifiée)
  - CRUD resource : insert, read, soft delete (CON-010)
  - JSONB : requête `metadata_json->>'essence' = 'chene_sessile'`
  - PostGIS : Place avec Geometry SRID 2154 (Lambert-93)
  - PostGIS : `ST_DWithin` — places proches de Landiras (zone test Ignis)
  - Redis : set/get + Pub/Sub (WebSocket fan-out)
- **CI** — `python-integration` ajouté au CI gate (bloque merge si échec)

### Qualité

- **app.py** — migration `on_event` (déprécié) → `lifespan` (FastAPI 0.115+)
- **194 tests passent**, 84% couverture, 0 warning deprecation
- **ruff check** : 0 erreur | **mypy --strict** : 0 erreur

---

## [PHASE 4 — VAGUE 1 : QUALITÉ + GOUVERNANCE + INGESTION] - 2026-07-16

### Qualité API

- **22 tests service.py** — mass-assignment, append-only, soft-delete (98% coverage)
- **CI gate** — ruff + mypy --strict + pytest (83% couverture, 194 tests, 0 échec)
- **Fix bugs** — revision_id → to_revision_id (ResourceDiffModel), create() retournait request.data non filtré
- **Typage** — 14 erreurs mypy corrigées, 54 erreurs ruff corrigées

### Gouvernance

- **RFC-0013** — ingestion données forestières ONF/CNPF/IGN (Draft)
- **DEC-000024** — décision ingestion données forestières (Proposé)

### Métamodèle v6.2

- **7 types métier ONF/CNPF** — management_plan, intervention, economic_scenario, regulation, compliance_check, outcome_tracking, administrative_unit (69 → 76 types)
- **RBAC complet** — reader/writer/admin/rgpd_manager par type, 19 tests
- **Migration progressive** — 0002-0005 selon ADR-004 (4 étapes au lieu d'un big bang)

---

## [GOUVERNANCE — VALIDATIONS RÉTROACTIVES] - 2026-07-16

### Gouvernance

- **DEC-000022** (métamodèle v6.2) : Proposé → Validated (validation rétroactive)
- **DEC-000023** (migration API v6.2) : Proposé → Validated (validation rétroactive)
- **ADR-004** (migration progressive) : Proposé → Validated (plan en 4 migrations confirmé)
- **RFC-0012** (migration API v6.2) : Proposé → Validated + amendement cohérence ADR-004
- Note : l'implémentation a précédé la validation formelle — écart assumé, CI à venir

---

## [MIGRATION API V6.2 — RFC-0012 + DEC-000023 + ADR-007] - 2026-07-16

Migration complète de l'API GSIE du schéma v6.1 (12 tables, `KnowledgeObject`)
vers le métamodèle v6.2 (73 types noyau, table racine `resource`).

### Ajouts

- **RFC-0012** — migration API v6.2 (73 types, resource racine, WebSocket, SDK)
- **ADR-007** — architecture API v6.2 (CRUD générique + modules par domaine)
- **DEC-000023** — décision de migration API v6.2
- **Table racine `resource`** (ADR-001) — class-table inheritance, 73 types, soft delete (CON-010)
- **73 modèles SQLAlchemy** groupés par domaine (12 fichiers) :
  - `provenance.py` — types 1-8 (Entity, Concept, Vocabulary, Instance, etc.)
  - `assertion.py` — types 9-13 (Assertion, Predicate, EvidenceAssessment, etc.)
  - `observation.py` — types 14-19 (Observation, Result, Method, Instrument, etc.)
  - `prov.py` — types 20-24 (Activity, ProvEntity, Agent, Source, Citation)
  - `spatial_temporal.py` — types 25-28 (Unit, Place avec PostGIS Geometry, TemporalContext, Media)
  - `temporal_engine.py` — types 29-30, 61 (Revision, Snapshot, ResourceDiff)
  - `models_ai.py` — types 31-36, 41, 50-52 (Model, Dataset, Feature, Inference, etc.)
  - `ecology.py` — types 43-49 (ScaleContext, Phenomenon, EcologicalProcess, etc.)
  - `reasoning.py` — types 53-60 (Question, Decision, Recommendation, Scenario, etc.)
  - `governance.py` — types 37-40, 42 (Rights, Access, Sensitivity, Conflict)
  - `dynamics.py` — types 59, 66-73 (EcosystemService, Flow, Goal, Constraint, etc.)
  - `fair_rgpd.py` — types 62-65 (Sample, Consent, DataSubject, PersistentIdentifier)
- **52 enums PostgreSQL** (§3.3 à §3.22 + enums supplémentaires + 7 enums audit)
- **17 tables de jonction n:m** (`junctions.py`) — ModelRun inputs/outputs, ConflictCluster assertions, Hypothesis supporting/contradicting, Decision recommendations/evidence, Recommendation assertions/scenarios, FeatureSet features, Experiment scenarios/model_runs, EcologicalState basis, Correlation variables, KnowledgeLineage derived, TerrainSession sampling/media
- **Outbox/Inbox pattern** (ADR-005) — `outbox.py` pour la cohérence événementielle
- **Object Storage abstraction** (ADR-006) — `object_storage.py` (S3/MinIO/local)
- **Registry pattern** — `@register_type` pour auto-enregistrement des 69 types resources
- **CRUD générique** — 8 endpoints `/api/v1/resources` pour les 69 types :
  - GET `/resources/types` — liste des types
  - GET `/resources` — liste paginée (filtre par type)
  - POST `/resources` — créer (Revision v1, validation dynamique, gsie_id auto)
  - GET `/resources/{id}` — détail
  - PUT `/resources/{id}` — mettre à jour (Revision + ResourceDiff, CON-010)
  - DELETE `/resources/{id}` — soft delete (Revision finale, CON-010)
  - GET `/resources/{id}/revisions` — historique des révisions (Temporal Engine)
- **Validation dynamique** — `validators.py` valide les champs obligatoires et enums par type
- **WebSocket** — `/api/v1/ws/hub` et `/api/v1/ws/events` pour le Hub (UE5.8) :
  - Auth JWT obligatoire (token en query param)
  - Rate limiting (10 messages/60s par client)
  - Validation des canaux (16 canaux autorisés)
  - Redis Pub/Sub pour fan-out inter-workers
  - Broadcast events sur create/update/delete
- **Migration Alembic 0002** — création des 73 tables + 17 jonctions + Outbox/Inbox + migration des données existantes
- **Tests** — 19 nouveaux tests (resources + WebSocket), 152 tests passent, 79 skipped (legacy v6.1)
- **Config** — paramètres WebSocket (max connections, heartbeat, allowed origins) + Object Storage (local path, S3 endpoint, bucket)

### Corrections (audit post-implémentation)

- **Soft delete au lieu de hard delete** (CON-010 respecté)
- **Revision créée dans update** (CON-010 respecté, avec ResourceDiff)
- **PostGIS Geometry** pour Place (GeoAlchemy2, SRID 2154)
- **Auth WebSocket** (token JWT en query param, close si invalide)
- **Validation dynamique** des `data` par type (champs obligatoires + enums)
- **17 tables de jonction n:m** manquantes ajoutées
- **12 types avec champs manquants** corrigés (ModelRun, DatasetVersion, ModelVersion, DataSubject, ConfidenceGraph, Goal, Constraint, KnowledgeLineage, TerrainSession, EcosystemService, ResourceDiff)
- **7 enums manquants** ajoutés (EcosystemServiceCategory, GoalPriority, ConstraintSeverity, PropagationMethod, ProductionMethod, TerrainSessionType, SyncStatus)
- **Redis Pub/Sub** pour WebSocket fan-out inter-workers
- **Outbox/Inbox** (ADR-005) pour la cohérence événementielle
- **Object Storage** (ADR-006) abstraction S3/local
- **4 fichiers de tests legacy** marqués skip (migration Vague 2)
- **gsie_id auto-généré** quand non fourni (ex. `assertion:2026:a1b2c3d4`)
- **Broadcast WebSocket** sur create/update/delete
- **Endpoint `/resources/{id}/revisions`** implémenté

### Breaking changes

- `KnowledgeObject` → `Assertion` (type 9 du métamodèle v6.2)
- `knowledge_objects` table → supprimée après migration vers `resource` + `assertion`
- Endpoints `/knowledge/*` migrés vers le CRUD générique `/resources` (Vague 2)

### Conservation

- Endpoint `/evidence/evaluate` — conservé (pas de breaking change)
- Auth JWT RS256 — conservée
- Middlewares (TraceId, CORS, rate limiting, Gzip) — conservés
- Pipeline Evidence → Knowledge devient Evidence → Assertion

---

## [MÉTAMODÈLE V6.2 — RFC-0011 + DEC-000022 + 6 ADR] - 2026-07-15

Rédaction complète du métamodèle v6.2 de l'Encyclopédie de l'Écosystème
et soumission à adoption via RFC-0011 + DEC-000022. Le métamodèle
définit un noyau universel de **73 types** en 5 niveaux, avec
PostgreSQL 16 + PostGIS comme vérité canonique. Neo4j, Elasticsearch,
Jena et GraphQL sont différés (projections régénérables, benchmark
Apache AGE en Vague 1).

La v6.2 enrichit la v6.1 (42 types) avec 18 types issus de la passe
écologique du Fondateur :
- ScaleContext (43) — multi-échelle écologique
- Phenomenon (44) + EcologicalProcess (45) — phénomènes et processus
- RelationType (46) — classification des prédicats
- SamplingEvent (47) — hiérarchie d'échantillonnage
- TraitDefinition (48) + TraitValue (49) — traits fonctionnels
- Feature (50) + FeatureSet (51) + Inference (52) — IA/ML
- Question (53) + Hypothesis (54) + Decision (55) + Recommendation (56) + Scenario (57) — raisonnement
- Correlation (58) — objet de connaissance versionné
- EcosystemService (59) — concept différé
- Capability (60) — orchestration moteurs/apps
- ResourceDiff (61) — GSIE Temporal & Provenance Engine (diff explicite entre revisions)
- Sample (62) — échantillon physique, mapping SOSA/SSN `sosa:Sample`
- Consent (63) + DataSubject (64) — conformité RGPD (art. 6 + 9.2.j)
- PersistentIdentifier (65) — FAIR F1 (DOI, PURL, ORCID, GBIF, Wikidata)
- Flow (66) — flux écologiques (carbone, eau, nutriments, énergie, graines, gènes, pathogènes)
- ConfidenceGraph (67) — graphe de confiance, propagation d'incertitude
- Goal (68) + Constraint (69) — objectifs de gestion + contraintes de faisabilité
- KnowledgeLineage (70) — DAG explicite de production de connaissance
- Experiment (71) — série de ModelRuns avec cadre de comparaison
- TerrainSession (72) — mission terrain GeoSylva (météo, GPS, martelage, inventaire)
- EcologicalState (73) — état synthétique de santé/vitalité/risque/résilience
- + 3 champs : Assertion.rule_subtype, Dataset.purpose, Scenario.scenario_subtype
- + document orchestration Knowledge OS §9.4 (à rédiger Vague 0)
- + stratification méta-architecturale (niveau 0 : Universe → MetaOntology → Ontology → MetaModel → Profiles → Applications)
- + section FAIR compliance §15.1 (audit 15 principes : 4/15 OK, cible 10/15 Vague 1, 15/15 Vague 2)
- + section RGPD §15.2 (art. 6, 7, 9.2.j, 15, 16, 17, 20, 30, 32, 35)
- + mapping SOSA/SSN §15.3 (W3C/OGC — 14 concepts mappés)
- + roadmap Vague 2 exhaustive (16 actions P1 + 20 actions P2)

**Documents créés** :
- `GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md` — livrable 213 v6.1 (654 lignes, 42 types)
- `02_RFC/RFC-0011-metamodele-encyclopedie-v6.1.md` — RFC principale (430 lignes)
- `02_RFC/annexes/annexe-302.md` à `annexe-205.md` — 7 annexes de superseding/amendement
- `03_DECISIONS/DEC-000022.md` — décision d'adoption (Proposé)
- `GSIE/ARCHITECTURE/ADR-001-racine-resource.md` — class-table inheritance, FK fortes
- `GSIE/ARCHITECTURE/ADR-002-pg-temporal.md` — GSIE Temporal & Provenance Engine (Revision + Snapshot + ResourceDiff + PROV-O)
- `GSIE/ARCHITECTURE/ADR-003-age-benchmark.md` — stratégie d'évaluation AGE vs Neo4j
- `GSIE/ARCHITECTURE/ADR-004-migration-schema.md` — migration knowledge_objects → v6.1
- `GSIE/ARCHITECTURE/ADR-005-outbox-inbox.md` — transactional outbox pattern
- `GSIE/ARCHITECTURE/ADR-006-object-storage.md` — interface MinIO/S3 pour DataAsset

**Superseding** (contenu historique conservé intact, CON-010) :
- Livrable 302 (Knowledge Method) — KnowledgeObject 6 types → Assertion + EvidenceAssessment
- Livrable 304 (Knowledge Graph Spec) — topologie Neo4j → tables PG + AGE
- Livrable 309 (Encyclopedia DB Schema) — 4 couches → PG canonique
- Livrable 310 (Engine Data Socle) — contrats moteurs KnowledgeObject → Assertion

**Amendements** :
- GSIE-DIR-0008 §2.1/§2.3/§2.4 — Neo4j/Jena/GraphQL différés
- DEC-000012 — ADR-0008/0009/0010/0011/0012/0013 → ADR-001 à ADR-006
- DEC-000019 — Vague 0 ajoutée, Vague 1 étendue (42 types)
- DEC-000020 — transition in-memory → schéma v6.1

**Annotation** : livrable 205 (Scientific Data Model, Draft) —
evidence_level → EvidenceAssessment, entités → profils v6.1.

**19 corrections intégrées** (5 P0, 8 P1, 6 P2) + 11 arbitrages
Fondateur additionnels. Statut : **Proposé** — en attente de validation
du Fondateur. Gate documentaire Vague 0 avant toute implémentation.

---

## [ARCHIVAGE PROPOSITION MÉTAMODÈLE V5] - 2026-07-15

Archivage de la proposition non adoptée de métamodèle v5 ; préparation
d'une convergence v6.1 avant RFC. Aucun choix d'architecture adopté.
Les deux documents v5 (`03_DECISIONS/DEC-000022.md` et
`GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md`) ont été retirés des
emplacements actifs et archivés intégralement dans
`22_PROJECT_MEMORY/SUPERSEDED_DRAFTS/` comme ressources historiques non
normatives. Le numéro DEC-000022 reste disponible pour une future
décision après RFC.

> **Correction (même jour)** : l'emplacement `GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md`
> n'est pas resté vide comme annoncé ci-dessus — un nouveau brouillon de travail (v6.1
> puis v6.2, non commité) y a été redéposé en parallèle pendant la préparation de
> RFC-0011. Ce brouillon porte désormais son propre avertissement de gouvernance en tête
> de fichier. RFC-0011.md et DEC-000022.md restent inexistants à ce jour ; rien n'est
> adopté.

---

## [VEILLE TECHNOLOGIQUE GSIE — 6 DOMAINES] - 2026-07-15

Rapport de veille technologique couvrant les 6 domaines GSIE (forestier,
géospatial, IA environnementale, incendies, Unreal Engine, Python
scientifique). Ajout de `GSIE/RESEARCH/VEILLE_2026-07-15.md`.

Trouvailles principales : ForestFormer3D et SelectAnyTree (segmentation
d'arbres LiDAR, candidats à évaluer pour succéder/compléter
SegmentAnyTreeV2), SAGStree et ForestSplat (Gaussian Splatting
forestier), citation JOSS officielle de ForeFire (DOI 10.21105/joss.08680,
à référencer pour Ignis), PostGIS 3.6.x (`ST_CoverageClean`,
`ST_ReclassExact`), Cesium for Unreal v2.28.0 (support UE 5.8, correctif
`UCesiumGaussianSplatSubsystem`), TorchGeo 0.9.0. Aucune connaissance
ingérée dans `GSIE/KNOWLEDGE/` — document au stade bibliographie brute,
non qualifiée A-F par l'Evidence Engine.

## [PIPELINE INTÉGRÉ EVIDENCE → KNOWLEDGE — SEMAINE 4] - 2026-07-15

### Tranche verticale prioritaire validée (DEC-000021)

Pipeline intégré chainant l'Evidence Engine et le Knowledge Engine de
bout en bout : soumission → qualification A-F → ingestion (si accepte) →
requête → révision (CON-010).

**Module `pipeline.py`** :
- `EvidenceKnowledgePipeline.process()` — traite une soumission de bout
  en bout : qualification Evidence + ingestion Knowledge si statut « accepte »
- `PipelineResult` — contient la connaissance qualifiée ET l'objet ingéré
  (si applicable), avec statut (ingested | quarantined | refused)
- `query()` et `revise()` — délèguent au Knowledge Engine
- Validation humaine (CON-001) : les connaissances quarantined/refused
  sont retournées à l'appelant, non ingérées automatiquement

**Tests d'intégration E2E** (11 tests) :
- 8 tests engine : ingest si accepte, refuse si F, quarantine si D,
  query après ingest, revise après ingest, préservation evidence_level,
  préservation source, type PipelineResult
- 3 tests API : pipeline complet via endpoints (evaluate → ingest →
  query), pipeline avec révision (evaluate → ingest → revise → query v2),
  refus d'ingestion d'une connaissance refusée

**Qualité** : 166 tests au total (155 + 11 nouveaux), Ruff + mypy --strict OK.

**Fichiers créés** :
- `GSIE/API/src/gsie_api/engines/pipeline.py` — module d'intégration
- `GSIE/API/tests/unit/test_pipeline.py` — tests E2E

**Décision** : DEC-000021 — Semaine 4 pipeline intégré.

---

## [KNOWLEDGE ENGINE — SEMAINE 3] - 2026-07-15

### Implémentation du Knowledge Engine (DEC-000020)

Moteur de base de connaissances — source unique de vérité pour tous les
moteurs de raisonnement. Conforme à KNOWLEDGE_ENGINE.md §5 (contrat d'interface)
et KNOWLEDGE_METHOD.md §2 (structure KnowledgeObject).

**Fonctionnalités** :
- **Ingestion** : reçoit les connaissances qualifiées (statut « accepte »
  depuis Evidence Engine), rejette quarantine et refuse (CON-001).
- **Requête** : 5 types (par_concept, par_relation, par_domaine,
  par_essence, par_station) avec filtres clé-valeur, filtre par niveau
  de preuve minimum, pagination.
- **Versionnement** (CON-010) : chaque révision archive l'ancienne version
  dans l'historique (VersionEntry avec justification), incrémente la
  version, aucune connaissance supprimée silencieusement.
- **Révision** : mise à jour du contenu, du niveau de preuve, de la source
  ou des domaines de validité, avec justification obligatoire.
- **Statistiques** : nombre d'objets par type.

**Endpoints API** :
- `GET  /api/v1/knowledge/status` — statut du moteur
- `GET  /api/v1/knowledge/version` — version et backend
- `POST /api/v1/knowledge/ingest` — ingère une connaissance (201)
- `POST /api/v1/knowledge/query` — interroge le graphe (200)
- `POST /api/v1/knowledge/revise` — révise une connaissance (200/404/400)
- `GET  /api/v1/knowledge/stats` — statistiques du graphe

**Qualité** :
- 33 nouveaux tests (19 unitaires + 14 API), 155 tests au total.
- Ruff + mypy --strict : zéro erreur.
- Rate limiting sur ingest (30/min) et query (60/min).
- Auth JWT obligatoire sur tous les endpoints POST/GET sensibles.

**Fichiers créés** :
- `GSIE/API/src/gsie_api/engines/knowledge/schemas.py` — schémas Pydantic
- `GSIE/API/src/gsie_api/engines/knowledge/engine.py` — implémentation
- `GSIE/API/src/gsie_api/engines/knowledge/router.py` — router FastAPI (remplace placeholder)
- `GSIE/API/tests/unit/test_knowledge.py` — tests unitaires engine
- `GSIE/API/tests/unit/test_knowledge_api.py` — tests API endpoints

**Décision** : DEC-000020 — Knowledge Engine Semaine 3.

---

## [STABILISATION QUALITE VAGUE 1] - 2026-07-14

### Passe qualité complète sur `GSIE/API` et `GSIE/ENGINES/EVIDENCE_ENGINE/rust`

- **Lint / type / tests** : Ruff, mypy `--strict` et Clippy `-D warnings` passent à zéro.
- **Tests** : 122 tests Python unitaires, 41 tests Rust et 2 tests d'intégration PostGIS/Redis passent (couverture Python 98 %).
- **CI** : `.github/workflows/ci.yml` étendue avec les jobs `python-quality` (Ruff, mypy, pytest unitaires), `python-integration` (testcontainers PostGIS/Redis), `rust-quality` (clippy, test) et `docker-build`.
- **Auth** : credentials dev (`admin/changeme`) retirés du code ; `auth_dev_username` et `auth_dev_password` sont désormais configurables via variables d'environnement. Dev login désactivé en production.
- **Evidence** : détection de conflits/versionnement protégée par le feature flag `evidence_experimental_conflicts_enabled` (désactivé par défaut, à valider scientifiquement avant activation).
- **Docker** : build multi-stage mis à jour pour compiler le moteur Rust via Maturin et installer le wheel `gsie_evidence` dans l'image API.
- **Dépendances** : suppression de `types-redis` (obsolète et conflictuel avec Redis 5.x+ qui embarque ses propres stubs).
- Fichiers modifiés : `GSIE/API/src/gsie_api/**/*.py`, `GSIE/API/src/gsie_api/engines/evidence/wrapper.py`, `GSIE/API/tests/**/*.py`, `GSIE/API/pyproject.toml`, `GSIE/API/.env.example`, `GSIE/API/Dockerfile`, `GSIE/ENGINES/EVIDENCE_ENGINE/rust/src/engine.rs`, `.github/workflows/ci.yml`.

## [NETTOYAGE GOUVERNANCE DOCUMENTAIRE] - 2026-07-14

### Correction d'incohérences résiduelles entre l'état réel du projet (Phase 4 active) et sa mémoire documentaire

Aucun changement de statut de livrable, de décision ou de phase — correction
de faits obsolètes dans `PROJECT_MEMORY.md` et `ROADMAP.md`, repérés lors
d'une tâche précédente mais non corrigés à l'époque (hors périmètre).

- `PROJECT_MEMORY.md`, section « Prochaine étape » : décrivait encore la
  Phase 3 comme passée en `Review` en attente de validation, alors que la
  Phase 3 est clôturée (DEC-000017) et que la Phase 4 est active depuis le
  2026-07-13 (DEC-000017 / GSIE-DIR-0011). Remplacée par un état factuel de
  la Phase 4 : Vague 1 (Fondations, DEC-000019) — semaines 1 et 2 livrées
  (FastAPI + Docker Compose, Evidence Engine cœur Rust + bindings PyO3,
  couverture de tests 100 %, durcissement sécurité), semaine 3 (Knowledge
  Engine) à venir ; état du chantier Hub (Centre de Commandement GSIE,
  environnement UE 5.8 configuré, projet réel hors dépôt sur
  `E:\GSIE-Centre-Commandement` et dépôt GitHub `NeooeN45/Hub`).
- `ROADMAP.md` : deux faits périmés corrigés — (1) la note d'audit
  2026-07-06 sur « 3 moteurs dédiés / 11 READMEs de cadrage » ne reflétait
  plus la réalité depuis le livrable 207 (Phase 2, les 14 moteurs ont
  chacun un fichier d'architecture dédié) et l'enrichissement du
  2026-07-13 (section « État de l'art » ajoutée aux 14 fichiers) ; note
  annotée « statut dépassé » avec mise à jour, sans supprimer l'historique.
  (2) le livrable 211 référençait encore l'ancien nom de fichier
  `GSIE_IGNIS_GCS_CINEMA_UNREAL.md`, renommé `COMMAND_CENTER_UNREAL.md`
  lors de l'élargissement du livrable au Centre de Commandement GSIE
  (GSIE-DIR-0009). En outre, la note de clôture de la section Phase 3
  (« la Phase 3 peut passer en Review ») était incohérente avec l'en-tête
  de la même section (« clôturée ✅ ») et le reste du document ; corrigée
  pour refléter la clôture effective par DEC-000017.

Mémoire synchronisée : `PROJECT_MEMORY.md`, `ROADMAP.md`.

---

## [CONFIGURATION CENTRE DE COMMANDEMENT UE5.8] - 2026-07-13

### Installation et configuration du poste de pilotage immersif (livrable 211)

Configuration complète de l'environnement Unreal Engine 5.8 pour le Centre
de Commandement GSIE, sur disque `E:\GSIE-Centre-Commandement` (anciennement
`E:\Quintessences unréal ungin`, renommé). Conforme à DEC-000010 (adoption
UE 5.8 + Cesium) et au livrable 211 (`COMMAND_CENTER_UNREAL.md`).

**Composants installés et configurés :**
- Unreal Engine 5.8.0 (changelist 55116800) — moteur
- Cesium for Unreal v2.28.0 (EngineVersion 5.8.0) — globe 3D géoréférencé,
  installé dans `Engine/Plugins/Marketplace/CesiumForUnreal/`
- Unreal MCP v2.2.0 (GenOrca, EngineVersion 5.8.0) — pilotage IA de l'éditeur
  via MCP (Claude Code, Cursor), 253 actions, précompilé UE 5.8
- Twinmotion 2026.1 — installé
- RealityScan 2.2 — photogrammétrie, installé

**Plugins natifs UE5.8 vérifiés présents :**
- GeoReferencing (avec PROJ/vcpkg — projections EPSG)
- Niagara (effets feu/eau/fumée)
- ScriptPlugin/PythonScriptPlugin (requis par Unreal MCP)

**Plugins source clonés (Plugins-Sources/) :**
- UE-GeoViewer (Will747) — overlay maps Google/Bing, import terrain HGT SRTM
- LandscapeGen (TensorWorks) — veille (EngineVersion 4.25, incompatible 5.8 sans refonte)

**Configuration système :**
- Registre Windows : `HKCU\...\Unreal Engine\Builds\UE_5.8` enregistré
- 8 variables d'environnement utilisateur (UE_ENGINE_PATH, GSIE_UE_ROOT, etc.)
- 3 raccourcis bureau (UE5.8 Editor, Twinmotion, RealityScan)
- Scripts utilitaires (Tools/) : verify-install, launch-ue, launch-twinmotion,
  launch-realityscan, clean-cache
- Config Cesium ion template (Tools/cesium-ion-config.json) — coordonnées
  Landiras (zone de test Ignis, 44.4764°N, -0.4236°E)

**Plugins à installer via Fab (marketplace Epic) — manuel :**
- BlueprintWebSocket (Pandoa) — gratuit, WebSocket pour Blueprints
- FluidFlux (ImaginaryBlend) — $349.99, simulation eau shallow-water (app Hydro)

Mémoire synchronisée : `PROJECT_MEMORY.md`.

---

## [ÉTAT DE L'ART SOURCÉ — 14 MOTEURS + CENTRE DE COMMANDEMENT] - 2026-07-13

### Enrichissement documentaire par recherche sourcée multi-agents

Aucun changement de phase, de statut de livrable ou de décision
structurante. Enrichissement de contenu à l'intérieur de documents
existants, tous restés en `Draft` — des pistes de recherche pour la
Phase 4, pas des choix d'implémentation arrêtés. Toutes les sources
vérifiées par recherche web avant intégration (GSIE-CON-002, GSIE-CON-005).

- Les **14 fichiers de moteurs** (`GSIE/ENGINES/*/*_ENGINE.md` —
  EVIDENCE, KNOWLEDGE, CORRELATION, REASONING, DIAGNOSTIC,
  RECOMMENDATION, VALIDATION, GIS, CLIMATE, PEDOLOGY, BOTANICAL,
  FOREST_DYNAMICS, LEARNING, SIMULATION) reçoivent chacun une nouvelle
  section **« État de l'art et pistes de recherche sourcées »** (§8, ou
  avant « Références » pour `SIMULATION_ENGINE.md`) : technologies,
  algorithmes, bibliothèques et bases de données concrets, précédents
  scientifiques (articles peer-reviewed, standards W3C/OGC, plateformes
  open source), tableau de synthèse + sous-section « Sources ». Aucun
  contrat d'interface ni aucune garantie déjà documentée n'est modifié.
- Renvois croisés ajoutés entre moteurs partageant une même piste
  technique : CAPSIS (Forest Dynamics ↔ Simulation), NED-2/EMDS
  (Reasoning ↔ Recommendation), forêts aléatoires/Random Forest
  (Correlation ↔ Diagnostic), PROV-O (Knowledge ↔ Recommendation ↔
  Validation).
- Deux corrections mineures suite à relecture critique croisée : URL
  FAO-56 corrigée (`CLIMATE_ENGINE.md`), mention de LIME complétée
  (`VALIDATION_ENGINE.md`).
- `GSIE/ARCHITECTURE/COMMAND_CENTER_UNREAL.md` (livrable 211, Centre de
  Commandement GSIE, Unreal Engine 5.8) passe de **v2.1.0 à v2.2.0** :
  nouvelle section 9 « Compléments de recherche (mise à jour) » —
  détail des fonctionnalités UE5.8 (Mesh Terrain, MegaLights, Movie
  Render Graph, Live Link Hub), mises à jour Cesium for Unreal / Cesium
  ion postérieures à avril 2026 (v2.28.0, tilers NetCDF/GeoJSON),
  précédents de convergence multi-domaines hors incendie (NVIDIA
  Omniverse/OpenUSD, ArcGIS Urban, service « Jumeau numérique » de
  l'IGN — précédent institutionnel français, `ign.fr/offre`), mise à
  jour de maturité du plugin **Unreal MCP** (désormais nommé et
  documenté officiellement par Epic, statut expérimental confirmé), et
  deux publications académiques 2026 (jumeau numérique hydraulique en
  Unreal Engine, pertinent pour l'app Hydro ; convergence SIG/moteur de
  jeu urbain).

Mémoire synchronisée : `PROJECT_MEMORY.md`.

## [VALIDATION ARCHITECTURE PHASE 4] - 2026-07-13

### Validation par 3 subagents de recherche (DEC-000019)

Analyse approfondie de l'architecture Phase 4 par 3 subagents en
parallèle (sources web 2025-2026) :

- **Multi-langage validé** : Python + Rust (pyo3) + Go différé
  (MAVSDK-Go est PoC en 2026, MAVSDK-Python est production). PyO3
  mature (Polars, Pydantic v2, Ruff — gains 7.4x). Pièges : GIL
  (`py.allow_threads()`), FFI overhead (profiler avant)
- **Architecture API validée** : FastAPI + asyncpg + PostGIS + Redis
  + OpenTelemetry. 5 ajustements P0/P1 : bypass PgBouncer pour
  LISTEN/NOTIFY, `statement_cache_size=0`, pygeoapi comme lib
  Starlette, modules par moteur (pas DDD pur), fastgeoapi P1
- **Plan refondu** : 8 semaines → 24 semaines (6 vagues). Respect
  strict du graphe de dépendances (livrable 204). Knowledge Engine
  ajouté (dépendance critique sautée). 2 semaines/moteur Rust
  (réaliste solo). ForeFire repositionné après Climate Engine

Livrables produits :
- `GSIE/RESEARCH/PHASE4_ARCHITECTURE_VALIDATION.md` (318 lignes)
- `GSIE/RESEARCH/API_TECHNOLOGY_RESEARCH.md` (1092 lignes, 30 recos)
- `03_DECISIONS/DEC-000019.md` (141 lignes)

## [STRATÉGIE IA IGN + GEOCONTEXT MCP] - 2026-07-13

### Découverte et capitalisation de la stratégie IA IGN (DEC-000018)

Analyse de la feuille de route IA IGN 2022-2024, de la page vigie IA et
du dépôt `ignfab/geocontext`. 4 livrables produits :

- **`GSIE/RESEARCH/IGN_IA_STRATEGY.md`** (292 lignes) : feuille de route
  IA IGN (6 axes, 3 objectifs), produits (CoSIA 20cm, OCS GE, GéoLLM,
  cartes Anthropocène), consortium AI4GEO, IGNfab, 8 recommandations
- **`.devin/config.json`** : MCP geocontext configuré (instance HTTP
  `https://geollm.beta.ign.fr/geocontext/mcp`). 10 outils : geocode,
  altitude, adminexpress, cadastre, urbanisme, assiette_sup,
  gpf_search_types, gpf_describe_type, gpf_count_features,
  gpf_get_features
- **`DATASET_CATALOG.md`** : 3 nouveaux datasets (DS-027 CoSIA, DS-028
  OCS GE, DS-029 Datasets apprentissage LiDAR HD). Total : 29 datasets
- **`HUB_AND_APPS_PLAN.md`** §11 : interopérabilité IGN geocontext MCP
  documentée pour les specs (HUB-001, HUB-003, IGNIS-001, GEO-001,
  GIS Engine)
- **`DEC-000018`** : décision tracée (3 actes, 8 recommandations)

Alignement thématique IGN ↔ GSIE : forêts (Forest Dynamics), érosion
(GIS/Simulation), cours d'eau (Hydro), artificialisation (GIS),
biodiversité (Botanical). geocontext = première brique d'interopérabilité
avec la Géoplateforme.

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

### Fiche recherche LiDAR HD IGN — analyse complète des 4 PDFs officiels

Sources : `DC_LiDAR_HD_1-0.pdf` (46p, descriptif de contenu v1.0 juillet 2026),
`SE_LiDAR_HD.pdf` (suivi des évolutions), `Offre_Produit_LiDAR_2025-08.pdf`
(accès aux produits), `Traitements_Produits_LiDAR_2025-08.pdf` (traitements).

- `GSIE/RESEARCH/LIDAR_HD_SPECIFICATIONS.md` enrichie (236 → 461 lignes) :
  - 11 classes avec codes ASPRS précis (1,2,3,4,5,6,9,17,64,66,67) et définitions IGN complètes
  - 13 attributs standards + 3 Extra Bytes (DTM_Marker, DSM_Marker, Origin)
  - Qualité géométrique : REMQ plani 11,7cm (exigence 50cm), REMQ alti 5,5cm (exigence 10cm)
  - Accès : COPC.LAZ, EPT/VPC (streaming), WMS-Raster (MNT/MNS/MNH + ombrages), API altimétrique
  - Traitements : calendrier diffusion (juin 2026), améliorations version finale
  - Points d'attention : déficit points sur eau, vég < 20cm = sol, vergers inclus, divers bâtis incertain
  - Classe 64 (sursol pérenne) = lignes électriques → détection risque incendie (Ignis)
  - 15 recommandations Phase 4 priorisées (P0/P1/P2)
- `DATASET_CATALOG.md` DS-002 enrichi : codes précis, attributs, accès, qualité

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

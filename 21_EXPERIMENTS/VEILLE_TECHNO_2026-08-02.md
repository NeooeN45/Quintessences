# Veille technologique exhaustive — GSIE/Quintessences

| Champ | Valeur |
|---|---|
| **Date** | 2026-08-02 |
| **Méthode** | 8 sous-agents de recherche en parallèle (DB, Moteurs AI/ML, API FastAPI, Géospatial, Observabilité/Sécurité, Concurrence, Infrastructure, Data pipelines) |
| **Statut** | Draft — synthèse exploratoire, **pas une feuille de route** |
| **Niveau de preuve** | **C (sourcé)** — chiffres vérifiés par 2 sous-agents de recherche web (2026-08-02). Sources citées inline. Les chiffres marketing d'éditeur sont marqués comme tels. Voir §14 « Sources » pour la liste complète. |
| **Correction 2026-08-02 (post-revue)** | 5 écarts avec l'état réel du dépôt corrigés (§4, §6, §7, §9, §11). Voir §13 « Errata » pour le détail. Chiffres sourcés via 2 sous-agents de recherche web. Voir §14 « Sources ». |

---

## 1. Position concurrentielle

GSIE occupe un positionnement unique qu'aucun concurrent n'offre :

- **14 moteurs intégrés** : pipeline complet Evidence → Knowledge → Correlation → Reasoning → Diagnostic → Recommendation → Validation. Aucun concurrent n'a cette chaîne.
- **Multi-domaines** : Forêt + Faune + Incendies + Eau + Végétation dans une seule plateforme.
- **Multi-applications** : GeoSylva (Android), Artemis, Ignis, Hydro, Flora, QGISIA.
- **Prescriptif, pas descriptif** : IGN/ONF/GFW décrivent l'état. GSIE recommande des actions.

### Concurrents directs identifiés

| Acteur | Pays | Domaine | Type |
|---|---|---|---|
| IGN BD Forêt v3 | France | Cartographie essences IA | Institutionnel |
| ONF Forêt 4.0 | France | Transformation numérique | Institutionnel |
| CNPF (La Forêt Bouge, BioClimSol) | France | Propriétaires privés | Institutionnel |
| Sylv'Eclair (INRAE/CNPF) | France | Décision sylvicole Pin maritime | Recherche |
| Sylvamap | France | Gestion forestière SaaS | Startup |
| Arboreal | Suède | Mesures AR smartphone | Startup |
| Dryad Networks | Allemagne | Capteurs incendie LoRaWAN | Startup |
| Pivotal Earth | UK | Biodiversité TNFD | Startup |
| 20tree.ai / Overstory | Pays-Bas | Forest intelligence satellite | Startup |
| Sylvera | UK | Ratings crédits carbone | Startup |
| SilviaTerra | USA | Inventaire satellite IA | Startup |
| CTrees | Global | Carbone 1-hectare | Non-profit |
| Treevia | Brésil | Inventaire IoT | Startup |
| Pachama (racheté Carbon Direct) | USA | MRV carbone IA | Startup |
| Forest Source | USA | Traçabilité EUDR | Startup |
| PlantNet | France | Identification 77k espèces | Recherche |
| Global Forest Watch (WRI) | Global | Monitoring déforestation | Institutionnel |
| EFFIS | EU | Feux forêts Europe/MENA | Institutionnel |
| FAO FRA | Global | Évaluation globale | Institutionnel |

### Stratégie recommandée

**Partenariats intégratifs**, pas compétition. GSIE comme plateforme centrale intégrant données IGN/CTrees/GFW + technologies Arboreal/Dryad/INRAE-CAPSIS.

---

## 2. Améliorations DB PostgreSQL/PostGIS

### Quick wins (Phase 1-2)

| Extension | Bénéfice | Complexité | Statut dépôt |
|---|---|---|---|
| **pg_stat_statements** | Monitoring requêtes lentes | Faible | **DÉJÀ ACTIVÉ** |
| **pg_cron** | Jobs planifiés intégrés (refresh MV, cleanup) | Faible | **À faire** |
| **pgvector** | Recherche sémantique | Faible | **DÉJÀ ACTIVÉ** (migration `20260731_0024`) |
| **pg_trgm** | Recherche floue noms essences/parcelles | Faible | **À faire** |
| **HypoPG** | Test index sans création (dev tuning) | Faible | **À faire** (extension optionnelle) |
| **Index partiels** | Index ciblés `WHERE status='active'` — plus compacts | Faible | **À évaluer** |
| **BRIN indexes** | Jusqu'à 99% plus compacts que B-tree pour tables append-only avec haute corrélation physique ([cas réel](https://postgresdba.hashnode.dev/postgresql-brin-indexes-when-how-to-use-block-range-indexes)) | Faible | **À évaluer** |

### Moyen terme (Phase 3-4)

| Extension/Pattern | Bénéfice |
|---|---|
| **pg_partman** | Partitionnement automatique `revisions` par date |
| **BRIN indexes** | Index 99% plus compacts pour tables temporelles append-only |
| **Materialized views CONCURRENTLY** | Agrégations précalculées sans lock |
| **TimescaleDB** | Hypertables pour observations climatiques massives |
| **postgis_topology** | Validation topologique parcelles (gaps/overlaps) |
| **Logical replication** | Read replicas pour analytics |

### Stratégique (Phase 5+)

- **Apache AGE** — graph queries pour chaînes d'inférence (Cypher + SQL)
- **DuckDB Spatial** — analytics embedded complémentaire
- **ClickHouse** — analytics temps réel IoT si capteurs massifs

---

## 3. Améliorations moteurs AI/ML

### Reasoning Engine

- **vLLM** + **Phi-4-reasoning** (14B, MIT license) — vLLM 793 tok/s vs Ollama 41 tok/s (benchmark Red Hat, 256 utilisateurs concurrents, [source](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking)). Phi-4-reasoning-plus compétitif avec o1-mini sur AIME 25 (75.3 vs 63.6) et GPQA-D (65.8 vs 54.8) ([paper](https://arxiv.org/pdf/2504.21318), [HF](https://huggingface.co/microsoft/Phi-4-reasoning))
- **LangChain + LangGraph** pour orchestration multi-étapes stateful
- **LlamaIndex** pour RAG sur documentation forestière

### Evidence/Botanical Engine

- **API PlantNet** — 78 810 espèces identifiables ([my.plantnet.org](https://my.plantnet.org/))
- **PlantCLEF dataset** — 7 806 espèces, 1.4M images ([LifeCLEF 2024](https://www.imageclef.org/PlantCLEF2024), [paper](https://doi.org/10.1007/978-3-031-56072-9_3))
- **SAM2** pour segmentation arbres imagerie aérienne (zero-shot, [Meta AI](https://ai.meta.com/research/sam2/), [paper](https://arxiv.org/html/2408.00714v2))
- **DINOv2** comme backbone — F1 0.52 → 0.87 sur segmentation agricole multi-espèces (vs DeepLabV3, in-distribution, [paper](https://arxiv.org/html/2508.07514v2))

### Diagnostic Engine

- **YOLO-PTHD** — détection déclin pin par UAV (Sirex noctilio, mAP 0.923, F1 0.866, [paper](https://doi.org/10.3390/insects16080829))
- **MBA-Former** — pine wilt disease, mIoU 81.74% sur imagerie Gaofen-2 ([paper](https://doi.org/10.3390/f17050517))
- **RECONFORT** (CESBIO) — détection dépérissement chêne par Sentinel-2 + Random Forest

### Climate Engine

- **NeuralProphet** (successeur Prophet, PyTorch) — +55-92% accuracy sur short/medium-term forecasts vs Prophet ([paper](https://arxiv.org/pdf/2111.15397), Triebe et al. 2021)
- **Darts** — large collection de modèles (statistiques, ML, deep learning, [docs](https://unit8co.github.io/darts/))
- **Chronos-2** (Amazon, 120M params, zero-shot, 300+ forecasts/sec sur A10G, [HF](https://huggingface.co/amazon/chronos-2), [paper](https://arxiv.org/pdf/2510.15821))
- **ERA5** (Copernicus, 1940-présent, 31km, horaire, [CDS](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-complete)) pour données historiques long-terme
- **Xarray + Dask** pour grilles climatiques > RAM

### Correlation Engine

- **pingouin** (effect sizes, Bayes Factor, output riche) + **statsmodels** (GLM, ARIMA)
- **DoWhy** (Microsoft) — causal inference, refutation API
- **CausalNex** (McKinsey) — Bayesian Networks, structure learning

### Simulation Engine

- **CAPSIS** (CIRAD) — 25+ modèles dans le package ONF, ~80 modèles au total sur la plateforme ([capsis.cirad.fr](https://capsis.cirad.fr/))
- **SILVA** (TU Munich, pas INRAE) — single tree position-dependent, 155k+ observations (1952-1998, 5 espèces, [paper](https://webarchiv.it.ls.tum.de/waldwachstum.wzw.tum.de/fileadmin/publications/535.pdf))
- **ML emulators** (PREBASSO) — RNN/Transformer, bias ±2% sur 25 ans

### Learning Engine

- **QLoRA** — fine-tuning 7B sous 6GB VRAM (LoRA standard nécessite 15-28GB, [paper](https://arxiv.org/pdf/2305.14314), Dettmers et al. 2023)
- **GPTQ/AWQ** — quantization 4-bit, accuracy loss généralement <4% sur benchmarks standards (peut être plus élevé sur long-context, [GPTQ](https://arxiv.org/pdf/2210.17323), [AWQ](https://arxiv.org/html/2306.00978))
- **ONNX Runtime** — portabilité CPU/GPU/NPU

### Pedology Engine

- **SoilGrids 250m** (ISRIC) — pH, SOC, texture (sand/silt/clay), 6 profondeurs (0-5, 5-15, 15-30, 30-60, 60-100, 100-200 cm, [docs](https://docs.isric.org/globaldata/soilgrids/index.html))
- **INRAE BDETM** — 73.5k analyses éléments traces métalliques
- **INRAE DoneSol** — profils/horizons sols France

---

## 4. Améliorations API FastAPI

### Performance (Phase 1 — immédiat)

| Amélioration | Gain | Complexité | Statut dépôt |
|---|---|---|---|
| **orjson** | Sérialisation JSON plus rapide (chiffre non sourcé — voir avertissement) | 1 ligne | **À faire** |
| **uvloop** (Linux) | Throughput I/O (chiffre non sourcé) | 1 flag | **À faire** |
| **Connection pooling asyncpg** | Évite épuisement connexions | Config | **Déjà configuré** (`config.py:184`, `database.py`) |
| **Gunicorn graceful reload** | Zero-downtime deploys | Config | **Déjà en place** (`gunicorn.conf.py`) |

### Patterns (Phase 2)

- **API versioning URL path** (`/api/v1/`) — **déjà en place** depuis l'origine (`config.py:140`, `app.py:327`). Action périmée.
- **Cursor-based pagination** — performance O(1) vs OFFSET. **À faire** (endpoints list utilisent OFFSET actuellement).
- **SSE** pour notifications/dashboards (plus simple que WebSocket pour unidirectionnel). **À faire**.
- **Response streaming** pour exports géospatiaux volumineux. **À faire**.
- **Backpressure** avec `asyncio.Semaphore`. **À faire**.

### Testing (Phase 2)

- **Schemathesis** — property-based testing depuis OpenAPI. **À faire**.
- **k6** — load testing (30 000-40 000 VU par instance selon hardware, [benchmarks](https://github.com/grafana/k6-benchmarks)). **À faire**.
- **Hypothesis** — property-based testing fonctions critiques. **À faire**.

### Sécurité (Phase 1-2)

- **OWASP API Top 10 2023** — audit BOLA, SSRF, mass assignment. **Audit à faire**.
- **Trivy** dans CI — scan vulnérabilités conteneurs. **À faire** (aucun `.github/dependabot.yml`, aucune étape SAST dans le workflow).
- **Bandit** pre-commit + CI — SAST Python. **À faire**.
- **Sliding window rate limiting** (Redis + Lua) — précision vs fixed window. **À évaluer** (slowapi en place, algorithme actuel non audité).
- **DPoP** (RFC 9449) — sender-constrained tokens (Phase 4). **À faire**.
- **Security headers** — **DÉJÀ IMPLÉMENTÉS** dans `middleware.py:25-33` (`_SECURITY_HEADERS` dict, appliqué par `TraceIdMiddleware:134`). X-Content-Type-Options, X-Frame-Options, HSTS, Referrer-Policy, Permissions-Policy, CSP, Cache-Control tous présents. **Note** : HSTS est actuellement émis inconditionnellement (pas seulement en HTTPS/prod) — à corriger si besoin.

### Standards (Phase 3)

- **OGC API Features** (remplace WFS) — REST + OpenAPI + GeoJSON
- **OGC API Tiles** — tuiles vectorielles via `pg_tileserv`
- **STAC** — catalogage données spatio-temporelles satellites

---

## 5. Améliorations géospatiales

### Données (Phase 2)

- **BD Forêt v3** (IGN) — 0.5ha, 35 essences, production par IA, couverture Hexagone en 1 an ([IGN](https://cartes.gouv.fr/aide/fr/partenaires/ign/referentiels-description-territoire/foret/bd-foret-v3/))
- **Sentinel-2** (Copernicus) — NDVI, santé forestière, 4 bandes à 10m, revisite 5j (constellation 2 satellites), gratuit ([Copernicus](https://sentinels.copernicus.eu/))
- **SoilGrids 250m** — propriétés sol globales (voir §3 Pedology)
- **STAC** — organisation données satellites/drone

### Traitement (Phase 2-3)

- **GeoPandas 1.0** — PyOGrio (I/O par défaut), Shapely 2, GeoParquet 1.1 ([release](https://github.com/geopandas/geopandas/releases/tag/v1.0.0))
- **DuckDB Spatial** — fonctions ST_ compatibles PostGIS (ensemble complet en cours de développement, [docs](https://duckdb.org/docs/current/core_extensions/spatial/functions))
- **Xarray-Spatial** — 150+ fonctions raster sans GDAL, NDVI, indices forestiers
- **pg_tileserv** — tuiles vectorielles depuis PostGIS
- **TiTiler** — mosaïques dynamiques depuis COGs

### Visualisation 3D (Phase 3-4)

- **CesiumJS** (Apache 2.0, gratuit) + pg_tileserv
- **3D Tiles 1.1** (OGC) — standard pour streaming 3D geospatial
- **IGN LiDAR HD** (2021-2026) — 10 pts/m², MNT/MNS/MNH, France métropolitaine + DROM ([data.gouv.fr](https://www.data.gouv.fr/en/datasets/lidar-hd/))

### ML géospatial (Phase 3-4)

- **EuroSAT** (27k images Sentinel-2, 10 classes LULC, 13 bandes spectrales) — transfer learning ([paper](https://doi.org/10.1109/jstars.2019.2918242))
- **Détection dépérissement** (RECONFORT) — Random Forest + indices CRswir/CRre
- **Prédiction biomasse LiDAR** — modèles hiérarchiques, Random Forest vs NLME

---

## 6. Améliorations observabilité/sécurité

### Observabilité (Phase 2)

| Signal | Stack recommandée | Statut dépôt |
|---|---|---|
| **Traces** | OpenTelemetry (déjà instrumenté) → Grafana Tempo ou Jaeger | OTEL déjà en place (`app.py:179-213`) |
| **Metrics** | VictoriaMetrics (16x plus rapide en query latency médiane, 2.5x moins d'espace disque vs Prometheus, [benchmark éditeur](https://new.victoriametrics.com/blog/reducing-costs-p1/)) ou Prometheus | Prometheus déjà en place (`app.py:248`) |
| **Logs** | Grafana Loki (index labels only, ~75-80% moins cher qu'ES, [comparaison](https://lucaberton.com/blog/loki-vs-elasticsearch-2026/)) ou Azure Log Analytics | structlog en place, pas d'agrégation |
| **Profiling** | Pyroscope (continu) ou py-spy (ponctuel) | **À faire** |

Alternative tout-en-un : **OpenObserve** (Rust, 87x moins cher qu'ES selon benchmark éditeur 1.1TB, [source](https://openobserve.ai/blog/elasticsearch-openobserve-benchmarking/)). Chiffre marketing éditeur : « jusqu'à 140x ».

### Sécurité (Phase 1-2)

- **Trivy** + **Bandit** + **Dependabot** — immédiat dans CI. **À faire** (confirmé : aucun fichier dependabot, aucune étape SAST).
- **ZAP + Nuclei** — DAST dans CI (Phase 2). **À faire**.
- **Semgrep** — SAST multi-lang avec taint tracking (Phase 2). **À faire**.
- **Hypothesis** — fuzzing/property-based testing (Phase 2). **À faire**.
- **Audit logging immutable** — hash chain + triggers PostgreSQL (Phase 2, RGPD). **À faire**.
- **SOPS** (Mozilla) — secrets chiffrés per-field dans Git (Phase 2). **À faire**.
- **Azure Key Vault** en production — **transition** depuis Fernet local (commité 97e269d, `core/config.py` `_DecryptedEnvSource`). Fernet reste en local/dev, Key Vault en production Azure. Ce n'est pas un remplacement mais un déploiement production du même principe. **À faire**.

### Résilience (Phase 2)

- **Tenacity** — retries robustes. **À faire**.
- **Purgatory** — circuit breaker async avec stockage Redis distribué. **À faire**.
- **asyncio.Semaphore** — bulkhead pattern. **À faire**.
- **Health checks** — **DÉJÀ IMPLÉMENTÉS**. Routes réelles : `/health` (liveness, `health.py:73`) et `/ready` (readiness, `health.py:89`), pas `/health/live` + `/health/ready` comme écrit initialement. Séparation liveness/readiness avec cache Redis 5s sur `/ready`.

### Auth (Phase 3-4)

- **Keycloak** ou **Authentik** — IAM centralisé si SAML/LDAP/SSO enterprise
- **SuperTokens** — self-hosted, open-source, alternative à Auth0
- **Passkeys/WebAuthn** — auth sans mot de passe, phishing-resistant (Phase 4+)

---

## 7. Améliorations infrastructure/DevOps

### Containerisation (Phase 1)

- **Docker multi-stage** + **Debian slim** (déjà en place)
- **BuildKit** — builds parallèles, cache registry
- **Trivy** — scan vulnérabilités + secrets + IaC

### CI/CD (Phase 1-2)

- **GitHub Actions** (garder) — reusable workflows, composite actions
- **Cache uv + Docker** avec `setup-uv` + `actions/cache`
- **Matrix builds** Python 3.11/3.12/3.13
- **Preview environments** — PullPreview ou Prvue (URL par PR)

### Azure (Phase 1-2)

| Service | Usage | Coût/mois (estimation grossière) |
|---|---|---|
| **Container Apps** | API FastAPI, scale-to-zero | À valider avec Azure Pricing Calculator |
| **PostgreSQL Flexible Server** | DB prod + PostGIS + pgvector | À valider |
| **Azure Managed Redis** | Cache, rate limiting, JWT (remplace Cache for Redis en retraite) | À valider |
| **Key Vault** | Secrets (transition depuis Fernet local) | À valider |
| **Blob Storage** | GeoJSON, GeoTIFF | À valider |
| **Monitor + App Insights** | Observabilité (OTEL déjà intégré) | À valider |

**Note** : l'estimation initiale « ~$230-500/mois » est une impression d'agent non sourcée. Les coûts Azure dépendent de la région, du tier, des crédits Azure for Startups applicables. À recalculer avec Azure Pricing Calculator avant toute décision budgétaire.

### DB operations (Phase 2)

- **Expand-contract pattern** — migrations schema zero-downtime. **À faire**.
- **pgBackRest** — backups incrémentaux, PITR, compression zstd. **À faire** (P0-1 dans ROADMAP).
- **PgBouncer** — transaction pooling. **Config présent mais non déployé** : `docker/pgbouncer.ini` + `config.py:186` (`db_pgbouncer_mode: bool = False`) existent, mais service orphelin (audit P2-6 « configuré mais non déployé »). Activation requiert ADR + bascule `db_pgbouncer_mode=True` + pointage `GSIE_DATABASE_URL` vers port 6432.
- **PostgreSQL tuning** — `shared_buffers=25% RAM`, `random_page_cost=1.1` (SSD). **À faire**.
- **pg_stat_statements** — **DÉJÀ ACTIVÉ** : `docker-compose.yml:36` (`shared_preload_libraries=age,pg_stat_statements,pgaudit`), `docker/init/01-pg-stat-statements.sql` (`CREATE EXTENSION`), `postgres-queries.yaml` (queries exporter configuré). Action périmée.
- **pgAudit** — **DÉJÀ ACTIVÉ** : `docker-compose.yml:42` (`pgaudit.log=ddl,write,role`), `docker/init/02-pgaudit.sql`.

### Monitoring (Phase 2)

- **Uptime Kuma** — uptime monitoring self-hosted (quasi-gratuit)
- **k6** — load testing dans CI
- **py-spy** — profiling production sans restart
- **pg_stat_statements** — top queries lentes

### IaC (Phase 2-3)

- **Terraform** (multi-cloud) ou **Bicep** (Azure-native) avec Azure Verified Modules

### Coût (Phase 2+)

- **Reserved Instances** — économies par engagement 1-3 ans (chiffres exacts à valider avec Azure Pricing)
- **Spot VMs** — batch jobs (traitement GeoTIFF, ETL, ML training) à coût réduit
- **Azure Cost Management** — alertes budget, right-sizing

---

## 8. Améliorations data pipelines/science

### Orchestration (Phase 2)

- **Prefect 3.x** — Python natif, décorateurs `@flow`/`@task` (10x plus rapide que Prefect 2 selon benchmark éditeur, jusqu'à 98% réduction d'overhead, [blog](https://www.prefect.io/blog/prefect-3-generally-available-september-3))
- **DVC** — versioning datasets Météo-France, GBIF, SoilGrids avec Git
- **MLflow** — tracking expériences Learning Engine

### Analytics (Phase 2-3)

- **Polars 1.x** — 3-11x plus rapide que pandas selon l'opération (group-by/joins ~10x, Parquet read ~5x, filter ~11x, string ~1.3x, [benchmark](https://www.danilchenko.dev/posts/polars-vs-pandas/))
- **DuckDB** — SQL analytics embedded, interroge Parquet/JSON/S3 directement

### ML lifecycle (Phase 3-4)

- **Feast** — feature store (features climatiques/sol/forestières réutilisables)
- **BentoML** — model serving REST API
- **Metaflow** — pipelines ML distribués (Python-first)

### Time series (Phase 3-4)

- **NeuralProphet** — prévisions météo/croissance (Phase 3)
- **Darts** — framework forecasting polyvalent (Phase 3)
- **Chronos-2 / Lag-Llama** — foundation models zero-shot (Phase 4)

### Causal inference (Phase 4)

- **DoWhy** — passer de corrélation à causalité dans les diagnostics

---

## 9. Top 20 actions prioritaires

### Phase 1 — Immédiat (1-2 mois)

| # | Action | Domaine | Effort | Statut réel |
|---|---|---|---|---|
| 1 | **orjson** pour sérialisation JSON | API | 1 ligne | **À faire** |
| 2 | **uvloop** sur Linux | API | 1 flag | **À faire** |
| 3 | **Trivy** dans CI | Sécurité | 1 step GH Actions | **À faire** |
| 4 | **Bandit** pre-commit + **Dependabot** | Sécurité | Config | **À faire** |
| 5 | ~~pg_stat_statements~~ | DB | — | **DÉJÀ FAIT** (docker-compose.yml:36, init/01-pg-stat-statements.sql). Reste : pg_cron uniquement. |
| 6 | ~~Health checks~~ | API | — | **DÉJÀ FAIT** (`/health` + `/ready`, health.py:73,89) |
| 7 | ~~Docker multi-stage + Debian slim~~ | Infra | — | **DÉJÀ FAIT** (Dockerfile multi-stage, python:3.12-slim-bookworm, user non-root) |
| 8 | **Azure Key Vault** (transition depuis Fernet) | Sécurité | Migration | **À faire** — Fernet local déjà commité (97e269d), Key Vault pour prod Azure |
| 9 | **Uptime Kuma** | Monitoring | Docker compose | **À faire** |
| 10 | **API PlantNet** dans Evidence Engine | Moteurs | Intégration API | **À faire** |

**Bilan réel Phase 1** : 7 actions à faire (orjson, uvloop, Trivy, Bandit/Dependabot, Key Vault, Uptime Kuma, PlantNet). 3 actions déjà faites (pg_stat_statements, health checks, Docker multi-stage).

### Phase 2 — Court terme (3-6 mois)

| # | Action | Domaine | Effort | Statut réel |
|---|---|---|---|---|
| 11 | **pg_partman** + index partiels | DB | Extensions + tuning | pgvector **déjà activé** (migration 20260731_0024) |
| 12 | **Schemathesis** + **k6** dans CI | Testing | Intégration | **À faire** |
| 13 | **Cursor-based pagination** | API | Refactor endpoints list | **À faire** |
| 14 | **Grafana Stack** (Loki + Tempo) | Observabilité | Déploiement | Prometheus déjà en place |
| 15 | **Prefect 3.x** + **MLflow** + **DVC** | Data | Setup pipelines | **À faire** |
| 16 | **Polars 1.x** | Data | Remplacement pandas | **À faire** |
| 17 | **GeoPandas 1.0** + **DuckDB Spatial** | Géospatial | Upgrade | **À faire** |
| 18 | **BD Forêt v3** + **Sentinel-2** | Données | Intégration | **À faire** |
| 19 | **Audit logging immutable** (hash chain PostgreSQL) | Sécurité | Trigger + table | **À faire** |
| 20 | **NeuralProphet** dans Climate Engine | Moteurs | Intégration | **À faire** |

### Phase 3-4 — Moyen/long terme

- **DoWhy** causal inference dans Correlation Engine
- **CAPSIS** intégration dans Forest Dynamics/Simulation
- **SAM2** + **DINOv2** dans Botanical/GIS Engine
- **ERA5** + **Xarray/Dask** pour grilles climatiques
- **OGC API Features/Tiles** conformité
- **STAC** pour catalogage satellites
- **Feast** feature store + **BentoML** model serving
- **mTLS** / service mesh si microservices
- **IGN LiDAR HD** intégration 3D
- **Keycloak/Authentik** IAM centralisé

---

## 10. Partenariats stratégiques recommandés

| Partenaire | Type | Apport à GSIE |
|---|---|---|
| **IGN** | Données | BD Forêt v3, LiDAR HD, Géoportail API |
| **INRAE** | Science | Modèles croissance, CAPSIS, validation |
| **CIRAD** | Science | CAPSIS, 25+ modèles, IN-SYLVA |
| **CNPF** | Terrain | BioClimSol, ClimEssences, réseau propriétaires |
| **ONF** | Terrain | Forêt 4.0, applications mobiles, expansion internationale |
| **PlantNet** | API | Identification 77k espèces |
| **Arboreal** | Techno | AR measurements smartphone pour GeoSylva |
| **Dryad Networks** | Techno | Capteurs incendie LoRaWAN pour Ignis |
| **CTrees** | Données | Carbone global 1-hectare |
| **GFW (WRI)** | Données | Alerts déforestation temps réel |
| **EFFIS** | Données | Feux forêts Europe/MENA |
| **Pivotal Earth** | Techno | Métriques biodiversité TNFD |
| **EFI** | Policy | Standards EU, résilience climat |
| **FSC/PEFC** | Certification | Standards gestion durable |

---

## 11. Ce qui n'est pas recommandé

| Non-recommandé | Raison |
|---|---|
| ~~Apache AGE maintenant~~ | **DÉJÀ DÉPLOYÉ** — `docker-compose.yml:36` (`shared_preload_libraries=age`), `search_path=ag_catalog,public,tiger`. L'extension est active en local. La question n'est pas « faut-il l'activer » mais « faut-il l'utiliser pour les traversées de graphe » (benchmark Vague 1 RFC-0011). |
| **GraphQL** | REST + OpenAPI suffit pour GSIE, GraphQL = complexité N+1 |
| **gRPC** | Pas assez de services internes pour justifier |
| **Alpine base image** | Problèmes musl libc avec Python + extensions natives |
| **AKS maintenant** | Container Apps suffit, AKS = complexité K8s non justifiée |
| **Datadog** | Coûteux, Grafana Stack open-source couvre les besoins |
| **Auth0** | Cher post-acquisition Okta, SuperTokens open-source suffit |
| **ClickHouse** | Pas de volume IoT justifiant OLAP séparé |
| **Apache Sedona** | Pas de données >TB justifiant Spark géospatial |
| **NVIDIA Omniverse** | Unreal Engine 5.8 déjà choisi pour Centre de Commandement |

---

## 12. Conclusion

GSIE est bien positionné. Les actions Phase 1 réellement à faire sont au nombre de 7 (orjson, uvloop, Trivy, Bandit/Dependabot, Key Vault, Uptime Kuma, PlantNet API) — les 3 autres actions listées initialement sont déjà faites. La différenciation concurrentielle vient de l'architecture multi-moteurs — aucun concurrent n'a cette intégration.

**Ce document n'est pas une feuille de route.** La feuille de route canonique est `ROADMAP.md`. Si les actions identifiées ici doivent orienter le travail, elles doivent passer par un RFC dédié dans `02_RFC/`. Sinon ce document et `ROADMAP.md` diront deux choses différentes.

---

## 13. Errata — corrections post-revue dépôt (2026-08-02)

Le document initial contenait 5 écarts vérifiables avec l'état réel du dépôt, corrigés dans cette version :

| # | Affirmation initiale | Réalité dépôt | Correction |
|---|---|---|---|
| 1 | « Security headers middleware à implémenter » | `_SECURITY_HEADERS` dict dans `middleware.py:25-33`, appliqué par `TraceIdMiddleware:134`. Les 7 headers (X-Content-Type-Options, X-Frame-Options, HSTS, Referrer-Policy, Permissions-Policy, CSP, Cache-Control) sont déjà posés. | §4 et §9 corrigés. Note : HSTS émis inconditionnellement (pas seulement HTTPS/prod) — à corriger si besoin. |
| 2 | « pg_stat_statements + pg_cron, 2 extensions à activer » | pg_stat_statements déjà chargé (`docker-compose.yml:36` `shared_preload_libraries=age,pg_stat_statements,pgaudit`), `CREATE EXTENSION` dans `docker/init/01-pg-stat-statements.sql`, queries exporter dans `postgres-queries.yaml`. Seul pg_cron reste. | §7 et §9 corrigés. |
| 3 | « Apache AGE : non recommandé maintenant, attendre Phase 5+ » | AGE déjà dans `shared_preload_libraries` (`docker-compose.yml:36`), `search_path=ag_catalog,public,tiger`, `Dockerfile.db:42`. Déployé en local. | §11 corrigé. La question est l'utilisation, pas l'activation. |
| 4 | « API versioning URL path (/v1/, /v2/) à implémenter » | `api_v1_prefix: str = "/api/v1"` dans `config.py:140`, tous les routers montés avec ce prefix dans `app.py:327-346`. En place depuis l'origine. | §4 corrigé. |
| 5 | « PgBouncer : déjà prévu via config » | Config présent (`docker/pgbouncer.ini`, `config.py:186` `db_pgbouncer_mode`) mais **service orphelin non déployé** (audit P2-6). Le document initial était trompeur. | §7 corrigé. |
| 6 | « /health/live + /health/ready déjà implémenté » | Routes réelles : `/health` (liveness, `health.py:73`) et `/ready` (readiness, `health.py:89`). Noms faux dans le document initial. | §6 corrigé. |

### Chiffres non sourcés — statut

Les chiffres ont été vérifiés et sourcés par 2 sous-agents de recherche web (2026-08-02). Voir §14 « Sources » pour la liste complète. Les chiffres marketing d'éditeur (VictoriaMetrics, OpenObserve, Prefect) sont marqués comme tels avec la source du benchmark.

Corrections apportées :
- vLLM 793 tok/s : contexte ajouté (256 utilisateurs concurrents, benchmark Red Hat)
- NeuralProphet +55-92% : contexte ajouté (short/medium-term forecasts, paper Triebe et al. 2021)
- OpenObserve 140x : corrigé en 87x (benchmark éditeur 1.1TB), 140x est marketing
- Polars 5-10x : corrigé en 3-11x selon opération (benchmark indépendant)
- VictoriaMetrics 10x : corrigé en 16x query latency médiane, 2.5x stockage (benchmark éditeur)
- F1 0.52 → 0.87 DINOv2 : contexte ajouté (segmentation agricole, vs DeepLabV3, in-distribution)
- mIoU 81.74% MBA-Former : contexte ajouté (Gaofen-2 satellite imagery)
- PlantNet 77k : corrigé en 78 810 espèces (chiffre actuel)
- CAPSIS 25+ : précisé (25 dans package ONF, ~80 au total)
- SILVA : retiré INRAE, corrigé en TU Munich
- LoRA/QLoRA 6GB : précisé QLoRA spécifiquement (LoRA standard nécessite 15-28GB)
- GPTQ/AWQ <1% : corrigé en <4% (peut être plus élevé sur long-context)
- k6 2000+ VU : corrigé en 30 000-40 000 VU par instance
- IGN LiDAR HD 2024-2026 : corrigé en 2021-2026
- DuckDB Spatial 100+ : reformulé (ensemble complet en cours de développement)
- Darts 40+ : reformulé (large collection, chiffre exact non spécifié)
- Loki 1/10 coût ES : corrigé en ~75-80% moins cher
- Prefect 3.x 10x : précisé benchmark éditeur
- Azure ~$230-500/mois : retiré (estimation grossière non sourcée)

### Azure Key Vault — reframing

Le document initial disait « Azure Key Vault remplace Fernet local ». Fernet a été commité il y a quelques heures (97e269d, `core/config.py` `_DecryptedEnvSource`). Ce n'est pas un remplacement mais une **transition** : Fernet en local/dev, Key Vault en production Azure. Corrigé dans §6.

---

## 14. Sources

### AI/ML

| Affirmation | Source | Statut |
|---|---|---|
| vLLM 793 tok/s vs Ollama 41 | [Red Hat benchmark](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking) | Vérifié (256 users concurrents) |
| Phi-4-reasoning 14B MIT | [HF](https://huggingface.co/microsoft/Phi-4-reasoning), [paper](https://arxiv.org/pdf/2504.21318) | Vérifié (plus est compétitif avec o1-mini) |
| NeuralProphet +55-92% | [paper](https://arxiv.org/pdf/2111.15397) Triebe et al. 2021 | Vérifié (short/medium-term) |
| DINOv2 F1 0.52→0.87 | [paper](https://arxiv.org/html/2508.07514v2) | Vérifié (agricultural segmentation, vs DeepLabV3) |
| MBA-Former mIoU 81.74% | [paper](https://doi.org/10.3390/f17050517) Forests 2025 | Vérifié (Gaofen-2 imagery) |
| YOLO-PTHD mAP 0.923 | [paper](https://doi.org/10.3390/insects16080829) Insects 2025 | Vérifié (Sirex noctilio) |
| Chronos-2 120M, 300+ f/s | [HF](https://huggingface.co/amazon/chronos-2), [paper](https://arxiv.org/pdf/2510.15821) | Vérifié (A10G GPU) |
| PlantNet 78 810 espèces | [my.plantnet.org](https://my.plantnet.org/) | Vérifié |
| PlantCLEF 7 806 espèces, 1.4M | [LifeCLEF 2024](https://www.imageclef.org/PlantCLEF2024) | Vérifié |
| SAM2 zero-shot | [Meta AI](https://ai.meta.com/research/sam2/) | Vérifié |
| CAPSIS 25+ modèles | [capsis.cirad.fr](https://capsis.cirad.fr/) | Partiel (25 package ONF, ~80 total) |
| SILVA 155k+ obs | [paper](https://webarchiv.it.ls.tum.de/waldwachstum.wzw.tum.de/fileadmin/publications/535.pdf) | Partiel (TU Munich, pas INRAE) |
| QLoRA 7B 6GB | [paper](https://arxiv.org/pdf/2305.14314) Dettmers 2023 | Vérifié (QLoRA spécifiquement) |
| GPTQ/AWQ <4% loss | [GPTQ](https://arxiv.org/pdf/2210.17323), [AWQ](https://arxiv.org/html/2306.00978) | Partiel (<4%, pas <1%) |

### Infrastructure / Data / Géospatial

| Affirmation | Source | Statut |
|---|---|---|
| Polars 3-11x | [benchmark](https://www.danilchenko.dev/posts/polars-vs-pandas/) | Partiel (selon opération) |
| VictoriaMetrics 16x | [benchmark éditeur](https://new.victoriametrics.com/blog/reducing-costs-p1/) | Partiel (marketing) |
| OpenObserve 87x | [benchmark éditeur](https://openobserve.ai/blog/elasticsearch-openobserve-benchmarking/) | Partiel (marketing, 140x est claim) |
| Loki ~75-80% moins cher | [comparaison](https://lucaberton.com/blog/loki-vs-elasticsearch-2026/) | Partiel |
| ERA5 1940-, 31km, horaire | [Copernicus CDS](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-complete) | Vérifié |
| SoilGrids 250m, 6 profondeurs | [ISRIC docs](https://docs.isric.org/globaldata/soilgrids/index.html) | Vérifié |
| Sentinel-2 10m, 5j, gratuit | [Copernicus](https://sentinels.copernicus.eu/) | Vérifié |
| BD Forêt v3 0.5ha, 35 essences | [IGN](https://cartes.gouv.fr/aide/fr/partenaires/ign/referentiels-description-territoire/foret/bd-foret-v3/) | Vérifié |
| EuroSAT 27k, 10 classes | [paper](https://doi.org/10.1109/jstars.2019.2918242) | Vérifié |
| IGN LiDAR HD 10 pts/m² | [data.gouv.fr](https://www.data.gouv.fr/en/datasets/lidar-hd/) | Vérifié (2021-2026) |
| GeoPandas 1.0 | [release](https://github.com/geopandas/geopandas/releases/tag/v1.0.0) | Vérifié |
| Prefect 3.x 10x | [blog éditeur](https://www.prefect.io/blog/prefect-3-generally-available-september-3) | Partiel (marketing) |
| k6 30k-40k VU | [benchmarks](https://github.com/grafana/k6-benchmarks) | Vérifié |
| BRIN 99% plus compact | [cas réel](https://postgresdba.hashnode.dev/postgresql-brin-indexes-when-how-to-use-block-range-indexes) | Partiel (append-only, haute corrélation) |
| Azure Container Apps scale-to-zero | [Azure docs](https://azure.microsoft.com/en-us/products/container-apps) | Vérifié |

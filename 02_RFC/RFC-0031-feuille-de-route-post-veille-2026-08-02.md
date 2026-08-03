# RFC-0031 — Feuille de route technique post-veille 2026-08-02

| Champ | Valeur |
|---|---|
| **ID** | RFC-0031 |
| **Statut** | Adopté (2026-08-02, DEC-000042) |
| **Auteur** | Direction technique (assistée par Devin) |
| **Date** | 2026-08-02 |
| **Décision liée** | DEC-000042 |
| **Périmètre** | API GSIE, infrastructure, moteurs, observabilité, sécurité |
| **Document source** | `21_EXPERIMENTS/VEILLE_TECHNO_2026-08-02.md` (niveau de preuve C, sourcé) |

## 1. Problème

La veille technologique du 2026-08-02 a identifié 20 actions potentielles
réparties sur 4 phases. Sans encadrement, ces actions entrent en concurrence
avec `ROADMAP.md` (feuille de route canonique) et les directives actives
(GSIE-DIR-0011, RFC-0021, RFC-0016, RFC-0011). Le risque est celui d'une
deuxième source de vérité — exactement ce qui est arrivé au README.

Ce RFC formalise lesquelles des 20 actions sont adoptées, dans quel ordre,
et sous quelle autorité. Les actions non adoptées sont explicitement
écartées pour éviter l'ambiguïté.

## 2. Décision proposée

### 2.1 Actions adoptées — Phase 1 (immédiat, 1-2 mois)

Ces actions sont peu coûteuses, à faible risque, et ne contredisent
aucune directive ou RFC active.

| # | Action | Domaine | Statut dépôt | Effort |
|---|---|---|---|---|
| 1 | **orjson** pour sérialisation JSON | API | **Fait** (2026-08-02) | 1 ligne |
| 2 | **Trivy** dans CI | Sécurité | **Fait** (2026-08-02) | 1 job GH Actions |
| 3 | **Bandit** SAST dans CI | Sécurité | **Fait** (2026-08-02) | 1 job GH Actions |
| 4 | **Dependabot** | Sécurité | **Fait** (2026-08-02) | `.github/dependabot.yml` |
| 5 | **Tenacity** dépendance | Résilience | **Fait** (2026-08-02) | `pyproject.toml` |
| 6 | **uvloop** sur Linux | API | **À faire** | 1 flag |
| 7 | **Uptime Kuma** | Monitoring | **À faire** | docker-compose |
| 8 | **API PlantNet** dans Evidence Engine | Moteurs | **À faire** | Intégration API |

**Justification** : orjson, Trivy, Bandit, Dependabot, Tenacity sont déjà
implémentés. uvloop est 1 flag (Linux uniquement, gain I/O mesurable).
Uptime Kuma est un conteneur quasi-gratuit. PlantNet est l'intégration
la plus à forte valeur pour le Botanical Engine (78 810 espèces,
[source](https://my.plantnet.org/)).

### 2.2 Actions adoptées — Phase 2 (court terme, 3-6 mois)

Ces actions nécessitent un effort d'intégration mais sont cohérentes
avec l'architecture existante.

| # | Action | Domaine | Prérequis |
|---|---|---|---|
| 9 | **pg_cron** + **pg_trgm** + **HypoPG** | DB | Migration Alembic |
| 10 | **Index partiels** + **BRIN** sur tables temporelles | DB | Audit index existants |
| 11 | **Cursor-based pagination** sur endpoints list | API | Refactor endpoints |
| 12 | **SSE helper** pour notifications/dashboards | API | `shared/sse.py` |
| 13 | **Backpressure middleware** | API | `shared/middleware.py` |
| 14 | **Audit logging immutable** (hash chain PostgreSQL) | Sécurité/RGPD | Migration + trigger |
| 15 | **Hypothesis** + **Schemathesis** dev deps + tests | Testing | `pyproject.toml` |
| 16 | **Grafana Stack** (Loki + Tempo) | Observabilité | Déploiement Docker |
| 17 | **Polars 1.x** pour analytics | Data | Remplacement pandas (Forge) |
| 18 | **GeoPandas 1.0** + **DuckDB Spatial** | Géospatial | Upgrade |
| 19 | **BD Forêt v3** + **Sentinel-2** | Données | Pipeline ingestion |
| 20 | **NeuralProphet** dans Climate Engine | Moteurs | Intégration |

**Justification** : chaque action répond à un besoin identifié dans
`ROADMAP.md` ou les audits (`AUDIT_BASE_DONNEES_2026-07-27.md`,
`AUDIT_PHASE4_2026-08-02.md`). Les sources sont vérifiées dans
`21_EXPERIMENTS/VEILLE_TECHNO_2026-08-02.md` §14.

### 2.3 Actions explicitement écartées

| Action | Raison |
|---|---|
| **Apache AGE activation** | **Déjà déployé** (`docker-compose.yml:36`). La question est l'utilisation, pas l'activation — voir RFC-0011 Vague 1 benchmark. |
| **pg_stat_statements** | **Déjà activé** (`docker-compose.yml:36`, `docker/init/01-pg-stat-statements.sql`). |
| **Security headers middleware** | **Déjà implémenté** (`middleware.py:25-33`). Note : HSTS émis inconditionnellement — à corriger si besoin (action mineure). |
| **API versioning /api/v1/** | **En place depuis l'origine** (`config.py:140`). |
| **Docker multi-stage + Debian slim** | **Déjà en place** (Dockerfile multi-stage, `python:3.12-slim-bookworm`). |
| **Health checks** | **Déjà implémentés** (`/health` + `/ready`, `health.py:73,89`). |
| **Azure Key Vault** | **Transition** depuis Fernet local (97e269d), pas remplacement. À traiter dans le déploiement Azure production, pas dans ce RFC. |
| **GraphQL** | REST + OpenAPI suffit pour GSIE. GraphQL = complexité N+1 non justifiée. |
| **gRPC** | Pas assez de services internes pour justifier. |
| **Alpine base image** | Problèmes musl libc avec Python + extensions natives. Debian slim retenu. |
| **AKS** | Container Apps suffit. AKS = complexité K8s non justifiée. |
| **Datadog** | Coûteux. Grafana Stack open-source couvre les besoins. |
| **Auth0** | Cher post-acquisition Okta. SuperTokens open-source suffit si IAM centralisé nécessaire. |
| **ClickHouse** | Pas de volume IoT justifiant OLAP séparé. |
| **Apache Sedona** | Pas de données >TB justifiant Spark géospatial. |
| **NVIDIA Omniverse** | Unreal Engine 5.8 déjà choisi pour Centre de Commandement. |

### 2.4 Actions différées (Phase 3-4+)

| Action | Raison du report |
|---|---|
| **DoWhy** causal inference | Correlation Engine doit être stable avant d'ajouter causalité. |
| **CAPSIS** intégration | Nécessite partenariat CIRAD + Forest Dynamics Engine mature. |
| **SAM2** + **DINOv2** | Nécessite Botanical/GIS Engine mature + dataset d'entraînement. |
| **OGC API Features/Tiles** | Conformité standard — après que l'API REST de base soit stable. |
| **STAC** | Catalogage satellites — après pipeline Sentinel-2. |
| **Feast** feature store | Après que les features climatiques/sol/forestières soient identifiées. |
| **Keycloak/Authentik** | IAM centralisé — seulement si SAML/LDAP/SSO enterprise requis. |
| **vLLM** + **Phi-4-reasoning** | Reasoning Engine doit être spécifié avant changement d'inférence. |
| **Prefect 3.x** + **MLflow** + **DVC** | Data pipelines — après que Forge soit stabilisé. |
| **ERA5** + **Xarray/Dask** | Grilles climatiques — après NeuralProphet intégré. |

## 3. Alternatives considérées

### 3.1 Ne pas créer de RFC

Laisser `ROADMAP.md` comme seule source de vérité et le document de veille
comme document exploratoire sans force exécutoire.

**Rejeté** : le Fondateur a demandé de trancher. Sans RFC, le document de
veille et `ROADMAP.md` disent deux choses différentes.

### 3.2 Tout adopter

Adopter les 20 actions sans filtrage.

**Rejeté** : 3 actions sont déjà faites, 16 sont écartées ou différées.
Tout adopter créerait de la dette technique et de la confusion.

### 3.3 RFC par domaine

Créer un RFC par domaine (DB, API, moteurs, infra).

**Rejeté** : trop de RFC pour un périmètre qui est essentiellement une
priorisation. Un seul RFC suffit.

## 4. Conséquences

### 4.1 Positives

- Une seule source de vérité pour la roadmap technique post-veille.
- Actions déjà faites explicitement écartées (pas de double travail).
- Actions différées justifiées (pas de pression pour tout faire maintenant).
- Sources vérifiées pour chaque chiffre (niveau de preuve C).

### 4.2 Négatives

- 8 actions Phase 1 + 12 actions Phase 2 = 20 actions à suivre.
- Certaines actions Phase 2 (BD Forêt v3, NeuralProphet) nécessitent
  un effort d'intégration non négligeable.
- Le report de vLLM/Phi-4-reasoning maintient Ollama en place
  temporairement (throughput inférieur, [source](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking)).

## 5. Vérification de conformité

- [x] **Primauté** : ne contredit pas `00_CONSTITUTION/`.
- [x] **Locked** : ne modifie aucun document Locked.
- [x] **Phase 4** : code métier autorisé (DEC-000017).
- [x] **Français** : tout en français.
- [x] **Traçabilité** : sources citées dans `21_EXPERIMENTS/VEILLE_TECHNO_2026-08-02.md` §14.
- [x] **Statut** : Adopté (2026-08-02, DEC-000042).
- [x] **L'IA assiste** : recommandations contournables, explicables.

## 6. Décision

**Adopté** par le Fondateur le 2026-08-02 (DEC-000042).

Les 3 actions Phase 1 restantes (uvloop, Uptime Kuma, PlantNet) peuvent
être implémentées immédiatement. L'intégration des actions Phase 2 dans
`ROADMAP.md` est suspendue à la demande explicite du Fondateur — le feu
vert pour l'intégration sera donné ultérieurement.

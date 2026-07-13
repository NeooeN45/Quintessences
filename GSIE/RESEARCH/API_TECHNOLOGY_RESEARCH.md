# Fiche recherche — API GSIE : choix technologiques et architecture

| Champ | Valeur |
|---|---|
| **Document** | RESEARCH/API_TECHNOLOGY_RESEARCH |
| **Dossier** | GSIE/RESEARCH/ |
| **Phase** | 4 — Implémentation |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Livrable cible** | 401 — API GSIE (REST/WebSocket) |
| **Sources** | TechEmpower Benchmarks Round 23 (2025), benchmarks Python API frameworks 2025-2026, FastAPI docs, Litestar docs, articles architecture API gateway 2026, PostGIS/FastAPI production guides |
| **Lois fondatrices** | CON-002 (science), CON-003 (connaissance avant code), CON-005 (traçabilité), CON-007 (modularité) |
| **Documents connexes** | `TECHNOLOGY_STACK.md` (livrable 202, ADR-0001/0002/0003), `ENGINE_COMMUNICATION_PROTOCOL.md` (livrable 203), `GSIE_MASTER_ARCHITECTURE.md` (livrable 201), `ENGINE_INTERFACE_CONTRACTS.md` (livrable 206) |

---

## 1. Objet

Recherche opérationnelle pour le choix de la stack API GSIE
(livrable 401). Analyse des frameworks Python, des patterns
d'architecture API multi-protocole, des bonnes pratiques
géospatiales (PostGIS), et des options temps réel. Cette fiche
alimente la décision d'implémentation de l'API GSIE.

---

## 2. Contraintes du projet GSIE

### 2.1 Contraintes issues de l'architecture existante

| Contrainte | Source | Impact API |
|---|---|---|
| **Python 3.12** pour orchestration | ADR-0001 (livrable 202) | Framework Python requis |
| **Rust** pour cœur IP (pyo3) | ADR-0002 (livrable 202) | API appelle des bindings Rust |
| **Go optionnel** pour temps réel | ADR-0003 (livrable 202) | API temps réel pourrait être Go |
| **Couplage faible** (T-2) | Constitution technique | API = contrat, pas d'accès direct |
| **Offline-first** (RFC-0003) | Architecture distribuée | API doit gérer sync différée |
| **14 moteurs** à orchestrer | Livrable 206 | API multiplex les moteurs |
| **WebSocket + REST** | Livrable 203 | Double protocole requis |
| **PostGIS** pour géospatial | Datasets IGN | Driver async PostGIS requis |
| **Traçabilité** (CON-005) | Constitution | Toute requête doit être tracée |
| **Explicabilité** (CON-004) | Constitution | Réponses avec source + preuve |
| **Souveraineté données** (CON-008) | Constitution | Pas de cloud non-souverain |

### 2.2 Cas d'usage API GSIE

| Cas | Protocole | Latence cible | Fréquence |
|---|---|---|---|
| Hub → moteurs (requête statique) | REST | < 100 ms | On-demand |
| Hub ← Ignis (front de feu temps réel) | WebSocket | < 50 ms | 1-10 Hz |
| GeoSylva → Forest Dynamics (synchronisation) | REST + WebSocket | < 500 ms | Différé + live |
| ForeFire ← Simulation Engine (propagation) | WebSocket | < 100 ms | 10 Hz |
| Apps → API GSIE (lecture publique) | REST | < 200 ms | On-demand |
| Moteur → moteur (sync, < 1s) | Appel direct (in-process) | < 1 s | On-demand |
| Moteur → moteur (async, > 1s) | Message passing | N/A | Asynchrone |
| Encyclopédie → API publique | REST + GraphQL (option) | < 200 ms | On-demand |

---

## 3. Frameworks Python pour API — comparatif 2026

### 3.1 Benchmark (sources : TechEmpower Round 23, benchmarks communautaires 2025-2026)

| Framework | RPS (JSON 1k) | RPS (JSON 10k) | RPS (DB reads) | Base |
|---|---|---|---|---|
| **Django Bolt** (Rust-powered) | 39 157 | 29 857 | 5 263 | Django + Rust |
| **Litestar** | 35 398 | 27 820 | 1 456 | ASGI propre |
| **FastAPI** | 13 726 | 2 565 | 1 465 | Starlette (ASGI) |
| Django Ninja | 3 037 | 2 652 | 982 | Django |
| Django REST Framework | 1 951 | 1 702 | 1 489 | Django |

> **Note** : benchmarks informels (machine locale, sans isolation Docker).
> Ordre de grandeur indicatif, pas vérité absolue.

### 3.2 Analyse par framework

#### FastAPI (v0.139.x)

| Critère | Évaluation |
|---|---|
| **Performance** | Bonne (13K RPS JSON 1k). Étoile Starlette/ASGI |
| **Écosystème** | **~100K stars GitHub**, communauté massive, docs excellentes |
| **Validation** | Pydantic v2 (core Rust, 50x plus rapide que v1) |
| **Async** | Natif, first-class |
| **WebSocket** | First-class, type-checked, async |
| **OpenAPI** | Auto-généré, Swagger UI + ReDoc |
| **SQLAlchemy** | Supporté (async) |
| **PostGIS/asyncpg** | Recommandé (asyncpg > psycopg pour PostGIS) |
| **Courbe d'apprentissage** | Faible (type hints Python standard) |
| **Maturité production** | **Excellente** — FastAPI Conf '26, mini-documentaire 2025 |
| **Geospatial** | **Référence** — guides production FastAPI+PostGIS disponibles |
| **LLM/AI** | **Standard de fait** pour backends LLM en 2026 |

#### Litestar (v2.24.x)

| Critère | Évaluation |
|---|---|
| **Performance** | **Excellente** (35K RPS JSON 1k, 2.5x FastAPI) |
| **Écosystème** | ~8K stars, communauté croissante mais plus petite |
| **Validation** | msgspec (C-based, **12x plus rapide que Pydantic v2**) |
| **Async** | Natif |
| **WebSocket** | Supporté |
| **OpenAPI** | Auto-généré |
| **SQLAlchemy** | Plugin natif (SQLAlchemyPlugin) |
| **Architecture** | DI meilleure pour grandes apps (past few dozen routes) |
| **Courbe d'apprentissage** | Modérée (concepts propres) |
| **Maturité production** | Bonne, templates production disponibles |
| **Geospatial** | Pas de guide spécifique PostGIS |

#### Django Bolt (Rust-powered)

| Critère | Évaluation |
|---|---|
| **Performance** | **Meilleure** (39K RPS JSON 1k) |
| **Écosystème** | Récent, petit, non prouvé en production |
| **Base** | Django + Rust (moteur Rust) |
| **Maturité** | **Trop récent** pour production critique |
| **Verdict** | À surveiller, pas pour GSIE Phase 4 |

### 3.3 Verdict framework

| Framework | Recommandation GSIE | Raison |
|---|---|---|
| **FastAPI** | **✅ CHOIX RECOMMANDÉ** | Écosystème, maturité, WebSocket, PostGIS, LLM, communauté, docs. Déjà prévu dans ADR-0001 |
| Litestar | Alternative viable | Performance supérieure, mais écosystème plus petit et pas de guide PostGIS |
| Django Bolt | Trop récent | Non prouvé en production, écosystème immature |
| Django REST | Non adapté | Trop lent, pas async natif, Django = overhead inutile |

> **Recommandation** : **FastAPI 0.115+** pour l'API GSIE. Déjà acté
> dans ADR-0001 (livrable 202). Cette recherche confirme le choix avec
> données 2026. Litestar reste une alternative si la performance
> devient un goulot (migration possible grâce aux contrats d'interface).

---

## 4. Architecture API multi-protocole

### 4.1 Pattern 2026 recommandé : 3 couches protocole

Source : articles architecture API gateway 2026.

```
┌─────────────────────────────────────────────────────┐
│  COUCHE 1 — REST (API publique, partenaires)        │
│  FastAPI · OpenAPI · JSON · HTTPS                   │
│  → Apps clientes, Hub, partenaires, Encyclopédie    │
├─────────────────────────────────────────────────────┤
│  COUCHE 2 — WebSocket (temps réel, streaming)       │
│  FastAPI WebSocket · Redis Pub/Sub · JSON           │
│  → Front de feu (Ignis), sync live, telemetry       │
├─────────────────────────────────────────────────────┤
│  COUCHE 3 — gRPC (inter-moteurs, optionnel)         │
│  Protobuf · HTTP/2 · Bidirectional streaming        │
│  → Communication inter-moteurs haute performance    │
└─────────────────────────────────────────────────────┘
```

### 4.2 Justification par protocole

| Protocole | Cas GSIE | Pourquoi |
|---|---|---|
| **REST** | API publique, Hub (statique), Encyclopédie | Standard, simple, cacheable, OpenAPI auto-doc |
| **WebSocket** | Ignis (front de feu), sync live, ForeFire | Bidirectionnel, temps réel < 50ms, persistant |
| **gRPC** (optionnel) | Inter-moteurs haute perf | 30-50% moins de latence que REST, Protobuf binaire, types forts |
| **SSE** (optionnel) | Streaming unidirectionnel (LLM, logs) | Plus simple que WebSocket pour server→client seul |
| **GraphQL** (optionnel) | Encyclopédie (requêtes complexes) | Une endpoint, requêtes flexibles, federation |

### 4.3 Recommandation GSIE

| Protocole | Phase 4 | Priorité |
|---|---|---|
| **REST** | Oui — API publique + Hub | P0 |
| **WebSocket** | Oui — Ignis + sync live | P0 |
| gRPC | Évaluer — si perf inter-moteurs insuffisante | P2 |
| SSE | Non (WebSocket couvre le besoin) | — |
| GraphQL | Évaluer — Encyclopédie (livrable 450) | P2 |

---

## 5. Stack géospatiale (PostGIS)

### 5.1 Architecture recommandée (source : guides production 2026)

```
┌──────────────┐    asyncpg     ┌───────────┐    PgBouncer    ┌──────────────┐
│   FastAPI    │ ──────────────→ │  asyncpg  │ ──────────────→ │ PostgreSQL   │
│  (async I/O) │                 │   pool    │   (transaction) │ + PostGIS    │
└──────────────┘                 └───────────┘                 └──────────────┘
       │                                                            │
       │  Redis Pub/Sub                                             │  LISTEN/NOTIFY
       ↓                                                            ↓
┌──────────────┐                                            ┌──────────────┐
│   WebSocket  │ ←───────────── Redis Pub/Sub ───────────── │  PostGIS     │
│   fan-out    │                                            │  events      │
└──────────────┘                                            └──────────────┘
```

### 5.2 Composants clés

| Composant | Techno | Rôle | Justification |
|---|---|---|---|
| **Driver DB** | asyncpg | Connexion async PostgreSQL | **Recommandé** > psycopg pour PostGIS (binary protocol, zero-copy, prepared statements) |
| **Connection pool** | PgBouncer (transaction mode) | Multiplexage connexions | Découple concurrence API des limites PostgreSQL. Spatial = locks plus longs |
| **ORM** | SQLAlchemy 2.0 async | Abstraction SQL | Déjà prévu ADR-0001. Supporte asyncpg |
| **Cache** | Redis | Cache + Pub/Sub | Cache requêtes spatiales + fan-out WebSocket |
| **Migrations** | Alembic | Versioning schéma | Déjà prévu ADR-0001 (T-6) |
| **Vector tiles** | Tippecanoe (static) + PostGIS MVT (dynamic) | Tuiles vectorielles | Pour Hub/Cesium |

### 5.3 Configuration PostGIS production

| Paramètre | Valeur recommandée | Source |
|---|---|---|
| `max_connections` | 20-40 par réplica API | Guide geospatial-api.com |
| `statement_timeout` | 5s | Empêche spatial joins runaway |
| PgBouncer mode | Transaction pooling | Découple concurrence |
| `shared_buffers` | 256MB | PostgreSQL tuning |
| `effective_cache_size` | 1GB | PostgreSQL tuning |
| Type géométrie | **Standardiser** `geometry` OU `geography` par table | Évite implicit casting overhead |
| Index | GiST + SP-GiST | Index spatiaux matures PostGIS 3.3+ |

### 5.4 Pattern temps réel géospatial (PostGIS → WebSocket)

```
1. Détection (capteur, simulation, drone)
   → INSERT dans PostGIS
   → PostGIS LISTEN/NOTIFY (zero polling)

2. WebSocket server (FastAPI)
   → Subscribe au channel PostGIS
   → Fan-out vers tous les clients connectés
   → < 100ms détection → navigateur

3. Reconnect with backoff
   → Replay-then-live resume
   → Throttle high-frequency streams
```

> **Implication GSIE** : ce pattern est directement applicable pour
> Ignis (front de feu), ForeFire (propagation), et la sync live
> GeoSylva. PostGIS LISTEN/NOTIFY → FastAPI WebSocket → Hub Unreal.

---

## 6. API Gateway — évaluation

### 6.1 Options

| Solution | Type | Avantages | Inconvénients | Pertinence GSIE |
|---|---|---|---|---|
| **Kong** | Self-hosted | 50K RPS/node, NGINX, plugins JWT/rate-limit | Ops overhead | P2 (si scale) |
| **Envoy** | Self-hosted | gRPC natif, xDS, Istio | Complexe | P2 (si gRPC) |
| **AWS API Gateway** | Managed | Auto-scale, WebSocket, Lambda | Vendor lock-in, non-souverain | ❌ (CON-008) |
| **NGINX** | Self-hosted | Simple, performant | Pas de plugins natifs | P1 (reverse proxy) |
| **Traefik** | Self-hosted | Auto-config Docker, Let's Encrypt | Moins performant que Kong | P1 (dev/staging) |
| **Aucun (FastAPI direct)** | — | Simple, pas de couche supplémentaire | Pas de rate-limit centralisé | **P0 (début Phase 4)** |

### 6.2 Recommandation GSIE

| Phase | Gateway | Raison |
|---|---|---|
| **Phase 4 début** | **FastAPI direct** (uvicorn + reverse proxy NGINX) | Simplicité, YAGNI, pas de traffic massif initialement |
| Phase 4 milieu | + NGINX (reverse proxy, TLS, rate-limit) | Production hardening |
| Phase 5 (si scale) | Kong ou Envoy | Si > 10K RPS ou multi-services |

> **Principe YAGNI** : ne pas ajouter de gateway tant que le traffic
> ne le justifie pas. FastAPI + uvicorn + NGINX suffit pour démarrer.

---

## 7. Go vs Rust pour API temps réel (évaluation ADR-0003)

### 7.1 Contexte

ADR-0003 prévoit Go optionnel pour l'API temps réel (GCS-Lite).
Cette recherche évalue si Go ou Rust est préférable.

### 7.2 Comparatif (sources : retours production 2026)

| Critère | Go | Rust | Verdict GSIE |
|---|---|---|---|
| **Performance brute** | Bonne | Excellente (15% mieux p99) | Rust gagne |
| **Stabilité production** | Excellente (3x moins OOMKilled) | Bonne (mais tuning nécessaire) | **Go gagne** |
| **Temps de compilation** | 28s | 4min30s (10x plus lent) | **Go gagne** |
| **Courbe d'apprentissage** | 2 jours | 1 semaine | **Go gagne** |
| **p99 sous charge mixte** | 5-8ms (defaults bons) | 35-45ms (Tokio à tuner) | **Go gagne** |
| **Goroutines vs Tokio** | Preemption auto, stack growth | Tuning manuel nécessaire | **Go gagne** |
| **Écosystème réseau** | Mature (net/http, décennies) | En construction | **Go gagne** |
| **Sécurité mémoire** | Modérée (GC) | Excellente (ownership) | Rust gagne |
| **Interop pyo3** | N/A | Natif (déjà utilisé) | **Rust gagne** |
| **Binaire statique** | Oui | Oui | Égalité |

### 7.3 Verdict Go vs Rust pour API temps réel GSIE

| Cas | Recommandation | Raison |
|---|---|---|
| **API temps réel (WebSocket fan-out, GCS-Lite)** | **Go** | Stabilité production, defaults meilleurs, compilation rapide, écosystème réseau mature |
| **Cœur IP (moteurs critiques)** | **Rust** (déjà acté ADR-0002) | Sécurité mémoire, performance calcul, pyo3 |
| **API principale (REST/WebSocket)** | **Python/FastAPI** (déjà acté ADR-0001) | Écosystème scientifique, async, PostGIS |

> **Recommandation** : si un service temps réel dédié est nécessaire
> (GCS-Lite, fan-out WebSocket haute fréquence), **Go** est préféré
> à Rust pour ce cas spécifique. Go excelle pour les services réseau
> I/O-bound avec concurrence massive. Rust reste pour le cœur IP.
> Mais en Phase 4 début, **FastAPI WebSocket suffit** — Go est P2.

---

## 8. Stack API GSIE recommandée — synthèse

### 8.1 Stack Phase 4 début (P0)

```
┌─────────────────────────────────────────────────────────────┐
│  API GSIE — Stack Phase 4                                   │
│                                                             │
│  Framework :    FastAPI 0.115+ (Python 3.12)                │
│  Validation :   Pydantic v2 (core Rust)                     │
│  REST :         FastAPI + OpenAPI auto-gen                  │
│  WebSocket :    FastAPI WebSocket (async, type-checked)      │
│  ORM :          SQLAlchemy 2.0 async                        │
│  Driver DB :    asyncpg (PostGIS)                           │
│  Pool :         PgBouncer (transaction mode)                │
│  Cache/PubSub : Redis 7+                                    │
│  Migrations :   Alembic                                     │
│  Server :       Uvicorn (ASGI) + NGINX (reverse proxy)      │
│  Tests :        pytest + httpx (async)                      │
│  Logs :         structlog (structured, CON-005)             │
│  Auth :         JWT (15min access, 7d refresh) + OAuth2     │
│  Docs :         OpenAPI 3.1 + Swagger UI + ReDoc            │
│                                                             │
│  Cœur IP :      Rust (pyo3 bindings) — ADR-0002             │
│  Temps réel :   FastAPI WebSocket (Go optionnel P2)         │
│  Geospatial :   PostGIS 3.3+ + asyncpg + GDAL/PDAL          │
│  Vector tiles : Tippecanoe (static) + PostGIS MVT (dynamic) │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Versions cibles (épinglées, T-10)

| Composant | Version cible | Statut |
|---|---|---|
| Python | 3.12.x | Acté ADR-0001 |
| FastAPI | 0.115+ | Acté ADR-0001, confirmé 2026 |
| Pydantic | 2.x | Acté ADR-0001 |
| SQLAlchemy | 2.x | Acté ADR-0001 |
| asyncpg | 0.30+ | Recommandé (PostGIS) |
| Alembic | 1.13+ | Acté ADR-0001 |
| Redis | 7+ | Cache + Pub/Sub |
| Uvicorn | 0.30+ | ASGI server |
| NGINX | 1.25+ | Reverse proxy + TLS |
| structlog | 24+ | Acté ADR-0001 |
| pytest | 8+ | Acté ADR-0001 |
| PostGIS | 3.3+ | Spatial maturity |
| PostgreSQL | 14+ | PostGIS stability |

### 8.3 Évolutions possibles (P1/P2)

| Évolution | Quand | Techno |
|---|---|---|
| API Gateway | > 10K RPS ou multi-services | Kong ou Envoy |
| gRPC inter-moteurs | Si perf REST insuffisante | Protobuf + HTTP/2 |
| GraphQL Encyclopédie | Livrable 450 | Strawberry ou Ariadne (Python) |
| Go temps réel | Si WebSocket fan-out massif | Go + goroutines |
| Litestar migration | Si perf FastAPI insuffisante | Contrats d'interface permettent migration |

---

## 9. Architecture API GSIE — schéma

```
                    ┌─────────────────────────────────┐
                    │        CLIENTS (Apps + Hub)       │
                    │  GeoSylva · Ignis · Hydro · Hub  │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │      NGINX (reverse proxy)       │
                    │  TLS 1.3 · rate-limit · routing  │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │      FASTAPI (API GSIE)          │
                    │                                  │
                    │  REST endpoints (/api/v1/...)    │
                    │  ├── /forest (Forest Dynamics)   │
                    │  ├── /climate (Climate Engine)   │
                    │  ├── /gis (GIS Engine)           │
                    │  ├── /ignis (Simulation)         │
                    │  ├── /botanical (Botanical)      │
                    │  ├── /knowledge (Encyclopédie)   │
                    │  └── /health, /metrics           │
                    │                                  │
                    │  WebSocket endpoints             │
                    │  ├── /ws/ignis (front de feu)    │
                    │  ├── /ws/forest (sync live)      │
                    │  └── /ws/sim (ForeFire)          │
                    │                                  │
                    │  OpenAPI 3.1 auto-gen            │
                    │  JWT auth + OAuth2               │
                    └──────┬──────────┬────────────────┘
                           │          │
              ┌────────────▼──┐   ┌───▼────────────┐
              │  pyo3 bridge  │   │  Redis Pub/Sub │
              │  (Rust cœur)  │   │  (cache+events)│
              └──────┬────────┘   └───┬────────────┘
                     │                │
              ┌──────▼────────┐   ┌───▼────────────┐
              │  14 moteurs   │   │  WebSocket     │
              │  (Rust/Python)│   │  fan-out       │
              └──────┬────────┘   └────────────────┘
                     │
              ┌──────▼────────────────────────┐
              │  PostgreSQL + PostGIS          │
              │  (asyncpg + PgBouncer)         │
              │  LISTEN/NOTIFY → Redis → WS    │
              └───────────────────────────────┘
```

---

## 10. Recommandations pour le livrable 401

| ID | Recommandation | Priorité |
|---|---|---|
| API-01 | **FastAPI 0.115+** comme framework API (confirme ADR-0001) | P0 |
| API-02 | **asyncpg** comme driver PostGIS (pas psycopg) | P0 |
| API-03 | **PgBouncer** en transaction pooling mode | P0 |
| API-04 | **Redis** pour cache + Pub/Sub + WebSocket fan-out | P0 |
| API-05 | **PostGIS LISTEN/NOTIFY** → Redis → WebSocket (zero polling) | P0 |
| API-06 | **NGINX** reverse proxy + TLS 1.3 | P0 |
| API-07 | **JWT** (15min access, 7d refresh) + OAuth2 | P0 |
| API-08 | **structlog** pour logs structurés traçables (CON-005) | P0 |
| API-09 | **OpenAPI 3.1** auto-généré + Swagger UI + ReDoc | P0 |
| API-10 | Versioning API : `/api/v1/` (CON-010 évolution sans perte) | P0 |
| API-11 | **pytest + httpx** pour tests API async | P0 |
| API-12 | gRPC inter-moteurs à évaluer si perf REST insuffisante | P2 |
| API-13 | GraphQL pour Encyclopédie (livrable 450) | P2 |
| API-14 | Go pour service temps réel dédié si WebSocket massif | P2 |
| API-15 | Kong/Envoy API gateway si > 10K RPS | P2 |
| API-16 | **OGC API Features** pour exposition vectorielle (BD TOPO, cadastre) | P0 |
| API-17 | **OGC API Tiles** pour tuiles vectorielles/raster (Hub Cesium) | P0 |
| API-18 | **STAC API** pour catalogue datasets (LiDAR, imagerie) | P1 |
| API-19 | **pygeoapi** à évaluer pour exposition catalogique OGC | P1 |
| API-20 | **Clean architecture** : domain ← infra ← api, repository pattern | P0 |
| API-21 | **geojson-pydantic + pydantic-shapely** pour validation géométries | P0 |
| API-22 | **ForeFire** via HTTP (`listenHTTP[]`) + WebSocket fan-out | P0 |
| API-23 | **pytest-asyncio** mode auto + **testcontainers** pour intégration | P0 |
| API-24 | **OpenTelemetry** auto-instrumentation (FastAPI, SQLAlchemy, Redis) | P0 |
| API-25 | **Prometheus + Grafana + Loki + Jaeger** stack observabilité | P1 |
| API-26 | **Keycloak** comme IdP quand gestion users complexe (P1) | P1 |
| API-27 | **RBAC** : roles forestier, chercheur, admin, public | P0 |
| API-28 | **SlowAPI** rate limiting (P0) → Redis custom token bucket (P1) | P0 |
| API-29 | **Docker Compose** pour Phase 4 début, K8s si scale (Phase 5) | P0 |
| API-30 | **Gunicorn + UvicornWorker** pour production (workers = 2×CPU+1) | P0 |

---

## 11. Standards OGC API — conformité géospatiale

### 11.1 Pourquoi respecter les standards OGC

L'IGN, l'INRAE, Météo-France et tous les partenaires institutionnels
de GSIE publient leurs données via des standards OGC (Open Geospatial
Consortium). Respecter ces standards garantit :

- **interopérabilité** avec les sources existantes (WMS, WFS, OGC API)
- **découvrabilité** via les catalogues STAC et CSW
- **conformité réglementaire** (INSPIRE pour les données environnementales)
- **réutilisation** d'outils matures (QGIS, pygeoapi, GeoServer)

### 11.2 Standards OGC API pertinents pour GSIE

| Standard | Description | Cas GSIE | Priorité |
|---|---|---|---|
| **OGC API — Features** | REST API pour features vectorielles (successeur WFS) | BD TOPO, ADMIN-EXPRESS, cadastre, parcelles | P0 |
| **OGC API — Tiles** | Tuiles vectorielles/raster (successeur WMTS) | Hub Cesium, couches statiques | P0 |
| **OGC API — Processes** | Processus asynchrones (calculs, simulations) | ForeFire, Forest Dynamics, simulations | P1 |
| **OGC API — Coverages** | Rasters (successeur WCS) | MNT/MNS/MNH LiDAR, Climate rasters | P1 |
| **OGC API — Maps** | Cartes rendues (successeur WMS) | Cartes statiques, export PDF | P2 |
| **OGC API — Records** | Catalogue de métadonnées (successeur CSW) | Catalogue datasets GSIE | P2 |
| **STAC** | SpatioTemporal Asset Catalog | Catalogue LiDAR, imagerie, datasets | P1 |

### 11.3 Implémentation recommandée

| Approche | Description | Recommandation GSIE |
|---|---|---|
| **pygeoapi** | Serveur OGC API Python (OSGeo, reference implementation) | Évaluer pour exposition datasets (P1) |
| **GeoServer** | Serveur Java, mature, OGC complet | Trop lourd pour GSIE (Java), mais possible |
| **FastAPI + extensions** | Implémenter les endpoints OGC API directement | **P0** — contrôle total, intégration native |
| **pg_tileserv** | Serveur de tuiles PostGIS léger | P1 pour tuiles vectorielles dynamiques |
| **TiTiler** | Serveur de tuiles raster Python (rasterio) | P1 pour rasters (MNT, imagerie) |

> **Recommandation** : implémenter les endpoints OGC API Features et
> Tiles directement dans FastAPI (P0). Évaluer pygeoapi pour
> l'exposition catalogique des datasets (P1). STAC pour le catalogue
> LiDAR/imagerie (P1).

### 11.4 STAC pour le catalogue de datasets GSIE

STAC (SpatioTemporal Asset Catalog) est le standard de facto pour
cataloguer les assets géospatiaux. Il couvre : imagerie satellite,
LiDAR, DEM, SAR, hyperspectral, vidéos, nuages de points.

| Composant STAC | Rôle GSIE | Implémentation |
|---|---|---|
| **STAC Catalog** | Racine du catalogue | `pystac` (Python) |
| **STAC Collection** | Groupe d'assets (ex: LiDAR HD) | Une collection par dataset |
| **STAC Item** | Asset individuel (ex: une dalle LAZ) | Un item par fichier |
| **STAC API** | Recherche spatio-temporelle | FastAPI + `stac-fastapi` |
| **STAC Browser** | Interface web de navigation | `stac-browser` (JS) |

> **Implication GSIE** : le `DATASET_CATALOG.md` (29 datasets) peut
> être exposé en STAC API, permettant aux moteurs de découvrir
> automatiquement les assets disponibles. Le LiDAR HD IGN (DS-002)
> est un cas parfait pour STAC (dalles LAZ avec bbox + date).

---

## 12. Architecture de projet FastAPI — clean architecture

### 12.1 Structure recommandée (sources : guides production 2026)

```
gsie-api/
├── pyproject.toml              ← dépendances épinglées (T-10)
├── alembic/                    ← migrations DB
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── src/
│   └── gsie_api/
│       ├── __init__.py
│       ├── main.py             ← create_app() — app factory
│       ├── config.py           ← Pydantic Settings (env vars)
│       ├── dependencies.py     ← DI FastAPI (get_db, get_redis, get_engine)
│       │
│       ├── api/                ← couche présentation (routes)
│       │   ├── v1/
│       │   │   ├── __init__.py
│       │   │   ├── router.py   ← agrège tous les routers
│       │   │   ├── forest.py   ← /api/v1/forest
│       │   │   ├── climate.py  ← /api/v1/climate
│       │   │   ├── gis.py      ← /api/v1/gis
│       │   │   ├── ignis.py    ← /api/v1/ignis
│       │   │   ├── botanical.py
│       │   │   ├── knowledge.py
│       │   │   └── health.py   ← /health, /metrics
│       │   └── ws/             ← WebSocket endpoints
│       │       ├── ignis.py    ← /ws/ignis (front de feu)
│       │       ├── forest.py   ← /ws/forest (sync live)
│       │       └── sim.py      ← /ws/sim (ForeFire)
│       │
│       ├── domain/             ← couche domaine (logique métier)
│       │   ├── models/         ← entités domaine (Pydantic)
│       │   ├── repositories/   ← interfaces repositories (abstract)
│       │   └── services/       ← use cases / services
│       │
│       ├── infrastructure/     ← couche infrastructure
│       │   ├── database/       ← SQLAlchemy models, asyncpg
│       │   ├── redis/          ← Redis client, Pub/Sub
│       │   ├── engines/        ← pyo3 bindings (Rust)
│       │   └── external/       ← clients API externes (IGN, Météo-France)
│       │
│       ├── core/               ← transverse
│       │   ├── security.py     ← JWT, OAuth2
│       │   ├── logging.py      ← structlog + OpenTelemetry
│       │   ├── exceptions.py   ← exceptions domaine
│       │   └── middleware.py   ← rate limit, CORS, tracing
│       │
│       └── schemas/            ← DTOs (request/response Pydantic)
│
└── tests/
    ├── unit/                   ← tests unitaires (mock repositories)
    ├── integration/            ← tests intégration (DB réelle via testcontainers)
    └── e2e/                    ← tests end-to-end (httpx AsyncClient)
```

### 12.2 Principes clés (clean architecture)

| Principe | Application GSIE |
|---|---|
| **Dependency direction** | Domain ← Infrastructure ← API. Le domaine ne connaît pas l'infra |
| **Repository pattern** | Interfaces dans `domain/repositories/`, implémentations dans `infrastructure/database/` |
| **App factory** | `create_app()` dans `main.py` — pas d'app au niveau module |
| **Dependency injection** | FastAPI `Depends()` pour injecter sessions DB, Redis, engines |
| **DTOs aux boundaries** | `schemas/` pour request/response, `domain/models/` pour interne |
| **Pas de logique métier dans routes** | Routes = HTTP seulement, délèguent aux services |
| **Pas d'appels DB dans services** | Services utilisent les interfaces repositories |
| **Configuration via env vars** | `Pydantic Settings` — jamais hardcoded |

### 12.3 Pattern Dependency Injection FastAPI

```python
# dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def get_forest_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ForestService:
    return ForestService(
        repo=ForestRepository(db),
        cache=redis,
    )

# forest.py
@router.get("/trees/{tree_id}")
async def get_tree(
    tree_id: str,
    service: ForestService = Depends(get_forest_service),
) -> TreeResponse:
    return await service.get_tree(tree_id)
```

> **Implication GSIE** : cette structure respecte CON-007 (modularité),
> T-2 (couplage faible), et permet de tester chaque couche
> indépendamment. Les 14 moteurs sont des services injectés.

---

## 13. Validation géospatiale — Pydantic v2 + Shapely

### 13.1 Validation des géométries en entrée

Toute géométrie reçue par l'API (GeoJSON, WKT) doit être validée avant
traitement. Pydantic v2 (core Rust) exécute la validation à la vitesse C.

| Librairie | Rôle | Recommandation |
|---|---|---|
| **geojson-pydantic** | Modèles Pydantic pour GeoJSON (Point, LineString, Polygon, etc.) | P0 — validation structurale |
| **pydantic-shapely** | Intégration Pydantic ↔ Shapely (validation géométrique) | P0 — validation géométrique |
| **shapely** | Géométrie computationnelle (buffer, intersect, area) | P0 — déjà dans stack GIS |
| **pydantic-geojson** | Alternative pour parsing GeoJSON | P2 |

### 13.2 Pattern de validation

```python
from geojson_pydantic import Feature, Point
from pydantic import BaseModel, field_validator
from shapely.geometry import shape
from shapely.validation import explain_validity

class ForestPlotRequest(BaseModel):
    geometry: Feature
    area_min_ha: float

    @field_validator("geometry")
    @classmethod
    def validate_geometry(cls, v: Feature) -> Feature:
        geom = shape(v.geometry.dict())
        if not geom.is_valid:
            reason = explain_validity(geom)
            raise ValueError(f"Invalid geometry: {reason}")
        # Vérification bounds France métropolitaine
        if not (-5.5 < geom.bounds[0] < 8.5 and 41.0 < geom.bounds[1] < 51.5):
            raise ValueError("Geometry outside France bounds")
        return v
```

### 13.3 Sérialisation PostGIS

| Type | Conversion | Recommandation |
|---|---|---|
| GeoJSON → PostGIS | `shapely.wkb.dumps(geom, hex=True)` → `ST_GeomFromEWKT` | asyncpg natif |
| PostGIS → GeoJSON | `ST_AsGeoJSON(geom)` → parsing Pydantic | Query SQL |
| WKT | `shapely.wkt.dumps(geom)` | Pour logs/debug |

> **Recommandation** : utiliser `geojson-pydantic` + `pydantic-shapely`
> pour valider toutes les géométries en entrée. Validation à la vitesse
> C (Pydantic v2 core Rust), pas de bottleneck sur l'event loop.

---

## 14. asyncpg vs psycopg3 — analyse approfondie

### 14.1 Benchmark (source : MagicStack/asyncpg, tests 2026)

| Critère | asyncpg | psycopg3 | Verdict |
|---|---|---|---|
| **Performance brute** | **5x plus rapide** (moyenne) | Référence | asyncpg gagne |
| **Protocol** | Binary protocol natif | Libpq (C) | asyncpg plus efficace |
| **Prepared statements** | Natif, zero-copy | Supporté | asyncpg gagne |
| **Pydantic mapping** | Workaround (pas built-in) | **Intégration native** | psycopg3 gagne |
| **SQLAlchemy 2.0 async** | Supporté (driver recommandé) | Supporté | Égalité |
| **PostGIS** | **Recommandé** (binary, zero-copy) | Supporté | asyncpg gagne |
| **Maturité** | Production, MagicStack | Production, psycopg team | Égalité |
| **Communauté** | Active, 12K stars | Active, héritier psycopg2 | Égalité |

### 14.2 Verdict

| Cas | Driver recommandé | Raison |
|---|---|---|
| **PostGIS + performance** | **asyncpg** | Binary protocol, zero-copy, 5x plus rapide |
| **Pydantic mapping natif** | psycopg3 | Intégration built-in Pydantic |
| **SQLAlchemy 2.0 async** | asyncpg | Driver recommandé par SQLAlchemy |

> **Recommandation GSIE** : **asyncpg** comme driver principal
> (PostGIS = besoin critique, performance binaire). SQLAlchemy 2.0
> async avec driver asyncpg pour l'ORM. Pour les queries Pydantic
> directes, mapping manuel via `record_to_pydantic()`.

### 14.3 Configuration asyncpg + PgBouncer

```python
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine

# Engine SQLAlchemy 2.0 async avec asyncpg
engine = create_async_engine(
    "postgresql+asyncpg://gsie:pass@localhost:5432/gsie",
    pool_size=20,          # 20-40 par réplica (guide geospatial-api.com)
    max_overflow=10,
    pool_timeout=30,       # Évite blocage indéfini (asyncpg n'a pas de timeout natif)
    pool_recycle=3600,     # Évite connexions zombies
    echo=False,
)

# Statement timeout au niveau DB
# postgresql.conf: statement_timeout = '5s'
```

---

## 15. Intégration ForeFire — API simulation incendie

### 15.1 ForeFire — vue d'ensemble

| Caractéristique | Détail |
|---|---|
| **Développeur** | CNRS, Université de Corse (Jean-Baptiste Filippi) |
| **Licence** | Open-source (GitHub: forefireAPI/forefire) |
| **Langage** | C++ (core), Python bindings |
| **Interface HTTP** | `listenHTTP[]` — serveur HTTP intégré sur port 8000 |
| **Scripts** | Fichiers `.ff` (event-driven scripting language) |
| **Couplage atmosphère** | MesoNH (fire-atmosphere two-way coupling) |
| **Performance** | C++ optimisé, MPI pour parallélisme |
| **Adoption** | Autorités françaises, AriaFire, Ororatech, umgrauemeio (Pantera) |

### 15.2 Architecture d'intégration GSIE ↔ ForeFire

```
┌──────────────┐    HTTP/REST     ┌───────────────┐    C++ core    ┌──────────────┐
│  FastAPI     │ ───────────────→ │  ForeFire     │ ─────────────→ │  Simulation  │
│  /ws/sim     │                  │  HTTP server  │                │  propagation │
│  (WebSocket) │ ←─────────────── │  (port 8000)  │ ←───────────── │  (feu)       │
└──────────────┘   events JSON    └───────────────┘   front de feu  └──────────────┘
       │
       │  Redis Pub/Sub
       ↓
┌──────────────┐
│  Hub Unreal  │  ← front de feu temps réel (3D)
│  Ignis app   │  ← position du feu, ROS, direction
└──────────────┘
```

### 15.3 Pattern d'intégration

| Étape | Techno | Détail |
|---|---|---|
| 1. Lancement simulation | FastAPI → ForeFire HTTP | `POST /api/v1/ignis/simulate` → `include[scenario.ff]` |
| 2. Streaming front de feu | ForeFire → FastAPI WebSocket | ForeFire émet events, FastAPI relay via WebSocket |
| 3. Fan-out temps réel | FastAPI → Redis Pub/Sub → Hub | Multi-clients (Hub, Ignis app, dashboard) |
| 4. Couplage météo | Climate Engine → ForeFire | Wind triggers, température, humidité |
| 5. Couplage terrain | GIS Engine → ForeFire | MNT, végétation (fuel models), pente |

### 15.4 Recommandation ForeFire

| Aspect | Recommandation |
|---|---|
| **Déploiement** | Docker (ForeFire Super Console Docker disponible) |
| **Communication** | HTTP REST (ForeFire intégré) + WebSocket (fan-out) |
| **Python bindings** | Utiliser pour contrôle programmatique (start/stop/params) |
| **Scénarios** | Fichiers `.ff` générés par Simulation Engine |
| **Données fuel** | BD Forêt IGN + Crown-BERT → fuel models ForeFire |
| **Météo** | Climate Engine → wind/temperature/humidity → ForeFire triggers |

> **Implication GSIE** : ForeFire s'intègre naturellement via HTTP.
> L'API GSIE agit comme proxy entre ForeFire et les clients (Hub, Ignis).
> Le pattern WebSocket fan-out (Redis Pub/Sub) est directement
> applicable pour diffuser le front de feu.

---

## 16. Tests API — stratégie complète

### 16.1 Stack de test

| Outil | Rôle | Version cible |
|---|---|---|
| **pytest** | Runner de tests | 8.x |
| **pytest-asyncio** | Tests async (mode auto) | 0.24+ |
| **httpx** | Client HTTP async pour tests | 0.28+ |
| **pytest-cov** | Couverture de code | 5+ |
| **testcontainers-python** | PostgreSQL/Redis réels pour intégration | 4+ |
| **faker** | Données de test réalistes | 30+ |
| **pytest-xdist** | Tests parallèles | 3+ |

### 16.2 Configuration pytest

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
asyncio_mode = auto
addopts = -v --cov=src --cov-report=term-missing --cov-report=html
markers =
    unit: Unit tests (no external deps)
    integration: Integration tests (real DB/Redis via testcontainers)
    slow: Slow tests (simulations, large datasets)
```

### 16.3 Pattern de test (Arrange → Act → Assert)

```python
# tests/integration/test_forest.py
import pytest
from httpx import ASGITransport, AsyncClient
from gsie_api.main import create_app

@pytest.fixture
async def client():
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

async def test_get_tree_returns_200_when_tree_exists(client):
    # Arrange
    tree_id = "GSIE-T-0000000001"
    # Act
    response = await client.get(f"/api/v1/forest/trees/{tree_id}")
    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == tree_id
    assert response.json()["species"] == "Quercus robur"
```

### 16.4 Niveaux de test

| Niveau | Scope | Outils | Couverture cible |
|---|---|---|---|
| **Unitaire** | Services, repositories (mock) | pytest + pytest-mock | 80% (domain) |
| **Intégration** | DB réelle (testcontainers), Redis | pytest + testcontainers | 60% |
| **E2E** | API complète (HTTP + WebSocket) | httpx AsyncClient | Cas critiques |
| **Performance** | Charge, latence | locust | P99 < seuils |

> **Implication GSIE** : `asyncio_mode = auto` — tous les tests
> `async def test_*` sont automatiquement async. `testcontainers` pour
> PostgreSQL+PostGIS et Redis réels en intégration. Dependency
> overrides FastAPI pour isoler les couches.

---

## 17. Observabilité — OpenTelemetry

### 17.1 Les trois piliers

| Pilier | Outil | Rôle GSIE |
|---|---|---|
| **Metrics** | Prometheus | RPS, latence, erreurs, connexions DB |
| **Traces** | Jaeger / Grafana Tempo | Traçage distribué (CON-005) — request → moteur → DB |
| **Logs** | Loki / structlog | Logs structurés JSON avec `trace_id` + `span_id` |

### 17.2 Stack observabilité recommandée

```
FastAPI (instrumentée OpenTelemetry)
    │
    ├── Metrics ──→ Prometheus ──┐
    ├── Traces  ──→ Jaeger ──────┤
    └── Logs    ──→ Loki ────────┤
                                 ↓
                          Grafana Dashboard
                          (corrélation trace ↔ log ↔ metric)
```

### 17.3 Instrumentation FastAPI

| Composant | Librairie | Auto/Manuel |
|---|---|---|
| FastAPI routes | `opentelemetry-instrumentation-fastapi` | Auto |
| SQLAlchemy queries | `opentelemetry-instrumentation-sqlalchemy` | Auto |
| Redis | `opentelemetry-instrumentation-redis` | Auto |
| HTTP client (httpx) | `opentelemetry-instrumentation-httpx` | Auto |
| Logs structurés | `structlog` + injection `trace_id` | Manuel |
| Spans métier | `@tracer.start_as_current_span("forest.compute")` | Manuel |

### 17.4 Attention production

> Source : retour production 2026. L'auto-instrumentation OpenTelemetry
> peut causer un **backup de l'event loop** si l'exporter ne suit pas.
> Symptôme : pause de 150ms dans le handler, queue de spans qui
> déborde. Solution : configurer le batch exporter avec `max_queue_size`
> et `max_export_batch_size` appropriés, ou utiliser un OTLP collector
> local asynchrone.

### 17.5 Recommandation GSIE

| Aspect | Recommandation | Priorité |
|---|---|---|
| OpenTelemetry instrumentation | Auto (FastAPI, SQLAlchemy, Redis) | P0 |
| structlog + trace_id | Logs JSON corrélés aux traces | P0 |
| Prometheus metrics | RPS, latence, erreurs, pool DB | P0 |
| Grafana dashboard | 4 golden signals + drill-down | P1 |
| Jaeger traces | Debug latence inter-moteurs | P1 |
| Alerting | Alertmanager (latence P99, error rate) | P1 |

> **Implication GSIE** : OpenTelemetry est **vendor-neutral** (CNCF).
> Instrumenter une fois, changer de backend sans modifier le code.
> Respecte CON-005 (traçabilité) — toute requête est traçable de bout
> en bout (client → API → moteur → DB).

---

## 18. Authentification et sécurité

### 18.1 Stack auth recommandée

| Composant | Techno | Rôle | Priorité |
|---|---|---|---|
| **Token** | JWT (RS256) | Access 15min, Refresh 7d | P0 |
| **OAuth2** | Authorization Code + PKCE | Apps clientes (mobile, web) | P0 |
| **IdP** | Keycloak (self-hosted) | Identity provider, gestion utilisateurs | P1 |
| **API Keys** | Clés persistantes | Accès programmatique (partenaires) | P1 |
| **RBAC** | Roles + permissions | forestier, chercheur, admin, public | P0 |

### 18.2 Configuration JWT

| Paramètre | Valeur | Raison |
|---|---|---|
| Algorithme | RS256 (asymétrique) | Vérification sans secret partagé |
| Access token TTL | 15 minutes | Limite d'exposition (global_rules) |
| Refresh token TTL | 7 jours | Équilibre UX vs sécurité |
| Validation | Signature + expiration + claims | À chaque requête |
| Stockage client | HttpOnly cookie (web) / secure storage (mobile) | Pas de localStorage |

### 18.3 Keycloak vs alternatives

| Solution | Type | Avantages | Inconvénients | Verdict GSIE |
|---|---|---|---|---|
| **Keycloak** | Self-hosted | Open-source, mature, OAuth2/OIDC complet, RBAC | Ops overhead | **P1** (recommandé) |
| Auth0 | SaaS | Managed, excellent DX | Vendor lock-in, payant | ❌ (CON-008 souveraineté) |
| Supabase Auth | SaaS | Simple, PostgreSQL natif | Limité vs Keycloak | ❌ |
| FastAPI JWT natif | Built-in | Simple, pas d'infra | Pas de gestion utilisateurs | **P0** (début Phase 4) |

> **Recommandation** : FastAPI JWT natif pour Phase 4 début (P0).
> Keycloak quand la gestion utilisateurs devient complexe (P1).
> Pas de SaaS d'auth (CON-008 souveraineté des données).

### 18.4 Rate limiting

| Solution | Description | Recommandation |
|---|---|---|
| **SlowAPI** | Rate limiting FastAPI (basé sur Starlette) | P0 — simple, per-IP |
| **Redis custom** | Token bucket distribué | P1 — per-user, sliding window |
| **NGINX** | Rate limiting au niveau proxy | P1 — protection edge |

> **Note** : SlowAPI a des limitations (per-IP seulement, pas de
> sliding window, problèmes derrière reverse proxy). Pour la
> production, un rate limiter custom Redis (token bucket) est
> recommandé (P1).

---

## 19. Déploiement — Docker + production

### 19.1 Stack de déploiement

```
┌─────────────────────────────────────────────────────┐
│  Production                                          │
│                                                      │
│  NGINX (reverse proxy, TLS 1.3, rate-limit)         │
│    ↓                                                 │
│  Gunicorn (process manager)                         │
│    ├── UvicornWorker 1 (FastAPI)                    │
│    ├── UvicornWorker 2 (FastAPI)                    │
│    └── UvicornWorker N (FastAPI)                    │
│    ↓                                                 │
│  Docker (multi-stage build)                         │
│    ↓                                                 │
│  PostgreSQL + PostGIS + PgBouncer                   │
│  Redis 7+                                           │
│  OpenTelemetry Collector                            │
│  Prometheus + Grafana + Loki + Jaeger               │
└─────────────────────────────────────────────────────┘
```

### 19.2 Configuration Gunicorn + Uvicorn

| Paramètre | Valeur | Raison |
|---|---|---|
| Workers | `(2 × CPU cores) + 1` | Standard Gunicorn |
| Worker class | `uvicorn.workers.UvicornWorker` | ASGI support |
| Timeout | 120s | Simulations longues |
| Graceful timeout | 30s | Connexions WebSocket |
| Max requests | 1000 + jitter | Évite memory leaks |
| Preload app | `True` | Mémoire partagée entre workers |

### 19.3 Docker multi-stage

```dockerfile
# Stage 1: builder
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir build && python -m build --wheel

# Stage 2: runtime
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/dist/*.whl .
RUN pip install --no-cache-dir *.whl uvicorn[standard] gunicorn
COPY src/ ./src/
EXPOSE 8000
CMD ["gunicorn", "src.gsie_api.main:app", \
     "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "--timeout", "120"]
```

### 19.4 Recommandation déploiement GSIE

| Phase | Setup | Raison |
|---|---|---|
| **Phase 4 début** | Docker Compose (API + Postgres + Redis) | Développement, tests |
| Phase 4 milieu | Docker Compose + NGINX + observabilité | Staging/production léger |
| Phase 5 | Kubernetes (si scale) | Multi-répliques, autoscaling |

> **YAGNI** : Docker Compose suffit pour démarrer. Kubernetes seulement
> si le traffic ou la complexité l'exige (Phase 5).

---

## 20. Versioning API — stratégie

### 20.1 Approche recommandée

| Stratégie | Description | Recommandation GSIE |
|---|---|---|
| **URI versioning** | `/api/v1/...` | **✅ P0** — simple, explicite, cacheable |
| Header versioning | `Accept: application/vnd.gsie.v1+json` | ❌ — complexe, pas debuggable |
| Query param | `?version=1` | ❌ — fragile |
| Content negotiation | `Accept` header | ❌ — trop subtil |

### 20.2 Règles de versioning (CON-010 — évolution sans perte)

| Changement | Impact version | Action |
|---|---|---|
| Ajout endpoint | Aucun (backward compatible) | Pas de version bump |
| Ajout champ response | Aucun (backward compatible) | Pas de version bump |
| Suppression endpoint | **Breaking** | Nouvelle version majeure |
| Changement type champ | **Breaking** | Nouvelle version majeure |
| Changement comportement | **Breaking** | Nouvelle version majeure |

### 20.3 Cycle de vie des versions

| Version | Statut | Durée |
|---|---|---|
| Courante (`/api/v1/`) | Active | Indéfinie |
| Précédente (`/api/v1/` après v2) | Deprecation | 6 mois minimum |
| Obsolète | Retirée | Après déprecation |

> **Implication GSIE** : CON-010 impose que toute connaissance puisse
> évoluer sans perdre son historique. L'API suit le même principe :
> `v1` reste disponible pendant 6 mois après sortie de `v2`. Toute
> déprecation est documentée dans l'OpenAPI et signalée via header
> `Deprecation: true`.

---

## 21. Critères d'acceptation (mis à jour)

- [x] Framework Python comparé (FastAPI vs Litestar vs Django Bolt vs Django REST)
- [x] Benchmark 2026 analysé (RPS, latence, DB)
- [x] Architecture multi-protocole définie (REST + WebSocket + gRPC optionnel)
- [x] Stack géospatiale PostGIS documentée (asyncpg, PgBouncer, Redis, MVT)
- [x] Pattern temps réel géospatial défini (LISTEN/NOTIFY → Redis → WebSocket)
- [x] API Gateway évalué (Kong, Envoy, AWS, NGINX, Traefik, aucun)
- [x] Go vs Rust pour temps réel comparé (production 2026)
- [x] Stack Phase 4 P0 complète définie avec versions épinglées
- [x] Schéma architecture API GSIE produit
- [x] 15 recommandations initialisées pour livrable 401
- [x] Cohérence avec ADR-0001/0002/0003 vérifiée
- [x] Standards OGC API analysés (Features, Tiles, Processes, Coverages, STAC)
- [x] Structure projet FastAPI clean architecture définie
- [x] Validation géospatiale Pydantic v2 + Shapely documentée
- [x] asyncpg vs psycopg3 comparé en profondeur (5x plus rapide)
- [x] Intégration ForeFire documentée (HTTP, scripts .ff, fan-out WebSocket)
- [x] Stratégie de tests complète (pytest-asyncio, httpx, testcontainers)
- [x] Observabilité OpenTelemetry documentée (metrics, traces, logs corrélés)
- [x] Authentification JWT + Keycloak + RBAC + rate limiting
- [x] Déploiement Docker + Gunicorn + Uvicorn + NGINX
- [x] Versioning API URI `/api/v1/` + cycle de déprecation

---

> Statut : *Draft — fiche recherche Phase 4 pour livrable 401 (API GSIE).
> Confirme ADR-0001 (FastAPI) avec données 2026. Aucun code métier
> produit (CON-003). La connaissance est le véritable produit (GSIE-FND-001).*

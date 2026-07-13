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

---

## 11. Critères d'acceptation

- [x] Framework Python comparé (FastAPI vs Litestar vs Django Bolt vs Django REST)
- [x] Benchmark 2026 analysé (RPS, latence, DB)
- [x] Architecture multi-protocole définie (REST + WebSocket + gRPC optionnel)
- [x] Stack géospatiale PostGIS documentée (asyncpg, PgBouncer, Redis, MVT)
- [x] Pattern temps réel géospatial défini (LISTEN/NOTIFY → Redis → WebSocket)
- [x] API Gateway évalué (Kong, Envoy, AWS, NGINX, Traefik, aucun)
- [x] Go vs Rust pour temps réel comparé (production 2026)
- [x] Stack Phase 4 P0 complète définie avec versions épinglées
- [x] Schéma architecture API GSIE produit
- [x] 15 recommandations priorisées pour livrable 401
- [x] Cohérence avec ADR-0001/0002/0003 vérifiée

---

> Statut : *Draft — fiche recherche Phase 4 pour livrable 401 (API GSIE).
> Confirme ADR-0001 (FastAPI) avec données 2026. Aucun code métier
> produit (CON-003). La connaissance est le véritable produit (GSIE-FND-001).*

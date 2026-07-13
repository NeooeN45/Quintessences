# Fiche recherche — Validation architecture et plan Phase 4

| Champ | Valeur |
|---|---|
| **Document** | RESEARCH/PHASE4_ARCHITECTURE_VALIDATION |
| **Dossier** | GSIE/RESEARCH/ |
| **Phase** | 4 — Implémentation |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Méthode** | 3 subagents de recherche en parallèle (sources web 2025-2026) |
| **Documents connexes** | `API_TECHNOLOGY_RESEARCH.md`, `TECHNOLOGY_STACK.md` (ADR-0001/0002/0003), `ENGINE_DEVELOPMENT_ORDER.md` (livrable 204), `ENGINE_COMMUNICATION_PROTOCOL.md` (livrable 203) |
| **Décision cible** | DEC-000019 |

---

## 1. Objet

Consolider les 3 analyses de validation menées par subagents sur :
1. L'approche multi-langage (Python + Rust + Go optionnel)
2. L'architecture API FastAPI
3. Le plan d'implémentation Phase 4

Cette fiche synthétise les verdicts, identifie les ajustements, et
propose un plan révisé réaliste.

---

## 2. Verdicts synthétiques

| Analyse | Verdict | Ajustements |
|---|---|---|
| **Multi-langage** | ✅ Validé | Différer Go — MAVSDK-Go est PoC en 2026 |
| **Architecture API** | ✅ Validé | 5 ajustements P0/P1 (PgBouncer, pygeoapi, modules) |
| **Plan implémentation** | ❌ Refonte | 8 semaines → 24 semaines, dépendances à respecter |

---

## 3. Analyse 1 — Approche multi-langage

### 3.1 Verdict : ✅ Python + Rust validé, Go différé

L'approche 3 langages est **justifiée** mais Go doit être **différé**.

| Alternative | Verdict | Raison |
|---|---|---|
| All-Python | ❌ | Viole CON-002 (sécurité mémoire non négociable) |
| All-Rust | ❌ | Écosystème scientifique immature (pandas, rasterio absents) |
| Python+C++ | ⚠️ | Suboptimal — C++ introduit plus de risques mémoire que Rust |
| **Python+Rust** | ✅ | Couvre 95% des besoins. PyO3 mature en production |
| Python+Rust+Go | ✅ avec réserves | Go uniquement si besoin temps réel confirmé |

### 3.2 Preuves de production PyO3 2026

Polars, Ruff, Pydantic v2, Hugging Face tokenizers, orjson,
cryptography : **tous utilisent PyO3 en production**.

Systèmes ML hybrides Python+Rust : gains de **7.4x** mesurés
(source : Level Up Coding, juin 2026).

PyO3 v0.28 + maturin 1.8 : toolchain mature, API stable depuis v0.23.
Support free-threaded Python 3.14 (résout partiellement le GIL).

### 3.3 Go — pourquoi différer

| Critère | Constation | Source |
|---|---|---|
| MAVSDK-Go | **Proof of concept** en 2026 | MAVSDK Guide 2026 |
| MAVSDK-Python | **Used in production** | MAVSDK Guide 2026 |
| Rust axum/tokio | 3x plus rapide que Go, 47% moins de mémoire | Medium 2026 |
| Complexité stack | Un service Go supplémentaire = complexité ops | — |

**Recommandation** : commencer avec **FastAPI WebSocket + MAVSDK-Python**.
Si latence < 20ms requise → envisager **Rust axum** (pas Go).
Go uniquement si MAVSDK-Go atteint la maturité production **et** le
besoin est confirmé par benchmarks.

### 3.4 Pièges PyO3 en production

| Piège | Mitigation |
|---|---|
| **GIL contention** | `py.allow_threads()` systématique dans bindings Rust |
| **FFI overhead** | Profiler avant de déplacer code vers Rust (hot paths seulement) |
| **Debug cross-language** | structlog + trace_id, tests unitaires des deux côtés |
| **Build multi-plateforme** | maturin + CI/CD GitHub Actions pour wheels |

---

## 4. Analyse 2 — Architecture API

### 4.1 Verdict : ✅ Validé avec 5 ajustements

| # | Ajustement | Priorité | Impact |
|---|---|---|---|
| 1 | **Bypass PgBouncer** pour connexion LISTEN/NOTIFY dédiée | P0 | Bloquant temps réel |
| 2 | **asyncpg `statement_cache_size=0`** pour transaction pooling | P0 | Bloquant production |
| 3 | **pygeoapi comme lib Starlette** (pas standalone, pas from scratch) | P0 | Conformité OGC |
| 4 | **Architecture par modules moteurs** (pas DDD pur) | P1 | Maintenabilité |
| 5 | **fastgeoapi** à étudier P1 pour sécurité enterprise (OIDC+OPA) | P1 | Auth |

### 4.2 Points validés sans modification

| Choix | Verdict | Raison |
|---|---|---|
| FastAPI 0.115+ | ✅ | 4.5M+ téléchargements/jour, adopté par OpenAI/Anthropic/Microsoft |
| asyncpg (vs psycopg3) | ✅ | 5x plus rapide, recommandé sources géospatiales 2026 |
| LISTEN/NOTIFY → Redis → WebSocket | ✅ | Pattern éprouvé (LaunchDetect Academy 2026) |
| OpenTelemetry + Prometheus + Loki | ✅ | Overhead < 5% si configuré correctement |
| URI versioning `/api/v1/` | ✅ | Standard OGC API, cacheable, debuggable |
| Clean architecture | ✅ | Nécessaire pour 14 moteurs (monstre au-delà de 50 endpoints) |

### 4.3 Pièges production identifiés

| Piège | Solution |
|---|---|
| PgBouncer + LISTEN/NOTIFY | Connexion directe dédiée (bypass pooler) |
| Prepared statements + PgBouncer | `statement_cache_size=0` |
| Connection leaks SQLAlchemy async | DI avec `yield` + rollback automatique |
| `expire_on_commit=False` | Obligatoire pour async (accès après commit) |
| N+1 queries géospatiales | `selectinload` pour relations |
| WebSocket backpressure | Files bornées (MAX_QUEUE=100) |
| JWT refresh | Rotation avec reuse detection |

### 4.4 Architecture par modules moteurs (ajustement)

Au lieu de DDD pur, structurer par module moteur :

```
api/
├── core/           # Configuration, DI, logging
├── engines/        # 1 module par moteur
│   ├── evidence/   # api/ services/ repositories/ models/
│   ├── knowledge/
│   ├── gis/
│   └── ...
├── shared/         # Cross-cutting (auth, spatial utils)
└── infrastructure/ # DB, cache, external services
```

---

## 5. Analyse 3 — Plan d'implémentation

### 5.1 Verdict : ❌ Plan initial non réaliste, refonte nécessaire

| Problème | Sévérité | Correction |
|---|---|---|
| Knowledge Engine sauté | **Critique** | Respecter graphe dépendances livrable 204 |
| 6 moteurs Rust en 5 semaines (solo) | **Critique** | 12 semaines (2 semaines/moteur) |
| API après premier moteur Rust | **Élevé** | API en premier |
| Correlation avant moteurs domaine | **Élevé** | Respecter dépendances |
| ForeFire mal positionné | **Moyen** | Après Climate Engine |
| Durée totale 8 semaines | **Critique** | 24 semaines réaliste |

### 5.2 Graphe de dépendances (livrable 204 — à respecter strictement)

```
Evidence → Knowledge → [GIS, Botanical, Pedology, Climate]
                                ↓
                          Correlation
                                ↓
                          Reasoning
                                ↓
                          Diagnostic
                                ↓
              Forest Dynamics → Simulation
                                ↓
                          Recommendation
                                ↓
                          Validation
                                ↓
                          Learning (transverse, dernier)
```

### 5.3 Plan révisé (24 semaines, solo développeur)

#### Vague 1 — Fondations (Semaines 1-4)

| Semaine | Livrable | Langage | Justification |
|---|---|---|---|
| 1 | FastAPI (clean architecture) + Docker Compose | Python | Infrastructure de base |
| 2 | Evidence Engine + bindings pyo3 | Rust | Filtre amont, aucune dépendance |
| 3 | Knowledge Engine + bindings pyo3 | Rust | Centralise connaissances |
| 4 | Tests intégration API → Evidence → Knowledge | — | Valider pipeline |

#### Vague 2 — Moteurs domaine Python (Semaines 5-8)

| Semaine | Livrable | Langage | Justification |
|---|---|---|
| 5 | GIS Engine (LiDAR HD, MNT/MNS/MNH) | Python | rasterio/geopandas/PostGIS |
| 6 | Climate Engine (Météo-France, FWI) | Python | APIs météo Python |
| 7 | Botanical Engine (taxonomie, autécologie) | Python | Bases botaniques Python |
| 8 | Pedology Engine + intégration ForeFire (HTTP wrapper) | Python | Données sol + préparer Simulation |

#### Vague 3 — Cœur de raisonnement Rust (Semaines 9-14)

| Semaine | Livrable | Langage | Justification |
|---|---|---|
| 9-10 | Correlation Engine | Rust | Dépend de Knowledge + moteurs domaine |
| 11-12 | Reasoning Engine | Rust | Dépend de Knowledge, Correlation |
| 13-14 | Diagnostic Engine | Rust | Dépend de Reasoning + moteurs domaine |

#### Vague 4 — Moteurs avancés (Semaines 15-20)

| Semaine | Livrable | Langage | Justification |
|---|---|---|
| 15-16 | Forest Dynamics Engine | Python | Dépend de Knowledge, Correlation |
| 17-18 | Simulation Engine (ForeFire) | Python | Dépend de Forest Dynamics, Climate |
| 19-20 | Recommendation Engine | Rust | Dépend de Diagnostic, Simulation |

#### Vague 5 — Validation + Learning (Semaines 21-24)

| Semaine | Livrable | Langage | Justification |
|---|---|---|
| 21-22 | Validation Engine | Rust | Dépend de Recommendation, Diagnostic |
| 23-24 | Learning Engine | Rust | Transverse, dépend de tous |

#### Vague 6 — Évaluation Go (Semaines 25-26, optionnel)

| Semaine | Action | Critère |
|---|---|---|
| 25 | Benchmark WebSocket FastAPI (1000 connexions) | Latence, throughput |
| 26 | Décision Go + création gsie-realtime/ si activé | Seuil : > 100ms ou < 10k msg/s |

### 5.4 Risques et mitigations

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Courbe Rust sous-estimée | Élevée | Élevé | 2 semaines/moteur, plan de repli Python |
| Dépendances non respectées | Moyenne | Critique | Diagramme + tests d'intégration |
| ForeFire non intégré à temps | Moyenne | Élevé | Intégration semaine 8, mock pour tests |
| WebSocket perf insuffisante | Faible | Moyen | Benchmark semaine 25, Go si besoin |
| Solo développeur surchargé | Élevée | Critique | Prioriser P0, reporter P1 si nécessaire |

---

## 6. Synthèse — ce qui change vs plan initial

| Aspect | Plan initial | Plan révisé | Raison |
|---|---|---|---|
| **Durée** | 8 semaines | 24 semaines | Rust learning curve + dépendances |
| **Go** | Étape 8 (évaluation) | Semaine 25 (différé) | MAVSDK-Go est PoC |
| **API** | Étape 3 (semaine 2) | Semaine 1 (première) | API = point d'entrée |
| **Knowledge Engine** | Manquant | Semaine 3 (Rust) | Dépendance critique |
| **ForeFire** | Semaine 5 | Semaine 8 (après Climate) | Dépend de météo |
| **Rust pace** | 1 moteur/semaine | 1 moteur/2 semaines | Réaliste solo |
| **PgBouncer** | Non configuré | Bypass pour LISTEN + stmt_cache=0 | Piège production |
| **OGC API** | FastAPI from scratch | pygeoapi comme lib | Conformité garantie |
| **Architecture** | DDD pur | Modules par moteur | Pragmatique 14 moteurs |

---

## 7. Ce qui ne change pas (validé sans modification)

- **FastAPI 0.115+** comme framework API
- **Rust + pyo3** pour les 6 moteurs critiques du cœur IP
- **asyncpg + PostGIS + PgBouncer** pour la base géospatiale
- **Redis** pour cache + Pub/Sub + WebSocket fan-out
- **PostGIS LISTEN/NOTIFY → Redis → WebSocket** pour temps réel
- **OpenTelemetry + Prometheus + Loki** pour observabilité
- **JWT RS256 + RBAC** pour authentification
- **Docker Compose + Gunicorn + Uvicorn + NGINX** pour déploiement
- **URI versioning `/api/v1/`** pour versioning API
- **Clean architecture** (adaptée par modules moteurs)
- **30 recommandations** de la fiche API_TECHNOLOGY_RESEARCH.md

---

## 8. Recommandations finales

| ID | Recommandation | Priorité |
|---|---|---|
| VAL-01 | Valider le plan révisé 24 semaines (DEC-000019) | P0 |
| VAL-02 | Commencer par FastAPI + Docker Compose (semaine 1) | P0 |
| VAL-03 | Evidence Engine en Rust semaine 2 (premier moteur) | P0 |
| VAL-04 | Knowledge Engine en Rust semaine 3 (dépendance critique) | P0 |
| VAL-05 | Respecter strictement le graphe de dépendances (livrable 204) | P0 |
| VAL-06 | Différer Go — utiliser MAVSDK-Python + FastAPI WebSocket | P0 |
| VAL-07 | Bypass PgBouncer pour connexion LISTEN/NOTIFY dédiée | P0 |
| VAL-08 | asyncpg `statement_cache_size=0` pour PgBouncer transaction | P0 |
| VAL-09 | pygeoapi comme lib Starlette dans FastAPI (pas from scratch) | P0 |
| VAL-10 | Architecture par modules moteurs (pas DDD pur) | P1 |
| VAL-11 | `py.allow_threads()` systématique dans bindings Rust | P0 |
| VAL-12 | Profiler avant de déplacer code vers Rust (FFI overhead) | P1 |
| VAL-13 | 2 semaines par moteur Rust (realiste solo) | P0 |
| VAL-14 | ForeFire après Climate Engine (semaine 8) | P0 |
| VAL-15 | Benchmark WebSocket semaine 25 (décision Go) | P2 |

---

## 9. Sources

### Subagent 1 — Multi-langage
- PyO3 production : Nandann Creative Agency, DEV Community (Aegis), Medium (LiteLLM)
- Multi-language : GitHub (VLE, Shrew, Pulsar, Astrocyte, Ironkernel)
- Go vs Rust : Medium (3x faster), Abrarqasim, CallSphere, LevelUpGo
- MAVSDK-Go : pkg.go.dev, PX4 Guide, MAVSDK Guide 2026
- PyO3 GIL : PyO3 user guide, GitHub discussions

### Subagent 2 — Architecture API
- FastAPI clean architecture : zestminds.com, dev.to (2026 guides)
- PostGIS LISTEN/NOTIFY : LaunchDetect Academy 2026
- asyncpg vs psycopg3 : MagicStack/asyncpg, fernandoarteaga.dev, goldlapel.com
- pygeoapi : pygeoapi.io, OSGeo, OGC reference implementation
- fastgeoapi : GeoBeyond (FastAPI + pygeoapi + OIDC + OPA)
- OpenTelemetry : SigNoz, DEV Community, prodevs.in
- OGC API Features : ogc.org, opengeospatial/ogcapi-features

### Subagent 3 — Plan implémentation
- Rust learning curve : Rustify 2026, PyO3 guide, "Surviving the Rust Learning Curve 2026"
- Solo developer scientific : "From Zero to 5 AI Products: Solo Developer Journey"
- FastAPI setup : zestminds.com, oneuptime.com, dev.to (2026 guides)
- Engine dependencies : ENGINE_DEVELOPMENT_ORDER.md (livrable 204)

---

> Statut : *Draft — synthèse de 3 analyses par subagents (sources web 2025-2026).
> Alimente DEC-000019 (validation architecture + plan révisé Phase 4).
> Aucun code métier produit (CON-003).*

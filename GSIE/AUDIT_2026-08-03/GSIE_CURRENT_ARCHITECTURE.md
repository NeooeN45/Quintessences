# Architecture courante du GSIE Server

| Champ | Valeur |
|---|---|
| Document | GSIE_CURRENT_ARCHITECTURE.md |
| Livrable | #1 — Cartographie de l'architecture courante |
| Audit | 2026-08-03 |
| Périmètre | GSIE Server (`GSIE/API/`) et écosystème d'applications clientes |
| Phase projet | Phase 4 — Implémentation (ouverte par `DEC-000017`) |
| Méthode | 4 subagents en exploration parallèle : modules plateforme, moteurs, infrastructure, écosystème |
| Statut | Draft |

---

## 1. Stack technique

Extrait de `GSIE/API/pyproject.toml`.

| Couche | Technologie | Version |
|---|---|---|
| Langage | Python | 3.12 |
| Framework HTTP | FastAPI | 0.115.6 |
| Validation | Pydantic | 2.10.4 |
| ORM | SQLAlchemy (async) | 2.0.36 |
| Driver PostgreSQL | asyncpg | 0.30.0 |
| Base de données | PostgreSQL | 16 |
| Spatial | PostGIS | 3.4 |
| Graphe (Cypher) | Apache AGE | — |
| Vecteur | pgvector | — |
| Cache / Pub/Sub | Redis | 7.2 |
| Migrations | Alembic | 1.14.0 |
| Logging | structlog | — |
| Métriques | Prometheus | — |
| Tracing | OpenTelemetry | — |
| Authentification | JWT RS256 | — |
| Hachage mots de passe | Argon2id | — |
| Rate limiting | slowapi | — |
| Isolation multi-tenant | RLS PostgreSQL | — |
| Evidence Engine (cœur) | Rust (gsie_evidence) | — |
| Liaison Rust ↔ Python | PyO3 / Maturin | — |

Dépendances notables **absentes** : Keycloak, Stripe, Vault.

---

## 2. Structure du dépôt

Racine du serveur : `GSIE/API/src/gsie_api/`.

```
app.py                          Factory FastAPI, 23 routers (422 lignes)
core/                           config.py, auth.py, rbac.py, limiter.py, logging.py
auth/                           identity.py, identity_router.py, repository.py,
                                router.py (legacy), google_identity.py, google_nonces.py,
                                account_lifecycle.py, refresh_tokens.py,
                                transactional_email.py, schemas.py
sync/                           geosylva.py, repository.py, router.py, schemas.py
audit/                          router.py (STUB), schemas.py
governance/                     source_registry.py
infrastructure/                 database.py, db_privileges.py, health.py,
                                object_storage.py, redis_client.py,
                                knowledge_models.py (legacy v6.1),
                                models/ (24 fichiers, 73 types métamodèle v6.2)
resources/                      service.py, router.py, schemas.py, coercion.py, validators.py
ingestion/                      bulk.py
metrics/                        db_quality.py
websocket/                      manager.py, router.py, events.py
seeds/                          run_seeds.py, *_data.py (DRAFT)
gamification/                   router.py, schemas.py (PROTOTYPE)
shared/                         http_client.py, middleware.py, schemas.py
engines/                        14 moteurs (voir §5)
```

---

## 3. Cartographie des modules plateforme

| Module | Lignes | Statut | Notes clés |
|---|---|---|---|
| `core/` | ~1082 | PRODUCTION_READY | JWT RS256, RBAC, rate limiting, secrets chiffrés |
| `auth/` | ~2408 | FUNCTIONAL_BUT_INCOMPLETE | Compte canonique OK ; double système `router.py` (legacy) + `identity_router.py` ; pas d'organisations/workspaces ; pas de MFA |
| `sync/` | ~511 | FUNCTIONAL_BUT_INCOMPLETE | GeoSylva parcelles uniquement ; push mobile→serveur ; pas de pull, pas d'outbox, pas d'event bus |
| `audit/` | ~142 | STUB | Données statiques hardcoded ; pas de persistance ; pas de middleware |
| `governance/` | ~354 | FUNCTIONAL | Registre déclaratif des sources scientifiques ; porte programmatique `require_ingestible` |
| `infrastructure/` | ~6072 | PRODUCTION_READY | RLS, 31 migrations, health checks ; `S3Storage` lève `NotImplementedError` |
| `resources/` | ~1843 | PRODUCTION_READY | CRUD générique 73 types ; protection mass-assignment ; coercion |
| `ingestion/` | ~265 | PRODUCTION_READY | Bulk 1000 items, SAVEPOINT, RBAC |
| `metrics/` | ~300 | PRODUCTION_READY | Prometheus custom ; pas de métriques performance/business |
| `websocket/` | ~658 | PRODUCTION_READY | Redis Pub/Sub, RBAC par canal ; pas de persistance des messages |
| `seeds/` | ~2902 | DRAFT | Refus v6.1 ; données v6.2 prêtes mais non migrées |
| `gamification/` | ~150 | PROTOTYPE | Données statiques ; pas de moteur |
| `shared/` | ~691 | PRODUCTION_READY | `ResilientHttpClient` (5 modes panne), middleware `trace_id` |

---

## 4. Les 14 moteurs GSIE

Chaîne principale :

```
Evidence → Knowledge → Correlation → Reasoning → Diagnostic
→ Recommendation → Validation → Utilisateur
```

Moteurs domaine : GIS, Climate, Pedology, Botanical, Forest Dynamics.
Moteurs transverses : Learning, Simulation.

| Moteur | Lignes | Statut | Tests | Sources externes |
|---|---|---|---|---|
| `botanical` | ~1892 | PRODUCTION_READY | 3 | GBIF, Taxref, PlantNet, Treekipedia, Wikimedia, Bellifa |
| `climate` | ~1972 | PRODUCTION_READY | 5 | Météo-France (SYNOP, AROME, DPClim, Vigilance, Météo des forêts) |
| `correlation` | ~596 | FUNCTIONAL_BUT_INCOMPLETE | 4 | scipy, numpy |
| `diagnostic` | ~1289 | PRODUCTION_READY | 11 | Aucune (assemblage) |
| `evidence` | ~701 | PRODUCTION_READY | 8 | Rust (`gsie_evidence`) + fallback Python |
| `forest_dynamics` | ~718 | FUNCTIONAL_BUT_INCOMPLETE | 1 | Géométrie pure |
| `gis` | ~1143 | PRODUCTION_READY | 3 | IGN (Carto, Altimétrie, Téléchargement) |
| `knowledge` | ~1189 | PRODUCTION_READY | 5 | PostgreSQL (graphe v6.2) |
| `learning` | ~418 | PROTOTYPE | 1 | Aucune (cache mémoire) |
| `orchestration` | ~486 | PRODUCTION_READY | 7 | Branchement 4 moteurs |
| `pedology` | ~447 | PRODUCTION_READY | 2 | SoilGrids (ISRIC) |
| `reasoning` | ~1183 | PRODUCTION_READY | 5 | AST (évaluateur sûr) |
| `recommendation` | ~1105 | PRODUCTION_READY | 4 | PostgreSQL |
| `simulation` | ~551 | PROTOTYPE | 0 | Modèle linéaire v1 |
| `validation` | ~625 | PRODUCTION_READY | 7 | Contrôles constitutionnels |

Synthèse des statuts :

| Statut | Nombre |
|---|---|
| PRODUCTION_READY | 10 |
| FUNCTIONAL_BUT_INCOMPLETE | 2 |
| PROTOTYPE | 2 |

---

## 5. Routes API

### 5.1 Routers montés (`app.py`)

23 routers montés sous `/api/v1` :

| Domaine | Endpoints |
|---|---|
| Santé | `health` |
| Auth (legacy) | `auth` |
| Identité (nouveau) | `identity` |
| Ressources | `resources` |
| Sync | `sync` |
| Gamification | `gamification` |
| Audit | `audit` |
| Moteurs (14) | `evidence`, `knowledge`, `correlation`, `gis`, `botanical`, `pedology`, `forest_dynamics`, `climate`, `reasoning`, `diagnostic`, `recommendation`, `validation`, `simulation`, `learning`, `orchestration` |
| WebSocket | `/ws/hub`, `/ws/events` |

### 5.2 Routes identité (`identity_router.py`)

12 endpoints :

| Endpoint | Méthode |
|---|---|
| `/providers` | GET |
| `/register` | POST |
| `/login/password` | POST |
| `/google/nonce` | POST |
| `/login/google` | POST |
| `/link/google` | POST |
| `/email/verification/request` | POST |
| `/email/verification/confirm` | POST |
| `/password/reset/request` | POST |
| `/password/reset/confirm` | POST |
| `/me` | GET |
| `/me` | PATCH |

### 5.3 Routes sync (`sync/router.py`)

3 endpoints :

| Endpoint | Méthode |
|---|---|
| `/sync/geosylva/parcelles/{client_id}` | PUT |
| `/sync/geosylva/parcelles/{client_id}` | DELETE |
| `/sync/geosylva/parcelles` | GET |

---

## 6. Tables DB critiques

| Table | Schéma | Rôle |
|---|---|---|
| `user_account` | `gsie_rgpd_identites` | Compte canonique (RFC-0032) |
| `identity_provider_link` | `gsie_rgpd_identites` | Moyens de connexion |
| `local_credential` | `gsie_rgpd_identites` | Credentials locaux |
| `geosylva_parcels` | `gsie_synchronisation` | Sync parcelles (RLS par `account_id`) |
| `resource` | — | Table racine, 73 types (class-table inheritance, ADR-001) |

Tables **absentes** : `audit_log`, `organisation`, `workspace`.

---

## 7. Écosystème d'applications

| App | Statut | Auth Quintessences | Sync | Notes |
|---|---|---|---|---|
| ADMIN_WEB | FUNCTIONAL_BUT_INCOMPLETE | Non | N/A | Astro 5.13 + React 19 + Tailwind 4 ; mode mock |
| API GSIE | PRODUCTION_READY (core) | Oui | Oui (push GeoSylva) | 23 routers, 166+ tests |
| GeoSylva | PRODUCTION_READY (locale) | Oui | Oui (push), Non (pull) | Kotlin/Compose, 420+ tests, Room + SQLCipher |
| Ignis | PROTOTYPE | Non | Non | Banc d'essai ForeFire + PX4 + Gazebo |
| Artemis | STUB | Non | Non | README uniquement |
| Flora | STUB | Non | Non | README uniquement |
| Hydro | STUB | Non | Non | README uniquement |
| Terra | DOCUMENTATION_ONLY | Non | Non | Dossier inexistant |
| Atmos | DOCUMENTATION_ONLY | Non | Non | Dossier inexistant |

---

## 8. Conformité enterprise

Évaluation selon 6 piliers.

| Pilier | Statut | Observations |
|---|---|---|
| Reliability | PARTIEL | `ResilientHttpClient` (5 modes panne) ; health checks ; pas de circuit breaker global ; pas de retries sur DB |
| Security | PARTIEL | JWT RS256, Argon2id, RLS multi-tenant, rate limiting ; pas de MFA ; pas de rotation automatique des secrets ; `S3Storage` non implémenté |
| Observability | PARTIEL | structlog, Prometheus, OpenTelemetry, `trace_id` middleware ; pas de métriques business ; pas de dashboarding |
| Administrability | INSUFFISANT | Pas d'organisations/workspaces ; pas de table `audit_log` ; module `audit/` en STUB ; pas d'admin API |
| Testability | PARTIEL | 166+ tests API ; couverture inégale sur moteurs (0 pour `simulation`, 1 pour `forest_dynamics` et `learning`) ; pas de tests E2E |
| Scalability | PARTIEL | Async partout, Redis Pub/Sub pour WebSocket fan-out ; pas de sharding ; pas de partitioning ; pas de file de messages |

---

## 9. Synthèse

### 9.1 Ce qui est prêt

- **Cœur API** : factory FastAPI, 23 routers, 166+ tests, configuration centralisée.
- **10 moteurs sur 14** en statut PRODUCTION_READY, dont toute la chaîne principale (Evidence → Knowledge → Correlation → Reasoning → Diagnostic → Recommendation → Validation).
- **Infrastructure** : RLS multi-tenant, 31 migrations Alembic, health checks, Redis (cache + Pub/Sub + refresh tokens + nonces Google).
- **Ressources** : CRUD générique sur 73 types métamodèle v6.2, protection mass-assignment, coercion.
- **Authentification** : compte canonique (RFC-0032), JWT RS256, Argon2id, Google OAuth, refresh tokens.
- **Sync GeoSylva** : push parcelles mobile→serveur avec RLS.
- **Application GeoSylva** : PRODUCTION_READY en local, 420+ tests.

### 9.2 Ce qui manque

- **Authentification** : double système de routers (legacy + nouveau) à consolider ; pas de MFA ; pas d'organisations ni de workspaces.
- **Audit** : module en STUB, données statiques, pas de persistance, pas de middleware. Table `audit_log` absente.
- **Sync** : pas de pull serveur→mobile, pas d'outbox, pas d'event bus.
- **Stockage objets** : `S3Storage` lève `NotImplementedError`.
- **Moteurs incomplets** : `correlation` et `forest_dynamics` (FUNCTIONAL_BUT_INCOMPLETE) ; `learning` et `simulation` (PROTOTYPE, 0–1 test).
- **Seeds** : données v6.2 prêtes mais non migrées ; refus v6.1.
- **Observabilité** : pas de métriques business ni de dashboarding.
- **Scalabilité** : pas de sharding, pas de partitioning, pas de file de messages.
- **Gamification** : prototype statique, pas de moteur.
- **Écosystème** : Artemis, Flora, Hydro en STUB ; Terra et Atmos sans dossier ; ADMIN_WEB en mode mock sans authentification Quintessences.

---

*Fin du livrable #1.*

# GSIE API — General System Intelligence Engine

API REST/WebSocket du moteur GSIE. Phase 4 — Implémentation.
Métamodèle v6.2 — 73 types noyau et extensions métier, table racine `resource`, CRUD générique.

## Stack technique (DEC-000019, DEC-000023)

- **FastAPI 0.115+** — framework API REST + WebSocket
- **asyncpg + SQLAlchemy 2.0 async** — PostgreSQL 16 + PostGIS
- **GeoAlchemy2** — support géométrie PostGIS (Place, SRID 2154)
- **Redis 7.2** — cache + Pub/Sub + WebSocket fan-out inter-workers
- **Pydantic v2** — validation (core Rust)
- **OpenTelemetry** — observabilité (CON-005)
- **JWT RS256 + RBAC** — authentification (HTTP + WebSocket)
- **slowapi** — rate limiting (OWASP A07)
- **Cloudflare Tunnel optionnel** — bordure Zero Trust sans port Internet entrant (DEC-000047)

## Métamodèle v6.2 (RFC-0011, RFC-0012, ADR-007)

L'API est alignée sur le métamodèle v6.2 qui définit **73 types noyau**
organisés en 5 niveaux :

1. **Identité et référentiels** (1-8) — Entity, Concept, Vocabulary, Instance
2. **Assertions et connaissances** (9-13) — Assertion, Predicate, EvidenceAssessment
3. **Observations et mesures** (14-19) — Observation, Result, Method, Uncertainty
4. **Provenance et activités** (20-24) — Activity, Agent, Source, Citation
5. **Contextes** (25-28) — Unit, Place, TemporalContext, Media
6. **Versionnement** (29-30, 61) — Revision, Snapshot, ResourceDiff
7. **Modèles et datasets** (31-36, 41, 50-52) — Model, Dataset, Feature, Inference
8. **Confidentialité** (37-40, 42) — Rights, Access, Sensitivity, Conflict
9. **Écologie** (43-49) — ScaleContext, Phenomenon, EcologicalProcess, Trait
10. **Raisonnement** (53-60) — Question, Decision, Recommendation, Scenario
11. **FAIR/RGPD** (62-65) — Sample, Consent, DataSubject, PersistentIdentifier
12. **Dynamiques** (66-73) — Flow, Goal, Constraint, Experiment, EcologicalState

Toute resource a une ligne dans la table racine `resource` (ADR-001) +
une ligne dans sa table spécifique (class-table inheritance).

## Endpoints

### Identité Quintessences (RFC-0032 / DEC-000044 à DEC-000046)

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/auth/providers` | Moyens de connexion réellement disponibles |
| POST | `/api/v1/auth/register` | Créer un compte local par e-mail et mot de passe |
| POST | `/api/v1/auth/login/password` | Se connecter avec un compte local |
| POST | `/api/v1/auth/google/nonce` | Créer un nonce Google à usage unique |
| POST | `/api/v1/auth/login/google` | Se connecter ou créer un compte avec Google |
| POST | `/api/v1/auth/link/google` | Rattacher Google au compte GSIE courant |
| GET | `/api/v1/auth/me` | Consulter le profil du compte courant |
| PATCH | `/api/v1/auth/me` | Modifier le nom affiché |
| POST | `/api/v1/auth/email/verification/request` | Demander un code de vérification |
| POST | `/api/v1/auth/email/verification/confirm` | Confirmer l'adresse électronique |
| POST | `/api/v1/auth/password/reset/request` | Demander une récupération anti-énumération |
| POST | `/api/v1/auth/password/reset/confirm` | Définir un nouveau mot de passe et révoquer les anciennes sessions |
| POST | `/api/v1/auth/refresh` | Rotation du refresh token, tous fournisseurs |
| GET | `/api/v1/auth/verify` | Vérifier un access token GSIE |
| POST | `/api/v1/auth/logout` | Révoquer un refresh token |

Les comptes persistés vivent dans `gsie_rgpd_identites`. Google est fermé
tant que `GSIE_GOOGLE_OAUTH_CLIENT_IDS` est vide. Le login de développement
historique `/auth/login` reste interdit en staging et production.

En développement, `docker compose up -d mailpit` expose l'interface captive
sur <http://localhost:8025> et le SMTP uniquement dans le réseau Compose.
Avant toute ouverture publique, configurer `GSIE_SMTP_HOST`, les identifiants
du relais et STARTTLS ou TLS direct ; Mailpit ne doit jamais recevoir de
données réelles.

La publication de production passe par le profil `edge` :

```bash
docker compose --profile edge up -d cloudflared
```

Le token est fourni par fichier secret hors Git. Le protocole public,
l'isolement du plan de contrôle et la rotation sont décrits dans
[`docs/CLOUDFLARE_ZERO_TRUST.md`](docs/CLOUDFLARE_ZERO_TRUST.md).

### CRUD générique (ADR-007)

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/resources/types` | Liste autorisée des types enregistrés |
| GET | `/api/v1/resources` | Liste paginée (filtre par type) |
| POST | `/api/v1/resources` | Créer une resource (Revision v1) |
| GET | `/api/v1/resources/{id}` | Détail d'une resource |
| PUT | `/api/v1/resources/{id}` | Mettre à jour (Revision + ResourceDiff) |
| DELETE | `/api/v1/resources/{id}` | Soft delete (Revision finale, CON-010) |
| GET | `/api/v1/resources/{id}/revisions` | Historique des révisions |

### WebSocket (temps réel Hub UE5.8)

| Endpoint | Description |
|---|---|
| `/api/v1/ws/hub` | Canal temps réel Hub (token JWT en query param) |
| `/api/v1/ws/events` | Events système (resource.created, etc.) |

### Moteurs (legacy v6.1 — migration en Vague 2)

| Endpoint | Description |
|---|---|
| `/api/v1/evidence/*` | Evidence Engine (conservé) |
| `/api/v1/knowledge/*` | Knowledge Engine (migration Vague 2) |
| `/api/v1/gis/*` | GIS Engine (placeholder) |

## Démarrage rapide

```bash
# 1. Copier la configuration et définir les secrets
cp .env.example .env
# Éditer .env : GSIE_DB_PASSWORD, GSIE_REDIS_PASSWORD, GSIE_AUTH_DEV_PASSWORD

# 2. (Optionnel) Générer les clés JWT RS256 pour la production
./docker/generate-jwt-keys.sh

# 3. Démarrer les dépendances, sans muter implicitement le schéma
docker compose up -d db redis

# 4. Appliquer explicitement la baseline sur une base neuve.
#    Une ancienne base locale Alembic 0001-0013 doit être recréée.
docker compose run --rm \
  -e GSIE_RUN_MIGRATIONS_ON_STARTUP=true \
  api true

# 5. Démarrer l'API, le worker outbox et le courrier local captif
docker compose up -d api outbox-worker mailpit

# 6. Vérifier l'API
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/docs

# 7. Authentification persistée locale
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "forestier@example.fr", "password": "un-mot-de-passe-long-et-unique"}'

# Login historique réservé au développement
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-dev-password"}'
```

## Développement local (sans Docker pour l'API)

```bash
# 1. Installer les dépendances
pip install -e ".[dev]"

# 2. Lancer PostgreSQL + Redis via Docker
docker compose up -d db redis

# 3. Appliquer explicitement les migrations
alembic upgrade head

# 4. Lancer l'API en mode dev
uvicorn gsie_api.app:app --reload --port 8000

# 5. Tests
pytest
```

## Contrat de migration

- La lignée officielle commence à `20260726_0001`, baseline immuable du schéma
  GSIE v6.2 (116 tables applicatives).
- Une ancienne base locale marquée `0001` à `0013` n'est pas compatible : elle
  doit être recréée, aucune donnée historique n'étant à conserver.
- Toute évolution future crée une nouvelle révision Alembic autonome ; la
  baseline ne doit jamais être réécrite ni importer les modèles applicatifs.
- La CI exécute réellement `upgrade head`, `downgrade base`, puis un second
  `upgrade head` sur PostgreSQL 16 avec PostGIS et Apache AGE.

## Architecture (clean architecture par modules moteurs)

```
src/gsie_api/
├── app.py                  # Factory FastAPI
├── core/                   # Config, logging, auth, health
├── engines/                # 1 module par moteur
│   ├── evidence/           # Rust + pyo3 (semaine 2)
│   ├── knowledge/          # Rust + pyo3 (semaine 3 — migration Vague 2)
│   └── gis/                # Python natif (semaine 5)
├── resources/              # CRUD générique des types enregistrés (ADR-007)
│   ├── router.py           # 8 endpoints REST
│   ├── service.py          # Logique CRUD + Revision + broadcast WS
│   ├── schemas.py          # DTOs Pydantic
│   └── validators.py       # Validation dynamique par type
├── websocket/              # WebSocket temps réel (Hub UE5.8)
│   ├── router.py           # /ws/hub + /ws/events (auth JWT)
│   ├── manager.py          # ConnectionManager + Redis Pub/Sub
│   └── events.py           # Event types (resource.created, alert, etc.)
├── shared/                 # Middleware (TraceId, CORS, Gzip)
└── infrastructure/         # DB, Redis, models
    ├── models/             # Types noyau + extensions SQLAlchemy par domaine
    │   ├── base.py         # Table racine resource + registry @register_type
    │   ├── enums.py        # 52 enums PostgreSQL
    │   ├── junctions.py    # 17 tables de jonction n:m
    │   ├── outbox.py       # Outbox/Inbox (ADR-005)
    │   └── [domaine].py    # provenance, assertion, observation, etc.
    ├── database.py         # SQLAlchemy async engine
    ├── redis_client.py     # Pool Redis
    └── object_storage.py   # Abstraction S3/local (ADR-006)
```

## Plan d'implémentation (DEC-000019 — 24 semaines)

| Semaine | Livrable | Langage |
|---|---|---|
| 1 | FastAPI + Docker Compose (ce dépôt) | Python |
| 2 | Evidence Engine + pyo3 | Rust |
| 3 | Knowledge Engine + pyo3 | Rust |
| 5 | GIS Engine | Python |
| ... | Voir ROADMAP.md | ... |

## Conventions

- **Commits** : Conventional Commits (`feat(api): ...`)
- **Tests** : pytest-asyncio, 80% coverage sur domain
- **Linting** : ruff + mypy strict
- **Sécurité** : aucun secret en clair, JWT RS256, paramétré via .env

## Documentation

- [Application du manifeste Data Registry](docs/data/GSIE_DATA_REGISTRY_MANIFEST_APPLICATION_2026-08-10.md) —
  dry-run, application transactionnelle, santé réelle persistée, idempotence
  et limites `metadata_only`/`FETCH`.
- [Test réel Data Registry](docs/data/GSIE_DATA_E2E_REAL_TEST_2026-08-10.md) —
  acquisition publique, normalisation, archivage MinIO, round-trip checksum et
  sélection par le resolver.
- [Guide d'exploitation Outbox](docs/OUTBOX_EXPLOITATION.md) — cycle de
  vie, métriques Prometheus, procédure de ré-enfilement
- [Rotation des clés JWT](docs/JWT_KEY_ROTATION.md) — procédure de
  rotation RSA et contrainte multi-clés (pas de `kid`/JWKS natif)
- [Parallélisation pytest (xdist)](docs/TESTING_XDIST.md) — état,
  contraintes (scipy DLL, fuite SQLAlchemy) et usage manuel

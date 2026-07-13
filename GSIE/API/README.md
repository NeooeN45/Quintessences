# GSIE API — General System Intelligence Engine

API REST/WebSocket du moteur GSIE. Phase 4 — Implémentation (semaine 1).

## Stack technique (DEC-000019)

- **FastAPI 0.115+** — framework API REST + WebSocket
- **asyncpg + SQLAlchemy 2.0 async** — PostgreSQL + PostGIS
- **Redis 7.2** — cache + Pub/Sub + WebSocket fan-out
- **Pydantic v2** — validation (core Rust)
- **OpenTelemetry** — observabilité (CON-005)
- **JWT RS256 + RBAC** — authentification

## Démarrage rapide

```bash
# 1. Copier la configuration
cp .env.example .env

# 2. Lancer les services (PostgreSQL+PostGIS, Redis, API)
docker compose up -d

# 3. Vérifier l'API
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## Développement local (sans Docker pour l'API)

```bash
# 1. Installer les dépendances
pip install -e ".[dev]"

# 2. Lancer PostgreSQL + Redis via Docker
docker compose up -d db redis

# 3. Lancer l'API en mode dev
uvicorn gsie_api.app:app --reload --port 8000

# 4. Tests
pytest
```

## Architecture (clean architecture par modules moteurs)

```
src/gsie_api/
├── app.py                  # Factory FastAPI
├── core/                   # Config, logging, health
├── engines/                # 1 module par moteur
│   ├── evidence/           # Rust + pyo3 (semaine 2)
│   ├── knowledge/          # Rust + pyo3 (semaine 3)
│   └── gis/                # Python natif (semaine 5)
├── shared/                 # Schemas, middleware (cross-cutting)
└── infrastructure/         # DB, Redis, models
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

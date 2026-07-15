---
name: deploiement
description: Checklist de déploiement GSIE — Docker, CI/CD, vérifications pré-prod, rollback
triggers:
  - user
  - model
---

# Déploiement GSIE — Checklist

## Pré-déploiement (obligatoire)

### Code
- [ ] Tous les tests passent : `pytest GSIE/ --cov=GSIE --cov-fail-under=80`
- [ ] Mypy strict : `mypy GSIE/ --strict` — 0 erreur
- [ ] Ruff : `ruff check GSIE/` — 0 erreur
- [ ] Aucun TODO/FIXME dans le code à déployer
- [ ] Aucun secret dans le code (`git log -S "SECRET" --oneline`)

### Sécurité (skill /securite-gsie)
- [ ] `pip audit` — aucun CVE non mitigé
- [ ] Auth JWT validée sur tous les endpoints
- [ ] Rate limiting configuré
- [ ] Headers sécurité activés (HSTS, X-Frame-Options, X-Content-Type-Options)
- [ ] CORS restreint (pas `allow_origins=["*"]`)
- [ ] Taille max payload configurée
- [ ] Logs sans données sensibles

### Base de données
- [ ] Migrations Alembic testées (upgrade + downgrade)
- [ ] Backup de la DB de production effectué
- [ ] Utilisateur DB applicatif (pas superuser)
- [ ] Index créés sur les nouvelles tables

### Documentation
- [ ] CHANGELOG.md mis à jour
- [ ] PROJECT_MEMORY.md mis à jour
- [ ] DEC-xxxxxx créé si décision structurante
- [ ] `.env.example` à jour avec les nouvelles variables

## Docker

```dockerfile
# Base image Debian Bookworm (pas slim — PostGIS nécessite des deps)
FROM python:3.12-bookworm

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    libpq-dev gdal-bin libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

# Code applicatif
COPY GSIE/ ./GSIE/

# Non-root user
RUN useradd -m gsie
USER gsie

CMD ["uvicorn", "GSIE.API.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [db, redis]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  db:
    image: postgis/postgis:16-3.4
    volumes: ["pgdata:/var/lib/postgresql/data"]
    env_file: .env
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  pgdata:
```

## CI/CD (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:16-3.4
        env:
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install uv && uv sync --frozen
      - run: ruff check GSIE/
      - run: mypy GSIE/ --strict
      - run: pytest GSIE/ --cov=GSIE --cov-fail-under=80
```

## Déploiement

1. `docker compose build`
2. `docker compose up -d`
3. Vérifier `/health` → 200
4. Vérifier `/docs` → Swagger accessible
5. Smoke test : `curl -X POST /v1/engines/evidence/process ...`

## Rollback

1. `docker compose down`
2. `docker compose pull <previous-version>`
3. `docker compose up -d`
4. `alembic downgrade -1` si migration problématique
5. Restaurer backup DB si nécessaire

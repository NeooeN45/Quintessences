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
- [ ] Depuis `GSIE/API`, tests : `.\.venv\Scripts\python.exe -m pytest tests/ -q`
- [ ] Depuis `GSIE/API`, mypy : `.\.venv\Scripts\python.exe -m mypy src/gsie_api/` — 0 erreur
- [ ] Depuis `GSIE/API`, ruff : `.\.venv\Scripts\python.exe -m ruff check src/ tests/` — 0 erreur
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

Le Dockerfile canonique est `GSIE/API/Dockerfile`. Il doit rester la source de
vérité pour les stages Rust/Python, les dépendances natives, l'utilisateur non
root, l'entrypoint de migration explicite et le worker Gunicorn.

Depuis `GSIE/API`, utiliser le Compose existant :

```powershell
docker compose config
docker compose build api
docker compose up -d db redis api
docker compose ps
```

Le fichier `GSIE/API/docker-compose.yml` est la source de vérité pour les
services, les comptes DB, les secrets, les profils et les sondes. Ne recopier
aucun Compose minimal dans une nouvelle documentation.

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
      - run: cd GSIE/API && uv sync --frozen
      - run: cd GSIE/API && python -m ruff check src/ tests/
      - run: cd GSIE/API && python -m mypy src/gsie_api/
      - run: cd GSIE/API && python -m pytest tests/ -q --cov=gsie_api --cov-fail-under=80
```

## Déploiement

1. `docker compose build`
2. `docker compose up -d`
3. Vérifier `/health` → 200
4. Vérifier `/docs` → Swagger accessible
5. Smoke test : `curl -X POST http://localhost:8000/api/v1/evidence/evaluate ...`

## Rollback

1. `docker compose down`
2. `docker compose pull <previous-version>`
3. `docker compose up -d`
4. Préparer un `alembic downgrade -1` uniquement après sauvegarde, validation du plan de rollback et autorisation explicite
5. Restaurer backup DB si nécessaire

---
name: tests-gsie
description: Stratégie de tests pour GSIE Phase 4 — TDD, pytest, couverture, intégration
triggers:
  - user
  - model
---

# Tests GSIE — Phase 4

## Principe : TDD obligatoire

Écrire les tests AVANT l'implémentation. Si tu es tenté d'écrire le code d'abord, arrête — écris le test en premier.

`pytest-asyncio` est configuré en mode `auto` dans `GSIE/API/pyproject.toml` : les tests et fixtures asynchrones n'ajoutent pas `@pytest.mark.asyncio` et utilisent `@pytest.fixture`.

## Structure des tests par moteur

Dans l'API actuelle, les contrats des moteurs sont documentés dans
`GSIE/ENGINES/<NOM>_ENGINE/`, tandis que l'implémentation et les tests vivent
dans `GSIE/API/` :

```
GSIE/API/tests/
├── conftest.py              ← fixtures partagées
├── unit/                    ← services, schémas et moteurs sans I/O externe
├── integration/             ← PostgreSQL/PostGIS, API et frontières réelles
└── mutation/                ← harnais des gardes de résilience
```

## Nommage

```python
# Format : should_[comportement_attendu]_when_[condition]
def test_should_return_high_confidence_when_sources_agree():
def test_should_raise_validation_error_when_input_is_empty():
def test_should_fallback_to_cache_when_db_unavailable():
```

## Fixtures réutilisables

```python
# conftest.py
import pytest

@pytest.fixture
def sample_forest_plot():
    return ForestPlot(
        id="plot_001",
        lat=44.7, lon=-0.5,
        species=["Quercus robur", "Pinus pinaster"],
        surface_ha=2.5
    )

@pytest.fixture
async def test_db():
    """Base de test réinitialisée à chaque test."""
    pool = await asyncpg.create_pool(dsn=settings.TEST_DATABASE_URL)
    await pool.execute("BEGIN")
    yield pool
    await pool.execute("ROLLBACK")
    await pool.close()
```

## Cas à toujours tester

Pour chaque moteur :
- [ ] Input nominal → output correct
- [ ] Input vide / None → ValidationError (pas de crash silencieux)
- [ ] Input invalide → erreur explicite avec message
- [ ] Moteur amont indisponible → comportement de fallback
- [ ] Confidence score dans [0.0, 1.0]
- [ ] trace_id présent dans la réponse

## Tests API (FastAPI)

```python
async def test_should_return_200_when_valid_evidence_request(async_client):
    response = await async_client.post(
        "/api/v1/evidence/evaluate",
        json={"sources": [{"id": "DS-001", "type": "lidar"}]},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert 0.0 <= data["confidence"] <= 1.0
    assert "trace_id" in data
```

## Couverture cible

- Logique métier des moteurs : **80% minimum**
- API endpoints : **100%** (critiques)
- Modèles Pydantic : **100%** (validation)
- Infrastructure (DB, cache) : **60%** minimum

## Commandes

```bash
# Depuis GSIE/API
.\.venv\Scripts\python.exe -m pytest tests/ -q

# Avec couverture
.\.venv\Scripts\python.exe -m pytest tests/ -q --cov=gsie_api --cov-report=term-missing

# Tests unitaires d'un moteur
.\.venv\Scripts\python.exe -m pytest tests/unit/ -q -k evidence
```

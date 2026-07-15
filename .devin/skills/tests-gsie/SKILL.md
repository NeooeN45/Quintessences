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

## Structure des tests par moteur

```
GSIE/ENGINES/<NOM>_ENGINE/tests/
├── conftest.py              ← fixtures partagées (DB, mocks moteurs amont)
├── test_unit.py             ← tests unitaires (sans I/O externe)
├── test_integration.py      ← tests avec DB de test réelle
└── test_contract.py         ← vérification du contrat d'interface
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
import pytest_asyncio

@pytest.fixture
def sample_forest_plot():
    return ForestPlot(
        id="plot_001",
        lat=44.7, lon=-0.5,
        species=["Quercus robur", "Pinus pinaster"],
        surface_ha=2.5
    )

@pytest_asyncio.fixture
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
@pytest.mark.asyncio
async def test_should_return_200_when_valid_evidence_request(async_client):
    response = await async_client.post(
        "/v1/engines/evidence/process",
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
# Lancer tous les tests
pytest GSIE/TESTS/

# Avec couverture
pytest --cov=GSIE --cov-report=term-missing

# Un moteur spécifique
pytest GSIE/ENGINES/EVIDENCE_ENGINE/tests/ -v
```

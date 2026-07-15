---
name: api-fastapi
description: Conventions FastAPI pour l'API GSIE — structure, auth JWT, validation, observabilité
triggers:
  - user
  - model
---

# API GSIE — Conventions FastAPI

## Stack

- FastAPI + Pydantic v2
- Python 3.11+
- PostgreSQL + PostGIS via asyncpg
- Auth : JWT Bearer (python-jose)
- Tests : pytest + httpx AsyncClient

## Structure de l'API

```
GSIE/API/
├── main.py                    ← app FastAPI + lifespan
├── routers/
│   └── {engine_name}.py      ← un router par moteur
├── models/
│   ├── requests.py            ← modèles Pydantic entrée
│   └── responses.py           ← modèles Pydantic sortie
├── auth/
│   ├── jwt.py                 ← validation JWT
│   └── dependencies.py        ← Depends(get_current_user)
├── middleware/
│   ├── rate_limiting.py
│   └── observability.py       ← logging structuré + trace_id
└── tests/
    ├── conftest.py            ← fixtures AsyncClient
    ├── test_{router}.py
    └── test_auth.py
```

## Conventions de réponse

```python
# Succès — trace_id est un UUID généré par requête (pas un identifiant DEC)
{"data": {...}, "confidence": 0.95, "trace_id": "a3f1c2e4-...", "engine": "evidence"}

# Erreur
{"error": {"code": "INVALID_INPUT", "message": "...", "field": "..."}, "trace_id": "a3f1c2e4-..."}
```

**Note :** Le `trace_id` de requête est un `uuid4()` généré à chaque appel entrant (middleware).
Ne pas utiliser un identifiant de décision projet (`DEC-xxxxxx`) comme trace_id HTTP — ce sont deux
concepts distincts. Le `DEC-xxxxxx` peut figurer dans le champ `decision_ref` de la réponse si
pertinent, mais jamais comme identifiant de corrélation de logs.

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class TraceIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response
```

## Authentification

```python
from fastapi import Depends, HTTPException
from app.auth.dependencies import get_current_user

@router.post("/v1/engines/evidence/process")
async def process(
    request: EvidenceRequest,
    user: User = Depends(get_current_user)
) -> EvidenceResponse:
    ...
```

## Règles absolues

- Valider TOUTES les entrées avec Pydantic avant traitement
- Log structuré sur chaque requête : `{"trace_id": ..., "engine": ..., "latency_ms": ...}`
- Ne jamais exposer les stack traces en production
- Rate limiting sur tous les endpoints publics
- Pagination obligatoire sur toutes les listes (default=20, max=100)

## Tests

```python
@pytest.mark.asyncio
async def test_should_return_evidence_when_valid_input(async_client):
    response = await async_client.post("/v1/engines/evidence/process", json={...})
    assert response.status_code == 200
    assert "confidence" in response.json()
```

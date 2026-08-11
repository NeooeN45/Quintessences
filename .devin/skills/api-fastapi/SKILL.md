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
- Python 3.12
- PostgreSQL 16 + PostGIS via asyncpg/SQLAlchemy async
- Auth : JWT RS256 avec PyJWT
- Tests : pytest + httpx AsyncClient

## Structure de l'API

```
GSIE/API/
├── src/gsie_api/
│   ├── app.py                 ← factory FastAPI + lifespan
│   ├── core/                  ← configuration, auth, RBAC, logging
│   ├── engines/{name}/         ← engine.py, schemas.py, router.py
│   ├── infrastructure/        ← DB, modèles SQLAlchemy, santé
│   ├── shared/                 ← middleware et schémas communs
│   └── resources/              ← CRUD générique v6.2
└── tests/
    ├── unit/                  ← services, validateurs, clients
    └── integration/           ← PostgreSQL, API et frontières
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
from gsie_api.core.auth import get_current_user

@router.post("/api/v1/evidence/evaluate")
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
async def test_should_return_evidence_when_valid_input(async_client):
    response = await async_client.post("/api/v1/evidence/evaluate", json={...})
    assert response.status_code == 200
    assert "confidence" in response.json()
```

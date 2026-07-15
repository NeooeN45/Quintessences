---
name: securite-gsie
description: Hardening sécurité pour GSIE API — JWT, rate limiting, validation, secrets
triggers:
  - user
  - model
---

# Sécurité GSIE — Standards

## Authentification JWT

**Bibliothèque : `PyJWT` (pas `python-jose`)**

`python-jose` a des CVE actifs (CVE-2022-29217 — confusion d'algorithme). Utiliser `PyJWT >= 2.8.0` (activement maintenu, audit de sécurité public).

```python
import jwt  # PyJWT
from datetime import datetime, timedelta, timezone

SECRET_KEY: str = settings.JWT_SECRET_KEY  # depuis env, jamais hardcodé
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15   # court — renouveler via refresh token
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "iat": datetime.now(timezone.utc)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        # algorithms= est OBLIGATOIRE — empêche l'attaque "alg: none"
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalide")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        # Message générique — ne pas exposer la raison précise
        raise HTTPException(status_code=401, detail="Token invalide")
    return await user_repository.get(user_id)
```

**Note :** En production avec plusieurs services, préférer RS256 (clé asymétrique) : le service d'auth signe avec la clé privée, les autres services vérifient avec la clé publique uniquement.

## Taille maximale des payloads

```python
from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

# Limiter la taille des requêtes (évite les DoS par payload géant)
@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    max_body = 1 * 1024 * 1024  # 1 Mo
    if request.headers.get("content-length"):
        if int(request.headers["content-length"]) > max_body:
            return JSONResponse(status_code=413, content={"error": "Payload trop grand"})
    return await call_next(request)
```

## Validation des entrées (obligatoire)

```python
from pydantic import BaseModel, field_validator, Field

class EvidenceRequest(BaseModel):
    sources: list[SourceRef] = Field(min_length=1, max_length=100)
    confidence_threshold: float = Field(ge=0.0, le=1.0, default=0.75)

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, v: list[SourceRef]) -> list[SourceRef]:
        for source in v:
            if not source.id.startswith("DS-"):
                raise ValueError(f"ID source invalide : {source.id}")
        return v
```

## Rate limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/v1/engines/evidence/process")
@limiter.limit("60/minute")
async def process_evidence(request: Request, ...):
    ...
```

## Headers de sécurité (middleware)

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
```

## Règles de sécurité absolues

- **Secrets** : variables d'environnement UNIQUEMENT — jamais dans le code, jamais dans git
- **SQL** : requêtes paramétrées UNIQUEMENT — jamais de concaténation de chaînes SQL
- **Passwords** : argon2 (préféré) ou bcrypt — jamais MD5/SHA1
- **Logs** : jamais de données sensibles (tokens, mots de passe, données personnelles)
- **Erreurs clients** : messages génériques — les détails restent dans les logs internes
- **HTTPS** : obligatoire en production, aucun fallback HTTP

## Checklist sécurité avant déploiement

- [ ] `PyJWT >= 2.8.0` utilisé (pas `python-jose`)
- [ ] `algorithms=["HS256"]` explicite dans `jwt.decode()` — jamais de liste vide
- [ ] Aucun secret dans le code ou git (`git log -S "SECRET"` propre)
- [ ] Variables d'environnement documentées dans `.env.example` (valeurs factices)
- [ ] Taille max payload configurée (1 Mo par défaut)
- [ ] Rate limiting configuré sur tous les endpoints publics
- [ ] Auth JWT validée sur tous les endpoints protégés
- [ ] Inputs validés avec Pydantic sur chaque endpoint
- [ ] Headers sécurité activés (HSTS, X-Frame-Options, X-Content-Type-Options)
- [ ] CORS restreint aux origines connues (pas `allow_origins=["*"]` en prod)
- [ ] Dépendances auditées (`pip audit`) — aucun CVE connu non mitigé
- [ ] Logs sans données sensibles (revue manuelle d'un sample de logs)
- [ ] Token de révocation implémenté pour le logout (liste noire en Redis ou DB)
- [ ] Rotation des secrets planifiée (procédure documentée)

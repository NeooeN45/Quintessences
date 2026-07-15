---
name: gestion-erreurs
description: Stratégie de gestion des erreurs pour GSIE — exceptions typées, fail fast, logging
triggers:
  - user
  - model
---

# Gestion des erreurs GSIE

## Hiérarchie d'exceptions

```python
# Base commune à tous les moteurs
class GSIEBaseException(Exception):
    def __init__(self, message: str, trace_id: str | None = None):
        super().__init__(message)
        self.trace_id = trace_id

# Par domaine
class EngineException(GSIEBaseException): pass
class ValidationException(GSIEBaseException): pass
class DataSourceException(GSIEBaseException): pass
class InsufficientConfidenceException(EngineException): pass

# Par moteur
class EvidenceEngineException(EngineException): pass
class KnowledgeEngineException(EngineException): pass
# etc.
```

## Principe : Fail Fast

```python
# Valider à l'entrée, AVANT tout traitement
def process_evidence(request: EvidenceRequest) -> EvidenceResponse:
    if not request.sources:
        raise ValidationException("Au moins une source est requise")
    if request.confidence_threshold < 0 or request.confidence_threshold > 1:
        raise ValidationException("confidence_threshold doit être dans [0.0, 1.0]")
    
    # Traitement uniquement si validation passée
    ...
```

## Log avant propagation (obligatoire)

```python
import logging
logger = logging.getLogger(__name__)

try:
    result = external_service.call()
except ExternalException as e:
    # Logger le détail INTERNE (jamais exposé au client)
    logger.error(
        "Erreur service externe",
        extra={"trace_id": trace_id, "service": "external", "error": str(e)}
    )
    # Message CLIENT générique — str(e) ne doit JAMAIS y apparaître
    raise DataSourceException("Service de données temporairement indisponible", trace_id=trace_id) from e
```

## Gestion FastAPI — isolation message interne / message client

```python
from fastapi import Request
from fastapi.responses import JSONResponse

# RÈGLE : le message retourné au client est toujours le message de l'exception GSIE
# (contrôlé par le développeur), jamais str(cause) qui peut contenir des détails internes.

@app.exception_handler(ValidationException)
async def validation_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}}
        # ✓ ValidationException contient un message métier contrôlé
    )

@app.exception_handler(DataSourceException)
async def datasource_handler(request: Request, exc: DataSourceException):
    return JSONResponse(
        status_code=503,
        content={"error": {"code": "DATA_SOURCE_UNAVAILABLE", "message": str(exc)}}
        # ✓ Le message dans DataSourceException est générique (voir ci-dessus)
    )

@app.exception_handler(InsufficientConfidenceException)
async def confidence_handler(request: Request, exc: InsufficientConfidenceException):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "LOW_CONFIDENCE", "message": str(exc)}}
    )

# Attraper toutes les exceptions non prévues — ne jamais exposer le détail
@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    logger.critical("Exception non gérée", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Erreur interne du serveur"}}
        # JAMAIS str(exc) ici — peut contenir paths, credentials, stack traces
    )
```

## Règles absolues

- Ne JAMAIS avaler silencieusement une exception (`except: pass`)
- Toujours logger le détail AVANT de propager
- Le message du `raise MonException("...")` est le message client — rédiger en conséquence
- Ne JAMAIS passer `str(cause)` dans un message d'exception GSIE propagé vers le client
- Ne JAMAIS exposer les stack traces aux clients API en production
- Les messages d'erreur utilisateur sont en français, sobres et sans détail technique

---
name: logging-gsie
description: Observabilité et logging structuré pour GSIE — trace_id, métriques, alertes
triggers:
  - user
  - model
---

# Logging et Observabilité GSIE

## Logging structuré (JSON)

```python
import logging
import json
from typing import Any

class GSIEJSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", None),
            "engine": getattr(record, "engine", None),
        }
        return json.dumps(log_data, ensure_ascii=False)
```

## Contexte obligatoire dans chaque log

Chaque log d'un moteur doit contenir :
- `trace_id` : identifiant de la requête (propagé depuis l'API)
- `engine` : nom du moteur (`"evidence"`, `"knowledge"`, etc.)
- `latency_ms` : pour les opérations mesurables
- `confidence` : pour les résultats des moteurs IA

```python
logger.info(
    "Traitement Evidence Engine terminé",
    extra={
        "trace_id": request.trace_id,
        "engine": "evidence",
        "latency_ms": elapsed_ms,
        "confidence": result.confidence,
        "sources_count": len(request.sources)
    }
)
```

## Niveaux de log

| Niveau | Usage |
|---|---|
| `DEBUG` | Détail de traitement (désactivé en prod) |
| `INFO` | Événements normaux (requête reçue, résultat produit) |
| `WARNING` | Comportement dégradé mais récupérable (fallback activé, confiance basse) |
| `ERROR` | Erreur récupérée (service externe indisponible, validation échouée) |
| `CRITICAL` | Erreur système non récupérable (DB inaccessible, moteur planté) |

## Métriques (Prometheus)

```python
from prometheus_client import Counter, Histogram

engine_requests = Counter(
    "gsie_engine_requests_total",
    "Nombre de requêtes par moteur",
    ["engine", "status"]
)

engine_latency = Histogram(
    "gsie_engine_latency_seconds",
    "Latence par moteur",
    ["engine"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)
```

## Alertes (seuils)

- Latence > 2s : WARNING
- Latence > 5s : ERROR + alerte
- Confidence < 0.5 : WARNING (résultat dégradé)
- Taux d'erreur > 5% sur 5min : alerte critique
- DB query > 100ms : log slow query

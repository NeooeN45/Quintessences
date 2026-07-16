# ADR-007 — Architecture API v6.2 : CRUD générique + modules par domaine

| Champ | Valeur |
|---|---|
| **ID** | ADR-007 |
| **Statut** | Proposé |
| **Date** | 2026-07-16 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Décision liée** | DEC-000023, RFC-0012 |
| **Supersède** | Aucun (complète ADR-001 et ADR-002 pour la couche API) |

## Contexte

L'API GSIE (FastAPI) doit migrer du schéma v6.1 (12 tables,
`KnowledgeObject`) vers le métamodèle v6.2 (73 types, racine `resource`).
Avec 73 types, créer 73 routers × 5 endpoints CRUD = 365 endpoints
manuels est infaisable et non maintenable.

## Options envisagées

1. **73 routers manuels** — un router par type avec CRUD explicite.
   Avantage : contrôle total. Inconvénient : ~365 endpoints, duplication
   massive, maintenance impossible.

2. **CRUD générique auto-généré** — un router générique qui détecte le
   `type` dans `resource` et route vers le bon modèle SQLAlchemy.
   Endpoints spécialisés uniquement pour les moteurs (evidence/evaluate,
   correlation/detect, etc.). Avantage : 7 endpoints génériques +
   ~20 spécialisés = 27 endpoints total. Inconvénient : moins de
   contrôle par type, validation générique.

3. **GraphQL** — un schéma GraphQL auto-généré depuis les modèles.
   Avantage : flexibilité totale pour les clients. Inconvénient :
   complexité, pas de compatibilité REST, sur-ingénierie pour Phase 4.

## Décision

**Option 2 : CRUD générique + endpoints spécialisés par moteur.**

### Router générique

```
GET    /api/v1/resources            ?type=assertion&page=1&size=20
POST   /api/v1/resources             body: {type: "assertion", ... champs}
GET    /api/v1/resources/{id}
PUT    /api/v1/resources/{id}        body: {... champs modifiés}
DELETE /api/v1/resources/{id}        soft delete (transaction_time_end)
GET    /api/v1/resources/{id}/revisions
GET    /api/v1/resources/{id}/snapshot?at=2024-06-15
```

Le router générique utilise un **registry** qui mappe `type` → modèle
SQLAlchemy. Le body de POST/PUT est validé dynamiquement selon le type.

### Endpoints spécialisés (moteurs)

```
POST   /api/v1/evidence/evaluate              # existant — conserve
POST   /api/v1/knowledge/ingest               # migré → crée une Assertion
POST   /api/v1/knowledge/query                # migré → query sur Assertion
POST   /api/v1/engines/correlation/detect     # nouveau
POST   /api/v1/engines/reasoning/infer        # nouveau
POST   /api/v1/engines/diagnostic/diagnose    # nouveau
POST   /api/v1/engines/recommendation/recommend  # nouveau
GET    /api/v1/engines/gis/wms                # nouveau — proxy WMS IGN
POST   /api/v1/engines/simulation/run         # nouveau
GET    /api/v1/phenomena/active               # phénomènes écologiques actifs
GET    /api/v1/alerts                         # alertes (incendie, sécheresse)
```

### WebSocket

```
WS     /api/v1/ws/hub             # canal temps réel Hub (UE5.8)
WS     /api/v1/ws/events          # events système
```

### Registry des types

```python
# infrastructure/models/__init__.py
RESOURCE_TYPES: dict[str, type[Base]] = {}

def register_type(type_name: str):
    """Décorateur — enregistre un modèle dans le registry."""
    def decorator(cls):
        RESOURCE_TYPES[type_name] = cls
        return cls
    return decorator

@register_type("assertion")
class AssertionModel(ResourceBase):
    __tablename__ = "assertion"
    # ...
```

### Structure des modules API

```
src/gsie_api/
├── app.py                         # Factory FastAPI
├── core/                          # config, auth, logging
├── shared/                        # middleware, pagination, schemas génériques
├── infrastructure/
│   ├── database.py
│   ├── redis_client.py
│   ├── health.py
│   └── models/                    # 73 modèles SQLAlchemy (12 fichiers par domaine)
├── resources/                     # CRUD générique
│   ├── router.py                  # 7 endpoints génériques
│   ├── service.py                 # logique CRUD générique
│   └── schemas.py                 # DTOs génériques (ResourceCreate, ResourceRead, etc.)
├── engines/                       # endpoints spécialisés par moteur
│   ├── evidence/                  # existant — conserve
│   ├── knowledge/                 # migré vers Assertion
│   ├── correlation/               # nouveau
│   ├── reasoning/                 # nouveau
│   ├── diagnostic/                # nouveau
│   ├── recommendation/            # nouveau
│   ├── gis/                       # implémenté
│   ├── climate/                   # nouveau
│   ├── pedology/                  # nouveau
│   ├── botanical/                 # nouveau
│   ├── forest_dynamics/           # nouveau
│   ├── learning/                  # nouveau
│   ├── simulation/                # nouveau
│   └── pipeline.py                # orchestration Evidence → Assertion
├── websocket/                     # WebSocket pour Hub
│   ├── router.py
│   ├── manager.py                 # ConnectionManager + Redis Pub/Sub
│   └── events.py                  # définition des events
├── auth/                          # existant — conserve
└── seeds/                         # migré vers nouvelles tables
```

## Conséquences

- **27 endpoints** au lieu de 365 (7 génériques + 20 spécialisés)
- **Registry pattern** — ajout d'un type = 1 décorateur + 1 modèle
- **Validation dynamique** — le body est validé selon le type
- **Pagination obligatoire** sur tous les list endpoints
- **Soft delete** — DELETE marque `transaction_time_end` (Temporal Engine)
- **WebSocket** — Redis Pub/Sub pour scaling horizontal
- **SDK** — généré depuis OpenAPI, 3 clients (Python, Kotlin, C++)

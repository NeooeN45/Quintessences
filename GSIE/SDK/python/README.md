# SDK Python GSIE

Client Python asynchrone pour l'API GSIE. Phase 4 — autorisé par `DEC-000017`.

## Objectif

Envelopper l'API GSIE dans une bibliothèque ergonomique pour les
applications Python (QGISIA, scripts, notebooks). **Aucune logique métier** :
le SDK ne fait que transporter les appels, gérer l'authentification JWT
et exposer les réponses typées.

## Installation

```bash
uv sync --extra dev
```

## Usage minimal

```python
import asyncio
from gsie_sdk import GSIEClient

async def main():
    async with GSIEClient(base_url="http://localhost:8000") as client:
        await client.login(username="admin", password="secret")
        diag = await client.diagnostic.diagnostiquer(payload={...})
        print(diag)

asyncio.run(main())
```

## Périmètre v0.1.0

- Authentification : `login`, `refresh`, `verify` (JWT RS256 Bearer)
- Health : `health`, `ready`
- Moteurs : `diagnostic`, `recommendation`, `validation`, `simulation`
  (wrappers `status`, `version`, endpoint principal)
- Resources : CRUD générique (`list`, `get`, `create`, `update`, `delete`)
- Rafraîchissement automatique du token à l'expiration (401 → refresh → retry)

## Ce qui est interdit

- Logique métier GSIE (moteurs, raisonnement) — c'est le rôle de l'API
- Modification de l'API côté SDK — le SDK est un client purement passif

## Liens

- `GSIE/API/` : l'API que ce SDK enveloppe
- `GSIE/SDK/README.md` : charte du dossier SDK

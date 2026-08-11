---
name: nouveau-client-api
description: Checklist pour créer un nouveau client d'API externe GSIE — résilience automatique via ResilientHttpClient + factory de tests
triggers:
  - user
  - model
---

# Skill : Nouveau client d'API externe

## Quand l'utiliser

À la création de tout nouveau client d'API externe (HTTP) dans
`GSIE/API/src/gsie_api/engines/`. Depuis `GSIE/API`, le projet GSIE sera
connecté à des centaines voire des milliers d'API — chaque client doit être
résilient par construction, pas par accident.

## Les 5 modes de panne à couvrir

| # | Mode | Cause | Garde |
|---|------|-------|-------|
| 1 | Panne réseau | ConnectError, timeout | `except httpx.HTTPError` |
| 2 | HTTP 4xx/5xx | serveur down, 404, 500 | `raise_for_status()` + `except httpx.HTTPError` |
| 3 | Corps malformé | JSON/CSV/XML cassé | `except json.JSONDecodeError` (ou équivalent) |
| 4 | Champ absent | JSON valide sans champ attendu | `dict.get()` + retour `None`/`[]`/`{}` |
| 5 | Quota/Auth | 401/403/429 | capturé par le mode #2 si auth |

## Étapes obligatoires

### 1. Hériter de `ResilientHttpClient`

```python
from gsie_api.shared.http_client import ResilientHttpClient

class MonClient(ResilientHttpClient[dict[str, Any]]):
    @property
    def exception_class(self) -> type[Exception]:
        return MonClientError

    @property
    def base_url(self) -> str:
        return "https://api.exemple.com/v1"

    def auth_headers(self) -> dict[str, str]:
        return {"apikey": get_settings().ma_cle}  # si auth

    async def get_data(self, query: str) -> dict[str, Any] | None:
        data = await self._get_json("/search", params={"q": query})
        if "result" not in data:
            return None
        return data
```

Pour le CSV : hériter de `ResilientCsvClient` et utiliser `_get_csv()`.
Pour le gzip/binaire : hériter de `ResilientHttpClient` et utiliser
`_get_bytes()`.

### 2. Définir l'exception métier

```python
class MonClientError(Exception):
    """Erreur lors d'un appel à l'API MonService."""
```

### 3. Enregistrer dans la factory de tests

Ajouter une entrée dans `tests/unit/test_resilience_factory.py` :

```python
CLIENT_REGISTRY.append(
    ClientSpec(
        name="mon_client",
        factory=lambda: MonClient(),
        url="https://api.exemple.com/v1/search",
        exception=MonClientError,
        call=lambda c: c.get_data("test"),
        auth=True,  # ou False
        body_format=BodyFormat.JSON,  # ou CSV, GZIP_CSV, XML, BINARY
    ),
)
```

Les 5 tests paramétrés sont générés automatiquement.

### 4. Ajouter une mutation au harnais

Si une garde spécifique est ajoutée (au-delà de la base class), ajouter
une mutation dans `tests/mutation/harnais.py` qui supprime la garde et
vérifie qu'un test échoue.

### 5. Valider

```bash
.\.venv\Scripts\python.exe -m ruff check src/gsie_api/engines/.../mon_client.py
.\.venv\Scripts\python.exe -m mypy src/gsie_api/engines/.../mon_client.py
.\.venv\Scripts\python.exe -m pytest tests/unit/test_resilience_factory.py -q
.\.venv\Scripts\python.exe tests/mutation/harnais.py
```

## Anti-patterns

- **Ne pas** utiliser `httpx.MockTransport` dans les nouveaux tests —
  utiliser `respx`.
- **Ne pas** capturer `Exception` largement — capturer
  `httpx.HTTPError` + `json.JSONDecodeError` spécifiquement.
- **Ne pas** retourner une valeur inventée quand un champ est absent —
  retourner `None`, `[]`, ou `{}`.
- **Ne pas** avaler silencieusement une erreur — toujours `raise` avec
  `from exc`.
- **Ne pas** oublier `raise_for_status()` — un 200 avec un corps
  d'erreur est un piège classique.

## Référence

- Classe de base : `src/gsie_api/shared/http_client.py`
- Factory de tests : `tests/unit/test_resilience_factory.py`
- Harnais de mutation : `tests/mutation/harnais.py`
- Prompt source : `GSIE-PROMPT-0023`

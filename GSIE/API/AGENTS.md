# AGENTS.md — GSIE API

> Règles opérationnelles pour tout agent IA travaillant sur l'API GSIE.
> En cas de conflit, le fichier `AGENTS.md` racine du dépôt prime.

## Environnement

- **Python 3.12** dans `.venv/` (uv)
- **Source** : `src/gsie_api/`
- **Tests** : `tests/unit/`, `tests/integration/`, `tests/mutation/`

## Commandes de validation

| Commande | Usage |
|----------|-------|
| `.\.venv\Scripts\python.exe -m ruff check src/ tests/` | Lint |
| `.\.venv\Scripts\python.exe -m mypy src/gsie_api/` | Typage |
| `.\.venv\Scripts\python.exe -m pytest tests/unit -q --no-cov` | Tests unitaires |
| `.\.venv\Scripts\python.exe -m pytest tests/ -q` | Tests complets |
| `.\.venv\Scripts\python.exe tests/mutation/harnais.py` | Harnais de mutation |

## Conventions tests

- **respx** pour mocker le réseau (jamais `httpx.MockTransport` dans les nouveaux tests)
- **pytest-asyncio** en mode `auto` (pas de `@pytest.mark.asyncio`)
- Nommage : `should_[expected]_when_[condition]`
- Assertions précises avec `match=` sur `pytest.raises`
- Structure : Arrange → Act → Assert

## Harnais de mutation

`tests/mutation/harnais.py` contient des mutations textuelles. Chaque
mutation supprime une garde et vérifie qu'au moins un test l'échoue.
Score attendu : **14/14**. Ajouter une mutation pour chaque nouvelle
garde de résilience.

## Clients d'API externes

10 clients dans `engines/` : botanical (GBIF, Taxref), climate (AROME,
DPClim, MétéoFrance, SYNOP, Vigilance, PaquetObs), gis (IGN), pedology
(SoilGrids).

### Convention résilience (GSIE-PROMPT-0023)

**Tout nouveau client d'API externe DOIT :**

1. Hériter de `ResilientHttpClient` (ou `ResilientCsvClient`) dans
   `src/gsie_api/shared/http_client.py` — la capture des 5 modes de
   panne est automatique.
2. Être enregistré dans `CLIENT_REGISTRY` dans
   `tests/unit/test_resilience_factory.py` — les 5 tests paramétrés
   sont générés automatiquement.
3. Avoir une mutation dans `tests/mutation/harnais.py` si une garde
   spécifique est ajoutée au-delà de la base class.

**Les 5 modes de panne** : réseau, HTTP 4xx/5xx, corps malformé,
champ absent, quota/auth.

**Anti-patterns** : pas de `httpx.MockTransport` (utiliser `respx`),
pas de `except Exception` large, pas de valeur inventée pour un champ
absent (`None`/`[]`/`{}` uniquement), pas d'erreur avalée
(`raise ... from exc` obligatoire).

Voir le skill `/nouveau-client-api` pour la checklist complète.

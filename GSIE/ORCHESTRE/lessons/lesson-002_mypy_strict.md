# Leçon 002 — mypy strict

- **Date** : 2026-08-08
- **Source** : Convention AGENTS.md API
- **Contexte** : GSIE API utilise mypy strict sur `src/gsie_api/`

## Règle

Tout nouveau code doit passer `mypy src/gsie_api/` sans erreur.
Pas de `Any`, pas de paramètre non typé. Types explicites sur
toutes les APIs publiques.

## Commande

```powershell
.\.venv\Scripts\python.exe -m mypy src/gsie_api/
```

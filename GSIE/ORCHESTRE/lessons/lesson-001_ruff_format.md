# Leçon 001 — ruff format avant commit

- **Date** : 2026-08-08
- **Source** : Cycle benchmark Correlation Engine
- **Contexte** : Le pre-commit hook bloque si ruff format n'est pas exécuté

## Règle

Toujours exécuter `ruff check --fix` puis `ruff format` sur tout
nouveau fichier Python avant de committer. Le pre-commit hook GSIE
vérifie ruff check + ruff format + gouvernance.

## Commande

```powershell
.\.venv\Scripts\python.exe -m ruff check <fichiers> --fix
.\.venv\Scripts\python.exe -m ruff format <fichiers>
```

# Leçon 004 — Tests de mutation

- **Date** : 2026-08-08
- **Source** : AGENTS.md API
- **Contexte** : Le harnais de mutation doit couvrir chaque nouvelle garde

## Règle

Chaque nouvelle garde de résilience ajoutée à un client d'API externe
doit avoir une mutation correspondante dans `tests/mutation/harnais.py`.
Score attendu : 14/14 (ou plus si nouvelles mutations ajoutées).

## Commande

```powershell
.\.venv\Scripts\python.exe tests/mutation/harnais.py
```

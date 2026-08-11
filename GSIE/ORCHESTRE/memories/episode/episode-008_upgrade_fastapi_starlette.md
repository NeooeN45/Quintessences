# Épisode 008 — Upgrade coordonné FastAPI/Starlette

- **Type** : episode
- **Date** : 2026-08-09
- **Loop** : Sécurité+Perf
- **Statut** : réussi
- **Salience** : 1.0
- **Importance** : 1.0

## Résultat

Sur la branche `chore/upgrade-fastapi-starlette` :

- FastAPI 0.115.6 → 0.134.0
- Starlette 0.41.3 → 0.52.1
- `uv.lock` régénéré et vérifié
- 300 tests ciblés passants
- 2667 tests unitaires passants, 63 ignorés
- couverture 100 %
- ruff/mypy verts
- harnais de mutation code retour 0

187 warnings de dépréciation FastAPI restent à traiter dans une tâche
séparée ; ils ne bloquent pas la compatibilité fonctionnelle.

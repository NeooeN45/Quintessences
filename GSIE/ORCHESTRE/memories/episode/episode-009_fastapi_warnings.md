# Épisode 009 — Nettoyage des dépréciations FastAPI

- **Type** : episode
- **Date** : 2026-08-09
- **Loop** : QA
- **Statut** : réussi
- **Salience** : 0.8
- **Importance** : 0.7

## Résultat

- `ORJSONResponse` global supprimé au profit de la sérialisation Pydantic
  standard recommandée par FastAPI 0.134.
- Constante 422 dépréciée remplacée dans les routers concernés.
- 217 tests ciblés passants.
- Suite complète : 2667 tests passants, 63 ignorés, 100 % couverture.
- Warnings réduits de 187 à 3.
- Les 3 warnings résiduels sont des `RuntimeWarning` `runpy` dans les
  tests de points d'entrée (`outbox_health`, `outbox_worker`, `run_seeds`).

Les warnings applicatifs Stripe, SciPy et FastAPI/Starlette sont résolus.

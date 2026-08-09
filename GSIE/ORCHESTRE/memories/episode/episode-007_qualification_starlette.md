# Épisode 007 — Qualification Starlette/FastAPI

- **Type** : episode
- **Date** : 2026-08-09
- **Loop** : Sécurité+Perf
- **Statut** : qualification terminée, décision en attente
- **Salience** : 1.0
- **Importance** : 1.0

## Résultat

FastAPI 0.115.6 borne Starlette à `<0.42.0`. Les releases officielles
indiquent que FastAPI 0.133.0 supporte Starlette 1.0+ et que FastAPI
0.134.0 demande Starlette >=0.46.0.

La correction des CVE Starlette nécessite donc un upgrade coordonné du
framework public. Aucun changement n'a été appliqué.

## Décision attendue

Escalade #002 : choisir l'upgrade coordonné, une mitigation temporaire,
ou le report avec ticket prioritaire.

# Épisode 002 — Audit des dépendances CVE

- **Type** : episode
- **Date** : 2026-08-08
- **Loop** : Sécurité+Perf
- **Statut** : réussi avec escalade
- **Salience** : 1.0
- **Importance** : 1.0

## Résultat

Audit `pip-audit 2.10.1` sur 138 packages résolus : 24 CVE uniques
sur 7 packages, dont 6 HIGH. Aucun CRITIQUE détecté.

Packages prioritaires : pyjwt 2.10.1 (7 CVE, 3 HIGH), starlette 0.41.3
(7 CVE), python-multipart 0.0.20 (6 CVE), cryptography 49.0.0 (1 HIGH).

## Décision en attente

Escalade #001 : réponse du Fondateur requise avant toute mise à jour
de dépendance touchant l'authentification JWT.

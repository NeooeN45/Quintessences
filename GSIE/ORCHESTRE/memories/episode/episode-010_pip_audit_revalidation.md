# Épisode 010 — Revalidation pip-audit dans le venv GSIE

- **Type** : episode
- **Date** : 2026-08-09
- **Loop** : Sécurité+Perf
- **Statut** : audit terminé, escalade ouverte
- **Salience** : 1.0
- **Importance** : 1.0

## Résultat

`pip-audit==2.10.1` exécuté dans le venv réel avec TLS système.

- Starlette 1.3.1 : aucun avis restant
- pyjwt 2.13.0 : aucun avis restant
- python-multipart 0.0.32 : aucun avis restant
- cryptography 50.0.0 : aucun avis restant
- 4 avis restants sur 3 packages : app-store-server-library 1.5.0,
  orjson 3.10.11 et pytest 8.3.4
- gsie-api local ignoré car non publié sur PyPI

Escalade #003 ouverte pour décider des trois mises à jour restantes.

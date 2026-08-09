# Épisode 005 — Résolution escalade dépendances HIGH

- **Type** : episode
- **Date** : 2026-08-09
- **Loop** : Sécurité+Perf
- **Statut** : réussi avec revalidation réseau différée
- **Salience** : 1.0
- **Importance** : 1.0

## Décision Fondateur

Option B : vérifier et maintenir à jour les trois dépendances HIGH :
`pyjwt==2.13.0`, `python-multipart==0.0.32` et `cryptography==50.0.0`.

## Preuves

- `uv lock --check` : réussi
- Versions installées : conformes
- Tests auth/JWT/SSRF : 60/60 passants
- Suite unitaire précédente : 2667 passés, 63 ignorés, 100 % couverture

## Résiduel

`pip-audit` doit être relancé lorsque la chaîne TLS du proxy permet
l'accès à PyPI/OSV. Starlette 0.41.3 reste à qualifier avec une montée
de FastAPI compatible.

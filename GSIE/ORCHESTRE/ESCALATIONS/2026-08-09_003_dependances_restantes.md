# ESCALADE #003 — Vulnérabilités restantes des dépendances

## Statut: RÉSOLU

**Réponse du Fondateur (2026-08-09) : A.** Les trois mises à jour ont
été appliquées et validées :

- `app-store-server-library==3.1.2`
- `orjson==3.11.6`
- `pytest==9.0.3`
- `pytest-asyncio==1.3.0` ajouté pour la compatibilité pytest 9

Validation : pip-audit ne trouve plus aucune vulnérabilité connue ;
89 tests billing, 155 tests app/auth/routers, 2667 tests unitaires,
63 ignorés, couverture 100 %, ruff/mypy verts et harnais de mutation
terminé avec code retour 0.

## Question

Faut-il mettre à jour les trois packages restants signalés par
`pip-audit` : `app-store-server-library`, `orjson` et `pytest` ?

## Résultat de l'audit réel

Audit exécuté dans le venv GSIE avec `pip-audit==2.10.1` et TLS système :

- `pyjwt`, `python-multipart`, `cryptography` : aucun avis restant
- `starlette==1.3.1` : aucun avis restant
- `app-store-server-library==1.5.0` : GHSA-8f6j-263m-g72x, MODERATE, fix 3.1.2
- `orjson==3.10.11` : PYSEC-2026-107, MODERATE, fix 3.11.6
- `pytest==8.3.4` : PYSEC-2026-1845, LOW, dev uniquement, fix 9.0.3
- `gsie-api==0.1.0` : package local ignoré (non publié sur PyPI)

## Options

A) **Mettre à jour les trois packages maintenant**
   - `app-store-server-library==3.1.2`
   - `orjson==3.11.6`
   - `pytest==9.0.3`
   - Risque : moyen à élevé pour App Store (major 1.x → 3.x), moyen pour
     pytest 9 avec pytest-asyncio/xdist
   - Tests : billing App Store, suite complète, lockfile

B) **Mettre à jour orjson et pytest uniquement**
   - Corrige le package runtime simple et le package dev
   - Laisse la dépendance App Store majeure en attente
   - Risque résiduel : GHSA moderate si l'intégration App Store est active

C) **Reporter les trois**
   - Conserver les versions actuelles
   - Documenter les trois avis et ouvrir une tâche de compatibilité App Store

## Recommandation

**B** si l'intégration App Store n'est pas activée en production ; sinon
**A** avec une validation dédiée de `SignedDataVerifier` avant fusion.

## Impact

- Fichiers probables : `pyproject.toml`, `uv.lock`, tests billing/dev
- Aucun changement de code métier requis a priori
- Le package `pytest` est dev-only ; la CVE est LOW et UNIX-only

## Réponse attendue

Réponds A, B, C ou ta propre option.

---
name: git-flow-gsie
description: Conventions git + commits pour Quintessences — Conventional Commits, branches, traçabilité
triggers:
  - user
  - model
---

# Git Flow Quintessences

## Branches

```
main          ← stable, protégé
feat/xxx      ← nouvelle fonctionnalité
fix/xxx       ← correction de bug
docs/xxx      ← documentation uniquement
refactor/xxx  ← refactoring sans changement de comportement
```

## Commits — Conventional Commits obligatoires

Format : `type(scope): description courte en français`

Types : `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `ci`, `revert`
Scopes : `evidence-engine`, `knowledge-engine`, `api`, `geosylva`, `ignis`, `unreal`, `db`, `infra`

Exemples :
```
feat(evidence-engine): ajout validation croisée des sources
fix(api): correction rate limiting sur endpoint /process
docs(knowledge-engine): ajout état de l'art Wikidata
test(gis-engine): couverture 100% des requêtes PostGIS
```

## Repos externes

- `apps/GeoSylva/` → repo indépendant GitHub: NeooeN45/GeoSylva
- `apps/QGISIA/` → repo indépendant GitHub: NeooeN45/QGISIAPRO
- `Forge/` → dépôt indépendant GitHub : NeooeN45/Forge (branche `master`)

Pour travailler sur un repo externe : cd dans le dossier, git indépendant.

## Avant chaque commit

1. `git diff --stat` — vérifier le périmètre
2. Aucun secret, clé API, .env dans le commit
3. Tests passent (`pytest` ou équivalent)
4. Pas de fichier de debug temporaire

## PRs

- Une seule préoccupation par PR
- Reviewable en < 30 min
- Titre = message du commit principal

## Protection du travail

- Vérifier les références distantes avant de conclure qu’un accès manque.
- Préserver les changements non commités et les branches divergentes.
- Ne jamais afficher les valeurs de secrets ; les détecteurs doivent les masquer.
- Une visibilité privée ne remplace ni la licence ni la protection des branches.
- Changer une visibilité, transférer un dépôt ou réécrire l’historique exige une décision explicite.

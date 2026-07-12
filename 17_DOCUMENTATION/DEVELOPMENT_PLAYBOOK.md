# GSIE Development Playbook

Livrable : 011 — Système de documentation
Statut : Validated
Version : 1.0
Date : 2026-07-12

## Mission

Définir la méthode officielle de développement de GSIE, du besoin à la mise en
production. En Phase 1, ce playbook sert de **référence anticipée** : aucun code
métier n'est produit, mais le cycle est applicable à toute contribution
documentaire.

## Cycle de vie d'une fonctionnalité

```
Spec → Implémentation → Tests → Review → Merge
```

| Étape | Action | Livrable |
|---|---|---|
| 1. Spécification | Rédiger l'exigence dans `05_SPECIFICATIONS/` | Spec validée |
| 2. Implémentation | Coder conformément aux `CODING_STANDARDS.md` | Code + tests |
| 3. Tests | Écrire et passer les tests (mypy, ruff, pytest) | Couverture ≥ 80 % |
| 4. Review | Revue par un pair, vérification de la traçabilité | Approbation |
| 5. Merge | Fusion squash sur `main`, historique linéaire | CHANGELOG mis à jour |

Aucune étape n'est sautée. La documentation précède toujours l'implémentation
(`GSIE-CON-003`).

## Branches par fonctionnalité

- Une branche par fonctionnalité ou correctif : `feat/<description>`,
  `fix/<description>`, `docs/<description>`.
- `main` reste toujours déployable et son historique est **linéaire**
  (squash merge).
- Pas de force-push sur `main`.

## Commits conventionnels

Format : `type(scope): description`

| Type | Usage |
|---|---|
| `feat` | Nouvelle fonctionnalité |
| `fix` | Correctif |
| `refactor` | Refactoring sans changement de comportement |
| `test` | Ajout ou correction de tests |
| `docs` | Documentation |
| `chore` | Tâches de maintenance |
| `perf` | Performance |
| `ci` | Intégration continue |
| `revert` | Annulation d'un commit |

- Sujet ≤ 72 caractères ; le corps explique le **pourquoi**, pas le **quoi**.
- Tout commit doit passer `lint + tests` (pre-commit hook quand possible).

## ADR pour les décisions structurantes

Toute décision d'architecture (choix technologique, pattern, contrat d'interface)
fait l'objet d'un **ADR** (`ADR_TEMPLATE.md`). L'ADR est explicabile
(`GSIE-CON-004`) et ne contredit jamais la Constitution ni une décision `DEC-`
de niveau supérieur.

## Règles non négociables

- La **Constitution prévaut** toujours.
- **Développement incrémental** : petits PRs, une préoccupation par PR,
  reviewable en moins de 30 minutes.
- **Tests systématiques** : pas de code sans test.
- **Documentation à jour** : minimale mais synchronisée.
- **Aucun code sans objectif métier identifié** (YAGNI).

## Definition of Done

Une fonctionnalité est terminée lorsque :
1. Le code est **testé** (couverture ≥ 80 % sur le domaine).
2. Le code est **documenté** (API publique, ADR si décision structurante).
3. Le code est **validé** par un pair (review approuvée).
4. Le code est **traçable** (spec, ADR, `DEC-` le cas échéant).
5. Le code est **conforme** à la Constitution et aux `CODING_STANDARDS.md`.
6. Le `CHANGELOG.md` est mis à jour.

## Voir aussi

- `CODING_STANDARDS.md` — standards de code détaillés.
- `ADR_TEMPLATE.md` — gabarit de décision d'architecture.
- `CONTRIBUTING_GUIDE.md` — règles de contribution.

# GSIE Coding Standards

Livrable : 011 — Système de documentation
Statut : Validated
Version : 1.0
Date : 2026-07-12

## Objet

Définir les standards de code applicables à tout développement GSIE (Phase 2+
et au-delà). En Phase 1, ces standards servent de **référence anticipée** :
aucun code métier n'est produit, mais les contributeurs s'y conforment dès les
premiers prototypes.

## Principes directeurs

- **Clean Architecture** : la dépendance va toujours vers l'intérieur (le
  domaine ignore l'infrastructure).
- **SOLID** : une responsabilité par classe ; interfaces plutôt
  qu'implémentations ; composition plutôt qu'héritage.
- **YAGNI** : on construit ce qui est nécessaire maintenant, pas ce qui pourrait
  l'être.
- **Fail fast** : valider aux frontières, remonter les erreurs tôt et clairement.
- **Explicit plutôt qu'implicite** : pas d'effet de bord, pas de magie.

## Outils de référence

| Outil | Rôle | Configuration |
|---|---|---|
| **mypy** | Vérification statique des types | mode strict (`--strict`) |
| **ruff** | Lint et formatage | règles activées par le projet |
| **pytest** | Tests unitaires et d'intégration | couverture ≥ 80 % sur le domaine |

Aucun code n'est fusionné si `mypy`, `ruff` et `pytest` ne passent pas.

## Conventions de nommage

- **Variables** : noms révélateurs d'intention — `userCount`, pas `n` ni `data`.
- **Booléens** : préfixe `is`/`has`/`can`/`should` — `isAuthenticated`.
- **Fonctions** : verbes d'action — `fetchUser`, `validateToken`.
- **Constantes** : `SCREAMING_SNAKE` (Python/Kotlin), `UPPER_SNAKE` (TypeScript).
- **Abbréviations admises** : `id`, `url`, `api`, `db`, `err`, `ctx`, `req`,
  `res`. Aucune autre.
- **Identifiants en anglais**, commentaires et docstrings en **français**.

## Structure des fonctions

- **30 lignes maximum** par fonction (corps, hors signature/docstring).
- **3 paramètres maximum** ; au-delà, regrouper dans un objet paramètre.
- **Complexité cyclomatique ≤ 5** : extraire les branches en fonctions nommées.
- **Un seul niveau d'abstraction** par fonction.
- **Pas de nombre magique** : tout littéral devient une constante nommée.
- **Pas d'état global mutable**.

## Gestion des erreurs

- **Logger avant de propager** ; ne jamais avaler silencieusement une erreur.
- **Valider aux points d'entrée** ; ne jamais propager de `null`/`None` à
  travers le système.
- **Exceptions typées** : utiliser des hiérarchies d'exceptions métier, pas des
  `Exception` génériques.
- **Aucune donnée sensible** dans les logs, URLs ou messages d'erreur retournés.

## Tests

- Écrits **en même temps** que le code, jamais après.
- Structure **Arrange → Act → Assert**, clairement séparée.
- **Une assertion logique** par test.
- Noms décrivant le comportement : `should_return_401_when_token_expired`.
- Préférer les **fakes et stubs** aux mocks ; tester le comportement, pas
  l'implémentation.
- **Cas limites obligatoires** : entrée vide, `None`, valeurs maximales, accès
  concurrent.
- Tests d'intégration pour toute frontière externe (BD, API, système de
  fichiers).
- Couverture cible : **80 %** sur la logique métier, **60 %** minimum global.

## Commentaires

- Les commentaires expliquent le **pourquoi**, jamais le **quoi** (le code le
  montre).
- **Pas de code commenté** : git s'en souvient, supprimer.
- Les docstrings documentent l'intention, les paramètres, le retour et les
  exceptions levées.

## Imports

- Imports **standard → tiers → projet**, séparés par une ligne vide.
- Pas d'import wildcard (`from x import *`).
- Imports explicites ; pas d'import inutilisé (ruff le détecte).

## Typage

- **mypy strict** : tout paramètre et tout retour sont typés explicitement.
- Pas de `Any` (TypeScript), pas de paramètre non typé (Python).
- Les API publiques ont des signatures explicites.
- Les DTO bornent les frontières ; les modèles domaine restent internes.

## Versionnage

- **Versionnement sémantique** (`MAJEUR.MINEUR.CORRECTIF`).
- Toute rupture de compatibilité est documentée dans le `CHANGELOG.md`.

## Voir aussi

- `DEVELOPMENT_PLAYBOOK.md` — cycle de vie d'une fonctionnalité.
- `CONTRIBUTING_GUIDE.md` — règles de contribution.
- `MASTER_IMPLEMENTATION_GUIDE.md` — référence d'ingénierie complète.

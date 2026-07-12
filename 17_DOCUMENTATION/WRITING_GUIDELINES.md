# Règles de rédaction — GSIE

Livrable : 011 — Système de documentation
Statut : Validated
Version : 1.0
Date : 2026-07-12

## Objet

Définir la manière officielle de rédiger tout document GSIE, afin que le corpus
reste homogène, sobre, traçable et lisible sur vingt ans.

## Langue

- **Tout est rédigé en français** : titres, corps, commentaires, messages de
  commit. Les sigles anglais consacrés (API, SDK, GIS) sont admis.

## Ton

- Sobre, scientifique, factuel. Aucune emphase commerciale.
- Une affirmation scientifique se **source** (`06_RESEARCH/`, `08_DATASETS/`).
  Une connaissance sans origine est une opinion (`GSIE-CON-005`).

## Structure d'un document

- Un titre `#` unique portant l'identifiant et l'intitulé.
- Un bloc d'en-tête : identifiant, édition, version, **statut**, classification
  le cas échéant.
- Des sections `##` hiérarchisées ; pas de saut de niveau.
- Les listes de faits vont en tableaux ; les flux vont en blocs de code.

## Statuts

Tout nouveau document naît en `Draft`. On ne s'auto-attribue jamais
`Validated` ni `Locked` (rôle du Fondateur). Cycle : `Draft` → `Review` →
`Validated` → `Locked`.

## Traçabilité

- Toute décision structurante reçoit un `DEC-` ou un `RFC-`.
- Aucune décision perdue : après un changement d'état, synchroniser
  `PROJECT_MEMORY.md`, `ROADMAP.md`, `CHANGELOG.md`.

## Interdits

- Écrire du remplissage. Un document court et vrai vaut mieux qu'un document
  long et creux.
- Contredire un niveau supérieur de la hiérarchie (Vision → Constitution → …).
- Modifier un document `Locked` hors RFC.

## Déclaration finale

« On n'écrit pas pour aujourd'hui : on écrit pour le lecteur de 2045. »

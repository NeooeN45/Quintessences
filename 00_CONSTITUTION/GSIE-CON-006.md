# GSIE-CON-006 — La Documentation fait partie du Produit

Édition : Première Édition
Version : 1.0 (Validated)
Statut : Validé par le Fondateur
Classification : Loi Fondamentale (Immuable)

## Principe

La documentation n'est pas un livrable secondaire : elle constitue une
partie intégrante du produit GSIE. Aucun composant ne peut être
considéré comme terminé sans une documentation permettant de comprendre
son objectif, son fonctionnement, ses dépendances et ses limites.

## Pourquoi

Le code évolue, les développeurs partent, les technologies changent. La
documentation transmet la connaissance et garantit la maintenabilité
sur la durée. Un projet conçu pour durer 20 ans ne peut pas survivre
sans documentation — le code seul ne suffit pas à comprendre pourquoi
une décision a été prise.

En Phase 1, la documentation est **le** produit principal. Cette loi
formalise ce qui est déjà la pratique du projet.

## Conséquences

- Toute fonctionnalité possède une spécification avant d'être codée.
- Tout moteur possède une documentation technique (README, API, schémas).
- Toute donnée possède une définition et une source.
- Tout algorithme possède une justification scientifique.
- Toute API possède une documentation d'utilisation.
- Tout changement d'architecture fait l'objet d'un ADR (Architecture
  Decision Record).
- Une documentation obsolète est traitée comme un bug.

## Exemple

Le Evidence Engine ne peut pas être considéré comme terminé tant que
son README ne décrit pas : son objectif, ses entrées, ses sorties, ses
niveaux de preuve (A à F), ses dépendances et ses limites. Un moteur
qui fonctionne mais dont la documentation est absente est un composant
inachevé.

## Contre-exemple

Un développeur ajoute un module de calcul d'indice de qualité des
stations. Le code fonctionne, les tests passent, mais aucune
spécification n'existe. Le module est refusé. C'est une violation de
CON-006. La spécification doit précéder ou accompagner le code.

## Références

- `GSIE-DESIGN-PHILOSOPHY.md` — Principe 3 (La documentation avant
  l'implémentation)
- `GSIE-CON-003` — La Connaissance avant le Code
- `TECHNICAL_CONSTITUTION.md` — Article T-6 (Versionnement)

## Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — Première Édition |
| 2026-07-12 | Mise en conformité template RFC-0001, validation Fondateur |

## Statut

ADOPTÉ — Loi Fondamentale Immuable. Modification uniquement par RFC de
révision constitutionnelle.

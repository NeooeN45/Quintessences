# GSIE-CON-007 — La Modularité est obligatoire

Édition : Première Édition
Version : 1.0 (Validated)
Statut : Validé par le Fondateur
Classification : Loi Fondamentale (Immuable)

## Principe

GSIE est construit comme un ensemble de modules indépendants,
faiblement couplés et fortement cohérents. Chaque module possède :

- **une responsabilité unique** — pas de module multi-rôle ;
- **une interface stable** — contrat d'entrée/sortie documenté et
  versionné ;
- **des dépendances minimales** — le graphe de dépendances est acyclique
  ;
- **une testabilité individuelle** — le module peut être testé isolément
  ;
- **un remplacement possible** — un module peut être remplacé sans
  casser les autres si le contrat est respecté.

## Pourquoi

La modularité garantit la pérennité, la maintenabilité et l'évolution du
projet. Un système monolithique ne peut pas évoluer : chaque
modification risque de casser l'ensemble. Un système modulaire permet
de remplacer, améliorer ou tester chaque composant indépendamment.

GSIE est conçu pour durer des décennies. Sur cette durée, des moteurs
entiers seront réécrits. La modularité est la condition qui rend ces
réécritures possibles sans tout reconstruire.

## Conséquences

- Les 14 moteurs sont indépendants et communiquent par interfaces
  contractuelles.
- Aucun moteur n'accède à l'implémentation interne d'un autre.
- Le graphe de dépendances entre moteurs est acyclique.
- Un moteur peut être remplacé par une autre implémentation si le
  contrat d'interface est respecté.
- Les tests d'un moteur ne dépendent pas de l'état des autres moteurs.

## Exemple

Le Climate Engine fournit des données climatiques via son API. Le
Diagnostic Engine consomme cette API sans connaître l'implémentation
sous-jacente (cache local, appel distant, mode dégradé). Si le Climate
Engine est réécrit en Rust, le Diagnostic Engine n'est pas affecté tant
que le contrat d'interface est respecté.

## Contre-exemple

Un moteur accède directement à la base de données d'un autre moteur au
lieu de passer par son API. Le moteur cible change son schéma de base.
Le moteur appelant casse. C'est une violation de CON-007. L'accès
direct doit être remplacé par un appel d'API.

## Références

- `TECHNICAL_CONSTITUTION.md` — Article T-1 (Architecture modulaire) et
  T-2 (Couplage faible)
- `GSIE-DESIGN-PHILOSOPHY.md` — Principe 4 (La modularité avant la
  complexité)
- `GSIE-CON-003` — La Connaissance avant le Code

## Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — Première Édition |
| 2026-07-12 | Mise en conformité template RFC-0001, validation Fondateur |

## Statut

ADOPTÉ — Loi Fondamentale Immuable. Modification uniquement par RFC de
révision constitutionnelle.

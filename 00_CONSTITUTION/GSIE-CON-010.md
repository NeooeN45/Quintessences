# GSIE-CON-010 — Toute connaissance doit pouvoir évoluer sans perdre son historique

Édition : Première Édition
Version : 1.0 (Validated)
Statut : Validé par le Fondateur
Classification : Loi Fondamentale (Immuable)

## Principe

Aucune connaissance n'est figée. Toute évolution doit préserver les
versions précédentes et leur justification.

Chaque évolution d'une connaissance doit :

- **préserver l'historique complet** — les versions précédentes sont
  archivées, jamais supprimées ;
- **versionner** — chaque version porte un numéro et une date ;
- **justifier la modification** — la raison du changement est documentée
  (nouvelle publication, invalidation de source, évolution du consensus)
  ;
- **archiver les règles remplacées** — une règle obsolète reste
  accessible pour audit ;
- **tracer la décision** — qui a décidé de la modification, quand, via
  quel RFC.

## Pourquoi

La science progresse par révision. Une connaissance d'aujourd'hui peut
être invalidée demain par une nouvelle publication. Si l'ancienne
version est perdue, on ne peut plus expliquer les recommandations
passées — or un forestier peut avoir engagé des décisions sur la base
de l'ancienne connaissance et doit pouvoir en retracer l'origine.

L'historique est aussi la garantie de l'honnêteté scientifique : on ne
cache pas ses erreurs, on les archive et on les explique.

## Conséquences

- Aucune modification de connaissance n'écrase l'ancienne version.
- Chaque version archivée reste accessible et citable.
- L'historique des modifications est consultable pour chaque
  connaissance.
- Une recommandation passée peut toujours être ré-auditée avec les
  connaissances qui étaient disponibles à l'époque.
- Les révisions passent par un RFC pour les connaissances
  constitutionnelles, par une procédure documentée pour les
  connaissances opérationnelles.

## Exemple

Un seuil de vulnérabilité au gel pour une essence est fixé à -15°C d'après
une publication de 2015. En 2028, une nouvelle étude montre que le seuil
est en réalité -12°C pour les provenances du Sud. La version 2015
(-15°C) est archivée avec sa source. La version 2028 (-12°C) la remplace
avec la nouvelle référence. Les recommandations émises entre 2015 et
2028 restent explicables : on sait quel seuil était utilisé.

## Contre-exemple

Un développeur met à jour un coefficient de croissance dans la base sans
archiver l'ancienne valeur. Les recommandations émises avec l'ancien
coefficient ne peuvent plus être reproduites. C'est une violation de
CON-010. La mise à jour doit être annulée et reprise avec archivage.

## Références

- `SCIENTIFIC_CONSTITUTION.md` — Article S-4 (Révision des connaissances)
- `GSIE-CON-005` — Toute connaissance doit être traçable
- `GSIE-CON-009` — GSIE est un patrimoine scientifique vivant
- `TECHNICAL_CONSTITUTION.md` — Article T-6 (Versionnement)

## Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — Première Édition |
| 2026-07-12 | Mise en conformité template RFC-0001, validation Fondateur |

## Statut

ADOPTÉ — Loi Fondamentale Immuable. Modification uniquement par RFC de
révision constitutionnelle.

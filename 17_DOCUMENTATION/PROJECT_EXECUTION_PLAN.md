# GSIE Project Execution Plan

Livrable : 011 — Système de documentation
Statut : Validated
Version : 1.0
Date : 2026-07-12

## Objectif

Construire progressivement GSIE jusqu'à une plateforme scientifique
opérationnelle, en respectant la hiérarchie documentaire et la gouvernance.
Ce plan décrit les étapes d'exécution, les critères de succès et les
dépendances entre livrables.

## Étapes d'exécution

| Étape | Phase | Description |
|---|---|---|
| 1 | Phase 1 | Finaliser les 12 livrables Foundation (Constitution, documentation, mémoire) |
| 2 | Phase 2 | Documenter l'architecture détaillée des 14 moteurs et leurs interfaces |
| 3 | Phase 2 | Spécifier les schémas de données et contrats d'interface (ADR) |
| 4 | Phase 3 | Peupler la base de connaissances et les ontologies (sourcé) |
| 5 | Phase 3 | Qualifier et référencer les jeux de données |
| 6 | Phase 4 | Implémenter les moteurs (Knowledge, Evidence, Correlation en premier) |
| 7 | Phase 4 | Implémenter le moteur de diagnostic et la chaîne de raisonnement |
| 8 | Phase 4 | Développer l'application GeoSylva (premier client du moteur) |
| 9 | Phase 5 | Industrialiser et ouvrir aux partenaires |

## Critères de succès

- Chaque livrable atteint le statut **Validated** minimum.
- Toute décision structurante est **tracée** (`DEC-`, ADR, RFC).
- Toute affirmation scientifique est **sourcée** (`GSIE-CON-005`).
- Le code métier est **testé** (couverture ≥ 80 %), **documenté** et
  **conforme** aux `CODING_STANDARDS.md`.
- La documentation et la mémoire projet restent **synchronisées** à chaque
  changement d'état.

## Jalons

| Jalon | Phase | Condition de clôture |
|---|---|---|
| M1 — Foundation clôturée | Phase 1 | 12 livrables Validated/Locked |
| M2 — Architecture validée | Phase 2 | 14 moteurs documentés + interfaces spécifiées |
| M3 — Connaissance qualifiée | Phase 3 | Base de connaissances sourcée et référentiels validés |
| M4 — Premier prototype | Phase 4 | Diagnostic Engine opérationnel sur une essence forestière |
| M5 — Application GeoSylva | Phase 4 | Application cliente déployable et fonctionnelle |
| M6 — Industrialisation | Phase 5 | CI/CD complète, API publique stabilisée |

## Dépendances entre livrables

```
Livrable 011 (Documentation) → Livrable 012 (Mémoire complète)
                                → Clôture Phase 1
                                → Phase 2 (Architecture)
                                → Phase 3 (Connaissance)
                                → Phase 4 (Implémentation)
                                → Phase 5 (Industrialisation)
```

- Un livrable ne passe en **Review** que si le précédent est au minimum en
  **Review** (ordre imposé).
- Une phase ne démarre que lorsque la précédente est **clôturée** (tous ses
  jalons Validated).
- L'architecture (Phase 2) dépend de la Constitution et de la documentation
  (Phase 1).
- L'implémentation (Phase 4) dépend de l'architecture (Phase 2) et de la
  connaissance (Phase 3).

## Règle

Toujours privilégier une **architecture robuste** à une fonctionnalité rapide.
La gouvernance prime sur la vitesse. En cas de doute, s'arrêter et signaler
plutôt que contourner une règle.

## Voir aussi

- `MASTER_ROADMAP.md` — vue d'ensemble des phases.
- `ROADMAP.md` (racine) — détail des livrables et statuts.
- `DEVELOPMENT_PLAYBOOK.md` — cycle de vie d'une fonctionnalité.

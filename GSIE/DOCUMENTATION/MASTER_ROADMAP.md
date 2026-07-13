# GSIE Master Roadmap

Livrable : 011 — Système de documentation
Statut : Validated
Version : 1.0
Date : 2026-07-12

## Objet

Synthèse de la roadmap GSIE, alignée sur `ROADMAP.md` racine. Ce document
donne la vue d'ensemble des phases du projet ; le détail des livrables et
statuts se trouve dans `ROADMAP.md` et `PROJECT_MEMORY.md`.

## Phase 1 — Foundation (courante)

> Lancée par **GSIE-DIR-0003**. La documentation est le produit. Aucun
> développement métier avant validation des 12 livrables.

| Jalons | Critère de succès |
|---|---|
| Constitution complète | Articles 000-010 validés (Locked/Validated) |
| 12 livrables validés | Tous au minimum `Validated` |
| Mémoire projet complète | `22_PROJECT_MEMORY/` synchronisée |

**Avancement** : 10/12 livrables Validated ou Locked. Reste les livrables 011
(documentation) et 012 (mémoire complète).

## Phase 2 — Architecture

| Jalons | Critère de succès |
|---|---|
| Architecture détaillée des 14 moteurs | Chaque moteur documenté en profondeur |
| Contrats d'interface entre moteurs | Interfaces validées et tracées (ADR) |
| Schémas de données | Modèles de données validés |
| RFC-0003 (GSIE-Net) activé | Architecture distribuée spécifiée |
| RFC-0004 (Ignis) activé | Branche incendie spécifiée |

## Phase 3 — Connaissance

| Jalons | Critère de succès |
|---|---|
| Base de connaissances structurée | `GSIE/KNOWLEDGE/` peuplé et sourcé |
| Ontologies et taxonomies | Référentiels validés scientifiquement |
| Sourcing scientifique | Toute affirmation sourcée (`GSIE-CON-005`) |
| Jeux de données référencés | `GSIE/DATASETS/` qualifié |

## Phase 4 — Implémentation

| Jalons | Critère de succès |
|---|---|
| Moteurs implémentés | 14 moteurs opérationnels et testés |
| API et SDK | Contrats publics documentés |
| Application GeoSylva | Première application cliente du moteur |
| Fonctionnement hors ligne | Validé sur le terrain |

## Phase 5 — Industrialisation

| Jalons | Critère de succès |
|---|---|
| Ouverture partenaires | API publique stabilisée |
| Industrialisation | CI/CD complète, monitoring, alerting |
| Patrimoine vivant | Évolution sans perte d'historique (`GSIE-CON-010`) |

## Règle transverse

Chaque phase fait l'objet d'une **Directive dédiée** (`01_DIRECTIVES/`). Une
phase ne se clôture que lorsque tous ses jalons sont au minimum `Validated`.
La gouvernance prime toujours sur la vitesse.

## Voir aussi

- `ROADMAP.md` (racine) — détail des livrables et statuts.
- `PROJECT_EXECUTION_PLAN.md` — plan d'exécution et dépendances.
- `PROJECT_MEMORY.md` (racine) — état courant du projet.

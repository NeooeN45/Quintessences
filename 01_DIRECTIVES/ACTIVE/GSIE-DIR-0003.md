# ============================================================================
# GSIE FOUNDATION DIRECTIVE
# Directive ID : GSIE-DIR-0003
# Version : 1.0
# Statut : ACTIVE
# Priorité : CRITIQUE
# Classification : FONDATION
# Auteur : Camille Perraudeau
# Date : 2026-07-01
# ============================================================================

# Titre : Lancement officiel de la Phase 1 – Foundation

## Résumé exécutif

La Phase 1 « Foundation » est officiellement lancée. Elle est composée
de **12 livrables obligatoires**. Aucun développement métier ne
commencera avant leur validation. La **documentation devient le cœur du
projet** durant cette phase.

## Décisions validées

1. La documentation devient le cœur du projet.
2. La Phase 1 est composée de 12 livrables obligatoires.
3. Aucun développement métier ne commencera avant leur validation.
4. Les livrables sont produits dans l'ordre défini ci-dessous.
5. Les futures discussions se concentrent exclusivement sur ces
   livrables jusqu'à la clôture de la Phase 1.

## Les 12 livrables de la Phase 1

| # | Livrable | Fichier / Dossier | Statut |
|---|---|---|---|
| 001 | Structure documentaire et arborescence officielle | `GSIE/` (ensemble) | Validated |
| 002 | Préambule Constitutionnel | `00_CONSTITUTION/CONSTITUTIONAL_PREAMBLE.md` | Draft |
| 003 | Préambule Philosophique | `00_CONSTITUTION/PHILOSOPHICAL_PREAMBLE.md` | Draft |
| 004 | Article 000 — Primauté de la Constitution | `00_CONSTITUTION/ARTICLE_000.md` | Validated |
| 005 | Pacte pour les IA | `00_CONSTITUTION/PACT_FOR_AI_AGENTS.md` | Draft |
| 006 | Philosophie de conception | `00_CONSTITUTION/DESIGN_PHILOSOPHY.md` | Draft |
| 007 | Constitution scientifique | `00_CONSTITUTION/SCIENTIFIC_CONSTITUTION.md` | Draft |
| 008 | Constitution technique | `00_CONSTITUTION/TECHNICAL_CONSTITUTION.md` | Draft |
| 009 | Constitution de l'IA | `00_CONSTITUTION/AI_CONSTITUTION.md` | Draft |
| 010 | Articles constitutionnels 001-100 | `00_CONSTITUTION/ARTICLE_001.md` à `ARTICLE_100.md` | Draft |
| 011 | Système de documentation et guides contributeurs | `GSIE/DOCUMENTATION/` | Draft |
| 012 | Mémoire du projet complète et snapshots | `22_PROJECT_MEMORY/` | Draft |

### Règles de statut

| Statut | Définition |
|---|---|
| **Draft** | Fichier créé, contenu non rédigé ou en cours de rédaction |
| **Review** | Contenu rédigé, en attente de relecture par le fondateur |
| **Validated** | Contenu rédigé et validé par le fondateur |
| **Locked** | Validé et verrouillé — toute modification requiert un RFC |

## Contexte

Le projet a posé son arborescence (DIR-0001) et ses documents fondateurs
préliminaires (préambules, Article 000). La Phase 1 formalise le
processus : 12 livrables à produire dans l'ordre, sans déviation, avant
tout développement.

## État actuel du projet

- **Phase active** : Foundation
- **Priorité absolue** : Constitution, gouvernance, architecture
  documentaire
- **Développement logiciel** : Suspendu, sauf organisation documentaire
- **Livrables validés** : 001 (structure), 004 (Article 000)
- **Livrables en brouillon** : 002, 003 (préambules rédigés, en attente
  de validation)
- **Livrables en attente** : 005 à 012

## Vision à cet instant T

GSIE est une fondation scientifique. Durant la Phase 1, le produit
principal n'est pas le code — c'est la **documentation**. La
Constitution, les RFC, les Directives et la mémoire du projet sont les
véritables livrables. Le code viendra en son temps, subordonné à ces
fondations.

## Engagements de l'architecte

- Produire les livrables dans l'ordre strict défini ci-dessus.
- Ne jamais anticiper un livrable avant que le précédent ne soit au
  minimum en statut **Review**.
- Maintenir la traçabilité de chaque livrable dans `ROADMAP.md` et
  `22_PROJECT_MEMORY/`.

## Engagements du fondateur

- Valider ou rejeter chaque livrable présenté en statut **Review**.
- Ne pas demander de développement métier avant la clôture de la Phase 1.
- Concentrer les discussions sur les livrables en cours.

## Documents impactés

- `ROADMAP.md` — ajout de la section Foundation Roadmap
- `PROJECT_MEMORY.md` — entrée sur la documentation comme produit principal
- `22_PROJECT_MEMORY/PROJECT_MEMORY.md` — mise à jour de l'état
- `22_PROJECT_MEMORY/DECISION_HISTORY.md` — nouvelle décision
- `CHANGELOG.md` — version 0.0.3
- `GSIE/DOCUMENTATION/` — création des fichiers du livrable 011

## Fichiers à créer

- `GSIE/DOCUMENTATION/CONTRIBUTING_GUIDE.md` (vide)
- `GSIE/DOCUMENTATION/DOCUMENTATION_SYSTEM.md` (vide)
- `GSIE/DOCUMENTATION/ADR_TEMPLATE.md` (vide)
- `GSIE/DOCUMENTATION/WRITING_GUIDELINES.md` (vide)
- `22_PROJECT_MEMORY/CONTEXT_SNAPSHOT_001.md` (vide — sera rempli à la
  10e Directive)

## Fichiers à modifier

- `ROADMAP.md`
- `PROJECT_MEMORY.md`
- `22_PROJECT_MEMORY/PROJECT_MEMORY.md`
- `22_PROJECT_MEMORY/DECISION_HISTORY.md`
- `22_PROJECT_MEMORY/ARCHITECT_JOURNAL.md`
- `22_PROJECT_MEMORY/VISION_HISTORY.md`
- `CHANGELOG.md`

## RFC impactées

- Aucune RFC directement impactée. La RFC-0001 reste le cadre
  méthodologique pour les livrables 002 à 010.

## Décisions impactées

- DEC-000002 (Phase 1 : Fondation) — précisée et formalisée par cette
  directive.

## Idées reportées

- Aucune à ce stade.

## Risques

- **Risque d'épuisement documentaire** : 12 livrables représentent un
  volume important. Mitigation : avancer dans l'ordre, un livrable à la
  fois.
- **Risque de tentation de développement** : la pression pour coder
  pourrait surgir. Mitigation : la Directive interdit tout
  développement métier avant clôture de la Phase 1.

## Actions pour les IA

1. Créer les fichiers vides manquants pour les livrables 005 à 012.
2. Mettre à jour `ROADMAP.md` avec la Foundation Roadmap.
3. Mettre à jour `PROJECT_MEMORY.md` avec l'entrée sur la documentation.
4. Préparer le Livrable 002 pour passage en statut **Review**.

## Prochaine étape

Commencer la rédaction complète du **Livrable 002 — Préambule
Constitutionnel**, qui définira officiellement l'autorité de la
Constitution GSIE, la hiérarchie documentaire et les règles d'évolution
de tous les documents du projet.

FIN DE DIRECTIVE.

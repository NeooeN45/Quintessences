---
name: consortium-agents
description: |
  Consortium d'agents GSIE — boucle poussée à 9 phases avec déclenchement
  adaptatif (léger / standard / lourd) et séparation des rôles
  (architecte / implémenteur / testeur / reviewer). Intègre et étend
  AI_AGENT_ORCHESTRATION.md sans le dupliquer. Conçu pour GLM 5.2 High
  (contexte 1M, tokens illimités, sous-agents parallèles massifs).
trigger: |
  Tâche GSIE complexe (migration DB, API publique, architecture, sécurité,
  >10 fichiers) OU demande explicite du Fondateur « consortium » /
  « boucle poussée » / « best in class » / « 4 agents » / « revue
  indépendante ». Ne PAS déclencher pour les tâches simples (<5 fichiers,
  pas de migration, pas d'API publique) — utiliser la micro-boucle.
---

# Consortium d'agents GSIE — boucle poussée adaptative

## 1. Objet

Ce skill formalise le **consortium d'agents** : une boucle de travail
poussée à 9 phases qui sépare qui conçoit, qui implémente, qui teste et
qui révise. Il s'intègre au processus existant
`23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md` (RACI, états
de tâche, portes renforcées) sans le dupliquer — il l'**enrichit** d'un
schéma d'exécution concret pour les tâches à haut risque.

## 2. Méthode GLM 5.2 High

Ce skill est conçu pour fonctionner avec la méthode
`/methode-glm52-high` :

- tokens illimités — profondeur maximale sans économie ;
- sous-agents en parallèle massif — plusieurs vagues si besoin ;
- recherche approfondie — web, docs, comparaisons ;
- rapports toutes les ~20 minutes ;
- approche « best in class » — état de l'art, pas minimum viable ;
- décider et exécuter — valider par preuves, reporter seulement les
  décisions structurantes.

## 3. Gating adaptatif — 3 niveaux de cérémonie

La cérémonie est **proportionnelle au risque**. Ne pas appliquer 9
phases + 4 agents à un fix one-line.

### Niveau LÉGER — micro-boucle

| Critère | Valeur |
|---|---|
| Fichiers touchés | < 5 |
| Migration DB | Non |
| API publique | Non |
| Architecture | Non |
| Sécurité | Non |

**Process** : fix → test ciblé → inspection diff → commit.
**Agents** : 1 (implémenteur seul).
**Pas de revue indépendante** — l'agent s'auto-vérifie via tests.

### Niveau STANDARD — boucle tâche

| Critère | Valeur |
|---|---|
| Fichiers touchés | 5 à 15 |
| Migration DB | Non, ou additive only |
| API publique | Endpoint nouveau, pas de breaking |
| Architecture | Module complet, pas transverse |

**Process** : qualification → reconnaissance → plan → implémentation
incrémentale → tests pyramide → PR dossier de preuve.
**Agents** : 1 implémenteur + 1 reviewer (skill `code-review`).
**Revue** : diff final contre critères d'acceptation.

### Niveau LOURD — consortium complet

| Critère | Valeur |
|---|---|
| Fichiers touchés | > 15 OU transverse |
| Migration DB | Oui, ou breaking |
| API publique | Breaking change |
| Architecture | Transverse, nouveau moteur, nouveau sous-système |
| Sécurité | Auth, crypto, RLS, secrets, PII |

**Process** : 9 phases complètes (§4) + 4 agents (§5).
**Revue** : adversariale indépendante obligatoire.
**Validation Fondateur** : requise avant fusion.

### Arbre de décision

```
La tâche touche-t-elle > 15 fichiers OU est-elle transverse ?
├─ OUI → LOURD (consortium complet)
└─ NON → Migration DB breaking OU API publique breaking OU sécurité ?
   ├─ OUI → LOURD
   └─ NON → 5 à 15 fichiers OU module complet OU endpoint nouveau ?
      ├─ OUI → STANDARD
      └─ NON → LÉGER
```

## 4. Les 9 phases (niveau LOURD)

### Phase 1 — Qualification

Transformer la demande en **contrat vérifiable**. Produire :

- objectif utilisateur ;
- comportement attendu ;
- comportement actuel ;
- critères d'acceptation (liste cochable) ;
- éléments hors périmètre ;
- risques possibles ;
- définition précise de « terminé ».

**Règle** : si la demande est ambiguë, poser **une seule** question
clariﬁante. Pour les autres incertitudes, formuler une hypothèse
explicite et réversible.

### Phase 2 — Reconnaissance

Reverse engineering **ciblé**, pas lecture aveugle du dépôt. Rechercher :

- point d'entrée de la fonctionnalité ;
- flux de données complet ;
- composants similaires déjà existants ;
- conventions du projet (AGENTS.md, .devin/rules/, skills applicables) ;
- tests correspondants ;
- dépendances concernées ;
- décisions architecturales documentées (03_DECISIONS/, 02_RFC/) ;
- zones de régression potentielle.

**Produire** : une carte d'impact concise (fichiers, flux, persistance,
affichage, tests existants, risques).

**Outil** : sous-agent `architecte` (read-only) ou `subagent_explore`
pour exploration parallèle.

### Phase 3 — Plan avec niveaux de confiance

Chaque étape du plan doit comporter :

- fichiers concernés ;
- modification prévue ;
- justification ;
- méthode de vérification ;
- risque ;
- niveau de confiance (0 à 100 %).

**Règle de confiance** : si une étape a une confiance < 80 %, effectuer
d'abord une investigation, un test ou un prototype isolé.

**Attente de validation Fondateur** obligatoire si :
- migration de données nécessaire ;
- API publique change ;
- > 10 fichiers à modifier ;
- architecture affectée ;
- suppression de données ou de fonctionnalités.

### Phase 4 — Implémentation par petites unités

Granularité : **une intention logique → un petit ensemble de fichiers →
une vérification → un commit éventuel → étape suivante**.

Après chaque unité :
1. compile ou vérifie la syntaxe ;
2. exécute les tests ciblés ;
3. inspecte le diff ;
4. confirme que le périmètre n'a pas dérivé.

**Ne pas poursuivre** si une vérification échoue.

### Phase 5 — Diagnostic fondé sur la cause racine

Quand un test échoue, **ne jamais appliquer immédiatement un correctif
au hasard**. Suivre :

1. reproduire l'échec ;
2. collecter les preuves (logs, stack trace, état DB) ;
3. identifier la **première erreur réellement causale** ;
4. distinguer symptôme, facteur aggravant et cause racine ;
5. formuler au maximum **3 hypothèses** ;
6. concevoir le test le moins coûteux pour les départager ;
7. appliquer la **correction minimale** ;
8. ajouter un **test de non-régression**.

**Skill associé** : `/debug-moteur` pour les moteurs GSIE.

### Phase 6 — Tests en pyramide

Vérifier successivement, du moins coûteux au plus coûteux :

```
formatage + compilation
    ↓
analyse statique (lint, typage)
    ↓
tests unitaires ciblés
    ↓
tests du module complet
    ↓
tests d'intégration (DB, API, frontières)
    ↓
tests de non-régression
    ↓
test fonctionnel réel
    ↓
validation visuelle (émulateur / navigateur / UE5.8)
```

**Ne jamais déclarer terminé** uniquement parce que le code compile.

**Skill associé** : `/tests-gsie` pour la stratégie de tests GSIE.

### Phase 7 — Revue adversariale indépendante

L'agent qui écrit le code **ne doit pas** être le seul à l'évaluer.
Voir §5 pour la séparation des rôles.

Le reviewer agit comme un **reviewer hostile mais constructif**.
Recherche :

- régressions ;
- pertes de données ;
- conditions de concurrence ;
- erreurs de cycle de vie ;
- erreurs silencieuses ;
- gestion incomplète des entrées invalides ;
- dette technique inutile ;
- duplication ;
- violations architecturales ;
- problèmes de sécurité ;
- problèmes de performance ;
- tests qui réussissent pour de mauvaises raisons.

Classement : **bloquant** / **majeur** / **mineur** / **suggestion**.

Corriger les bloquants + majeurs, puis relancer les validations.

**Skill associé** : `/code-review` (6 dimensions) ou sous-agent `qa`.

### Phase 8 — Livraison (PR dossier de preuve)

Utiliser le template existant `.github/pull_request_template.md` qui
couvre déjà : objet, traçabilité, preuves, déploiement, retour arrière,
risques résiduels.

Compléter avec les sections consortium si non présentes :

- **Cause identifiée** (root cause) ;
- **Solution retenue** et justification ;
- **Alternatives rejetées** avec motif ;
- **Tests exécutés** (liste cochable) ;
- **Preuves** (capture, vidéo, logs, CI) ;
- **Procédure de retour arrière** explicite.

### Phase 9 — Capitalisation

Après une tâche réussie, demander :

> Qu'avons-nous appris qui devrait survivre à cette session ?

Répartir l'information selon le tableau existant du système GSIE :

| Type | Emplacement |
|---|---|
| Architecture permanente | `GSIE/ARCHITECTURE/` |
| Instructions générales | `AGENTS.md` |
| Règle liée à certains fichiers | `.devin/rules/` |
| Procédure répétable | `.devin/skills/.../SKILL.md` |
| Décision importante | `03_DECISIONS/DEC-xxxxxx.md` |
| Dette non traitée | Issue GitHub |
| Mémoire de session | `22_PROJECT_MEMORY/` via `/session-archive` |

**Skill associé** : `/session-archive` pour l'archivage de session.

## 5. Séparation des rôles (niveau LOURD)

Quatre rôles, mappés sur les profils subagent existants de Devin :

| Rôle | Profil subagent | Accès | Responsabilité |
|---|---|---|---|
| Architecte | `architecte` | Read-only | Analyse, plan, conséquences architecturales. **Ne modifie aucun fichier.** |
| Implémenteur | `backend` ou `subagent_general` | Écriture | Applique le plan validé. Incréments vérifiables. **Ne change pas l'architecture sans signaler.** |
| Testeur adversarial | `qa` | Écriture (tests) | Part du principe que l'implémentation est incorrecte. Cherche cas limites, pertes données, concurrence, entrées invalides. **Ne corrige pas le code.** |
| Reviewer | `code-review` skill ou `qa` | Read-only | Examine le diff final + critères d'acceptation. Classe les observations. Ignore les préférences stylistiques (linters s'en chargent). |

### Orchestration pratique

```
Vague 1 (parallèle) :
  └─ Architecte (foreground) → produit plan + carte d'impact
                              → validation Fondateur si breaking

Vague 2 (séquentiel) :
  └─ Implémenteur (foreground) → exécute le plan par incréments
                                → tests ciblés après chaque incrément

Vague 3 (parallèle à l'implémenteur sur modules indépendants) :
  └─ Testeur adversarial (background) → écrit tests de cas limites
                                       → sur modules déjà stabilisés

Vague 4 (après implémentation complète) :
  └─ Reviewer (foreground) → revue diff final
                            → verdict bloquant/majeur/mineur/suggestion

Vague 5 (corrections éventuelles) :
  └─ Implémenteur → corrige bloquants + majeurs
                  → relance validations
```

### Contraintes de coordination

- **Pas de chevauchement de fichiers** entre sous-agents simultanés
  (règle AI_AGENT_ORCHESTRATION.md §5.4).
- **Sous-agents stateless** : front-load tout le contexte nécessaire
  dans le prompt de chaque sous-agent (fichiers, symboles, plan,
  critères).
- **Sous-agents background** : ne peuvent pas demander approval —
  outils auto-deniés. Prévoir les permissions ou utiliser foreground.
- **Un seul sous-agent foreground** à la fois.

## 6. Les 3 boucles imbriquées

### Boucle micro (minutes)

```
petite modification → test ciblé → inspection diff → commit
```

### Boucle tâche (heures)

```
spécification → reconnaissance → plan → implémentation
→ tests → revue indépendante → PR
```

### Boucle projet (hebdomadaire)

```
analyser les échecs de Devin
  → identifier les instructions manquantes
  → améliorer Knowledge, Rules et Skills
  → mesurer le taux de réussite
```

**C'est la boucle projet qui fait la différence** : au bout de
plusieurs semaines, le système de travail est spécialisé pour GSIE,
GeoSylva et Quintessences, amélioré à partir de chaque erreur passée.

**Métrique clé** : taux de réussite première passe (objectif > 80 %).

## 7. Intégration avec l'existant GSIE

Ce skill **ne remplace pas** :

- `AI_AGENT_ORCHESTRATION.md` (RACI, états, portes) — il l'enrichit
  d'un schéma d'exécution concret ;
- `gsie-governance` (gouvernance constitutionnelle, statuts Locked) —
  il s'y soumet ;
- `session-archive` (capitalisation post-session) — il l'utilise ;
- `audit-phase4` (audit qualité complet) — il le déclenche en fin de
  tâche LOURD ;
- `code-review` (revue 6 dimensions) — il l'utilise en phase 7 ;
- `.github/pull_request_template.md` (PR dossier de preuve) — il le
  référence en phase 8.

Ce skill **ajoute** :

- le gating adaptatif 3 niveaux (léger / standard / lourd) ;
- la séparation formelle des 4 rôles sur les tâches LOURD ;
- les 9 phases comme workflow canonique pour le niveau LOURD ;
- les 3 boucles imbriquées (micro / tâche / projet) ;
- le seuil de confiance 80 % comme gate d'implémentation.

## 8. Prompt maître associé

Le prompt maître complet est dans `.devin/playbooks/feature.devin.md`.
Il est activable manuellement via Devin, pas imposé systématiquement.

## 9. Conformité gouvernance

- Respecte `00_CONSTITUTION/` (primauté constitutionnelle) ;
- Respecte les statuts `Locked` (modification uniquement via RFC) ;
- Respecte `AI_AGENT_ORCHESTRATION.md` (RACI, états, portes) ;
- Traçabilité : toute tâche LOURD → `GSIE-PROMPT-xxxx` dans
  `GSIE/PROMPTS/REGISTER.md` ;
- Mémoire : mise à jour `PROJECT_MEMORY.md` après toute tâche LOURD.

## 10. Références

- `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md`
- `.devin/skills/methode-glm52-high/SKILL.md`
- `.devin/skills/gsie-governance/SKILL.md`
- `.devin/skills/session-archive/SKILL.md`
- `.devin/skills/audit-phase4/SKILL.md`
- `.devin/skills/code-review/SKILL.md`
- `.devin/skills/debug-moteur/SKILL.md`
- `.devin/skills/tests-gsie/SKILL.md`
- `.devin/playbooks/feature.devin.md`
- `.devin/rules/consortium-gating.md`
- `.github/pull_request_template.md`

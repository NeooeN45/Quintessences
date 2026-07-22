# RFC-0022 — Orchestration contrôlée des agents IA

| Champ | Valeur |
|---|---|
| **Statut** | Adopté (2026-07-22, DEC-000032) |
| **Auteur** | Direction technique |
| **Date** | 2026-07-22 |
| **Décision liée** | DEC-000032 |
| **Périmètre** | Quintessences, GSIE, GeoSylva, Forge et agents de développement |

## 1. Problème

Plusieurs agents IA peuvent analyser ou modifier le projet avec des contextes,
forces et environnements différents. Sans orchestration unique, ils peuvent
travailler sur une documentation périmée, modifier les mêmes fichiers,
annoncer des vérifications non exécutées, élargir le périmètre ou faire
accepter leur propre production sans contrôle indépendant.

Une conversation, un rapport d'agent ou une session Devin n'est pas une source
de vérité. L'accélération permise par les agents ne doit pas affaiblir la
Constitution, la traçabilité scientifique ni les portes qualité de RFC-0021.

## 2. Décision

### 2.1 Autorité et responsabilités

- Le **Fondateur** conserve l'autorité finale sur la vision, les priorités,
  les arbitrages scientifiques, juridiques et commerciaux.
- **Codex** assure l'orchestration technique : état courant, découpage,
  attribution, prévention des conflits, vérification des preuves, revue des
  diffs et recommandation d'acceptation ou de rejet.
- **Claude** est privilégié pour la contre-analyse, l'architecture, la revue
  adversariale et les sujets nécessitant une forte compréhension transverse.
- **GLM 5.2** est privilégié pour les implémentations bornées, inventaires,
  migrations mécaniques et matrices de tests dont les critères sont
  déterministes.
- **Devin** est un environnement d'exécution et de coordination. Son état ou
  sa mémoire ne remplace jamais Git ni les documents canoniques.

Aucun agent n'est réputé infaillible. Une production IA est une contribution
à vérifier, jamais une décision auto-exécutoire.

### 2.2 Cycle obligatoire d'une tâche

Une tâche suit le cycle :

`PROPOSÉE → PRÊTE → ASSIGNÉE → EN_COURS → EN_REVUE → VALIDÉE → INTÉGRÉE`

Les états `BLOQUÉE`, `REJETÉE` et `ANNULÉE` sont possibles. Une tâche
n'est `PRÊTE` que si son périmètre, ses sources, ses critères d'acceptation,
ses interdictions et son mécanisme de retour arrière sont explicites.

### 2.3 Contrat minimal d'un prompt

Chaque prompt versionné `GSIE-PROMPT-xxxx` indique au minimum :

1. identifiant, dépôt, branche et état de référence ;
2. objectif mesurable et justification ;
3. périmètre autorisé et non-objectifs ;
4. documents canoniques à lire avant toute action ;
5. fichiers autorisés et zones interdites ;
6. risques, hypothèses et conditions d'arrêt ;
7. commandes de validation attendues ;
8. livrables et format du rapport de fin ;
9. interdiction de commit, push, fusion ou déploiement sans autorisation ;
10. obligation de signaler ce qui n'a pas été vérifié.

### 2.4 Séparation des rôles

- L'agent qui produit un changement ne valide pas seul son propre travail.
- Les tâches critiques de sécurité, données, migration ou science exigent une
  contre-revue indépendante avant recommandation de fusion.
- Codex vérifie le diff réel et les résultats reproductibles ; il ne se
  contente pas du résumé de l'agent.
- Seul le Fondateur ou un humain explicitement délégué autorise une décision
  juridique, une dépense, un déploiement de production ou une publication.

### 2.5 Concurrence et propriété des fichiers

Deux agents ne modifient pas simultanément les mêmes fichiers. Les tâches
parallèles doivent avoir des périmètres disjoints et des dépendances
déclarées. Si un chevauchement apparaît, la tâche la moins prioritaire
s'arrête et remonte le conflit à l'orchestrateur.

### 2.6 Portes d'acceptation

Aucun résultat d'agent n'est accepté sans :

- diff limité au périmètre autorisé ;
- absence de secret et de modification d'un document `Locked` ;
- tests et contrôles statiques adaptés au risque ;
- preuve des commandes réellement exécutées ;
- mise à jour de la documentation et de la mémoire si l'état change ;
- risques résiduels explicitement consignés ;
- revue humaine ou indépendante conforme au processus de revue de code.

## 3. Sécurité opérationnelle

Les agents utilisent le moindre privilège, ne copient pas de secret dans un
prompt et ne publient pas de données privées. Toute action externe
irréversible, toute modification de production et toute dépense exigent une
autorisation distincte du Fondateur.

## 4. Critères d'acceptation

- Le processus `AI_AGENT_ORCHESTRATION.md` est versionné dans le QMS.
- Un registre et un modèle de prompts existent dans `GSIE/PROMPTS/`.
- Les guides `AGENTS.md` et `CLAUDE.md` renvoient vers le processus.
- Les premiers prompts Claude et GLM 5.2 sont préparés mais non envoyés sans
  validation de leur snapshot de travail.
- Le registre des sources de vérité contrôle les instructions opérationnelles
  des agents.

## 5. Limites

La présente RFC n'autorise ni l'accès automatique à Devin, ni la création de
comptes, ni un push, une fusion ou un déploiement. En l'absence de connecteur
Devin disponible, les prompts sont remis au Fondateur pour transmission
manuelle et leurs résultats reviennent à Codex pour revue.

## 6. Retour arrière

Le processus et les prompts peuvent être retirés par une nouvelle décision
sans modifier le Pacte constitutionnel des Agents IA. Les changements de code
produits par une tâche conservent leur propre stratégie de retour arrière.

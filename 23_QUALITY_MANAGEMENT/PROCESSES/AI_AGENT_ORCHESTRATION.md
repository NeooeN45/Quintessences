# Processus d'orchestration des agents IA

| Champ | Valeur |
|---|---|
| Document | AI_AGENT_ORCHESTRATION.md |
| Dossier | 23_QUALITY_MANAGEMENT/PROCESSES |
| Version | 1.0.0 |
| Date | 22 juillet 2026 |
| Statut | Adopté |
| Référence | RFC-0022, DEC-000032, PACT_FOR_AI_AGENTS.md |

## 1. Objet

Ce processus organise les contributions de Codex, Claude, GLM 5.2 et des
environnements d'exécution tels que Devin. Il impose un responsable unique de
l'orchestration, des tâches bornées, une séparation entre production et
acceptation et des preuves reproductibles.

## 2. Principes

1. Le Fondateur décide ; les agents conseillent et exécutent.
2. Git et les documents canoniques priment sur la mémoire d'une conversation.
3. Codex contrôle la file de travail et la cohérence transverse.
4. Un prompt correspond à un objectif vérifiable et à un périmètre borné.
5. Aucun rapport d'agent ne remplace l'inspection du diff et l'exécution des
   contrôles.
6. Une tâche critique reçoit une revue indépendante.
7. Les résultats négatifs, incertains ou incomplets sont conservés.

## 3. RACI

| Activité | Fondateur | Codex | Claude | GLM 5.2 | Devin |
|---|---|---|---|---|---|
| Vision et priorité finale | A/R | C | C | I | I |
| Découpage et ordonnancement | A | R | C | C | I |
| Architecture complexe | A | R | R/C | C | I |
| Implémentation bornée | I | A | R/C | R | Support |
| Exécution des tests | I | A | C | R | Support |
| Revue indépendante | I | A/R | R | C | Support |
| Acceptation technique | A | R | C | C | I |
| Décision juridique/scientifique | A/R | C | C | I | I |
| Push, fusion, déploiement | A/R | C | I | I | Support autorisé |

R = réalise, A = autorité, C = consulté, I = informé.

## 4. États d'une tâche

| État | Condition |
|---|---|
| PROPOSÉE | Besoin identifié, périmètre encore à qualifier |
| PRÊTE | Prompt complet, dépendances et critères vérifiés |
| ASSIGNÉE | Agent, modèle, environnement et snapshot identifiés |
| EN_COURS | Exécution commencée sur le snapshot convenu |
| BLOQUÉE | Condition d'arrêt rencontrée ; aucune extension implicite |
| EN_REVUE | Rapport et diff remis à Codex |
| VALIDÉE | Preuves reproduites et critères satisfaits |
| INTÉGRÉE | Changement fusionné par l'autorité compétente |
| REJETÉE | Résultat incorrect, dangereux ou hors périmètre |
| ANNULÉE | Besoin retiré avec motif conservé |

## 5. Préparation par l'orchestrateur

Avant attribution, Codex :

1. consulte `PROJECT_MEMORY.md`, `ROADMAP.md`, le registre de sources et
   les règles du dépôt cible ;
2. vérifie la branche, le statut Git et les changements non publiés ;
3. choisit un objectif livrable sans dépendance cachée ;
4. assigne des fichiers ou répertoires sans chevauchement ;
5. inscrit les non-objectifs, interdictions et conditions d'arrêt ;
6. définit les tests et preuves proportionnés au risque ;
7. choisit Claude pour la contre-analyse ou GLM 5.2 pour une exécution bornée ;
8. attribue un identifiant `GSIE-PROMPT-xxxx` et met à jour le registre.

Une tâche n'est jamais envoyée à un agent distant si son snapshot de travail
n'est pas accessible et identifiable par commit, branche ou archive contrôlée.

## 6. Exécution dans Devin

L'agent exécutant doit :

- confirmer le dépôt, la branche et le commit observés ;
- lire tous les documents obligatoires listés dans le prompt ;
- signaler un dépôt sale ou une divergence avant de modifier ;
- rester dans les fichiers autorisés ;
- appliquer les tests avant et après ;
- ne masquer aucun échec, avertissement pertinent ou test ignoré ;
- ne pas committer, pousser, fusionner ou déployer sans permission ;
- remettre le diff, les commandes, résultats et risques résiduels.

Si un secret, un document `Locked`, une migration destructive, une donnée
réelle non sauvegardée ou un conflit de périmètre apparaît, l'agent s'arrête.

## 7. Revue par Codex

Codex ne valide pas un résumé seul. Il :

1. compare le snapshot de départ et le diff réel ;
2. vérifie chaque fichier contre le périmètre autorisé ;
3. inspecte les changements sécurité, données, concurrence et migrations ;
4. réexécute les contrôles déterminants dans un environnement indépendant ;
5. vérifie les assertions scientifiques contre les sources canoniques ;
6. identifie les tests absents et les risques non annoncés ;
7. rend un verdict : accepter, demander correction, scinder ou rejeter ;
8. synchronise mémoire, roadmap, changelog et registre si l'état change.

## 8. Portes renforcées selon le risque

| Risque | Preuve supplémentaire |
|---|---|
| Sécurité/authentification | Tests négatifs, échec fermé, revue adversariale |
| Migration de données | Sauvegarde, fixture réelle anonymisée, test aller/retour |
| Science/métier | Source versionnée, domaine de validité, revue experte |
| Concurrence/idempotence | Tests de course ou invariant en base |
| Mobile/offline | Test interruption, reprise, ancien format et stockage chiffré |
| Déploiement | Artefact reproductible, health/readiness, rollback testé |
| Documentation canonique | Registre de vérité et références dépendantes à jour |

## 9. Rapport obligatoire de l'agent

Le rapport de fin contient :

- snapshot de départ ;
- résumé factuel ;
- fichiers modifiés ;
- commandes exécutées avec codes de sortie ;
- tests passés, échoués et ignorés ;
- hypothèses et éléments non vérifiés ;
- risques résiduels ;
- procédure de retour arrière ;
- recommandation, sans auto-approbation.

## 10. Gestion des incidents

Une modification hors périmètre, une preuve inventée, un secret exposé ou une
altération d'un document `Locked` est une non-conformité. Codex suspend la
tâche, préserve les preuves, évalue l'impact et applique le processus
d'incident du QMS. Aucun autre agent ne poursuit sur les mêmes fichiers avant
arbitrage.

## 11. Indicateurs

- 100 % des tâches IA avec identifiant et critères d'acceptation ;
- 100 % des rapports avec commandes et résultats vérifiables ;
- zéro chevauchement de fichiers non arbitré ;
- zéro fusion d'une production IA sans revue indépendante ;
- taux de réouverture inférieur à 10 % ;
- délai de correction d'une non-conformité critique inférieur à 24 heures.

## 12. Références

- `../../00_CONSTITUTION/PACT_FOR_AI_AGENTS.md`
- `../../02_RFC/RFC-0022-orchestration-agents-ia.md`
- `../../03_DECISIONS/DEC-000032.md`
- `../../GSIE/PROMPTS/README.md`
- `CODE_REVIEW.md`
- `CI_CD.md`
- `DOCUMENT_CONTROL.md`

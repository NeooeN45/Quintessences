# GSIE-PROMPT-0003 — Contre-audit de la refondation constitutionnelle

| Champ | Valeur |
|---|---|
| Statut | PRÊTE — contre-audit en lecture seule |
| Agent cible | Claude |
| Environnement | Claude Code ou Cowork via Devin |
| Dépôt | Quintessences |
| Branche | `fix/enterprise-reliability-2026-07-21` |
| Commit de départ | `3616b78` |
| Orchestrateur | Codex |
| Relecteur | Codex puis Fondateur |
| Priorité | P0 |

## Mission

Réaliser une contre-analyse constitutionnelle, scientifique, technique,
juridique et sécuritaire strictement en lecture seule de :

- `RFC-0023-alignement-identite-perimetre-propriete-intellectuelle.md` ;
- `RFC-0024-autonomie-graduee-selon-le-risque.md`.

Chercher activement les contradictions, ambiguïtés, autorisations
involontaires, exigences impossibles à tester, oublis documentaires et risques
de gouvernance. Le livrable est un rapport adversarial sourcé. Ne corriger
aucun fichier.

## Pourquoi maintenant

Les textes constitutionnels verrouillés définissent encore GSIE comme un
moteur forestier, open source et sans aucune décision automatique. La vision
validée par le Fondateur définit désormais Quintessences comme un écosystème
environnemental multi-domaines, permet des licences par composant et conserve
l'autonomie décisionnelle comme programme de recherche encadré.

Les deux RFC doivent être contre-auditées avant toute décision ou nouvelle
édition constitutionnelle.

## Précondition bloquante

Les deux RFC doivent être présentes dans le commit de départ ou dans un
artefact immuable dont le hash est fourni.

Si elles sont seulement locales, non suivies, différentes du snapshot annoncé
ou modifiées pendant l'audit, arrêter avec le statut `BLOQUÉE`.

## Documents obligatoires

1. `AGENTS.md`
2. `PROJECT_MEMORY.md`
3. `00_CONSTITUTION/README.md`
4. `00_CONSTITUTION/GSIE-CON-000.md`
5. `00_CONSTITUTION/GSIE-CON-001.md`
6. `00_CONSTITUTION/GSIE-CON-002.md`
7. `00_CONSTITUTION/GSIE-CON-004.md`
8. `00_CONSTITUTION/GSIE-CON-005.md`
9. `00_CONSTITUTION/GSIE-CON-006.md`
10. `00_CONSTITUTION/GSIE-CON-007.md`
11. `00_CONSTITUTION/GSIE-CON-008.md`
12. `00_CONSTITUTION/GSIE-FND-001.md`
13. `00_CONSTITUTION/GSIE-FND-002.md`
14. `00_CONSTITUTION/AI_CONSTITUTION.md`
15. `00_CONSTITUTION/SCIENTIFIC_CONSTITUTION.md`
16. `00_CONSTITUTION/TECHNICAL_CONSTITUTION.md`
17. `02_RFC/RFC-0022-orchestration-agents-ia.md`
18. `03_DECISIONS/DEC-000006.md`
19. `03_DECISIONS/DEC-000013.md`
20. `03_DECISIONS/DEC-000032.md`
21. `23_QUALITY_MANAGEMENT/SOURCE_OF_TRUTH_REGISTRY.json`
22. `23_QUALITY_MANAGEMENT/PROCESSES/DOCUMENT_CONTROL.md`
23. `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md`
24. `22_PROJECT_MEMORY/PROPOSITION_PLAN_REALISATION_2026-07-24.md`
25. les deux RFC à auditer.

## Périmètre autorisé

- lecture des documents listés ;
- inspection de leurs références directes ;
- commandes Git et contrôles documentaires non mutants ;
- production d'un rapport textuel hors dépôt ou dans la réponse de session.

## Non-objectifs

- réécrire les RFC ;
- modifier la Constitution ;
- créer une décision ;
- choisir les licences finales des composants ;
- autoriser un niveau d'autonomie ;
- auditer le code métier complet ;
- concevoir l'architecture détaillée des moteurs.

## Interdictions

- Aucun fichier modifié.
- Aucun commit, push, fusion, déploiement ou commentaire externe.
- Aucun document `Locked` modifié.
- Aucun secret ou donnée personnelle affiché.
- Aucune conclusion juridique présentée comme un avis d'avocat.
- Aucune approbation automatique des RFC.
- Aucun élargissement du périmètre sans arrêt et arbitrage.

## Angles de contre-audit obligatoires

1. respect de la hiérarchie Vision → Constitution → RFC → Décision ;
2. procédure correcte de nouvelle édition des documents `Locked` ;
3. cohérence des identités Quintessences, GSIE, Forge, GeoSylva, Hub et
   Ignis ;
4. risque de dispersion multi-domaines ou de couplage aux applications ;
5. distinction entre ouverture scientifique, code source, données, modèles,
   services et licences commerciales ;
6. compatibilité avec les droits des utilisateurs et des sources ;
7. exhaustivité de la taxonomie calcul, diagnostic, publication, décision et
   action ;
8. robustesse et testabilité des classes R0 à R5 ;
9. frontière entre automatisation technique et promotion de connaissance ;
10. sécurité des décisions R4 et systèmes physiques R5 ;
11. responsabilité humaine, délégation, reprise en main et arrêt d'urgence ;
12. traitement des modèles opaques sans exiger une chaîne de pensée privée ;
13. preuves nécessaires avant A3 et risques de validation trompeuse ;
14. cohérence du régime autorisé pendant les six premiers mois ;
15. documents canoniques ou contrôles automatiques oubliés ;
16. formulations pouvant être interprétées comme une autorisation immédiate.

## Questions auxquelles le rapport doit répondre

1. Les deux RFC sont-elles correctement séparées ?
2. Une Vision canonique racine est-elle la bonne solution documentaire ?
3. La RFC-0023 protège-t-elle suffisamment la science et les données malgré
   la liberté de licence ?
4. La RFC-0024 interdit-elle sans ambiguïté toute autonomie critique
   immédiate ?
5. Les classes R0 à R5 permettent-elles de classer les cas réels sans zone
   grise dangereuse ?
6. La notion de justification externe est-elle assez forte pour remplacer
   l'exigence de chaîne de raisonnement interne ?
7. Quels textes, processus, tests ou compétences humaines manquent avant une
   adoption ?
8. Quelles clauses doivent être corrigées avant de présenter les RFC au
   Fondateur pour adoption ?

## Méthode attendue

1. confirmer le dépôt, la branche, le commit et les hashes des deux RFC ;
2. lire intégralement les documents obligatoires ;
3. construire une matrice `proposition → source supérieure → verdict` ;
4. chercher les conflits réels, conflits conditionnels et fausses alertes ;
5. tenter de construire au moins cinq scénarios d'abus ou d'échec ;
6. vérifier que chaque exigence majeure peut recevoir une preuve ;
7. classer les constats P0, P1, P2, P3 ou observation ;
8. lister les zones examinées sans anomalie ;
9. remettre le rapport sans auto-approuver.

## Validations obligatoires

```text
git status --short --branch
git rev-parse HEAD
python tools/check_source_of_truth.py
rg -n "GeoSylva Intelligence Engine|moteur d'intelligence forestière|open.source|pilote automatique|ne décide jamais" 00_CONSTITUTION README.md PROJECT_MEMORY.md ROADMAP.md
```

Chaque commande doit être accompagnée de son code de sortie. Une commande
indisponible est signalée, jamais présentée comme réussie.

## Critères d'acceptation

- le snapshot audité est immuable et contient les deux RFC ;
- chaque constat cite un fichier et une section ;
- les conflits réels sont distingués des nuances compatibles ;
- les risques P0/P1 possèdent un scénario d'impact ;
- les lacunes de test et de gouvernance sont identifiées ;
- le rapport répond aux huit questions obligatoires ;
- aucune modification de fichier n'a eu lieu ;
- les limites de l'audit sont explicites.

## Format du rapport

### A. Verdict exécutif

- statut recommandé : `EN_REVUE`, `BLOQUÉE` ou `REJETÉE` ;
- nombre de constats par gravité ;
- conditions indispensables avant adoption.

### B. Constats

| ID | Gravité | RFC/section | Source supérieure | Preuve | Scénario d'impact | Correction recommandée |
|---|---|---|---|---|---|---|

### C. Matrice de conformité

| Proposition | Constitution/décision applicable | Compatible | Condition ou conflit |
|---|---|---|---|

### D. Scénarios adversariaux

Décrire au moins cinq scénarios concrets, dont :

- fermeture abusive d'un composant essentiel ;
- publication automatique d'un diagnostic erroné ;
- mauvaise classification R2/R3 ou R3/R4 ;
- système physique privé de journalisation ou d'arrêt ;
- modèle opaque donnant une justification plausible mais non prouvée.

### E. Rapport de preuve

- SHA et hashes examinés ;
- commandes et codes de sortie ;
- fichiers modifiés : doit être `aucun` ;
- hypothèses et éléments non vérifiés ;
- risques résiduels ;
- recommandation finale.

La recommandation de Claude n'est pas une acceptation. Codex reproduit les
preuves et le Fondateur conserve l'autorité de décision.

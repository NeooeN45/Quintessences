# GSIE-PROMPT-0013 — Contre-audit n°2, A10 — Red team sur les 793 lignes ajoutées

| Champ | Valeur |
|---|---|
| Statut | VALIDÉE — rapport remis et consolidé |
| Agent cible | GLM 5.2 |
| Environnement | Devin |
| Dépôt | Quintessences |
| Branche | `fix/enterprise-reliability-2026-07-21` |
| Commit de départ | `b4096b6` |
| Constats couverts | défauts nouveaux |
| Orchestrateur | Architecte |
| Relecteur | Architecte puis Fondateur |
| Verdict rendu | RÉSERVÉ |
| Rapport consolidé | `23_QUALITY_MANAGEMENT/AUDITS/2026-07-25_CONTRE_AUDIT_2_RFC_0023_0026.md` |

## Mission

Chercher les défauts **nouveaux** introduits par les corrections.

Seule mission ne vérifiant aucun constat existant. Périmètre : le texte ajouté
entre `3616b78` et `b4096b6`, obtenu par
`git diff 3616b78 b4096b6 -- 02_RFC/`.

Six catégories imposées, chacune devant produire un résultat ou un
« recherché, rien trouvé » justifié : contradiction interne ; autorisation
involontaire ; exigence intestable ; complexité ingérable au regard de
l'effectif réel ; vocabulaire employé avec plusieurs sens ou non défini ; effet
de bord rendant non conforme une pratique actuelle sans période de transition.

Trois scénarios d'abus complets sont exigés, différents de ceux de l'audit n°1.

## Précondition bloquante

`git rev-parse HEAD` doit retourner
`b4096b6c4f8da1e74bcb3cf21c2699792b0d447d`. Les empreintes des quatre RFC
doivent correspondre à celles inscrites au rapport consolidé. Toute divergence
impose l'arrêt avec le statut `BLOQUÉE`.

## Documents obligatoires

1. `AGENTS.md`
2. `23_QUALITY_MANAGEMENT/AUDITS/2026-07-24_CONTRE_AUDIT_RFC_0023_0024.md`
3. `03_DECISIONS/DEC-000033.md`
4. `02_RFC/RFC-0022-orchestration-agents-ia.md`
5. `02_RFC/RFC-0023-alignement-identite-perimetre-propriete-intellectuelle.md`
6. `02_RFC/RFC-0024-autonomie-graduee-selon-le-risque.md`
7. `02_RFC/RFC-0025-editions-fondatrices-identite-perimetre-propriete-intellectuelle.md`
8. `02_RFC/RFC-0026-editions-constitutionnelles-autonomie-graduee.md`

## Règles de preuve

Verdicts autorisés : `CLOS`, `PARTIEL`, `NON_CLOS`, `RÉGRESSION`,
`NON_APPLICABLE`.

Un verdict `CLOS` exige la citation du fichier, du numéro de ligne et du texte
exact qui ferme le constat. Sans citation vérifiable, le verdict maximal
autorisé est `PARTIEL`.

Une RFC qui affirme d'elle-même qu'un point est traité n'est jamais une preuve.
Les sections « critères d'acceptation », « risques et mesures » et « ce que
cette RFC ne fait pas » ne peuvent pas être citées comme preuve de clôture.

Chaque constat marqué `CLOS` ou `PARTIEL` doit faire l'objet d'une tentative de
réouverture documentée.

## Interdictions

- Aucun fichier modifié, créé ou supprimé.
- Aucun `git add`, `commit`, `push`, `merge`, `rebase`, `checkout`, `reset`,
  `stash`.
- Aucune PR, aucun commentaire externe, aucun déploiement.
- Aucun document `Locked` touché.
- Aucun secret, clé ou donnée personnelle affiché.
- Aucun élargissement du périmètre : dix agents travaillent en parallèle sur
  des périmètres disjoints.
- Aucun avis juridique.
- Aucune approbation : elle n'appartient qu'au Fondateur.

## Commandes de validation

```text
git rev-parse HEAD
git status --short --branch
python3 tools/check_source_of_truth.py
python3 tools/check_governance_consistency.py
python3 tools/check_ai_prompts.py
```

Chaque commande est rapportée avec son code de sortie. Une commande
indisponible est signalée, jamais présentée comme réussie.

## Format du rapport

1. Preuve d'exécution — snapshot, empreintes, commandes et codes de sortie,
   fichiers modifiés.
2. Verdicts — tableau constat / verdict / fichier:ligne / citation / tentative
   de réouverture / reste à faire.
3. Défauts nouveaux dans le périmètre.
4. Zones examinées sans anomalie.
5. Ce qui n'a pas pu être vérifié — section obligatoire, jamais vide.
6. Hors périmètre.
7. Verdict de mission — `FAVORABLE`, `RÉSERVÉ` ou `DÉFAVORABLE`.

La recommandation de l'agent n'est pas une acceptation.

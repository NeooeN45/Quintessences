---
name: pilotage-wip
description: Analyse le backlog, les prompts et la roadmap pour piloter la limite WIP 1+1+1 sans créer de registre parallèle
argument-hint: "[optionnel: produit ou domaine]"
triggers:
  - user
  - model
---

# Pilotage WIP Quintessences

Tu aides le Fondateur à choisir le prochain travail utile sans créer de nouveau
système de tâches. Tu produis une vue dérivée à partir des sources existantes et
ne modifies aucun registre par défaut.

## Sources lues

- `PROJECT_MEMORY.md` ;
- `ROADMAP.md` ;
- `22_PROJECT_MEMORY/IDEA_BACKLOG.md` ;
- `GSIE/PROMPTS/REGISTER.md` ;
- `CHANGELOG.md` ;
- `git status` et l'historique utile ;
- les RFC, décisions ou spécifications liées au sujet.

## Limite WIP de référence

```text
1 tranche produit active
1 expérimentation de recherche
1 correction urgente
```

Une tâche `PROPOSÉE`, `PRÊTE` ou `BLOQUÉE` n'est pas automatiquement active.
Une tâche `EN_COURS` doit avoir un périmètre, un agent et des validations
identifiables.

## Processus

1. Construire une vue des tâches actives par état, produit, agent et dépendance.
2. Détecter les incohérences : tâche sans prompt, prompt sans preuve, idée déjà
   implémentée, chantier sans propriétaire ou travaux qui se chevauchent.
3. Vérifier les dépendances et les blockers.
4. Classer les candidats selon : valeur utilisateur, risque réduit, dépendances,
   coût de validation et proximité d'un incrément démontrable.
5. Recommander une seule prochaine tranche principale.
6. Proposer une expérimentation séparée uniquement si elle ne met pas en danger
   la tranche produit.
7. Signaler les sujets à archiver, rejeter, scinder ou transformer en RFC.

## Format de sortie

```markdown
# Pilotage WIP — [date]

## État réel
- Produit actif :
- Recherche active :
- Correction urgente :
- Tâches bloquées :
- Dépôt sale ou travaux non attribués :

## Dépassements et incohérences
- ...

## Recommandation unique
- Sujet :
- Pourquoi maintenant :
- Hors périmètre :
- Critère de sortie :

## Options différées
- ...

## Action nécessitant le Fondateur
- ...
```

## Garde-fous

- Ne crée jamais un tableau WIP concurrent.
- Ne réordonne jamais la roadmap silencieusement.
- Ne transforme jamais une recommandation en tâche assignée sans accord.
- Ne lance jamais plusieurs agents sur les mêmes fichiers.
- Signale honnêtement les tests ou informations manquants.

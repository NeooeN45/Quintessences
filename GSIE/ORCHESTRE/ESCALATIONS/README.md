# Escalades — ORCHESTRE GSIE

> File d'escalade pour les décisions critiques qui nécessitent
> l'avis du Fondateur. L'orchestrateur met la loop en pause et
> notifie dans l'IDE jusqu'à réponse.

## Format d'escalade

Chaque escalade est un fichier `YYYY-MM-JJ_NNN_loop.md` :

```markdown
# ESCALADE #NNN — [Sujet court]

## Statut: EN ATTENTE DE RÉPONSE

## Question
[La question, claire et directe]

## Contexte
- [éléments de contexte pertinents]
- [impact estimé]
- [risque évalué]

## Options
A) [option 1 — description + impact]
B) [option 2 — description + impact]
C) [option 3 — description + impact]

## Recommandation
[option recommandée par l'agent + justification]

## Impact
- Temps estimé: [durée]
- Fichiers: [liste]
- Breaking: [oui/non]

## Réponse attendue
Réponds A, B, C ou ta propre option.
```

## Règles d'escalade

1. **Critique (sécurité, breaking change, RFC)** → escalade obligatoire
2. **Important (architecture, dépendance majeure)** → consensus d'abord, escalade si échec
3. **Mineur (ordre, priorité)** → l'orchestrateur décide seul
4. **Trivial (nom, format)** → la loop décide seule

## Cycle de vie d'une escalade

```
1. Loop détecte une décision critique
2. Loop écrit le fichier d'escalade dans ESCALATIONS/
3. Loop se met en PAUSE
4. Orchestrateur notifie le Fondateur dans l'IDE
5. Fondateur répond (A, B, C, ou option custom)
6. Orchestrateur transmet la réponse à la loop
7. Loop reprend avec la décision
8. Escalade marquée comme RÉSOLUE
```

## Escalades actuelles

Aucune escalade en attente.

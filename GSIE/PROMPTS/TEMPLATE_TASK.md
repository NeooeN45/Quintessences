# GSIE-PROMPT-XXXX — [Titre]

| Champ | Valeur |
|---|---|
| Statut | PROPOSÉE |
| Agent cible | [Claude / GLM 5.2] |
| Environnement | Devin |
| Dépôt | [chemin / URL] |
| Branche | [branche] |
| Commit de départ | [SHA obligatoire avant attribution] |
| Orchestrateur | Codex |
| Relecteur | [agent indépendant / humain] |
| Priorité | [P0 / P1 / P2 / P3] |

## Mission

[Un résultat principal, mesurable et vérifiable.]

## Pourquoi maintenant

[Lien avec roadmap, risque, incident, RFC ou décision.]

## Documents obligatoires

1. `AGENTS.md`
2. `PROJECT_MEMORY.md`
3. [README du composant]
4. [RFC, décision, spécification et processus applicables]

## Périmètre autorisé

- [fichiers ou répertoires exacts]

## Non-objectifs

- [ce que la tâche ne doit pas entreprendre]

## Interdictions

- Ne pas modifier un document `Locked`.
- Ne pas exposer de secret ou de donnée personnelle.
- Ne pas élargir le périmètre sans arrêt et arbitrage.
- Ne pas committer, pousser, fusionner ou déployer sans autorisation.
- Ne pas annoncer un test non exécuté.

## Conditions d'arrêt

Arrête la tâche et remets un rapport `BLOQUÉE` si :

- le dépôt, la branche ou le commit ne correspondent pas ;
- le working tree contient des changements inconnus ;
- une migration destructive ou une source scientifique absente est requise ;
- les fichiers autorisés ne suffisent pas ;
- une instruction contredit une source supérieure.

## Méthode attendue

1. Confirmer le snapshot.
2. Lire les documents obligatoires.
3. Établir l'état initial et les tests de référence.
4. Réaliser uniquement la mission.
5. Exécuter les validations.
6. Examiner le diff complet.
7. Remettre le rapport sans auto-approuver.

## Validations obligatoires

```text
[commandes exactes et résultats attendus]
```

## Critères d'acceptation

- [critères binaires ou mesurables]

## Rapport final obligatoire

1. Snapshot de départ.
2. Résumé factuel.
3. Fichiers modifiés.
4. Commandes et codes de sortie.
5. Tests réussis, échoués et ignorés.
6. Hypothèses et éléments non vérifiés.
7. Risques résiduels.
8. Retour arrière.
9. Recommandation : `EN_REVUE`, `BLOQUÉE` ou `REJETÉE`.

La recommandation de l'agent n'est pas une acceptation. Codex reproduit les
preuves et rend le verdict technique.

# Subagent Guard — protéger le quota payant Devin Hub

> **CRITIQUE.** Ce skill se déclenche à CHAQUE fois qu'une demande
> implique des sous-agents, subagents, parallélisation, ou délégation
> de tâches. Il protège le quota payant du Fondateur.

## Le problème

L'outil `run_subagent` route les sous-agents vers **Devin Hub**
(service cloud payant de Cognition). Chaque sous-agent lancé consomme
le **quota hebdomadaire payant** du Fondateur. Quand le quota est
épuisé, tous les sous-agents échouent immédiatement avec :

```
[Error] Your weekly usage quota has been exhausted.
Visit https://app.devin.ai/settings/usage to purchase on-demand
usage or turn on auto-reload.
```

**Conséquence** : perte immédiate de la capacité de parallélisation,
travail interrompu, tokens déjà consommés perdus sans résultat.

## La règle absolue

### NE JAMAIS lancer `run_subagent` sans confirmation explicite

Avant de lancer un sous-agent via `run_subagent`, l'agent DOIT :

1. **Demander confirmation au Fondateur** avec `ask_user_question` :
   - Expliquer que le sous-agent consommera du quota payant Devin Hub
   - Demander : « Lancer le sous-agent (payant) ou faire le travail
     manuellement avec les outils locaux (gratuit) ? »
2. **Si le Fondateur refuse ou ne répond pas** : faire le travail
   manuellement avec les outils disponibles (`exec`, `read`, `edit`,
   `grep`, `find_file_by_name`, `code_search`, `web_search`).

### Exception : aucun sous-agent sans quota

Si le quota est déjà épuisé (erreur reçue dans la session), ne JAMAIS
retenter `run_subagent` — faire tout le travail manuellement.

## Alternatives gratuites (à privilégier)

Le modèle **GLM 5.2 High** (modèle local actif) dispose de :

- **Contexte 1M de tokens** — largement suffisant pour la plupart
  des tâches sans sous-agent
- **Tous les outils** : `exec`, `read`, `edit`, `grep`, `grep`,
  `find_file_by_name`, `code_search`, `web_search`, `webfetch`
- **Exécution parallèle** : plusieurs `exec` ou `read` en parallèle
  dans un seul message (vraie parallélisation côté outils)

### Stratégies de remplacement

| Besoin | Au lieu de `run_subagent` | Faire |
|---|---|---|
| Explorer le code | subagent_explore | `code_search` + `grep` + `read` en parallèle |
| Modifier du code | subagent_general | `edit` directement après `read` |
| Lancer des tests | subagent qa | `exec` avec pytest, analyser sortie |
| Build frontend | subagent frontend | `exec` avec npm/astro build |
| Tâche longue | subagent background | `exec` avec `timeout: 0` (background) |
| Plusieurs tâches indépendantes | N subagents parallèles | N appels `exec`/`read` dans un seul message |

### Parallélisation sans sous-agents

Lancer plusieurs outils **dans le même message** (le moteur exécute
en parallèle) :

```
# Au lieu de 3 subagents, faire dans UN message :
- exec: commande 1 (background, timeout: 0)
- exec: commande 2 (background, timeout: 0)
- read: fichier A
- read: fichier B
- grep: pattern C
```

Puis récupérer les résultats avec `get_output` pour les shells
background.

## Quand les sous-agents SONT légitimes (avec confirmation)

- Tâche vraiment longue (>10 min) qui bloque la session entière
- Travail sur un repo externe indépendant (GeoSylva, QGISIA, Forge)
- Besoin d'un profil spécialisé (architecte, sig, unreal, android)
  pour une analyse approfondie que le contexte 1M ne peut pas absorber

**Dans tous ces cas** : demander d'abord avec `ask_user_question`.

## Méthode GLM 5.2 High (rappel)

Voir `methode-glm52-high` : tokens illimités, sous-agents en parallèle
massif **autorisés** — mais uniquement quand le quota Devin Hub est
disponible. En l'absence de quota, la méthode s'adapte : travail
manuel, outils en parallèle, contexte 1M.

## Triggers

Ce skill se déclenche sur :
- « sous-agent », « subagent », « agent en parallèle »
- « déléguer », « lance un agent », « utilise un subagent »
- `run_subagent`, `is_background`, `profile:`
- « parallélise », « en parallèle » (quand ça implique des agents)
- Toute mention de consortium-agents, handoff, délégation cloud

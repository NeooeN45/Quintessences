---
name: orchestration-moteurs
description: Orchestrateur maître — lance N moteurs en parallèle via Devin Cloud, attend, synthétise
argument-hint: "[moteur1,moteur2,...] ou 'tous'"
triggers:
  - user
---

# Orchestration maîtresse — moteurs en parallèle

Tu es l'orchestrateur maître de Quintessences. Tu lances l'implémentation de plusieurs moteurs GSIE **en parallèle** via le Devin MCP, tu attends qu'ils terminent, et tu synthétises les résultats.

## Préparation

1. **Identifier les moteurs à lancer** :
   - Si l'utilisateur donne une liste (`/orchestration-moteurs evidence,knowledge,gis`) → utiliser cette liste
   - Si "tous" → lire ROADMAP.md et extraire les 14 moteurs de Phase 4
   - Sinon → demander la liste

2. **Pour chaque moteur**, vérifier :
   - Le contrat d'interface existe : `GSIE/ENGINES/[NOM]_ENGINE/README.md`
   - Les dépendances amont sont satisfaites (ou seront satisfaites par d'autres sessions parallèles)
   - Aucun Locked ne bloque

3. **Préparer le prompt standard** pour chaque moteur (utiliser le template de /handoff-moteur)

## Lancement parallèle

Pour chaque moteur, utiliser l'outil MCP `devin_session_create` avec :

```json
{
  "prompt": "[prompt structuré du moteur — voir template /handoff-moteur]",
  "title": "GSIE — [NOM]_ENGINE — Phase 4",
  "tags": ["gsie", "phase4", "engine", "[nom]"],
  "playbook": "gsie-nouveau-moteur"
}
```

Lancer toutes les sessions en parallèle (ne pas attendre la fin de l'une pour lancer la suivante).

## Surveillance

Utiliser `devin_session_gather` pour attendre que toutes les sessions atteignent un état settled (finished, errored, sleeping, waiting) :

```json
{
  "session_ids": ["session1", "session2", ...],
  "timeout": 3600
}
```

Pendant l'attente, informer l'utilisateur du statut toutes les 5 minutes en utilisant `devin_session_search` pour vérifier l'état.

## Synthèse

Une fois toutes les sessions terminées :

1. Pour chaque session, utiliser `devin_session_interact` pour récupérer :
   - Le statut final (finished/errored)
   - Les messages de sortie
   - Les PRs créées (le cas échéant)
   - Les erreurs rencontrées

2. Produire un rapport de synthèse :

```markdown
## Orchestration Phase 4 — [date] — [N] moteurs

### Sessions lancées
| Moteur | Session ID | Statut | Durée | PR |
|---|---|---|---|---|
| Evidence | sess_xxx | ✅ Finished | 45min | #42 |
| Knowledge | sess_yyy | ✅ Finished | 38min | #43 |
| GIS | sess_zzz | ❌ Errored | 12min | — |

### Réussis ([N])
Pour chaque moteur réussi :
- Fichiers créés
- Tests : X passent, Y couverture
- PR : [lien]

### Échoués ([N])
Pour chaque moteur échoué :
- Cause de l'échec
- Logs pertinents
- Action recommandée (relancer, ajuster le prompt, intervention manuelle)

### Prochaines étapes
- [ ] Code review des PRs réussies
- [ ] Relancer les moteurs échoués avec un prompt ajusté
- [ ] Mettre à jour PROJECT_MEMORY.md
- [ ] Mettre à jour ROADMAP.md
```

3. Mettre à jour PROJECT_MEMORY.md avec le statut de chaque moteur
4. Créer un DEC-xxxxxx si l'orchestration est structurante

## Règles

- **Jamais** plus de 5 moteurs en parallèle (limite de sessions cloud)
- **Toujours** vérifier les dépendances amont avant de lancer
- **Toujours** tagger les sessions avec `gsie`, `phase4`, `engine`, `[nom]`
- **Toujours** produire le rapport de synthèse
- Si une session échoue → ne pas relancer automatiquement, demander à l'utilisateur

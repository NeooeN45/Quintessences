# Index des mémoires — ORCHESTRE GSIE

> Index de toutes les mémoires persistées. L'orchestrateur consulte
> cet index pour l'association spontanée (injection de mémoires
> pertinentes avant chaque cycle).

## Types de mémoire

| Type | Description | Dossier |
|---|---|---|
| `info` | Fait durable, convention, règle | `memories/info/` |
| `skill` | Procédure réutilisable, how-to | `memories/skill/` |
| `episode` | Ce qui s'est passé dans un cycle | `memories/episode/` |
| `error` | Erreur passée, pour éviter la répétition | `memories/error/` |
| `reflection` | Insight distillé d'épisodes | `memories/reflection/` |
| `todo` | Engagement en attente | `memories/todo/` |

## Mémoires enregistrées

### info

| ID | Date | Salience | Contenu (extrait) |
|---|---|---|---|
| info-001 | 2026-08-08 | 1.0 | GSIE Phase 4 — code métier autorisé |
| info-002 | 2026-08-08 | 0.9 | 14 moteurs GSIE, API FastAPI, Hub UE5.8 |
| info-003 | 2026-08-08 | 0.8 | Constitution prime — jamais modifier un Locked |

### skill

| ID | Date | Salience | Contenu (extrait) |
|---|---|---|---|
| skill-001 | 2026-08-08 | 0.9 | Comment lancer un benchmark Correlation Engine |

### episode

| ID | Date | Salience | Contenu (extrait) |
|---|---|---|---|
| — | — | — | Aucun épisode enregistré (système nouvellement créé) |

### error

| ID | Date | Salience | Contenu (extrait) |
|---|---|---|---|
| — | — | — | Aucune erreur enregistrée |

### reflection

| ID | Date | Salience | Contenu (extrait) |
|---|---|---|---|
| — | — | — | Aucune reflection enregistrée |

### todo

| ID | Date | Salience | Contenu (extrait) |
|---|---|---|---|
| todo-001 | 2026-08-08 | 0.9 | Lancer premier cycle loop Sécurité+Perf |

## Association spontanée

L'orchestrateur, avant chaque cycle :
1. Lit cet index
2. Sélectionne les mémoires par salience × récence
3. Injecte les mémoires pertinentes dans son contexte
4. Exécute le cycle avec la mémoire active

Règle : maximum 10 mémoires injectées par cycle (limite de contexte).
Priorité : error > reflection > info > skill > episode > todo.

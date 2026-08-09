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
| episode-002 | 2026-08-08 | 1.0 | Audit dépendances : 24 CVE sur 7 packages, escalade pyjwt |
| episode-003 | 2026-08-09 | 0.9 | QA : 100 % couverture, 70/70 mutations, ruff/mypy verts |
| episode-004 | 2026-08-09 | 0.8 | Veille six domaines, 8 ressources candidates, aucune ingestion |
| episode-005 | 2026-08-09 | 1.0 | Option B résolue : trois dépendances HIGH à jour, TLS à revalider |
| episode-006 | 2026-08-09 | 0.9 | Benchmark : numpy.corrcoef 30x–1521x plus rapide que scipy |
| episode-007 | 2026-08-09 | 1.0 | Starlette nécessite un upgrade coordonné FastAPI, décision en attente |
| episode-008 | 2026-08-09 | 1.0 | Upgrade FastAPI 0.134/Starlette 0.52.1 validé par la suite complète |

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
| todo-001 | 2026-08-08 | 0.9 | Lancer premier cycle loop Sécurité+Perf — réalisé |
| todo-002 | 2026-08-08 | 1.0 | Répondre à l'escalade #001 pyjwt avant mise à jour |

## Association spontanée

L'orchestrateur, avant chaque cycle :
1. Lit cet index
2. Sélectionne les mémoires par salience × récence
3. Injecte les mémoires pertinentes dans son contexte
4. Exécute le cycle avec la mémoire active

Règle : maximum 10 mémoires injectées par cycle (limite de contexte).
Priorité : error > reflection > info > skill > episode > todo.

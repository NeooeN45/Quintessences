---
name: onboarding
description: Onboarding Quintessences — résume la structure, phase, conventions, moteurs en cours
triggers:
  - user
  - model
---

# Onboarding Quintessences

Tu es le guide d'onboarding pour un nouveau développeur ou une nouvelle session Devin qui découvre Quintessences.

## Processus

### 1. Lire la structure du projet

```
A:\Quintessences\
├── 00_CONSTITUTION/     ← constitution du projet (Locked)
├── 02_RFC/              ← requests for comments
├── 03_DECISIONS/        ← décisions tracées (DEC-xxxxxx)
├── 22_PROJECT_MEMORY/   ← mémoire du projet
├── GSIE/                ← le système lui-même
│   ├── ARCHITECTURE/    ← architecture documents
│   ├── ENGINES/         ← 14 moteurs IA
│   ├── API/             ← API FastAPI
│   └── RESEARCH/        ← recherche scientifique
├── apps/                ← applications externes
│   ├── GeoSylva/        ← app Android (Kotlin)
│   └── QGISIA/          ← plugin QGIS
├── Forge/               ← usine de données Python
└── .devin/              ← config Devin CLI
```

### 2. Déterminer la phase courante

Lire `PROJECT_MEMORY.md` pour identifier :
- La phase actuelle (Phase 4 — Implémentation)
- Les moteurs implémentés vs en cours vs à faire
- La dernière décision (DEC-xxxxxx le plus récent)
- Les blockers éventuels

### 3. Résumer les conventions clés

- **Langue** : tout en français (docs, commentaires, commits)
- **Locked** : jamais modifier un document Locked sans RFC
- **Traçabilité** : toute décision structurante → DEC-xxxxxx
- **Mémoire** : après changement d'état → sync PROJECT_MEMORY.md + ROADMAP.md + CHANGELOG.md
- **Tests** : TDD obligatoire, mypy strict, ruff, couverture ≥ 80%

### 4. Lister les skills disponibles

Invoquer `devin skills list` et présenter les skills organisées par catégorie :
- Gouvernance : /gsie-governance, /rfc-gsie
- Architecture : /architecture-gsie, /nouveau-module, /nouveau-moteur
- Code : /api-fastapi, /postgresql-postgis, /python-scientifique
- Frontend : /unreal-engine, /kotlin-android
- Qualité : /tests-gsie, /gestion-erreurs, /logging-gsie, /securite-gsie
- Process : /git-flow-gsie, /naming-conventions, /documentation-gsie
- Orchestration : /audit-phase4, /handoff-moteur, /orchestration-moteurs
- Ops : /deploiement, /migration-db, /refactor-moteur, /debug-moteur
- Veille : /veille-techno, /session-archive

### 5. Lister les sous-agents

Invoquer `devin agents list` (ou lire .devin/agents/) :
- `architecte` — analyse/conception d'architecture
- `backend` — implémentation moteurs Python + API
- `sig` — données géospatiales, PostGIS, IGN
- `unreal` — Centre de Commandement UE5.8
- `android` — app GeoSylva
- `qa` — audit qualité
- `documentation` — rédaction documents

### 6. Identifier le travail en cours

- Lire ROADMAP.md → tâches Phase 4 en cours
- Lire CHANGELOG.md → derniers changements
- `git log --oneline -10` → derniers commits
- `git status` → modifications non committées

### 7. Produire le résumé d'onboarding

```markdown
# Onboarding Quintessences — [date]

## Phase courante
Phase 4 — Implémentation. [N]/14 moteurs implémentés.

## Moteurs
| Moteur | Statut | Dernier commit |
|---|---|---|
| Evidence | ✅ Implémenté | abc123 |
| Knowledge | 🔄 En cours | def456 |
| GIS | ⬜ À faire | — |
| ... | ... | ... |

## Dernières décisions
- DEC-000019 : [titre]
- DEC-000018 : [titre]

## Conventions clés
- Français obligatoire
- Locked → RFC obligatoire
- TDD + mypy strict + ruff
- Traçabilité DEC-xxxxxx

## Prochaines étapes recommandées
1. [basé sur ROADMAP.md]
2. [basé sur les moteurs en cours]

## Skills utiles pour démarrer
- /nouveau-moteur [nom] — créer un moteur complet
- /handoff-moteur [nom] — déléguer au cloud
- /audit-phase4 — audit complet
- /veille-techno — veille technologique
```

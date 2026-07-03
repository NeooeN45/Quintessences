# Configuration Claude Code — GSIE

Configuration versionnée pour piloter GSIE avec Claude Code, alignée sur la
gouvernance du projet (voir `../CLAUDE.md`).

## Contenu

| Élément | Rôle |
|---|---|
| `settings.json` | Permissions, garde-fous, hooks (versionné, partagé) |
| `settings.local.json` | Réglages locaux personnels (ignoré par git) |
| `hooks/guard-locked.mjs` | Bloque toute écriture sur un document `Locked` |
| `commands/` | Commandes métier GSIE (slash commands) |
| `agents/` | Sous-agents spécialisés |
| `skills/gsie-governance/` | Skill projet auto-déclenchée (gouvernance) |
| `skills/skill-management/` | Gestion des skills (installer/évaluer/tracer/retirer) |
| `skills/mermaid/` | Skill communautaire vendorisée (diagrammes, MIT, épinglée) |
| `SKILLS_GSIE.md` | Sélection curatée des meilleures skills par phase |

## Commandes disponibles

| Commande | Effet |
|---|---|
| `/rfc <titre>` | Crée un RFC tracé dans `02_RFC/` |
| `/decision <résumé>` | Trace une décision dans `03_DECISIONS/` |
| `/article <n° ou titre>` | Rédige/complète un article constitutionnel |
| `/engine-doc <MOTEUR>` | Documente un moteur (`09_ENGINES/`, sans code) |
| `/sync-memory` | Synchronise PROJECT_MEMORY / ROADMAP / CHANGELOG |
| `/constitution-audit [cible]` | Audite conformité et traçabilité |

## Sous-agents

| Agent | Rôle |
|---|---|
| `constitution-guardian` | Audit de conformité (lecture seule) |
| `doc-redactor` | Rédaction scientifique française sobre et sourcée |
| `memory-keeper` | Synchronisation de la mémoire du projet |

## Garde-fou `Locked`

Le hook `hooks/guard-locked.mjs` s'exécute avant chaque `Edit`/`Write` et
**refuse** la modification si la cible est un document verrouillé :
- fondateurs connus : `GSIE-FND-001`, `GSIE-FND-002`, `GSIE-CON-000` ;
- ou tout fichier dont l'en-tête (15 premières lignes) déclare `statut … Locked`.

Un `Locked` ne se modifie que par un **RFC** (`/rfc`). Le hook requiert Node.js.

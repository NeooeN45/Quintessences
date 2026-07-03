# Skills recommandées pour GSIE

Sélection curatée des meilleures skills (parmi celles disponibles) pour ce
projet, classées par utilité et par phase. La skill **projet** `gsie-governance`
(dans `.claude/skills/`) se déclenche automatiquement et impose la gouvernance —
elle est prioritaire sur toutes les autres.

## Priorité maximale — utiles dès maintenant (Phase 1 : Foundation)

| Skill | Pourquoi pour GSIE |
|---|---|
| `gsie-governance` *(projet)* | Applique la gouvernance à toute production documentaire. **Auto-déclenchée.** |
| `superpowers:brainstorming` | Concrétise « l'architecture avant les fonctionnalités » : conçois avant de rédiger. À lancer avant tout nouveau document structurant. |
| `superpowers:writing-plans` + `executing-plans` | Structure la production des 12 livrables dans l'ordre, sans en sauter. |
| `deep-research` | Sourcing scientifique fact-checké et cité pour `06_RESEARCH/`, `07_KNOWLEDGE/`, Evidence Engine. Cœur de « la science avant l'opinion ». |
| `context7-doc` | Docs à jour et exactes des standards/formats (ontologies, SIG, schémas) sans halluciner. |
| `claude-md-management:revise-claude-md` | Maintient `CLAUDE.md` à jour quand la gouvernance évolue. |
| `claude-mem:learn-codebase` | Charge tout le dépôt en mémoire en une passe (~5 min) → contexte auto-injecté ensuite. |
| `superpowers:writing-skills` / `skill-creator` | Pour créer d'autres skills GSIE sur-mesure au besoin. |

## Phase 2 — Architecture

| Skill | Usage |
|---|---|
| `feature-dev:feature-dev` (agent `code-architect`) | Concevoir l'architecture détaillée des 14 moteurs et leurs contrats d'interface. |
| `superpowers:writing-plans` | Séquencer l'ordre de développement des moteurs. |

## Phase 3 — Connaissance

| Skill | Usage |
|---|---|
| `deep-research` | Constituer la base de connaissances sourcée, les ontologies, les niveaux de preuve. |
| `superpowers:verification-before-completion` | Vérifier chaque affirmation avant validation (traçabilité). |

## Phase 4 — Implémentation (le code viendra en son temps)

| Domaine | Skills |
|---|---|
| Développement moteurs | `feature-dev:feature-dev`, `superpowers:test-driven-development`, `superpowers:systematic-debugging` |
| Qualité / revue | `code-review`, `security-review`, `superpowers:requesting-code-review` + `receiving-code-review` |
| Intégration LLM/IA | `claude-api`, `model-economy` |
| Interfaces (Mobile/Desktop/Web) | `frontend-design`, `ui-ux-pro-max`, `web-design-guidelines`, `react-best-practices`, `composition-patterns` |
| Accessibilité | `accesslint:audit` |
| Backend/données (si retenu) | `supabase`, `supabase-postgres-best-practices` |

## Skills communautaires (externes — à réviser avant adoption)

⚠️ Une skill communautaire = instructions/scripts tiers. Conformément à la
gouvernance GSIE : **lire le `SKILL.md` avant de faire confiance**, épingler la
version (submodule git pour la traçabilité), préférer les licences claires (MIT).
Le hook `guard-locked` et la skill `gsie-governance` continuent de protéger les
documents `Locked`.

| Skill | Utilité pour GSIE | Source | Licence |
|---|---|---|---|
| **mermaid** ✅ *installée* | 23 types de diagrammes. Idéal pour `04_ARCHITECTURE/` (data-flow, C4), `09_ENGINES/`. Les diagrammes compressent le contexte ~3-6×. Vendorisée, épinglée `8ab1815` (voir `.claude/skills/mermaid/PROVENANCE.md`). | `github.com/WH-2099/mermaid-skill` | MIT |
| **docs-with-mermaid** | Génère une doc technique structurée avec diagrammes Mermaid. | `github.com/pranavred/...docs-with-mermaid` | à vérifier |
| **walkthrough** ⏸ *non installée* | Explications HTML interactives (Mermaid cliquable) — utile pour présenter les 14 moteurs. **Bloquée : pas de licence claire dans le dépôt.** À réévaluer si une licence est publiée. | `github.com/alexanderop/walkthrough` | à clarifier |
| **tapestry** | Interlie et résume des documents en réseaux de connaissances — aligné avec `07_KNOWLEDGE/` et le Knowledge Graph. | via marketplaces (ci-dessous) | à vérifier |
| **get-shit-done (gsd)** | Développement piloté par spécifications + context engineering — utile pour séquencer les livrables. | `github.com/gsd-build/get-shit-done` | à vérifier |
| **obra/superpowers** | Bibliothèque de skills de processus (déjà présente dans cette session). | `github.com/obra/superpowers` | — |
| **skill-creator** | Création guidée de skills GSIE sur-mesure (déjà disponible). | `github.com/anthropics/skills` | — |

### Nouveaux candidats évalués (recherche 2026-07-03)

Licences vérifiées ; verdict selon la gouvernance GSIE.

| Skill | Utilité GSIE | Source | Licence | Verdict |
|---|---|---|---|---|
| **markdown-linter-fixer** | Corrige automatiquement le lint markdown (MD029, etc.) sur les centaines de `.md` du dépôt. Sert « la documentation est le produit ». | `github.com/s2005/markdown-linter-fixer-skill` | MIT | ✅ **Recommandée** (dépend de Node + `markdownlint-cli2`) |
| **graphify** | Transforme docs/PDF/schémas en **knowledge graph** interrogeable (HTML + markdown + JSON). Aligné `07_KNOWLEDGE/` + Knowledge Graph. Code traité en local ; docs via LLM au choix. | `github.com/safishamsi/graphify` | MIT | ✅ Recommandée Phase 3 (installation via `uv tool install`, pas une simple vendorisation) |
| **obra/knowledge-graph** | Interroge un vault Markdown comme graphe (recherche sémantique, chemins) — 100 % local. Plugin Claude Code (auteur de superpowers). | `github.com/obra/knowledge-graph` | à vérifier | ⏳ À évaluer (licence) |
| **claude-obsidian** | « Second cerveau » PKM : 15 skills, liaison auto de sources en graphe Markdown (7,2k★). | `github.com/AgriciDaniel/claude-obsidian` | à vérifier | ⏳ À évaluer (licence + périmètre large) |
| **academic-research-skills** | Pipeline recherche→rédaction→revue par les pairs (13/12/7 agents). Puissant pour `06_RESEARCH/`. | `github.com/imbad0202/academic-research-skills` | CC-BY-NC 4.0 | ⚠ **Bloquée** : licence **non commerciale** (incompatible avec licence GSIE non encore fixée) + API payante. Rouvrir après le RFC licence. |

> Catalogues additionnels repérés : `alirezarezvani/claude-skills` (337 skills),
> `mingrath/awesome-claude-skills`, `glebis/claude-skills`, `daymade/claude-code-skills`.

### Installation d'une skill projet (exemple mermaid, épinglé)

```bash
git submodule add https://github.com/WH-2099/mermaid-skill.git .claude/skills/mermaid-skill
# puis pointer .claude/skills/mermaid vers mermaid-skill/.claude/skills/mermaid
```

### Où chercher d'autres skills communautaires

- `claudemarketplaces.com` — annuaire communautaire (skills, MCP, marketplaces).
- `claudeskills.info` — grand catalogue de skills open-source.
- `github.com/ComposioHQ/awesome-claude-skills` — 1000+ skills curées.
- `github.com/VoltAgent/awesome-agent-skills` — 1000+ skills multi-agents.
- `github.com/travisvn/awesome-claude-skills` — liste curée.

## Règle d'usage

Quand plusieurs skills s'appliquent : les **skills de processus** d'abord
(`gsie-governance`, `brainstorming`, `systematic-debugging`) fixent l'approche,
puis les skills d'implémentation exécutent. En Phase 1, aucune skill ne doit
conduire à écrire du code métier.

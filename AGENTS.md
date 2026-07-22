# Règles Devin CLI — Quintessences / GSIE

> Règles always-on concises. Les détails techniques sont dans les skills.
> En cas de conflit, `00_CONSTITUTION/` prime toujours.

---

## Phase et périmètre courant

**Phase 4 — Implémentation** (lancée par DEC-000017). Le code métier est désormais autorisé.
Priorités : 14 moteurs GSIE, API GSIE (FastAPI), Centre de Commandement UE5.8, GeoSylva, Ignis.

---

## Règles non négociables

1. **Tout en français** — documentation, commentaires, messages utilisateur, commits.
2. **Jamais modifier un Locked** — uniquement via RFC dans `02_RFC/`.
3. **Lire avant d'agir** — `README.md` du dossier cible + contrat d'interface du moteur concerné.
4. **Traçabilité** — toute décision structurante → `DEC-xxxxxx` dans `03_DECISIONS/`.
5. **Mémoire à jour** — après tout changement d'état → synchroniser `PROJECT_MEMORY.md`, `ROADMAP.md`, `CHANGELOG.md`.

## Orchestration des agents IA

- Le Fondateur conserve l'autorité finale ; Codex orchestre le travail
  technique et contrôle les preuves avant acceptation.
- Toute mission Claude ou GLM 5.2 via Devin utilise un prompt versionné
  `GSIE-PROMPT-xxxx` enregistré dans `GSIE/PROMPTS/REGISTER.md`.
- Une production d'agent n'est jamais acceptée sur son seul résumé : le diff
  et les validations sont reproduits selon
  `23_QUALITY_MANAGEMENT/PROCESSES/AI_AGENT_ORCHESTRATION.md`.
- Deux agents ne modifient pas simultanément les mêmes fichiers.
- Aucun agent ne pousse, fusionne ou déploie sans autorisation explicite.

---

## Skills à invoquer selon le contexte

| Contexte | Skill |
|---|---|
| Gouvernance, RFC, statut de document | `/gsie-governance` |
| Architecture d'un moteur ou composant | `/architecture-gsie` |
| Créer un nouveau module | `/nouveau-module` |
| API FastAPI | `/api-fastapi` |
| PostgreSQL / PostGIS | `/postgresql-postgis` |
| Unreal Engine 5.8 | `/unreal-engine` |
| Kotlin / GeoSylva Android | `/kotlin-android` |
| Python scientifique | `/python-scientifique` |
| Stratégie de tests | `/tests-gsie` |
| Rédiger un document | `/documentation-gsie` |
| Git / commits | `/git-flow-gsie` |
| Nommage / identifiants | `/naming-conventions` |
| Gestion des erreurs | `/gestion-erreurs` |
| Logging / observabilité | `/logging-gsie` |
| Sécurité API | `/securite-gsie` |
| Créer un moteur complet (orchestrateur) | `/nouveau-moteur` |
| Audit Phase 4 complet (orchestrateur) | `/audit-phase4` |
| Déléguer un moteur au Devin Cloud | `/handoff-moteur` |
| Veille technologique | `/veille-techno` |
| Déploiement (Docker, CI/CD) | `/deploiement` |
| Refactoring sécurisé d'un moteur | `/refactor-moteur` |
| Créer / gérer une RFC | `/rfc-gsie` |

---

## Sous-agents disponibles

| Profil | Quand l'utiliser |
|---|---|
| `architecte` | Analyse ou conception d'architecture GSIE |
| `backend` | Implémentation moteurs Python + API FastAPI |
| `sig` | Données géospatiales, PostGIS, IGN, LiDAR |
| `unreal` | Centre de Commandement UE5.8 + Cesium |
| `android` | Application GeoSylva (Kotlin/Compose) |
| `qa` | Audit qualité, couverture tests, conformité |
| `documentation` | Rédaction de documents GSIE |

---

## Repos externes (ne pas committer dans le repo parent)

| Dossier | Repo | Notes |
|---|---|---|
| `apps/GeoSylva/` | GitHub: NeooeN45/GeoSylva | `cd apps/GeoSylva/` pour travailler |
| `apps/QGISIA/` | GitHub: NeooeN45/QGISIAPRO | `cd apps/QGISIA/` |
| `Forge/` | GitHub: NeooeN45/Forge | Usine de données Python/uv |

---

## MCP configurés

| Serveur | Usage |
|---|---|
| `geocontext` | IGN GeoContext — données géospatiales françaises |
| `github` | Gestion repos GeoSylva + QGISIAPRO |
| `postgres` | Requêtes directes PostGIS (configurer `DATABASE_URL` dans config.local.json) |
| `devin` | Devin Cloud — créer/orchestrer sessions, playbooks, knowledge, schedules |

---

## Commandes globales (tous projets)

| Commande | Usage |
|---|---|
| `/code-review` | Review de code senior (6 dimensions) |
| `/git-best-practices` | Conventions git, commits, PRs |
| `/security-audit` | Audit OWASP Top 10 complet |
| `/performance-profiling` | Analyse performance et profiling |

---

## Modèle

Adaptive par défaut (routeur automatique Cognition). Switch vers `opus` pour architecture complexe, `swe` pour edits simples.
`/model adaptive` en session ou `--model adaptive` au lancement.

---

## Handoff cloud

`/handoff [tâche]` — délègue au Devin Cloud (VM avec shell, browser, repo complet).
Idéal pour : tâches longues, builds Docker, tests E2E, migrations DB, parallélisation des 14 moteurs.
Voir aussi `/handoff-moteur [nom]` pour un handoff optimisé pour un moteur GSIE.

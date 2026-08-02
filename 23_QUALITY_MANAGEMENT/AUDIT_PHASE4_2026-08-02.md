# Rapport Audit Phase 4 — 2026-08-02

> Audit complet (qualité + sécurité + fiabilité + gouvernance + documentation)
> conduit par le "sous-chef" (Devin CLI, GLM 5.2 High, sous-agents locaux).
> Périmètre : `GSIE/` (moteurs + API FastAPI) + docs racines.
> Exclus : repos externes `apps/GeoSylva/`, `apps/QGISIA/`, `Forge/`.
> Rapport sécurité détaillé : `GSIE/API/SECURITY_AUDIT_2026-08-02.md` (377 lignes).

---

## Score global

| Dimension | Score | Statut |
|---|---|---|
| Qualité code | **94 / 100** | ✅ |
| Sécurité | **87 / 100** | ✅ |
| Fiabilité (tests + résilience) | **92 / 100** | ✅ |
| Gouvernance | **82 / 100** | ⚠️ |
| Documentation | **78 / 100** | ⚠️ |

**Verdict global : 87 / 100 — État sain, aucun P0 bloquant.**

Le projet est prêt à poursuivre la Phase 4. Les 8 P1 ci-dessous doivent
être traités avant exposition production (certains sont déjà connus et
tracés). Aucune régression n'a été introduite par la session
2026-08-02 de correction P1/P2 précédente.

---

## Synthèse exécutive

- **0 P0** (bloquant) — aucune vulnérabilité critique, aucune violation
  constitutionnelle, aucun test en échec.
- **8 P1** (élevé) — 3 sécurité + 2 gouvernance + 3 documentation.
- **13 P2** (moyen) — durcissement et cohérence.
- **Points forts** : mypy 0 erreur / 153 fichiers, ruff clean, 1452
  tests passés (0 échec), couverture 94%, JWT RS256 + RBAC granulaire,
  SQL 100% paramétré, 14/14 moteurs documentés, hiérarchie
  documentaire respectée, 3 documents Locked intacts.

---

## Audit 1 — Qualité code (94 / 100 ✅)

### Commandes exécutées (depuis `GSIE/API/`)

| Outil | Commande | Résultat |
|---|---|---|
| ruff | `uv run ruff check .` | **All checks passed** |
| mypy | `uv run mypy src/gsie_api` | **Success: no issues found in 153 source files** |
| pytest | `uv run pytest -q --tb=line -x --ignore=tests/integration` | **1452 passed, 62 skipped, 0 failed** (112.84s) |
| couverture | (pytest-cov intégré) | **94% global** (525 lignes non couvertes / 8503) |

### Couverture par zone (extrait)

| Module | Couverture | Commentaire |
|---|---|---|
| `infrastructure/models/*` | 100% | Excellent |
| `websocket/manager.py` | 100% | Excellent |
| `outbox_worker.py` | 99% | Excellent |
| `shared/http_client.py` | 99% | Résilience couverte |
| `resources/router.py` | 92% | Bon |
| `resources/service.py` | 89% | Bon |
| `metrics/db_quality.py` | 46% | ⚠️ branche de collecte peu couverte |
| `ingestion/bulk.py` | 38% | ⚠️ ingestion bulk à couvrir |
| `resources/coercion.py` | 28% | ⚠️ conversion géospatiale à couvrir |

### Conformité conventions (AGENTS.md)

- Fonctions ≤30 lignes, complexité ≤5 : respecté sur l'échantillon
  (`router.py`, `service.py`, `http_client.py`).
- Pas de `any` non typé, pas de `!!` (Python N/A), pas de code
  commenté observé.
- Nommage `should_[expected]_when_[condition]` : conforme
  (vérifié sur `tests/unit/test_db_quality_metrics.py` récemment refactoré).

### P1 qualité

Aucun — la qualité code est solide.

### P2 qualité

1. `metrics/db_quality.py` (46%) — la branche de collecte réelle
   (connexion DB, agrégats) n'est pas couverte par les tests unitaires
   (mockés). Ajouter un test d'intégration `requires_docker`.
2. `ingestion/bulk.py` (38%) — ingestion bulk peu couverte. Risque
   élevé car chemin critique d'ingestion.
3. `resources/coercion.py` (28%) — conversion EWKT/GeoJSON peu couverte
   alors que c'est une frontière utilisateur sensible (sécurité P2-3).

---

## Audit 2 — Sécurité (87 / 100 ✅)

> Rapport détaillé : `GSIE/API/SECURITY_AUDIT_2026-08-02.md` (377 lignes,
> produit par sous-agent `subagent_general`).

### OWASP Top 10

| ID | Catégorie | Statut |
|---|---|---|
| A01 | Broken Access Control | ✅ RBAC granulaire |
| A02 | Cryptographic Failures | ✅ RS256, refresh rotation atomique Redis |
| A03 | Injection | ✅ SQL 100% paramétré (SQLAlchemy `text()` + `:param`) |
| A04 | Insecure Design | ⚠️ `dict[str, Any]` sur CRUD générique |
| A05 | Security Misconfiguration | ✅ `validate_production_security` refuse 10 configs dangereuses |
| A06 | Vulnerable Components | ✅ PyJWT 2.10.1 (pas python-jose), images pinées par digest |
| A07 | Auth Failures | ✅ JWT `sub`/`exp`/`iss`/`aud`/`jti`/`type` requis |
| A08 | Data Integrity | ✅ RLS PostgreSQL + isolation RGPD par schéma |
| A09 | Logging Failures | ✅ Pas de secret dans logs (vérifié) |
| A10 | SSRF | ✅ Clients API externes via `ResilientHttpClient` |

### Points forts confirmés

- **PyJWT 2.10.1** (pas python-jose — CVE-2024-33664 évitée), **RS256**
  asymétrique, expiry 15min access / 7j refresh.
- Validation JWT complète avec `options={"require": [...]}`.
- **RBAC granulaire** avec sortie fermée (`_ACTIONS_EVALUEES`),
  `rgpd_manager` restreint aux types RGPD.
- **SQL 100% paramétré** : aucune concaténation f-string, `text()` avec
  `:param` partout.
- **Rate limiting distribué** (slowapi + Redis), `key_style="endpoint"`
  anti-contournement.
- **7 headers de sécurité** + suppression header Server.
- Docker : non-root (uid 1000), `cap_drop: ALL`, `no-new-privileges`,
  `read_only`, images pinées par digest.
- RLS PostgreSQL + isolation RGPD par schéma dédié.
- Rotation refresh tokens atomique en Redis (script Lua `eval`).
- Validation WKT via `shapely.wkt.loads` sur toutes les géométries
  entrantes.
- `git ls-files` confirme `.env` non tracké, `.env.example` sans vraies
  valeurs.

### P1 sécurité (3)

1. **Clé API Météo-France réelle en `.env` local** (`.env:18`) — JWT avec
   `tier: Unlimited`, `owner: NeooeN`, `exp: 2030`. Non commité (gitignore
   OK) mais en clair sur disque. **Action** : rotation + stockage
   vault/secret manager.
2. **2 query params `id_departement: str` sans validation Pydantic**
   (`climate/router.py:133,224`) — pas de `Query(min_length, max_length,
   pattern)`. Risque injection/fingerprinting. **Action** : ajouter
   contraintes `Query(min_length=2, max_length=3, pattern="^[0-9A-Z]+$")`.
3. **HEALTHCHECK absent du Dockerfile** (`Dockerfile:90-100`) — présent
   uniquement dans docker-compose.yml. **Action** : ajouter
   `HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1`.

### P2 sécurité (5)

1. `dict[str, Any]` sur CRUD générique (`resources/schemas.py:31,37`) et
   retour `list[dict[str, Any]]` (`climate/router.py:120).
2. 28 endpoints `/status`+`/version` sans auth (fingerprinting en prod).
3. Validation SRID absente sur entrée EWKT utilisateur
   (`coercion.py:85-104`) — accepte n'importe quel SRID.
4. Token WebSocket en query param (standard, mitigations en place mais
   risque logs proxy).
5. Rate limiter WebSocket in-memory non distribué
   (`websocket/router.py:65`).

---

## Audit 3 — Fiabilité (92 / 100 ✅)

> Dérivé des audits qualité + sécurité + conventions `AGENTS.md` API.

### Tests

- **1452 tests passés, 0 échec, 62 skip** (skip = `requires_docker`
  sans Docker daemon).
- Harnais de mutation : 14/14 attendu (non rejoué cette session, état
  précédent conforme).
- Pattern `db_session` sans `@pytest.mark.asyncio` (pytest-asyncio
  mode `auto`) — conforme à `AGENTS.md` API.

### Résilience clients API externes

- 10 clients dans `engines/` : botanical (GBIF, Taxref), climate (AROME,
  DPClim, MétéoFrance, SYNOP, Vigilance, PaquetObs), gis (IGN), pedology
  (SoilGrids).
- Tous héritent de `ResilientHttpClient` (5 modes de panne capturés).
- Enregistrés dans `CLIENT_REGISTRY` (`test_resilience_factory.py`).
- Cache SynopClient TTL 1h (correction P1b session précédente).

### P1 fiabilité

Aucun — la fiabilité est solide.

### P2 fiabilité

1. 62 tests skip (Docker non disponible) — rejouer en CI avec Docker.
2. `ingestion/bulk.py` (38% couverture) — chemin critique peu testé.
3. `resources/coercion.py` (28%) — frontière géospatiale peu testée.

---

## Audit 4 — Gouvernance (82 / 100 ⚠️)

> Produit par sous-agent `subagent_general` (rapport complet dans la
> notification de complétion).

### Tableau par contrôle

| # | Contrôle | Statut |
|---|---|---|
| 1 | Documents Locked non modifiés hors RFC | ✅ |
| 2 | PROJECT_MEMORY.md à jour | ✅ (écart 19 min) |
| 3 | ROADMAP.md cohérent | ⚠️ chemins Ignis 208-210 incorrects |
| 4 | Décisions tracées | ⚠️ 3 DEC non référencées + DEC-000040 |
| 5 | CHANGELOG.md à jour | ✅ (écart 19 min) |
| 6 | RFCs | ✅ 30 RFC, statuts cohérents |
| 7 | Hiérarchie documentaire | ✅ |
| 8 | Identifiants tracés | ⚠️ trous GSIE-PROMPT 0018-0022, GSIE-DIR-0002 |
| 9 | Statuts de documents | ⚠️ DIR-0005/0006 en Draft alors qu'actives |
| 10 | Repos externes dans .gitignore | ✅ |

### P1 gouvernance (2)

1. **DEC-000024, DEC-000028, DEC-000034 non tracées** dans
   `PROJECT_MEMORY.md` ni `CHANGELOG.md` — violation règle
   « Aucune décision perdue » (CLAUDE.md §2.7). DEC-000040 référencée
   dans CHANGELOG mais absente de PROJECT_MEMORY.
2. **GSIE-DIR-0005 et GSIE-DIR-0006 en statut `Draft`** alors qu'elles
   pilotent des livrables Phase 2 actifs (208-210). Incohérent avec
   leur rôle opérationnel de directive fondatrice.

### P2 gouvernance (5)

1. Trou GSIE-PROMPT 0018-0022 (non documenté dans `REGISTER.md`).
2. GSIE-DIR-0002 absent (non documenté comme réservé).
3. Chemins ROADMAP.md incorrects pour livrables Ignis 208-210
   (préfixe `GSIE_` absent des fichiers réels).
4. Skill `/gsie-governance` référencé dans AGENTS.md/CLAUDE.md mais
   absent du disque (`.devin/skills/gsie-governance/` n'existe pas).
5. GSIE-CON-000 : statut ambigu (« LOCKED sous réserve de validation »).

---

## Audit 5 — Documentation (78 / 100 ⚠️)

> Produit en direct (sous-agent `documentation` échoué sur quota).

### README moteurs (14/14 présents)

| Moteur | README | Lignes | Contrat interface | Statut |
|---|---|---|---|---|
| EVIDENCE_ENGINE | ✅ | 42 | Partiel | OK |
| KNOWLEDGE_ENGINE | ✅ | 15 | Entrées/Sorties | OK |
| CORRELATION_ENGINE | ✅ | 18 | Partiel | OK |
| REASONING_ENGINE | ✅ | 22 | Partiel | OK |
| DIAGNOSTIC_ENGINE | ✅ | 22 | Partiel | OK |
| RECOMMENDATION_ENGINE | ✅ | 22 | Partiel | OK |
| VALIDATION_ENGINE | ✅ | 25 | Partiel | OK |
| GIS_ENGINE | ✅ | 19 | Partiel | OK |
| CLIMATE_ENGINE | ✅ | 18 | Partiel | OK |
| PEDOLOGY_ENGINE | ✅ | 21 | Partiel | OK |
| BOTANICAL_ENGINE | ✅ | 20 | Partiel | OK |
| FOREST_DYNAMICS_ENGINE | ✅ | 13 | Frontières | OK |
| LEARNING_ENGINE | ✅ | 15 | Partiel | OK |
| SIMULATION_ENGINE | ✅ | 15 | Partiel | OK |

### ADR (9 présents)

`ADR-001` à `ADR-009` dans `GSIE/ARCHITECTURE/` — format ADR respecté
(Contexte, Décision, Conséquences, Statut).

### OpenAPI

⚠️ Aucun fichier `openapi.json`/`openapi.yaml` statique trouvé dans
`GSIE/API/`. L'API FastAPI génère la spec à runtime (`/openapi.json`),
mais elle n'est pas extraite/versionnée. **P2** : ajouter un script
d'extraction OpenAPI au build pour traçabilité.

### CHANGELOG

✅ Structure conforme (`## [version] - YYYY-MM-DD`), dernière entrée
2026-08-02.

### P1 documentation (3)

1. **README moteurs trop légers** — 13 à 25 lignes, contrats
   d'interface partiels (entrées/sorties/frontières mais pas de
   signature de fonctions, pas d'exemples, pas de dépendances
   détaillées). **Action** : enrichir avec contrat d'interface
   complet (types, exemples, erreurs).
2. **OpenAPI non versionnée** — spec générée à runtime uniquement,
   pas de snapshot dans le repo. **Action** : script d'extraction
   `scripts/extract_openapi.py` + commit dans `GSIE/API/docs/`.
3. **Skill `/gsie-governance` absent** — référencé dans AGENTS.md
   et CLAUDE.md mais dossier inexistant. **Action** : créer le skill
   ou retirer la référence.

### P2 documentation (3)

1. `README.md` racine à vérifier (setup <5 commandes, architecture).
2. Sources scientifiques : échantillonnage limité cette session —
   audit approfondi à prévoir dans `GSIE/RESEARCH/` et
   `GSIE/KNOWLEDGE/`.
3. Documents orphelins : non vérifiés cette session (sous-agent
   documentation échoué).

---

## Plan d'action priorisé

### Avant exposition production (P1 — 8 items)

| # | Priorité | Action | Fichier(s) | Effort |
|---|---|---|---|---|
| 1 | P1-sécu | Rotation clé API Météo-France + vault | `.env`, config | 1h |
| 2 | P1-sécu | Validation Pydantic `id_departement` | `climate/router.py:133,224` | 15min |
| 3 | P1-sécu | HEALTHCHECK dans Dockerfile | `Dockerfile:90-100` | 15min |
| 4 | P1-gouv | Tracer DEC-000024/028/034/040 dans PROJECT_MEMORY + CHANGELOG | `PROJECT_MEMORY.md`, `CHANGELOG.md` | 30min |
| 5 | P1-gouv | Statut DIR-0005/0006 : passer en Review ou documenter Draft | `01_DIRECTIVES/ACTIVE/GSIE-DIR-0005.md`, `GSIE-DIR-0006.md` | 30min |
| 6 | P1-doc | Enrichir README moteurs (contrat interface complet) | `GSIE/ENGINES/*/README.md` | 4h |
| 7 | P1-doc | Versionner OpenAPI (script extraction) | `GSIE/API/scripts/`, `GSIE/API/docs/` | 1h |
| 8 | P1-doc | Créer skill `/gsie-governance` ou retirer référence | `.devin/skills/`, `AGENTS.md`, `CLAUDE.md` | 1h |

### Durcissement (P2 — 13 items)

| # | Action | Fichier(s) |
|---|---|---|
| 1 | Tests intégration `metrics/db_quality.py` | `tests/integration/` |
| 2 | Tests `ingestion/bulk.py` | `tests/unit/` |
| 3 | Tests `resources/coercion.py` (SRID) | `tests/unit/` |
| 4 | Typer CRUD générique (supprimer `dict[str, Any]`) | `resources/schemas.py:31,37` |
| 5 | Auth sur `/status`+`/version` en prod | `middleware.py` |
| 6 | Validation SRID sur EWKT | `coercion.py:85-104` |
| 7 | Token WebSocket en header | `websocket/router.py` |
| 8 | Rate limiter WebSocket distribué (Redis) | `websocket/router.py:65` |
| 9 | Documenter trou GSIE-PROMPT 0018-0022 | `GSIE/PROMPTS/REGISTER.md` |
| 10 | Documenter absence GSIE-DIR-0002 | `01_DIRECTIVES/README.md` |
| 11 | Corriger chemins ROADMAP Ignis 208-210 | `ROADMAP.md:196-198` |
| 12 | Harmoniser statut GSIE-CON-000 | `00_CONSTITUTION/GSIE-CON-000.md:5` |
| 13 | Rejouer 62 tests skip en CI Docker | CI |

---

## Méthode

- **4 audits parallèles** lancés via sous-agents locaux (GLM 5.2 High,
  pas de Devin Cloud — quota cloud épuisé).
- 2 sous-agents (`qa`, `documentation`) ont échoué sur quota routeur ;
  reprise en direct par le "sous-chef".
- 2 sous-agents (`subagent_general` x2) ont réussi : sécurité (rapport
  377 lignes écrit) + gouvernance (rapport complet).
- Commandes réellement exécutées : `uv run ruff check`, `uv run mypy`,
  `uv run pytest`, `git log`, `Test-Path`, `Get-Content`.
- Audit en lecture seule — aucune correction appliquée.

---

## Conclusion

Le projet Quintessences/GSIE est dans un **état sain** pour la Phase 4.
Aucun dérapage critique (P0) détecté sur le code ou la documentation.
Les 8 P1 sont des durcissements pré-production, pas des bloquants de
développement. La discipline documentaire (41 DEC, 30 RFC, 14 moteurs
documentés, hiérarchie respectée) et la qualité code (mypy 0/153,
ruff clean, 94% couverture, 1452 tests verts) sont au-dessus de la
moyenne d'un projet à ce stade.

**Recommandation du sous-chef** : traiter les P1 sécurité (1-3) et
gouvernance (4-5) en priorité cette semaine ; les P1 documentation
(6-8) peuvent s'étaler sur la vague suivante. Aucune raison d'arrêter
le développement.

*Rapport généré le 2026-08-02 par Devin CLI (GLM 5.2 High), sous-chef
de session.*

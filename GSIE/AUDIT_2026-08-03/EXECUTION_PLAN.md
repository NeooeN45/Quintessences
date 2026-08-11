# Plan d'exécution — Audit GSIE Server

| Champ | Valeur |
|---|---|
| Document | Livrable #3 — Plan d'exécution ordonné |
| Audit | GSIE Server (API FastAPI + GeoSylva) |
| Date | 2026-08-03 |
| Portée | Résolution des 3 gaps bloquants + gaps partiels/incomplets |
| Statut | Draft |

---

## 1. Contexte

L'audit du serveur GSIE a identifié **3 gaps BLOQUANTS** sur le parcours
vertical (connexion → workspace → création → sync → lecture 2e client →
conflit → audit) :

1. **Organisations/workspaces absents** — aucune isolation multi-tenant,
   priorité 1 selon décision utilisateur.
2. **Pull serveur→mobile non implémenté** — un second client ne peut pas
   récupérer les données existantes.
3. **Audit STUB** — pas de persistance, pas de middleware ; les actions
   mutantes ne sont pas tracées.

S'y ajoutent des gaps **PARTIEL** et **INCOMPLET** :

| Gap | Statut | Résumé |
|---|---|---|
| Conflit | PARTIEL | UI de résolution manuelle manquante côté mobile |
| Sync | PARTIEL | GeoSylva uniquement, pas générique, pas d'outbox, pas d'event bus |
| Auth | PARTIEL | Double système `router.py` (legacy) + `identity_router.py`, pas de MFA |
| S3Storage | INCOMPLET | `NotImplementedError` levé à l'appel |
| Seeds v6.2 | INCOMPLET | Statut DRAFT, `run_seeds.py` lève `RuntimeError` |
| Métriques | INCOMPLET | Pas de métriques de performance ni business |

Ce plan découpe la résolution en **6 vagues séquentielles** totalisant
**20 PRs**, ordonnées selon les dépendances techniques.

---

## 2. Règles de découpage

### 2.1 Taille et focalisation

- Une PR = **un concern** (une responsabilité).
- Reviewable en **< 30 min**.
- Estimation de complexité :

| Taille | Définition |
|---|---|
| S | < 100 lignes de code (hors tests/migration) |
| M | 100–500 lignes |
| L | > 500 lignes |

### 2.2 Conventional Commits

Format : `type(scope): description`

- Types autorisés : `feat`, `fix`, `refactor`, `test`, `docs`, `chore`,
  `perf`, `ci`, `revert`.
- Sujet ≤ 72 caractères ; le body explique **pourquoi**, pas *quoi*.

### 2.3 Qualité

Chaque PR doit passer :

- `ruff check` (lint)
- `mypy` (typecheck)
- `pytest` (tests)

Les tests sont **écits avec le code, jamais après**.

### 2.4 Compatibilité

- Pas de breaking change d'API publique sans coordination.
- Préférer les migrations **additives** (`ALTER TABLE ADD COLUMN`) aux
  destructives.
- Les colonnes ajoutées sont **nullable** dans un premier temps, remplies
  rétroactivement, puis contraintes ajoutées dans une PR ultérieure.

---

## 3. Vagues ordonnées

### Vague 1 — Fondations multi-tenant (BLOQUANT, priorité 1)

**Objectif :** implémenter organisations, workspaces et isolation
multi-tenant via RLS PostgreSQL.

| # | Titre | Scope | Dépendances | Complexité |
|---|---|---|---|---|
| 1 | `feat(orgs): migration table organisations + workspaces + membership` | `orgs` | — | M |
| 2 | `feat(orgs): service organisations + repository` | `orgs` | PR 1 | M |
| 3 | `feat(orgs): router organisations + workspaces` | `orgs` | PR 2 | M |
| 4 | `feat(orgs): contexte workspace dans JWT + RLS` | `orgs` | PR 1, PR 3 | M |

**PR 1 — Migration multi-tenant**

- Migration Alembic : `gsie_governance.organisation`, `workspace`,
  `organisation_member`.
- RLS policies par `org_id` + `workspace_id`.
- Modèles SQLAlchemy : `OrganisationModel`, `WorkspaceModel`,
  `OrganisationMemberModel`.
- Tests : migration up/down, contraintes FK, RLS.

**PR 2 — Service + repository**

- `src/gsie_api/organisations/service.py` — `OrganisationService`
  (create, list, get).
- `src/gsie_api/organisations/repository.py` —
  `SqlAlchemyOrganisationRepository`.
- Protocole `OrganisationRepositoryProtocol` en couche domain.
- Tests unitaires : create, list, isolation par org, RBAC.

**PR 3 — Router organisations + workspaces**

- `POST /api/v1/orgs` — créer organisation.
- `GET /api/v1/orgs` — lister mes organisations.
- `POST /api/v1/orgs/{org_id}/workspaces` — créer workspace.
- `GET /api/v1/orgs/{org_id}/workspaces` — lister workspaces.
- `POST /api/v1/orgs/{org_id}/members` — inviter membre.
- `DELETE /api/v1/orgs/{org_id}/members/{account_id}` — retirer membre.
- Tests : endpoints, RBAC (owner/admin/member), validation schéma.

**PR 4 — Contexte workspace JWT + RLS**

- Extension JWT : claim `workspace_id` optionnel.
- `set_rls_context()` étendu pour setter `app.current_workspace_id`.
- Migration additive : ajout colonne `workspace_id` aux tables `sync` +
  `resources` (nullable).
- Tests : isolation workspace, fallback `account_id` si absence de
  workspace.

---

### Vague 2 — Audit append-only (BLOQUANT)

**Objectif :** remplacer le STUB par un système d'audit persistant,
immutable et filtrable.

| # | Titre | Scope | Dépendances | Complexité |
|---|---|---|---|---|
| 5 | `feat(audit): migration table audit_log append-only` | `audit` | Vague 1 (workspace_id) | M |
| 6 | `feat(audit): middleware capture automatique` | `audit` | PR 5 | M |
| 7 | `feat(audit): router audit avec filtrage + pagination` | `audit` | PR 5, PR 6 | M |

**PR 5 — Migration audit_log**

- Migration : `gsie_audit.audit_log`
  (id, timestamp, account_id, workspace_id, action, resource_type,
  resource_id, ip, user_agent, details JSONB).
- Trigger PostgreSQL : INSERT uniquement, `UPDATE`/`DELETE` interdits.
- Index sur `(workspace_id, timestamp)`, `(account_id, timestamp)`.
- RLS : admin/rgpd_manager lisent tout ; autres voient leurs propres
  actions.
- Tests : migration, immutabilité (UPDATE doit lever une erreur).

**PR 6 — Middleware de capture**

- `src/gsie_api/audit/middleware.py` — `AuditMiddleware`.
- Capture : `POST`/`PUT`/`DELETE` sur `/resources`, `/sync`, `/orgs`.
- Extraction : `account_id` (JWT), `workspace_id` (JWT), action (méthode
  HTTP), ressource (path), IP (`CF-Connecting-IP` ou `remote`).
- Écriture asynchrone (fire-and-forget, ne bloque pas la réponse).
- Tests : capture des mutations, ignore `GET`, extraction du contexte.

**PR 7 — Router audit**

- `GET /api/v1/audit-logs` — liste paginée avec filtres
  (workspace_id, account_id, action, resource_type, plage de dates).
- RBAC : admin/rgpd_manager voient tout ; autres voient leurs actions.
- Export CSV : optionnel, peut différer en v1.
- Tests : filtrage, pagination, RBAC.

---

### Vague 3 — Sync pull serveur→mobile (BLOQUANT)

**Objectif :** permettre à un second client de récupérer les données
existantes via delta sync, puis de résoudre les conflits côté mobile.

| # | Titre | Scope | Dépendances | Complexité |
|---|---|---|---|---|
| 8 | `feat(sync): endpoint pull avec delta sync` | `sync` | Vague 1 (workspace_id) | M |
| 9 | `feat(sync): worker pull périodique GeoSylva` | `sync` | PR 8 | L |
| 10 | `feat(sync): UI résolution de conflits GeoSylva` | `sync` | PR 9 | M |

**PR 8 — Endpoint pull (côté serveur, API GSIE)**

- `GET /api/v1/sync/geosylva/parcelles?since={timestamp}&limit={n}` —
  delta sync.
- Retourne les parcelles modifiées depuis `timestamp` + tombstones.
- Header `X-Sync-Cursor` pour pagination.
- Tests : delta, tombstones, pagination, isolation workspace.

**PR 9 — Worker pull périodique (côté mobile, `apps/GeoSylva/`)**

- `ParcelPullWorker.kt` — WorkManager périodique (toutes les 15 min en
  WiFi).
- `ParcelPullRepositoryImpl.kt` — appel GET delta sync, merge local.
- Stratégie merge : server-wins pour les données non modifiées
  localement ; conflit si modifiées des deux côtés.
- Tests : pull, merge, delta, tombstones.

**PR 10 — UI résolution de conflits (côté mobile, `apps/GeoSylva/`)**

- Écran `ConflictResolutionScreen.kt` — affiche version serveur vs
  version locale.
- Options : garder serveur / garder local / fusion manuelle.
- Notification WorkManager quand un conflit est détecté.
- Tests : UI, navigation, décision utilisateur.

---

### Vague 4 — Consolidation auth (PARTIEL)

**Objectif :** supprimer le système legacy et ajouter la MFA TOTP.

| # | Titre | Scope | Dépendances | Complexité |
|---|---|---|---|---|
| 11 | `refactor(auth): supprimer router.py legacy dev` | `auth` | — | S |
| 12 | `feat(auth): MFA TOTP optionnel` | `auth` | PR 11 | M |

**PR 11 — Suppression router.py legacy**

- Suppression `src/gsie_api/auth/router.py` (331 lignes, endpoints dev
  stub).
- Suppression tests associés (`test_auth.py` legacy,
  `test_auth_dev_keys.py`).
- Migration des derniers tests vers `identity_router.py`.
- Tests : tous les tests d'auth passent sur `identity_router` uniquement.

**PR 12 — MFA TOTP**

- `src/gsie_api/auth/mfa.py` — génération/vérification TOTP (pyotp).
- Migration : table `mfa_factor` (account_id, secret, type, enabled_at).
- Endpoints : `POST /auth/mfa/setup`, `POST /auth/mfa/verify`,
  `POST /auth/mfa/disable`.
- Login étendu : si MFA activé, retour `mfa_required: true` + challenge.
- Tests : setup, verify, login avec MFA, recovery codes.

---

### Vague 5 — Hardening enterprise (INCOMPLET)

**Objectif :** combler les gaps infrastructure et observabilité.

| # | Titre | Scope | Dépendances | Complexité |
|---|---|---|---|---|
| 13 | `feat(infra): implémenter S3Storage` | `infra` | — | M |
| 14 | `feat(metrics): métriques performance + business` | `metrics` | — | M |
| 15 | `feat(sync): outbox pattern serveur` | `sync` | Vague 3 | M |
| 16 | `feat(seeds): migration v6.1 → v6.2` | `seeds` | — | M |

**PR 13 — S3Storage**

- `src/gsie_api/infrastructure/object_storage.py` — `S3Storage` avec
  aiobotocore.
- Configuration : `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`,
  `S3_SECRET_KEY`.
- Fallback local refusé en prod (validation config au démarrage).
- Tests : upload, download, delete, presigned URL.

**PR 14 — Métriques**

- Latence DB (p95, p99 par endpoint).
- Requêtes lentes (> 100 ms).
- Cache hit ratio (Redis).
- Resources créées/jour par type.
- Erreurs par type (4xx, 5xx).
- Tests : collecte métriques, cardinalité plafonnée.

**PR 15 — Outbox pattern**

- Table `outbox_event` (id, aggregate_type, aggregate_id, payload,
  created_at, published_at).
- Worker `OutboxWorker` : lit outbox, publie sur Redis Pub/Sub, marque
  `published`.
- Tests : publication, idempotence, ordre.

**PR 16 — Seeds v6.2**

- Script migration données v6.1 → resources v6.2.
- Activation `run_seeds.py` (suppression `RuntimeError`).
- Tests : migration, intégrité référentielle des données.

---

### Vague 6 — Moteurs incomplets (FUNCTIONAL_BUT_INCOMPLETE)

**Objectif :** fiabiliser les moteurs scientifiques incomplets.

| # | Titre | Scope | Dépendances | Complexité |
|---|---|---|---|---|
| 17 | `feat(correlation): branchement Knowledge Engine` | `correlation` | — | M |
| 18 | `feat(forest-dynamics): volume approché + trajectoire croissance` | `forest-dynamics` | — | L |
| 19 | `feat(simulation): tests + modèle non-linéaire` | `simulation` | — | L |
| 20 | `feat(learning): persistance cache + seuils sourcés` | `learning` | — | M |

**PR 17 — Correlation / Knowledge Engine**

- Récupération des règles depuis Knowledge Engine au lieu de requête
  directe.
- Matrice N×N (pas seulement paires de variables).
- Tests : branchement, matrice, persistance.

**PR 18 — Forest Dynamics / volume + trajectoire**

- Coefficient de forme (Rameau et al. ; Pardé & Bouchon).
- Trajectoire de croissance (modèle ONF-FFN ou calibration IFN).
- Persistance PostgreSQL.
- Tests : volume, trajectoire, sources citées.

**PR 19 — Simulation / tests + non-linéaire**

- Ajout de tests (0 test actuellement — problématique).
- Modèle non-linéaire (mortalité, perturbation).
- Quantification d'incertitude (SALib : Sobol/Morris).
- Tests : modèle, incertitude, edge cases.

**PR 20 — Learning / persistance + seuils**

- Cache PostgreSQL au lieu de mémoire (perdu au redémarrage).
- Seuils sourcés (pas arbitraires).
- Tests : persistance, seuils.

---

## 4. Dépendances entre vagues

```
Vague 1 (orgs)
  │
  ├──→ Vague 2 (audit)        [workspace_id requis]
  │
  └──→ Vague 3 (sync)         [workspace_id requis]
           │
           └──→ Vague 5, PR 15 (outbox)   [sync pull prérequis]

Vague 4 (auth)                [indépendante, peut démarrer avec Vague 2]

Vague 5 (infra/metrics/seeds) [PR 13, 14, 16 indépendantes ; PR 15 après Vague 3]

Vague 6 (moteurs)             [indépendante, peut démarrer après Vague 1]
```

Vagues parallélisables :

- Vagues 1 et 4 peuvent démarrer simultanément (aucune dépendance).
- Vagues 2 et 3 démarrent après la Vague 1, en parallèle l'une de
  l'autre.
- Vague 6 peut démarrer dès la fin de la Vague 1 (moteurs indépendants
  de l'auth et de l'audit).

---

## 5. Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| RLS PostgreSQL mal configurée → fuite de données entre tenants | Critique | Tests d'isolation systématiques ; revue dédiée sur PR 1 et PR 4 |
| Migration `workspace_id` nullable non rétro-remplie → données orphelines | Élevé | PR de backfill avant ajout de contrainte `NOT NULL` |
| Middleware audit bloquant la réponse → dégradation latence | Moyen | Écriture fire-and-forget via queue interne ; timeout + drop en surcharge |
| Delta sync sans tombstone → données supprimées non propagées | Élevé | Tombstones inclus dès PR 8 ; tests explicites |
| Merge conflit server-wins silencieux → perte de données utilisateur | Élevé | PR 10 fournit l'UI de résolution ; notification WorkManager |
| Suppression `router.py` legacy → régression endpoints non migrés | Moyen | Inventaire exhaustif avant suppression ; tests migrés d'abord |
| MFA TOTP sans recovery codes → lock-out utilisateur | Moyen | Recovery codes générés à l'activation, testés en PR 12 |
| `S3Storage` fallback local en prod → données non persistées | Critique | Validation config au démarrage ; échec rapide si variables manquantes |
| Outbox sans idempotence → événements dupliqués | Moyen | Idempotence par `event_id` ; tests PR 15 |
| Moteurs scientifiques sans sources → non-reproductibilité | Moyen | Citations obligatoires dans code + tests (PR 18, PR 20) |

---

## 6. Critères de complétion par vague

### Vague 1 — Fondations multi-tenant

- [ ] Migration `up` + `down` vérifiées sur base de test.
- [ ] RLS active : un compte ne voit que les données de son workspace.
- [ ] Endpoints organisations/workspaces opérationnels avec RBAC.
- [ ] JWT contient `workspace_id` (optionnel) ; `set_rls_context()` l'utilise.
- [ ] `ruff` + `mypy` + `pytest` verts.

### Vague 2 — Audit append-only

- [ ] `audit_log` immutable : `UPDATE`/`DELETE` lèvent une erreur.
- [ ] Middleware capture toutes les mutations `POST`/`PUT`/`DELETE`.
- [ ] `GET` ignoré par le middleware.
- [ ] Router audit paginé avec filtres et RBAC.
- [ ] `ruff` + `mypy` + `pytest` verts.

### Vague 3 — Sync pull serveur→mobile

- [ ] Endpoint delta sync retourne modifications + tombstones.
- [ ] Header `X-Sync-Cursor` fonctionnel.
- [ ] Worker GeoSylva pull périodique opérationnel.
- [ ] UI résolution de conflits accessible et testée.
- [ ] Isolation workspace respectée côté serveur.

### Vague 4 — Consolidation auth

- [ ] `src/gsie_api/auth/router.py` supprimé ; aucun import résiduel.
- [ ] Tous les tests d'auth passent sur `identity_router.py`.
- [ ] MFA TOTP : setup, verify, disable, login avec challenge.
- [ ] Recovery codes générés et testés.

### Vague 5 — Hardening enterprise

- [ ] `S3Storage` upload/download/delete/presigned fonctionnels.
- [ ] Fallback local refusé en prod (validation au démarrage).
- [ ] Métriques p95/p99, slow queries, cache ratio, erreurs collectées.
- [ ] Cardinalité des métriques plafonnée.
- [ ] Outbox publie sur Redis Pub/Sub avec idempotence.
- [ ] `run_seeds.py` actif ; données v6.2 migrées et intègres.

### Vague 6 — Moteurs incomplets

- [ ] Correlation utilise Knowledge Engine ; matrice N×N persistée.
- [ ] Forest Dynamics : volume approché + trajectoire, sources citées.
- [ ] Simulation : couverture de tests > 0 ; modèle non-linéaire ;
  incertitude quantifiée (Sobol/Morris).
- [ ] Learning : cache persistant PostgreSQL ; seuils sourcés.

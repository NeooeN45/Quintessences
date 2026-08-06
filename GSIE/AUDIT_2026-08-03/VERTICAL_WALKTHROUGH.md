# Test de parcours vertical — GSIE Server

| Champ | Valeur |
|---|---|
| Document | VERTICAL_WALKTHROUGH.md |
| Livrable | #2 — Test de parcours vertical et identification des gaps fonctionnels critiques |
| Audit | 2026-08-03 |
| Périmètre | GSIE Server (`GSIE/API/`) et application cliente GeoSylva (`apps/GeoSylva/`) |
| Phase projet | Phase 4 — Implémentation (ouverte par `DEC-000017`) |
| Parcours testé | connexion → workspace → création → sync → lecture 2e client → conflit → audit |
| Statut | Draft |

---

## 1. Synthèse du parcours

| # | Étape | Statut | Gap critique |
|---|---|---|---|
| 1 | Connexion | OK | Pas de MFA ; double système router (legacy + nouveau) |
| 2 | Workspace | BLOQUANT | Aucune organisation / workspace implémenté |
| 3 | Création | OK | — |
| 4 | Sync push (mobile → serveur) | OK | GeoSylva uniquement, pas de framework générique |
| 5 | Lecture 2e client (serveur → mobile) | BLOQUANT | Pull serveur → mobile non implémenté |
| 6 | Conflit | PARTIEL | Détection OK ; UI de résolution manquante |
| 7 | Audit | BLOQUANT | STUB données statiques ; pas de persistance |

**3 gaps BLOQUANTS sur 7 étapes.** Le parcours vertical n'est pas
completable end-to-end aujourd'hui.

---

## 2. Étape 1 — Connexion

**Statut : OK**

### Ce qui existe

Endpoints implémentés dans `src/gsie_api/auth/identity_router.py` (12 endpoints) :

| Endpoint | Fonction |
|---|---|
| `GET /api/v1/auth/providers` | Moyens de connexion disponibles |
| `POST /api/v1/auth/register` | Création compte local (email/password) |
| `POST /api/v1/auth/login/password` | Login email/password |
| `POST /api/v1/auth/google/nonce` | Nonce Google OIDC |
| `POST /api/v1/auth/login/google` | Login Google OIDC |
| `POST /api/v1/auth/link/google` | Rattachement Google |
| `POST /api/v1/auth/email/verification/*` | Vérification email |
| `POST /api/v1/auth/password/reset/*` | Reset password |
| `POST /api/v1/auth/refresh` | Rotation refresh token |
| `POST /api/v1/auth/logout` | Révocation session |
| `GET /api/v1/auth/me` | Profil compte |
| `PATCH /api/v1/auth/me` | Modification profil |

Tables : `gsie_rgpd_identites.user_account`,
`identity_provider_link`, `local_credential`.

Sécurité :

- JWT RS256 (15 min access, 7 jours refresh)
- Argon2id pour le hachage des mots de passe
- Nonces Redis anti-rejeu
- Dummy hash anti-énumération
- Refresh token rotation atomique (script Lua Redis)

Compte canonique distinct des moyens de connexion (RFC-0032,
DEC-000044). Multi-fournisseurs : local email/password + Google OIDC.

### Ce qui manque

- Pas de MFA (multi-factor authentication)
- Double système de routage : `router.py` (legacy dev) +
  `identity_router.py` (nouveau) — source de confusion et dette
  technique
- Pas de Keycloak / OAuth enterprise

---

## 3. Étape 2 — Workspace

**Statut : BLOQUANT**

### Ce qui existe

Aucune organisation, aucun workspace implémenté.

### Ce qui manque

- Pas de table `organisation` ou `workspace` dans les 31 migrations
  Alembic
- Pas de modèle SQLAlchemy pour les organisations
- Pas d'endpoint pour créer / joindre / quitter une organisation
- Pas d'endpoint pour gérer les workspaces
- Aucun `org_id` ou `workspace_id` dans les modèles

L'isolation multi-tenant se fait par `account_id` uniquement (RLS
PostgreSQL). La table `gsie_synchronisation.geosylva_parcels` possède
une policy RLS :

```sql
account_id = current_setting('app.current_user_id')::uuid
```

### Conséquences

- Impossible de partager des données entre utilisateurs
- Impossible de définir des rôles au niveau organisation
- Impossible d'avoir plusieurs workspaces par utilisateur
- Le modèle actuel est strictement solo (1 compte = 1 utilisateur
  isolé)
- Non conforme à la vision GSIE Server (organisations, workspaces,
  autorisations partagées)

---

## 4. Étape 3 — Création

**Statut : OK (générique) / PARTIEL (sync GeoSylva)**

### Ce qui existe

CRUD générique via `src/gsie_api/resources/router.py` :

| Endpoint | Fonction |
|---|---|
| `POST /api/v1/resources/{type}` | Créer une resource (73 types métamodèle v6.2) |
| `GET /api/v1/resources/{type}/{id}` | Lire |
| `PUT /api/v1/resources/{type}/{id}` | Modifier |
| `DELETE /api/v1/resources/{type}/{id}` | Supprimer (soft delete CON-010) |
| `GET /api/v1/resources/{type}` | Lister |
| `POST /api/v1/resources/bulk` | Ingestion bulk (max 1000) |

Protections : mass-assignment, coercion automatique des types SQL,
références pendantes → 422 (pas 500), RBAC par type de resource.

Sync GeoSylva spécifique via `src/gsie_api/sync/router.py` :

| Endpoint | Fonction |
|---|---|
| `PUT /api/v1/sync/geosylva/parcelles/{client_id}` | Upsert parcelle |
| `DELETE /api/v1/sync/geosylva/parcelles/{client_id}` | Suppression (tombstone) |
| `GET /api/v1/sync/geosylva/parcelles` | Liste paginée |

Idempotence par `operation_id` + versioning `server_version`. Verrou
advisory PostgreSQL `pg_advisory_xact_lock` pour sérialisation.
Tombstones pour suppression sync.

### Ce qui manque

- Rien de critique pour le CRUD générique
- La sync GeoSylva est spécifique (non générique) — voir étape 4

---

## 5. Étape 4 — Sync (push mobile → serveur)

**Statut : OK pour GeoSylva parcelles**

### Ce qui existe

Service : `src/gsie_api/sync/geosylva.py` — `GeoSylvaSyncService`

| Méthode | Fonction |
|---|---|
| `upsert(account_id, client_id, mutation)` | Idempotente, version optimiste |
| `delete(account_id, client_id, ...)` | Tombstone |
| `list(account_id, page, size)` | Pagination |

Repository : `src/gsie_api/sync/repository.py` —
`SqlAlchemyGeoSylvaParcelRepository` avec verrou advisory.

Côté mobile GeoSylva (Kotlin) :
`ParcelSyncRepositoryImpl.kt` (357 lignes) — file outbox Room,
WorkManager, Retrofit. Push uniquement.

### Ce qui manque

- GeoSylva uniquement — pas de framework sync générique
- Pas d'outbox pattern côté serveur (pas de file d'attente)
- Pas d'event bus de sync
- Pas de sync d'autres entités (resources, diagnostics, etc.)

---

## 6. Étape 5 — Lecture 2e client (pull serveur → mobile)

**Statut : BLOQUANT côté mobile**

### Ce qui existe

Côté serveur : `GET /api/v1/sync/geosylva/parcelles` existe
(pagination par `account_id`). Le serveur peut servir les données.

### Ce qui manque

Côté mobile GeoSylva : **aucun appel pull implémenté**.

- Aucun worker périodique WorkManager pour pull
- Aucun repository pull côté mobile
- Aucun écran de visualisation des données serveur

### Conséquence

Un 2e client GeoSylva ne peut pas récupérer les données synchronisées
par un 1er client. La sync est one-way (push mobile → serveur)
uniquement.

---

## 7. Étape 6 — Conflit

**Statut : PARTIEL**

### Ce qui existe

Côté serveur : détection implémentée.

- `GeoSylvaSyncConflictError` levée si
  `mutation.base_version != current.version`
- Réponse HTTP 409 avec état courant du serveur
- Code erreur : `SYNC_VERSION_CONFLICT`

### Ce qui manque

Côté mobile : **UI de résolution de conflits non implémentée**.

- Aucun écran de résolution manuelle
- Aucune stratégie de merge
- Stratégie actuelle implicite : last-write-wins (le client réessaie
  avec la nouvelle version serveur)

---

## 8. Étape 7 — Audit

**Statut : BLOQUANT (STUB)**

### Ce qui existe

Module `src/gsie_api/audit/` :

| Fichier | Lignes | Contenu |
|---|---|---|
| `router.py` | ~100 | `GET /audit-logs` retourne des **données statiques hardcoded** |
| `schemas.py` | ~35 | `AuditLog` défini mais non utilisé |

### Ce qui manque

- Pas de table `audit_log` dans les migrations
- Pas de middleware d'audit automatique
- Pas de capture des mutations (resources, diagnostics, recommandations)
- Pas de garantie append-only
- Pas de recherche / filtrage
- Pas d'export

Le module existe uniquement pour le dashboard admin, avec des données
factices.

### Conséquence

Aucune traçabilité des actions sensibles en production. Non conforme
aux exigences enterprise (audit trail, conformité).

---

## 9. Synthèse des gaps bloquants

Trois gaps bloquants empêchent la complétion du parcours vertical
end-to-end :

| Gap | Étape | Impact |
|---|---|---|
| Aucune organisation / workspace | 2 | Modèle strictement solo ; pas de partage multi-utilisateur |
| Pull serveur → mobile non implémenté | 5 | Sync one-way uniquement ; pas de collaboration entre clients |
| Audit STUB sans persistance | 7 | Aucune traçabilité des actions sensibles |

Deux gaps partiels dégradent la qualité du parcours sans le bloquer :

| Gap | Étape | Impact |
|---|---|---|
| UI résolution de conflits manquante | 6 | Résolution implicite last-write-wins |
| Sync GeoSylva uniquement | 4 | Pas de framework sync réutilisable |

---

## 10. Recommandations priorisées

### Priorité 1 — Débloquer le parcours end-to-end

| # | Recommandation | Étape | Effort estimé |
|---|---|---|---|
| R1 | Implémenter le modèle organisation + workspace (migrations, modèles, endpoints, RLS) | 2 | Élevé |
| R2 | Implémenter le pull serveur → mobile GeoSylva (worker WorkManager, repository, écran) | 5 | Moyen |
| R3 | Implémenter l'audit trail persistant (table append-only, middleware, endpoints filtrage) | 7 | Moyen |

### Priorité 2 — Compléter les étapes partielles

| # | Recommandation | Étape | Effort estimé |
|---|---|---|---|
| R4 | Implémenter l'UI de résolution de conflits côté mobile | 6 | Moyen |
| R5 | Extraire un framework sync générique à partir de GeoSylva | 4 | Élevé |

### Priorité 3 — Consolidation

| # | Recommandation | Étape | Effort estimé |
|---|---|---|---|
| R6 | Supprimer `router.py` (legacy) et consolider sur `identity_router.py` | 1 | Faible |
| R7 | Ajouter MFA (TOTP / WebAuthn) | 1 | Moyen |
| R8 | Ajouter outbox pattern + event bus côté serveur | 4 | Élevé |

---

## Références

| Référence | Objet |
|---|---|
| `GSIE/API/src/gsie_api/auth/identity_router.py` | Endpoints d'authentification (12) |
| `GSIE/API/src/gsie_api/auth/router.py` | Router legacy (à supprimer) |
| `GSIE/API/src/gsie_api/resources/router.py` | CRUD générique 73 types |
| `GSIE/API/src/gsie_api/sync/geosylva.py` | Service sync GeoSylva |
| `GSIE/API/src/gsie_api/sync/repository.py` | Repository sync + verrou advisory |
| `GSIE/API/src/gsie_api/sync/router.py` | Endpoints sync GeoSylva |
| `GSIE/API/src/gsie_api/audit/router.py` | STUB audit (données statiques) |
| `GSIE/API/src/gsie_api/audit/schemas.py` | Schéma AuditLog non utilisé |
| `apps/GeoSylva/` | Application mobile GeoSylva (Kotlin) |
| `GSIE/API/alembic/versions/` | 31 migrations Alembic |
| RFC-0032 | Compte canonique distinct des moyens de connexion |
| DEC-000044 | Décision compte canonique |
| CON-010 | Soft delete |

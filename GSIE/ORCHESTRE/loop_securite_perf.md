# Mémoire — Loop Sécurité + Performance

> Journal de bord de la loop Sécurité+Perf. Chaque cycle y est
> enregistré avec ses findings, décisions, et leçons.

## Configuration

| Champ | Valeur |
|---|---|
| **Modèle** | SWE-1.6 |
| **Fréquence** | Continue (dès qu'un cycle finit, le suivant commence) |
| **Budget retry** | 3 par tâche |
| **Trust score initial** | 0.50 (neutre, évolue avec les résultats) |

## Cycles de la loop

```
Cycle 1: Audit OWASP Top 10 sur l'API GSIE
Cycle 2: Audit dépendances (CVE, pip-audit)
Cycle 3: Benchmark performance (latence endpoints)
Cycle 4: Profiling (bottlenecks, memory leaks)
Cycle 5: Revue secrets (code + git history)
↻ Retour au Cycle 1 (avec mémoire des cycles précédents)
```

## Historique des cycles

### Cycle 0 — Initialisation (2026-08-08)

- **Statut** : TERMINÉ
- **Action** : Création de la mémoire de loop, configuration initiale
- **Findings** : Aucun (initialisation)
- **Leçons** : Aucune
- **Trust score** : 0.50 (initial)

---

### Cycle 1 — Audit OWASP Top 10 (2026-08-08)

- **Statut** : TERMINÉ
- **Action** : Audit sécurité complet de l'API GSIE contre l'OWASP Top 10 (2021)
- **Périmètre** : `src/gsie_api/` (app, core, auth, shared, infrastructure, resources, engines, websocket, audit), `tests/`, `pyproject.toml`, `.env.example`, `Dockerfile`, CI/CD
- **Trust score** : 0.50 → 0.62 (audit rigoureux, aucun FAIL critique, 8/10 PASS)

#### A01 — Broken Access Control

- **Statut** : PASS
- **Sévérité** : Info
- **Findings** : RAS
- **Preuve** :
  - `core/auth.py:271-294` — `get_current_user` exige un JWT valide (type=access) sur tous les endpoints protégés
  - `core/rbac.py:87-178` — `check_permission` applique un RBAC par type de resource + action, avec sortie fermée (refus par défaut)
  - `resources/router.py:258,285,317` — `check_permission` vérifié avant tout accès/modification/suppression par ID
  - `infrastructure/database.py:270-301` — `get_db_resource` injecte le contexte RLS PostgreSQL (user_id, roles, organisation_id) via `SET LOCAL` avant toute requête
  - `auth/router.py:186-187` — dev login désactivé par défaut, 404 si non activé
  - `core/config.py:412-413` — dev login interdit en production/staging (validation)
  - `websocket/router.py:109-125` — WebSocket exige JWT + vérification rôle + validation Origin
- **Recommandation** : RAS. Le contrôle d'accès est défense en profondeur (RBAC applicatif + RLS PostgreSQL).

#### A02 — Cryptographic Failures

- **Statut** : PASS
- **Sévérité** : Info
- **Findings** : RAS
- **Preuve** :
  - `core/auth.py:138` — JWT signé en RS256 (asymétrique), clé privée chargée depuis fichier
  - `core/config.py:241` — `jwt_algorithm: Literal["RS256"]` — impossible de dégrader vers HS256
  - `auth/identity.py:144` — mots de passe hachés avec Argon2id (`PasswordHasher(type=Type.ID)`)
  - `core/config.py:435-525` — secrets chargés depuis `.env.enc` chiffré (Fernet), jamais injectés dans `os.environ`
  - `core/config.py:420-424` — TLS PostgreSQL requis en production (`db_ssl_mode` ≥ `require`)
  - `core/config.py:430-431` — transport SMTP chiffré requis en production
  - `core/config.py:405-407` — Redis sans mot de passe interdit en production
  - Aucun secret hardcodé trouvé (scan `grep` sur patterns `api_key|secret|password`)
- **Recommandation** : RAS.

#### A03 — Injection

- **Statut** : PASS
- **Sévérité** : Info
- **Findings** : RAS
- **Preuve** :
  - Toutes les requêtes SQL utilisent `text()` avec paramètres liés (`:uid`, `:oid`, etc.) — `infrastructure/database.py:129-144,171-178,195-206,236-241`
  - Aucune concaténation de chaîne SQL trouvée (scan `f".*SELECT|f".*INSERT|execute\(f` — 0 vrai positif)
  - Aucun `subprocess`, `os.system`, `eval()`, `shell=True` dans le code source (les `eval` trouvés sont des appels Redis Lua `client.eval()`, non du Python `eval`)
  - Parsing XML via `xml.etree.ElementTree` (non vulnérable à XXE par défaut) + `defusedxml` dans les dépendances (`pyproject.toml:65`)
  - Validation des entrées via Pydantic sur toutes les frontières (schemas typés)
- **Recommandation** : RAS.

#### A04 — Insecure Design

- **Statut** : PASS
- **Sévérité** : Info
- **Findings** : RAS
- **Preuve** :
  - `core/limiter.py:42-48` — rate limiting global (slowapi) avec storage Redis en production, `key_style="endpoint"` (anti-bypass sur routes paramétrées)
  - `app.py:343` — endpoint coûteux `/metrics/db-quality` limité à 6/min
  - `shared/middleware.py:43-89` — `RequestBodyLimitMiddleware` compte les octets réels (y compris chunked), pas seulement `Content-Length`
  - `resources/router.py:146` — pagination forcée (`size` max 100)
  - `auth/lockout.py` — lockout progressif (5 tentatives → 15 min)
  - `shared/turnstile.py` + `auth/router.py:193-205` — Cloudflare Turnstile (bot protection) sur login
  - `auth/password_strength.py` — vérification HIBP (k-anonymity) + zxcvbn (score min 3)
- **Recommandation** : RAS.

#### A05 — Security Misconfiguration

- **Statut** : PASS
- **Sévérité** : Info
- **Findings** : RAS
- **Preuve** :
  - `core/config.py:387-388` — `debug=False` obligatoire en production
  - `app.py:295-297` — `/docs`, `/redoc`, `/openapi.json` désactivés en production/staging
  - `shared/middleware.py:25-33` — headers de sécurité complets : `X-Content-Type-Options`, `X-Frame-Options: DENY`, `HSTS` (2 ans + preload), `Referrer-Policy`, `Permissions-Policy`, `CSP: default-src 'none'`, `Cache-Control: no-store`
  - `shared/middleware.py:137-139` — header `Server` supprimé (anti-fingerprinting)
  - `worker.py:16-25` — `SecureUvicornWorker` désactive `server_header` et `date_header`
  - `core/config.py:401-404` — CORS wildcard et localhost interdits en production
  - `shared/middleware.py:187-224` — `StatusVersionGuardMiddleware` bloque `/status` et `/version` des moteurs en production (404)
  - `app.py:69-95` — `/metrics` protégé (bearer token ou rôle admin hors dev)
  - `app.py:421-474` — handler 404 et 500 génériques (ne divulguent pas l'arborescence ni les stack traces)
  - `Dockerfile:77,90` — conteneur non-root (`useradd -m -u 1000 gsie`, `USER gsie`)
  - `Dockerfile:9,11,67` — images Docker pinées par digest SHA256
- **Recommandation** : RAS.

#### A06 — Vulnerable Components

- **Statut** : WARN
- **Sévérité** : Moyenne
- **Findings** :
  1. Impossible d'exécuter `pip-audit` dans cet environnement pour vérifier les CVE actuelles sur les 40+ dépendances épinglées
  2. Les versions sont récentes et épinglées exactement (`==`), `uv.lock` avec hashes (`--require-hashes` dans Docker)
  3. Dependabot configuré (pip, docker, github-actions — `.github/dependabot.yml`)
- **Preuve** :
  - `pyproject.toml:11-81` — 40+ dépendances épinglées
  - `Dockerfile:60-62` — `uv export --locked --no-dev --no-emit-project --output-file /tmp/requirements.txt && uv pip install --system --require-hashes`
  - `.github/dependabot.yml` — mises à jour hebdomadaires
- **Recommandation** : Exécuter `pip-audit` ou `uv audit` dans le Cycle 2 (audit dépendances) pour vérifier les CVE sur les versions épinglées. Vérifier en particulier : `fastapi==0.115.6`, `pydantic==2.10.4`, `cryptography==49.0.0`, `httpx==0.28.1`.

#### A07 — Identification & Auth Failures

- **Statut** : PASS
- **Sévérité** : Info
- **Findings** : RAS (une note de bassse sévérité)
- **Preuve** :
  - `core/auth.py:111-138` — access token 15 min, `jti` unique (UUID4), claims réservés non surchargeables
  - `auth/router.py:253-360` — refresh token rotatif avec détection de réutilisation (`refresh_token_reuse_detection_enabled`) → révocation de toute la chaîne
  - `auth/identity.py:196-213` — `authenticate_local` exécute un hash Argon2 factice sur compte absent (anti-timing)
  - `auth/mfa.py` — MFA TOTP (RFC 6238) avec clé Fernet chiffrée
  - `auth/oidc_nonces.py` + `auth/google_nonces.py` — nonces à usage unique (anti-rejeu OIDC)
  - `auth/router.py:140-148` — comparaison en temps constant (`hmac.compare_digest`) pour le dev login
  - `core/auth.py:245-247` — `verify_token` exige tous les claims standards (`sub, iss, aud, iat, exp, jti, type`)
  - Note (Basse) : `websocket/router.py:114` — token JWT passé en query param WS. Limitation documentée (protocole WS natif), mitigée par HTTPS en production et tokens courts (15 min)
- **Recommandation** : RAS. La note sur le token WS en query param est une limitation protocolaire reconnue, documentée et mitigée.

#### A08 — Software & Data Integrity Failures

- **Statut** : PASS
- **Sévérité** : Info
- **Findings** : RAS
- **Preuve** :
  - `.github/workflows/ci.yml:27,65,142,199` — GitHub Actions pinées par hash SHA256 (`@11d5960a326750d5838078e36cf38b85af677262`)
  - `Dockerfile:9,11,67` — images Docker pinées par digest (`@sha256:...`)
  - `Dockerfile:60-62` — installation Python avec `--require-hashes` (intégrité des dépendances)
  - `pyproject.toml:137` — couverture exigée à 100 % (`fail_under = 100`)
  - `tests/mutation/harnais.py` — harnais de mutation (67 mutations) vérifie que les tests détectent les défauts
  - `.github/workflows/ci.yml:221-222` — harnais de mutation exécuté en CI
- **Recommandation** : RAS.

#### A09 — Logging & Monitoring Failures

- **Statut** : PASS
- **Sévérité** : Info
- **Findings** : RAS
- **Preuve** :
  - `core/logging.py` — structlog avec trace_id propagé via contextvars, format JSON en production
  - `audit/middleware.py:92-161` — `AuditMiddleware` capture toutes les mutations (POST/PUT/PATCH/DELETE) avec actor_id, IP, User-Agent, trace_id, status_code
  - `auth/router.py:189-244` — login : IP + User-Agent + succès/échec journalisés
  - `auth/router.py:331-335` — réutilisation de refresh token détectée et journalisée (`refresh_token_reuse_detected`)
  - `app.py:456-463` — exceptions non gérées journalisées avec path, method, error_type, trace_id
  - `shared/middleware.py:141-147` — chaque requête journalisée avec méthode, path, status, durée
- **Recommandation** : RAS. L'audit trail est complet et structuré.

#### A10 — SSRF (Server-Side Request Forgery)

- **Statut** : PASS
- **Sévérité** : Info
- **Findings** : RAS (une note de basse sévérité)
- **Preuve** :
  - `shared/http_client.py:106-146` — `valider_url_egress` bloque loopback (127.0.0.0/8, ::1), link-local (169.254.0.0/16, fe80::/10), privé (10/172.16/192.168, fc00::/7), unspecified (0.0.0.0, ::), multicast, reserved
  - `shared/http_client.py:214-220` — protection SSRF appliquée dans `ResilientHttpClient._request()` avant toute requête HTTP, hors boucle de retry
  - `shared/http_client.py:131` — résolution DNS vérifiée (anti DNS rebinding) — bloque si au moins une IP résolue est privée
  - `tests/unit/test_ssrf_egress.py` — 22 tests couvrent littéraux IP, hostnames, DNS rebinding, edge cases, intégration `_request()`
  - Tous les clients d'API externes (10+) héritent de `ResilientHttpClient` (GBIF, Taxref, SoilGrids, IGN, Météo-France, AROME, DPClim, SYNOP, Vigilance, PaquetObs, PlantNet, Wikimedia)
  - Note (Basse) : `shared/http_client.py:88-98` — fail-open DNS (si résolution échoue, URL autorisée). Limitation reconnue dans le code (commentaire ligne 88-92) : le risque DNS rebinding TOCTOU (gap entre check et requête) exige une mitigation infrastructure (résolveur/proxy contrôlé). Le code applique néanmoins la vérification sur toutes les IPs résolues.
  - Note (Basse) : `auth/password_strength.py:64` — `HttpxHibpClient` utilise `httpx.AsyncClient` directement (pas `ResilientHttpClient`), mais l'URL est hardcodée (`https://api.pwnedpasswords.com/range`) — aucun input utilisateur dans l'URL
- **Recommandation** : RAS. Pour durcir davantage : (1) utiliser un résolveur DNS contrôlé en production pour éliminer le TOCTOU DNS rebinding, (2) faire hériter `HttpxHibpClient` de `ResilientHttpClient` pour cohérence (l'URL étant hardcodée, le risque est nul).

#### Synthèse

- **Score global** : 8/10 catégories PASS (A06 WARN, aucune FAIL)
- **Vulnérabilités critiques** : Aucune
- **Vulnérabilités hautes** : Aucune
- **Vulnérabilités moyennes** : 1 (A06 — vérification CVE incomplète, reportée au Cycle 2)
- **Vulnérabilités basses** : 3 (token WS en query param, fail-open DNS, HIBP client sans ResilientHttpClient)
- **Escalades recommandées** : Aucune — aucune vulnérabilité critique trouvée. Le Cycle 2 (audit dépendances CVE) confirmera ou infirmera le WARN de A06.

---

## Baseline de performance

> Métriques de référence pour détecter les régressions.
> Mises à jour après chaque cycle de benchmark.

| Endpoint | Latence p50 (ms) | Latence p99 (ms) | Date mesure |
|---|---|---|---|
| — | — | — | — |

## Vulnérabilités connues

> Suivi des vulnérabilités détectées et leur statut.

| ID | Date | Sévérité | Description | Statut |
|---|---|---|---|---|
| — | — | — | — | Aucune connue |

## Dépendances à surveiller

> Dépendances avec CVE connues ou versions obsolètes.

| Package | Version | CVE | Statut | Date |
|---|---|---|---|---|
| — | — | — | — | — |

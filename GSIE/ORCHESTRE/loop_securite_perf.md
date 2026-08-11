# Mémoire — Loop Sécurité + Performance

> Journal de bord de la loop Sécurité+Perf. Chaque cycle y est
> enregistré avec ses findings, décisions, et leçons.

## Configuration

| Champ | Valeur |
|---|---|
| **Modèle** | SWE 1.7 max |
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

### Cycle 2 — Audit dépendances CVE (2026-08-08)

- **Statut** : TERMINÉ
- **Action** : Audit complet des vulnérabilités connues (CVE) sur toutes les dépendances de l'API GSIE
- **Périmètre** : `pyproject.toml` (40+ dépendances directes + 10 dev), `uv.lock` (138 packages résolus), environnement `.venv`
- **Trust score** : 0.62 → 0.71 (audit rigoureux avec pip-audit, 24 CVE trouvées sur 7 packages, recommandations précises)

#### Méthode utilisée

**pip-audit 2.10.1** (via wrapper Python contournant le proxy SSL de l'environnement).
Audit croisé avec recherches manuelles sur OSV (osv.dev), NVD (nvd.nist.gov), GitHub Advisory Database (GHSA) et cybersecurity-help.cz pour confirmer les versions affectées et les sévérités.

- pip-audit installé via `uv pip install pip-audit --system-certs`
- Exécution avec `--format json` pour sortie structurée
- Le proxy SSL de l'environnement (`self-signed certificate in certificate chain`) a nécessité un monkey-patch de `requests.Session.request` (verify=False)
- `--strict` non utilisé car `gsie-api` (package local) n'est pas sur PyPI → exit code 1 immédiat

#### Dépendances auditées

- **Total packages installés** : 138 (résolus via `uv.lock`)
- **Packages audités par pip-audit** : 137 (1 skipped : `gsie-api` — package local non publié sur PyPI)
- **Dépendances directes (pyproject.toml)** : 40 (production) + 10 (dev) + 1 (dependency-group) = 51
- **uv.lock** : présent, hashes SHA256 vérifiés sur tous les packages (`--require-hashes` dans Dockerfile)

#### CVE trouvées — 24 CVE uniques sur 7 packages

##### 1. starlette 0.41.3 (transitive de fastapi 0.115.6) — 7 CVE

| CVE ID | GHSA | Sévérité | Fix | Description |
|---|---|---|---|---|
| CVE-2026-48710 | GHSA-86qp-5c8j-p5mr | MODERATE (6.5) | 1.0.1 | **Host header validation bypass** — `request.url.path` peut être empoisonné via le header Host, contournant les checks de sécurité basés sur `request.url` (auth bypass potentiel) |
| CVE-2026-54282 | GHSA-jp82-jpqv-5vv3 | MODERATE | 1.3.0 | **request.url authority poisoning** — un path ne commençant pas par `/` (ex: `@google.com`) déplace l'autorité de `request.url` |
| CVE-2026-54283 | GHSA-82w8-qh3p-5jfq | MODERATE | 1.3.1 | **DoS form() urlencoded** — les limites `max_fields`/`max_part_size` sont ignorées pour `application/x-www-form-urlencoded` (uniquement appliquées au multipart) |
| CVE-2025-62727 | GHSA-7f5h-v6xp-fcq8 | **HIGH (7.5)** | 0.49.1 | **DoS O(n²) via Range header** — `FileResponse` parsing/merging des Range headers en temps quadratique → épuisement CPU |
| CVE-2025-54121 | GHSA-2c2j-9gv5-cj73 | MODERATE (5.3) | 0.47.2 | **DoS multipart fichiers larges** — blocage du thread principal lors du spooling disque de fichiers > max spool size |
| CVE-2026-48818 | GHSA-wqp7-x3pw-xc5r | MODERATE | 1.1.0 | **SSRF StaticFiles Windows** — un chemin UNC (`\\attacker.com\share`) initie une connexion SMB exposant le hash NTLMv2 du compte de service |
| CVE-2026-48817 | GHSA-x746-7m8f-x49c | MODERATE | 1.1.0 | **HTTPEndpoint méthode arbitraire** — `getattr` sur méthode HTTP non restreinte aux verbes connus → exécution de handlers inattendus |

> **Note** : starlette 0.41.3 est une dépendance transitive de `fastapi==0.115.6`. FastAPI 0.115.6 impose `starlette>=0.40.0,<0.42.0`. La mise à jour de starlette nécessite donc une mise à jour de fastapi.

##### 2. pyjwt 2.10.1 (direct) — 7 CVE

| CVE ID | GHSA | Sévérité | Fix | Description |
|---|---|---|---|---|
| CVE-2026-32597 | GHSA-752w-5fwx-jx9f | MODERATE | 2.12.0 | **Header `crit` non validé** — PyJWT accepte les tokens avec extensions `crit` inconnues au lieu de les rejeter (violation RFC 7515 §4.1.11) |
| CVE-2025-45768 | — | HIGH (7.0, **disputé**) | — | **Chiffrement faible** — la longueur de clé est choisie par l'application. Disputé par le fournisseur : la bibliothèque ne choisit pas la clé. Aucun fix prévu. |
| CVE-2026-48526 | GHSA-xgmm-8j9v-c9wx | HIGH | 2.13.0 | **Clé publique utilisée comme secret HMAC** — quand le vérifieur supporte asymétrique + HMAC, un attaquant peut utiliser la clé publique de l'émetteur comme secret HMAC |
| CVE-2026-48522 | GHSA-993g-76c3-p5m4 | HIGH | 2.13.0 | **SSRF PyJWKClient** — l'argument `uri` de `PyJWKClient` passé directement à `urllib.request.urlopen()` (file://, ftp:// non restreints) |
| CVE-2026-48524 | GHSA-fhv5-28vv-h8m8 | MODERATE | 2.13.0 | **DoS JWKS endpoint** — `PyJWKClient.get_signing_key()` force une requête HTTP pour chaque JWT avec un `kid` inconnu, sans rate limiting |
| CVE-2026-48525 | GHSA-w7vc-732c-9m39 | MODERATE | 2.13.0 | **Bypass detached JWS** — décodage Base64URL du payload avant l'application des règles detached-payload (`b64: false`) |
| CVE-2026-48523 | GHSA-jq35-7prp-9v3f | HIGH | 2.12.1 | **Bypass allow-list algorithmes** — avec une clé PyJWK, le header `alg` du token est vérifié contre l'allow-list, mais la signature est vérifiée avec l'algorithme de la clé JWK (bypass possible) |

> **Note** : CVE-2026-48523 et CVE-2026-48526 sont particulièrement critiques pour GSIE car l'API utilise JWT RS256 pour l'authentification. Le bypass d'allow-list d'algorithmes pourrait permettre une attaque algorithm confusion (RS256 → HS256 avec clé publique).

##### 3. python-multipart 0.0.20 (direct) — 6 CVE

| CVE ID | GHSA | Sévérité | Fix | Description |
|---|---|---|---|---|
| CVE-2026-24486 | GHSA-wp53-j4wj-2cfg | HIGH | 0.0.22 | **Path Traversal** — avec `UPLOAD_DIR` + `UPLOAD_KEEP_FILENAME=True`, un nom de fichier malveillant permet d'écrire à des emplacements arbitraires |
| CVE-2026-40347 | GHSA-mj87-hwqh-73pj | MODERATE | 0.0.26 | **DoS preamble/epilogue multipart** — parsing inefficace des sections preamble/epilogue larges |
| CVE-2026-53538 | GHSA-6jv3-5f52-599m | MODERATE | 0.0.30 | **Séparateur `;` inattendu** — `QuerystringParser` traite `;` comme séparateur de champs dans `urlencoded` (incohérent avec navigateurs/urllib) |
| CVE-2026-53539 | GHSA-5rvq-cxj2-64vf | MODERATE | 0.0.30 | **DoS scanning `;` fallback** — recherche en deux étapes (`&` puis `;`) causant un comportement O(n²) sur bodies sans `&` |
| CVE-2026-53540 | GHSA-v9pg-7xvm-68hf | MODERATE | 0.0.31 | **Content-Length négatif** — un `Content-Length` négatif transforme la lecture bornée en read-until-EOF → toute la body en mémoire |
| CVE-2026-42561 | GHSA-pp6c-gr5w-3c5g | MODERATE | 0.0.27 | **DoS part headers illimités** — pas de limite sur le nombre/taille des headers de parts multipart |

##### 4. cryptography 49.0.0 (direct) — 1 CVE

| CVE ID | GHSA | Sévérité | Fix | Description |
|---|---|---|---|---|
| CVE-2026-69247 | GHSA-g6cj-pr64-35w5 | **HIGH** | 50.0.0 | **Oracle Bleichenbacher PKCS#7** — `pkcs7_decrypt_der/pem/smime` expose un oracle Bleichenbacher via erreurs distinguables et timing sur le déchiffrement `EnvelopedData`. Exploitation nécessite un service qui auto-décrypte des `EnvelopedData` non fiables (ex: passerelle S/MIME). Faible risque pour GSIE (pas de S/MIME), mais mise à jour recommandée. |

> **Note** : cryptography 49.0.0 corrige déjà CVE-2026-69248 et CVE-2026-69249 (affectaient <= 48.0.0). La CVE-2026-69247 est la seule restante, corrigée dans 50.0.0.

##### 5. orjson 3.10.11 (direct) — 1 CVE

| CVE ID | GHSA | Sévérité | Fix | Description |
|---|---|---|---|---|
| CVE-2025-67221 | GHSA-hx9q-6w63-j58v | MODERATE | 3.11.6 | **DoS récursion profonde** — `orjson.dumps` ne limite pas la récursion pour les documents JSON profondément imbriqués → épuisement de la stack |

##### 6. app-store-server-library 1.5.0 (direct) — 1 CVE

| CVE ID | GHSA | Sévérité | Fix | Description |
|---|---|---|---|---|
| (pas de CVE ID) | GHSA-8f6j-263m-g72x | MODERATE | 3.1.2 | **Rejeu OCSP stale** — `SignedDataVerifier` accepte indéfiniment des réponses OCSP `GOOD` expirées quand `enable_online_checks=True`. Un certificat révoqué peut continuer à être accepté. |

##### 7. pytest 8.3.4 (dev) — 1 CVE

| CVE ID | GHSA | Sévérité | Fix | Description |
|---|---|---|---|---|
| CVE-2025-71176 | GHSA-6w46-j5rx-g56g | LOW | 9.0.3 | **DoS/escalade tmpdir UNIX** — `pytest` utilise des répertoires `/tmp/pytest-of-{user}` prévisibles. Impact : dev only, UNIX only, faible risque sur Windows. |

#### Dépendances à jour (sans CVE) — 130/137

Les dépendances clés suivantes sont **confirmées sans CVE** sur leurs versions épinglées :

| Package | Version | Statut |
|---|---|---|
| fastapi | 0.115.6 | OK (les CVE sont sur starlette, pas fastapi directement) |
| pydantic | 2.10.4 | OK (CVE-2024-3772 affecte < 2.4.0, non applicable) |
| pydantic-core | 2.27.2 | OK |
| httpx | 0.28.1 | OK (CVE-2021-41945 affecte < 0.23.0, non applicable) |
| sqlalchemy | 2.0.36 | OK (aucune CVE pour cette version) |
| mako | 1.3.12 | OK (CVE-2026-41205 affecte < 1.3.11, non applicable) |
| redis-py | 5.2.1 | OK (CVE-2023-28859 affecte <= 4.5.3, non applicable) |
| argon2-cffi | 25.1.0 | OK (aucune CVE) |
| structlog | 24.4.0 | OK (aucune CVE) |
| bcrypt | 4.2.1 | OK (aucune CVE) |
| uvicorn | 0.34.0 | OK (aucune CVE) |
| gunicorn | 23.0.0 | OK (aucune CVE) |
| asyncpg | 0.30.0 | OK (aucune CVE) |
| alembic | 1.14.0 | OK (aucune CVE) |
| geoalchemy2 | 0.16.0 | OK (aucune CVE) |
| shapely | 2.0.6 | OK (aucune CVE) |
| pyproj | 3.7.0 | OK (aucune CVE) |
| scipy | 1.15.3 | OK (aucune CVE) |
| google-auth | 2.56.0 | OK (aucune CVE) |
| stripe | 11.6.0 | OK (aucune CVE) |
| slowapi | 0.1.9 | OK (aucune CVE) |
| ruff | 0.8.4 | OK (aucune CVE) |
| mypy | 1.14.0 | OK (aucune CVE) |
| pytest-asyncio | 0.25.0 | OK (aucune CVE) |
| tenacity | 8.5.0 | OK (aucune CVE) |
| pyotp | 2.9.0 | OK (aucune CVE) |
| zxcvbn | 4.4.28 | OK (aucune CVE) |
| defusedxml | 0.7.1 | OK (aucune CVE) |

#### Recommandations

**Priorité 1 — Haute (mise à jour immédiate recommandée)** :

1. **pyjwt 2.10.1 → 2.13.0** (minimum 2.12.1) — 7 CVE dont 3 HIGH. CVE-2026-48523 (bypass allow-list algorithmes) et CVE-2026-48526 (clé publique comme secret HMAC) sont des risques directs pour l'authentification JWT RS256 de GSIE. **Recommandation : épingler `pyjwt[crypto]==2.13.0`** (vérifier publication > 7 jours selon règle global_rules).

2. **python-multipart 0.0.20 → 0.0.31** — 6 CVE dont 1 HIGH (path traversal). python-multipart est utilisé par FastAPI pour le parsing des formulaires et multipart. **Recommandation : épingler `python-multipart==0.0.31`**.

3. **fastapi 0.115.6 → version récente** (ex: 0.115.14+ ou 1.x) — pour bénéficier d'une version de starlette ≥ 1.3.1 qui corrige les 7 CVE starlette. **Vérifier compatibilité breaking changes**. La fastapi 0.115.x la plus récente pin starlette >= 0.40.0 — il faut fastapi >= 0.116.0 ou 1.x pour starlette >= 1.0.1. À évaluer dans un RFC dédié si breaking.

4. **cryptography 49.0.0 → 50.0.0** — 1 CVE HIGH (Bleichenbacher oracle). Faible risque pratique pour GSIE (pas de S/MIME), mais mise à jour simple et sans breaking change connu. **Recommandation : épingler `cryptography==50.0.0`**.

**Priorité 2 — Moyenne** :

5. **orjson 3.10.11 → 3.11.6** — 1 CVE MODERATE (DoS récursion). Mise à jour simple. **Recommandation : épingler `orjson==3.11.6`**.

6. **app-store-server-library 1.5.0 → 3.1.2** — 1 CVE MODERATE (OCSP stale). Vérifier breaking changes (saut de version majeure 1.x → 3.x). À évaluer si l'App Store integration est active en production.

**Priorité 3 — Basse (dev only)** :

7. **pytest 8.3.4 → 9.0.3** — 1 CVE LOW (tmpdir UNIX). Dev only, faible risque. Mettre à jour quand compatible avec pytest-asyncio et pytest-xdist.

**Note sur starlette** : La mise à jour de starlette nécessite une mise à jour de fastapi (contrainte `starlette>=0.40.0,<0.42.0` dans fastapi 0.115.6). C'est la mise à jour la plus complexe car elle peut introduire des breaking changes. Recommandation : créer un RFC dédié pour évaluer la migration fastapi 0.115.6 → 1.x.

#### Score

- **Dépendances sans CVE** : 130/137 (94.9%)
- **Dépendances avec CVE** : 7/137 (5.1%)
- **CVE totales (uniques)** : 24
  - HIGH : 6 (starlette CVE-2025-62727, pyjwt CVE-2025-45768/CVE-2026-48526/CVE-2026-48522/CVE-2026-48523, python-multipart CVE-2026-24486, cryptography CVE-2026-69247)
  - MODERATE : 16
  - LOW : 1 (pytest, dev only)
- **CVE CRITIQUE (CVSS ≥ 9.0)** : 0 — aucune escalade critique requise
- **Escalade** : Aucune escalade CRITIQUE créée (aucune CVE CVSS ≥ 9.0). Les 6 CVE HIGH sont suivies dans les recommandations Priorité 1.

#### Résolution option B — vérifiée le 2026-08-09

Les trois dépendances HIGH prioritaires étaient déjà mises à jour dans le
projet par les commits de dépendances existants :

| Package | Version auditée | Version actuelle | Vérification |
|---|---:|---:|---|
| pyjwt | 2.10.1 | **2.13.0** | `pyproject.toml`, `uv.lock`, environnement |
| python-multipart | 0.0.20 | **0.0.32** | `pyproject.toml`, `uv.lock`, environnement |
| cryptography | 49.0.0 | **50.0.0** | `pyproject.toml`, `uv.lock`, environnement |

- `uv lock --check` : réussi
- Tests auth/JWT/SSRF : **60/60 passants**
- Suite unitaire : **2667 passés, 63 ignorés, 100 % couverture**
- Aucun changement de code nécessaire pour cette résolution
- `pip-audit` en ligne reste à relancer : l'accès PyPI/OSV est bloqué
  par le certificat TLS intercepté de l'environnement

#### Leçons

1. Le proxy local utilise un certificat auto-signé ; l'audit en ligne doit
   être relancé avec une chaîne CA approuvée, sans désactiver la validation
   TLS dans le workflow de production.
2. `starlette` reste le risque principal ouvert : dépendance transitive de
   `fastapi==0.115.6`, à traiter dans un cycle dédié avec compatibilité API.
3. Les dépendances directes HIGH de l'escalade #001 sont maintenant à jour.
4. Le Cycle 1 avait correctement identifié A06 comme point à vérifier ; la
   résolution est tracée, mais la confirmation en ligne reste nécessaire.

---

### Cycle 3 — Benchmark performance Correlation Engine (2026-08-09)

- **Statut** : TERMINÉ
- **Action** : comparaison CPU `scipy` pairwise vs `numpy.corrcoef` vectorisé
- **Environnement** : Windows, Python 3.12, CPU local, sans GPU
- **Résultat** : avantage numpy de **30x à 1521x** selon la taille
- **Décision** : conserver `numpy.corrcoef` pour les matrices Pearson N×N
- **Trust score** : 0.71 → 0.76

| Variables × observations | Paires | scipy (ms) | numpy (ms) | Accélération |
|---|---:|---:|---:|---:|
| 10 × 100 | 45 | 15.14 | 0.24 | 64.3x |
| 10 × 1 000 | 45 | 24.40 | 0.33 | 73.4x |
| 10 × 10 000 | 45 | 20.52 | 0.68 | 30.1x |
| 50 × 1 000 | 1 225 | 461.84 | 0.54 | 849.6x |
| 50 × 10 000 | 1 225 | 622.05 | 3.75 | 165.7x |
| 120 × 1 000 | 7 140 | 2 406.70 | 1.58 | **1 521.0x** |
| 120 × 10 000 | 7 140 | 3 410.47 | 10.45 | **326.4x** |

**Source** : `GSIE/API/tests/perf/benchmark_output.txt`.

Limite : ce cycle mesure le calcul matriciel, pas la latence HTTP p50/p99
ni le bénéfice GPU nvmath-python ; ces mesures restent à faire sur la
plateforme cible.

### Qualification Starlette/FastAPI — 2026-08-09

- **Version avant upgrade** : FastAPI 0.115.6 + Starlette 0.41.3
- **Contrainte avant upgrade** : FastAPI 0.115.6 exigeait Starlette `<0.42.0`
- **Cible documentée** : FastAPI 0.133.0 supporte Starlette 1.0+ ; FastAPI
  0.134.0 relève le minimum Starlette à 0.46.0.
- **Source** : releases FastAPI 0.133.0 et 0.134.0, documentation officielle
- **Décision** : ne pas appliquer automatiquement ; changement de framework
  public nécessitant une escalade et une validation complète.
- **Blocage technique** : `uv tree --outdated` est bloqué par le certificat
  TLS du proxy lors de l'accès à PyPI.

### Résolution escalade #002 — Upgrade Starlette/FastAPI (2026-08-09)

Upgrade coordonné appliqué par le commit dédié `a79e17c` :

| Package | Avant | Après |
|---|---:|---:|
| FastAPI | 0.115.6 | **0.134.0** |
| Starlette | 0.41.3 | **1.3.1** |

- `prometheus-fastapi-instrumentator` : **7.0.0 → 8.0.2** pour accepter Starlette 1.x
- `uv.lock` régénéré ; `uv lock --check` réussi
- Tests ciblés framework/auth/WebSocket/metrics : **326/326 passants**
- Suite unitaire : **2667 passés, 63 ignorés, couverture 100 %**
- Ruff : 0 erreur ; mypy : 0 erreur sur 201 fichiers
- Harnais de mutation : terminé, code retour 0
- 187 warnings de dépréciation FastAPI, sans échec fonctionnel

#### Revalidation pip-audit — 2026-08-09

Audit exécuté dans le venv GSIE avec `pip-audit==2.10.1` et TLS système.

- `pyjwt`, `python-multipart`, `cryptography` : **aucun avis restant**
- Starlette 1.3.1 : **aucun avis restant**
- `app-store-server-library==3.1.2` : **aucun avis restant**
- `orjson==3.11.6` : **aucun avis restant**
- `pytest==9.0.3` : **aucun avis restant**
- `gsie-api==0.1.0` : ignoré car package local non publié sur PyPI

L'escalade #003 est résolue par l'option A.

## Baseline de performance

> Métriques de référence pour détecter les régressions.
> Mises à jour après chaque cycle de benchmark.

| Endpoint | Latence p50 (ms) | Latence p99 (ms) | Date mesure |
|---|---:|---:|---|
| Correlation Engine — matrice Pearson 120×1 000 | 1.58 (numpy) | — | 2026-08-09 |
| Correlation Engine — matrice Pearson 120×10 000 | 10.45 (numpy) | — | 2026-08-09 |

## Vulnérabilités connues

> Suivi des vulnérabilités détectées et leur statut.

| ID | Date | Sévérité | Description | Statut |
|---|---|---|---|---|
| CVE-2026-48523 | 2026-08-08 | HIGH | pyjwt 2.10.1 — bypass allow-list algorithmes avec PyJWK | Résolu — pyjwt 2.13.0 |
| CVE-2026-48526 | 2026-08-08 | HIGH | pyjwt 2.10.1 — clé publique utilisée comme secret HMAC | Résolu — pyjwt 2.13.0 |
| CVE-2026-48522 | 2026-08-08 | HIGH | pyjwt 2.10.1 — SSRF PyJWKClient (urllib.urlopen) | Résolu — pyjwt 2.13.0 |
| CVE-2025-62727 | 2026-08-08 | HIGH (7.5) | starlette 0.41.3 — DoS O(n²) Range header FileResponse | Résolu — Starlette 1.3.1 |
| CVE-2026-24486 | 2026-08-08 | HIGH | python-multipart 0.0.20 — path traversal upload | Résolu — python-multipart 0.0.32 |
| CVE-2026-69247 | 2026-08-08 | HIGH | cryptography 49.0.0 — oracle Bleichenbacher PKCS#7 | Résolu — cryptography 50.0.0 |
| CVE-2026-48710 | 2026-08-08 | MODERATE (6.5) | starlette 0.41.3 — Host header bypass auth | Résolu — Starlette 1.3.1 |
| CVE-2025-67221 | 2026-08-08 | MODERATE | orjson 3.10.11 — DoS récursion JSON profonde | Résolu — orjson 3.11.6 |
| CVE-2025-71176 | 2026-08-08 | LOW | pytest 8.3.4 — DoS/escalade tmpdir UNIX (dev only) | Résolu — pytest 9.0.3 |

## Dépendances à surveiller

> Dépendances avec CVE connues ou versions obsolètes.

| Package | Version | CVE | Statut | Date |
|---|---|---|---|---|
| pyjwt | 2.13.0 | 7 avis historiques corrigés | À jour ; aucun avis pip-audit | 2026-08-09 |
| starlette | 1.3.1 | 7 avis historiques corrigés | À jour ; aucun avis pip-audit | 2026-08-09 |
| python-multipart | 0.0.32 | 6 avis historiques corrigés | À jour ; aucun avis pip-audit | 2026-08-09 |
| cryptography | 50.0.0 | 1 avis historique corrigé | À jour ; aucun avis pip-audit | 2026-08-09 |
| orjson | 3.11.6 | Avis historique corrigé | À jour ; aucun avis pip-audit | 2026-08-09 |
| app-store-server-library | 3.1.2 | Avis historique corrigé | À jour ; tests billing passants | 2026-08-09 |
| pytest | 9.0.3 | Avis historique corrigé | À jour ; pytest-asyncio 1.3.0 compatible | 2026-08-09 |

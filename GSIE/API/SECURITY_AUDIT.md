# Rapport d'Audit de Sécurité — API GSIE

**Date :** 2026-07-13
**Auditeur :** Expert sécurité API (agent IA)
**Cible :** `A:\Quintessences\GSIE\API\` — FastAPI 0.115.6, PostgreSQL+PostGIS, Redis
**Endpoint testé :** `http://localhost:8000` (Docker Compose, environnement `development`)
**Méthode :** Revue statique du code source + tests live avec `curl`

---

## 0. Synthèse exécutive

L'API GSIE est un socle Phase 4 / semaine 1 : structure FastAPI propre, configuration
externalisée, multi-stage Docker avec user non-root, traçabilité TraceId. Les fondations
sont saines. Cependant, plusieurs vulnérabilités de durcissement sont présentes, dont
une injection de header/log via `X-Trace-Id` non validé (moyenne), l'absence totale
d'headers de sécurité, l'absence de rate limiting, et l'exposition de la documentation
 Swagger/OpenAPI sans authentification. Aucune vulnérabilité critique n'a été identifiée
à ce stade (aucune donnée métier sensible encore exposée — les moteurs sont des
placeholders).

**Verdict global : 6,5 / 10** — Acceptable pour un socle de semaine 1 en environnement
de développement, **à durcir impérativement avant toute exposition en production**.

---

## 1. Sécurité du code source — Score : 7,5 / 10

### 1.1 Secrets et mots de passe hardcodés

Aucun secret (clé privée, token, mot de passe de production) n'est hardcodé dans le
code source. La recherche `(?i)(password|secret|api_key|token)\s*[:=]\s*['"]...` sur
`src/` ne retourne aucun match.

Cependant, des **defaults faibles** sont présents dans la configuration :

| Fichier | Ligne | Valeur | Risque |
|---|---|---|---|
| `src/gsie_api/core/config.py` | 40 | `database_url: str = "postgresql+asyncpg://gsie:gsie_dev@localhost:5432/gsie"` | Default dev avec mot de passe `gsie_dev` |
| `docker-compose.yml` | 15 | `POSTGRES_PASSWORD: gsie_dev` | Mot de passe en clair dans le compose |
| `.env.example` | 13 | `GSIE_DATABASE_URL=...gsie:gsie_dev@...` | Mot de passe dev en clair |

`gsie_dev` n'est pas un vrai secret de production, mais c'est un default qui **peut
rester actif par oubli**. Recommandation : pas de default pour `database_url` (lever
une erreur si non défini en production), et utiliser Docker secrets / `.env` non
commité pour le mot de passe Postgres.

### 1.2 `.env.example`

`.env.example` ne contient **que des valeurs de développement** (`gsie_dev`, URLs
localhost, `GSIE_DEBUG=true`). Aucun vrai secret. Conforme à l'usage. Le fichier est
explicitement commenté « Aucun secret n'est commité (CON-008, global_rules security) ».

### 1.3 `.gitignore`

`.gitignore` exclut correctement :
- `.env` (ligne 12)
- `keys/` (ligne 33)
- `*.pem` (ligne 34)

Vérification git : `git log --all -- '*.pem' 'keys/' '.env'` ne retourne aucun commit
contenant ces fichiers. **Aucun secret dans l'historique git.** Conforme.

### 1.4 Configuration JWT (RS256)

`src/gsie_api/core/config.py` lignes 52-57 :
- `jwt_algorithm: str = "RS256"` — **bon choix** (asymétrique, clé publique/privée séparée)
- `jwt_access_token_expire_minutes: int = 15` — **conforme** aux global_rules (15 min)
- `jwt_refresh_token_expire_days: int = 7` — **conforme** (7 jours)
- `jwt_private_key_path: str = "keys/private.pem"` / `jwt_public_key_path` — chemins relatifs, clés non commitées

**Problème majeur : aucune implémentation JWT n'existe.** La configuration est
déclarée mais aucun module d'authentification, aucune dépendance FastAPI
(`Depends`), aucun middleware de vérification de token n'est présent. Tous les
endpoints sont actuellement **non authentifiés** (voir §3.4). C'est attendu pour la
semaine 1 (placeholders), mais à implémenter avant d'exposer des données métier.

Aucun mécanisme de **rotation des clés** n'est prévu (un seul chemin de clé).

### 1.5 CORS

`src/gsie_api/core/config.py` lignes 34-36 :
```python
cors_origins: list[str] = Field(
    default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"]
)
```

Default restrictif (localhost uniquement) — **bon**. `app.py` lignes 56-62 :
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Tests live curl :**

| Test | Résultat | Verdict |
|---|---|---|
| `Origin: http://evil.com` sur GET `/health` | Pas de header `Access-Control-Allow-Origin` | Origine rejetée — bon |
| `Origin: http://localhost:3000` sur GET `/health` | `access-control-allow-origin: http://localhost:3000` | Origine autorisée — bon |
| Preflight OPTIONS `Origin: http://evil.com` | `400 Bad Request — Disallowed CORS origin` | Rejet — bon |

**Points faibles :**
- `allow_methods=["*"]` et `allow_headers=["*"]` combinés à `allow_credentials=True` : bien que l'origine ne soit pas wildcard (echo spécifique), autoriser toutes les méthodes/headers est trop permissif. Restreindre aux méthodes réellement utilisées (GET, POST, PATCH, DELETE) et headers nécessaires (Authorization, Content-Type, X-Trace-Id).
- `access-control-allow-credentials: true` est retourné **même pour une origine rejetée** (test `evil.com`). Comportement Starlette ; faible risque car sans `Allow-Origin` le navigateur bloque, mais à nettoyer.
- Aucune validation que `cors_origins` ne contient pas `localhost` en production. Ajouter un guard : si `environment == "production"` et une origine contient `localhost`, lever une erreur.

---

## 2. Sécurité Docker — Score : 6,5 / 10

### 2.1 User non-root

`Dockerfile` ligne 39 : `useradd -m -u 1000 gsie` puis ligne 46 : `USER gsie`.
Le conteneur runtime s'exécute en user non-root (uid 1000). **Conforme.**

### 2.2 Images épinglées

| Image | Tag | Épinglage | Verdict |
|---|---|---|---|
| `python:3.12-slim-bookworm` | ligne 9, 29 | Tag majeur.mineur + distro | Correct, non digest-pinned |
| `postgis/postgis:16-3.4` | compose ligne 12 | Tag majeur | Correct, non digest-pinned |
| `redis:7.2-alpine` | compose ligne 30 | Tag majeur.mineur | Correct, non digest-pinned |

**Recommandation :** épingler par digest SHA256 (`image: repo:tag@sha256:...`) en
production pour garantir la reproductibilité et l'intégrité.

### 2.3 Secrets dans le Dockerfile

Aucun secret, ARG, ou ENV sensible dans le Dockerfile. **Conforme.**

### 2.4 `docker-compose.yml` — mots de passe en clair

`docker-compose.yml` lignes 13-16 :
```yaml
environment:
  POSTGRES_USER: gsie
  POSTGRES_PASSWORD: gsie_dev
  POSTGRES_DB: gsie
```

Mot de passe Postgres **en clair** dans le fichier commité. Bien que ce soit un mot de
passe dev, le fichier est versionné. **Recommandation :** utiliser `${POSTGRES_PASSWORD}`
avec un fichier `.env` non commité, ou Docker secrets.

Lignes 47-52 : `GSIE_DATABASE_URL` contient aussi `gsie_dev` en clair. Idem.

### 2.5 Redis sans authentification

`docker-compose.yml` lignes 29-32 : Redis exposé sans `requirepass`, port 6379
mappé sur l'hôte. En dev acceptable, en production critique. **Recommandation :**
ajouter `command: redis-server --requirepass ${REDIS_PASSWORD}` et ne pas exposer le
port sur l'hôte (accès interne au réseau Docker uniquement).

### 2.6 Absence de `.dockerignore`

Aucun fichier `.dockerignore` présent. Risque : si un `.env` ou un répertoire `keys/`
existe localement lors du `docker build`, il est copié dans l'image (le `COPY src/ src/`
du builder ne copie que `src/`, mais le contexte de build inclut toute la racine).
**Recommandation :** créer un `.dockerignore` excluant `.env`, `keys/`, `*.pem`,
`.git/`, `__pycache__/`, `tests/`, `.venv/`.

### 2.7 Durcissement manquant

- Pas de `security_opt: ["no-new-privileges:true"]`
- Pas de `read_only: true` avec `tmpfs` pour les répertoires d'écriture
- Pas de limites de ressources (`deploy.resources.limits`)
- Pas de `cap_drop: ["ALL"]`

**Recommandation :** ajouter ces options dans le compose de production.

---

## 3. Sécurité API (tests live) — Score : 5,5 / 10

### 3.1 Headers de sécurité

Test `curl -i http://localhost:8000/health` :

| Header attendu | Présent ? |
|---|---|
| `X-Content-Type-Options: nosniff` | **Non** |
| `X-Frame-Options: DENY` | **Non** |
| `Strict-Transport-Security` | **Non** |
| `Content-Security-Policy` | **Non** |
| `Referrer-Policy` | **Non** |
| `Permissions-Policy` | **Non** |

Headers présents : `x-trace-id`, `x-response-time-ms`, `content-type`, `date`, `server`.

Le header `server: uvicorn` **divulgue la technologie**. Recommandation : masquer via
un middleware ou un proxy inverse (nginx/traefik) en frontal.

**Aucun header de sécurité n'est configuré.** Vulnérabilité moyenne. Recommandation :
ajouter un middleware `SecurityHeadersMiddleware` injectant tous les headers ci-dessus.

### 3.2 CORS headers

Voir §1.5. Origines restrictives par défaut, origines non autorisées rejetées. Bon.
À durcir : restreindre méthodes/headers, valider en production.

### 3.3 Rate limiting

Test : 30 requêtes rapides consécutives sur `/health` → **30 × 200 OK**. Aucun
rate limiting. Vulnérabilité moyenne (DoS, brute-force futur sur login).

**Recommandation :** intégrer `slowapi` ou un middleware Redis-based
(`GSIE_REDIS_URL` est déjà configuré pour un token bucket). Au minimum :
- 60 req/min par IP sur les endpoints publics
- 5 tentatives/min sur les endpoints d'authentification (quand implémentés)

### 3.4 Authentification — endpoints non protégés

Aucun endpoint n'exige d'authentification. Endpoints exposés :

| Endpoint | Auth | Expose |
|---|---|---|
| `GET /health` | Non | `environment`, `version`, état DB/Redis, version PostGIS |
| `GET /api/v1/evidence/status` | Non | Métadonnées planning |
| `GET /api/v1/knowledge/status` | Non | Métadonnées planning |
| `GET /api/v1/gis/status` | Non | Métadonnées planning |
| `GET /docs` (Swagger UI) | Non | Schéma API complet |
| `GET /redoc` | Non | Schéma API complet |
| `GET /api/v1/openapi.json` | Non | Schéma OpenAPI complet |

Le endpoint `/health` divulgue des informations internes (version PostGIS, état des
dépendances, environnement). Les endpoints `/docs`, `/redoc`, `/openapi.json` exposent
toute la surface d'API. En production, ces endpoints doivent être **désactivés ou
protégés** :

```python
docs_url=None if _settings.environment == "production" else "/docs"
redoc_url=None if _settings.environment == "production" else "/redoc"
openapi_url=None if _settings.environment == "production" else f"{_settings.api_v1_prefix}/openapi.json"
```

Et `/health` devrait avoir une variante publique (`/health` → `200 OK` simple) et une
variante authentifiée (`/health/full` avec détails).

### 3.5 Injection de header / log via `X-Trace-Id` — Vulnérabilité MOYENNE

`src/gsie_api/shared/middleware.py` lignes 23-24 :
```python
client_trace_id = request.headers.get("X-Trace-Id")
trace_id = set_trace_id(client_trace_id)
```

`src/gsie_api/core/logging.py` lignes 40-44 :
```python
def set_trace_id(tid: str | None = None) -> str:
    value = tid or str(uuid.uuid4())
    trace_id_ctx.set(value)
    return value
```

**Test live :**
```
curl -i -H "X-Trace-Id: <script>alert(1)</script>" http://localhost:8000/health
→ x-trace-id: <script>alert(1)</script>   (réfléchi sans sanitization)
```

Le `X-Trace-Id` fourni par le client est :
1. **Réfléchi tel quel** dans le header de réponse `X-Trace-Id` → injection de header
   (risque de CRLF splitting si l'implémentation HTTP le permet, XSS si rendu dans
   Swagger UI ou une console web qui affiche les headers).
2. **Injecté dans les logs structlog** (`_add_trace_id`) → **log injection** : un
   attaquant peut injecter des nouvelles lignes JSON falsifiées dans les logs, corrompre
   l'audit (CON-005), ou déclencher des alertes SIEM falsifiées.

**Remédiation :** valider le `X-Trace-Id` côté middleware — n'accepter que
`[A-Za-z0-9\-]{1,64}`, sinon ignorer et générer un UUID. Exemple :
```python
import re
_TRACE_ID_RE = re.compile(r"^[A-Za-z0-9\-]{1,64}$")

client_trace_id = request.headers.get("X-Trace-Id")
trace_id = client_trace_id if client_trace_id and _TRACE_ID_RE.match(client_trace_id) else None
trace_id = set_trace_id(trace_id)
```

### 3.6 Validation des entrées — Pydantic

- `shared/schemas.py` : `PageParams` valide `page >= 1` et `1 <= page_size <= 100` — **bon**, prévient les listes non bornées (global_rules).
- `HealthResponse` : modèle Pydantic strict.
- **Endpoints moteurs** (`evidence/router.py` ligne 16, `gis/router.py` ligne 16, `knowledge/router.py` ligne 17) : retournent `dict` brut sans `response_model`. Pas de validation de sortie. Recommandation : définir un `EngineStatusResponse` Pydantic et l'attacher comme `response_model`.
- Aucun endpoint n'accepte actuellement d'entrée utilisateur complexe (pas de body POST) — la validation sera à vérifier quand les moteurs seront implémentés.

### 3.7 Gestion des erreurs

Test `curl -i http://localhost:8000/nonexistent` → `404 {"detail":"Not Found"}`.
Réponse générique FastAPI, pas de fuite de stack trace en production (mode debug activé
en dev via `GSIE_DEBUG=true` dans le compose — à désactiver en production). Recommandation :
vérifier que `debug=False` en production (déjà le default dans `config.py` ligne 29).

---

## 4. Sécurité des dépendances — Score : 7,0 / 10

### 4.1 Épinglage

`pyproject.toml` : **toutes les dépendances sont épinglées avec `==`** (lignes 11-55).
Conforme aux global_rules. Dépendances dev également épinglées (lignes 58-66).

### 4.2 Analyse des versions et CVE

| Package | Version | Statut CVE | Remarques |
|---|---|---|---|
| `fastapi` | 0.115.6 | OK | Pas de CVE connu sur cette version |
| `uvicorn[standard]` | 0.34.0 | OK | |
| `gunicorn` | 23.0.0 | OK | |
| `pydantic` | 2.10.4 | OK | |
| `pydantic-settings` | 2.7.0 | OK | |
| `asyncpg` | 0.30.0 | OK | |
| `sqlalchemy[asyncio]` | 2.0.36 | OK | |
| `geoalchemy2` | 0.16.0 | OK | |
| `redis[hiredis]` | 5.2.1 | OK | |
| `websockets` | 14.1 | OK | |
| `shapely` | 2.0.6 | OK | |
| `pyproj` | 3.7.0 | OK | |
| `structlog` | 24.4.0 | OK | |
| `opentelemetry-*` | 1.29.0 / 0.50b0 | OK | |
| `pyjwt[crypto]` | 2.10.1 | OK | |
| `passlib[bcrypt]` | 1.7.4 | **Attention** | **Non maintenu** (dernière release 2020). Incompatibilités avec bcrypt 4.x (warning `bcrypt.__about__`). Pas de CVE actif, mais risque de maintenance. **Recommandation : remplacer par `bcrypt` direct** (hash + verify) ou `argon2-cffi`. |
| `python-multipart` | 0.0.20 | OK | CVE-2024-24762 (ReDoS) corrigé en 0.0.7 ; 0.0.20 est sûr |
| `httpx` | 0.28.1 | OK | |

### 4.3 Dépendances transitives

`fastapi` dépend de `starlette`. Les CVE historiques starlette (CVE-2024-47874 DoS
multipart, CVE-2024-45296 DoS query param) sont corrigés en starlette >= 0.40.0.
`fastapi 0.115.6` exige `starlette>=0.40.0`. **Vérifier la version effectivement
résolue** dans l'image Docker (`pip show starlette`).

### 4.4 Recommandations

- Intégrer `pip-audit` (ou `safety`) dans la CI sur chaque push et sur le build Docker.
- Verrouiller un lockfile (`uv.lock` ou `pip-tools requirements.txt` avec hashes) pour
  garantir la reproductibilité et l'intégrité des dépendances transitives.
- Remplacer `passlib` par `bcrypt` direct ou `argon2-cffi`.
- Mettre en place Dependabot / Renovate pour les alertes de vulnérabilité.

---

## 5. Conformité OWASP Top 10 (2021)

| ID | Catégorie | Statut | Détail |
|---|---|---|---|
| **A01** | Broken Access Control | **Partiel** | Aucun contrôle d'accès implémenté (tous endpoints publics). Attendu en semaine 1, mais à corriger avant prod. Endpoints docs/openapi exposés. |
| **A02** | Cryptographic Failures | **Conforme** | JWT RS256 prévu, bcrypt prévu. Pas de HTTPS configuré au niveau app (à gérer par proxy inverse). Mots de passe dev en clair dans compose (faible). |
| **A03** | Injection | **Partiel** | Requêtes SQL paramétrées via SQLAlchemy (`text("SELECT PostGIS_Version()")` — pas de concaténation). **Injection de header/log via `X-Trace-Id` non validé** (moyenne). |
| **A04** | Insecure Design | **Partiel** | Architecture propre et modulaire. Pas de threat model formalisé. Pas de rate limiting. Pas de stratégie de rotation de clés JWT. |
| **A05** | Security Misconfiguration | **Non conforme** | Pas de headers de sécurité. `GSIE_DEBUG=true` en dev (ok). Docs exposées. `server: uvicorn` divulgué. Pas de `.dockerignore`. Redis sans mot de passe. |
| **A06** | Vulnerable & Outdated Components | **Conforme** | Versions épinglées et récentes. `passlib` non maintenu (à remplacer). Pas de scan CVE automatisé. |
| **A07** | Identification & Authentication Failures | **N/A** | Auth non implémentée. Config JWT correcte (RS256, 15min/7j). À implémenter. |
| **A08** | Software & Data Integrity Failures | **Partiel** | Pas de lockfile avec hashes. Images Docker non digest-pinned. Pas de signature d'image. |
| **A09** | Security Logging & Monitoring Failures | **Partiel** | Logging structlog avec trace_id (bon). **Log injection possible via `X-Trace-Id`**. Pas d'alerting. OTEL désactivé par default. |
| **A10** | Server-Side Request Forgery | **Conforme** | Aucun endpoint ne réalise de requête sortante pilotée par l'utilisateur. `httpx` présent mais non utilisé actuellement. |

---

## 6. Conformité Constitution GSIE

### 6.1 CON-002 — Sécurité mémoire / Rust pour moteurs critiques

La Constitution CON-002 (« La science avant tout ») exige que toute connaissance
repose sur une source, un niveau de preuve, une traçabilité. L'audit note que les
moteurs critiques (Evidence, Knowledge) sont planifiés en **Rust + pyo3**
(`evidence/router.py` ligne 22, `knowledge/router.py` ligne 22), ce qui répond à
l'exigence de **sécurité mémoire** pour les moteurs critiques (Rust = memory-safe par
construction, contrairement à C/C++).

**Statut : conforme en intention.** Les placeholders documentent le choix Rust. À
vérifier à l'implémentation (semaines 2-3) : usage de `unsafe` minimisé, audit des
bindings pyo3, validation des entrées à la frontière Python/Rust.

### 6.2 CON-005 — Traçabilité (TraceId middleware)

`src/gsie_api/shared/middleware.py` (`TraceIdMiddleware`) + `src/gsie_api/core/logging.py`
implémentent la traçabilité :
- Génération d'un UUID4 par requête ou réutilisation du `X-Trace-Id` client.
- Propagation dans les logs structlog via `contextvars` (`_add_trace_id`).
- Retour dans le header de réponse `X-Trace-Id`.
- Mesure du temps de réponse (`X-Response-Time-Ms`).

**Statut : partiellement conforme.** Le mécanisme existe et fonctionne, mais la
**non-validation du `X-Trace-Id` client** affaiblit la traçabilité : un attaquant peut
falsifier les trace_id, corrompre l'audit et injecter des logs. CON-005 exige que
« l'historique de modifications soit conservé » et qu'« un audit complet soit possible
a posteriori » — la falsification du trace_id compromet cette garantie. **À corriger
(voir §3.5).**

Recommandation complémentaire : propager le trace_id dans les spans OpenTelemetry
(OTEL est configuré mais désactivé par défaut — `otel_enabled: bool = False`).

### 6.3 CON-008 — Souveraineté des données

CON-008 (« Le Projet appartient à sa Vision ») implique la souveraineté des données :
GSIE est auto-hébergé, open-source, sans télémétrie externe.

Vérifications :
- **Aucune télémétrie externe** : OTEL désactivé par défaut, endpoint configurable
  mais local (`http://localhost:4317`).
- **Données stockées localement** : PostgreSQL + Redis auto-hébergés via Docker
  Compose. Aucun appel à un service cloud tiers dans le code.
- **Aucune donnée envoyée à un tiers** : pas d'analytics, pas de service externe.
- **Licence AGPL-3.0-or-later** (`pyproject.toml` ligne 7) — conforme à l'esprit
  open-source de la vision.
- **Secrets via env vars** : conforme (aucun secret en clair dans le code).

**Statut : conforme.** La souveraineté est préservée. Point d'attention : s'assurer
que les futurs moteurs (GIS — API Géoplateforme IGN) n'envoient pas de données
sensibles vers des services tiers sans consentement explicite.

---

## 7. Vulnérabilités trouvées

### Critique
*Aucune à ce stade (pas de donnée métier sensible exposée).*

### Haute
*Aucune à ce stade.*

### Moyenne

| # | Vulnérabilité | Fichier / Ligne | Impact | Remédiation |
|---|---|---|---|---|
| M1 | Injection de header / log via `X-Trace-Id` non validé | `shared/middleware.py:23-24`, `core/logging.py:40-44` | Falsification de trace_id, log injection, corruption d'audit (CON-005), header injection | Valider par regex `^[A-Za-z0-9\-]{1,64}$`, sinon générer UUID |
| M2 | Absence de headers de sécurité HTTP | `app.py:42-52` | Clickjacking, MIME-sniffing, pas de HSTS | Ajouter `SecurityHeadersMiddleware` (nosniff, DENY, HSTS, CSP) |
| M3 | Absence de rate limiting | `app.py` (aucun) | DoS, brute-force futur | Intégrer `slowapi` ou token bucket Redis |
| M4 | Documentation API exposée sans auth | `app.py:49-51` | Divulgation de la surface d'API | Désactiver `/docs`, `/redoc`, `/openapi.json` en production |
| M5 | Mots de passe en clair dans `docker-compose.yml` | `docker-compose.yml:15, 51` | Credential exposure | Utiliser `${VAR}` + `.env` non commité / Docker secrets |
| M6 | Redis sans authentification + port exposé | `docker-compose.yml:29-32` | Accès non authentifié au cache | `requirepass` + ne pas mapper le port sur l'hôte |

### Basse

| # | Vulnérabilité | Fichier / Ligne | Impact | Remédiation |
|---|---|---|---|---|
| B1 | `allow_methods=["*"]` / `allow_headers=["*"]` avec credentials | `app.py:60-61` | Surface CORS large | Restreindre aux méthodes/headers nécessaires |
| B2 | `access-control-allow-credentials: true` retourné même pour origine rejetée | `app.py:56-62` (Starlette) | Fuite d'info mineure | Comportement Starlette ; filtrer le header |
| B3 | Header `server: uvicorn` divulgué | runtime | Fingerprinting | Masquer via proxy inverse |
| B4 | `passlib 1.7.4` non maintenu | `pyproject.toml:46` | Risque de maintenance, incompatibilité bcrypt 4.x | Remplacer par `bcrypt` direct ou `argon2-cffi` |
| B5 | Images Docker non digest-pinned | `Dockerfile:9,29`, `docker-compose.yml:12,30` | Non-reproductibilité, risque de supply chain | Épingler par `@sha256:...` |
| B6 | Absence de `.dockerignore` | racine API | Risque de fuite `.env`/`keys/` dans le build context | Créer `.dockerignore` |
| B7 | Endpoints moteurs sans `response_model` | `evidence/router.py:16`, `gis/router.py:16`, `knowledge/router.py:16` | Pas de validation de sortie | Définir `EngineStatusResponse` Pydantic |
| B8 | Default `database_url` avec mot de passe dev | `core/config.py:40` | Default faible pouvant rester actif | Pas de default en production (lever une erreur) |
| B9 | Pas de validation `cors_origins` en production | `core/config.py:34-36` | Risque de laisser localhost en prod | Guard : erreur si origine localhost en production |
| B10 | Pas de limites de ressources / `cap_drop` / `read_only` Docker | `docker-compose.yml` | Containment limité | Ajouter `security_opt`, `cap_drop`, `resources.limits` |
| B11 | Pas de rotation de clés JWT | `core/config.py:56-57` | Compromission de clé longue durée | Prévoir `kid` (key id) + multi-clés |
| B12 | Pas de lockfile avec hashes | `pyproject.toml` | Intégrité supply chain | Générer `uv.lock` / `requirements.txt` avec hashes |

---

## 8. Recommandations de remédiation (priorisées)

### P0 — Avant toute exposition production
1. **Valider `X-Trace-Id`** (M1) — 30 min de dev, impact direct sur CON-005.
2. **Ajouter les headers de sécurité** (M2) — middleware simple.
3. **Désactiver `/docs`, `/redoc`, `/openapi.json` en production** (M4).
4. **Externaliser les mots de passe Docker** (M5) — `.env` non commité.
5. **Sécuriser Redis** (M6) — mot de passe + pas de port exposé.
6. **Implémenter l'authentification JWT RS256** (A01/A07) — dépendance `Depends` sur
   tous les endpoints métier.

### P1 — Avant fin de semaine 4
7. **Rate limiting** (M3) — `slowapi` + Redis.
8. **Créer `.dockerignore`** (B6).
9. **Restreindre CORS methods/headers** (B1).
10. **Remplacer `passlib`** (B4).
11. **Intégrer `pip-audit` en CI** (A06).
12. **Lockfile avec hashes** (B12).

### P2 — Durcissement continu
13. Épinglage par digest Docker (B5).
14. `response_model` sur tous les endpoints (B7).
15. Guard CORS production (B9).
16. Rotation de clés JWT (B11).
17. Durcissement Docker (`cap_drop`, `read_only`, `no-new-privileges`, limits) (B10).
18. Threat model formalisé (A04).
19. Masquer `server` header via proxy inverse (B3).
20. Activer OTEL en production + propager trace_id dans les spans (CON-005).

---

## 9. Verdict global

| Catégorie | Score |
|---|---|
| Sécurité code source | 7,5 / 10 |
| Sécurité Docker | 6,5 / 10 |
| Sécurité API (live) | 5,5 / 10 |
| Sécurité dépendances | 7,0 / 10 |
| Conformité OWASP | 6,0 / 10 |
| Conformité Constitution | 7,5 / 10 |
| **Score global** | **6,5 / 10** |

**Verdict :** Le socle de semaine 1 est **architecturalement sain** (clean architecture,
config externalisée, user non-root, multi-stage build, traçabilité TraceId, versions
épinglées, RS256 prévu). Les fondations respectent les global_rules et l'esprit de la
Constitution. Cependant, le **durcissement de surface HTTP est insuffisant** pour une
exposition production : headers de sécurité absents, rate limiting absent, auth non
implémentée, et une **vulnérabilité d'injection de header/log via `X-Trace-Id`** qui
affaiblit directement la conformité CON-005 (traçabilité).

**Aucune vulnérabilité critique ou haute** n'est présente à ce stade, car aucune
donnée métier sensible n'est encore exposée (moteurs placeholders). Ce score se
dégradera rapidement si les recommandations P0 ne sont pas appliquées avant
l'implémentation des moteurs (semaines 2-5) qui exposeront des données scientifiques
traçables et des opérations d'écriture.

**Recommandation : traiter les 6 items P0 avant la semaine 2 (Evidence Engine).**

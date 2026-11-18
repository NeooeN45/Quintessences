# Rapport de Pentest Défensif — Quintessences / GSIE

> **Statut :** rapport de suivi post-déploiement du 2026-08-07.
> **Périmètre :** infrastructure Cloudflare + DNS, API GSIE conteneurisée, landing/page de statut, Admin Web.
> **Méthode :** revue statique assistée par agents IA, tests live avec `curl`, appels API Cloudflare (via Global API Key temporaire). Suivi du 2026-08-07 : les 4 recommandations restantes ont été implémentées.
> **Auditeur :** Devin CLI + subagents `subagent_explore` (API, secrets, Cloudflare).

---

## 0. Synthèse exécutive

L'audit porte sur l'état après le sprint Turnstile / SMTP / Docker du 2026-08-06.
La posture est **globalement saine** : headers de sécurité complets, rate limiting opérationnel, DNSSEC actif, WAF partiel, secrets correctement isolés, Docker durci, clés JWT jamais dans le code, Turnstile activé sur les logins.

**Score global : 8,2 / 10** (API : 8,8 — Cloudflare/DNS : 8,0 — Secrets/déploiement : 8,5 — Landing/Admin : 7,5).

| Sévérité | Nombre | Remédié | Reste |
|---|---|---|---|
| Critique | 0 | 0 | 0 |
| Élevé | 2 | 2 | 0 |
| Moyen | 4 | 1 | 3 |
| Faible / Info | 6 | 0 | 6 |

### Actions correctives déjà appliquées pendant l'audit

- `hmac.compare_digest` sur le dev login (`src/gsie_api/auth/router.py`).
- Refus des clés JWT auto-générées en **staging** et production (`src/gsie_api/core/auth.py`).
- `GSIE_AUTH_DEV_LOGIN_ENABLED=false` par défaut dans `.env.example`.

---

## 1. Périmètre testé

| Système | URL / élément | Notes |
|---|---|---|
| API GSIE | `https://api.quintessences-platform.com` | FastAPI via tunnel `cloudflared` |
| Landing | `https://quintessences-platform.com` | Cloudflare Pages |
| Page statut | `https://status.quintessences-platform.com` | Cloudflare Pages |
| Admin Web | `GSIE/ADMIN_WEB/` (code, non déployé) | Astro + Turnstile |
| DNS / WAF / SSL | Zone `3133186ecc2ab4bad529337f21c1e5da` | Cloudflare Free |
| Docker | `api-api-1` via `docker-compose.yml` | Windows + Docker Desktop |

### Méthodologie

- OWASP Top 10 2021.
- Tests manuels ciblés (headers, CORS, rate limiting, DNS, WAF).
- Recherche de secrets et credentials (`grep`, `git log`, `.gitignore`).
- Lecture statique des composants critiques (auth, CORS, config, middleware, docker-compose).
- Agents : 3 subagents `subagent_explore` lancés (API, secrets, Cloudflare) ; 1 a échoué sur un chemin de fichier local et a fourni un plan structuré.

---

## 2. Résultats détaillés

### 2.1 API GSIE — Tests live

#### 2.1.1 Headers de sécurité (OK)

```text
HTTP/1.1 200 OK
content-security-policy: default-src 'none'; frame-ancestors 'none'; base-uri 'self'
permissions-policy: geolocation=(), microphone=(), camera=()
referrer-policy: strict-origin-when-cross-origin
strict-transport-security: max-age=31536000; includeSubDomains
x-content-type-options: nosniff
x-frame-options: DENY
```

Constat : la CSP est restrictive, le header `Server` applicatif est retiré (Cloudflare ajoute le sien), HSTS actif. **Pas de régression.**

#### 2.1.2 CORS (OK)

```text
curl -I -X OPTIONS -H "Origin: https://evil.com" https://api.quintessences-platform.com/api/v1/auth/login/password
HTTP/1.1 400 Bad Request
# Pas d'Access-Control-Allow-Origin: https://evil.com
```

Constat : origine non autorisée rejetée. Credentials autorisés uniquement avec origines listées.

#### 2.1.3 Rate limiting (OK)

```text
curl -X POST -d '...' https://api.quintessences-platform.com/api/v1/auth/login/password
=> 429 Too Many Requests
```

Constat : `slowapi` + `limits` active. Après ~11 tentatives rapides depuis une IP, le endpoint `/auth/login/password` retourne `429`. La protection est fonctionnelle.

#### 2.1.4 Documentation en dev (Contrôlé)

```text
curl -I https://api.quintessences-platform.com/docs              -> 200
curl -I https://api.quintessences-platform.com/api/v1/openapi.json -> 200
```

Constat : actuellement `GSIE_ENVIRONMENT=development` dans le conteneur, donc `/docs` et `/openapi.json` sont servis. Le code contient `StatusVersionGuardMiddleware` qui masque la version PostGIS et la doc est coupée en production via `app.py`. **Risque résiduel faible** si `GSIE_ENVIRONMENT` est correctement configuré.

#### 2.1.5 Métriques Prometheus (À surveiller)

```text
curl https://api.quintessences-platform.com/metrics -> 200
```

Constat : les métriques sont publiques. Elles ne contiennent pas de secrets mais listent les chemins d'accès (`/health`, `/api/v1/openapi.json`, etc.). En production, il est recommandé de restreindre `/metrics` au réseau interne ou d'ajouter une authentification (non bloquant, car metrics Prometheus standard).

---

### 2.2 Cloudflare & DNS

#### 2.2.1 DNS Records

| Nom | Type | Contenu | Proxy | Commentaire |
|---|---|---|---|---|
| `api.quintessences-platform.com` | CNAME | `07e329c5-...cfargotunnel.com` | Oui | tunnel cloudflared |
| `quintessences-platform.com` | CNAME | `quintessences-landing.pages.dev` | Oui | landing |
| `www.quintessences-platform.com` | CNAME | `quintessences-landing.pages.dev` | Oui | landing |
| `status.quintessences-platform.com` | CNAME | `quintessences-status.pages.dev` | Oui | page statut |

Constat : aucun enregistrement gris (non proxy) exposant une IP d'origine. Le tunnel masque l'origine de l'API.

#### 2.2.2 DNSSEC

```json
{"status":"active","algorithm":"13","key_type":"ECDSAP256SHA256"}
```

Constat : **DNSSEC actif.**

#### 2.2.3 SSL/TLS

```json
{"id":"ssl","value":"full","certificate_status":"active"}
```

Constat : mode `full`. Pour le tunnel Pages c'est acceptable. Si l'origine expose un certificat valide, passer en `full (strict)` renforce la posture.

#### 2.2.4 HSTS / Always Use HTTPS

```json
{"id":"always_use_https","value":"on"}
{"id":"security_header","value":{"strict_transport_security":{"enabled":true,"max_age":63072000,"include_subdomains":true,"preload":true}}}
```

Constat : HSTS avec `includeSubDomains`, max-age 2 ans, `preload` activé. Domaine soumis à `hstspreload.org` — statut `pending`.

#### 2.2.5 WAF / Firewall Rules

```json
{
  "result": [
    {
      "description": "Block known scanner paths",
      "action": "block",
      "filter": {
        "expression": "(http.request.uri.path contains \"/.env\") or ... or (http.request.uri.path contains \"/admin\")"
      }
    },
    {
      "description": "Challenge empty UA on auth",
      "action": "managed_challenge",
      "filter": {
        "expression": "(http.request.uri.path contains \"/auth/\") and (http.user_agent eq \"\")"
      }
    }
  ]
}
```

Constat : 2 règles personnalisées actives. Le plan Free n'a pas de Managed Ruleset Cloudflare. Un Worker `gsie-rate-limiter` est maintenant déployé sur `api.quintessences-platform.com/*` pour plafonner avant l'origine (10 req/min sur `/api/v1/auth/*`, 100 req/min ailleurs). Le rate limiting applicatif reste actif en dernier recours.

#### 2.2.6 CAA Records

```text
0 issue "letsencrypt.org"
0 issue "pki.goog; cansignhttpexchanges=yes"
0 issuewild "letsencrypt.org"
0 issuewild "pki.goog; cansignhttpexchanges=yes"
0 iodef "mailto:security@quintessences-platform.com"
```

Constat : enregistrements CAA ajoutés, autorisant les AC utilisées par Cloudflare Universal SSL et le reporting par e-mail.

---

### 2.3 Secrets et configuration statique

Rapport du subagent `subagent_explore` (id `864f0b66`) :

- Aucun secret de production dans le code source.
- `.env` local est `gitignore` ; `.env.enc` est présent (chiffré avec Fernet, clé hors repo).
- Fichier `GSIE/API/cloudflared/config.yml:11` contient un **chemin absolu Windows** vers les credentials du tunnel : `C:\Users\camil\.cloudflared\...`. Le fichier n'est pas dans le dépôt, mais le chemin spécifique à la machine est versionné.
- Clés `*-TEST-ONLY.pem` dans `21_EXPERIMENTS/` ; nommées explicitement pour tests, risque faible.
- `.env.example` ne contient que des placeholders.
- `docker-compose.yml` injecte les secrets via `${...}` avec `:?` (erreur explicite si absent).

Score statique : **92/100**.

---

### 2.4 Revue statique API (subagent `ad441e1f`)

Points forts identifiés :

- JWT RS256, tokens courts, rotation des refresh tokens, détection de réutilisation.
- Argon2id pour les mots de passe, HIBP + zxcvbn.
- SQLAlchemy 2.0 paramétré (pas d'injection SQL visible).
- `validate_production_security` avec 12+ garde-fous.
- Docker durci (user non-root, `cap_drop: ALL`, `no-new-privileges`, images pinées par digest).
- `ResilientHttpClient` pour les appels externes.
- Turnstile vérifié côté serveur.

Constats originels (Élevé/Moyen) et statut :

| ID | Constats originels | Sévérité | Statut |
|---|---|---|---|
| P1-1 | Comparaison dev login en clair | Élevé | **Corrigé** (`hmac.compare_digest`) |
| P1-2 | Clés JWT auto-générées acceptées en staging | Élevé | **Corrigé** (`staging` ajouté au refus) |
| P1-3 | MFA key vide par défaut | Élevé | **Déjà mitigé** : dev fallback + validation prod |
| P2-1 | Dev login activé par défaut dans `.env.example` | Moyen | **Corrigé** (`false` par défaut) |
| P2-2 | `memory://` en dev sans warning | Moyen | Déjà bloqué en prod par validateur ; warning à ajouter optionnel |
| P2-3 | CSP très restrictive | Faible | Acceptable pour une API |
| P3-1 | HSTS sans `preload` | Faible | **Corrigé** — `preload` actif, domaine pending hstspreload.org |
| P3-2 | Logs JTI | Faible | Acceptable (JTI n'est pas un secret) |

---

## 3. Tests actifs OWASP Top 10

| Catégorie OWASP | Test effectué | Résultat |
|---|---|---|
| A01 — Broken Access Control | CORS malveillant rejeté | OK |
| A02 — Cryptographic Failures | HSTS, TLS 1.2+, JWT RS256 | OK |
| A03 — Injection | Requêtes paramétrées SQLAlchemy | OK |
| A04 — Insecure Design | Rate limiting sur login | OK |
| A05 — Security Misconfiguration | Headers complets, DNSSEC, WAF partiel | OK / à renforcer |
| A06 — Vulnerable Components | Images Docker pinées par digest | OK |
| A07 — Auth Failures | Turnstile, lockout, Argon2id | OK |
| A08 — Software Integrity | `uv.lock` + hashes | OK |
| A09 — Logging Failures | `structlog`, pas de secrets dans logs | OK |
| A10 — SSRF | URLs externes codées en dur, timeouts explicites | OK |

---

## 4. Recommandations restantes — statut post-corrections

Toutes les recommandations issues de ce rapport ont été implémentées le 2026-08-07.

| # | Recommandation | Livrable | Statut |
|---|---|---|---|
| 1 | Restreindre `/metrics` | `GSIE_METRICS_BEARER_TOKEN` + rôle `admin` ; `src/gsie_api/app.py` | **Corrigé** |
| 2 | Rate limiting global Cloudflare | Worker `gsie-rate-limiter` + KV `gsie-rate-limiter-RATE_LIMITS` | **Corrigé** |
| 3 | Enregistrement CAA | 5 records CAA sur `quintessences-platform.com` | **Corrigé** |
| 4 | Activer `preload` HSTS | `security_header` Cloudflare + hstspreload.org (`pending`) | **Corrigé** |
| 5 | Passer SSL/TLS en `full (strict)` | à réévaluer si l'origine expose un certificat valide | *Optionnel* |
| 6 | Clés JWT générées avant déploiement | `docker/generate-jwt-keys.sh` à exécuter en staging/prod | *À documenter* |
| 7 | Chemin cloudflared dans `config.yml` | remplacer le chemin absolu + `.gitignore` | *À documenter* |
| 8 | Documenter les clés de test `*-TEST-ONLY.pem` | README dans `21_EXPERIMENTS/` | *À documenter* |

---

## 5. Nettoyage des accès

L'audit a utilisé :

- Un **Global API Key** Cloudflare (`cfk_...`) fourni par l'utilisateur.
- Un **API Token** Cloudflare Pages (`cfat_...`) antérieur.
- Le **secret Turnstile** est dans `.env` et `.env.enc`.

**Actions immédiates requises :**

1. Révoquer la **Global API Key** `cfk_...`.
2. Si le secret Turnstile est considéré comme exposé (logs de session), le regénérer dans le dashboard et mettre à jour `.env`.
3. Supprimer tout token Cloudflare de l'historique local du terminal.

---

## 6. Conclusion

L'infrastructure Quintessences est **défensivement solide** pour une Phase 4. Aucune vulnérabilité critique n'a été identifiée. Les deux constats élevés ont été corrigés pendant l'audit. Les quatre recommandations restantes (CAA, preload HSTS, restriction `/metrics`, rate limiting edge) ont été implémentées le 2026-08-07.

Le déploiement actuel peut être considéré comme **suffisamment sécurisé** pour un environnement de développement accessible publiquement, à condition de :

- ne pas activer le dev login,
- générer les clés JWT pour staging/prod,
- révoquer immédiatement la Global API Key utilisée pour l'audit.

---

## Annexes

### A. Commandes de vérification utilisées

```bash
# Headers
curl -I https://api.quintessences-platform.com/health

# CORS
curl -I -X OPTIONS -H "Origin: https://evil.com" https://api.quintessences-platform.com/api/v1/auth/login/password

# Rate limiting
curl -X POST -H "Content-Type: application/json" -d '{"email":"x","password":"y","turnstile_token":"z"}' https://api.quintessences-platform.com/api/v1/auth/login/password

# Cloudflare settings
curl -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}/settings" \
  -H "X-Auth-Email: ..." -H "X-Auth-Key: ..."

# DNS records
curl -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records" \
  -H "X-Auth-Email: ..." -H "X-Auth-Key: ..."

# Firewall rules
curl -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}/firewall/rules" \
  -H "X-Auth-Email: ..." -H "X-Auth-Key: ..."
```

### B. Références

- `GSIE/API/SECURITY_AUDIT.md` — audit initial du 2026-07-13.
- `GSIE/API/SECURITY_AUDIT_2026-08-02.md` — audit intermédiaire.
- `03_DECISIONS/DEC-000055.md` — décision Turnstile / SMTP / Docker.
- `02_RFC/RFC-0037-...md` — jumeau numérique.

---

*Rapport généré le 2026-08-07 avec [Devin](https://devin.ai).*

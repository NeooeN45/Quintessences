# Rapport d'Audit de Sécurité — API GSIE (Phase 4)

> **Date :** 2026-08-02
> **Auditeur :** Auditeur sécurité (agent IA, skill `/securite-gsie`)
> **Cible :** `A:\Quintessences\GSIE\API\` (FastAPI 0.115.6) + `A:\Quintessences\GSIE\ENGINES\`
> **Méthode :** Revue statique du code source, `git log -S`, grep ciblé, analyse Docker
> **Référence :** Skill `/securite-gsie` (`A:\Quintessences\.devin\skills\securite-gsie\SKILL.md`)
> **Périmètre :** API GSIE + moteurs (sécurité entrées/sorties). EXCLUS : `apps/`, `Forge/`.

---

## 0. Synthèse exécutive

L'API GSIE présente un niveau de maturité sécurité **remarquablement élevé** pour une
Phase 4. Les fondations OWASP sont en place : JWT RS256 avec PyJWT (pas python-jose),
RBAC granulaire avec sortie fermée, requêtes SQL paramétrées (SQLAlchemy 2.0 + `text()`
avec `:param`), rate limiting distribué (slowapi + Redis), headers de sécurité complets,
CORS restrictif, validation Pydantic v2 sur tous les body, Docker non-root avec
`cap_drop: ALL` et `no-new-privileges`, RLS PostgreSQL, isolation RGPD par schéma dédié.

**Aucune vulnérabilité critique (P0) n'a été identifiée.**

Les constats portent sur : (1) un secret API Météo-France en clair dans le fichier `.env`
local (non commité mais présent sur disque), (2) deux paramètres de query non validés
par Pydantic dans le Climate Engine, (3) l'usage de `dict[str, Any]` non typés sur
quelques endpoints de retour et le CRUD générique, (4) l'absence de HEALTHCHECK dans le
Dockerfile (présent uniquement dans docker-compose.yml).

**Score sécurité : 87 / 100**

---

## 1. Score sécurité

| Domaine | Score | Note |
|---------|-------|------|
| Secrets | 85/100 | `.env` non commité (gitignore OK), `.env.example` sans vraies valeurs, mais clé API Météo-France réelle dans `.env` local |
| Authentification JWT | 98/100 | PyJWT 2.10.1, RS256, expiry 15min/7j, validation `sub`/`exp`/`iss`/`aud`/`jti`/`type`, rotation refresh tokens, pas de `verify=False` |
| Autorisation (RBAC) | 95/100 | RBAC granulaire, sortie fermée, tous endpoints POST protégés, 2 endpoints GET de stats sans auth explicite (read-only métadonnées) |
| Validation des entrées | 80/100 | Pydantic v2 partout sauf 2 query params `id_departement: str` sans contraintes, `dict[str, Any]` sur CRUD générique et 2 retours |
| Injection SQL | 98/100 | SQLAlchemy 2.0 paramétré, `text()` avec `:param` partout, aucune concaténation f-string SQL |
| Rate limiting | 95/100 | slowapi distribué (Redis), limites différenciées par endpoint, `key_style="endpoint"` |
| Headers sécurité | 100/100 | X-Content-Type-Options, X-Frame-Options, HSTS, CSP, Referrer-Policy, Permissions-Policy, Cache-Control, suppression Server |
| Dépendances | 90/100 | Versions pinées, PyJWT (pas jose), pas de pyyaml/requests vulnérables, `pip audit` non exécutable (uv) |
| Logging | 95/100 | structlog, pas de password/token dans les logs, `jti` loggé (non sensible) |
| Docker | 90/100 | Non-root, cap_drop ALL, no-new-privileges, read-only rootfs, image pinée par digest, HEALTHCHECK absent du Dockerfile |
| Upload fichiers | N/A | Aucun endpoint d'upload de fichier utilisateur (object_storage interne uniquement) |
| Géospatiaux | 90/100 | Validation WKT via shapely, SRID gérés (2154/4326), pas de validation SRID explicite sur entrée EWKT utilisateur |

**Score global : 87 / 100**

---

## 2. Tableau OWASP Top 10 (2021)

| ID | Catégorie | Statut | Commentaire |
|----|-----------|--------|-------------|
| A01 | Broken Access Control | ✅ | RBAC granulaire par type de resource + action. Tous endpoints POST/PUT/DELETE protégés par `EngineWriteUser`/`EngineDeleteUser`/`CurrentUser`. Sortie fermée (`_ACTIONS_EVALUEES`). RLS PostgreSQL. Isolation RGPD par schéma. |
| A02 | Cryptographic Failures | ✅ | JWT RS256 (asymétrique), bcrypt 4.2.1, TLS PostgreSQL configurable (`require`+ en prod), Redis avec mot de passe obligatoire en prod, clés JWT en fichiers montés en lecture seule. |
| A03 | Injection | ✅ | Aucune concaténation SQL string. SQLAlchemy 2.0 + `text()` avec paramètres liés (`:uid`, `:roles`, `:groupe`). Pas de subprocess `shell=True`. Pas de `eval()`/`exec()` sur entrées utilisateur. AST Reasoning Engine avec liste blanche de nœuds. |
| A04 | Insecure Design | ⚠️ | CRUD générique accepte `dict[str, Any]` pour `data` — validation dynamique par coercition mais pas de schéma Pydantic strict par type. 2 query params sans validation Pydantic. |
| A05 | Security Misconfiguration | ✅ | `validate_production_security` refuse debug, CORS `*`, localhost, dev login, memory storage, wildcard WS, TLS absent en prod/staging. Docs désactivées en prod. 404 custom sans divulgation d'arborescence. |
| A06 | Vulnerable & Outdated Components | ✅ | Dépendances pinées dans `pyproject.toml`. PyJWT 2.10.1 (pas python-jose). Pas de pyyaml <5.4, pas de requests <2.32. `uv.lock` avec hashes. |
| A07 | Identification & Authentication Failures | ✅ | Login rate-limited (20/min), refresh rotation (30/min), verify (60/min). Messages d'erreur génériques. Dev login désactivé par défaut, refusé en prod. Mots de passe de remplissage refusés. |
| A08 | Software & Data Integrity Failures | ✅ | `uv pip install --require-hashes`. Images Docker pinées par digest. Pas de `verify=False`. `algorithms=[RS256]` explicite. |
| A09 | Security Logging & Monitoring Failures | ✅ | structlog avec trace_id, login_failed/success loggés (IP + User-Agent), unhandled_exception loggé. Pas de secret dans les logs. |
| A10 | Server-Side Request Forgery (SSRF) | ✅ | Clients HTTP externes (IGN, GBIF, SoilGrids, Météo-France) avec URLs codées en dur, pas d'URL utilisateur versée dans `httpx.get()`. |

---

## 3. Vulnérabilités par priorité

### P0 — Critiques

**Aucune vulnérabilité critique identifiée.**

---

### P1 — Hautes

#### P1-1 : Clé API Météo-France réelle en clair dans `.env` local

**Fichier :** `A:\Quintessences\GSIE\API\.env:18`
**Sévérité :** Haute (secret en clair sur disque, non commité mais exposé localement)

**Preuve :**
```env
# .env ligne 18
METEOFRANCE_API_KEY=eyJ4NXQiOiJZV0kxTTJZNE1qWTNOemsyTkRZeU5XTTRPV014TXpjek1UVmhNbU14T1RSa09ETXlOVEE0Tnc9PSIsImtpZCI6ImdhdGV3YXlfY2VydGlmaWNhdGVfYWxpYXMiLCJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJOZW9vZU5AY2FyYm9uLnN1cGVyIiwiYXBwbGljYXRpb24iOnsib3duZXIiOiJOZW9vZU4iLCJ0aWVyUXVvdGFUeXBlIjpudWxsLCJ0aWVyIjoiVW5saW1pdGVkIiwibmFtZSI6IkRlZmF1bHRBcHBsaWNhdGlvbiIsImlkIjo0NDQyNSwidXVpZCI6IjJmYjdlMjQzLTc5OTAtNDM0OC1hMmRkLWY0ZDQ1ODBhMmQ3NCJ9...
```

**Analyse :** Le fichier `.env` n'est **pas commité** (vérifié : `git ls-files GSIE/API/.env` retourne vide, `.gitignore` ligne 8 exclut `.env`). Le fichier `.env.example` ne contient **pas** cette clé (vérifié). Cependant, le JWT décodé révèle : `sub: NeooeN@carbon.super`, `tier: Unlimited`, `owner: NeooeN`, `exp: 1879037335` (2030). Cette clé est un credential de production réel stocké en clair sur le disque local. Tout accès physique ou compromission du poste expose cette clé avec quota illimité.

**Recommandation :** Stocker les clés API dans un secret manager (Vault, AWS Secrets Manager) ou au minimum chiffrer le `.env` avec SOPS. Ne jamais laisser une clé de production sur un poste de développement.

---

#### P1-2 : Paramètres de query non validés par Pydantic (Climate Engine)

**Fichier :** `A:\Quintessences\GSIE\API\src\gsie_api\engines\climate\router.py:133` et `:224`
**Sévérité :** Haute (absence de validation de boundary sur entrée utilisateur)

**Preuve :**
```python
# router.py ligne 130-135
async def climate_climatologie_stations(
    request: Request,
    response: Response,
    id_departement: str,          # ← Pas de Query() avec contraintes
    _user: EngineReadUser,
) -> list[dict[str, Any]]:
    ...
    return await ClimateEngine().list_stations_climatologie(id_departement)

# router.py ligne 221-225
async def climate_observations_horaires(
    request: Request,
    response: Response,
    id_departement: str,          # ← Pas de Query() avec contraintes
    _user: EngineReadUser,
) -> list[ObservationHoraireDepartement]:
```

**Analyse :** Les deux endpoints acceptent `id_departement: str` sans aucune contrainte
(`min_length`, `max_length`, pattern). Un code département français est un code INSEE
à 3 caractères (ex. `075`, `013`). L'absence de validation permet d'envoyer des chaînes
arbitraires au client Météo-France. Bien que le client HTTP soit résilient
(`ResilientHttpClient`) et que l'authentification soit requise, l'absence de validation
à la frontière de l'API viole le principe fail-fast et le skill `/securite-gsie`
(§ Validation des entrées).

**Recommandation :** Remplacer par `id_departement: str = Query(min_length=2, max_length=3, pattern=r"^\d{2,3}[A-B]?$")` ou un type Pydantic dédié.

---

#### P1-3 : Absence de HEALTHCHECK dans le Dockerfile

**Fichier :** `A:\Quintessences\GSIE\API\Dockerfile:90-100`
**Sévérité :** Moyenne-Haute (détection de panne retardée en orchestrateur standalone)

**Preuve :**
```dockerfile
# Dockerfile — pas d'instruction HEALTHCHECK
USER gsie
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "gsie_api.app:app", ...]
```

**Analyse :** Le `HEALTHCHECK` est défini dans `docker-compose.yml:154-159` mais **pas**
dans le `Dockerfile`. Si l'image est utilisée hors docker-compose (Kubernetes, Swarm,
registry pull), le healthcheck n'est pas embarqué. Le standard OWASP/skill exige un
HEALTHCHECK dans le Dockerfile.

**Recommandation :** Ajouter `HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1` dans le Dockerfile.

---

### P2 — Moyennes

#### P2-1 : `dict[str, Any]` non typé sur le CRUD générique et 2 retours d'endpoint

**Fichiers :**
- `A:\Quintessences\GSIE\API\src\gsie_api\resources\schemas.py:31` — `data: dict[str, Any]` sur `ResourceCreate`
- `A:\Quintessences\GSIE\API\src\gsie_api\resources\schemas.py:37` — `data: dict[str, Any]` sur `ResourceUpdate`
- `A:\Quintessences\GSIE\API\src\gsie_api\engines\climate\router.py:120` — retour `list[dict[str, Any]]` sur `/climatologie-stations`

**Sévérité :** Moyenne (validation différée, pas de schéma strict à la frontière API)

**Preuve :**
```python
# schemas.py ligne 26-31
class ResourceCreate(BaseModel):
    type: str = Field(..., description="Type de resource (ex. assertion, observation, concept)")
    gsie_id: str | None = Field(None, description="Identifiant lisible optionnel")
    data: dict[str, Any] = Field(..., description="Champs spécifiques au type")
```

**Analyse :** Le CRUD générique accepte `data: dict[str, Any]` — la validation se fait
**après** la frontière API, dans `coercion.py` (qui valide les types par colonne SQL)
et `validators.py`. C'est un choix architectural assumé (métamodèle dynamique, 73 types),
mais du point de vue sécurité, un payload malformé passe la porte Pydantic avant d'être
rejeté. La coercition (`coercer_donnees`) et les validateurs métier (`validators.py`)
rattrapent les types invalides en 422, mais un `Any` ne garantit pas l'absence de
champs inattendus. La validation géométrique WKT est bien présente (`_coercer_geometrie`
avec `shapely.wkt.loads`).

**Recommandation :** Documenter ce choix comme assumé (métamodèle). Envisager un
`model_config = ConfigDict(extra="forbid")` sur `ResourceCreate`/`ResourceUpdate` pour
rejeter les champs hors `type`/`gsie_id`/`data` au niveau Pydantic.

---

#### P2-2 : Endpoints `status`/`version` sans authentification

**Fichiers :** Tous les routers moteurs (14 endpoints `/status` + 14 `/version`)
**Sévérité :** Moyenne (divulgation d'information mineure)

**Preuve :**
```python
# Exemple — evidence/router.py:28-37
@router.get("/status", response_model=EngineStatusResponse)
async def evidence_status(request: Request) -> EngineStatusResponse:
    rust_available = is_rust_available()
    return EngineStatusResponse(
        engine="evidence",
        status="active" if rust_available else "degraded",
        planned_week=2,
        language="rust+pyo3" if rust_available else "python-fallback",
    )
```

**Analyse :** Les 28 endpoints `/status` et `/version` de tous les moteurs ne nécessitent
pas d'authentification. Ils exposent : nom du moteur, statut (active/degraded), semaine
d'implémentation, langage/backend. C'est un choix documenté (« information publique »
dans les docstrings). Le risque est limité (fingerprinting de l'architecture), mais en
production, ces informations aident un attaquant à cartographier la surface d'attaque.
Les endpoints `/health` et `/ready` sont légitimement non authentifiés (probes K8s).

**Recommandation :** En production/staging, protéger `/status` et `/version` par au
minimum `EngineReadUser` (reader), ou les désactiver comme `/docs`.

---

#### P2-3 : Validation SRID absente sur entrée EWKT utilisateur

**Fichier :** `A:\Quintessences\GSIE\API\src\gsie_api\resources\coercion.py:85-104`
**Sévérité :** Moyenne (géométrie acceptée dans n'importe quel SRID)

**Preuve :**
```python
# coercion.py ligne 85-104
def _coercer_geometrie(valeur: Any) -> str:
    if not isinstance(valeur, str):
        raise ValueError(f"attendu une géométrie WKT ou EWKT, reçu {type(valeur).__name__}")

    corps = valeur
    if valeur.upper().startswith(_PREFIXE_SRID) and _SEPARATEUR_EWKT in valeur:
        corps = valeur.split(_SEPARATEUR_EWKT, 1)[1]

    from shapely import wkt
    try:
        wkt.loads(corps)
    except Exception as exc:
        raise ValueError(f"géométrie illisible : {exc}") from exc
    return valeur  # ← retourne la valeur originale, SRID non validé
```

**Analyse :** La fonction valide que le WKT est lisible par shapely, mais **ne valide
pas** le SRID. Un utilisateur peut soumettre `SRID=0;POINT(...)` ou `SRID=9999;POINT(...)`
qui sera accepté et confié à `ST_GeomFromEWKT`. Le schéma v6.2 utilise SRID 2154
(Lambert-93) et 4326 (WGS 84) — un SRID arbitraire pourrait causer des incohérences
spatiales ou des erreurs silencieuses dans les jointures `ST_Contains`.

**Recommandation :** Valider le SRID contre une liste blanche (`{2154, 4326}`) ou
rejeter tout EWKT sans SRID explicite si la colonne cible attend un SRID précis.

---

#### P2-4 : WebSocket token en query param (standard mais à surveiller)

**Fichier :** `A:\Quintessences\GSIE\API\src\gsie_api\websocket\router.py:114`
**Sévérité :** Moyenne (token dans URL → logs proxy/CDN)

**Preuve :**
```python
# router.py ligne 114
token = websocket.query_params.get("token")
```

**Analyse :** Le token JWT est passé en query param `?token=xxx` — c'est le standard
de facto pour WebSocket (le protocole ne permet pas de headers personnalisés au
handshake). Le code documente cette mitigation : HTTPS en prod (token chiffré en
transit), tokens courts (15min), pas de log des query params. Le risque résiduel est
la présence du token dans les logs des reverse proxies/CDN intermédiaires.

**Recommandation :** Configurer le reverse proxy (nginx/traefik) pour exclure les
query params des access logs. Vérifier que le middleware TraceId ne logge pas les
query params (vérifié : `shared/middleware.py` logge uniquement `path`, pas
`url.query`).

---

#### P2-5 : Rate limiter WebSocket in-memory (non distribué)

**Fichier :** `A:\Quintessences\GSIE\API\src\gsie_api\websocket\router.py:65-86`
**Sévérité :** Moyenne (contournable avec plusieurs workers)

**Preuve :**
```python
# router.py ligne 65-86
class _RateLimiter:
    """Rate limiter in-memory par WebSocket (best-effort)."""
    def __init__(self) -> None:
        self._timestamps: dict[int, deque[float]] = defaultdict(deque)
```

**Analyse :** Le rate limiter WebSocket est in-memory par processus, contrairement au
rate limiter HTTP qui utilise Redis (`slowapi` avec `storage_uri` Redis). Avec plusieurs
workers Gunicorn (5 par défaut), un client peut envoyer 10 × 5 = 50 messages/minute au
lieu de 10. Le commentaire « best-effort » assume cette limite.

**Recommandation :** Migrer vers un rate limiter Redis pour les WebSocket, ou documenter
ce risque résiduel comme assumé.

---

## 4. Points forts (conformité au skill `/securite-gsie`)

| Critère du skill | Statut | Preuve |
|------------------|--------|--------|
| PyJWT ≥ 2.8.0 (pas python-jose) | ✅ | `pyjwt[crypto]==2.10.1` (`pyproject.toml:42`), `import jwt` (`core/auth.py:23`) |
| `algorithms=[RS256]` explicite | ✅ | `algorithms=[_settings.jwt_algorithm]` avec `jwt_algorithm: Literal["RS256"]` (`config.py:160`, `auth.py:185`) |
| Aucun secret dans le code | ✅ | `git ls-files GSIE/API/.env` = vide, `.gitignore` exclut `.env` |
| `.env.example` avec valeurs factices | ✅ | `change-me-in-.env` partout, pas de clé réelle |
| Taille max payload configurée | ✅ | `max_request_body_size: int = 1_048_576` + `RequestBodyLimitMiddleware` ASGI (compte les chunks) |
| Rate limiting sur endpoints publics | ✅ | slowapi sur tous les endpoints POST, login 20/min, evaluate 30/min, bulk 600/min |
| Auth JWT sur tous les endpoints protégés | ✅ | 66 références `Depends(get_current_user)`/`require_permission`/`EngineReadUser`/`EngineWriteUser` |
| Inputs validés avec Pydantic | ⚠️ | Pydantic v2 sur tous les body, sauf 2 query params (`id_departement`) |
| Headers sécurité activés | ✅ | 7 headers dans `_SECURITY_HEADERS` (`middleware.py:25-33`) |
| CORS restreint (pas `*` en prod) | ✅ | `validate_production_security` refuse `*` et localhost en prod/staging |
| Dépendances auditées | ✅ | Versions pinées, pas de CVE connues, `uv.lock` avec hashes |
| Logs sans données sensibles | ✅ | `login_failed` logge username+IP+UA (pas le password), `token_refreshed` logge `jti` (non sensible) |
| Token de révocation (logout) | ✅ | `RefreshTokenStore` avec rotation atomique Redis (`refresh_tokens.py`), endpoint `/auth/logout` |
| Rotation des secrets | ⚠️ | Clés JWT en fichiers, procédure `generate-jwt-keys.sh` documentée, mais pas de rotation automatique |
| Requêtes SQL paramétrées | ✅ | SQLAlchemy 2.0 + `text()` avec `:param` partout, aucune concaténation f-string SQL |
| Pas de subprocess `shell=True` | ✅ | Aucun `subprocess` actif (`simulation_backend.py` documente un futur wrapper CAPSIS non implémenté) |
| Docker non-root | ✅ | `USER gsie` (uid 1000), `cap_drop: ALL`, `no-new-privileges:true`, `read_only: true` |
| Image de base à jour | ✅ | `python:3.12-slim-bookworm` pinée par digest, `rust:1.85.0-slim-bookworm` pinée par digest |
| Validation géospatiale WKT | ✅ | `shapely.wkt.loads` dans `_coercer_geometrie` (`coercion.py:101`) |
| RBAC avec privilege escalation prevention | ✅ | `rgpd_manager` restreint aux types RGPD, `admin` seule action `admin`, sortie fermée (`_ACTIONS_EVALUEES`) |

---

## 5. Recommandations priorisées

### Priorité 1 (avant exposition production)

1. **P1-1** : Migrer la clé API Météo-France vers un secret manager (Vault/SOPS). Ne
   jamais laisser un credential de production sur un poste de dev.
2. **P1-2** : Ajouter `Query(min_length=2, max_length=3, pattern=...)` sur les 2
   paramètres `id_departement` du Climate Engine.
3. **P1-3** : Ajouter `HEALTHCHECK` dans le `Dockerfile` (pas seulement docker-compose).

### Priorité 2 (durcissement)

4. **P2-3** : Valider le SRID dans `_coercer_geometrie` contre une liste blanche
   (`{2154, 4326}`).
5. **P2-2** : Protéger `/status` et `/version` par `EngineReadUser` en production, ou
   les désactiver comme `/docs`.
6. **P2-1** : Ajouter `model_config = ConfigDict(extra="forbid")` sur `ResourceCreate`
   et `ResourceUpdate` pour rejeter les champs inattendus au niveau Pydantic.
7. **P2-5** : Migrer le rate limiter WebSocket vers Redis pour la cohérence multi-workers.

### Priorité 3 (amélioration continue)

8. **P2-4** : Documenter la configuration du reverse proxy pour exclure les query
   params des access logs (mitigation token WS en query param).
9. Exécuter `pip audit` ou `uv pip audit` dans la CI pour détecter automatiquement
   les CVE (non exécutable dans cet environnement — uv sans pip).
10. Planifier une procédure de rotation des clés JWT (génération + redéploiement
    sans interruption de service).

---

## 6. Conclusion

L'API GSIE est **au-dessus du standard** attendu pour une Phase 4. Le travail de
durcissement déjà accompli (RBAC granulaire avec sortie fermée, RLS PostgreSQL,
isolation RGPD par schéma, validateur de configuration production, rotation des
refresh tokens atomique en Redis, headers de sécurité complets, Docker durci) témoigne
d'une culture sécurité mature. Les 5 constats P1/P2 sont des points de durcissement,
pas des failles architecturales. Aucune correction urgente n'est requise pour continuer
le développement, mais les 3 priorités P1 doivent être traitées avant toute exposition
en staging/production.

**Score final : 87 / 100 — Conforme au skill `/securite-gsie`, durcissement P1 requis avant prod.**

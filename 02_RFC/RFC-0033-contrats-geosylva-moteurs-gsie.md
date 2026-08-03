# RFC-0033 — Contrats d'interface GeoSylva ↔ moteurs GSIE

| Champ | Valeur |
|---|---|
| **ID** | RFC-0033 |
| **Statut** | Proposé |
| **Auteur** | Direction technique (assistée par Devin CLI, GLM-5.2 High) |
| **Date** | 2026-08-03 |
| **Décision liée** | À valider par DEC (Phase P4) |
| **Périmètre** | Connexion canal 1 GeoSylva mobile ↔ moteurs GSIE serveur |
| **Motivation** | Spécifier les contrats d'interface opérationnels entre l'app mobile et les moteurs GSIE pour permettre l'implémentation de la Phase P4 |

## 1. Problème

GeoSylva 3.0 (GEOSYLVA-003 §14) délègue aux moteurs GSIE via le canal 1
l'analyse approfondie, le diagnostic, la recommandation et la simulation.
Les contrats d'interface des moteurs (`GSIE/ENGINES/*/`) définissent les
formats *moteur à moteur*, mais pas le contrat *application cliente → API
GSIE → moteurs*. GeoSylva a aujourd'hui deux endpoints directs (Identity,
Sync parcelles) consommés via Retrofit, mais aucun canal pour invoquer
Correlation, Reasoning, Diagnostic, Recommendation, Forest Dynamics ou
Simulation.

Sans contrat explicite, chaque intégration serait ad hoc, non traçable,
et violerait ADR-009 (provenance obligatoire) et GSIE-CON-005 (traçabilité).

## 2. Solution proposée

### 2.1 Architecture

GeoSylva consomme les moteurs via l'API GSIE (FastAPI, JWT RS256), pas en
direct. L'API GSIE expose un endpoint unifié par moteur, accepte
l'enveloppe commune (§2.2), route vers le moteur, et renvoie l'enveloppe
commune de réponse (§2.3). Le SDK Kotlin (§2.6) encapsule ce contrat.

```text
GeoSylva mobile
    │  (HTTPS, JWT RS256, certificate pinning)
    ▼
API GSIE (FastAPI)
    │  (routage interne, auth, RLS, rate limit)
    ▼
Moteur GSIE (Correlation, Reasoning, Diagnostic, ...)
    │  (exécution, persistance si applicable)
    ▼
API GSIE
    │  (enveloppe réponse + source_reference)
    ▼
GeoSylva mobile (cache SQLCipher)
```

### 2.2 Enveloppe commune de requête

Toute requête GeoSylva → API GSIE → moteur porte :

```json
{
  "requete_id": "uuid-v4",
  "session_id": "uuid-v4",
  "auteur": "user_account_uuid",
  "device_id": "sha256(android_id)",
  "source": "manual | sync | gps",
  "version": 1,
  "moteur_cible": "correlation | reasoning | diagnostic | recommendation | forest_dynamics | simulation | botanical | learning",
  "payload": { "...": "spécifique au moteur" },
  "cache_hint": "string optionnel"
}
```

**Champs obligatoires** : `requete_id`, `session_id`, `auteur`,
`moteur_cible`, `payload`.

**Idempotence** : `requete_id` est la clé d'idempotence. Deux requêtes
avec le même `requete_id` renvoient le même `resultat_id` sans réexécuter
le moteur (sauf si le résultat a expiré du cache serveur).

**Version** : `version` est la version des données envoyées (optimistic
locking). Le serveur compare avec sa version courante ; si la version
diffère, il renvoie 409 Conflict avec sa version.

### 2.3 Enveloppe commune de réponse

```json
{
  "resultat_id": "uuid-v5",
  "requete_origine": "uuid-v4 reflète requete_id",
  "moteur_version": "correlation-engine@1.3.0",
  "source_reference": {
    "type_source": "referentiel_officiel | publication | observation_terrain | api",
    "reference": "string (URL, DOI, ou identifiant interne)",
    "version": "string",
    "date": "ISO 8601"
  },
  "evidence_level": "A | B | C | D | E | F",
  "incertitude": 0.12,
  "chaine_inference": [
    {
      "ordre": 1,
      "regle_appliquee": "string",
      "source_regle": { "...": "SourceReference" },
      "premisses": ["string"],
      "conclusion_locale": "string"
    }
  ],
  "date_calcul": "ISO 8601",
  "payload": { "...": "spécifique au moteur" },
  "cache_ttl": 3600
}
```

**Champs obligatoires** : `resultat_id`, `requete_origine`,
`moteur_version`, `source_reference`, `evidence_level`, `date_calcul`,
`payload`.

**Garde-fou ADR-009** : une réponse sans `source_reference` est un défaut
bloquant. L'API GSIE rejette toute réponse moteur non conforme.

### 2.4 Endpoints par moteur

| Moteur | Méthode | Endpoint | Payload entrée | Payload sortie |
|---|---|---|---|---|
| Correlation | POST | `/api/v1/engines/correlation/analyze` | `CorrelationRequest` | `CorrelationMatrix` |
| Reasoning | POST | `/api/v1/engines/reasoning/infer` | `ReasoningRequest` | `InferenceResult` |
| Diagnostic | POST | `/api/v1/engines/diagnostic/diagnose` | `DiagnosticRequest` | `Diagnostic` |
| Recommendation | POST | `/api/v1/engines/recommendation/recommend` | `RecommendationRequest` | `RecommendationSet` |
| Forest Dynamics | POST | `/api/v1/engines/forest-dynamics/project` | `DynamicsRequest` | `DynamicsProjection` |
| Simulation | POST | `/api/v1/engines/simulation/run` | `ScenarioSimulation` | `SimulationResult` |
| Botanical | POST | `/api/v1/engines/botanical/query` | `BotanicalQuery` | `BotanicalData` |
| Learning | POST | `/api/v1/engines/learning/signal` | `LearningSignal` | `LearningOutput` |

**Authentification** : JWT RS256 (Bearer token), refresh automatique côté
SDK. RLS PostgreSQL isole par `auteur` (compte Quintessences).

**Rate limit** : 60 requêtes/min par compte, 10 requêtes/min par moteur
lourd (Diagnostic, Recommendation, Simulation). Retry exponentiel côté
SDK (15s → 1h).

### 2.5 Chaîne d'analyse approfondie

L'analyse GSIE approfondie post-martelage enchaîne les moteurs. GeoSylva
n'appelle pas chaque moteur individuellement — elle appelle un endpoint
d'orchestration qui exécute la chaîne et renvoie le résultat consolidé :

| Endpoint | Rôle |
|---|---|
| `POST /api/v1/engines/orchestrate/analyze` | Chaîne Correlation → Reasoning → Diagnostic, renvoie `Diagnostic` + `InferenceResult` |
| `POST /api/v1/engines/orchestrate/recommend` | Chaîne Diagnostic → Recommendation → Simulation (optionnel), renvoie `RecommendationSet` + `SimulationResult` |

L'orchestrateur préserve les `resultat_id` intermédiaires pour traçabilité.
GeoSylva peut aussi appeler chaque moteur individuellement (mode
développeur, §10) pour debug ou ré-exécution.

### 2.6 SDK Kotlin

Le SDK Kotlin (`GSIE/SDK/kotlin/`) encapsule :

- Authentification JWT (refresh automatique, réutilisation du pattern
  `IdentityRepositoryImpl`).
- Sérialisation kotlinx.serialization alignée sur le métamodèle GSIE v6.2.
- Enveloppes communes (§2.2, §2.3) avec validation à la compilation.
- Cache local SQLCipher avec expiration et détection d'obsolescence.
- File d'attente `EN_ATTENTE_AMPLIFICATION` (WorkManager, retry
  exponentiel).
- Gestion d'erreurs : 401 (refresh), 409 (conflit), 429 (rate limit),
  5xx (retry), autre (permanent).

**Statut** : non implémenté. Livrable Phase P4. En attendant, GeoSylva
utilise Retrofit directement (pattern Factory existant).

### 2.7 Cache local

Table Room `gsie_cache` (SQLCipher, migration à spécifier) :

```sql
CREATE TABLE gsie_cache (
  requete_id TEXT PRIMARY KEY,
  moteur_cible TEXT NOT NULL,
  payload TEXT NOT NULL,          -- JSON chiffré
  moteur_version TEXT NOT NULL,
  date_calcul INTEGER NOT NULL,
  cache_ttl INTEGER NOT NULL,
  source_reference TEXT NOT NULL,  -- JSON
  evidence_level TEXT NOT NULL,
  chaine_inference TEXT,            -- JSON, optionnel
  statut TEXT NOT NULL DEFAULT 'SYNCED'  -- SYNCED | EN_ATTENTE | OBSOLETE
);
```

**Règles** :

- À l'affichage, badge « amplification GSIE (version X, date Y) ».
- Si `moteur_version` < dernière version connue → badge « obsolète » +
  proposition de ré-exécution.
- Appel échoué → `statut = EN_ATTENTE`, retry WorkManager.
- Ré-exécution manuelle (mode développeur) → compare cache vs nouvelle
  exécution, conserve les deux.

### 2.8 Pull serveur → mobile

| Endpoint | Rôle |
|---|---|
| `GET /api/v1/sync/geosylva/resources/{client_id}?since={timestamp}&type={diagnostic,recommendation,...}` | Récupère les ressources modifiées depuis `timestamp`, paginé (cursor-based, RFC-0031 Phase 2) |

Chaque ressource renvoyée porte son `version`. Si la version locale est
identique → ignorée. Si locale plus récente → 409, résolution explicite.

### 2.9 Résolution de conflits

Écran `ConflictResolutionScreen` (Phase P4) :

- Affichage côte à côte version locale / version serveur.
- Choix : garder local, garder serveur, fusionner manuellement.
- Décision tracée (auteur, date, choix, justification optionnelle).
- Aucune fusion automatique silencieuse (§8 GEOSYLVA-003).

## 3. Garde-fous

- **ADR-009** : toute réponse moteur expose `source_reference` +
  `evidence_level`. Défaut bloquant sinon.
- **GSIE-CON-001** : toute recommandation est `contournable: vrai`.
- **GSIE-CON-004** : toute conclusion expose `chaine_inference`.
- **GSIE-CON-005** : `requete_id` + `resultat_id` tracés dans la session
  de martelage.
- **Offline-first** : un appel échoué → `EN_ATTENTE_AMPLIFICATION`, pas
  d'erreur bloquante. Le cœur forestier continue.
- **Pas de LLM sans moteur** : le LLM T3 (RFC-0034) invoque toujours un
  moteur pour produire une valeur numérique forestière.

## 4. Migration et impact

- **API GSIE** : ajout de 8 endpoints moteurs + 2 endpoints
  orchestration + 1 endpoint pull. Pas de breaking change (endpoints
  nouveaux).
- **GeoSylva** : nouvelle table Room `gsie_cache` (migration v34→v35),
  nouveau SDK Kotlin, nouvel écran `ConflictResolutionScreen`.
- **Tests** : mock serveur GSIE (MockWebServer) pour tests E2E, tests
  contractuels par endpoint (schéma + garde-fous ADR-009).

## 5. Alternatives envisagées

| Alternative | Pourquoi rejetée |
|---|---|
| Appels moteurs en direct (sans API GSIE) | Violente l'architecture clean, pas d'auth/RLS/rate limit centralisé |
| WebSocket pour tous les moteurs | Seuls Correlation/Diagnostic sont synchrones courts ; Simulation est long → async. WebSocket ajouté pour temps réel Hub, pas pour moteurs |
| GraphQL | Sur-ingénierie pour 8 endpoints ; REST + enveloppe commune suffit |
| Pas de cache local | Violente offline-first ; un appel échoué bloquerait le parcours |

## 6. Statut et validation

- **Statut** : Proposé. À valider par le Fondateur.
- **Décision requise** : DEC (Phase P4) pour activer l'implémentation.
- **Dépendances** : P0 (corrections audits) + P3 (moteurs scientifiques
  locaux) terminés. SDK Kotlin peut démarrer en parallèle.

## 7. Références

- `GEOSYLVA_3_SPECIFICATION_FONCTIONNELLE.md` §14 (connexion GSIE Serveur)
- `GSIE/ENGINES/*/` (contrats d'interface des 14 moteurs)
- `GSIE/ARCHITECTURE/ENGINE_INTERFACE_CONTRACTS.md` (matrice d'interactions)
- `GSIE/ARCHITECTURE/ADR-009-garde-fou-anti-invention.md`
- `02_RFC/RFC-0003.md` (GSIE-Net, architecture distribuée)
- `02_RFC/RFC-0032-identite-quintessences-multi-fournisseurs.md` (auth JWT)
- `03_DECISIONS/DEC-000048.md` (sync parcelles, pattern de base)
- `GSIE/API/README.md` (API FastAPI, métamodèle v6.2)

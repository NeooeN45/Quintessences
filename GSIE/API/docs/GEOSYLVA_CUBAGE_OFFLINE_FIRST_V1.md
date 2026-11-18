# Contrat API V1 — Cubage offline-first GeoSylva–GSIE

**Statut :** aligné sur RFC-0042  
**Date :** 2026-08-31  
**Public :** client GeoSylva authentifié et BFF GSIE

## Principe

GeoSylva calcule le cubage localement. L’API GSIE ne reçoit pas seulement un nombre : elle reçoit la session, les mesures, le calcul, la méthode, les paramètres, les contrôles et les références ayant servi au calcul.

Le calcul local reste consultable sans réseau. La synchronisation est une opération séparée et répétable. GSIE peut accepter le résultat, demander une revue ou fournir une vérification serveur, mais ne modifie jamais silencieusement le résultat local.

## Ressources

### Session de cubage

```text
POST /api/v1/geosylva/cubage/sessions/sync
GET  /api/v1/geosylva/cubage/sessions/{session_id}
```

La création et la synchronisation utilisent :

- `Authorization: Bearer <access_token>` ;
- `Idempotency-Key: <uuid>` ;
- `Content-Type: application/json` ;
- un corps conforme à `geosylva.cubage.sync.request.v1`.

La synchronisation retourne :

```json
{
  "session_id": "uuid",
  "calculation_id": "uuid",
  "status": "accepted|synced|review_required|rejected|retryable_error",
  "server_record_id": "uuid|null",
  "server_verification_id": "uuid|null",
  "retry_after_seconds": 30,
  "warnings": [],
  "trace_id": "string",
  "schema_version": "geosylva.cubage.sync.response.v1"
}
```

Les réponses `accepted`, `synced` et `review_required` ne signifient pas la même chose :

- `accepted` : le paquet a été reçu et va être traité ;
- `synced` : le paquet est enregistré et les contrôles contractuels sont passés ;
- `review_required` : il est conservé, mais une validation humaine ou scientifique est nécessaire ;
- `rejected` : le paquet ne peut pas être enregistré comme résultat exploitable ;
- `retryable_error` : la session reste locale et pourra être renvoyée.

## Requête de synchronisation

```json
{
  "schema_version": "geosylva.cubage.sync.request.v1",
  "session": {
    "session_id": "uuid",
    "owner_account_id": "uuid",
    "station_id": "string|null",
    "geometry": {
      "type": "Point|Polygon|MultiPolygon",
      "coordinates": []
    },
    "purpose": "inventory|martelage|commercial|other",
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601",
    "revision": 4,
    "sync_state": "LOCAL_CALCULATED",
    "session_fingerprint": "sha256"
  },
  "measurements": {
    "items": [],
    "canonical_units": "SI",
    "measurements_fingerprint": "sha256"
  },
  "calculation": {
    "calculation_id": "uuid",
    "engine": "geosylva.cubage",
    "engine_version": "semver",
    "method_id": "string",
    "method_version": "semver",
    "parameters": {},
    "results": {},
    "units": {},
    "quality": {
      "status": "valid|warning|blocked",
      "warnings": [],
      "uncertainty": {}
    },
    "basis": [],
    "inputs_fingerprint": "sha256",
    "result_fingerprint": "sha256",
    "calculated_at": "ISO-8601"
  },
  "client": {
    "application_id": "geosylva",
    "application_version": "semver",
    "os_version": "string",
    "locale": "fr-FR"
  }
}
```

Le serveur déduit le compte à partir du jeton. `owner_account_id` est contrôlé et ne peut pas être utilisé pour transférer une session à un autre compte.

## Idempotence

Une répétition avec la même clé et le même contenu retourne la même ressource logique. Une répétition avec la même clé et un contenu différent retourne `409 Conflict`.

La clé d’idempotence doit être conservée localement jusqu’à la réception d’un état définitif. Une session en erreur réseau ne doit pas être recréée avec un nouvel identifiant sans raison explicite.

## Vérification serveur

La vérification GSIE est un objet distinct du résultat local :

```json
{
  "verification_id": "uuid",
  "source_calculation_id": "uuid",
  "status": "not_run|consistent|divergent|not_comparable|blocked",
  "server_engine": "string|null",
  "server_engine_version": "semver|null",
  "method_id": "string|null",
  "method_version": "semver|null",
  "results": {},
  "differences": [],
  "warnings": [],
  "evidence": [],
  "verified_at": "ISO-8601|null"
}
```

Une divergence entre le calcul local et la vérification serveur est conservée, expliquée et visible dans la synthèse. Elle ne déclenche pas un remplacement automatique.

## Erreurs attendues

| HTTP | Cas | Comportement GeoSylva |
|---:|---|---|
| 400 | JSON ou version de schéma invalide | conserver la session, signaler l’erreur corrigeable |
| 401 | jeton absent ou expiré | renouveler via le flux d’identité, puis réessayer une fois |
| 403 | session appartenant à un autre compte | arrêter la synchronisation et journaliser sans données sensibles |
| 409 | conflit d’idempotence | ne pas écraser ; afficher le conflit |
| 413 | paquet trop volumineux | conserver localement et demander une réduction contrôlée |
| 422 | mesure ou méthode non admissible | conserver le résultat local comme bloqué ou à revoir |
| 429 | quota atteint | respecter `Retry-After` |
| 5xx | indisponibilité GSIE | retry borné, puis retour à l’état local |

## Règles de stockage mobile

GeoSylva doit stocker séparément :

- le brouillon courant ;
- les mesures brutes ;
- chaque révision ;
- le calcul local ;
- la file de synchronisation ;
- l’accusé GSIE ;
- la vérification serveur ;
- les erreurs de synchronisation.

Les tokens restent dans le stockage sécurisé existant. Les journaux ne contiennent ni token, ni géométrie complète, ni donnée personnelle inutile.

## Compatibilité future

Le contrat est extensible par version de schéma. Une nouvelle méthode de cubage ajoute un identifiant et une version ; elle ne change pas l’interprétation des anciens calculs.

Le contrat de cubage offline-first ne rend pas automatiquement hors ligne la bibliothèque Forge ni les autres moteurs GSIE. Une synthèse nécessitant des ressources non présentes sur l’app reste une analyse serveur, avec un statut explicite.


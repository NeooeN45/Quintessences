# RFC-0042 — Contrat offline-first du cubage GeoSylva–GSIE

**Statut :** Review  
**Date :** 2026-08-31  
**Périmètre :** GeoSylva Android, BFF GSIE, sessions de cubage, synchronisation scientifique

## Résumé

GeoSylva doit pouvoir réaliser le cubage sans connexion réseau. Le calcul est exécuté dans l’application à partir d’un moteur local versionné, puis conservé dans une session de cubage avec ses mesures, sa méthode, ses paramètres, ses contrôles et ses bases documentaires.

Lorsque la connexion est disponible, GeoSylva transmet à GSIE la session et le résultat local. GSIE authentifie l’utilisateur, vérifie l’intégrité, contrôle le contrat et la compatibilité de la méthode, enregistre la version reçue et peut produire une vérification serveur. Cette vérification ne remplace pas silencieusement le résultat local affiché comme résultat du terrain.

Le calcul local est donc obligatoire pour le cubage GeoSylva. Le serveur est responsable de la traçabilité centralisée, de la validation scientifique complémentaire, de la synchronisation, de la recherche et de l’intégration avec les autres données GSIE.

## Décision de responsabilité

| Responsabilité | GeoSylva | GSIE |
|---|---:|---:|
| Saisie et correction des mesures | Oui | Non |
| Contrôles immédiats de saisie | Oui | Contrôle complémentaire |
| Calcul du cubage en mode hors ligne | Oui, obligatoire | Non requis |
| Conservation du brouillon et du résultat local | Oui | Non |
| Conservation canonique distante | Après synchronisation | Oui |
| Vérification de l’intégrité et du contrat | Pré-contrôle | Oui |
| Vérification scientifique complémentaire | Optionnelle | Oui |
| Publication dans la bibliothèque GSIE | Non | Oui |
| Synthèse enrichie par les ressources serveur | Non hors ligne | Oui après synchronisation |

GSIE ne doit jamais prétendre qu’un calcul a été exécuté par le serveur si le calcul original a été exécuté par GeoSylva. Les deux origines doivent être distinguées dans le résultat.

## Modèle de session

Une session de cubage est un agrégat local et distant identifié par un `session_id` stable. Elle contient au minimum :

- l’utilisateur et le contexte autorisé ;
- la parcelle, la géométrie et le système de coordonnées ;
- les arbres, grumes ou lots mesurés ;
- les unités d’affichage et les unités canoniques ;
- les mesures brutes, sans écrasement destructif ;
- les corrections et l’historique des modifications ;
- l’objectif du cubage ;
- la méthode de calcul et sa version ;
- les paramètres et coefficients utilisés ;
- la documentation ou le profil scientifique de référence ;
- les contrôles effectués et leurs avertissements ;
- le résultat local et son empreinte ;
- l’état de synchronisation.

La session modifiable et le calcul validé sont deux objets distincts. Toute modification d’une mesure produit une nouvelle version du calcul.

États de synchronisation :

```text
LOCAL_DRAFT
  → LOCAL_CALCULATED
  → QUEUED_FOR_SYNC
  → SYNCING
  → SYNCED
  → SERVER_REVIEW_REQUIRED
  → SYNC_FAILED_RETRYABLE
  → SYNC_FAILED_FINAL
```

Une panne réseau ne doit pas supprimer les mesures ni le résultat local. Les retries sont limités, idempotents et liés au cycle de vie de la session.

## Contrat de calcul local

Le moteur de cubage GeoSylva doit être déterministe pour une même version de méthode, un même jeu de mesures et les mêmes paramètres.

Chaque résultat local expose :

```json
{
  "calculation_id": "uuid",
  "session_id": "uuid",
  "engine": "geosylva.cubage",
  "engine_version": "semver",
  "method_id": "method.identifier",
  "method_version": "semver",
  "inputs_fingerprint": "sha256",
  "parameters": {},
  "measurements": {},
  "results": {},
  "units": {},
  "quality": {
    "status": "valid|warning|blocked",
    "warnings": [],
    "uncertainty": {}
  },
  "basis": [
    {
      "source_id": "string",
      "source_version": "string",
      "citation": "string",
      "role": "method|parameter|reference"
    }
  ],
  "calculated_at": "ISO-8601"
}
```

Les noms exacts des méthodes et paramètres seront ceux définis dans la documentation scientifique du cubage. Le contrat interdit les coefficients implicites, les unités non déclarées et les arrondis non documentés.

## Synchronisation vers GSIE

GeoSylva envoie la session et le calcul local par une opération idempotente. La requête doit contenir :

- `session_id` ;
- `calculation_id` ;
- `Idempotency-Key` ;
- version du contrat ;
- identité de l’utilisateur ;
- empreinte de la session ;
- empreinte des mesures ;
- empreinte du résultat ;
- moteur et version ;
- méthode et version ;
- résultat local ;
- preuves et références documentaires ;
- état des contrôles locaux ;
- version de l’application.

GSIE répond avec un état explicite :

```text
accepted
synced
review_required
rejected
retryable_error
```

Une même clé d’idempotence avec un contenu différent est une erreur de conflit. Une répétition avec le même contenu retourne le même accusé de réception.

## Vérification côté GSIE

GSIE vérifie notamment :

- propriété de la session ;
- validité du schéma ;
- intégrité des empreintes ;
- cohérence des unités ;
- compatibilité de la méthode ;
- présence des paramètres obligatoires ;
- plages de valeurs ;
- version de l’application et du moteur ;
- références documentaires ;
- absence de résultat prétendant provenir de GSIE alors qu’il est local.

Si une méthode est connue et que GSIE dispose de l’implémentation correspondante, il peut recalculer une vérification. Cette vérification est publiée comme une observation distincte :

```text
LOCAL_RESULT
SERVER_VERIFICATION
RECONCILIATION
```

Une divergence n’est jamais écrasée. Elle crée un avertissement ou une contradiction avec gravité, explication et impact sur la synthèse.

## Règles scientifiques

- Un résultat local peut être consulté hors ligne, mais il doit afficher son statut de validation.
- Un résultat `blocked` ne peut pas être présenté comme valide.
- Une recommandation sylvicole ne peut pas être déduite d’un résultat de cubage seul sans règles et preuves suffisantes.
- Une synthèse serveur doit distinguer calcul local, vérification serveur et conclusion GSIE.
- Toute conclusion doit référencer directement ses preuves.
- Toute évolution de formule ou de paramètre change la version de méthode et l’empreinte du résultat.
- Les anciennes versions restent lisibles et reproductibles.

## API GeoSylva

Le contrat mobile reste indépendant de l’implémentation interne de GSIE. Les opérations minimales sont :

- créer ou mettre à jour une session de cubage locale ;
- calculer localement ;
- mettre en file une session calculée ;
- synchroniser une session ;
- consulter l’accusé de réception ;
- récupérer la vérification et la synthèse enrichie ;
- reprendre ou abandonner une synchronisation.

Le résultat synchronisé peut être partiel. GeoSylva doit afficher les éléments déjà disponibles sans les confondre avec une validation complète.

## Migration

La migration de l’ancien backend de calcul suit quatre étapes :

1. Archiver l’ancien code et ses résultats de référence.
2. Transformer les méthodes documentées en cas de test déterministes.
3. Implémenter le moteur local GeoSylva derrière ce contrat.
4. Brancher la synchronisation GSIE sans dépendance à l’ancien backend.

La suppression définitive de l’ancien backend n’est autorisée qu’après validation des cas de référence, de la reprise de session et de la synchronisation idempotente.

## Critères d’acceptation

- Un cubage valide peut être réalisé sans réseau.
- Une session interrompue reprend sans perte de mesures.
- Le résultat local est reproductible avec la même méthode et les mêmes entrées.
- La synchronisation répétée ne crée pas de doublon.
- Une divergence locale/serveur est visible et traçable.
- Les unités, méthodes, paramètres et sources sont consultables.
- Les résultats bloqués ne sont pas publiés comme fiables.
- La page de synthèse distingue clairement calcul local, vérification GSIE et recommandation.
- Le contrat peut accueillir de nouvelles méthodes sans modifier les anciennes sessions.


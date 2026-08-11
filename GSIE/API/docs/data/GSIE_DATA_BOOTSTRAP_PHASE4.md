# Bootstrap Data Registry — Phase 4

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-DATA-BOOTSTRAP-0001 |
| **Statut** | Draft |
| **Version** | 1.0.0 |
| **Date** | 2026-08-10 |
| **Rattachement** | RFC-0038 v1.2.0 / DEC-000059 |

## Objet

Le bootstrap active explicitement les quatre façades fournisseurs prévues par
la Phase 3 : GBIF, IGN, SoilGrids et Météo-France. L'activation signifie que
leurs factories sont enregistrées dans `AdapterPluginRegistry`; elle ne
déclenche aucune connexion réseau au démarrage et ne promeut aucune donnée.

Le registre process-wide est obtenu par `get_adapter_registry()`. Les tests et
les jobs isolés utilisent `build_adapter_registry()` afin de ne pas partager
d'état d'instance.

## Contrôle de santé

`AdapterHealthService` exécute une campagne séquentielle dans l'ordre stable des
clés d'adapter. Le mode `offline=True` produit `unknown` avec le code
`OFFLINE_MODE` et n'ouvre aucun socket. Une exception fournisseur est ramenée
à `unavailable` avec `ADAPTER_HEALTH_CHECK_FAILED`; le détail de l'exception
n'est jamais exposé.

Ces rapports sont des résultats d'exécution fournisseur. Ils ne sont pas
automatiquement insérés dans `gsie_gouvernance.dataset_health` : cette table
est append-only et exige une `Distribution` et une `DatasetVersion` qualifiées.
La persistance sera ajoutée avec le job de santé périodique, après le bootstrap
du catalogue et l'association explicite source → distribution.

## Vérification

- quatre descripteurs sont présents et triés `gbif`, `ign`, `meteofrance`,
  `soilgrids` ;
- l'accès à un adapter est lazy et mis en cache par le registre ;
- la campagne offline retourne quatre rapports `unknown` sans réseau ;
- les tests ciblés adapters/bootstrap passent ; Ruff et mypy strict passent.

## Limites

Le bootstrap ne choisit pas de source, n'effectue pas de téléchargement, ne
contourne pas la porte juridique d'ingestion et ne remplace pas le Data
Selection Engine. La campagne online doit être déclenchée par un job ou une
action opérateur corrélée par un `trace_id`.

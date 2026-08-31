# Import persistant du bundle Forge dans GSIE TEST

## Positionnement

Le contrat `forge_analysis_bundle.v1` est validé avant l'import. Le point
d'entrée persistant est :

    POST /api/v1/data/analysis-bundles/import

Le corps est le bundle Forge lui-même. L'appel exige un JWT portant le rôle
`writer` ou `admin`, un profil présent dans
`GSIE_FORGE_ANALYSIS_BUNDLE_ALLOWED_PROFILES` et une base configurée avec
`database_role=test`.

## Persistance et idempotence

Le bundle est stocké dans la table existante `field_intake`, sans nouvelle
table par source ou par moteur :

- `application_key=forge-analysis-bundle-v1` ;
- `client_event_id=bundle_id` ;
- `kind=analysis_bundle` ;
- `status=quarantined` ;
- `target_resource_id=station_id` ;
- `payload.analysis_bundle` contient la représentation canonique ;
- `provenance.bundle_hash` reprend l'empreinte SHA-256 du bundle.

Le rejeu du même bundle renvoie `duplicate=true`. Le même `bundle_id` avec
une empreinte différente est refusé en `409`. La représentation canonique
rend le rejeu indépendant de l'ordre des listes de sources, paramètres et
features. Une course concurrente est arbitrée par la contrainte unique
existante et un savepoint transactionnel.

## Barrière de consommation

L'import ne crée ni `Place`, ni ressource canonique, ni appel fournisseur. Un
bundle reste en quarantaine et n'est pas consommé par l'hydratation. Même une
acceptation manuelle ultérieure ne le rend pas automatiquement exploitable :
le type `analysis_bundle` doit d'abord être converti par une étape de
promotion scientifique qui produira le contrat stationnel attendu.

La CLI équivalente est :

    python scripts/import_forge_analysis_bundle_test.py BUNDLE.json +      --submitted-by UUID_OPERATEUR --operator-role writer --trace-id TRACE

La production reste volontairement fermée. L'ouverture future exigera une
décision séparée, un profil de production, une règle de promotion et une
preuve PostgreSQL/PostGIS à grande échelle.

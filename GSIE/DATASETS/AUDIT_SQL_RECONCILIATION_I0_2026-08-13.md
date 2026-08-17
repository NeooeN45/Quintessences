# Audit SQL de réconciliation Registry I0 — 2026-08-13

| Champ | Valeur |
|---|---|
| **Statut** | Exécuté en lecture seule — migration non exécutée |
| **Décision** | DEC-000068 |
| **Instance** | PostgreSQL Docker `api-db-1` |
| **Version Alembic** | `20260810_0048` |
| **Effet d'écriture** | Aucun — requêtes `SELECT` uniquement |
| **FETCH** | Fermé |

## 1. Résultat principal

L'audit de l'instance active trouve **36 ressources** Registry, réparties en
quatre groupes de neuf. L'ancien compteur de 32 excluait les quatre agents.

| Source historique | Agent | Source | Alias | Dataset | Version | Distribution | Droits | Santé | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `gbif` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **9** |
| `ign-apicarto-geopf` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **9** |
| `meteofrance-portail-api` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **9** |
| `soilgrids` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **9** |
| **Total** | **4** | **4** | **4** | **4** | **4** | **4** | **4** | **4** | **36** |

Tous les datasets sont encore `discovered`. Aucun n'est `staging`, `validated`
ou `production`.

## 2. Datasets persistés

| Slug historique | Version | Méthode | URL | Source |
|---|---|---|---|---|
| `gbif-occurrences` | `metadata-2026-08-10` | `api_rest` | `https://api.gbif.org` | `gbif` |
| `ign-apicarto` | `metadata-2026-08-10` | `api_rest` | `https://apicarto.ign.fr` | `ign-apicarto-geopf` |
| `meteofrance-services` | `metadata-2026-08-10` | `api_rest` | `https://portail-api.meteofrance.fr` | `meteofrance-portail-api` |
| `soilgrids-properties` | `metadata-2026-08-10` | `api_rest` | `https://www.isric.org/explore/soilgrids` | `soilgrids` |

## 3. Santé et droits réellement persistés

Les snapshots de santé sont `healthy` : GBIF 595,64 ms, IGN 1 290,26 ms,
Météo-France 309,21 ms et SoilGrids 3 429,46 ms. Ces valeurs prouvent un
contrôle technique du 10 août, pas la licence, la qualité scientifique ou
l'autorisation FETCH actuelle.

Les droits persistés sont identiques pour les quatre entrées :

```text
usage_rights=open
commercial_use_allowed=true
redistribution_allowed=true
attribution_required=true
ai_training_allowed=false
```

Cette représentation est trop large pour GBIF, Météo-France et les couches IGN.
DEC-000068 interdit de recopier ces droits vers les nouvelles identités sans
revue produit par produit.

## 4. DataAsset RAW et point critique SoilGrids

La base contient un seul `DataAsset` :

```text
format       GEOTIFF_INT16
taille       569 octets
sha256       a6fd8b120b11e64612cdf3ee22854d8db28413cbe7bd480291cfb203ee24840e
storage_uri  s3://gsie-assets/raw/fetch/soilgrids/a584c377-ff39-4e58-967a-7304b732bb47.tif
dataset      soilgrids-properties
```

Il s'agit du micro-extrait autorisé par DEC-000061. Il est rattaché à la
version historique `soilgrids-properties`, même si son resource n'a pas le
marqueur `registry=data_registry`.

La migration ne doit donc pas simplement renommer le slug vers `soilgrids-wcs`.
Elle doit conserver DEC-000061, le checksum, l'URI MinIO, l'identité historique,
l'alias, la preuve WCS et le statut `discovered`.

## 5. État du schéma

Les tables `data_rights_statement` et `dataset_health` existent dans le schéma
`gsie_gouvernance`, pas dans `public`. La version Alembic `20260810_0048` et
les tables gouvernance ont été vérifiées en lecture seule.

## 6. Mapping de migration

| Historique | Cible proposée | Confiance | Action |
|---|---|---|---|
| `gbif-occurrences` | `gbif-species-api` | Faible | Le code cible Species API, mais le nom prétend aux occurrences. Revue obligatoire. |
| `gbif-occurrences` | `gbif-occurrence-datasets` | Nulle sans contenu | Ne pas créer avant identification du jeu constitutif. |
| `ign-apicarto` | Cadastre / limites / WFS | Nulle sans traces | Lire les appels réellement consommés. |
| `meteofrance-services` | Météo des forêts / SAFRAN / AROME / observations | Nulle sans traces | L'adapter actuel ne suffit pas. |
| `soilgrids-properties` | `soilgrids-wcs` | Élevée pour le DataAsset | Conserver l'alias historique et DEC-000061 ; aucun déplacement automatique. |

## 7. Requêtes reproductibles

Les contrôles ont été effectués avec `psql` en lecture seule :

```sql
SELECT version_num FROM alembic_version;
SELECT type, count(*) FROM resource
 WHERE deleted_at IS NULL AND metadata_json->>'registry'='data_registry'
 GROUP BY type ORDER BY type;
SELECT d.slug, dv.version, dv.status, dist.access_method,
       dist.access_url, dist.licence
FROM dataset d JOIN resource rd ON rd.id=d.id
JOIN dataset_version dv ON dv.dataset_id=d.id
JOIN distribution dist ON dist.dataset_version_id=dv.id
WHERE rd.metadata_json->>'registry'='data_registry';
SELECT d.slug, h.health_status, h.checked_at, h.latency_ms
FROM dataset d JOIN dataset_version dv ON dv.dataset_id=d.id
JOIN gsie_gouvernance.dataset_health h ON h.dataset_version_id=dv.id;
SELECT count(*) FROM data_asset;
```

Aucun `UPDATE`, `INSERT`, `DELETE`, migration Alembic ou application de
manifeste n'a été exécuté.

## 8. Décision de sortie

L'audit SQL est terminé, mais la migration n'est pas autorisée. Il faut encore
inspecter les adapters et traces d'utilisation, puis produire un `dry-run`
spécialisé qui préserve le DataAsset SoilGrids. Les cibles GBIF, IGN et
Météo-France restent à décider humainement. `E:\Documents` reste exclu.

## 9. Comparaison avec les adapters du code

La lecture statique des adapters réduit certaines ambiguïtés, sans autoriser
à elle seule une migration des lignes historiques :

| Adapter | Capacité et endpoint observés | Cible historique étayée |
|---|---|---|
| `GBIFAdapter` | Species API sur `api.gbif.org/v1`, opérations `species_match` et `vernacular_name` | `gbif-species-api` — confiance élevée pour ces opérations ; le slug `gbif-occurrences` reste non résolu pour les occurrences. |
| `IGNAdapter` | Cadastre sur `apicarto.ign.fr` et altitude sur `data.geopf.fr` | Au moins deux fiches distinctes à confirmer : `ign-apicarto-cadastre` et une fiche altitude/GeoPlateforme ; aucune fusion automatique avec les limites administratives. |
| `MeteoFranceAdapter` | Météo des forêts sur `public-api.meteofrance.fr`, opération `danger_feux_departements` | `meteofrance-meteo-forets` — confiance élevée pour cette opération ; les anciennes données services restent à ventiler. |
| `SoilGridsAdapter` | REST propriétés sur `rest.isric.org`, opération `properties` | Ne justifie pas à lui seul le rattachement du micro-extrait WCS `soilgrids-wcs` ; la preuve WCS doit conserver sa lignée explicite. |

Conclusion : la comparaison permet de préparer un `dry-run` spécialisé pour
GBIF Species et Météo des forêts. Elle ne remplace ni la qualification des
contenus persistés, ni la décision humaine pour IGN, les occurrences GBIF et
la lignée WCS SoilGrids.

Le scan des traces de code a également trouvé la projection historique du
`health_scheduler`. Elle a été corrigée en préférence canonique avec repli
historique strictement opérationnel : tant que la base n'est pas migrée, la
santé peut encore être mesurée sur les anciens slugs ; dès qu'un slug canonique
est présent dans le manifeste, il est choisi. Cette compatibilité ne réécrit
aucune ressource et n'ouvre pas FETCH.

## 10. Traces persistées disponibles

Une lecture complémentaire des champs `stats`, `changes` et `metadata_json`
confirme que les quatre versions historiques ne contiennent aucune opération
adapter, couche, propriété ou jeu d'occurrences : `stats` est `null` et
`metadata_json.operation` vaut seulement `metadata_only`. Les URL et formats
persistés sont des métadonnées générales (`json`) ; ils ne permettent donc pas
de décider une ventilation rétroactive. Cette absence de preuve maintient les
portes de migration fermées.

Le dry-run d'identité exécuté ensuite a produit
`GSIE/DATASETS/DRY_RUN_RECONCILIATION_I0_2026-08-13.json`. Il confirme trois
résultats `UNRESOLVED`, un `PRESERVE_LINEAGE` SoilGrids et zéro écriture.

# Migration GeoSylva ↔ Data Registry — Phase 7

**Statut :** audit du contrat et préparation, sans modification du dépôt
mobile

**Date :** 2026-08-10
**Dépôts concernés :** `Quintessences` (API) et `apps/GeoSylva` (dépôt
Android externe)
## 1. Constat vérifié

GeoSylva possède déjà une synchronisation parcellaire distincte et cohérente :

- `PUT /api/v1/sync/geosylva/parcelles/{client_id}` pour les upserts ;
- `DELETE /api/v1/sync/geosylva/parcelles/{client_id}` pour les tombstones ;
- `GET /api/v1/sync/geosylva/parcelles` pour le pull paginé ;
- `operation_id` idempotent, `base_version` optimiste et réponse `409` en cas
  de conflit ;
- le mobile refuse l'écrasement d'une modification locale non synchronisée et
  conserve la session dans un stockage chiffré.

Cette synchronisation ne doit pas être remplacée par le Data Registry : une
parcelle est une donnée métier éditable, alors qu'un `DatasetVersion` est une
publication immuable et qualifiée.

## 2. Ce que le Data Registry apporte à GeoSylva

Le client mobile pourra consommer, après authentification et autorisation
`dataset:read` :

1. `POST /api/v1/data/resolve` pour demander une donnée par domaine, emprise,
   période et usage ;
2. lire la décision explicable (`selected`, `fallback`, blocages, version de
   politique) ;
3. télécharger ensuite un pack ou une projection uniquement via un endpoint
   de distribution qui vérifiera version, licence, checksum et droits offline.

Le troisième point n'est volontairement pas encore inventé : aucun endpoint
de téléchargement ou d'URL présignée n'est ajouté tant que le service
d'application du manifeste et l'archivage `DataAsset` ne sont pas livrés.

## 3. Mapping initial des packs GeoSylva

| Besoin mobile | Domaine Registry | Sources manifestées | Mode actuel |
|---|---|---|---|
| Parcellaire/contours IGN | `gis`, `land_cover` | `ign-apicarto-geopf` | lien metadata-only |
| Essences et occurrences | `biodiversity`, `botany` | `gbif` | lien metadata-only |
| Sols | `pedology`, `soil_moisture` | `soilgrids` | lien metadata-only |
| Météo/feu | `weather`, `climate` | `meteofrance-portail-api` | lien metadata-only |

Le mode `metadata_only` ne fournit donc pas encore de données offline. Il
permet au site et aux outils de contrôle de vérifier l'identité, la licence et
le domaine avant de produire un pack.

## 4. Garde-fous d'implémentation mobile

La future façade Kotlin doit :

- réutiliser la base URL et le client TLS déjà validés par
  `ParcelSyncApiFactory` ;
- transmettre le jeton Bearer sans le journaliser et rafraîchir une fois sur
  `401` ;
- conserver localement `dataset_slug`, `dataset_version`, `policy_version`,
  `checksum` et `licence` avec le pack ;
- refuser l'installation si le checksum ou la licence ne correspond pas à la
  décision GSIE ;
- distinguer un pack absent, obsolète, interdit ou partiellement téléchargé ;
- ne jamais fusionner automatiquement une géométrie IGN avec une géométrie
  technicien sans conserver la provenance et le CRS.

## 5. Ordre de réalisation

1. Appliquer le manifeste en base via un service idempotent `dry-run` ;
2. persister les contrôles `DatasetHealth` des distributions connues ;
3. exposer une lecture de décision adaptée au mobile et un manifeste de pack
   signé/versionné ;
4. implémenter le downloader GeoSylva et ses tests checksum/offline ;
5. seulement ensuite activer les quatre familles de packs par configuration
   progressive.

Le dépôt Android externe n'est pas modifié dans cette étape afin de ne pas
brancher un client sur des distributions qui ne sont pas encore archivées et
vérifiables.

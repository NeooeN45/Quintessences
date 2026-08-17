# Manifeste spatial metadata-only — quarantaine locale

**Identifiant :** GSIE-DATA-QUARANTINE-SPATIAL-2026-08-12  
**Statut :** Draft / quarantaine  
**Date :** 2026-08-12  
**Source :** inventaire borné de `E:\Documents`  
**Ingestion :** interdite  
**Copie d'octets :** interdite  
**Entraînement IA :** interdit  

Ce manifeste enregistre uniquement des candidats et leur routage. Il ne
constitue ni une autorisation d'usage, ni une copie, ni une preuve de qualité
géométrique. Les fichiers restent à leur emplacement local et ne sont pas
référencés par le Data Registry comme `DataAsset`.

## Candidats prioritaires

| Identifiant logique | Ressource locale | Usage de test proposé | CRS / technique | Statut droits |
|---|---|---|---|---|
| `spatial.ccf-celles.gpkg` | `E:\Documents\CCF Celles sur Plaine.gpkg` | scénario forêt, parcellaire et placettes | 7 couches, EPSG:2154 | à qualifier ; données potentiellement cadastrales |
| `spatial.placette.gpkg` | `E:\Documents\Placette.gpkg` | déduplication et contrôle de reprojection | couche signalée en EPSG:3857 | à qualifier ; CRS inadapté aux surfaces forestières |
| `spatial.longeyroux.placettes` | couches Longeyroux | rattachement station–placette | EPSG:2154 annoncé | provenance couche par couche à reconstruire |
| `spatial.chantier-ecole.osm` | `E:\Documents\chantier_ecole_osm.geojson` | test OSM/terrain et import FieldIntake | GeoJSON ; couverture à vérifier | ODbL et attribution à confirmer |
| `spatial.dfci.legacy-gpkg` | dossiers DFCI et GeoPackages associés | futur test Ignis/DFCI en sandbox | couches et CRS hétérogènes | données sensibles et licences à formaliser |
| `spatial.mnh-hauteur-objets.tif` | raster MNH local | contrôle dérivation MNS–MNT | raster d'environ 39,8 Mio | recette et droits à qualifier |

## Portes obligatoires avant ouverture

1. Identifier le producteur, la version, le millésime et la couverture de chaque
   couche.
2. Confirmer licence, attribution, droit de copie, redistribution et usage IA.
3. Calculer un SHA-256 du fichier source sans le déplacer ; si le fichier est
   modifié, créer une nouvelle version logique.
4. Contrôler CRS, unités, emprise, géométrie invalide, doublons et systèmes de
   coordonnées verticaux avant toute mesure de surface ou de distance.
5. Produire un rapport de quarantaine signé par un opérateur ; aucun scénario
   Gold ne peut dépendre d'un candidat `pending_review`.

## Routage prévu

```text
fichier local
  -> fiche de qualification DATASETS
  -> quarantaine technique et juridique
  -> manifeste metadata-only
  -> FieldIntake / scénario Silver si autorisé
  -> Data Registry uniquement après décision explicite
```

Les grands ensembles DFCI et les couches potentiellement cadastrales restent
hors benchmark public et hors FETCH. Toute future sélection territoriale devra
être pseudonymisée et limitée à l'emprise nécessaire.


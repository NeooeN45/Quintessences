# GIS Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | GIS Engine |
| **Catégorie** | Moteur domaine (géospatial) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-005, GSIE-CON-007 |
| **Ordre de développement** | 6 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Gérer, calculer et fournir les données géospatiales de référence
(parcelles, relief, hydrographie) et les caractéristiques stationnelles
dérivées (pente, exposition, altitude), avec traçabilité de la source
et de la date de mise à jour.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| Spatial Database | Base de données | Données géospatiales stockées (parcelles, MNT, hydrographie) |
| IGN | Source externe | BD Ortho, BD Topo, MNT, cadastre, données forestières IGN |
| Cadastre | Source externe | Limites parcellaires, propriété |
| Bundle de mission | Cache local | Données préchargées pour fonctionnement hors-ligne (RFC-0003) |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `DIAGNOSTIC_ENGINE` | Caractéristiques stationnelles | Pente, exposition, altitude, distance, hydrographie |
| `CORRELATION_ENGINE` | Données géospatiales | Couches pour croisement statistique |
| `REASONING_ENGINE` | Caractéristiques stationnelles | Données géographiques pour l'inférence |
| `SIMULATION_ENGINE` | Emprise et terrain | MNT et limites pour les projections spatialisées |
| Utilisateur (via interface) | Cartes | Couches cartographiques pour visualisation terrain |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Base externe | Spatial Database | Stockage des données géospatiales |
| Source externe | IGN | Données officielles (BD Ortho, BD Topo, MNT) |
| Source externe | Cadastre | Limites parcellaires |
| Aucun moteur | — | Le GIS Engine ne dépend d'aucun autre moteur (source domaine) |

## 5. Contrat d'interface

### Entrée — `GeoQuery`

```
GeoQuery = {
  requete_id : UUID
  type       : enum { station, parcelle, zone, itineraire }
  emprise    : EmpriseGeographique
  couches_demandees : liste de enum { mnt, pente, exposition, altitude, hydrographie, cadastre, orthophoto, sol }
  resolution : texte (optionnel — ex. « 5m », « 25m »)
}
```

### Sortie — `GeoData`

```
GeoData = {
  requete_id   : UUID
  station_id   : UUID (optionnel)
  couches      : liste de GeoLayer
  source       : SourceReference
  date_donnees : ISO 8601 (date de mise à jour des données)
  mode         : enum { en_ligne, hors_ligne, degrade }
}

GeoLayer = {
  nom       : enum { mnt, pente, exposition, altitude, hydrographie, cadastre, orthophoto }
  type      : enum { raster, vecteur, mesure }
  valeurs   : structure selon type (grille, géométries, valeur ponctuelle)
  unite     : texte (ex. « degrés », « mètres », « % »)
  resolution: texte (optionnel)
  source    : SourceReference
  date_maj  : ISO 8601
}

StationCharacteristics = {
  station_id  : UUID
  altitude_m  : décimal
  pente_degres: décimal
  exposition_degres : décimal (0–360)
  hydrographie_proximite_m : décimal (optionnel)
  coordonnees : { latitude, longitude } (WGS 84)
  source      : SourceReference
}
```

## 6. Garanties

- **Toute donnée géospatiale est sourcée et datée** — chaque couche
  porte son origine (IGN, cadastre) et sa date de mise à jour (principe
  fondateur).
- Mode hors-ligne : cache local des données de référence (article T-8,
  RFC-0003 bundle de mission).
- Mode dégradé documenté lorsque les données temps réel sont
  indisponibles.
- Le moteur ne produit **pas de diagnostic** — il fournit des données
  et des caractéristiques (séparation des responsabilités).
- Les coordonnées sont en WGS 84 (standard interoperable).

## 7. Cas d'usage

### Cas 1 — Calcul des caractéristiques stationnelles pour une parcelle

Le forestier sélectionne la parcelle 27 sur l'application. Le GIS
Engine interroge le MNT en cache local (IGN, 2024) et calcule : altitude
moyenne 420 m, pente moyenne 18°, exposition dominante sud-ouest (225°),
distance au cours d'eau le plus proche : 150 m. Ces caractéristiques
sont transmises au Diagnostic Engine et au Reasoning Engine.

### Cas 2 — Visualisation cartographique hors-ligne en terrain isolé

Le forestier est en terrain sans réseau. Le GIS Engine fournit les
couches cartographiques (orthophoto IGN, limites parcellaires, MNT)
depuis le cache local du bundle de mission. L'application affiche la
carte, la position GPS du forestier et les arbres inventoriés. Les
modifications sont stockées localement et synchronisées au retour
(RFC-0003, synchronisation orientée données).

## 8. État de l'art et pistes de recherche sourcées

Cette section recense, à titre de piste pour la Phase 4
(implémentation), des technologies et méthodes actuelles pertinentes
pour la responsabilité du GIS Engine — gérer et calculer les données
géospatiales de référence (parcelles, relief, hydrographie) et les
caractéristiques stationnelles dérivées (pente, exposition, altitude),
avec traçabilité de la source et de la date. Elle ne couvre pas la
donnée LiDAR HD, déjà traitée dans
`GSIE/RESEARCH/LIDAR_HD_SPECIFICATIONS.md`.

### 8.1 Stack SIG open-source (stockage, calcul, publication)

La combinaison **PostGIS + GDAL/OGR + QGIS Server** constitue une pile
de référence largement documentée pour ce type de moteur : PostGIS
assure le stockage et l'indexation spatiale des couches de référence
(parcelles, MNT, hydrographie), GDAL/OGR assure l'ingestion et la
conversion de formats hétérogènes (Shapefile, GeoJSON, GeoTIFF), et
QGIS Server publie les couches selon les standards OGC (WMS, WFS,
OGC API Features) — partageant le même moteur de rendu que QGIS
desktop, déjà mentionné comme client dans l'écosystème Quintessences
(`apps/QGISIA`).

Pour le calcul dérivé de pente et d'exposition à partir d'un MNT,
l'outil `gdaldem` du projet GDAL implémente les deux algorithmes de
référence du domaine : la méthode de **Horn (1981)**, par défaut dans
GDAL/QGIS/ArcGIS car robuste au bruit, et celle de
**Zevenbergen & Thorne (1987)**, qui ajuste un polynôme quartique sur
une fenêtre 3×3. Les deux méthodes divergent sensiblement en zone de
forte courbure ou de pente quasi nulle — un choix méthodologique à
documenter explicitement pour la traçabilité exigée par
`GSIE-CON-005`.

### 8.2 API Géoplateforme IGN (successeur de Géoservices/Géoportail)

Depuis juillet 2021, les données de référence de l'IGN (BD Ortho,
BD Topo, RGE ALTI, plan IGN, cadastre) sont diffusées gratuitement et
sans clé d'API via la **Géoplateforme** (`data.geopf.fr`), qui
convergence progressivement avec le portail `cartes.gouv.fr`. Deux
composantes sont directement pertinentes pour le contrat d'interface
du moteur :

- **API Carto — module Cadastre** (`apicarto.ign.fr`) : accès REST
  (OpenAPI, GeoJSON, WGS 84) aux limites parcellaires (PCI —
  Parcellaire Express), correspondant à l'entrée « Cadastre » déjà
  documentée.
- **API de calcul altimétrique** (`data.geopf.fr/altimetrie`) : fournit
  l'altitude d'un ou plusieurs points, ou un profil altimétrique le
  long d'une ligne, en s'appuyant au choix sur RGE ALTI® ou BD ALTI®
  — avec une précision qui diffère selon la ressource choisie, donc
  une source et une résolution à tracer dans `SourceReference`.

Le catalogue général des offres IGN (`ign.fr/offre`) confirme par
ailleurs la diffusion de **BD TOPO**, de l'**occupation du sol
(OCS-GE)**, des **données altimétriques** (MNT/MNS/MNH, accessibles
via `cartes.gouv.fr`) et du **Registre Parcellaire Graphique (RPG)**
— des couches complémentaires à évaluer pour enrichir `GeoLayer` au-delà
du périmètre actuel (mnt, pente, exposition, altitude, hydrographie,
cadastre, orthophoto, sol).

### 8.3 Référentiel hydrographique national

Pour la couche `hydrographie` et le champ
`hydrographie_proximite_m`, le référentiel opérationnel existant est
**BD Carthage** (Base de données sur la cartographie thématique des
agences de l'eau), produit en partenariat entre le ministère chargé de
l'environnement, les agences de l'eau et l'IGN à partir de BD Carto.
Il normalise et hiérarchise les cours d'eau, bassins et zones
hydrographiques du territoire français et constitue la référence
citée par le Sandre (portail national des référentiels sur l'eau).

### 8.4 Formats cloud-natifs et indexation spatiale moderne

Pour le cache local du bundle de mission (mode hors-ligne, RFC-0003),
deux formats récents méritent d'être évalués comme alternative ou
complément à un export classique (GeoJSON, GeoTIFF) :

- **GeoParquet** (standard porté par l'Open Geospatial Consortium
  depuis sa version 1.0 d'août 2023) encode les données vectorielles
  dans le format colonnaire Apache Parquet, ce qui permet un accès
  partiel et performant aux données de parcelles ou de cadastre sans
  base de données dédiée.
- **PMTiles** (format développé par Protomaps / Brandon Liu) empaquette
  une pyramide de tuiles (vectorielles ou raster) dans un fichier
  unique interrogeable par requêtes HTTP range — une piste directement
  adaptée au cas d'usage « visualisation cartographique hors-ligne en
  terrain isolé » (§7, Cas 2) sans nécessiter de serveur cartographique
  embarqué.

Sur le plan de l'indexation, le système hexagonal **H3** (porté
par Uber) est cité dans la littérature cloud-native comme schéma de
partitionnement possible pour accélérer les jointures spatiales entre
couches — une piste à considérer pour les échanges avec le
`CORRELATION_ENGINE`, sans nécessité de trancher à ce stade entre H3,
une grille régulière ou un index R-tree classique (déjà natif dans
PostGIS).

### 8.5 Synthèse

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| **PostGIS** (extension spatiale de PostgreSQL, projet OSGeo) | Base de données géospatiale de référence (« Spatial Database ») | Stockage et indexation natifs des parcelles, MNT et hydrographie avec requêtes topologiques ; correspond à l'entrée déjà documentée en §2. |
| **GDAL/OGR** — module `gdaldem` (algorithmes Horn 1981 / Zevenbergen & Thorne 1987) | Calcul dérivé de la pente, de l'exposition et de l'altitude à partir du MNT | Implémente les méthodes de référence du domaine, déjà standards de facto dans QGIS/ArcGIS ; alimente directement `StationCharacteristics`. |
| **QGIS Server** | Publication des couches cartographiques (WMS/WFS/OGC API Features) vers l'utilisateur | Partage le moteur de rendu avec QGIS desktop (cohérent avec `apps/QGISIA`) ; sert les mêmes couches que le contrat `GeoLayer`. |
| **API Géoplateforme IGN** (BD Ortho, BD Topo, RGE ALTI, API Carto/cadastre, API de calcul altimétrique, OCS-GE, RPG) | Source externe de référence pour l'ingestion des couches IGN et cadastre | Correspond aux entrées « IGN » et « Cadastre » déjà documentées ; l'API altimétrique fournit une piste concrète pour `altitude_m` avec source et résolution tracées. |
| **BD Carthage** (IGN / agences de l'eau) | Référentiel hydrographique national | Correspond directement à la couche `hydrographie` et au champ `hydrographie_proximite_m`. |
| **GeoParquet (standard OGC) / PMTiles (Protomaps)** | Formats cloud-natifs pour le cache local du bundle de mission hors-ligne | Accès partiel et performant sans serveur dédié, adapté au mode hors-ligne (RFC-0003) et au cas d'usage terrain isolé (§7, Cas 2). |

Ces pistes restent à arbitrer en Phase 4, en fonction des contraintes
d'hébergement, de volumétrie et du niveau de dépendance réseau
acceptable pour l'application terrain.

### Sources

- **PostGIS** — projet OSGeo, extension spatiale de PostgreSQL. https://postgis.net/
- **GDAL/OGR**, module `gdaldem` — OSGeo Foundation. https://gdal.org/
- **QGIS Server** — projet QGIS. https://github.com/qgis/qgis ; https://qgis.org/
- Horn, B.K.P. (1981), *Hill Shading and the Reflectance Map*, méthode de calcul de pente/exposition par fenêtre glissante 3×3 (référence décrite dans la documentation xDEM : https://xdem.readthedocs.io/en/stable/advanced_examples/plot_slope_methods.html).
- Zevenbergen, L.W. & Thorne, C.R. (1987), méthode d'ajustement polynomial quartique pour le calcul de pente/exposition sur MNT (référence décrite dans la documentation xDEM, idem).
- **IGN — Géoplateforme** (successeur de Géoservices/Géoportail). Portail : https://cartes.gouv.fr/ ; documentation technique : https://geoservices.ign.fr/
- **IGN — Catalogue des offres** (BD TOPO, données forestières, OCS-GE, données altimétriques, RPG). https://www.ign.fr/offre
- **API Carto — module Cadastre**, IGN. https://apicarto.ign.fr/api/doc/cadastre ; fiche data.gouv.fr : https://www.data.gouv.fr/dataservices/api-carto-module-cadastre
- **API Géoplateforme — Calcul altimétrique**, IGN. https://geoplateforme.pages.gpf-tech.ign.fr/altimetrie/api-rest-calcul-altimetrique/
- **BD Carthage**, référentiel hydrographique national, IGN / agences de l'eau / ministère chargé de l'environnement, diffusé via le Sandre. https://www.sandre.eaufrance.fr/notice-doc/diffusion-du-r%C3%A9f%C3%A9rentiel-hydrographique-bd-carthage
- **GeoParquet** — spécification OGC, version 1.0.0 (août 2023). https://github.com/opengeospatial/geoparquet ; guide : https://guide.cloudnativegeo.org/geoparquet/
- **PMTiles** — format développé par Protomaps (Brandon Liu). https://docs.protomaps.com/pmtiles/ ; https://github.com/protomaps/pmtiles
- **H3** — système d'indexation géospatiale hexagonale, Uber. Mentionné dans le guide cloud-native geospatial (https://guide.cloudnativegeo.org/geoparquet/).

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*

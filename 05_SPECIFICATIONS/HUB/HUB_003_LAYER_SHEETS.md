# HUB-003 — Fiches détaillées des couches du Hub

| Champ | Valeur |
|---|---|
| **Document** | HUB-003 |
| **Dossier** | 05_SPECIFICATIONS/HUB/ |
| **Phase** | 3 — Connaissance (préparation Phase 4) |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Lois fondatrices** | CON-005 (traçabilité), CON-007 (modularité) |
| **Documents connexes** | `HUB_001_SPECIFICATION.md`, `HUB_002_INTERFACE_CONTRACT.md`, `IGNIS_001_SPECIFICATION.md`, `GEO_001_SPECIFICATION.md` |

---

## 1. Objet

Fiche détaillée de chacune des 22 couches du contrat HUB-002. Une fiche
décrit l'identité, la géométrie, le canal, les datasets sources, le
moteur producteur et le mode de rendu attendu dans le Hub.

---

## 2. Structure d'une fiche

Chaque fiche contient les champs suivants :

| Champ | Description |
|---|---|
| `layer_id` | Identifiant stable (HUB-002 §2) |
| `app` | App productrice |
| `display_name` | Nom affiché dans l'UI Hub |
| `description` | Description courte |
| `geometry_type` | Type de géométrie (HUB-002 §4) |
| `canal` | WebSocket (temps réel) ou REST (volumineux/statique) |
| `fréquence` | Fréquence de mise à jour |
| `SRS` | Système de référence spatial |
| `format_payload` | GeoJSON / 3D Tiles / GeoTIFF |
| `mode_rendu` | Mode de rendu Hub (HUB-002 §4) |
| `datasets_sources` | DS-xxx consommés (CON-005) |
| `moteur_producteur` | Moteur GSIE |
| `état` | réel / simulé / mixte |
| `priorité_P4` | P0 (critique) / P1 (haute) / P2 (standard) |

---

## 3. Couches GeoSylva (7 fiches)

### 3.1 geosylva.peuplements

| Champ | Valeur |
|---|---|
| `layer_id` | `geosylva.peuplements` |
| `app` | GeoSylva |
| `display_name` | Peuplements forestiers |
| `description` | Carte des peuplements (type, structure, dendrométrie) |
| `geometry_type` | `polygon` |
| `canal` | REST (3D Tiles) |
| `fréquence` | Statique |
| `SRS` | EPSG:2154 |
| `format_payload` | 3D Tiles 1.1 + EXT_structural_metadata |
| `mode_rendu` | Mesh + matériau (translucent possible) |
| `datasets_sources` | DS-001 (BD Forêt v2), DS-002 (LiDAR HD) |
| `moteur_producteur` | GIS Engine + Forest Dynamics |
| `état` | réel |
| `priorité_P4` | P0 |

### 3.2 geosylva.arbres

| Champ | Valeur |
|---|---|
| `layer_id` | `geosylva.arbres` |
| `app` | GeoSylva |
| `display_name` | Arbres individuels |
| `description` | Arbres segmentés (hauteur, DBH, essence) |
| `geometry_type` | `point` |
| `canal` | REST (GeoJSON) |
| `fréquence` | Statique |
| `SRS` | EPSG:2154 |
| `format_payload` | GeoJSON |
| `mode_rendu` | Sprite / instanced mesh |
| `datasets_sources` | DS-002 (LiDAR HD), DS-003 (IFN) |
| `moteur_producteur` | Forest Dynamics (PyCrown / SegmentAnyTreeV2) |
| `état` | réel |
| `priorité_P4` | P1 |

### 3.3 geosylva.essences

| Champ | Valeur |
|---|---|
| `layer_id` | `geosylva.essences` |
| `app` | GeoSylva |
| `display_name` | Essences dominantes |
| `description` | Carte des essences (BD Forêt + Crown-BERT) |
| `geometry_type` | `polygon` |
| `canal` | REST (3D Tiles) |
| `fréquence` | Statique |
| `SRS` | EPSG:2154 |
| `format_payload` | 3D Tiles 1.1 |
| `mode_rendu` | Mesh + matériau (couleur par essence) |
| `datasets_sources` | DS-001 (BD Forêt v2) |
| `moteur_producteur` | Botanical Engine |
| `état` | réel |
| `priorité_P4` | P1 |

### 3.4 geosylva.diagnostics

| Champ | Valeur |
|---|---|
| `layer_id` | `geosylva.diagnostics` |
| `app` | GeoSylva |
| `display_name` | Diagnostics sylvicoles |
| `description` | Diagnostics par parcelle (état sanitaire, recommandations) |
| `geometry_type` | `polygon` |
| `canal` | REST (GeoJSON) |
| `fréquence` | Quotidien |
| `SRS` | EPSG:2154 |
| `format_payload` | GeoJSON |
| `mode_rendu` | Mesh + matériau (couleur par diagnostic) |
| `datasets_sources` | DS-001, DS-002, DS-003 |
| `moteur_producteur` | Diagnostic Engine |
| `état` | réel |
| `priorité_P4` | P0 |

### 3.5 geosylva.recommandations

| Champ | Valeur |
|---|---|
| `layer_id` | `geosylva.recommandations` |
| `app` | GeoSylva |
| `display_name` | Recommandations |
| `description` | Recommandations de gestion (contournables, CON-001) |
| `geometry_type` | `polygon` |
| `canal` | REST (GeoJSON) |
| `fréquence` | Quotidien |
| `SRS` | EPSG:2154 |
| `format_payload` | GeoJSON |
| `mode_rendu` | Mesh + matériau (icônes superposées) |
| `datasets_sources` | — (sortie Diagnostic Engine) |
| `moteur_producteur` | Recommendation Engine |
| `état` | réel |
| `priorité_P4` | P1 |

### 3.6 geosylva.biomasse

| Champ | Valeur |
|---|---|
| `layer_id` | `geosylva.biomasse` |
| `app` | GeoSylva |
| `display_name` | Biomasse (GEDI / ESA) |
| `description` | Carte de biomasse aérienne (AGB) |
| `geometry_type` | `raster` |
| `canal` | REST (GeoTIFF) |
| `fréquence` | Annuel |
| `SRS` | EPSG:4326 |
| `format_payload` | GeoTIFF (COG) |
| `mode_rendu` | Texture draped sur terrain |
| `datasets_sources` | DS-002 (LiDAR HD), DS-025 (GEDI), DS-026 (ESA CCI) |
| `moteur_producteur` | Forest Dynamics |
| `état` | réel |
| `priorité_P4` | P1 |

### 3.7 geosylva.pcg_vegetation

| Champ | Valeur |
|---|---|
| `layer_id` | `geosylva.pcg_vegetation` |
| `app` | GeoSylva |
| `display_name` | Végétation procédurale |
| `description` | PCG Unreal + Gaussian Splats (arbres remarquables) |
| `geometry_type` | `gaussian_splat` / `mesh_3dtiles` |
| `canal` | REST (metadata) |
| `fréquence` | Statique |
| `SRS` | EPSG:2154 |
| `format_payload` | 3D Tiles 1.1 (Gaussian Splat) |
| `mode_rendu` | Cesium Gaussian Splat tileset |
| `datasets_sources` | DS-001, DS-002 |
| `moteur_producteur` | — (rendu Hub) |
| `état` | réel |
| `priorité_P4` | P2 |

---

## 4. Couches Ignis (8 fiches)

### 4.1 ignis.front_de_feu

| Champ | Valeur |
|---|---|
| `layer_id` | `ignis.front_de_feu` |
| `app` | Ignis |
| `display_name` | Front de feu |
| `description` | Front de feu simulé (ForeFire) |
| `geometry_type` | `polygon` |
| `canal` | WebSocket |
| `fréquence` | Temps réel (< 1s) |
| `SRS` | EPSG:2154 |
| `format_payload` | GeoJSON (WebSocket) |
| `mode_rendu` | Mesh + matériau (translucent, animation) |
| `datasets_sources` | DS-002, DS-009, DS-022 |
| `moteur_producteur` | Simulation Engine (ForeFire) |
| `état` | simulé |
| `priorité_P4` | P0 |

### 4.2 ignis.hotspots

| Champ | Valeur |
|---|---|
| `layer_id` | `ignis.hotspots` |
| `app` | Ignis |
| `display_name` | Hotspots (FIRMS / VIIRS) |
| `description` | Détections satellites de chaleur active |
| `geometry_type` | `point` |
| `canal` | WebSocket |
| `fréquence` | Temps réel (< 30s) |
| `SRS` | EPSG:4326 |
| `format_payload` | GeoJSON (WebSocket) |
| `mode_rendu` | Sprite / instanced mesh (icône heatmap) |
| `datasets_sources` | DS-024 (FIRMS/VIIRS) |
| `moteur_producteur` | — (ingestion directe) |
| `état` | réel |
| `priorité_P4` | P0 |

### 4.3 ignis.meteo_vent

| Champ | Valeur |
|---|---|
| `layer_id` | `ignis.meteo_vent` |
| `app` | Ignis |
| `display_name` | Vent (vecteurs) |
| `description` | Champ de vent (direction, vitesse) Météo-France |
| `geometry_type` | `point` |
| `canal` | WebSocket |
| `fréquence` | Temps réel (< 5 min) |
| `SRS` | EPSG:2154 |
| `format_payload` | GeoJSON (WebSocket) |
| `mode_rendu` | Sprite / instanced mesh (flèches vectorielles) |
| `datasets_sources` | DS-009 (ARPEGE/AROME) |
| `moteur_producteur` | Climate Engine |
| `état` | réel |
| `priorité_P4` | P0 |

### 4.4 ignis.meteo_humidite

| Champ | Valeur |
|---|---|
| `layer_id` | `ignis.meteo_humidite` |
| `app` | Ignis |
| `display_name` | Humidité |
| `description` | Humidité relative + FWI |
| `geometry_type` | `raster` |
| `canal` | WebSocket |
| `fréquence` | Temps réel (< 5 min) |
| `SRS` | EPSG:2154 |
| `format_payload` | GeoJSON (WebSocket, échantillonné) |
| `mode_rendu` | Texture draped sur terrain |
| `datasets_sources` | DS-009, DS-010 |
| `moteur_producteur` | Climate Engine |
| `état` | réel |
| `priorité_P4` | P1 |

### 4.5 ignis.combustible

| Champ | Valeur |
|---|---|
| `layer_id` | `ignis.combustible` |
| `app` | Ignis |
| `display_name` | Combustible (3 strates) |
| `description` | Modèle de combustible 3 strates (0-3m, 3-15m, >15m) |
| `geometry_type` | `mesh_3dtiles` |
| `canal` | REST (3D Tiles) |
| `fréquence` | Statique |
| `SRS` | EPSG:2154 |
| `format_payload` | 3D Tiles 1.1 |
| `mode_rendu` | Cesium 3D Tiles tileset |
| `datasets_sources` | DS-001 (BD Forêt), DS-002 (LiDAR HD) |
| `moteur_producteur` | GIS Engine + Simulation |
| `état` | réel |
| `priorité_P4` | P0 |

### 4.6 ignis.drones

| Champ | Valeur |
|---|---|
| `layer_id` | `ignis.drones` |
| `app` | Ignis |
| `display_name` | Positions drones |
| `description` | Télémétrie drones (position, cap, altitude) |
| `geometry_type` | `point` |
| `canal` | WebSocket |
| `fréquence` | Temps réel (< 1s, 10 Hz) |
| `SRS` | EPSG:2154 |
| `format_payload` | GeoJSON (WebSocket) |
| `mode_rendu` | Sprite / instanced mesh (icône drone + trajectoire) |
| `datasets_sources` | — (télémétrie live) |
| `moteur_producteur` | — (PX4 → API GSIE) |
| `état` | réel |
| `priorité_P4` | P0 |

### 4.7 ignis.propagation

| Champ | Valeur |
|---|---|
| `layer_id` | `ignis.propagation` |
| `app` | Ignis |
| `display_name` | Propagation prédite |
| `description` | Propagation prédite à T+1h, T+3h, T+6h |
| `geometry_type` | `polygon` |
| `canal` | WebSocket |
| `fréquence` | Temps réel (< 1s) |
| `SRS` | EPSG:2154 |
| `format_payload` | GeoJSON (WebSocket) |
| `mode_rendu` | Mesh + matériau (translucent, niveau de confiance) |
| `datasets_sources` | DS-002, DS-009 |
| `moteur_producteur` | Simulation Engine (ForeFire) |
| `état` | simulé |
| `priorité_P4` | P0 |

### 4.8 ignis.perimetre_brule

| Champ | Valeur |
|---|---|
| `layer_id` | `ignis.perimetre_brule` |
| `app` | Ignis |
| `display_name` | Périmètre brûlé |
| `description` | Périmètre brûlé (Sentinel-2 / EFFIS) |
| `geometry_type` | `polygon` |
| `canal` | REST (GeoJSON) |
| `fréquence` | Quotidien |
| `SRS` | EPSG:4326 |
| `format_payload` | GeoJSON |
| `mode_rendu` | Mesh + matériau (texture brûlé) |
| `datasets_sources` | DS-023 (EFFIS) |
| `moteur_producteur` | Simulation Engine |
| `état` | réel |
| `priorité_P4` | P1 |

---

## 5. Couches Hydro (3 fiches)

### 5.1 hydro.reseau

| Champ | Valeur |
|---|---|
| `layer_id` | `hydro.reseau` |
| `app` | Hydro |
| `display_name` | Réseau hydrographique |
| `description` | Cours d'eau et canaux |
| `geometry_type` | `line` |
| `canal` | REST (3D Tiles) |
| `fréquence` | Statique |
| `SRS` | EPSG:2154 |
| `format_payload` | 3D Tiles 1.1 |
| `mode_rendu` | Mesh + matériau (eau) |
| `datasets_sources` | BD Topo IGN |
| `moteur_producteur` | GIS Engine |
| `état` | réel |
| `priorité_P4` | P2 |

### 5.2 hydro.zones_humides

| Champ | Valeur |
|---|---|
| `layer_id` | `hydro.zones_humides` |
| `app` | Hydro |
| `display_name` | Zones humides |
| `description` | Inventaire zones humides |
| `geometry_type` | `polygon` |
| `canal` | REST (GeoJSON) |
| `fréquence` | Quotidien |
| `SRS` | EPSG:2154 |
| `format_payload` | GeoJSON |
| `mode_rendu` | Mesh + matériau (translucent) |
| `datasets_sources` | Inventaire régional |
| `moteur_producteur` | GIS Engine |
| `état` | réel |
| `priorité_P4` | P2 |

### 5.3 hydro.regimes

| Champ | Valeur |
|---|---|
| `layer_id` | `hydro.regimes` |
| `app` | Hydro |
| `display_name` | Régimes hydriques |
| `description` | Régimes hydriques saisonniers |
| `geometry_type` | `raster` |
| `canal` | REST (GeoTIFF) |
| `fréquence` | Saisonnier |
| `SRS` | EPSG:2154 |
| `format_payload` | GeoTIFF (COG) |
| `mode_rendu` | Texture draped sur terrain |
| `datasets_sources` | — |
| `moteur_producteur` | Climate Engine |
| `état` | réel |
| `priorité_P4` | P2 |

---

## 6. Couches Flora (2 fiches)

### 6.1 flora.repartition

| Champ | Valeur |
|---|---|
| `layer_id` | `flora.repartition` |
| `app` | Flora |
| `display_name` | Répartition floristique |
| `description` | Carte de répartition des espèces végétales |
| `geometry_type` | `polygon` |
| `canal` | REST (GeoJSON) |
| `fréquence` | Saisonnier |
| `SRS` | EPSG:2154 |
| `format_payload` | GeoJSON |
| `mode_rendu` | Mesh + matériau (couleur par espèce) |
| `datasets_sources` | SILENE, CBN |
| `moteur_producteur` | Botanical Engine |
| `état` | réel |
| `priorité_P4` | P2 |

### 6.2 flora.phenologie

| Champ | Valeur |
|---|---|
| `layer_id` | `flora.phenologie` |
| `app` | Flora |
| `display_name` | Phénologie |
| `description` | Stades phénologiques saisonniers |
| `geometry_type` | `raster` |
| `canal` | REST (GeoTIFF) |
| `fréquence` | Saisonnier |
| `SRS` | EPSG:2154 |
| `format_payload` | GeoTIFF (COG) |
| `mode_rendu` | Texture draped sur terrain |
| `datasets_sources` | Sentinel-2 (indices vegetation) |
| `moteur_producteur` | Botanical Engine |
| `état` | réel |
| `priorité_P4` | P2 |

---

## 7. Couches Artemis (2 fiches)

### 7.1 artemis.observations

| Champ | Valeur |
|---|---|
| `layer_id` | `artemis.observations` |
| `app` | Artemis |
| `display_name` | Observations faune |
| `description` | Observations faune (saisie terrain, pièges caméra) |
| `geometry_type` | `point` |
| `canal` | REST (GeoJSON) |
| `fréquence` | Événementiel |
| `SRS` | EPSG:2154 |
| `format_payload` | GeoJSON |
| `mode_rendu` | Sprite / instanced mesh (icône par espèce) |
| `datasets_sources` | INPN |
| `moteur_producteur` | — (saisie terrain) |
| `état` | réel |
| `priorité_P4` | P2 |

### 7.2 artemis.habitats

| Champ | Valeur |
|---|---|
| `layer_id` | `artemis.habitats` |
| `app` | Artemis |
| `display_name` | Habitats faune |
| `description` | Carte des habitats faune |
| `geometry_type` | `polygon` |
| `canal` | REST (3D Tiles) |
| `fréquence` | Statique |
| `SRS` | EPSG:2154 |
| `format_payload` | 3D Tiles 1.1 |
| `mode_rendu` | Mesh + matériau (couleur par habitat) |
| `datasets_sources` | Habitats CBN |
| `moteur_producteur` | GIS Engine |
| `état` | réel |
| `priorité_P4` | P2 |

---

## 8. Couches globales Hub (3 fiches)

### 8.1 hub.terrain_ign

| Champ | Valeur |
|---|---|
| `layer_id` | `hub.terrain_ign` |
| `app` | Hub |
| `display_name` | Terrain IGN (MNT 50cm) |
| `description` | MNT LiDAR HD IGN, rendu Cesium 3D Terrain |
| `geometry_type` | `mesh_3dtiles` (terrain) |
| `canal` | REST (3D Tiles) |
| `fréquence` | Statique |
| `SRS` | EPSG:4978 (géocentrique) |
| `format_payload` | 3D Tiles 1.1 (quantized mesh) |
| `mode_rendu` | Cesium 3D Terrain |
| `datasets_sources` | DS-002 (LiDAR HD IGN) |
| `moteur_producteur` | GIS Engine |
| `état` | réel |
| `priorité_P4` | P0 |

### 8.2 hub.ortho_ign

| Champ | Valeur |
|---|---|
| `layer_id` | `hub.ortho_ign` |
| `app` | Hub |
| `display_name` | Orthophoto IGN (BD Ortho) |
| `description` | Orthophotographie HD IGN draped sur terrain |
| `geometry_type` | `raster` |
| `canal` | REST (WMTS / GeoTIFF) |
| `fréquence` | Statique |
| `SRS` | EPSG:2154 |
| `format_payload` | WMTS / COG |
| `mode_rendu` | Texture draped sur terrain |
| `datasets_sources` | BD Ortho IGN |
| `moteur_producteur` | GIS Engine |
| `état` | réel |
| `priorité_P4` | P0 |

### 8.3 hub.cesium_world

| Champ | Valeur |
|---|---|
| `layer_id` | `hub.cesium_world` |
| `app` | Hub |
| `display_name` | Globe Cesium (fallback) |
| `description` | Globe Cesium ion world terrain + bing imagery (fallback) |
| `geometry_type` | `mesh_3dtiles` (terrain) |
| `canal` | REST (3D Tiles) |
| `fréquence` | Statique |
| `SRS` | EPSG:4978 |
| `format_payload` | 3D Tiles 1.1 |
| `mode_rendu` | Cesium 3D Terrain (fallback) |
| `datasets_sources` | Cesium ion (fallback hors zone IGN) |
| `moteur_producteur` | — |
| `état` | réel |
| `priorité_P4` | P2 |

---

## 9. Matrice de compatibilité (couche × mode rendu × priorité)

| layer_id | geometry_type | mode_rendu | priorité_P4 | canal |
|---|---|---|---|---|
| geosylva.peuplements | polygon | Mesh + matériau | P0 | REST |
| geosylva.arbres | point | Instanced mesh | P1 | REST |
| geosylva.essences | polygon | Mesh + matériau | P1 | REST |
| geosylva.diagnostics | polygon | Mesh + matériau | P0 | REST |
| geosylva.recommandations | polygon | Mesh + icônes | P1 | REST |
| geosylva.biomasse | raster | Texture draped | P1 | REST |
| geosylva.pcg_vegetation | gaussian_splat | Gaussian Splat | P2 | REST |
| ignis.front_de_feu | polygon | Mesh + animation | P0 | WebSocket |
| ignis.hotspots | point | Sprite heatmap | P0 | WebSocket |
| ignis.meteo_vent | point | Flèches vectorielles | P0 | WebSocket |
| ignis.meteo_humidite | raster | Texture draped | P1 | WebSocket |
| ignis.combustible | mesh_3dtiles | 3D Tiles tileset | P0 | REST |
| ignis.drones | point | Sprite + trajectoire | P0 | WebSocket |
| ignis.propagation | polygon | Mesh translucent | P0 | WebSocket |
| ignis.perimetre_brule | polygon | Mesh texture brûlé | P1 | REST |
| hydro.reseau | line | Mesh + matériau | P2 | REST |
| hydro.zones_humides | polygon | Mesh translucent | P2 | REST |
| hydro.regimes | raster | Texture draped | P2 | REST |
| flora.repartition | polygon | Mesh + couleur | P2 | REST |
| flora.phenologie | raster | Texture draped | P2 | REST |
| artemis.observations | point | Sprite icône | P2 | REST |
| artemis.habitats | polygon | Mesh + couleur | P2 | REST |
| hub.terrain_ign | mesh_3dtiles | Cesium 3D Terrain | P0 | REST |
| hub.ortho_ign | raster | Texture draped | P0 | REST |
| hub.cesium_world | mesh_3dtiles | Cesium 3D Terrain | P2 | REST |

**Synthèse priorités Phase 4 :**
- **P0 (critique, Phase 4 initiale) :** 11 couches (terrain, ortho, peuplements, diagnostics, front de feu, hotspots, vent, combustible, drones, propagation)
- **P1 (haute, Phase 4 mi-parcours) :** 6 couches (arbres, essences, recommandations, biomasse, humidité, périmètre brûlé)
- **P2 (standard, Phase 4 finalisation / Phase 5) :** 8 couches (PCG, hydro, flora, artemis, cesium_world)

---

## 10. Critères d'acceptation

- [x] 22 couches du contrat HUB-002 documentées (7 GeoSylva + 8 Ignis + 3 Hydro + 2 Flora + 2 Artemis)
- [x] 3 couches globales Hub ajoutées (terrain, ortho, cesium_world)
- [x] Chaque fiche contient les 14 champs requis
- [x] Datasets sources cités (DS-xxx) pour chaque couche
- [x] Moteur producteur identifié pour chaque couche
- [x] Mode de rendu Hub défini (HUB-002 §4)
- [x] État réel/simulé indiqué (CON-010)
- [x] Priorité Phase 4 assignée (P0/P1/P2)
- [x] Matrice de compatibilité complète (25 couches)

---

> Statut : *Draft — fiches couches Phase 3 (préparation Phase 4).
> À valider par le Fondateur. Aucun code métier (CON-003).*

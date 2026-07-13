# Fiche recherche — IGN LiDAR HD : spécifications, classification et pipeline

| Champ | Valeur |
|---|---|
| **Document** | RESEARCH/LIDAR_HD_SPECIFICATIONS |
| **Dossier** | GSIE/RESEARCH/ |
| **Phase** | 3 — Connaissance (préparation Phase 4) |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Source primaire** | `DC_LiDAR_HD_1-0.pdf` (IGN, descriptif de contenu) |
| **Sources secondaires** | ignf.github.io, data.gouv.fr, ign.fr/lidar-hd-detection-changement, GitHub imagodata/IGN_LIDAR_HD_DATASET |
| **Lois fondatrices** | CON-002 (science), CON-005 (traçabilité) |
| **Documents connexes** | `DATASET_CATALOG.md` (DS-002), `GEOSYLVA_UNREAL_ARCHITECTURE.md` (livrable 212), `COMMAND_CENTER_UNREAL.md` (livrable 211), `ENGINE_DATA_SOCLE.md` (livrable 310) |

---

## 1. Objet

Synthèse opérationnelle des spécifications IGN LiDAR HD pour
l'exploitation dans les moteurs GSIE (Forest Dynamics, GIS, Simulation)
et le rendu Unreal/Cesium. Source primaire : descriptif de contenu
officiel IGN (`DC_LiDAR_HD_1-0.pdf`).

---

## 2. Spécifications techniques

| Paramètre | Valeur | Source |
|---|---|---|
| Densité minimale | 10 impulsions / m² (5 au-dessus de 3200 m) | data.gouv.fr |
| Couverture | France métropolitaine + DROM (sauf Guyane), prévu 2026 | IGN |
| Format diffusion | LAZ 1.4 (binaire LAS compressé) | data.gouv.fr |
| Découpage | Dalles 1 km × 1 km (blocs 50 km × 50 km) | data.gouv.fr |
| Poids par dalle | 500 MB à 2 GB | data.gouv.fr |
| Modèles dérivés | MNT, MNS, MNH — pas 50 cm | IGN webinaire |
| SRS | Lambert 93 (EPSG:2154) | Standard IGN |
| Licence | Licence Ouverte 2.0 (etalab-2.0) | IGN |

---

## 3. Classification du nuage de points — 11 catégories

Le nuage LiDAR HD est classé en **11 catégories** : 8 respectant les
valeurs ASPRS (American Society for Photogrammetry and Remote Sensing)
et 3 classes personnalisées IGN.

### 3.1 Classes ASPRS (8)

| Code | Classe | Hauteur | Utilisation GSIE |
|---|---|---|---|
| 2 | Sol (ground) | — | MNT, terrain Hub, hydrologie |
| 3 | Végétation basse | 0 – 50 cm | Combustible strate 1 (Ignis), sous-bois |
| 4 | Végétation moyenne | 50 cm – 1,50 m | Combustible strate 2 (Ignis), régénération |
| 5 | Végétation haute | > 1,50 m | Canopée, dendrométrie (GeoSylva), combustible strate 3 |
| 6 | Bâtiment | — | BD Topo, Centre de Commandement |
| 9 | Eau | — | Hydro, zones humides |
| 17 | Tablier de pont | — | Infrastructures |
| 1 | Non classé / bruit | — | À filtrer |

### 3.2 Classes personnalisées IGN (3)

| Code | Classe | Utilisation GSIE |
|---|---|---|
| — | Sursol pérenne | Murs, quays, ouvrages d'art |
| — | Points virtuels | Points calculés (compléments) |
| — | Divers bâtis | Objets bâtis non standard |

### 3.3 Correspondance avec les strates Ignis

La classification LiDAR HD **mappe directement** sur le modèle de
combustible 3 strates d'Ignis (HUB-002 `ignis.combustible`) :

| Strate Ignis | Classe LiDAR HD | Source |
|---|---|---|
| Strate 1 (0 – 3 m) | Végétation basse (classe 3) + moyenne (classe 4) | DC_LiDAR_HD |
| Strate 2 (3 – 15 m) | Végétation haute (classe 5, sous-canopée) | DC_LiDAR_HD |
| Strate 3 (> 15 m) | Végétation haute (classe 5, canopée) | DC_LiDAR_HD |

> **Implication moteur** : le Simulation Engine (ForeFire) peut
> consommer directement les classes 3-4-5 du nuage classé pour
> construire le modèle de combustible, sans reclassification.

---

## 4. Pipeline IGN de traitement (référence)

L'IGN a publié son pipeline officiel (webinaire 25/09/2025) :

```
Nuage .laz (classé)
    ↓ PDAL (filtrage par classe)
MNH .tif (50 cm, par strate)
    ↓ PostGIS ST_Tile(rast, 5, 5)  → tuiles 1 m²
    ↓ ST_SummaryStats()            → count, mean, min, max
    ↓ Calcul densité = count / 25 × 100
    ↓ ST_DumpAsPolygon()
Hauteurs classées POLYGON + Analyse densité POLYGON
```

### 4.1 Outils IGN

| Étape | Outil | Opération |
|---|---|---|
| Filtrage nuage | PDAL | `--filters.range --limits Classification[2:2]` (sol), etc. |
| Rasterisation | GDAL | `gdal_wrap` (alignement raster sol), `gdal_calc` (MNH = VegH − Sol) |
| Tuilage | PostGIS | `ST_Tile(rast, 5, 5)` → 1 m² |
| Statistiques | PostGIS | `ST_SummaryStats()` → count, mean, min, max |
| Densité | PostGIS | `count / 25 × 100` (points par m²) |
| Vectorisation | PostGIS | `ST_DumpAsPolygon()` |

### 4.2 Implication GSIE

Ce pipeline est directement applicable au **GIS Engine** et **Forest
Dynamics Engine** :

1. **Ingestion** : PDAL pour filtrer les classes ASPRS du LAZ
2. **Rasterisation** : GDAL pour produire MNT/MNS/MNH à 50 cm
3. **Segmentation** : PyCrown / SegmentAnyTreeV2 sur MNH (déjà prévu,
   livrable 212)
4. **Vectorisation** : PostGIS pour polygones de peuplements (déjà
   prévu, `geosylva.peuplements`)
5. **Combustible** : classes 3-4-5 directement pour `ignis.combustible`

---

## 5. Bibliothèque de référence : IGN_LIDAR_HD_DATASET

| Champ | Valeur |
|---|---|
| **Dépôt** | `github.com/sducournau/IGN_LIDAR_HD_DATASET` |
| **Version** | 4.1.2 |
| **Langage** | Python |
| **Accélération** | GPU (CUDA, 10× plus rapide) |
| **Features** | 35-45 features géométriques (normales, courbure, eigenvalues, shape descriptors) |
| **Modes** | LOD2 (12 features, rapide), LOD3 (37 features, détaillé), Full (43+) |
| **Multimodal** | Géométrie + RGB (ortho) + NIR (NDVI) |
| **Sortie** | NPZ, HDF5, PyTorch, LAZ |
| **Classification** | Rules framework extensible, building gap detection |

### 5.1 Pertinence GSIE

- **Forest Dynamics Engine** : features géométriques LOD3 directement
  exploitables pour la segmentation d'arbres individuels
- **Learning Engine** : datasets ML-ready (PyTorch, HDF5) pour
  entraîner des classificateurs d'essences
- **Botanical Engine** : RGB + NIR → NDVI pour discrimination
  essences (complément Crown-BERT)
- **GIS Engine** : spatial indexing (rtree) pour lookup efficace
  des dalles MNT

> **Recommandation** : évaluer cette bibliothèque comme dépendance
  candidate pour le pipeline d'ingestion Phase 4. À sourcer et tester
  sur un département pilote.

---

## 6. Implications pour le rendu Unreal / Cesium

### 6.1 Hub (Centre de Commandement, livrable 211)

| Aspect | Apport LiDAR HD |
|---|---|
| Terrain 3D | MNT 50 cm → Cesium 3D Terrain quantized mesh de haute précision |
| Végétation procédurale | MNH + classes 3-4-5 → PCG Unreal pour placement d'arbres par strate |
| Bâtiments | Classe 6 → 3D Tiles bâtiments (complément BD Topo) |
| Eau | Classe 9 → mesh hydrographique précis |
| Gaussian Splats | Nuage classé → reconstruction splat par strate (canopée, sous-bois) |

### 6.2 GeoSylva (livrable 212)

| Aspect | Apport LiDAR HD |
|---|---|
| Segmentation arbres | MNH 50 cm → PyCrown / SegmentAnyTreeV2 (déjà prévu) |
| Dendrométrie | Hauteur par arbre (MNH), densité (count/m²), structure (3 strates) |
| Cartes peuplements | Polygones PostGIS (hauteur + densité classées) |
| Biomasse | MNT + MNH → volume sur pied → AGB (complément GEDI/ESA) |

### 6.3 Ignis

| Aspect | Apport LiDAR HD |
|---|---|
| Combustible 3 strates | Classes 3-4-5 directement (pas de reclassification) |
| Continuité 0-3 m | Classes 3 + 4 (végétation basse + moyenne) |
| CCF (combustible) | Densité points/m² par strate (PostGIS) |
| Front de feu | MNT 50 cm → simulation ForeFire précise (pente, aspect) |

---

## 7. Cas d'usage IGN validés (référence)

L'IGN a déjà déployé LiDAR HD en production pour :

1. **Détection de changements bâtiments** : vectorisation classe 6
   (TerraScan) → comparaison BD Topo → créations/suppressions
   détectées automatiquement
2. **Mise à jour BD Topo** : bâtiments 3D (toit, mur, emprise) issus
   de la vectorisation
3. **Reculer routes sous canopée** : classe sol (2) sous forêt →
   recalage géométrique
4. **Érosion / glissements de terrain** : comparaison multi-temporelle
   MNT
5. **Densité points sol variable** : Vosges (dense) vs maquis corse
   (clairsemé) → adaptation des paramètres de traitement par région

---

## 8. Recommandations pour la Phase 4

| ID | Recommandation | Moteur / App | Priorité |
|---|---|---|---|
| REC-01 | Pipeline PDAL → GDAL → PostGIS pour ingestion LiDAR HD | GIS Engine | P0 |
| REC-02 | Évaluer `IGN_LIDAR_HD_DATASET` v4.1.2 sur département pilote | Forest Dynamics | P1 |
| REC-03 | Mapper classes 3-4-5 sur strates combustible Ignis | Simulation Engine | P0 |
| REC-04 | MNT 50 cm → Cesium 3D Terrain (Hub) | Hub / GIS | P0 |
| REC-05 | MNH + classes → PCG Unreal placement végétation par strate | Hub / GeoSylva | P1 |
| REC-06 | Polygones PostGIS (hauteur + densité) → `geosylva.peuplements` | Forest Dynamics | P1 |
| REC-07 | RGB + NIR → NDVI pour discrimination essences (Botanical) | Botanical Engine | P2 |
| REC-08 | Adaptation paramètres par région (densité sol variable) | GIS Engine | P2 |

---

## 9. Critères d'acceptation

- [x] Spécifications techniques documentées (densité, format, SRS, licence)
- [x] 11 classes de classification détaillées (8 ASPRS + 3 IGN)
- [x] Correspondance strates Ignis ↔ classes LiDAR établie
- [x] Pipeline IGN officiel documenté (PDAL → GDAL → PostGIS)
- [x] Bibliothèque de référence identifiée (IGN_LIDAR_HD_DATASET v4.1.2)
- [x] Implications Unreal/Cesium définies (Hub, GeoSylva, Ignis)
- [x] Cas d'usage IGN validés référencés
- [x] Recommandations Phase 4 priorisées (8 recommandations)

---

> Statut : *Draft — fiche recherche Phase 3. Source primaire :
> `DC_LiDAR_HD_1-0.pdf` (IGN). Aucun code (CON-003).*

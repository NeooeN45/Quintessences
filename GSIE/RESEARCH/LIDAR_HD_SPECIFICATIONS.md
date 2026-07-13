# Fiche recherche — IGN LiDAR HD : spécifications, classification et pipeline

| Champ | Valeur |
|---|---|
| **Document** | RESEARCH/LIDAR_HD_SPECIFICATIONS |
| **Dossier** | GSIE/RESEARCH/ |
| **Phase** | 4 — Implémentation |
| **Statut** | Draft |
| **Date de création** | 2026-07-13 |
| **Date de révision** | 2026-07-13 (analyse complète des 4 PDFs IGN) |
| **Source primaire** | `GSIE/RESEARCH/DC_LiDAR_HD_1-0.pdf` (IGN, descriptif de contenu v1.0, juillet 2026, 46 pages) |
| **Sources PDF locales** | `DC_LiDAR_HD_1-0.pdf` (descriptif de contenu), `SE_LiDAR_HD.pdf` (suivi des évolutions, juillet 2026), `Offre_Produit_LiDAR_2025-08.pdf` (accès aux produits, août 2025), `Traitements_Produits_LiDAR_2025-08.pdf` (traitements, août 2025) |
| **Sources secondaires** | ignf.github.io, data.gouv.fr, ign.fr/lidar-hd-detection-changement, GitHub imagodata/IGN_LIDAR_HD_DATASET |
| **Lois fondatrices** | CON-002 (science), CON-005 (traçabilité) |
| **Documents connexes** | `DATASET_CATALOG.md` (DS-002), `GEOSYLVA_UNREAL_ARCHITECTURE.md` (livrable 212), `COMMAND_CENTER_UNREAL.md` (livrable 211), `ENGINE_DATA_SOCLE.md` (livrable 310) |

---

## 1. Objet

Synthèse opérationnelle des spécifications IGN LiDAR HD pour
l'exploitation dans les moteurs GSIE (Forest Dynamics, GIS, Simulation)
et le rendu Unreal/Cesium. Basée sur l'analyse complète des 4 documents
officiels IGN (juillet 2026).

---

## 2. Spécifications techniques

| Paramètre | Valeur | Source |
|---|---|---|
| Densité minimale | 10 impulsions / m² (5 au-dessus de 3200 m) | DC §2.3.1.2 |
| Couverture | France métropolitaine + Corse + DROM (sauf Guyane) | DC §1.2 |
| Échéance couverture | Fin 2026 (diffusion complète prévue juin 2026) | Traitements §2 |
| Format nuage | LAZ 1.4 (LAS 1.4 OGC), Point Data Record Format 6 | DC §2.1 |
| Indexation | COPC (Cloud Optimized Point Cloud) | DC §2.5.1 |
| Découpage | Dalles 1 km × 1 km, blocs 50 km × 50 km (238 chantiers) | DC §1.4, §2.5.1 |
| Poids par dalle | 500 MB à 2 GB (nuage) | data.gouv.fr |
| Modèles dérivés | MNT, MNS, MNH — GeoTIFF, pas 50 cm (2000×2000 px/dalle) | DC §3.3 |
| NoData | -9999 | DC §3.3.1.3 |
| SRS métropole | RGF93/Lambert 93 (EPSG:2154), altitude IGN69 | DC §1.3 |
| SRS DROM | Spécifiques par territoire (RGAF09UTM20, MART87, RGR92UTM40S, RGM23UTM38S) | DC §1.3 |
| Licence | Licence Ouverte 2.0 (etalab-2.0) | IGN |
| Nomenclature nuage | `LHD_{ZONE}_{XXXX}_{YYYY}_PTS_{SRC}_{SRV}.copc.laz` | DC §2.5.1 |
| Nomenclature MNx | `LHD_{ZONE}_{XXXX}_{YYYY}_{PROD}_{SRC}_{SRV}.tif` | DC §3.3.1.4 |

### 2.1 Qualité géométrique (contrôles IGN)

| Métrique | Exigence | Exemple constaté | Source |
|---|---|---|---|
| REMQ planimétrique absolue | ≤ 50 cm | 11,7 cm | DC §2.4.1 |
| REMQ altimétrique absolue | ≤ 10 cm | 5,5 cm | DC §2.4.1 |
| Écart moyen tie-lines (altimétrie) | ≤ 5 cm | < 5 cm | DC §2.4.1 |
| Densité (carte 4 m de résolution) | ≥ 10 imp/m² | — | DC §2.4.1 |
| Contrôle classement | 20-30% du chantier | < 1 bâtiment / 1000 mal classé (zone à enjeu) | DC §2.4.2 |

### 2.2 Zones à enjeux (contrôle renforcé)

Définies en DC §2.4.2 :
- **Zones inondables** : emprises MNT LiDAR produits pour la DGPR (2010-2019)
- **Zones urbaines** : couche « Zone d'habitation » BD TOPO® importance 1

> **Implication GSIE** : ces zones correspondent aux périmètres Ignis
> (risque incendie en zone urbaine/péri-urbaine) et Hydro (inondation).
> La qualité de classification y est maximale.

---

## 3. Attributs des points (DC §2.2)

### 3.1 Attributs standards (Point Data Record Format 6)

| Attribut | Usage LiDAR HD |
|---|---|
| X, Y, Z | Position 3D (projection + altitude) |
| Intensity | Intensité du signal retour (0-65536, non homogène entre acquisitions) |
| Return Number | Numéro d'écho |
| Number of Returns | Nombre d'échos pour l'impulsion |
| Classification Flags | Sans objet |
| Scanner Channel | Canal du scanner |
| Scan Direction Flag | Sens de balayage |
| Edge of flight line | Bord de bande |
| Classification | Classe (11 catégories, §4) |
| User Data | Donnée utilisateur (opérateur, non contraint) |
| Scan Angle | Angle de scan (degrés, précision 0,006°) |
| Point Source ID | ID de l'axe de vol |
| GPS Time | Temps GPS |

### 3.2 Attributs Extra Bytes (VLR)

| Attribut | Usage |
|---|---|
| DTM_Marker | Utilisation pour le calcul des MNT |
| DSM_Marker | Utilisation pour le calcul des MNS |
| Origin | Origine du point (acquisition, virtuel, exogène) |

> **Implication moteur** : l'attribut `Origin` permet de distinguer
> les points acquis (LiDAR) des points virtuels (code 66) et exogènes
> (RGE ALTI®). Utile pour le contrôle qualité dans le pipeline GSIE.

### 3.3 Intensité du signal (DC §2.2.2)

Valeur 0-65536, **non homogène** entre acquisitions et axes de vol.
Dépend de : puissance d'émission, réflectivité du terrain, angle
d'incidence, conditions atmosphériques, traitements.

> **Implication Botanical Engine** : l'intensité peut aider à
> discriminer les essences (réflectivité différente) mais nécessite
> une normalisation par axe de vol. À utiliser avec précaution
> (CON-005 : niveau de preuve à qualifier).

---

## 4. Classification du nuage de points — 11 catégories

### 4.1 Classes ASPRS (8) — DC §2.2.8

| Code | Classe | Définition IGN | Hauteur | Utilisation GSIE |
|---|---|---|---|---|
| 1 | Non classé | Véhicules, personnes, animaux, objets transitoires (grues, tas de bois/fumier/betteraves, bottes de foin), dépôts agricoles, tas de terre/sable/gravier, carrières, zones de travaux | — | À filtrer (bruit) |
| 2 | Sol | Surface du sol nu (y compris herbe < 20 cm) | — | MNT, terrain Hub, hydrologie, recalage routes sous canopée |
| 3 | Végétation basse | Arbustes, garrigue, fougères, roselière, arbres de culture (vergers, vignes) | 0 – 50 cm | Combustible strate 1 (Ignis), régénération, sous-bois |
| 4 | Végétation moyenne | Idem classe 3 | 50 cm – 1,50 m | Combustible strate 1-2 (Ignis), régénération |
| 5 | Végétation haute | Arbres, arbustes, formations végétales | > 1,50 m | Canopée, dendrométrie (GeoSylva), combustible strate 2-3 (Ignis) |
| 6 | Bâtiment | Toits + façades, constructions pérennes (résidentiel, agricole, industriel, commercial, religieux, sportif). Inclut cheminées, lucarnes, verrières, balcons, terrasses. Monuments, châteaux, moulins, phares, cheminées industrielles, remparts. | — | BD Topo, Centre de Commandement, 3D Tiles bâtiments |
| 9 | Eau | Surface cours d'eau, plans d'eau, mer, océan. ⚠️ **DÉFICIT de points** : nombreuses impulsions sur l'eau non perceptibles par le capteur | — | Hydro (avec gestion du déficit) |
| 17 | Tablier de pont | Tablier des ponts (toute largeur). Inclut passerelles piétonnes. Piles/parapets → Non classé. Haubans/piiliers > 5m → Sursol pérenne | — | Infrastructures |

### 4.2 Classes personnalisées IGN (3) — DC §2.2.8

| Code | Classe | Définition IGN | Utilisation GSIE |
|---|---|---|---|
| 64 | Sursol pérenne | Éoliennes, téléphériques, antennes, câbles électriques, pylônes, caténaires, haubans de ponts. **Exclut** véhicules, personnes, animaux, objets transitoires | Infrastructures critiques (Ignis : lignes électriques = risque) |
| 66 | Points Virtuels | Points artificiels sur lignes de rupture de pente sous ponts + grilles 50 cm sur cours d'eau > 5 m (altitude interpolée depuis bord) | MNT précis sous ponts, hydro surfacique |
| 67 | Divers bâtis | Bâtiments incertains (degré de certitude < classe 6). Haies taillées, pins parasols, rochers, terrasses, cabanes, caravanes, bungalows, bâtiments atypiques | À valider (Botanical/GIS) |

### 4.3 Correspondance avec les strates Ignis

| Strate Ignis | Classes LiDAR HD | Source |
|---|---|---|
| Strate 1 (0 – 3 m) | 3 (vég. basse) + 4 (vég. moyenne) | DC §2.2.8.3 |
| Strate 2 (3 – 15 m) | 5 (vég. haute, sous-canopée) | DC §2.2.8.3 |
| Strate 3 (> 15 m) | 5 (vég. haute, canopée) | DC §2.2.8.3 |

> **Implication moteur** : le Simulation Engine (ForeFire) peut
> consommer directement les classes 3-4-5 du nuage classé pour
> construire le modèle de combustible, **sans reclassification**.
> La séparation strate 2 / strate 3 au sein de la classe 5 se fait par
> seuil de hauteur (MNH = MNS − MNT).

### 4.4 Points d'attention pour les moteurs

| Point | Détail | Source | Moteur concerné |
|---|---|---|---|
| Déficit points sur eau | Impulsions LiDAR non perceptibles sur plans d'eau → trous dans le nuage | DC §2.2.8.5 | Hydro, GIS |
| Végétation < 20 cm = Sol | Herbe classée en sol (non mesurable avec précision) | DC §2.2.8.3 | Forest Dynamics, Ignis |
| Arbres de culture inclus | Vergers et vignes classés en végétation (3-4-5) | DC §2.2.8.3 | Botanical (à filtrer pour forêt) |
| Bâtiments ruinés sans toit | Traités comme murs → Non classé (code 1) | DC §2.2.8.4 | GIS |
| Divers bâtis (67) incertain | Degré de certitude < classe 6, peut inclure végétation | DC §2.2.8.9 | Botanical, GIS |
| Sursol pérenne = lignes électriques | Code 64 inclut câbles et pylônes → **risque incendie** | DC §2.2.8.7 | Ignis (détection de risque) |

---

## 5. Accès aux données (Offre_Produit_LiDAR_2025-08.pdf)

### 5.1 Nuages de points — 3 modes d'accès

| Mode | Format | Détail | Source |
|---|---|---|---|
| Téléchargement | COPC.LAZ | Dalles 1 km × 1 km via cartes.gouv.fr | Offre §2.1 |
| Flux/streaming | COPC.LAZ en streaming | Fichier texte référençant les dalles, exploitable dans QGIS | Offre §2.2 |
| Visionneuse | Web | Outil IGN de visualisation interactive des nuages classés | Offre §2.3 |

### 5.2 Flux nuage — format EPT (DC §2.5.2)

| Format | URL | Source |
|---|---|---|
| VPC (Virtual Point Cloud) | `https://data.geopf.fr/chunk/telechargement/download/lidarhd_fxx_ept/vpc/index.vpc` | DC §2.5.2 |
| EPT (Entwine Point Tiles) | Alternative au COPC pour grandes quantités en cloud | DC §2.5.2 |

> **Implication Hub** : le format EPT/VPC permet le streaming direct
> du nuage de points dans Cesium (Cesium Ion ou EPT loader). Pas besoin
> de télécharger localement pour le rendu Hub.

### 5.3 Modèles numériques (MNT/MNS/MNH)

| Mode | Format | Détail | Source |
|---|---|---|---|
| Téléchargement | GeoTIFF | Dalles 1 km × 1 km, 50 cm, 32 bits | Offre §3.1, DC §3.3 |
| WMS-Raster | GeoTIFF/PNG/JPEG | `IGNF_LIDAR-HD_{PROD}_ELEVATIONGRIDCOVERAGE.{SRC}` | Offre §3.2, DC §3.3.2 |
| WMS ombrages | PNG | `IGNF_LIDAR-HD_{PROD}_ELEVATIONGRIDCOVERAGE.shadow` | DC §3.3.2 |
| API Calcul Altimétrique | REST | `ign_lidar_hd_mnt_multi_wld`, `ign_lidar_hd_mnx_multi_wld` | Offre §3.3 |

### 5.4 Couches WMS disponibles

| ID | Couche | Projection |
|---|---|---|
| 121 | MNH LAMB93 | Métropole |
| 132 | MNS LAMB93 | Métropole |
| 143 | MNT LAMB93 | Métropole |
| 124/135/146 | MNH/MNS/MNT RGR92UTM40S | Réunion |
| 129/140/151 | MNH/MNS/MNT WGS84G | Mondial (reprojeté) |

> **Implication Hub** : les couches WMS ombrages peuvent être
> directement utilisées comme couche de relief dans Cesium
> (ImageryLayer WMS). Les couches GeoTIFF (GetMap) peuvent être
> drapées sur le terrain 3D.

### 5.5 API Calcul Altimétrique

4 ressources connectées au service Géoplateforme :

| Ressource | Description |
|---|---|
| `ign_lidar_hd_mnt_multi_wld` | Altitude terrain (multi-pyramides, projection native) |
| `ign_lidar_hd_mnt_mono_wld` | Altitude terrain (pyramide unique, WGS84) |
| `ign_lidar_hd_mnx_multi_wld` | Altitudes terrain + sursol + hauteur (multi-pyramides) |
| `ign_lidar_hd_mnx_mono_wld` | Idem (pyramide unique, WGS84) |

> **Implication Simulation Engine** : l'API altimétrique permet à
> ForeFire de récupérer l'altitude du terrain en temps réel pour
> n'importe quel point, sans télécharger les dalles. Utile pour la
> simulation de propagation (pente, aspect).

---

## 6. Traitements et versions (Traitements_Produits_LiDAR_2025-08.pdf)

### 6.1 Statuts de diffusion (août 2025)

| Statut | Description |
|---|---|
| Version finale | Dernier processus de production IGN |
| Sous-traitée finale | Classée par sous-traitant, qualité équivalente |
| Version intermédiaire | Version antérieure, en attente de mise à jour |

### 6.2 Calendrier de diffusion

| Échéance | Périmètre |
|---|---|
| 30 septembre 2025 | Vague 1 |
| 31 décembre 2025 | Vague 2 |
| 31 mars 2026 | Vague 3 |
| 30 juin 2026 | **Diffusion complète** |

### 6.3 Améliorations de la version finale

| Amélioration | Impact GSIE |
|---|---|
| Classification végétation en zones ombrées | Forest Dynamics : meilleure segmentation sous canopée dense |
| Classification grands bâtiments | GIS : bâtiments 3D plus précis |
| Classification serres et vergers | Botanical : distinction serres/vergers améliorée |
| Classification de l'eau | Hydro : moins de faux négatifs sur plans d'eau |
| Saisie manuelle tabliers de pont | GIS : ponts correctement classés (code 17) |

> **Important** : la version finale est la **seule** utilisée pour
> calculer les MNT/MNS/MNH. Temporairement, la version du nuage
> diffusé peut différer de celle ayant servi aux MNx.

---

## 7. Pipeline IGN de traitement (référence)

L'IGN a publié son pipeline officiel (webinaire 25/09/2025) :

```
Nuage .laz (classé, COPC)
    ↓ PDAL (filtrage par classe ASPRS)
MNH .tif (50 cm, par strate)
    ↓ PostGIS ST_Tile(rast, 5, 5)  → tuiles 1 m²
    ↓ ST_SummaryStats()            → count, mean, min, max
    ↓ Calcul densité = count / 25 × 100
    ↓ ST_DumpAsPolygon()
Hauteurs classées POLYGON + Analyse densité POLYGON
```

### 7.1 Outils IGN

| Étape | Outil | Opération |
|---|---|---|
| Filtrage nuage | PDAL | `--filters.range --limits Classification[2:2]` (sol), etc. |
| Rasterisation | GDAL | `gdal_wrap` (alignement raster sol), `gdal_calc` (MNH = VegH − Sol) |
| Tuilage | PostGIS | `ST_Tile(rast, 5, 5)` → 1 m² |
| Statistiques | PostGIS | `ST_SummaryStats()` → count, mean, min, max |
| Densité | PostGIS | `count / 25 × 100` (points par m²) |
| Vectorisation | PostGIS | `ST_DumpAsPolygon()` |
| Vectorisation bâtiments | TerraScan | Volumes 3D (toit, mur, emprise) |

### 7.2 Implication GSIE

Ce pipeline est directement applicable au **GIS Engine** et **Forest
Dynamics Engine** :

1. **Ingestion** : PDAL pour filtrer les classes ASPRS du LAZ (COPC)
2. **Rasterisation** : GDAL pour produire MNT/MNS/MNH à 50 cm
3. **Segmentation** : PyCrown / SegmentAnyTreeV2 sur MNH (livrable 212)
4. **Vectorisation** : PostGIS pour polygones de peuplements
   (`geosylva.peuplements`)
5. **Combustible** : classes 3-4-5 directement pour `ignis.combustible`
6. **Streaming** : EPT/VPC pour rendu Hub sans téléchargement local

---

## 8. Bibliothèque de référence : IGN_LIDAR_HD_DATASET

| Champ | Valeur |
|---|---|
| **Dépôt** | `github.com/sducournau/IGN_LIDAR_HD_DATASET` |
| **Version** | 4.1.2 |
| **Langage** | Python |
| **Accélération** | GPU (CUDA, 10× plus rapide), async processing (10-20% speedup) |
| **Features** | 35-45 features géométriques (normales, courbure, eigenvalues, shape descriptors, architectural features) |
| **Modes** | LOD2 (12 features, rapide), LOD3 (37 features, détaillé), Full (43+) |
| **Multimodal** | Géométrie + RGB (ortho) + NIR (NDVI) |
| **Sortie** | NPZ, HDF5, PyTorch, LAZ |
| **Classification** | Rules framework extensible, building gap detection, spatial indexing (rtree) |
| **Sécurité** | GPU OOM prevention, pre-flight checks |

### 8.1 Pertinence GSIE

- **Forest Dynamics Engine** : features géométriques LOD3 pour
  segmentation d'arbres individuels
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

## 9. Implications pour le rendu Unreal / Cesium

### 9.1 Hub (Centre de Commandement, livrable 211)

| Aspect | Apport LiDAR HD | Source |
|---|---|---|
| Terrain 3D | MNT 50 cm → Cesium 3D Terrain quantized mesh haute précision | DC §3.3 |
| Végétation procédurale | MNH + classes 3-4-5 → PCG Unreal placement par strate | DC §2.2.8.3 |
| Bâtiments | Classe 6 → 3D Tiles bâtiments (complément BD Topo) | DC §2.2.8.4 |
| Eau | Classe 9 → mesh hydrographique (⚠️ déficit points) | DC §2.2.8.5 |
| Infrastructures | Classe 64 (sursol pérenne) → lignes électriques, éoliennes, antennes | DC §2.2.8.7 |
| Gaussian Splats | Nuage classé → reconstruction splat par strate (canopée, sous-bois) | — |
| Streaming nuage | EPT/VPC → Cesium EPT loader (pas de téléchargement local) | DC §2.5.2 |
| Ombrages relief | WMS `.shadow` → couche d'imagerie Cesium | DC §3.3.2 |
| API altimétrique | REST → altitude terrain temps réel pour interaction 3D | Offre §3.3 |

### 9.2 GeoSylva (livrable 212)

| Aspect | Apport LiDAR HD | Source |
|---|---|---|
| Segmentation arbres | MNH 50 cm → PyCrown / SegmentAnyTreeV2 | DC §3.3 |
| Dendrométrie | Hauteur par arbre (MNH), densité (count/m²), structure (3 strates) | DC §2.2.8.3 |
| Cartes peuplements | Polygones PostGIS (hauteur + densité classées) | Pipeline IGN §7 |
| Biomasse | MNT + MNH → volume sur pied → AGB (complément GEDI/ESA) | — |
| Essences | Intensité du signal (normalisée) + RGB/NIR → discrimination | DC §2.2.2, IGN_LIDAR_HD_DATASET |

### 9.3 Ignis

| Aspect | Apport LiDAR HD | Source |
|---|---|---|
| Combustible 3 strates | Classes 3-4-5 directement (pas de reclassification) | DC §2.2.8.3 |
| Continuité 0-3 m | Classes 3 + 4 (vég. basse + moyenne) | DC §2.2.8.3 |
| CCF (combustible) | Densité points/m² par strate (PostGIS) | Pipeline IGN §7 |
| Front de feu | MNT 50 cm → ForeFire précis (pente, aspect) | DC §3.3 |
| API altimétrique | REST → altitude temps réel pour simulation | Offre §3.3 |
| Lignes électriques | Classe 64 → détection risque (départ incendie) | DC §2.2.8.7 |
| Zones ombrées | Version finale : meilleure classification végétation | Traitements §3 |

---

## 10. Métadonnées (DC §4)

### 10.1 Métadonnées sémantiques (polygones par dalle)

| Attribut | Définition |
|---|---|
| coordonnees_NW | Coordonnées kilométriques coin NW (XXXX-YYYY) |
| url_npl | URL fichier nuage de points |
| url_mnt | URL fichier MNT |
| url_mns | URL fichier MNS |
| url_mnh | URL fichier MNH |
| systeme_planimetrique | Code IGNF projection |
| systeme_altimetrique | Code IGNF altitude |

> **Implication GIS Engine** : les métadonnées par dalle permettent
> de construire un index spatial pour localiser rapidement les dalles
> disponibles sans téléchargement. Utile pour le tuilage dynamique
> du Hub.

---

## 11. Cas d'usage IGN validés (référence)

L'IGN a déjà déployé LiDAR HD en production pour :

1. **Détection de changements bâtiments** : vectorisation classe 6
   (TerraScan) → comparaison BD Topo → créations/suppressions
   détectées automatiquement (DC §ign.fr/lidar-hd-detection-changement)
2. **Mise à jour BD Topo** : bâtiments 3D (toit, mur, emprise) issus
   de la vectorisation
3. **Reculer routes sous canopée** : classe sol (2) sous forêt →
   recalage géométrique
4. **Érosion / glissements de terrain** : comparaison multi-temporelle
   MNT
5. **Densité points sol variable** : Vosges (dense) vs maquis corse
   (clairsemé) → adaptation paramètres par région
6. **Inondation** : traitements complémentaires (digues, cours d'eau,
   ponts) pour modélisation hydraulique (DC §2.3.2.3)

---

## 12. Recommandations pour la Phase 4

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
| REC-09 | Streaming EPT/VPC → Cesium EPT loader (pas de téléchargement) | Hub | P1 |
| REC-10 | API Calcul Altimétrique → ForeFire (altitude temps réel) | Simulation Engine | P1 |
| REC-11 | Classe 64 (sursol pérenne) → détection lignes électriques (Ignis) | Ignis / GIS | P1 |
| REC-12 | WMS ombrages → couche d'imagerie Cesium (relief) | Hub | P2 |
| REC-13 | Métadonnées par dalle → index spatial GIS Engine | GIS Engine | P1 |
| REC-14 | Gestion NoData (-9999) dans le pipeline (ZICAD + eau) | GIS / Hydro | P0 |
| REC-15 | Normalisation intensité par axe de vol (Botanical) | Botanical Engine | P2 |

---

## 13. Critères d'acceptation

- [x] Spécifications techniques documentées (densité, format, SRS, licence, qualité)
- [x] 11 classes de classification détaillées avec codes ASPRS précis (1,2,3,4,5,6,9,17,64,66,67)
- [x] Définitions IGN complètes par classe (inclusions, exclusions, points d'attention)
- [x] Attributs des points documentés (13 standards + 3 Extra Bytes)
- [x] Correspondance strates Ignis ↔ classes LiDAR établie
- [x] Pipeline IGN officiel documenté (PDAL → GDAL → PostGIS, TerraScan)
- [x] Accès aux données détaillé (téléchargement COPC, flux EPT/VPC, WMS, API altimétrique)
- [x] Couches WMS référencées (LAMB93, RGR92UTM40S, WGS84G + ombrages)
- [x] Traitements et versions documentés (calendrier, améliorations version finale)
- [x] Bibliothèque de référence identifiée (IGN_LIDAR_HD_DATASET v4.1.2)
- [x] Implications Unreal/Cesium définies (Hub, GeoSylva, Ignis)
- [x] Cas d'usage IGN validés référencés (6 cas)
- [x] Métadonnées par dalle documentées
- [x] Recommandations Phase 4 priorisées (15 recommandations)
- [x] Points d'attention moteurs identifiés (déficit eau, vég < 20cm = sol, vergers, divers bâtis)

---

> Statut : *Draft — fiche recherche Phase 4. Sources primaires :
> 4 PDFs IGN officiels (DC, SE, Offre, Traitements — juillet 2026).
> Aucun code (CON-003).*

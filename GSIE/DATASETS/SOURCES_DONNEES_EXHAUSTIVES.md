# Sources de Données — Liste Exhaustive GSIE

> **Livrable** : Note de référence — Phase 4
> **Date de création** : 2026-07-17
> **Auteur** : Cascade (pair programming)
> **Source** : Synthèse de `DATASET_CATALOG.md`, `IGNIS_DATA_PIPELINE.md`, `ENGINE_DATA_SOCLE.md`, `SOURCING_PLAN.md`, `GIS_ENGINE.md` + recherches web complémentaires (juillet 2026)
> **Statut** : Document de référence

---

## 1. Catalogue principal des datasets (DS-001 à DS-029)

> Source : `GSIE/DATASETS/DATASET_CATALOG.md`

### Catégorie A — Forestier

| ID | Nom | Producteur | Résolution | Licence | Moteurs |
|---|---|---|---|---|---|
| **DS-001** | BD Forêt v2 | IGN | Polygones 500 m² min | Licence Ouverte 2.0 | GIS, Forest Dynamics, Diagnostic |
| **DS-002** | LiDAR HD (MNT/MNS/MNH + nuages de points) | IGN | 50 cm rasters, ~10 pts/m² | Licence Ouverte 2.0 | GIS, Forest Dynamics, Simulation, Ignis |
| **DS-003** | Inventaire Forestier National (placettes permanentes) | IGN | Placettes 20 m rayon, maille ~2 km | Licence Ouverte 2.0 | Forest Dynamics, Correlation, Learning |
| **DS-004** | BD Ortho (imagerie aérienne) | IGN | 20-50 cm | Licence Ouverte 2.0 | GIS, Diagnostic |
| **DS-005** | RPF — Référentiel Pédologique Forestier | ONF/INRAE | Station/parcelle | Accord ONF (à formaliser) | Pedology, Diagnostic, Recommendation |
| **DS-006** | SOERE F-ORE-T (sites expérimentaux long terme) | INRAE | Placette/arbre | Accord SOERE | Forest Dynamics, Correlation, Learning |

### Catégorie B — Climatique

| ID | Nom | Producteur | Résolution | Licence | Moteurs |
|---|---|---|---|---|---|
| **DS-007** | Safran (analyse spatialisée quotidienne) | Météo-France | Maille 8 km | Accord Météo-France | Climate, Simulation, Forest Dynamics |
| **DS-008** | DRIAS (projections climatiques régionalisées) | Météo-France | 8-12 km | Licence Ouverte 2.0 | Climate, Simulation |
| **DS-009** | ARPEGE / AROME (modèles atmosphériques) | Météo-France | AROME 1.3 km | Accord Météo-France | Climate, Simulation, Ignis |
| **DS-010** | Observations sol (postes climatiques) | Météo-France | Ponctuel (~3000 postes) | Licence Ouverte 2.0 | Climate, Correlation |

### Catégorie C — Pédologique

| ID | Nom | Producteur | Résolution | Licence | Moteurs |
|---|---|---|---|---|---|
| **DS-011** | BDAT (analyses de terre) | INRAE/GIS Sol | Canton | Licence Ouverte 2.0 | Pedology, Correlation, Diagnostic |
| **DS-012** | RPFR (Référentiel Pédologique Forestier Régional) | ONF/INRAE | Station | Accord ONF | Pedology, Diagnostic |
| **DS-013** | SoilGrids (cartographie mondiale des sols) | ISRIC | 250 m | CC-BY 4.0 | Pedology, GIS |

### Catégorie D — Taxonomique / Biodiversité

| ID | Nom | Producteur | Résolution | Licence | Moteurs |
|---|---|---|---|---|---|
| **DS-014** | GBIF (occurrences taxonomiques) | GBIF | Ponctuel | Variable par occurrence | Botanical, Correlation, Diagnostic |
| **DS-015** | Tela Botanica (observations flore) | Tela Botanica | Ponctuel | CC-BY-SA | Botanical, Correlation |
| **DS-016** | BDNFF (nomenclature flore de France) | Tela Botanica/SBF | Référentiel | CC-BY | Botanical, Knowledge |
| **DS-017** | INPN (patrimoine naturel) | MNHN | Ponctuel + zonages | Licence Ouverte 2.0 | Botanical, Diagnostic, Correlation |

### Catégorie E — Satellite / Télédétection

| ID | Nom | Producteur | Résolution | Licence | Moteurs |
|---|---|---|---|---|---|
| **DS-018** | Sentinel-2 (optique multispectral) | ESA/Copernicus | 10 m / 5 jours | CC-BY 4.0 | GIS, Forest Dynamics, Diagnostic, Ignis |
| **DS-019** | Sentinel-1 (radar C-SAR) | ESA/Copernicus | 10 m / 6 jours | CC-BY 4.0 | GIS, Forest Dynamics |
| **DS-020** | Landsat 8/9 (multispectral) | USGS/NASA | 30 m / 8 jours | Domaine public | GIS, Forest Dynamics |
| **DS-021** | MODIS (NDVI/EVI végétation globale) | NASA | 250 m-1 km / 16 jours | Domaine public | GIS, Climate, Forest Dynamics |

### Catégorie F — Incendie

| ID | Nom | Producteur | Résolution | Licence | Moteurs |
|---|---|---|---|---|---|
| **DS-022** | Prométhée (incendies méditerranéens) | Entente Forêt Méditerranéenne | Polygone | Accord | Ignis, Simulation, Diagnostic |
| **DS-023** | EFFIS (système européen feux) | JRC (Commission européenne) | 250 m-20 m | CC-BY 4.0 | Ignis, Simulation |
| **DS-024** | MODIS/FIRMS (détection active fire) | NASA | 375 m-1 km / quasi temps réel | Domaine public | Ignis, Simulation |

### Catégorie G — Biomasse spatiale

| ID | Nom | Producteur | Résolution | Licence | Moteurs |
|---|---|---|---|---|---|
| **DS-025** | GEDI L4A/L4B (biomasse aérienne spatiale) | NASA/Univ. Maryland | Footprint 25 m / grille 1 km | Domaine public | Forest Dynamics, Correlation, GIS |
| **DS-026** | ESA Biomass CCI v7 (cartes globales biomasse) | ESA (CCI) | 100 m / annuelle | OGL / CC-BY 4.0 | Forest Dynamics, Correlation, GIS |

### Catégorie H — IA / Occupation du sol

| ID | Nom | Producteur | Résolution | Licence | Moteurs |
|---|---|---|---|---|---|
| **DS-027** | CoSIA (couverture du sol par IA) | IGN | 20 cm | Licence Ouverte 2.0 | Forest Dynamics, GIS, Botanical, Ignis |
| **DS-028** | OCS GE (occupation du sol grande échelle) | IGN | Grande échelle | Licence Ouverte 2.0 | GIS, Forest Dynamics, Hydro, Ignis |
| **DS-029** | Datasets apprentissage LiDAR HD | IGN | Nuages de points classés | Licence Ouverte 2.0 | Learning, Botanical, Forest Dynamics |

---

## 2. Sources additionnelles du pipeline Ignis

> Source : `GSIE/ARCHITECTURE/IGNIS_DATA_PIPELINE.md`

### 2.1 Topographie et géospatial

| Source | Type | Résolution | Licence | Usage |
|---|---|---|---|---|
| **BD TOPO / BD TOPO Express** (IGN) | Bâtiments, infrastructures, transport 3D | Métrique | Licence Ouverte 2.0 | Analyse d'enjeux (J-06) |
| **Atlas DFCI** | Pistes, points d'eau, massifs | Variable | Open data | Accès terrain, cartographie |
| **OpenStreetMap + BAN** | Sentiers, campings, adressage | Variable | ODbL / open | Compléments enjeux (D-17) |
| **OSO / CESBIO (Theia)** | Occupation des sols France | 10 m | Open data | Complément combustible (D-15) |
| **API Géoplateforme IGN** | BD Ortho, BD Topo, RGE ALTI, OCS-GE, RPG | Variable | Open data | Couches de référence |
| **API Carto — Cadastre** (IGN) | Limites parcellaires (PCI) | Métrique | Open data | Cadastre |
| **API Calcul altimétrique** (IGN) | Altitude points/profils | RGE ALTI / BD ALTI | Open data | Altitude, MNT |
| **BD ALTI** (IGN) | MNT raster | 5 m-25 m | Licence Ouverte 2.0 | Topographie |
| **BD Carthage** (IGN) | Référentiel hydrographique national | Variable | Open data | Hydrographie, cours d'eau |

### 2.2 Météorologiques

| Source | Type | Résolution | Licence | Usage |
|---|---|---|---|---|
| **ERA5** (Copernicus Climate) | Réanalyses historiques | ~30 km | Open data | Entraînement feux historiques (J-08) |
| **Méso-NH** (CNRS/Météo-France) | Météo haute résolution | Variable | Recherche | Couplage feu→atmosphère (pyroconvection) |
| **CorrDiff / FourCastNet 3** (NVIDIA Earth-2) | Météo IA, descente d'échelle | 25 km → 2 km | Open (modèles) | Vent hyper-local sur relief (M-09, M-12) |
| **AIFS** (ECMWF) | Météo IA fondation | Variable | Open | Benchmark météo IA (M-10) |
| **GenCast** (DeepMind) | Météo IA fondation | Variable | Open | Benchmark météo IA (M-10) |
| **Aurora** (Microsoft) | Météo IA fondation | Variable | Open | Benchmark météo IA (M-10) |

### 2.3 Satellite — observation de la Terre

| Source | Type | Résolution / revisite | Licence | Usage |
|---|---|---|---|---|
| **Copernicus EMS** | Contours validés de feux | Variable (post-événement) | Open | Vérité terrain validation (J-08) |
| **Sentinel-3** (ESA) | Thermique | 1 km / ~1 jour | Open | Détections thermiques quasi temps réel |
| **Météosat MTG-FCI** (EUMETSAT) | Géostationnaire thermique | ~2 km / ~10 min | Open | Pré-alerte satellite haute fréquence (D-11) |
| **Google FireSat / EFA** | Constellation dédiée feu | 5 m / ≤20 min | À négocier | Détection précoce satellite (K-01, pilote 2026) |
| **EFFIS / GWIS** (JRC) | Recensement feux UE | Variable | Open | Complément européen (D-10) |

### 2.4 Incendie historiques

| Source | Type | Couverture | Licence | Usage |
|---|---|---|---|---|
| **BDIFF** | Base officielle feux France | Depuis 1973 | Open | Colonne vertébrale feux historiques + causes (D-08) |
| **feuxdeforet.fr** | Événements validés géolocalisés | France, saison | À qualifier | Étiquettes + signalements citoyens (D-07) |
| **WildfireSpreadTS** | Séries temporelles propagation | International | Open | Simulation / apprentissage |

### 2.5 DFCI et infrastructure

| Source | Type | Licence | Usage |
|---|---|---|---|
| **GIP ATGeRi / PIGMA** | Données DFCI Aquitaine (pistes, points d'eau, massifs) | Partenariat | Partenaire données régional (D-09) |
| **Réseaux RTE / Enedis** | Lignes électriques | Open data | Cause d'ignition + enjeu à protéger (D-16) |
| **ANFR Cartoradio** | Positions émetteurs radio | Open data | Couverture radio / déconfliction (G-12) |

### 2.6 Capteurs sol et citoyens

| Source | Type | Licence | Usage |
|---|---|---|---|
| **Stations Meshtastic solaires** | Capteurs sol LoRa (T°, humidité, particules) | Propriétaire | Maillage territorial low-cost (C-04) |
| **sensor.community** | Capteurs citoyens particules/T° | Open data | Préfiguration du maillage (D-18) |
| **Météorage / Blitzortung** | Détections de foudre | Payant / communautaire | Cause d'ignition, surveillance post-orage (D-13) |
| **CAMS** (Copernicus Atmosphère) | Modélisation panaches/qualité air | Open | Validation panache + impact sanitaire (D-14) |

### 2.7 Datasets d'entraînement IA

| Dataset | Type | Licence | Usage |
|---|---|---|---|
| **Pyro-SDIS** (data.gouv.fr) | Images réelles feux France | Open | Entraînement / validation (D-01) |
| **FLAME / FLAME2** | Spectres / images feux | Open | Caractérisation |
| **D-Fire** | Images feu de forêt | Open | Détection |
| **FASDD** | Fumée et flammes aériennes | Open | Détection drone |
| **FIgLib** | Incendies généralistes | Open | Benchmark |
| **links-ads/wildfires-cems** | Segmentation surfaces brûlées Europe | CC-BY | Apprentissage (M-15) |
| **links-ads/effis-wildfire** | Sentinel-2 × EFFIS | Open | Apprentissage (M-15) |
| **TheRootOf3/next-day-wildfire-spread** | Série temporelle (xarray) | Open | Simulation / apprentissage |
| **Google FireBench** | Benchmark ML incendie | Open | Émulateur (M-16) |

### 2.8 Données synthétiques

| Source | Méthode | Usage |
|---|---|---|
| **GCS-Cinéma (Unreal/Niagara)** | Rendu photoréaliste géoréférencé de feux | Images aériennes annotées, vérité terrain (D-05) |
| **Gazebo** | Rendu physique (fumée lointaine) | Détections simulées bruitées (banc) |
| **Isaac Sim** (NVIDIA) | Synthèse photoréaliste massive | Synergie Jetson, phase 4+ |

### 2.9 Capteurs drone (temps réel)

| Capteur | Type | Données produites | Latence |
|---|---|---|---|
| **RGB (caméra optique)** | Vidéo H.264/H.265 | Flux vidéo, détection YOLO fumée/flamme | < 100 ms (edge) |
| **Thermique LWIR (radiométrique)** | Température par pixel (Kelvin) | Anomalies thermiques, intensité front (kW/m) | < 100 ms (edge) |
| **Capteurs atmosphériques drone** | CO/CO₂, particules, T°, hygrométrie | Composition air, qualité atmosphère | < 30 s |
| **GPS / IMU** | Position, attitude, vent par dérive | Lat/lon/alt, quaternions RPY, vent estimé | Temps réel |

---

## 3. Sources scientifiques et référentiels (Sourcing Plan)

> Source : `GSIE/RESEARCH/SOURCING_PLAN.md` — 64 sources sur 17 semaines

### 3.1 Vague 0 — Backbone méthodologique

| Source | Type | Domaine | Licence |
|---|---|---|---|
| Sacks et al. (2023) — Frameworks d'évidence | Peer-reviewed | Méthodologie | CC-BY |
| Pullin et al. (2018) — Collaboration for Environmental Evidence | Peer-reviewed | Méthodologie | CC-BY |
| GRADE — Grading of Recommendations Assessment | Référentiel | Méthodologie | Domaine public |
| Standards ontologiques OWL/RDF (W3C) | Référentiel | Informatique | Domaine public |
| Baize & Jabiol (2008) — RPF INRAE | Référentiel | Pédologie | Accord INRAE |
| Rameau et al. (2008) — Flore forestière française (3 tomes) | Ouvrage | Écologie | IDF |

### 3.2 Vague 1 — Moteurs domaine

**Botanical Engine :**
- Rameau et al. (2008) — Flore forestière française (3 tomes)
- GBIF — Backbone Taxonomic
- BDNFF — Base Nomenclaturale Flore de France
- Tela Botanica — eFlore
- APG IV (2016) — classification phylogénétique
- Tutin et al. — Flora Europaea
- Boullet et al. — Référentiel des habitats forestiers

**Pedology Engine :**
- Baize & Jabiol (2008) — RPF INRAE
- IUSS WRB (2015) — Base de référence mondiale des sols
- INRAE — BDAT
- BRGM — Cartographie géologique 1/50000
- Gobin et al. — Pédologie forestière française
- Legros — Les sols acides

**Climate Engine :**
- Météo-France — Safran, DRIAS, ARPEGE/AROME
- Ozenda (1982/2002) — Végétation de la chaîne alpine
- Badeau et al. (2004) — Changement climatique et forêts
- Chebbi et al. — DRIAS scenarios

**GIS Engine :**
- IGN — BD Forêt v2, LiDAR HD, BD Ortho, BD ALTI
- Copernicus — Sentinel-2
- USGS/NASA — Landsat 8/9

### 3.3 Vague 2 — Correlation & Reasoning

- ONF — Guides sylvicoles par région
- CRPF — Fiches techniques de choix d'essences
- Gégout et al. — EcoPlant (écologie des plantes forestières, INRAE)
- Piedallu et al. — Distribution des essences et climat
- Nageleisen — Santé des forêts (DSF)

### 3.4 Vague 3 — Diagnostic & Forest Dynamics

- ONF-FFN — Modèles de croissance (2019)
- INRAE — CAPSIS (modèles de dynamique)
- Deleuze et al. — Modèle de croissance hêtre/douglas
- Dhôte — Modèles de croissance futaies régulières
- Bouchon — Structure et dynamique des peuplements
- DSF — Bilan annuel santé des forêts (ONF)
- INRAE — Chalarose du frêne

### 3.5 Vague 4 — Simulation, Recommendation, Validation

- ONF — Guides de sylviculture (régions forestières)
- CRPF — Recommandations de choix d'essences
- IDF — Fiches de sylviculture par essence
- INRAE — Projections d'aire de distribution
- Seidl et al. — Disturbances in forest ecosystems

### 3.6 Vague 5 — Learning

- Breiman (2001) — Random Forests
- Cutler et al. — Random Forests for classification
- Chen & Guestrin (2016) — XGBoost
- Lundberg & Lee (2017) — SHAP values
- Reichstein et al. (2019) — Deep learning in ecology

### 3.7 Vague I — Ignis (scientifique)

- FIRETWIN (NASA/NSF 2025) — jumeau numérique incendie
- FIRE-VLM (2026) — vision-language modeling incendie
- IVSR (2026) — immersive visual situational awareness
- Rothermel (1972) — Modèle de propagation du feu
- FARSITE — Fire Area Simulator
- Dupuy (2000) — Comportement du feu en France
- ForeFire — Simulateur front-tracking (Allaire, Filippi & Mallet)
- Balbi — Modèle de propagation (référence ForeFire)

---

## 4. Sources par moteur GSIE (14 moteurs)

> Source : `GSIE/ARCHITECTURE/ENGINE_DATA_SOCLE.md`

### 4.1 Evidence Engine
- **Consomme** : Métadonnées de sourçage des DS-001 à DS-029 (évaluation fiabilité)
- **Entités** : `Publication` (sources scientifiques à évaluer)
- **Volume** : ~100 000 évaluations

### 4.2 Knowledge Engine
- **Consomme** : Les 6 types de KnowledgeObject (concept, relation, regle, seuil, modele, classification)
- **Référence** : Tous les datasets comme SourceReference
- **Volume** : ~1 000 000 KO + ~5 000 000 arêtes

### 4.3 GIS Engine
- **Datasets** : DS-001, DS-002, DS-004, DS-013, DS-018, DS-019, DS-020, DS-021, DS-027, DS-028
- **Sources additionnelles** : API Géoplateforme IGN, BD ALTI, BD Carthage, API Carto Cadastre, API Calcul altimétrique
- **Volume** : ~10 To raster + ~500 000 polygones

### 4.4 Botanical Engine
- **Datasets** : DS-014 (GBIF), DS-015 (Tela Botanica), DS-016 (BDNFF), DS-017 (INPN)
- **Sources scientifiques** : Rameau et al. (2008), APG IV, Flora Europaea, EcoPlant, Boullet (habitats)
- **Volume** : ~50 000 taxons + ~200 000 occurrences

### 4.5 Pedology Engine
- **Datasets** : DS-005 (RPF), DS-011 (BDAT), DS-012 (RPFR), DS-013 (SoilGrids)
- **Sources scientifiques** : Baize & Jabiol, IUSS WRB, BRGM (géologie 1/50000), Gobin, Legros
- **Volume** : ~2 000 types de sols + ~100 000 analyses + ~1 To raster

### 4.6 Climate Engine
- **Datasets** : DS-007 (Safran), DS-008 (DRIAS), DS-009 (ARPEGE/AROME), DS-010 (obs sol), DS-021 (MODIS)
- **Sources additionnelles Ignis** : ERA5, Méso-NH, CorrDiff, AIFS, GenCast, Aurora
- **Volume** : ~5 To gridded + ~10 M observations

### 4.7 Correlation Engine
- **Datasets** : DS-003 (IFN), DS-006 (INRAE), DS-010 (Météo-France), DS-011 (BDAT), DS-014 (GBIF), DS-017 (INPN)
- **Volume** : ~100 000 corrélations, ~10 M paires testées

### 4.8 Reasoning Engine
- **Consomme** : Règles d'inférence du Knowledge Graph, corrélations du Correlation Engine
- **Aucun dataset brut** — travaille sur les connaissances qualifiées

### 4.9 Diagnostic Engine
- **Datasets** : DS-001 (BD Forêt), DS-004 (BD Ortho), DS-005 (RPF), DS-011 (BDAT), DS-017 (INPN), DS-018 (Sentinel-2)
- **Volume** : ~10 000 diagnostics/an

### 4.10 Forest Dynamics Engine
- **Datasets** : DS-001, DS-002, DS-003, DS-006, DS-018, DS-019, DS-020, DS-021, DS-025 (GEDI), DS-026 (ESA Biomass)
- **Sources scientifiques** : ONF-FFN, CAPSIS, Deleuze, Dhôte, Bouchon
- **Volume** : ~100 000 peuplements + ~10 M arbres

### 4.11 Simulation Engine
- **Datasets** : DS-002, DS-007, DS-008, DS-009, DS-022 (Prométhée), DS-023 (EFFIS), DS-024 (FIRMS)
- **Sources additionnelles** : ForeFire, FARSITE, Rothermel, ERA5, BDIFF, Copernicus EMS
- **Volume** : ~1 000 scénarios/an, ~50 Go/scénario

### 4.12 Recommendation Engine
- **Aucun dataset brut** — travaille sur sorties Diagnostic + Simulation
- **Sources scientifiques** : ONF (guides sylvicoles), CRPF, IDF

### 4.13 Validation Engine
- **Aucun dataset brut** — valide les sorties des moteurs amont
- **Référence** : Constitution GSIE (CON-000 à CON-010, S-1 à S-7, T-1 à T-8)

### 4.14 Learning Engine
- **Datasets** : DS-003 (IFN), DS-006 (INRAE), DS-018 (Sentinel-2), DS-024 (FIRMS)
- **Sources scientifiques** : Breiman, XGBoost, SHAP, Reichstein
- **Volume** : ~50 000 signaux/an

---

## 5. Sources par application

### 5.1 GeoSylva (forêt — app principale)

**Moteurs consommés** : les 14 moteurs (chaîne complète)

| Type de donnée | Sources |
|---|---|
| Cartes / GIS | DS-001 BD Forêt, DS-002 LiDAR HD, DS-004 BD Ortho, DS-018 Sentinel-2, DS-027 CoSIA, DS-028 OCS GE |
| Essences / botanique | DS-014 GBIF, DS-015 Tela Botanica, DS-016 BDNFF, DS-017 INPN, Rameau et al. |
| Sols | DS-005 RPF, DS-011 BDAT, DS-012 RPFR, DS-013 SoilGrids |
| Climat | DS-007 Safran, DS-008 DRIAS, DS-009 AROME, DS-010 obs sol |
| Dendrométrie | DS-003 IFN, DS-006 INRAE SOERE, DS-025 GEDI, DS-026 ESA Biomass |
| Sylviculture | ONF-FFN, CAPSIS, CRPF, IDF, ONF guides régionaux |
| Diagnostic | DS-017 INPN, DS-018 Sentinel-2 (stress), DSF (santé forêts) |
| Simulation | DS-008 DRIAS (projections 2100), DS-009 AROME |
| Recommandations | Sorties Validation Engine (recommandations contournables) |

### 5.2 Ignis (incendie — jumeau numérique UE 5.8)

**Moteurs consommés** : GIS, Climate, Simulation, Knowledge, Reasoning, Forest Dynamics, Diagnostic

| Type de donnée | Sources |
|---|---|
| Terrain / topographie | DS-002 LiDAR HD (MNT 1 m), BD TOPO, BD ALTI, API altimétrique IGN |
| Combustible | DS-001 BD Forêt v2, DS-027 CoSIA, DS-028 OCS GE, OSO/CESBIO, DS-002 MNH (hauteur canopée) |
| Météo temps réel | DS-009 AROME (vent, T°, hygrométrie), CorrDiff (descente d'échelle 100 m) |
| Météo historique | ERA5 (~30 km), Méso-NH (pyroconvection) |
| Météo IA | AIFS (ECMWF), GenCast (DeepMind), Aurora (Microsoft) |
| Satellite optique | DS-018 Sentinel-2 (NDVI, stress hydrique, surfaces brûlées) |
| Satellite radar | DS-019 Sentinel-1 (surfaces brûlées à travers fumée) |
| Satellite thermique | Sentinel-3 (1 km), MTG-FCI (~2 km / 10 min), DS-024 FIRMS (375 m) |
| Satellite dédié feu | Google FireSat / EFA (5 m / ≤20 min, pilote 2026) |
| Historique feux | DS-022 Prométhée, BDIFF, feuxdeforet.fr, WildfireSpreadTS |
| Cadre européen | DS-023 EFFIS, GWIS (JRC) |
| Validation post-feu | Copernicus EMS (contours officiels) |
| DFCI / infrastructure | Atlas DFCI, GIP ATGeRi/PIGMA, RTE/Enedis (lignes), ANFR Cartoradio |
| Capteurs drone | RGB, thermique LWIR, atmosphériques (CO/CO₂), GPS/IMU |
| Capteurs sol | Stations Meshtastic (LoRa), sensor.community |
| Foudre | Météorage, Blitzortung |
| Atmosphère | CAMS (Copernicus, panaches/qualité air) |
| Entraînement IA | Pyro-SDIS, FLAME/FLAME2, D-Fire, FASDD, FIgLib, links-ads, Google FireBench |
| Données synthétiques | GCS-Cinéma (Unreal/Niagara), Gazebo, Isaac Sim |
| Modèles feu | ForeFire, FARSITE, Rothermel (1972), Balbi, Dupuy (2000) |
| Open data complémentaire | OpenStreetMap, BAN (adressage) |

### 5.3 Artemis (faune)

**Moteurs consommés** : GIS, Botanical, Knowledge, Climate

| Type de donnée | Sources |
|---|---|
| Habitats faune | DS-014 GBIF (occurrences), DS-017 INPN (patrimoine naturel, ZNIEFF) |
| Flore (corrélation faune-flore) | DS-015 Tela Botanica, DS-016 BDNFF, Boullet (habitats forestiers) |
| Cartes / GIS | DS-001 BD Forêt, DS-004 BD Ortho, DS-002 LiDAR HD |
| Météo terrain | DS-007 Safran, DS-010 obs sol Météo-France |

### 5.4 QGISIA (QGIS + IA)

**Moteurs consommés** : GIS, Knowledge, Correlation, Reasoning

| Type de donnée | Sources |
|---|---|
| Couches QGIS | DS-001 BD Forêt, DS-002 LiDAR HD, DS-013 SoilGrids |
| Télédétection | DS-018 Sentinel-2, DS-019 Sentinel-1, DS-020 Landsat 8/9 |
| Analyses IA | Correlation Engine (patterns inter-domaines), Knowledge Graph |
| Géologie | BRGM (cartographie géologique 1/50000) |

### 5.5 Hydro (eau)

**Moteurs consommés** : GIS, Climate, Knowledge, Correlation

| Type de donnée | Sources |
|---|---|
| Hydrographie | BD TOPAGE (IGN/OFB, millésime 2025), BD Carthage (legacy), Sandre (portail national référentiels eau) |
| Occupation sol | DS-028 OCS GE (imperméabilité → ruissellement) |
| Climat | DS-007 Safran, DS-008 DRIAS, DS-009 AROME, DS-010 obs sol |
| GIS | DS-002 LiDAR HD (MNT pour écoulement), DS-001 BD Forêt |
| Corrélations | Correlation Engine (hydro-climatiques) |

### 5.6 Flora (végétation)

**Moteurs consommés** : Botanical, Knowledge, GIS, Climate

| Type de donnée | Sources |
|---|---|
| Taxonomie / flore | DS-014 GBIF, DS-015 Tela Botanica, DS-016 BDNFF, DS-017 INPN |
| Cartographie végétale | DS-001 BD Forêt, DS-004 BD Ortho, DS-027 CoSIA |
| Phénologie | DS-018 Sentinel-2 (NDVI temporal), DS-021 MODIS (phénologie globale) |
| Climat | DS-007 Safran, DS-010 obs sol |
| Référentiels | APG IV (classification), Flora Europaea, Rameau et al. |

### 5.7 Hub / Centre de Commandement (Unreal Engine 5.8)

**Moteurs consommés** : tous (visualisation 3D immersive)

| Type de donnée | Sources |
|---|---|
| Globe 3D | Cesium ion (terrain 3D, imagerie satellite globale) |
| Orthophotographies | DS-004 BD Ortho IGN, Cesium World Imagery |
| MNT global | Cesium World Terrain, DS-002 LiDAR HD (haute résolution locale) |
| Bâtiments 3D | BD TOPO (IGN), Google 3D Tiles (si disponible) |
| Données temps réel | Toutes les sorties validées GSIE (via API) |
| Ignis (feu) | Sorties Simulation Engine (contours front, intensité, ensembles) |

---

## 6. NOUVELLES SOURCES DÉCOUVERTES (recherche juillet 2026)

> Sources identifiées par recherche web, non encore cataloguées dans les documents du projet

### 6.1 Biomasse forestière — produits THEIA/LSCE (France)

| Source | Producteur | Résolution | Période | Licence | Moteurs pertinents |
|---|---|---|---|---|---|
| **FORMS-T** (Forest Multiple Source height, wood volume, biomass time-series) | LSCE / THEIA / Data Terra | Hauteur 10 m, Biomasse & Volume 30 m | 2018-présent | Open (CC-BY) | Forest Dynamics, Correlation, GIS |
| **FORMSpoT** (canopy height 1.5 m + disturbance polygons) | LSCE / THEIA | 1.5 m (SPOT-6/7) | 2014-2024 | Open | Forest Dynamics, Diagnostic, GIS |
| **FORMSpoT-Δ** (forest disturbance polygons) | LSCE / THEIA | Polygones | 2014-2024 | Open | Forest Dynamics, Diagnostic |

**Détails FORMS-T :**
- Cartes nationales d'attributs forestiers (hauteur, biomasse, volume) dérivées de Sentinel-1 + Sentinel-2 + GEDI par deep learning
- Réf : Schwartz et al. (2025), *Remote Sensing of Environment*, vol. 330, 114959
- Accès STAC : `https://browser-theia.stac.teledetection.fr/`
- Accès Zenodo : `https://zenodo.org/records/15489231`

**Détails FORMSpoT :**
- Cartes annuelles de hauteur de canopée à 1.5 m sur toute la France (2014-2024)
- Entraîné sur SPOT-6/7 + LiDAR HD IGN (PVTv2 hierarchical vision transformer)
- Polygones de perturbation (pertes de hauteur year-to-year)
- Réf : Schwartz et al. (2026), in review

### 6.2 Biomasse forestière — produits européens

| Source | Producteur | Résolution | Couverture | Licence | Moteurs pertinents |
|---|---|---|---|---|---|
| **PathFinder** (Pan-European forest maps) | EU PathFinder / JRC | 10 m | 40 pays européens | Open | Forest Dynamics, Correlation, GIS |
| **SafeNet Forest Carbon** (carte carbone forestier Europe) | SafeNet project / EU | 100 m | Europe 2020 | Open (Zenodo) | Forest Dynamics, Climate, Correlation |

**Détails PathFinder :**
- Cartes de volume de bois (Vol), biomasse aérienne (AGB), proportion décidue/conifère (DCP)
- k-Nearest Neighbour (k=7) avec ~151 000 placettes NFI de 14 pays + Sentinel-2
- Réf : DOI 10.1016/j.dib.2025.111613

**Détails SafeNet :**
- Carte de densité de carbone forestier (AGC + BGC + SOC) à 100 m pour 2020
- Combine PathFinder (AGB) + Köppen-Geiger + fractions carbone Martin et al. (2018)
- Disponible sur Zenodo (Bennett et al., 2026)

### 6.3 Copernicus Land Monitoring Service — couches forestières

| Source | Producteur | Résolution | Période | Licence | Moteurs pertinents |
|---|---|---|---|---|---|
| **HRL Tree Cover Density (TCD)** | Copernicus / EEA | 10 m / annuel | 2018-présent | Open | GIS, Forest Dynamics, Diagnostic |
| **HRL Dominant Leaf Type (DLT)** | Copernicus / EEA | 10 m / annuel | 2018-présent | Open | GIS, Forest Dynamics, Botanical |
| **HRL Forest Type (FTY)** | Copernicus / EEA | 10 m et 100 m | 2018-présent | Open | GIS, Forest Dynamics |
| **Copernicus Global Land Cover (LCFM)** | Copernicus / VITO | 10 m | 2020-2026 | Open | GIS, Forest Dynamics, Botanical |
| **Pan-Tropical TCD 10 m** | Copernicus LCFM | 10 m | 2020 | Open | GIS (référence globale) |

### 6.4 Humidité des sols — nouvelles sources

| Source | Producteur | Résolution | Période | Licence | Moteurs pertinents |
|---|---|---|---|---|---|
| **Copernicus Soil Water Index (SWI)** | Copernicus / EEA | 1 km / quotidien | 2025-présent | Open | Pedology, Climate, Forest Dynamics, Ignis |
| **Copernicus Surface Soil Moisture** | Copernicus / EEA (Sentinel-1) | 1 km | 2015-présent | Open | Pedology, Climate, Ignis |
| **Météo-France SWI (Soil Wetness Index)** | Météo-France | Maille 8 km / mensuel | Historique + temps réel | Licence Ouverte 2.0 | Climate, Pedology, Forest Dynamics |
| **JRC GDO Soil Moisture Anomaly (SMA)** | JRC / Copernicus | 3 arcmin / 3x par mois | 1995-2024 baseline | Open | Climate, Pedology, Ignis |
| **ECA&D European Soil Moisture** | KNMI / ECA&D | 5758 stations / quotidien | 1852-présent | CC-BY 4.0 | Climate, Pedology, Correlation |

### 6.5 Incendie — sources complémentaires

| Source | Producteur | Résolution | Licence | Usage |
|---|---|---|---|---|
| **VIIRS Active Fire** (NASA FIRMS) | NASA / Suomi NPP | 375 m / quasi temps réel | Domaine public | Complément MODIS, meilleure résolution |
| **Copernicus Burnt Area v4** | Copernicus / Sentinel-3 OLCI+SLSTR | 300 m / quotidien | Open | Surfaces brûlées globales NRT |
| **DLR Burnt Area Daily NRT** | DLR / Sentinel-3 OLCI | 300 m / NRT | Open | Europe, incrémental sur 10 jours |
| **DLR Burnt Area Monthly/Yearly** | DLR / Sentinel-3 | 300 m | Open | Europe, produits consolidés |

### 6.6 Santé des forêts — pathologies et ravageurs

| Source | Producteur | Type | Licence | Moteurs pertinents |
|---|---|---|---|---|
| **DSF — Bilans annuels santé des forêts** | Département Santé des Forêts (MEAE) | Rapports annuels par région | Open | Diagnostic, Forest Dynamics, Learning |
| **DSF — DEPERIS (méthode de notation dépérissement)** | DSF | Méthode + données placettes | Open | Diagnostic, Correlation |
| **EPPO Global Database** | EPPO (European & Mediterranean Plant Protection Org.) | Distribution ravageurs/pathogènes | Open | Diagnostic, Knowledge, Botanical |
| **PEPR FORESTT / MASSIF** | INRAE (2025-2029) | Suivi automatisé insectes forêt | Accord INRAE | Diagnostic, Learning, Botanical |
| **PEPR FORESTT / MONITOR** | INRAE | Monitoring écologique télédétection | Accord INRAE | Diagnostic, Forest Dynamics, GIS |
| **PEPR FORESTT / FOMES** | INRAE (2024-2025) | Détection Heterobasidion spp. (pourridié) | Accord INRAE | Diagnostic, Knowledge |

### 6.7 Biodiversité — plateformes européennes

| Source | Producteur | Type | Licence | Moteurs pertinents |
|---|---|---|---|---|
| **EuropaBON** (84 Essential Biodiversity Variables) | EuropaBON / EU | Framework + datasets | Open | Botanical, Correlation, Knowledge |
| **FloraVeg.EU** | Masaryk Univ. / EVCC | Végétation, habitats, flore européenne | Open | Botanical, Knowledge, Correlation |
| **EMODnet Biology** | EMODnet / EU | Biodiversité marine européenne | Open | Botanical (marine), Knowledge |
| **LifeWatch ERIC / BMD Project** | LifeWatch ERIC / Naturalis | e-DNA, AI taxon ID, VREs | Open | Botanical, Learning, Knowledge |
| **European Vegetation Archive (EVA)** | IAVS | Archive végétation européenne | Accord | Botanical, Correlation, Knowledge |
| **Euro+Med PlantBase** | Euro+Med | Flore européenne et méditerranéenne | Open | Botanical, Knowledge |

### 6.8 Hydrographie — mise à jour 2025

| Source | Producteur | Résolution | Licence | Moteurs pertinents |
|---|---|---|---|---|
| **BD TOPAGE 2025** (remplace BD Carthage) | IGN / OFB | Métrique (grande échelle) | Licence Ouverte 2.0 | GIS, Hydro, Knowledge |
| **Sandre** (portail national référentiels eau) | OIEau / ministère | Référentiels | Licence Ouverte 2.0 | Hydro, Knowledge |
| **SHOM — Limite terre-mer** | SHOM | ~5 m planimétrique | Open data | GIS, Hydro (littoral) |

### 6.9 Infrastructure — BD TOPO Express

| Source | Producteur | Fréquence | Licence | Moteurs pertinents |
|---|---|---|---|---|
| **BD TOPO Express** (édition hebdomadaire) | IGN | Hebdomadaire (depuis mai 2025) | Licence Ouverte 2.0 | GIS, Ignis (enjeux temps réel) |

---

## 7. Synthèse — comptage total

| Catégorie | Nombre de sources |
|---|---|
| Datasets catalogués (DS-001 à DS-029) | 29 |
| Sources additionnelles Ignis (topographie, météo, satellite, feux, DFCI, capteurs, IA) | ~45 |
| Sources scientifiques (Sourcing Plan, publications, ouvrages, référentiels) | ~64 |
| Sources spécifiques apps (Hydro: BD TOPAGE, Sandre, SHOM ; Hub: Cesium, Google 3D Tiles ; BRGM) | ~7 |
| Capteurs drone (RGB, thermique, atmosphériques, GPS/IMU) | 4 |
| **NOUVELLES sources (recherche juillet 2026)** | **~30** |
| **Total estimé** | **~179 sources distinctes** |

### Détail des nouvelles sources par catégorie

| Catégorie nouvelles sources | Nombre |
|---|---|
| Biomasse forestière (FORMS-T, FORMSpoT, PathFinder, SafeNet) | 6 |
| Copernicus HRL forestières (TCD, DLT, FTY, LCFM, TCD tropical) | 5 |
| Humidité des sols (Copernicus SWI, SSM, Météo-France SWI, JRC SMA, ECA&D) | 5 |
| Incendie (VIIRS, Copernicus BA v4, DLR BA) | 4 |
| Santé forêts (DSF bilans, DEPERIS, EPPO, PEPR FORESTT ×3) | 6 |
| Biodiversité (EuropaBON, FloraVeg.EU, EMODnet, LifeWatch/BMD, EVA, Euro+Med) | 6 |
| Hydrographie (BD TOPAGE 2025, SHOM) | 2 |
| Infrastructure (BD TOPO Express) | 1 |

---

## 8. Volumétrie globale estimée

> Source : `GSIE/ARCHITECTURE/ENGINE_DATA_SOCLE.md`

| Moteur | Volume consommé | Nature |
|---|---|---|
| GIS Engine | ~10 To raster + ~500 000 polygones | Raster/vectoriel (lourd) |
| Climate Engine | ~5 To gridded + ~10 M observations | Raster temporel (lourd) |
| Pedology Engine | ~2 000 types + ~100 000 analyses + ~1 To raster | Raster + tabulaire (lourd) |
| Forest Dynamics | ~100 000 peuplements + ~10 M arbres | Tabulaire + raster (modéré) |
| Knowledge Engine | ~1 000 000 KO + ~5 000 000 arêtes | Graphe (modéré) |
| Simulation Engine | ~50 Go/scénario long | Calcul + raster (lourd) |
| **Total brut** | **~20 To** | Essentiellement raster |

---

## 9. Recommandations d'ingestion pour les nouvelles sources

### Priorité haute (bloquante pour Phase 4)

1. **FORMS-T** → Forest Dynamics Engine : cartes nationales biomasse/hauteur/volume, parfaites pour validation et calibration
2. **Copernicus HRL TCD 10 m** → GIS Engine : couverture européenne annuelle, complément BD Forêt
3. **BD TOPAGE 2025** → GIS Engine / Hydro : remplace BD Carthage, précision métrique
4. **Météo-France SWI** → Climate Engine : humidité sol gratuite, critique pour stress hydrique

### Priorité moyenne (enrichissement)

5. **PathFinder** → Forest Dynamics / Correlation : harmonisation européenne NFI + Sentinel-2
6. **VIIRS Active Fire** → Ignis / Simulation : complémente MODIS FIRMS, meilleure résolution
7. **Copernicus Burnt Area v4** → Ignis : surfaces brûlées NRT 300 m
8. **DSF DEPERIS** → Diagnostic Engine : méthode standardisée de notation dépérissement
9. **EPPO Global Database** → Diagnostic / Knowledge : distribution ravageurs/pathogènes Europe

### Priorité basse (veille)

10. **FloraVeg.EU** → Botanical / Knowledge : classification phytosociologique européenne
11. **EuropaBON EBVs** → Knowledge / Correlation : framework monitoring biodiversité
12. **FORMSpoT 1.5 m** → Forest Dynamics / Diagnostic : suivi perturbations arbre par arbre
13. **SafeNet Forest Carbon** → Climate / Forest Dynamics : carte carbone Europe 100 m
14. **ECA&D Soil Moisture** → Climate / Pedology : 5758 stations européennes

---

## 10. Méthodes d'ingestion par source

> Méthodes concrètes et programmatiques pour récupérer chaque type de donnée. Recherches effectuées en juillet 2026.

### 10.1 IGN — Géoplateforme (DS-001, DS-002, DS-004, BD TOPO, BD ALTI, OCS GE, Cadastre)

**3 méthodes complémentaires :**

#### A. API de téléchargement (Atom, bulk)
- **Endpoint** : `https://data.geopf.fr/telechargement/capabilities`
- **Méthodes** : `GetCapabilities` → `GetResource` → `GetSubResource` → `Download`
- **Format** : 7z multi-volumes (BD Ortho), GeoPackage (BD TOPO), LAZ (LiDAR HD)
- **Limite** : 10 requêtes / 10 min / IP
- **Exemple LiDAR HD MNT** :
  ```
  https://data.geopf.fr/telechargement/download/IGNF_MNT-LIDAR-HD/{subResource}/{fileName}
  ```
- **Exemple BD Forêt** : `https://data.geopf.fr/telechargement/resource/BDFORET`
- **BD TOPO Express** (hebdomadaire) : `https://data.geopf.fr/telechargement/resource/BDTOPO_EXPRESS`

#### B. API d'extraction vecteur (OGC API Processes, REST)
- **Endpoint** : `https://data.geopf.fr/extraction`
- **Swagger** : `https://data.geopf.fr/extraction/swagger-ui/index.html`
- **Auth** : Compte Géoplateforme requis
- **Formats sortie** : Shapefile, GeoPackage, GeoJSON, GeoParquet, GML, PGDUMP
- **Usage** : Extraction personnalisée par emprise (EPCI, région) + sélection tables/champs
- **Avantage** : Évite de télécharger des départements entiers pour quelques communes

#### C. WMS / WMTS (flux streaming)
- **WMTS** : `https://data.geopf.fr/wmts?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities`
- **Couches LiDAR HD** : `IGNF_LIDAR-HD_MNT_ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW`
- **Usage** : Visualisation temps réel dans QGIS / Unreal Engine / Hub

**Nouveauté BD Forêt v3** (2026) : Jeu test sur 40 zones disponible, production par IA à partir de BD Ortho. Retours attendus jusqu'avril 2026. À suivre pour migration DS-001 → v3.

### 10.2 Copernicus Data Space Ecosystem (DS-018, DS-019, Sentinel-1/2/3, ERA5, Burnt Area)

**4 interfaces d'accès :**

#### A. STAC API (recommandé, nouveau)
- **Endpoint** : `https://stac.dataspace.copernicus.eu/v1/`
- **Collections disponibles** : Sentinel-1 GRD, Sentinel-2 L1C/L2A, Sentinel-2 Global Mosaics
- **Recherche par filtre CQL2** :
  ```
  https://stac.dataspace.copernicus.eu/v1/collections/sentinel-2-l2a/items?filter-lang=cql2-text&filter=eo:cloud_cover<15
  ```
- **POST search** : `https://stac.dataspace.copernicus.eu/v1/search`
- **Avantage** : Standard STAC 1.1.0, compatible xarray/stac, pystac-client

#### B. OData API (catalogue complet)
- **Endpoint** : `https://catalogue.dataspace.copernicus.eu/odata/v1/Products`
- **Auth** : Compte CDSE + token Bearer (`https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token`)
- **Filtre par collection + date + cloud cover + zone** :
  ```
  $filter=Collection/Name eq 'SENTINEL-2' and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le 40.00) and ContentDate/Start gt 2022-01-01T00:00:00.000Z
  ```
- **Téléchargement** : `Nodes(ProductName)/Nodes(BandFile)/$value` avec session authentifiée
- **Subscriptions OData** : Recommandé pour monitoring nouveaux produits

#### C. S3 API (bulk, performant)
- **Endpoint** : `s3://eodata/`
- **Avantage** : Accès direct aux objets, téléchargement massif parallèle
- **Instructions** : Disponibles sur la doc CDSE

#### D. Streamlined Data Access (SDA) API
- **Usage** : API simplifiée pour les cas courants, abstraction des spécificités par collection

### 10.3 Météo-France (DS-007, DS-008, DS-009, DS-010, SWI)

#### A. Portail des API Météo-France
- **URL** : `https://portail-api.meteofrance.fr/`
- **Auth** : Clé API (inscription sur le portail)
- **AROME** : API paramétrable (paramètres, niveaux, échéances, domaines)
- **Formats** : GRIB2, GeoTIFF, PNG
- **Rétention** : 14 jours pour les PNT (Prévisions Numériques du Temps)

#### B. data.gouv.fr (téléchargement bulk)
- **SIM (Safran-ISBA)** : `https://www.data.gouv.fr/datasets/meteo-france-donnees-sim`
  - Données quotidiennes, maille 8 km, j-1
  - SWI (humidité sol), évapotranspiration, précipitations
  - Licence Ouverte 2.0
- **Paquets AROME 0.01°** : `https://www.data.gouv.fr/datasets/paquets-arome-resolution-0-01deg`
  - Fichiers horaires, analyse + prévision
- **SWI mensuel (CatNat)** : `https://donneespubliques.meteofrance.fr/?fond=produit&id_produit=301`
  - Maille 8 km, CSV, Licence Ouverte 2.0

#### C. DRIAS (projections climatiques)
- **URL** : `https://www.drias-climat.fr/`
- **Accès** : Interface web + API (après inscription)
- **Données** : RCP/SSP, modèles ALADIN/RCA/REMO, 8-12 km

### 10.4 GBIF (DS-014)

#### A. API REST (recherche paginée)
- **Endpoint** : `https://api.gbif.org/v1/occurrence/search`
- **Limite** : 300 records/page, max 100 000 records par query
- **Rate limit** : HTTP 429 si surcharge → utiliser download API

#### B. API Download (asynchrone, bulk)
- **Endpoint** : `https://api.gbif.org/v1/occurrence/download/request`
- **Auth** : `--user userName:password` (compte GBIF.org requis)
- **Formats** : `SIMPLE_CSV`, `DWCA` (Darwin Core Archive), `SPECIES_LIST`, `SIMPLE_PARQUET`
- **Prédicats** : `equals`, `and`, `or`, `in`, `within`, `greaterThan`, `like`...
- **Limites** : 101 000 items max, 10 000 points géométriques
- **Workflow** :
  1. POST request → retourne un `download key`
  2. Poll `GET /occurrence/download/{key}` jusqu'à `SUCCEEDED`
  3. Download du fichier zip

#### C. pygbif (Python)
```python
from pygbif import occurrences
# Recherche simple
occ.search(country='FR', taxonKey=6)
# Download asynchrone
occ.download('country = FR and hasCoordinate = true', user='...', pwd='...', email='...')
# Download SQL
occ.download_sql("SELECT * FROM occurrence WHERE country = 'FR'")
```

### 10.5 NASA FIRMS (DS-024, VIIRS)

#### A. API REST (temps réel + historique)
- **Auth** : `MAP_KEY` gratuite (inscription : `https://firms.modaps.eosdis.nasa.gov/api/map_key`)
- **Rate limit** : 5 000 transactions / 10 min
- **Area endpoint** :
  ```
  https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{AREA_COORDS}/{DAY_RANGE}/{DATE}
  ```
- **Sources** : `MODIS_NRT`, `VIIRS_SNPP_NRT`, `VIIRS_NOAA20_NRT`, `VIIRS_NOAA21_NRT`, `GOES_NRT`, `LANDSAT_NRT`
- **Data availability** : `https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/{MAP_KEY}/all`
- **Formats** : CSV, SHP, KML/KMZ
- **Burned Area** : `BA_MODIS` (2000-présent), `BA_VIIRS` (2012-présent)

#### B. Archive Download (historique)
- **URL** : `https://firms.modaps.eosdis.nasa.gov/download/`
- **Formats** : CSV, Shapefile, KML
- **Période** : Archive complète (MODIS depuis 2000, VIIRS depuis 2012)

### 10.6 ERA5 / Copernicus Climate Data Store

#### A. cdsapi (Python, recommandé)
```python
import cdsapi
client = cdsapi.Client()
client.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': 'reanalysis',
        'variable': ['10m_u_component_of_wind', '10m_v_component_of_wind', '2m_temperature'],
        'year': '2025', 'month': ['01','02','03'],
        'day': [f'{d:02d}' for d in range(1,32)],
        'time': ['00:00','06:00','12:00','18:00'],
        'area': [51, -5, 41, 10],  # France: N, W, S, E
        'data_format': 'netcdf',
    },
    'era5_france_2025q1.nc'
)
```
- **Install** : `pip install "cdsapi>=0.7.7"`
- **Config** : `~/.cdsapirc` avec `url` + `key` (Personal Access Token)
- **Prérequis** : Accepter les Terms of Use de chaque dataset sur le portail CDS
- **Nouveau client** : `ecmwf-datastores-client` (incubating, features avancées)

### 10.7 INPN / MNHN (DS-017, ZNIEFF)

#### A. Téléchargement direct
- **URL** : `https://inpn.mnhn.fr/telechargement/cartes-et-information-geographique`
- **Couches** : ZNIEFF type 1/2 (continentales + marines), aires protégées, Natura 2000
- **Formats** : Shapefile, GeoPackage
- **Note** : Serveurs MNHN temporairement indisponibles (cyberattaque 2025), page de téléchargement alternative via PatriNat

#### B. Services web WMS / WFS
- **WMS** : `https://inpn.mnhn.fr/webgeoservice/WMS/fxx_inpn`
- **WFS** : `https://inpn.mnhn.fr/webgeoservice/WFS/fxx_inpn`
- **Usage** : Intégration directe dans QGIS, GeoServer, PostGIS

#### C. data.gouv.fr
- ZNIEFF type I : `https://www.data.gouv.fr/datasets/znieff-de-type-i` (via Géoplateforme IGN)
- Programme ZNIEFF complet : `https://www.data.gouv.fr/datasets/inpn-donnees-du-programme-znieff`

### 10.8 THEIA / Data Terra (FORMS-T, FORMSpoT, OSO, Sentinel)

#### A. STAC API (recommandé)
- **Endpoint** : `https://browser-theia.stac.teledetection.fr/`
- **Collections** : FORMS-T (biomasse/hauteur/volume), FORMSpoT (canopée 1.5 m), RECONFORT (dépérissement chêne), FORDEAD (scolytes épicéa)
- **Accès programmatique** : API STAC standard
- **Visualisation QGIS** : Plugin « STAC API Browser » (QGIS ≥ 3.44)

#### B. Package Python `teledetection`
```python
# Accès aux produits THEIA via STAC
# Installation: pip install teledetection
```

#### C. Package R `rstactheia`
- Accès équivalent via R

#### D. Zenodo (téléchargement bulk)
- FORMS-T : `https://zenodo.org/records/15489231`
- Format : Cloud-Optimized GeoTIFFs (COGs)

### 10.9 PEPR FORESTT / MONITOR (nouvelles sources 2026)

#### A. Entrepôt Recherche Data Gouv
- **URL** : `https://entrepot.recherche.data.gouv.fr/dataverse/pepr-forestt`
- **Contenu** : 16 projets (MONITOR, MASSIF, FOMES, NUM-DATA...)
- **Accès** : Open data, DOI persistants

#### B. Produits MONITOR via THEIA
- **FORMS-T** : cartes annuelles hauteur/biomasse/volume France
- **RECONFORT** : cartes annuelles dépérissement chêne
- **FORDEAD** : détection temps réel scolytes épicéa (Sentinel-2)
- **CLIMARBRE** : base nationale microclimat forestier (capteurs LASCAR + TOMST, 100 placettes)
- **Accès** : STAC THEIA + package `fordead` (Python)

### 10.10 Copernicus Land Monitoring Service (HRL TCD, Burnt Area, Soil Moisture)

#### A. Copernicus Data Space Ecosystem (CDSE)
- **Browser** : `https://browser.dataspace.copernicus.eu/`
- **S3 storage** : `s3://eodata/`
- **OData API** : `https://catalogue.dataspace.copernicus.eu/odata/v1/Products`
- **Collections** : CLMS (Copernicus Land Monitoring Service)

#### B. land.copernicus.eu (téléchargement direct)
- **HRL TCD 10 m** : `https://land.copernicus.eu/en/products/high-resolution-layer-forests-and-tree-cover`
- **Burnt Area v4** : `https://land.copernicus.eu/en/products/vegetation/burnt-area-v4-daily-300m`
- **Soil Water Index** : `https://land.copernicus.eu/en/products/soil-moisture/daily-soil-water-index-europe-1km-v2`
- **Formats** : GeoTIFF, COG

### 10.11 BD TOPAGE / Sandre (Hydro)

#### A. Atlas-catalogue Sandre
- **URL** : `https://www.sandre.eaufrance.fr/`
- **Millésime 2025** : Disponible en Shapefile, GeoJSON, GeoPackage
- **Services WMS/WFS** : `https://www.sandre.eaufrance.fr/` (services web)
- **Licence** : Licence Ouverte 2.0

#### B. data.gouv.fr
- BD TOPAGE 2025 : `https://www.data.gouv.fr/datasets/bd-topage-r-metropole-2025`
- Cours d'eau : `https://www.data.gouv.fr/datasets/cours-deau-metropole-2025-bd-topage-r`

### 10.12 EPPO Global Database (pathogènes / ravageurs)

- **URL** : `https://gd.eppo.int/`
- **Accès** : Interface web + API REST (sur demande)
- **Données** : Distribution par pays, statut réglementaire, fiches techniques
- **Usage** : Diagnostic Engine — détection ravageurs invasifs

### 10.13 DSF — Département Santé des Forêts

- **Bilans annuels** : `https://agriculture.gouv.fr/bilans-annuels-en-sante-des-forets`
- **Méthode DEPERIS** : Documentation + données placettes (sur demande DSF)
- **Lettres du DSF** : Publications périodiques (open data)
- **Accès** : Téléchargement direct PDF + données tabulaires

### 10.14 Autres sources — méthodes d'accès rapides

| Source | Méthode | Auth | Format |
|---|---|---|---|
| **OpenStreetMap** | Overpass API / Geofabrik (bulk) | Aucune | PBF, Shapefile |
| **BAN** (Base Adresse Nationale) | `https://api.gouv.fr/adresse` | Aucune | CSV, JSON |
| **RTE / Enedis** (lignes électriques) | Open data portals respectifs | Aucune | GeoJSON, SHP |
| **ANFR Cartoradio** | `https://www.anfr.fr/cartoradio` | Aucune | CSV, KML |
| **CAMS** (Copernicus Atmosphère) | ADS API (`cdsapi`) | Compte ADS | NetCDF, GRIB |
| **Météorage** | API commerciale (sur devis) | Contrat | JSON, XML |
| **Blitzortung** | API communautaire (REST) | Inscription | JSON |
| **sensor.community** | API REST publique | Aucune | JSON, CSV |
| **Meshtastic** | Protocole mesh LoRa (propriétaire) | Configuration | MQTT / Serial |
| **Cesium ion** | API REST + token | Compte Cesium | 3D Tiles, GeoTIFF |
| **Google 3D Tiles** | API Maps Platform | Clé API Google | 3D Tiles |
| **PathFinder** (EU) | Zenodo + JRC Data Catalogue | Aucune | GeoTIFF |
| **SafeNet Forest Carbon** | Zenodo | Aucune | GeoTIFF (100 m) |
| **FloraVeg.EU** | API REST + interface web | Aucune | JSON, CSV |
| **EuropaBON** | Zenodo | Aucune | CSV, Shapefile |
| **EMODnet Biology** | WFS / REST API | Aucune | Darwin Core, JSON |
| **ECA&D Soil Moisture** | Download direct (KNMI) | Aucune | CSV |
| **DLR Burnt Area** | `https://geoservice.dlr.de/web/maps/` | Aucune | WMS, GeoTIFF |

---

## 11. Architecture d'ingestion recommandée

### 11.1 Pipeline d'ingestion par couches

```
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 1 — APIs temps réel (latence < 1h)                  │
│  NASA FIRMS (VIIRS/MODIS) · AROME API · MTG-FCI · Meshtastic│
│  → Ingestion continue, polling 10-60 min                    │
├─────────────────────────────────────────────────────────────┤
│  COUCHE 2 — APIs quasi temps réel (latence 1-24h)           │
│  Copernicus CDSE (Sentinel-2/3) · Météo-France SIM          │
│  → Ingestion quotidienne, scripts planifiés                 │
├─────────────────────────────────────────────────────────────┤
│  COUCHE 3 — Téléchargement bulk (hebdomadaire/mensuel)      │
│  IGN Géoplateforme (BD Forêt, LiDAR HD, BD TOPO)            │
│  THEIA STAC (FORMS-T, FORMSpoT, RECONFORT, FORDEAD)         │
│  Copernicus HRL (TCD, DLT, FTY) · BD TOPAGE                 │
│  → Ingestion mensuelle, scripts planifiés                   │
├─────────────────────────────────────────────────────────────┤
│  COUCHE 4 — Téléchargement ponctuel (annuel/ponctuel)       │
│  GBIF (download async) · ERA5 (cdsapi) · DRIAS              │
│  INPN (ZNIEFF) · EPPO · DSF bilans · PathFinder             │
│  → Ingestion manuelle ou semi-automatisée                   │
├─────────────────────────────────────────────────────────────┤
│  COUCHE 5 — Sources sous accord (quarantaine)               │
│  Safran · RPF ONF · SOERE INRAE · Prométhée · PEPR FORESTT  │
│  → Nécessite formalisation partenariat (20_PARTNERSHIPS/)   │
└─────────────────────────────────────────────────────────────┘
```

### 11.2 Stack technique recommandée

| Composant | Technologie | Usage |
|---|---|---|
| **Orchestration** | Apache Airflow / Prefect | Planification des pipelines d'ingestion |
| **Téléchargement raster** | `cdsapi`, `pystac-client`, `rasterio` | ERA5, Sentinel, THEIA |
| **Téléchargement vectoriel** | `geopandas`, `pyogrio`, API IGN extraction | BD Forêt, BD TOPO, ZNIEFF |
| **Stockage raster** | PostGIS Raster + COG (Cloud Optimized GeoTIFF) | Accès streaming + requêtes spatiales |
| **Stockage vectoriel** | PostGIS (PostgreSQL + PostGIS) | Requêtes spatiales, jointures |
| **Cache / file** | Redis + Celery / RQ | Asynchrone, rate limiting |
| **Monitoring** | Prometheus + Grafana | Suivi ingestion, alertes échec |
| **STAC** | `pystac`, `stac-fastapi` | Catalogue interne des données ingérées |
| **Qualité** | `great_expectations` | Validation schéma + complétude |

### 11.3 Authentification — gestion des secrets

| Source | Méthode auth | Secret à stocker |
|---|---|---|
| IGN Géoplateforme (extraction) | Compte + token | `IGN_GPF_TOKEN` |
| Copernicus CDSE | OAuth2 (client_id `cdse-public`) | `CDSE_USERNAME`, `CDSE_PASSWORD` |
| Météo-France API | Clé API | `METEOFRANCE_API_KEY` |
| GBIF Download | Basic auth | `GBIF_USER`, `GBIF_PWD` |
| NASA FIRMS | MAP_KEY | `FIRMS_MAP_KEY` |
| ERA5 / CDS | Personal Access Token | `CDS_API_KEY` |
| Cesium ion | Token | `CESIUM_ION_TOKEN` |

**Tous les secrets dans des variables d'environnement** (jamais en code, jamais en git). Utiliser `.env` + `python-dotenv` ou un vault (HashiCorp Vault / AWS Secrets Manager).

### 11.4 Code snippet — template d'ingestion générique

```python
"""Template d'ingestion pour GSIE — à adapter par source."""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

import requests
import geopandas as gpd
import rasterio

logger = logging.getLogger(__name__)

class IngestionConfig:
    """Configuration d'ingestion d'une source."""
    source_id: str           # ex: "DS-018"
    source_name: str         # ex: "Sentinel-2 L2A"
    api_endpoint: str
    auth_env_var: str        # nom de la variable d'environnement
    output_dir: Path
    cadence_hours: int       # fréquence d'ingestion
    max_retries: int = 3
    timeout_seconds: int = 300

def fetch_sentinel2(
    bbox: tuple[float, float, float, float],
    date_start: str,
    date_end: str,
    max_cloud_cover: float = 20.0,
) -> list[dict]:
    """Récupère les métadonnées Sentinel-2 via STAC CDSE."""
    url = "https://stac.dataspace.copernicus.eu/v1/search"
    payload = {
        "collections": ["sentinel-2-l2a"],
        "bbox": list(bbox),
        "datetime": f"{date_start}T00:00:00Z/{date_end}T23:59:59Z",
        "filter": {"op": "<", "args": [
            {"property": "eo:cloud_cover"}, {"value": max_cloud_cover}
        ]},
    }
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    return response.json().get("features", [])

def fetch_firms_fire_detections(
    bbox: tuple[float, float, float, float],
    day_range: int = 1,
    source: str = "VIIRS_SNPP_NRT",
) -> gpd.GeoDataFrame:
    """Récupère les détections de feux actifs via NASA FIRMS API."""
    map_key = os.environ["FIRMS_MAP_KEY"]
    area = f"{bbox[3]},{bbox[0]},{bbox[1]},{bbox[2]}"
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/{source}/{area}/{day_range}"
    df = gpd.read_file(url)
    logger.info(f"FIRMS: {len(df)} détections récupérées ({source}, {day_range}j)")
    return df
```

---

## 12. Projets GitHub pertinents pour GSIE

> Recherche effectuée en juillet 2026 — projets open source couvrant ingestion de données, moteurs IA, simulation, détection, visualisation et architecture backend.

### 12.1 Simulation incendie (Ignis / Simulation Engine)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[pcm-dpc/propagator](https://github.com/pcm-dpc/propagator)** | — | Python | EUPL 1.2 | **Très haute** — Cellular automata wildfire simulator (CIMA Research Foundation). Numba-accelerated, CLI + API programmatique. Modèle stochastique avec vent, humidité, combustible.Intégrable directement dans Ignis. |
| **[forefireapi/firefront](https://github.com/forefireapi/firefront)** (ForeFire) | — | C++/Python | Open source | **Très haute** — Moteur CNRS (Université de Corse). Couplage fire-atmosphère (MesoNH). Python bindings. Publié dans JOSS 2025. Modèles ROS multiples, NetCDF. |
| **[xiazeyu/PyTorchFire](https://github.com/xiazeyu/PyTorchFire)** | 3 | Python | MIT | **Haute** — Cellular automata différentiable GPU (PyTorch). Calibration temps réel par gradient. Millisecondes. `pip install pytorchfire`. Publié dans Environmental Modelling & Software 2025. |
| **[mzhen77/neural-ca-wildfire](https://github.com/mzhen77/neural-ca-wildfire)** | — | Python | — | **Haute** — CNN-parameterized probabilistic CA. Inputs LANDFIRE + ERA5. JAX. 6 feux historiques. Modèle pré-entraîné inclus. |
| **[infordata-sistemi/pyrowise](https://github.com/infordata-sistemi/pyrowise)** (PyroWISE) | — | Python | AGPL-3.0 | **Moyenne** — Implémentation CFFDRS (Canadian FWI). FastAPI, OGC-friendly, COGs, SSE streaming. Architecture similaire à GSIE. Engine commercial mais méthodes open. |

### 12.2 LiDAR / Inventaire forestier (Forest Dynamics / GIS Engine)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[SmartForest-no/ForestFormer3D](https://github.com/SmartForest-no/ForestFormer3D)** | — | C++/Python | — | **Très haute** — ICCV 2025 (Oral). Segmentation end-to-end forêt LiDAR 3D point clouds. Pre-trained model sur Zenodo. Dataset ForAINetV2. **Idéal pour LiDAR HD IGN**. |
| **[prs-eth/ForAINet](https://github.com/prs-eth/ForAINet)** | 100 | Python | — | **Très haute** — Automated forest inventory avec airborne LiDAR 3D deep learning. ETH Zürich. TreeMix data augmentation. Panoptic segmentation. |
| **[ecker-lab/TreeLearn](https://github.com/ecker-lab/TreeLearn)** | — | Python | — | **Haute** — Tree instance segmentation from ground-based LiDAR. Deep learning pipeline. 6665 arbres entraînés. Fine-tuning possible. Benchmark dataset 156 arbres. |
| **[PRBonn/forest_inventory_pipeline](https://github.com/PRBonn/forest_inventory_pipeline)** | 32 | C++/Python | MIT | **Haute** — Tree instance segmentation + traits estimation (DBH) from mobile robot LiDAR. Docker, CLI. Dataset DigiForests. |
| **[shenglandu/SATree](https://github.com/shenglandu/SATree)** | 5 | Python/C++ | Apache 2.0 | **Moyenne** — Structure-aware tree instance segmentation. Multi-task: semantic + heatmap + offset. Courant 2026. |

### 12.3 Botanique / Identification d'espèces (Botanical Engine)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[MUYang99/GlobalGeoTree](https://github.com/MUYang99/GlobalGeoTree)** | 66 | Python | — | **Très haute** — 6.3M occurrences, 21 001 espèces, 221 pays. Sentinel-2 time series + 27 variables env. GeoTreeCLIP (vision-language). Dataset sur HuggingFace. **Idéal pour Botanical Engine + Correlation**. ESSD 2026. |
| **[WHU-USI3DV/TreeCLS](https://github.com/WHU-USI3DV/TreeCLS)** | — | Python | — | **Haute** — Fine-grained tree species classification (102 espèces). Expert knowledge-guided calibration. Plug-and-play (+6.42% accuracy, 0.08M params). Dataset CU-Tree102. |
| **[AlfredsLapkovskis/MultimodalPlantClassifier](https://github.com/AlfredsLapkovskis/MultimodalPlantClassifier)** | 10 | Python | MIT | **Moyenne** — Multimodal deep learning (image + metadata). Neural architecture search (MFAS). PlantCLEF dataset. iOS app companion. Frontiers in Plant Science 2025. |
| **[vsriram24/pnw-tree-id](https://github.com/vsriram24/pnw-tree-id)** | — | Python | — | **Moyenne** — EfficientNetV2-S, 40 espèces, Flask web app. Pipeline complet iNaturalist → training → inference. Bon template pour app GeoSylva. |

### 12.4 Santé des forêts / Dépérissement (Diagnostic Engine)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[SamanthaBiegel/s2-forest-browning-monitoring](https://github.com/SamanthaBiegel/s2-forest-browning-monitoring)** | 2 | Python | AGPL-3.0 | **Très haute** — Monitoring pays entier dépérissement (Sentinel-2 10m). Autoencoder neural network pour anomalies NDVI. Suisse complète. Zarr datasets. **Directement applicable à la France**. ISPRS 2026. |
| **[s4rgax/ULISSE](https://github.com/s4rgax/ULISSE)** | — | Python | — | **Haute** — Forest disturbance detection Sentinel-2 multi-temporel. U-Net + ResNet50 + PEFT (LoRA/DoRA/HRA). XAI (band occlusion). 24GB VRAM. |
| **[SilvIA-development/SilvIA](https://github.com/SilvIA-development/SilvIA)** | — | Python/JS | — | **Moyenne** — Système complet monitoring forestier IA. Sentinel-2 + MODIS + ERA5. U-Net/DeepLabV3+. FastAPI + React + PostGIS. Architecture similaire à GSIE. |
| **[garydoranjr/tree-monitoring](https://github.com/garydoranjr/tree-monitoring)** | 1 | Python | — | **Moyenne** — Phenology + mortality from space. SegFormer, Mask R-CNN. Planet + drone imagery. Caltech/JPL. Pipeline complet acquisition → coreg → classification → NDVI. |

### 12.5 Ingestion de données satellite / pipelines (GIS Engine / ingestion)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[VTvito/cdse-client](https://github.com/VTvito/cdse-client)** | — | Python | MIT | **Très haute** — Client Python moderne pour Copernicus CDSE. Remplace sentinelsat. STAC search + OData download. Async, type hints, CLI. `pip install cdse-client`. **À utiliser pour Sentinel-1/2/3/5P**. |
| **[C4B-AI/c4b-nbs-pipeline](https://github.com/C4B-AI/c4b-nbs-pipeline)** | — | Python | — | **Très haute** — Pipeline ingestion Sentinel-1/2 + IoT sensors (LoRaWAN/MQTT). CDSE API, Sen2Cor, STAC metadata, Zarr output. **Architecture exacte de notre couche 2-3**. |
| **[sgofferj/python-sentinel-pipeline](https://github.com/sgofferj/python-sentinel-pipeline)** | — | Python | — | **Haute** — Pipeline automatique Sentinel-1/2 CDSE. NDVI, NBR, NDRE, NDBI. Fusion S1+S2. Notifications Apprise. .env config. |
| **[julianManning/cdse-sentinel2-pipeline](https://github.com/julianManning/cdse-sentinel2-pipeline)** | — | Python | — | **Haute** — High-throughput Sentinel-2 CDSE. OData + Keycloak OAuth2. Smart spatial thresholding (anti-redondance edge-tiles). Multi-threaded. Jupyter workflow. |
| **[developmentseed/stactools-ingest](https://github.com/developmentseed/stactools-ingest)** | — | Python | — | **Moyenne** — Infrastructure serverless STAC ingestion AWS (SNS/SQS → Lambda → pgstac). Cloud-native. Pour déploiement production. |

### 12.6 Humidité du sol / Pédologie (Pedology / Climate Engine)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[tuananhdao/soil-moisture](https://github.com/tuananhdao/soil-moisture)** | 1 | Python | — | **Haute** — Prédiction humidité sol avec Sentinel-2 NDVI + ERA5 + élévation. Surface + root zone. Penman-Monteith FAO-56. **Stack exacte GSIE**. |
| **[Sydney-Informatics-Hub/AgReFed-ML](https://github.com/Sydney-Informatics-Hub/AgReFed-ML)** | — | Python | LGPL3 | **Moyenne** — Gaussian Process regression pour soil properties 3D. Uncertainty quantification. Spatiotemporal models. Notebooks reproductibles. |
| **[pegasus-isi/soilmoisture-workflow](https://github.com/pegasus-isi/soilmoisture-workflow)** | — | Python | — | **Moyenne** — LSTM soil moisture forecasting. Open-Meteo ERA5-Land. Irrigation recommendation. Pegasus WMS. |
| **[Sly231/SoilWeatherPredictor](https://github.com/Sly231/SoilWeatherPredictor)** | 2 | Python | — | **Basse** — LSTM + SHAP explainability. Bon template pour intégration Pedology Engine. |

### 12.7 Détection feux par drone / AI vision (Ignis / app mobile)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[khangle2101/Real-Time-Fire-Smoke-Detection-Drone](https://github.com/khangle2101/Real-Time-Fire-Smoke-Detection-Drone)** | — | Python | — | **Très haute** — YOLOv11 + TensorRT sur Jetson Nano. Détection 2-stage (smoke → fire). MAVLink Pixhawk. GPS geo-tagged alerts. Telegram notifications. **Template pour app Ignis/Artemis**. |
| **[imnuman/fire-detection-yolo](https://github.com/imnuman/fire-detection-yolo)** | — | Python | — | **Haute** — YOLOv8 edge deployment Jetson. Thermal FLIR Lepton support. MQTT/HTTP alerts. `pip install` ready. |
| **[chri5tianlol/Territory-Project](https://github.com/chri5tianlol/Territory-Project)** | — | Python | — | **Haute** — Dual-engine: YOLOv8 + HSV heuristic fallback. GSD calculation, fire footprint area. Streamlit dashboard. D-Fire dataset. |
| **[ali-ibrahim-alshaikh/Drone_Project](https://github.com/ali-ibrahim-alshaikh/Drone_Project)** | — | Python | — | **Moyenne** — YOLOv8 + ROS Noetic + Gazebo. MAVLink. Distance estimation. Hexacopter F550. |
| **[varunlakshmanan11/FireDroneX](https://github.com/varunlakshmanan11/FireDroneX)** | — | Python | — | **Moyenne** — VOXL2 autonomous drone. DepthAnythingV2 + YOLOv8. ROS 2. Monocular depth estimation 3D. |

### 12.8 Backend géospatial / API (GSIE API)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[rupestre-campos/geofastmapAPI](https://github.com/rupestre-campos/geofastmapAPI)** | 4 | Python | — | **Très haute** — FastAPI + PostGIS async. OGC API Features compliant. Vector tiles (MVT/MBTiles/PMTiles). Streaming GeoJSONL. Redis workers. **Architecture très proche de GSIE API**. |
| **[notarious2/geolocations](https://github.com/notarious2/geolocations)** | 9 | Python | MIT | **Haute** — FastAPI + SQLAlchemy 2 + GeoAlchemy2 + asyncpg. Pydantic v2. Alembic. Docker. **Stack exacte GSIE API**. |
| **[matthew-lottly/spatial-data-api](https://github.com/matthew-lottly/spatial-data-api)** | — | Python | — | **Haute** — FastAPI + PostGIS backend pour monitoring stations environnementales. Threshold alerts, dashboard, tests. **Pattern direct pour GSIE**. |
| **[ChrisMcCarthyDev/geoalchemy-alembic-pydantic-fastapi-demo](https://github.com/ChrisMcCarthyDev/geoalchemy-alembic-pydantic-fastapi-demo)** | — | Python | — | **Moyenne** — Reference implémentation FastAPI + GeoAlchemy2 + Alembic + Pydantic. Dual DB (PostGIS prod / SpatiaLite dev). |
| **[kinuax/fastapi-strawberry-postgis](https://github.com/kinuax/fastapi-strawberry-postgis)** | 1 | Python | MIT | **Basse** — FastAPI + Strawberry GraphQL + PostGIS. Pour alternative GraphQL API. |

### 12.9 Visualisation 3D / Hub Unreal Engine

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[CesiumGS/cesium-unreal](https://github.com/CesiumGS/cesium-unreal)** | 1207 | C++ | Apache 2.0 | **Essentiel** — Plugin Cesium pour Unreal Engine. 3D Tiles, WGS84 globe, photogrammetry streaming. Support UE 5.5-5.8. **Déjà intégré dans le Hub GSIE**. v2.28.0 (juillet 2026). |

### 12.10 Knowledge Graph / Ontologie écologique (Knowledge / Evidence Engine)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[EnvironmentOntology/envo](https://github.com/EnvironmentOntology/envo)** | — | OWL/Python | — | **Très haute** — Environment Ontology (OBO Foundry). Biomes, environmental materials, ecological processes. OWL/OBO. **Référence ontologique pour Knowledge Engine**. |
| **[fusion-jena/KG-for-Biodiversity-Exploratories-Metadata](https://github.com/fusion-jena/KG-for-Biodiversity-Exploratories-Metadata)** | — | Python | — | **Haute** — Knowledge Graph RDF/OWL pour biodiversity. Semantic Units framework. 502K triples. R2RML mappings. LLM applications sur graph. |
| **[earth-metabolome-initiative/metrin-kg](https://github.com/earth-metabolome-initiative/metrin-kg)** | — | Python | — | **Moyenne** — KG intégrant plant metabolites + traits (TRY) + interactions (GloBI). Wikidata SPARQL. RDF triples. Pour Correlation Engine. |
| **[saiful1105020/KnowUREnvironment](https://github.com/saiful1105020/KnowUREnvironment)** | — | Python | — | **Moyenne** — KG climate change 210K entités, 411K RDF triples. Extraction automatique from literature. Pour Evidence Engine. |
| **Ecolink Model (ELM)** | — | LinkML | — | **Moyenne** — Schema pour KG écologiques. LinkML + Biolink. ELMO ontology (ENVO + NCBITaxon + RO). Pour structurer Knowledge Engine. |

### 12.11 Carbone forestier / Biomasse (Forest Dynamics / Climate Engine)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[jtran2509/forest_carbon_mrv](https://github.com/jtran2509/forest_carbon_mrv)** | — | Python | — | **Très haute** — Pipeline ML carbone forestier Sentinel-2 + ESA WorldCover. Attention U-Net, hard negative mining, mixed precision. AWS SageMaker. 600GB+ données. Streamlit demo. **Pour Forest Dynamics + Climate**. |
| **[priamus-lab/ReUse](https://github.com/priamus-lab/ReUse)** | — | Python | — | **Haute** — Regressive UNet pour carbone + AGB. ESA CCI Biomass + Sentinel-2. Sans observations in situ. CV 8-fold. Publié J. Imaging 2023. |
| **[Adityaraj-Gupta-JI/EcoAudit-AI](https://github.com/Adityaraj-Gupta-JI/EcoAudit-AI)** | 4 | Python | — | **Haute** — dMRV carbone multi-pool (AGB + roots + SOC). Sentinel-1/2 fusion. BiLSTM + Monte Carlo uncertainty. GEDI ground-truth. FastAPI. Rapports PDF audit. |
| **[vertify-earth/biomass-prediction-pixelwise](https://github.com/vertify-earth/biomass-prediction-pixelwise)** | — | Python | — | **Haute** — AGB pixel-level StableResNet. Multi-sensor (S1+S2+Landsat+PALSAR+DEM). R²=0.87, RMSE=28.7 Mg/ha. HuggingFace + Gradio deploy. |
| **[geofoluugm/WP-1.6-Geo-AI-for-Carbon-Storage-Assessment](https://github.com/geofoluugm/WP-1.6-Geo-AI-for-Carbon-Storage-Assessment)** | 1 | Python | Apache 2.0 | **Moyenne** — Geo-AI AGB + LULC. LiDAR + Sentinel + PlanetScope. IPCC Tier 2/3. Shallow + deep learning. |

### 12.12 Downscaling météo / AROME (Climate Engine)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[CyrilJl/MeteoFetch](https://github.com/CyrilJl/meteofetch)** | 16 | Python | GPL v2 | **Très haute** — Client Python pour AROME + ARPEGE + IFS ECMWF. **Sans clé API**. Retour xarray DataArray. `pip install meteofetch`. **Outil direct pour Climate Engine**. |
| **[lorisdanjou/AromeDownscaling-ddpm-pytorch](https://github.com/lorisdanjou/AromeDownscaling-ddpm-pytorch)** | — | Python | — | **Très haute** — Downscaling AROME par DDPM (Denoising Diffusion Probabilistic Model). Stage Météo-France. PyTorch. Ensembles. **Pour Climate Engine haute résolution**. |
| **[DSIP-FBK/DiffScaler](https://github.com/DSIP-FBK/DiffScaler)** | 25 | Python | MIT | **Haute** — Latent Diffusion Model pour downscaling ERA5 → 2km. Température + vent. Modèles pré-entraînés sur Zenodo. Publié GMD 2025. |
| **[louisletoumelin/neural_network_and_devine](https://github.com/louisletoumelin/neural_network_and_devine)** | — | Python | — | **Moyenne** — Correction + downscaling vent AROME 1300m → 30m. DEVINE + réseaux de neurones. Montagnes. |
| **[SDINAHET/wrf-bretagne-local-forecast](https://github.com/SDINAHET/wrf-bretagne-local-forecast)** | — | Python | — | **Moyenne** — WRF local Bretagne 9km/3km. Comparaison GFS/AROME/Open-Meteo. Pipeline Python + PostgreSQL. IA correction. |

### 12.13 Modèles de distribution d'espèces (Botanical / Correlation Engine)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[earth-chris/elapid](https://github.com/earth-chris/elapid)** | 69 | Python | MIT | **Très haute** — MaxEnt en Python. sklearn conventions. rasterio + geopandas. MaxentModel + NicheEnvelopeModel. Feature transformers (product, hinge). **Pour Correlation Engine + Botanical**. v1.0.3 (2026). |
| **[osgeokr/qmaxent](https://github.com/osgeokr/qmaxent)** | — | Python | — | **Haute** — Plugin QGIS pour MaxEnt SDM. Intègre elapid. Cross-validation spatiale, jackknife, projection habitat. **Pour QGISIA + Botanical**. QGIS 3.44+. |
| **[alrobles/maxentcpp](https://github.com/alrobles/maxentcpp)** | — | C++/R | — | **Moyenne** — Reimplementation C++17 MaxEnt. R bindings Rcpp. Haute performance. Lambda files, prediction maps, response curves. |

### 12.14 Risque incendie / Humidité des combustibles (Ignis / Diagnostic Engine)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[Perello-nico/DFMC_model](https://github.com/Perello-nico/DFMC_model)** | — | Python | EUPL 1.2 | **Très haute** — Dead Fuel Moisture Content model sub-daily. Paramètres par type de combustible. Calibration Particle Swarm. Publié Environmental Modelling & Software 2025. **Pour Ignis risque feu**. |
| **[jh-206/fmc_transfer](https://github.com/jh-206/fmc_transfer)** | — | Python | — | **Haute** — Transfer learning pour fuel moisture (1h, 10h, 100h fuels). LSTM + time-warping. Basé sur openwfm/ml_fmda. |
| **[dustinlit/California-Wildfire-Ignition-ML-Modeling](https://github.com/dustinlit/California-Wildfire-Ignition-ML-Modeling)** | — | Python | — | **Haute** — ML ignition risk. XGBoost + Random Forest. 6 ans données. SHAP + Feature Ablation. TerraClimate + FWI + WUI. **Pattern pour Diagnostic Engine**. |
| **[taimoor789/Forest-Fire-Predictor](https://github.com/taimoor789/Forest-Fire-Predictor)** | — | Python | — | **Moyenne** — API FastAPI FWI canadien (FFMC, DMC, DC, ISI, BUI, FWI, DSR). 15 000+ cellules grille. Mise à jour horaire. AWS. **Template API pour Ignis**. |

### 12.15 Croissance forestière / Yield models (Forest Dynamics Engine)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[mihiarc/pyfvs](https://github.com/mihiarc/pyfvs)** | 2 | Python | MIT | **Très haute** — Implémentation Python USDA Forest Vegetation Simulator. 10 variantes régionales, 500+ espèces. Croissance arbre individuel. Thinning, harvest. Taper-based volume. `pip install fvs-python`. **Modèle de base pour Forest Dynamics**. |
| **[Silviculturalist/pyforestry](https://github.com/Silviculturalist/pyforestry)** | 4 | Python | MIT | **Haute** — Toolkit Python forest science. Growth & yield models. Site index, climate utilities (Suède). Timber pricing, taper, bucking. OO helpers trees/stands/plots. |
| **[AbbasNabhani/TreeSim](https://github.com/AbbasNabhani/TreeSim)** | 15 | Python | Apache 2.0 | **Moyenne** — Simulateur arbre individuel distance-independent. 3D visualization. Parallel computing. Forest carbon, ecosystem services. |

### 12.16 Plugins QGIS forestiers (QGISIA)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[karasinski-mauro/Netflora](https://github.com/karasinski-mauro/Netflora)** | 7 | Python | AGPL-3.0 | **Très haute** — Plugin QGIS inventaire forestier par drone. IA détection espèces (ONNX). Orthomosaics tiled inference. Flight planner Litchi. PDF reports. **Pour QGISIA + Forest Dynamics**. |
| **[b-lack/qgis-fim-plugin](https://github.com/b-lack/qgis-fim-plugin)** | 4 | Python | GPL v3 | **Haute** — Plugin QGIS Forest Inventory & Monitoring. Inventaire régénération + influence gibier. Brandenburg. jsonschema. |
| **[RichterV/ForestPyTools-QGIS-module](https://github.com/RichterV/ForestPyTools-QGIS-module)** | 2 | Python | — | **Moyenne** — Plugin QGIS allocation placettes inventaire. scikit-learn. |

### 12.17 Apps mobiles forestières (GeoSylva / Ignis / Artemis)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[NeooeN45/GeoSylva](https://github.com/NeooeN45/GeoSylva)** | — | Kotlin | GPL-3.0 | **Essentiel** — App Android inventaire forestier 100% offline. Kotlin + Jetpack Compose. 12 couches carto, 7 méthodes cubage, IBP CNPF. **Déjà dans le repo GSIE** (`apps/GeoSylva/`). |
| **[aashir-athar/forest-sentry](https://github.com/aashir-athar/forest-sentry)** | — | TS/RN | MIT | **Très haute** — App offline-first forêt. TensorFlow Lite on-device leaf health. GPS tree registry. PostGIS zones. Active-learning loop OTA. Export CSV/GeoJSON. **Architecture très proche GeoSylva**. |
| **[wri/forest-watcher](https://github.com/wri/forest-watcher)** | — | JS/Kotlin | — | **Haute** — App Android+iOS Global Forest Watch. GLAD + VIIRS alerts. Custom layers (GeoJSON, KML, MBTiles). Offline sync. **Pour Ignis mobile**. |
| **[Vedant2402/Smoke-Forecast-Visualizer](https://github.com/Vedant2402/Smoke-Forecast-Visualizer)** | 1 | Kotlin | — | **Moyenne** — App Android Kotlin + Jetpack Compose. NASA FIRMS API + Google Maps + Retrofit. Wildfire heatmap. **Template pour Ignis/Artemis**. |
| **[Tian-Tan/fire-proof](https://github.com/Tian-Tan/fire-proof)** | — | Python/RN | — | **Moyenne** — Wildfire safety assistant. NASA FIRMS + OpenRouteService évacuation. LLM guidance. React Native + FastAPI. |

### 12.18 Explainable AI pour modèles environnementaux (Validation / Reasoning Engine)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[m-altieri/graph-xai](https://github.com/m-altieri/graph-xai)** | 6 | Python | MIT | **Haute** — Framework XAI end-to-end pour spatio-temporel. LSTM, GRU, Bi-LSTM, Attention-LSTM, GCN-LSTM. SHAP, LIME, GNNExplainer. **Pour Validation Engine**. |
| **[SameerSenapati17/MultiModal-AQI-XAI-Dashboard](https://github.com/SameerSenapati17/MultiModal-AQI-XAI-Dashboard)** | — | Python | — | **Moyenne** — CNN+LSTM + XAI (Grad-CAM, SHAP, LIME). FastAPI. Counterfactuals. **Pattern pour Validation Engine**. |
| **[Ali-Forootani/RELLM](https://github.com/Ali-Forootani/RELLM)** | — | Python | — | **Moyenne** — LLM + SHAP pour scenario analytics forestry/agriculture. Random Forest + DNN + XGBoost surrogates. Correlation clustering. **Pour Reasoning Engine + Correlation**. |

### 12.19 Résumé — priorités d'intégration

**Priorité 1 — Intégration directe (immédiate)** :
1. `propagator` (CIMA) → Ignis Simulation Engine — cellular automata wildfire
2. `cdse-client` → GIS Engine — téléchargement Sentinel CDSE
3. `cesium-unreal` → Hub — déjà intégré, maintenu à jour
4. `envo` → Knowledge Engine — ontologie environnementale de référence
5. `c4b-nbs-pipeline` → Architecture ingestion — template pipeline Sentinel + IoT
6. `meteofetch` → Climate Engine — client AROME/ARPEGE sans clé API
7. `elapid` → Correlation Engine — MaxEnt Python pour distribution d'espèces
8. `pyfvs` → Forest Dynamics — croissance arbre individuel (FVS Python)
9. `DFMC_model` → Ignis — humidité combustibles sub-daily
10. `GeoSylva` → App mobile — déjà dans le repo

**Priorité 2 — Étude approfondie (court terme)** :
11. `ForestFormer3D` + `ForAINet` → Forest Dynamics — segmentation LiDAR HD IGN
12. `GlobalGeoTree` → Botanical Engine — 6.3M occurrences + Sentinel-2
13. `s2-forest-browning-monitoring` → Diagnostic Engine — dépérissement Sentinel-2
14. `PyTorchFire` → Ignis — CA différentiable GPU calibration
15. `geofastmapAPI` → GSIE API — architecture FastAPI + PostGIS + OGC
16. `forest_carbon_mrv` → Forest Dynamics — carbone Sentinel-2 + Attention U-Net
17. `AromeDownscaling-ddpm` → Climate Engine — downscaling AROME par diffusion
18. `forest-sentry` → GeoSylva — architecture offline-first + TFLite + active learning
19. `Netflora` → QGISIA — plugin QGIS inventaire drone + IA
20. `qmaxent` → QGISIA — plugin QGIS MaxEnt SDM

**Priorité 3 — Veille / inspiration (moyen terme)** :
21. `ForeFire` → Ignis — couplage fire-atmosphère CNRS
22. `TreeLearn` → Forest Dynamics — segmentation TLS ground-based
23. `neural-ca-wildfire` → Ignis — CNN + CA probabiliste (JAX)
24. `ULISSE` → Diagnostic — PEFT LoRA/DoRA for forest disturbance
25. `fire-detection-yolo` + `Territory-Project` → App Ignis/Artemis — drone YOLOv8
26. `EcoAudit-AI` → Forest Dynamics — dMRV multi-pool carbone + GEDI
27. `DiffScaler` → Climate Engine — LDM downscaling ERA5 → 2km
28. `California-Wildfire-Ignition-ML` → Diagnostic — XGBoost + SHAP ignition risk
29. `pyforestry` → Forest Dynamics — growth & yield models européens
30. `graph-xai` → Validation Engine — XAI spatio-temporel

---

## 13. Modèles d'IA open source, LLM et plateformes pour GSIE

> Recherche effectuée en juillet 2026 — modèles de fondation géospatiaux, LLM scientifiques, RAG environnementaux, infrastructure de déploiement et benchmarks.

### 13.1 Modèles de fondation géospatiaux (GIS / Forest Dynamics / Climate Engine)

| Projet / Modèle | Params | Source | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[NASA-IMPACT/Prithvi-EO-2.0](https://github.com/NASA-IMPACT/Prithvi-EO-2.0)** | 300M / 600M | HLS (Landsat+Sentinel-2) 30m | MIT | **Essentiel** — Modèle de fondation NASA+IBM. 4.2M time series globaux. Temporal + location embeddings. Fine-tuning via TerraTorch. **Pour tous les moteurs utilisant Sentinel-2/Landsat**. 270 stars. GEO-Bench: 75.6% (+8% vs v1). |
| **[ibm-nasa-geospatial (HuggingFace)](https://huggingface.co/ibm-nasa-geospatial)** | 100M-600M | HLS + MERRA-2 | Open | **Essentiel** — Famille complète Prithvi: EO-1.0, EO-2.0 (300M/600M), WxC-1.0 (weather/climate). Fine-tuned: canopy height, biomass, flood detection, land cover. **Hub central pour tous les modèles géospatiaux GSIE**. |
| **[ibm-granite/granite-geospatial-canopyheight](https://huggingface.co/ibm-granite/granite-geospatial-canopyheight)** | — | HLS L30 + GEDI L2A | Open | **Très haute** — Fine-tuned Prithvi pour canopy height. Swin-B + UPerNet. 15 biomes. **Pour Forest Dynamics + estimation carbone**. |
| **[ibm-granite/granite-geospatial-biomass](https://huggingface.co/ibm-granite/granite-geospatial-biomass)** | — | HLS L30 + GEDI L4A | Open | **Très haute** — Fine-tuned Prithvi pour above-ground biomass. Même architecture. **Pour Forest Dynamics + Climate Engine**. |
| **[naturecodeproject/earth](https://huggingface.co/naturecodeproject/earth)** | 10.9M | Sentinel-2 + OpenLandMap | Open | **Haute** — Multi-modal Temporal ViT. Forest cover + biomass + deforestation + soil properties (SOC, clay, sand). 4 quarterly timestamps. Edge deployment (nano). **Pour Forest Dynamics + Pedology**. |
| **[jorlrodriguezg/floro](https://huggingface.co/jorlrodriguezg/floro)** | — | Multispectral + DEM | Open | **Haute** — FLORO: foundation model écologique multi-scale. Semantic seg, canopy height, biomass, nitrogen, carbon. ViT + masked autoencoding. |
| **[simonreise/forest-segmentation-2025](https://huggingface.co/simonreise/forest-segmentation-2025)** | — | Sentinel-2 time series | Open | **Moyenne** — SegFormer pour forêt boréale: espèces dominantes, classe productivité, type, âge, volume. **Pour Forest Dynamics boréale**. |

### 13.2 LLM & RAG pour science environnementale (Knowledge / Evidence / Reasoning Engine)

| Projet | Stars | Langue | Licence | Pertinence GSIE |
|---|---|---|---|---|
| **[project-araia/WildfireGPT](https://github.com/project-araia/WildfireGPT)** | 16 | Python | Apache 2.0 | **Très haute** — Multi-agent RAG pour wildfire. LLM + littérature scientifique CIACC. User profiles personnalisés. Publié npj Climate Action 2025. **Pour Ignis + Reasoning Engine**. |
| **[GeoGPT-Research-Project/GeoGPT-RAG](https://github.com/GeoGPT-Research-Project/GeoGPT-RAG)** | 56 | Python | Apache 2.0 | **Très haute** — RAG géoscience. GeoEmbedding (7B, Mistral-based) + GeoReranker (568M, BGE-M3). GeoRAG-QA benchmark. **Pour Knowledge Engine + Evidence Engine**. |
| **[Jo-Pan/TaxoDrivenKG](https://github.com/Jo-Pan/TaxoDrivenKG)** | — | Python | — | **Très haute** — KG construction depuis littérature scientifique. Taxonomy-anchored extraction + RAG validation. Case study: climate science. ACL 2025. **Pour Knowledge Engine + Evidence Engine**. |
| **[ejokhan/hydro-rag](https://github.com/ejokhan/hydro-rag)** | — | Python | — | **Haute** — RAG 8 618 papers (PubMed + ArXiv). 5 chunking strategies. FAISS. Llama 3.3 70B via Groq. **Architecture template pour Evidence Engine**. |
| **[Smit1400/EcoMed-Expert-llama-RAG-chainlit-FAISS](https://github.com/Smit1400/EcoMed-Expert-llama-RAG-chainlit-FAISS)** | — | Python | — | **Moyenne** — RAG environmental science + Llama 2 7B + LangChain + FAISS + Chainlit UI. Bon template simple. |

### 13.3 NVIDIA NIM & infrastructure IA (Climate / Simulation / Reasoning)

| Ressource | Type | Pertinence GSIE |
|---|---|---|
| **[NVIDIA NIM Microservices](https://developer.nvidia.com/blog/accelerating-scientific-literature-reviews-with-nvidia-nim-microservices-for-llms/)** | LLM serving | **Très haute** — NIM pour LLM deployment. Llama 3.1 8B fine-tuned LoRA. nv-ingest PDF → structured JSON. 25x speedup littérature scientifique. **Pour Evidence Engine ingestion papers**. |
| **[NVIDIA Earth-2 FourCastNet NIM](https://docs.nvidia.com/nim/earth-2/fourcastnet/latest/quickstart-guide.html)** | Weather forecasting | **Très haute** — NIM pour prévisions météo globales. FourCastNet neural operator. ERA5 input. API HTTP `/v1/infer`. Streaming résultats. **Pour Climate Engine + Simulation Engine**. |
| **[NVIDIA TerraTorch](https://github.com/IBM/terratorch)** | ML toolkit | **Haute** — Framework IBM pour fine-tuning Prithvi/geospatial foundation models. PyTorch Lightning. **Pour adapter Prithvi aux forêts françaises**. |

### 13.4 Microsoft Azure AI & AI Foundry (GSIE API / Ignis / Diagnostic)

| Projet | Stars | Langue | Pertinence GSIE |
|---|---|---|---|
| **[microsoft/AIforEarthDataSets](https://github.com/microsoft/AIforEarthDataSets)** | 313 | Python | **Très haute** — Catalogue datasets Azure Planetary Computer: Sentinel-1/2/3/5P, Landsat, MODIS, TerraClimate, GBIF, Harmonized Biomass, MTBS. **Source directe pour GIS Engine**. |
| **[Hardcoreprawn/azure-workflow-for-kml-satellite](https://github.com/Hardcoreprawn/azure-workflow-for-kml-satellite)** | — | Python | **Très haute** — Pipeline Azure Functions + Planetary Computer. KML → satellite imagery → NDVI + fire + flood + EUDR compliance. Azure AI Foundry narratives. **Architecture exacte pour GSIE ingestion + analyse**. 1315 tests. |
| **[RobertDalton/Ignis-Sentinels](https://github.com/RobertDalton/Ignis-Sentinels)** | — | Python | **Très haute** — Multi-agent wildfire resilience. 3rd Place Microsoft Innovation Challenge 2025. Azure AI Foundry + FastAPI + CosmosDB. NASA FIRMS + Sentinel-2 + VIIRS. **Nom similaire à Ignis GSIE — architecture directement applicable**. |
| **[Gerald-mut/Sauti-Porini-Js](https://github.com/Gerald-mut/Sauti-Porini-Js)** | — | Node.js | **Haute** — Agent environmental protection Azure AI Foundry. State machine + LLM hybride. NASA FIRMS + USSD citizen reports. **Pattern pour Ignis + app mobile**. |
| **[Microsoft AI for Good Lab — Wildfire Framework](https://news.microsoft.com/source/features/ai/ai-alberta-canada-wildfire-firefighting/)** | — | — | **Moyenne** — Framework prédiction risque wildfire. Azure ML. Alberta Wildfire + AltaML. Satellite + weather + carbon + human behaviour. **Référence méthodologique pour Diagnostic Engine**. |

### 13.5 Déploiement LLM self-hosted (Reasoning / Knowledge / Validation Engine)

| Outil | Type | Pertinence GSIE |
|---|---|---|
| **[Ollama](https://ollama.com/)** | LLM runtime | **Très haute** — Déploiement LLM local ultra-simple. `ollama pull llama3.3`. GGUF quantization. OpenAI-compatible API. **Pour dev/exploration Reasoning Engine**. Single-user, 62 tok/s (Llama 3.1 8B). |
| **[vLLM](https://github.com/vllm-project/vllm)** | LLM server | **Très haute** — Production inference server. PagedAttention, continuous batching. 920 tok/s (50 users). **Pour production GSIE API LLM endpoints**. OpenAI-compatible. 30K stars. |
| **[LocalAI](https://localai.io/)** | LLM runtime | **Haute** — Drop-in replacement OpenAI API. Broadest model support (GGUF, ONNX, TensorRT). **Pour compatibilité existante**. |
| **[Open-WebUI](https://github.com/open-webui/open-webui)** | UI + RAG | **Haute** — Interface ChatGPT-like pour Ollama/vLLM. RAG intégré (Docling + Qdrant). PostgreSQL. **Pour UI interne GSIE + Evidence Engine**. |
| **[Docling](https://github.com/DS4SD/docling)** | PDF parsing | **Haute** — Extraction PDF scientifiques → JSON structuré (text, tables, figures). IBM. **Pour Evidence Engine ingestion papers**. |

### 13.6 Benchmarks & évaluation (Validation Engine)

| Projet | Stars | Pertinence GSIE |
|---|---|---|
| **[iDEA-iSAIL-Lab-UIUC/ClimateBench-M](https://github.com/idea-isail-lab-uiuc/climatebench-m)** | 10 | **Très haute** — Benchmark multi-modal climat. ERA5 time series + NOAA events + NASA HLS satellite. Weather forecasting + anomaly detection. HuggingFace. **Pour Validation Engine + Climate Engine**. |
| **[ClimAgent + ClimaBench](https://github.com/usail-hkust/ClimAgent)** | — | **Très haute** — Agent LLM autonome pour climate science. ClimaBench: 220 problèmes réels 2000-2025. 5 catégories: query, concept, prediction, causal, policy. +40% vs baselines. **Pour Reasoning Engine + Validation**. |
| **[CBGB — Cloud-Based Geospatial Benchmark](https://github.com/google/earthengine-community/tree/master/experimental/cbgb_benchmark)** | — | **Haute** — 45 scénarios géospatiaux pratiques. LLM agents + Earth Engine. Error-correction feedback. **Pour évaluer capacités géospatiales des LLM GSIE**. |
| **[GeoAnalystBench](https://arxiv.org/html/2509.05881)** | — | **Moyenne** — 50 tâches Python GIS réelles. ChatGPT-4o-mini 95% validity. DeepSeek-R1-7B 48.5%. **Référence pour évaluer LLM sur workflows GIS**. |
| **[ClimaBench (NLP)](https://arxiv.org/pdf/2301.04253)** | — | **Moyenne** — Benchmark NLP climate change. Classification + QA. CLIMA-CDP + CLIMA-INSURANCE. ClimateBERT. **Pour évaluer LLM sur textes climatiques**. |

### 13.7 Résumé — priorités d'intégration IA/LLM

**Priorité 1 — Intégration directe (immédiate)** :
1. `Prithvi-EO-2.0` (600M) → GIS Engine — foundation model géospatial NASA+IBM, fine-tuning forêt française
2. `TerraTorch` → Toolkit fine-tuning Prithvi — adapter aux forêts françaises
3. `meteofetch` → Climate Engine — déjà identifié section 12
4. `Ollama` → Dev/exploration — LLM local pour Reasoning Engine prototypage
5. `vLLM` → Production — serving LLM pour GSIE API
6. `AIforEarthDataSets` → GIS Engine — catalogue Planetary Computer
7. `Docling` → Evidence Engine — extraction PDF papers → JSON

**Priorité 2 — Étude approfondie (court terme)** :
8. `granite-geospatial-canopyheight` + `granite-geospatial-biomass` → Forest Dynamics — modèles fine-tuned prêts
9. `WildfireGPT` → Ignis + Reasoning — multi-agent RAG wildfire
10. `GeoGPT-RAG` → Knowledge Engine — RAG géoscience + GeoEmbedding/GeoReranker
11. `TaxoDrivenKG` → Knowledge Engine — KG depuis littérature + taxonomy
12. `Ignis-Sentinels` → Ignis — architecture multi-agent Azure AI Foundry
13. `azure-workflow-for-kml-satellite` → GIS Engine — pipeline Azure Functions + Planetary Computer
14. `ClimateBench-M` → Validation Engine — benchmark multi-modal climat
15. `ClimAgent + ClimaBench` → Reasoning Engine — agent autonome climate science

**Priorité 3 — Veille / inspiration (moyen terme)** :
16. `NVIDIA NIM` → Infrastructure — déploiement LLM microservices
17. `Earth-2 FourCastNet NIM` → Climate Engine — prévisions météo neural operator
18. `naturecode-earth` → Forest Dynamics + Pedology — nano ViT multi-modal
19. `FLORO` → GIS Engine — foundation model écologique multi-scale
20. `Sauti-Porini` → Ignis mobile — pattern state machine + Azure AI Foundry
21. `hydro-rag` → Evidence Engine — template RAG 8K+ papers
22. `Open-WebUI` → UI interne — interface ChatGPT-like + RAG intégré
23. `CBGB` + `GeoAnalystBench` → Validation — benchmarks géospatiaux LLM

---

## 14. LLM sur téléphone — technologies, compatibilités et performances

> Recherche exhaustive juillet 2026 — toutes les solutions pour exécuter des LLM localement sur smartphone, classées du plus efficace au moins efficace.

### 14.1 Solutions constructeurs (intégrées, fermées)

| Solution | Modèle | Téléphones compatibles | Performance | Licence / Prix | Pertinence GSIE |
|---|---|---|---|---|---|
| **[Apple Intelligence — AFM on-device](https://machinelearning.apple.com/research/introducing-apple-foundation-models)** | ~3B params (AFM-on-device) | iPhone 15 Pro/Pro Max, iPhone 16全系, iPad M1+, Mac M1+ | **30 tok/s** (generation), **0.6ms/token** TTFT. 2-bit QAT (3.7 bpw). LoRA adapters dynamiques. | **Gratuit** (intégré iOS 18+/19+) | **Haute** — Foundation Models framework Swift. Guided generation, tool calling, LoRA fine-tuning. **Pour GeoSylva iOS si applicable**. |
| **[Google Gemini Nano — Android AICore](https://developer.android.com/ai/gemini-nano)** | Gemini Nano (v1/v2/v3) | Pixel 9/10全系, Samsung S25/S26全系, OnePlus 13/15, Xiaomi 15/17, OPPO Find X8/X9, vivo X200/X300, Honor Magic 7/8, Motorola Razr 60 Ultra, realme GT 7, iQOO 13/15, POCO F7/F8, Sharp AQUOS R11 | Non communiqué officiellement. Estimations: ~20-40 tok/s selon SoC. | **Gratuit** (intégré Android 14+) | **Très haute** — ML Kit GenAI APIs: summarization, proofreading, rewriting, image description. **Pour GeoSylva Android**. AICore gère distribution + safety. |
| **[Samsung Galaxy AI](https://www.samsung.com/galaxy-ai/)** | Gemini Nano (Samsung customization) | Galaxy S24全系, S25全系, S26全系, Z Fold6/7, Z Flip6/7 | Identique Gemini Nano | **Gratuit** (intégré One UI 6.1+) | **Moyenne** — Features Samsung-specific (Circle to Search, Live Translate). Pas d'API développeur directe. |
| **[MediaTek NeuroPilot](https://www.mediatek.com/ai-technology)** | APU/NPU MediaTek | Dimensity 9300/9400/9500 (OPPO Find X7, Vivo Pad3 Pro, OnePlus 12) | Variable selon SoC. Dimensity 9300: meilleur CPU decoding 2024. | **Gratuit** (SDK constructeur) | **Moyenne** — SDK pour NPU MediaTek. Moins documenté que Qualcomm. |

### 14.2 Solutions open source — moteurs d'inférence (classées par efficacité)

| Moteur | Plateforme | Backend | Modèles | Performance | Licence | GitHub |
|---|---|---|---|---|---|---|
| **[mllm-NPU](https://arxiv.org/html/2407.05858v1)** | Android (Xiaomi 14, Redmi K60 Pro) | **NPU** (Hexagon) | Qwen1.5-1.8B, Gemma-2B, Phi-2, Llama-2-7B, Mistral-7B | **1000+ tok/s prefill** (Qwen 1.8B). 22.4x faster prefill. 30.7x energy savings. | Open source | — |
| **[Transformer-Lite](https://arxiv.org/pdf/2403.20041)** | Android (OPPO Find X7: Dimensity 9300, Find X7 Ultra: Snapdragon 8 Gen 3) | **GPU** (Mali-G720, Adreno 750) | Gemma 2B, Qwen1.5 4B, ChatGLM2 6B, Llama2 7B, Qwen1.5 14B | **330 tok/s prefill / 30 tok/s decode** (Gemma 2B). **121 tok/s prefill / 14 tok/s decode** (ChatGLM2 6B). 10x faster than MLC-LLM prefill. | Open source | — |
| **[Qualcomm AI Hub (GENIE)](https://aihub.qualcomm.com/)** | Android (Samsung S25: Snapdragon 8 Elite) | **NPU** (Hexagon HTP) | Llama-3-8B, Llama-3.1-8B, Qwen3-4B, Qwen2.5-VL-7B, 207+ models | **16.4 tok/s** (Llama 3.1 8B, Snapdragon 8 Elite Gen 5). **23.2 tok/s** (Snapdragon X2 Elite). TTFT 0.1s. w4a16. | **Gratuit** (SDK), devices hosted payants | [qualcomm/ai-hub-models](https://github.com/qualcomm/ai-hub-models) |
| **[LiteRT-LM](https://developers.google.com/edge/litert-lm)** | Android, iOS, Web, Desktop, IoT | **GPU + NPU + CPU** | Gemma 4 E2B/E4B, Gemma 3 1B, Qwen, Phi-4, Llama, FunctionGemma | **52 tok/s decode GPU** (Gemma 4 E2B, Samsung S26 Ultra). **56 tok/s decode GPU** (iPhone 17 Pro). **3808 tok/s prefill GPU**. MTP >2x decode. | **Gratuit** (Apache 2.0) | [google-ai-edge/LiteRT-LM](https://github.com/google-ai-edge/LiteRT-LM) (6K stars) |
| **[MLC LLM](https://github.com/mlc-ai/mlc-llm)** | Android (OpenCL Adreno/Mali), iOS (Metal), Web (WebGPU), macOS, Windows, Linux | **GPU** (OpenCL, Metal, Vulkan) | Llama 3 8B, Phi-2, Gemma, Qwen, Vicuna 7B | ~10-20 tok/s (Llama 3 8B Q4, Samsung S23). OpenAI-compatible API. | **Gratuit** (Apache 2.0) | [mlc-ai/mlc-llm](https://github.com/mlc-ai/mlc-llm) |
| **[llama.cpp + OpenCL](https://github.com/InquiringMinds-AI/llama-droid)** | Android (Snapdragon 8 Gen 1/2/3/Elite) | **GPU** (Adreno OpenCL) | Tous modèles GGUF | **63.5 tok/s** (Qwen2.5-0.5B Q4_0, S25). **34.5 tok/s** (Qwen2.5-1.5B). **18.5 tok/s** (Llama-3.2-3B). **16.6 tok/s** (Qwen3-1.7B Q8_0, S24 Ultra). | **Gratuit** (MIT) | [InquiringMinds-AI/llama-droid](https://github.com/InquiringMinds-AI/llama-droid) |
| **[llama.cpp (CPU)](https://github.com/ggerganov/llama.cpp)** | Android (Termux), iOS | **CPU** | Tous modèles GGUF | **17 tok/s** (1B model, iPhone 15 Pro, 2 threads F16). **16.25 tok/s** (Qwen 0.5B Q5, Snapdragon 855). 7.6 tok/s (Qwen 1.5B Q3). | **Gratuit** (MIT) | [ggerganov/llama.cpp](https://github.com/ggerganov/llama.cpp) |
| **[MediaPipe LLM Inference](https://developers.google.com/edge/mediapipe/solutions/genai/llm_inference)** | Android, iOS, Web | **CPU + GPU** | Gemma 2B/7B, Gemma-2 2B, Gemma-3 1B, Gemma-3n E2B/E4B, Phi-2, Falcon 1B, StableLM 3B | Variable selon device. LoRA support (Gemma, Phi-2). | **Gratuit** (Apache 2.0) | ⚠️ **Maintenance mode** — migrer vers LiteRT-LM |
| **[ONNX Runtime Mobile](https://onnxruntime.ai/)** | Android, iOS | **CPU + QNN** | Tous modèles ONNX | **0.21 tok/s** (Phi-4-mini 3.8B, CPU). 0.31 tok/s (QNN HTP, partiel). Très lent pour LLM. | **Gratuit** (MIT) | [microsoft/onnxruntime](https://github.com/microsoft/onnxruntime) |
| **[MNN (Alibaba)](https://github.com/alibaba/MNN)** | Android, iOS | **CPU + GPU** | Qwen, Llama, ChatGLM | ~7-15 tok/s (1.8B, selon device). Moins optimisé que llama.cpp. | **Gratuit** (Apache 2.0) | [alibaba/MNN](https://github.com/alibaba/MNN) |

### 14.3 Projets GitHub indépendants et benchmarks

| Projet | Stars | Description | Device testé | Performance | Licence |
|---|---|---|---|---|---|
| **[InquiringMinds-AI/llama-droid](https://github.com/InquiringMinds-AI/llama-droid)** | — | llama.cpp + OpenCL Adreno GPU. No root. Termux. | Samsung Galaxy S25 (Snapdragon 8 Elite) | 63.5 tok/s (0.5B), 34.5 (1.5B), 18.5 (3B) | Open source |
| **[m4vic/TinyMobileLLM](https://github.com/m4vic/TinyMobileLLM)** | — | Benchmark tiny LLMs (0.5B-2B) sur mobile. llama.cpp + Termux. | Snapdragon 855, 6GB RAM | 16.25 tok/s (Qwen 0.5B Q5), 7.6 (Qwen 1.5B Q3), 5.1 (RecurrentGemma 2B Q2) | Open source |
| **[as1as/unity-android-ondevice-llm](https://github.com/as1as1984/unity-android-ondevice-llm)** | — | LLM on-device dans Unity Android. llama.cpp OpenCL → C# P/Invoke. | Samsung S24 Ultra (Snapdragon 8 Gen 3) | 16.6 tok/s (Qwen3-1.7B Q8_0), 9.0 (Phi-4-mini 3.8B Q8_0) | Open source |
| **[google-ai-edge/gallery](https://github.com/google-ai-edge/gallery)** | — | Google AI Edge Gallery app. Découverte + test modèles LiteRT. | Android + iOS | Benchmarks intégrés (TTFT, decode speed) | **Gratuit** |
| **[MobileAIBench](https://arxiv.org/pdf/2406.10290)** | — | Framework benchmark LLMs/LMMs mobile. App iOS. 7B max. | iPhone 14 | TTFT, ITPS, OET, CPU/RAM usage | Open source |

### 14.4 Modèles optimisés mobile (HuggingFace)

| Modèle | Params | Format | Taille | Plateforme | Pertinence GSIE |
|---|---|---|---|---|---|
| **[Gemma 4 E2B (LiteRT-LM)](https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm)** | 2B (effective) | .litertlm | 2.6 GB | Android, iOS, Web, Desktop | **Très haute** — Multimodal (text+image+audio). 52 tok/s GPU (S26). 56 tok/s GPU (iPhone 17 Pro). MTP speculative decoding. **Pour GeoSylva**. |
| **[Gemma 3 1B (LiteRT)](https://huggingface.co/litert-community/Gemma3-1B-IT)** | 1B | .task | ~700 MB | Android, Web | **Haute** — Ultra-léger. CPU 4 threads. **Pour GeoSylva low-end**. |
| **[Gemma-3n E4B (LiteRT-LM)](https://huggingface.co/google/gemma-3n-E4B-it-litert-lm)** | 4B (effective) | .litertlm | ~5 GB | Android, iOS | **Haute** — Multimodal. Pour devices haut de gamme. |
| **[Qwen2.5-0.5B-Instruct (GGUF)](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF)** | 0.5B | GGUF Q4_0 | 403 MB | Android (llama.cpp) | **Très haute** — 63.5 tok/s (S25 GPU). **Plus rapide pour chat temps réel**. |
| **[Qwen2.5-1.5B-Instruct (GGUF)](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF)** | 1.5B | GGUF Q3_K_M | 1.0 GB | Android (llama.cpp) | **Très haute** — 34.5 tok/s (S25 GPU). **Meilleur ratio vitesse/qualité**. |
| **[Llama-3.2-1B (GGUF)](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct)** | 1B | GGUF Q4_0 | 730 MB | Android (llama.cpp) | **Haute** — 37.7 tok/s (S25 GPU). Généraliste. |
| **[Llama-3.2-3B (GGUF)](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct)** | 3B | GGUF Q4_0 | 1.8 GB | Android (llama.cpp) | **Moyenne** — 18.5 tok/s (S25 GPU). Utilisable mais plus lent. |
| **[Phi-3-mini-4k (GGUF)](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct)** | 3.8B | GGUF Q4_K_M | 2.3 GB | Android (llama.cpp) | **Basse** — 4.1 tok/s (S25, Q4_K_M non optimisé Adreno). |
| **[RecurrentGemma 2B (GGUF)](https://huggingface.co/google/recurrentgemma-2b-it)** | 2B | GGUF Q2_K | 2.1 GB | Android (llama.cpp) | **Moyenne** — 5.1 tok/s (Snapdragon 855 CPU). Architecture récurrente efficace. |
| **[qualcomm/Llama-v3.1-8B-Instruct](https://huggingface.co/qualcomm/Llama-v3.1-8B-Instruct)** | 8B | w4a16 | ~4 GB | Snapdragon 8 Elite (NPU) | **Haute** — 16.4 tok/s NPU. **Pour devices Qualcomm haut de gamme**. |
| **[qualcomm/Qwen3-4B](https://huggingface.co/qualcomm/Qwen3-4B)** | 4B | w4a16 | ~2.5 GB | Snapdragon 8 Elite (NPU) | **Haute** — Optimisé NPU Hexagon. |

### 14.5 Tableau récapitulatif — classement par efficacité (tokens/seconde decode)

> Classement du plus efficace au moins efficace. Conditions: modèle ≤ 4B params, quantization 4-bit, device flagship récent.

| Rang | Solution | Modèle | Device | Backend | Decode tok/s | Prefill tok/s | TTFT |
|---|---|---|---|---|---|---|---|
| 1 | **LiteRT-LM + MTP** | Gemma 4 E2B | Samsung S26 Ultra | GPU | **56** | 3808 | 0.3s |
| 2 | **LiteRT-LM + MTP** | Gemma 4 E2B | iPhone 17 Pro | GPU | **56.5** | 2878 | 0.3s |
| 3 | **llama.cpp OpenCL** | Qwen2.5-0.5B Q4_0 | Samsung S25 | GPU (Adreno 830) | **63.5** | 388 | — |
| 4 | **Apple Intelligence** | AFM 3B (2-bit QAT) | iPhone 15 Pro | NPU+GPU | **30** | — | 0.6ms/token |
| 5 | **Transformer-Lite** | Gemma 2B | OPPO Find X7 (Dimensity 9300) | GPU (Mali-G720) | **30** | 330 | — |
| 6 | **LiteRT-LM** | Gemma 4 E2B | Samsung S26 Ultra | CPU | **47** | 557 | 1.8s |
| 7 | **llama.cpp OpenCL** | Qwen2.5-1.5B Q4_0 | Samsung S25 | GPU | **34.5** | 379 | — |
| 8 | **llama.cpp OpenCL** | Llama-3.2-1B Q4_0 | Samsung S25 | GPU | **37.7** | 331 | — |
| 9 | **Qualcomm AI Hub** | Llama 3.1 8B w4a16 | Snapdragon 8 Elite Gen 5 | NPU (Hexagon) | **16.4** | — | 0.1s |
| 10 | **llama.cpp OpenCL** | Qwen3-1.7B Q8_0 | Samsung S24 Ultra | GPU | **16.6** | — | — |
| 11 | **llama.cpp CPU** | Qwen2-0.5B Q4 F16 | iPhone 15 Pro | CPU (2 threads) | **17** | — | — |
| 12 | **llama.cpp CPU** | Qwen2.5-0.5B Q5 | Snapdragon 855 | CPU (1 thread) | **16.25** | — | — |
| 13 | **llama.cpp OpenCL** | Llama-3.2-3B Q4_0 | Samsung S25 | GPU | **18.5** | 194 | — |
| 14 | **Transformer-Lite** | ChatGLM2 6B | OPPO Find X7 (Dimensity 9300) | GPU | **14** | 121 | — |
| 15 | **llama.cpp CPU** | Qwen2.5-1.5B Q3 | Snapdragon 855 | CPU (4 threads) | **13.81** | — | — |
| 16 | **Qualcomm AI Hub** | Llama 3.1 8B w4a16 | Snapdragon 8 Elite | NPU | **15** | — | 0.14s |
| 17 | **llama.cpp OpenCL** | Phi-3-mini 3.8B Q4_K_M | Samsung S25 | GPU | **4.1** | 11 | — |
| 18 | **ONNX Runtime** | Phi-4-mini 3.8B | Samsung S24 Ultra | CPU | **0.21** | — | — |

### 14.6 Téléphones compatibles — matrice complète

| Constructeur | Modèle | SoC | RAM min | LLM max supporté | NPU | Solution recommandée |
|---|---|---|---|---|---|---|
| **Samsung** | Galaxy S26 Ultra | Snapdragon 8 Elite Gen 5 | 12-16 GB | 8B (NPU) / 4B (GPU) | Hexagon v81 | LiteRT-LM GPU/NPU, Qualcomm AI Hub |
| **Samsung** | Galaxy S25 | Snapdragon 8 Elite | 12-16 GB | 8B (NPU) / 4B (GPU) | Hexagon v73 | llama-droid OpenCL, Qualcomm AI Hub |
| **Samsung** | Galaxy S24 Ultra | Snapdragon 8 Gen 3 | 12 GB | 4B (GPU) / 8B (CPU) | Hexagon v73 | llama.cpp OpenCL |
| **Samsung** | Galaxy S23 | Snapdragon 8 Gen 2 | 8 GB | 7B (GPU Q4) | Hexagon v73 | MLC LLM, llama.cpp |
| **Google** | Pixel 10/10 Pro | Tensor G5 | 12-16 GB | Gemini Nano v3 | TPU | AICore (Gemini Nano) |
| **Google** | Pixel 9/9 Pro | Tensor G4 | 12-16 GB | Gemini Nano v2/v3 | TPU | AICore (Gemini Nano) |
| **Apple** | iPhone 17 Pro | A19 Pro | 8 GB | AFM 3B + Gemma 4 E2B | Neural Engine | Apple Intelligence, LiteRT-LM Metal |
| **Apple** | iPhone 16 Pro | A18 Pro | 8 GB | AFM 3B + Gemma 4 E2B | Neural Engine | Apple Intelligence, LiteRT-LM Metal |
| **Apple** | iPhone 15 Pro | A17 Pro | 8 GB | AFM 3B + 7B (CPU Q4) | Neural Engine | Apple Intelligence, llama.cpp CPU |
| **OPPO** | Find X7 Ultra | Snapdragon 8 Gen 3 | 12 GB | 7B (GPU) | Hexagon v73 | Transformer-Lite, llama.cpp |
| **OPPO** | Find X7 | Dimensity 9300 | 24 GB | 14B (GPU) | APU 790 | Transformer-Lite (Mali GPU) |
| **Xiaomi** | 17 / 17 Ultra | Snapdragon 8 Elite Gen 5 | 12-16 GB | 8B (NPU) | Hexagon v81 | Qualcomm AI Hub, LiteRT-LM |
| **Xiaomi** | 14 | Snapdragon 8 Gen 3 | 12 GB | 7B (NPU) | Hexagon v73 | mllm-NPU, llama.cpp |
| **OnePlus** | 15 / 13 | Snapdragon 8 Elite | 12-16 GB | 8B (NPU) | Hexagon v73 | Qualcomm AI Hub, Gemini Nano |
| **vivo** | X200 Pro | Dimensity 9400 | 16 GB | 7B (GPU) | APU 790 | Transformer-Lite |
| **Honor** | Magic 8 Pro | Snapdragon 8 Elite | 12-16 GB | 8B (NPU) | Hexagon v73 | Gemini Nano, Qualcomm AI Hub |
| **Motorola** | Razr 60 Ultra | Snapdragon 8 Elite | 12 GB | 8B (NPU) | Hexagon v73 | Gemini Nano |
| **Apple** | iPhone 14 | A16 Bionic | 6 GB | 2B max (Q4) | Neural Engine | MLC LLM, llama.cpp (limité) |
| **Samsung** | Galaxy S22 | Snapdragon 8 Gen 1 | 8 GB | 3B (Q4) | Hexagon v73 | llama.cpp (limité) |
| **Xiaomi** | Redmi K60 Pro | Snapdragon 8 Gen 2 | 12 GB | 7B (NPU) | Hexagon v73 | mllm-NPU |
| **Snapdragon 855** | (various) | Snapdragon 855 | 6 GB | 2B max (Q3-Q5) | Hexagon v69 | llama.cpp CPU (limité) |

### 14.7 Recommandations pour GeoSylva / GSIE

**Pour GeoSylva Android (Kotlin + Jetpack Compose)** :

1. **LiteRT-LM Kotlin API** — Production-ready, GPU+NPU, Gemma 4 E2B multimodal (text+image+audio). Maven package. **Recommandé pour production**.
2. **llama.cpp + OpenCL (llama-droid)** — Pour dev/exploration. Pas de root. Termux. Qwen2.5-1.5B Q4_0 = 34.5 tok/s (S25).
3. **Gemini Nano (AICore)** — Si device compatible (Pixel 9+, Samsung S25+). Gratuit, optimisé, safety intégré. ML Kit GenAI APIs.
4. **Qualcomm AI Hub (GENIE)** — Pour devices Snapdragon 8 Elite+. NPU Hexagon. Llama 3.1 8B = 16.4 tok/s.

**Modèles recommandés par cas d'usage** :

| Cas d'usage | Modèle | Taille | Vitesse attendue | Format |
|---|---|---|---|---|
| Chat assistant temps réel | Qwen2.5-0.5B Q4_0 | 403 MB | 63 tok/s | GGUF (llama.cpp) |
| Assistant qualité/vitesse | Qwen2.5-1.5B Q4_0 | 1.0 GB | 34 tok/s | GGUF (llama.cpp) |
| Assistant multimodal | Gemma 4 E2B | 2.6 GB | 52 tok/s | .litertlm (LiteRT-LM) |
| Reasoning complexe | Llama 3.1 8B w4a16 | 4 GB | 16 tok/s | Qualcomm AI Hub NPU |
| Identification botanique (image) | Gemma-3n E4B | 5 GB | 20-30 tok/s | .litertlm (LiteRT-LM) |
| Résumé / preuve | Gemini Nano | 0 (système) | ~30 tok/s | AICore (Android système) |

**Pour Ignis / Artemis (app mobile wildfire)** :
- **Gemini Nano** (AICore) pour summarization + smart reply (gratuit, intégré)
- **LiteRT-LM + Gemma 4 E2B** pour analyse multimodale offline (photo → texte)
- **llama.cpp + Qwen2.5-1.5B** pour reasoning offline sur devices plus anciens

### 14.8 Solutions payantes / commerciales

| Solution | Type | Prix | Description |
|---|---|---|---|
| **Qualcomm AI Hub Workbench (hosted devices)** | Cloud profiling | **Payant** (sur inscription) | Compilation + profiling sur devices Qualcomm hébergés dans le cloud. Pas obligatoire (SDK local gratuit). |
| **OpenAI GPT-4o API** | Cloud LLM | **Payant** ($5-15/M tokens) | Alternative cloud si on-device insuffisant. Pas offline. |
| **Google Gemini API (cloud)** | Cloud LLM | **Payant** (gratuit tier limité) | Gemini 1.5 Pro/Flash. Pas offline. |
| **Anthropic Claude API** | Cloud LLM | **Payant** ($3-15/M tokens) | Claude 3.5 Sonnet. Pas offline. |
| **Groq API** | Cloud LLM | **Payant** (gratuit tier limité) | Llama 3.3 70B ultra-rapide. Pas offline. |

> **Note** : Toutes les solutions on-device listées en sections 14.1-14.4 sont **gratuites**. Les solutions payantes sont uniquement cloud (alternative complémentaire, pas replacement).

---

## 15. Historique

| Date | Événement |
|---|---|
| 2026-07-17 | Création de la note — compilation exhaustive depuis DATASET_CATALOG, IGNIS_DATA_PIPELINE, ENGINE_DATA_SOCLE, SOURCING_PLAN, GIS_ENGINE + recherche web (30 nouvelles sources) |
| 2026-07-17 | Ajout section 10-11 : méthodes d'ingestion par source + architecture d'ingestion recommandée |
| 2026-07-17 | Ajout section 12 : 40+ projets GitHub pertinents (simulation incendie, LiDAR, botanique, santé forêt, ingestion satellite, sol, drone AI, backend géo, UE5, KG écologique) |
| 2026-07-17 | Extension section 12 : +30 projets (carbone forestier, downscaling AROME, distribution espèces MaxEnt, risque incendie/FWI, croissance forestière FVS, plugins QGIS, apps mobiles, XAI environnemental) — total 70+ projets |
| 2026-07-17 | Ajout section 13 : modèles d'IA open source, LLM et plateformes (Prithvi EO 2.0, IBM Granite geospatial, WildfireGPT, GeoGPT-RAG, NVIDIA NIM, Azure AI Foundry, Ollama/vLLM, ClimateBench-M, ClimAgent) — 30+ ressources IA |
| 2026-07-17 | Ajout section 14 : LLM sur téléphone — 10 moteurs d'inférence, 11 modèles HuggingFace, 20+ téléphones compatibles, classement par efficacité, recommandations GeoSylva/Ignis |

---

> **Note** : Les sources marquées "en quarantaine" (DS-005, DS-006, DS-007, DS-009, DS-012, DS-022) nécessitent une formalisation de partenariat avant ingestion (`20_PARTNERSHIPS/` + `19_LEGAL/`). Les nouvelles sources identifiées doivent être évaluées par l'Evidence Engine avant intégration au catalogue (DS-030+).

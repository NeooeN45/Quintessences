# Pipeline de données Ignis — Flux temps réel, simulation et post-feu

| Champ | Valeur |
|---|---|
| **ID document** | GSIE-ARCH-FEU-002 |
| **Statut** | Draft |
| **Phase** | 2 — Architecture |
| **Créé le** | 2026-07-12 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **RFC d'origine** | RFC-0004 (ADOPTÉ) |
| **Directives fondatrices** | GSIE-DIR-0005 (jumeau numérique vivant), GSIE-DIR-0006 (moteur cognitif) |
| **Décisions liées** | DEC-000003 (garde-fous), DEC-000005 (archive banc) |
| **Document parent** | `GSIE_IGNIS_ARCHITECTURE.md` |
| **Document connexe** | `GSIE_IGNIS_DRONE_ARCHITECTURE.md` |

---

## 1. Objet

Ce document décrit les flux de données du système Ignis à chaque étape
du cycle de vie d'un incendie : détection temps réel, simulation et
recalage, validation post-feu et apprentissage continu.

L'objectif est de spécifier **quelles données circulent, sous quel
format, à quelle latence, et depuis quelles sources** — sans produire de
code métier (Phase 2).

---

## 2. Vue d'ensemble des flux

```
┌──────────────────────────────────────────────────────────────────────┐
│                     FLUX TEMPS RÉEL (pendant feu)                    │
│                                                                      │
│  Capteurs drone → Edge → Liaison radio → GCS → Jumeau → COS          │
│                                                                      │
│  Latence cible : détection → présentation COS < 5 min (boucle)       │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                     FLUX SIMULATION (recalage)                       │
│                                                                      │
│  ForeFire (prédiction) ← Assimilation ← Observations drone           │
│                                                                      │
│  Latence cible : cycle de recalage ~5 min                            │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                     FLUX POST-FEU (validation)                       │
│                                                                      │
│  Copernicus EMS / Sentinel / BDIFF → Validation → Apprentissage      │
│                                                                      │
│  Latence cible : jours (satellite) → semaines (RETEX)                │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                     FLUX PRÉVENTIF (pré-feu)                         │
│                                                                      │
│  AROME + BD Forêt + MNT + DFCI → Carte de risque dynamique           │
│                                                                      │
│  Latence cible : rafraîchissement horaire                            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Flux temps réel — capteurs drone → edge → GCS → COS

### 3.1 Chaîne de traitement

```
Capteurs drone
  ├── RGB (caméra optique)
  ├── Thermique LWIR (radiométrique, T° par pixel)
  ├── Capteurs atmosphériques (CO/CO₂, particules, T°, hygrométrie)
  └── GPS / IMU (position, attitude, vent par dérive)
      ↓
  Edge processing (Jetson)
  ├── Détection YOLO quantisé (fumée/flamme) → boîtes + scores
  ├── Détection personnes/véhicules (YOLO standard) → boîtes + scores
  ├── VLM (description structurée de scène) → texte + attributs
  ├── Estimation intensité front (thermique → kW/m)
  ├── Vecteur de feu (géométrie front entre passages + vent)
  └── Compression / priorisation des messages
      ↓
  Liaison radio (hiérarchique par priorité)
  ├── Critique : LoRa maillé (Meshtastic) — détections, vecteur
  ├── Standard : 4G/5G — télémétrie, état mission
  └── Large bande : imagerie (si lien) ou stockage à bord
      ↓
  GCS-Lite (réception terrain)
  ├── Visualisation temps réel (carte 3D, détections, vol)
  ├── Cache local (mode dégradé offline)
  └── Relais vers serveur (si connexion disponible)
      ↓
  Serveur — Jumeau numérique
  ├── Assimilation (recalage ForeFire, ~5 min)
  ├── Prédiction (propagation + ensembles probabilistes)
  └── Analyse d'enjeux (intersection × bâtiments/infra)
      ↓
  GCS-Lite — Présentation COS
  ├── Front prédit + intensité + incertitude
  ├── Enjeux menacés + délais (30 min / 1 h / 2 h)
  ├── Timeline de simulation (passé → futur)
  └── Recommandations (suggestions, jamais ordres)
```

### 3.2 Latences cibles par étape

| Étape | Latence cible | Justification |
|---|---|---|
| Capteur → edge (inférence YOLO) | < 100 ms | Temps réel vidéo, détection immédiate |
| Edge → message compact | < 1 s | Construction du message prioritaire |
| Message critique (LoRa) → GCS | < 30 s | Bas débit mais passage garanti en zone blanche |
| Télémétrie (4G/5G) → GCS | < 5 s | Si couverture disponible |
| Imagerie (large bande) → GCS | Différé (secondes à minutes) | Si lien disponible, sinon à la récupération |
| GCS → serveur (si connexion) | < 5 s | Relais des observations |
| Assimilation + prédiction (serveur) | < 60 s | Un cycle ForeFire + filtre d'ensemble |
| Serveur → GCS (présentation COS) | < 5 s | WebSocket push |
| **Boucle complète (détection → COS)** | **< 5 min** | Cible de la boucle d'assimilation (J-03) |

### 3.3 Format des données à chaque étape

> Les structures ci-dessous sont des **descriptions logiques**, pas du
> code. Les schémas concrets (JSON Schema, Protobuf) seront spécifiés en
> Jalon 1 / Phase 3.

#### 3.3.1 Sortie capteur brut (drone)

| Champ | Type | Description |
|---|---|---|
| `horodatage` | ISO 8601 UTC | Précision milliseconde |
| `lat`, `lon` | Décimal degré | Position GPS du drone |
| `altitude` | Mètre | Altitude au-dessus du niveau de la mer |
| `attitude` | Quaternions ou RPY | Roll, Pitch, Yaw |
| `image_rgb` | Frame H.264/H.265 | Flux vidéo compressé |
| `image_thermique` | Frame radiométrique | Température par pixel (Kelvin) |
| `co`, `co2`, `particules` | ppm / µg/m³ | Capteurs atmosphériques |
| `temperature`, `hygrometrie` | °C / % | Capteurs atmosphériques |
| `vent_estime` | m/s + direction | Par dérive GPS (P-08) |

#### 3.3.2 Sortie edge (détection + caractérisation)

| Champ | Type | Description |
|---|---|---|
| `horodatage` | ISO 8601 UTC | De l'observation |
| `lat_detection`, `lon_detection` | Décimal degré | Position de la détection (projetée au sol) |
| `type_detection` | Énuméré | `fumée` / `flamme` / `anomalie_thermique` / `personne` / `véhicule` |
| `score_confiance` | Flottant [0, 1] | Score du détecteur |
| `intensite_estimee` | kW/m | Estimation à partir du thermique radiométrique (P-03) |
| `vecteur_feu` | Vitesse + direction | Vecteur de propagation estimé (J-04) |
| `description_vlm` | Texte structuré | Description de scène par VLM (P-02) |
| `rcci_fumee` | Attributs (optionnel) | Couleur, densité, comportement fumée (P-04, suggestion) |
| `metadonnees_capteur` | Référence | Quels capteurs ont contribué à cette détection |

#### 3.3.3 Message compact (liaison radio critique, ~200 octets)

| Champ | Taille approx. | Description |
|---|---|---|
| En-tête | ~20 octets | ID drone, type message, horodatage compressé |
| Position détection | ~12 octets | Lat/lon compressés (entier + facteur d'échelle) |
| Type + score | ~4 octets | Type énuméré + score quantisé |
| Intensité | ~4 octets | kW/m quantisé |
| Vecteur | ~8 octets | Vitesse + direction quantisées |
| Checksum | ~4 octets | Intégrité du message |

> Spécification détaillée du protocole compact à écrire (C-02, Phase 2).

#### 3.3.4 Observation assimilable (entrée du filtre d'ensemble)

| Champ | Type | Description |
|---|---|---|
| `horodatage` | ISO 8601 UTC | |
| `position_front` | Géométrie (ligne/polygone) | Position observée du front |
| `intensite` | kW/m | Intensité estimée par segment |
| `vecteur` | Vitesse + direction | Direction de propagation observée |
| `incertitude` | Flottant / matrice | Covariance de l'observation |
| `source` | Énuméré | `drone_rgb` / `drone_thermique` / `satellite` / `sol` / `manuel` |
| `niveau_preuve` | Énuméré | Attribué par l'Evidence Engine |

#### 3.3.5 Prédiction du jumeau numérique (sortie vers COS)

| Champ | Type | Description |
|---|---|---|
| `horodatage_prediction` | ISO 8601 UTC | |
| `horizon` | Minutes | Horizon de prédiction (30 min, 1 h, 2 h) |
| `contours_front` | GeoJSON Polygon[] | Contours prédits à chaque pas de temps |
| `intensite_par_segment` | kW/m | Intensité le long du front |
| `probabilites` | Carte de probabilité | Issue des ensembles (si émulateur) |
| `incertitude` | Indice / intervalle | Divergence des estimateurs (J-04) |
| `enjeux_menaces` | Liste structurée | Bâtiments/infra menacés + délais (J-06) |
| `recommandations` | Liste structurée | Suggestions tactiques (jamais ordres) |

---

## 4. Flux simulation — ForeFire → assimilation → recalage → prédiction

### 4.1 Boucle d'assimilation (J-03, cœur du projet)

```
État courant du jumeau (paramètres ForeFire : combustible, vent, ROS)
    ↓
Prédiction ForeFire (propagation sur T minutes)
    ↓
Nouvelles observations drone (position front, intensité, vecteur)
    ↓
Filtre d'ensemble (Kalman d'ensemble / particulaire)
    ├── Compare prédiction vs observation
    ├── Calcule l'innovation (écart)
    ├── Recale les paramètres (vent local, ROS, combustible)
    └── Propage l'incertitude
    ↓
État recalé du jumeau
    ↓
Nouvelle prédiction (propagation sur horizon COS)
    ↓
Présentation COS (front + enjeux + incertitude)
    ↓
[Cycle suivant dans ~5 min]
```

### 4.2 Vecteur de feu multi-estimateurs (J-04)

Trois estimateurs indépendants sont fusionnés :

| Estimateur | Source | Force | Faiblesse |
|---|---|---|---|
| **(1) Géométrie front thermique** | Thermique drone entre passages | Direct, physique | Dépend de la fréquence de passage |
| **(2) Inclinaison panache + vent** | RGB + vent local | Indicateur directionnel | Indirect, qualitatif |
| **(3) Prédiction ForeFire** | Simulation recalée | Spatial, temporel, ensembles | Dépend de la qualité des paramètres |

**Fusion** : pondérée par les incertitudes de chaque estimateur. En cas
de divergence significative, le système **signale l'incertitude au COS**
— jamais de fausse certitude.

### 4.3 Ensembles probabilistes

ForeFire permet des dizaines de scénarios par cycle (10 s / 1 000 ha).
L'émulateur neuronal (J-02, V2) permettra des centaines de scénarios en
continu pour produire des cartes de probabilité.

**Stratégie en trois temps** (Phase0 §1.4) :
1. **MVP** : ForeFire brut (suffisant pour le démonstrateur et les
   premiers ensembles).
2. **V1** : substituts ANN au niveau du modèle de vitesse
   (`wildfire_ROS_models`).
3. **V2 (recherche)** : émulateur du simulateur complet (U-Net/ConvLSTM
   ou Neural Operators FNO/SFNO via PhysicsNeMo).

**Sources** : Allaire, Filippi & Mallet (2020), *IJWF* — méthodologie
d'ensembles directement sur ForeFire.

### 4.4 Latences cibles — flux simulation

| Étape | Latence cible | Justification |
|---|---|---|
| Préparation des entrées ForeFire (paysage, vent, combustible) | < 10 s | Cache préchargé, données statiques |
| Exécution ForeFire (un scénario) | < 10 s | 1 000 ha, résolution métrique |
| Filtre d'ensemble (recalage) | < 30 s | Selon taille de l'ensemble |
| Ensembles probabilistes (10–50 scénarios) | < 60 s | Sans émulateur ; < 10 s avec émulateur V1 |
| Analyse d'enjeux (PostGIS) | < 5 s | Requête spatiale indexée |
| **Cycle complet de recalage** | **< 5 min** | Cible de la boucle (J-03) |

### 4.5 Format des données — flux simulation

#### 4.5.1 Entrée ForeFire (paysage)

| Couche | Format | Source | Résolution |
|---|---|---|---|
| Altitude (MNT) | NetCDF / GeoTIFF | IGN LiDAR HD | 1 m (LiDAR HD) à 5 m |
| Humidité (MNH) | NetCDF | IGN LiDAR HD (couche humidité) | 1 m |
| Combustible | NetCDF (classification) | BD Forêt v2 → modèle de combustible | 25 m (BD Forêt) |
| Vent | NetCDF (champ 3D) | AROME + descente d'échelle (CorrDiff) | 1–2 km (AROME) → 100 m (CorrDiff) |
| Température / hygrométrie | NetCDF | AROME | 1–2 km |

> Le format d'entrée ForeFire est analogue au format Landscape de
> FARSITE (NetCDF : altitude, vent, distribution de combustible).

#### 4.5.2 Sortie ForeFire (contours de front)

| Champ | Format | Description |
|---|---|---|
| Contours successifs | GeoJSON / KML | Polygones du front à chaque pas de temps |
| Pas de temps | ISO 8601 ou relatif (secondes depuis ignition) | |
| Position des marqueurs | Coordonnées (lat/lon ou projetées) | Marqueurs advectés du front-tracking |
| Vitesse de propagation (ROS) | m/s par segment | |
| Intensité | kW/m par segment | Si modèle Balbi/Rothermel le fournit |

---

## 5. Flux post-feu — validation satellite → apprentissage

### 5.1 Chaîne de validation

```
Fin de l'intervention
    ↓
Données de l'intervention (boîte noire du front, J-10)
  ├── Flux temporel ultra-compact (position/intensité/vecteur à chaque pas)
  ├── Décisions COS (horodatées, si disponibles)
  └── Observations drone (archive)
    ↓
Contours validés satellites (arrivée différée)
  ├── Copernicus EMS (contours officiels, latence jours)
  ├── Sentinel-2 (surfaces brûlées, latence 2–5 j)
  ├── Sentinel-1 SAR (si nuages/fumée, latence 6 j)
  └── NASA FIRMS / MTG-FCI (détections thermiques, latence 3 h à 10 min)
    ↓
Comparaison prédictions vs réalité
  ├── Métriques spatiales (intersection sur union, F1)
  ├── Métriques temporelles (décalage d'arrivée aux enjeux)
  └── Identification des écarts systématiques
    ↓
Apprentissage
  ├── Réentraînement des détecteurs (faux positifs/négatifs signalés, D-03)
  ├── Calibration des paramètres ForeFire (ROS, combustible)
  ├── Entraînement de l'émulateur (J-02)
  └── Enrichissement de la base de feux historiques (J-10, D-04)
    ↓
RETEX automatique (S-07)
  ├── Rapport comparatif prédictions vs réalité
  ├── Chronologie des décisions COS
  └── Produit vendable (les SDIS font leurs RETEX à la main aujourd'hui)
```

### 5.2 Boîte noire du front (J-10)

> Flux temporel ultra-compact pour rejouer n'importe quel feu passé dans
> le simulateur et valider les modèles en continu sur du réel. La base
> de données devient un banc de test qui grossit seul.

**Format** :

| Champ | Type | Description |
|---|---|---|
| `id_feu` | UUID | Identifiant unique de l'intervention |
| `commune` | Texte | Code INSEE |
| `horodatage_ignition` | ISO 8601 | |
| `pas_temporel` | Secondes | Résolution temporelle du flux |
| `positions_front[]` | Géométrie[] | Position du front à chaque pas |
| `intensite[]` | kW/m[] | Intensité par segment à chaque pas |
| `vecteur[]` | Vitesse + direction[] | Vecteur de propagation à chaque pas |
| `observations[]` | Référence | Liens vers les observations drone archivées |
| `predictions[]` | Référence | Liens vers les prédictions ForeFire archivées |
| `contours_valides` | Géométrie | Contours Copernicus EMS / Sentinel (post-feu) |
| `meteo` | Référence | Données AROME archivées sur la période |

### 5.3 Latences cibles — flux post-feu

| Étape | Latence | Justification |
|---|---|---|
| Détections thermiques satellite (FIRMS, MTG-FCI) | 10 min à 3 h | Pré-alerte large échelle + corroboration |
| Contours Copernicus EMS | 1–5 jours | Cartographie officielle de validation |
| Surfaces brûlées Sentinel-2 | 2–5 jours | Optical, si ciel dégagé |
| Surfaces brûlées Sentinel-1 SAR | 6 jours | Radar, voit à travers fumée/nuages |
| Comparaison + métriques | < 1 h (automatique) | À réception des contours validés |
| RETEX automatique | < 24 h | Rapport généré après validation |
| Réentraînement (batch) | Hebdomadaire / par intervention | Pipeline continu (D-03) |

---

## 6. Flux préventif — carte de risque dynamique (J-09)

### 6.1 Principe

> Carte de risque dynamique pré-feu, heure par heure : hygrométrie, vent,
> stress hydrique, combustible → « ce versant est une allumette
> aujourd'hui ». Déplace la valeur de la détection (réactif) vers la
> prévention et le pré-positionnement des moyens (proactif).

### 6.2 Chaîne

```
AROME (vent, T°, hygrométrie, prévisions horaires)
  + BD Forêt (combustible)
  + MNT LiDAR HD (topographie, exposition)
  + Sentinel-2 (stress hydrique, NDVI)
  + ERA5 (contexte historique)
  + BDIFF (feux historiques, calibrations)
    ↓
Modèle de risque (croisement multi-couches)
    ↓
Carte de risque dynamique (heure par heure)
    ↓
GCS-Lite (visualisation pré-positionnement SDIS)
```

### 6.3 Latence cible

| Étape | Latence | Justification |
|---|---|---|
| Ingestion AROME | Horaire (rafraîchissement modèle) | AROME produit des prévisions horaires |
| Calcul de la carte de risque | < 5 min | Croisement de couches préchargées |
| Présentation GCS-Lite | Temps réel (push) | Carte interactive |

---

## 7. Sources de données — catalogue exhaustif

### 7.1 Données topographiques et géospatiales

| Source | Type | Résolution | Licence | Usage |
|---|---|---|---|---|
| **IGN LiDAR HD** | MNT / MNH (modèle numérique de hauteur) | 1 m | Open data | Topographie, humidité, exposition |
| **BD Forêt v2** | Carte de végétation | 25 m | Open data | Combustible, types de peuplement |
| **BD TOPO / Cadastre** | Bâtiments, infrastructures | Métrique | Open data | Analyse d'enjeux (J-06) |
| **Atlas DFCI** | Pistes, points d'eau, massifs | Variable | Open data | Accès terrain, cartographie |
| **OpenStreetMap + BAN** | Sentiers, campings, adressage | Variable | ODbL / open | Compléments enjeux (D-17) |
| **OSO / CESBIO (Theia)** | Occupation des sols France | 10 m | Open data | Complément combustible (D-15) |

### 7.2 Données météorologiques

| Source | Type | Résolution | Licence | Usage |
|---|---|---|---|---|
| **AROME** (Météo-France) | Prévisions météo régionales | 1–2 km | Open data (portail) | Vent, T°, hygrométrie — paramètre n°1 de la propagation |
| **ERA5** (Copernicus Climate) | Réanalyses historiques | ~30 km | Open data | Entraînement sur feux historiques (J-08) |
| **Méso-NH** (CNRS/Météo-France) | Météo à haute résolution | Variable | Recherche | Couplage feu→atmosphère (pyroconvection, hors MVP) |
| **CorrDiff / FourCastNet 3** (NVIDIA Earth-2) | Météo IA, descente d'échelle | 25 km → 2 km | Open (modèles) | Vent hyper-local sur relief (M-09, M-12) |
| **AIFS** (ECMWF) / **GenCast** (DeepMind) / **Aurora** (Microsoft) | Météo IA fondation | Variable | Open | Benchmark météo IA (M-10) |

### 7.3 Données satellite — observation de la Terre

| Source | Type | Résolution / revisite | Licence | Usage |
|---|---|---|---|---|
| **Copernicus EMS** | Contours validés de feux | Variable (post-événement) | Open | Vérité terrain de validation (J-08) |
| **Sentinel-2** (ESA/Copernicus) | Optique multispectral | 10 m / 5 jours | Open | Combustible dynamique, stress hydrique, surfaces brûlées |
| **Sentinel-3** (ESA/Copernicus) | Thermique | 1 km / ~1 jour | Open | Détections thermiques quasi temps réel |
| **Sentinel-1 SAR** (ESA/Copernicus) | Radar | 10 m / 6 jours | Open | Surfaces brûlées à travers fumée/nuages (D-12) |
| **NASA FIRMS** | Détections thermiques (MODIS/VIIRS) | 375 m–1 km / 2× par jour | Open (API) | Pré-alerte large échelle + corroboration (J-08) |
| **Météosat MTG-FCI** (EUMETSAT) | Géostationnaire thermique | ~2 km / ~10 min | Open | Pré-alerte satellite haute fréquence (D-11) |
| **Google FireSat / EFA** | Constellation dédiée feu | 5 m / ≤20 min | À négocier | Détection précoce satellite (K-01, pilote 2026) |
| **EFFIS / GWIS** (JRC) | Recensement feux UE | Variable | Open | Complément européen (D-10) |
| **ERA5** | Réanalyses climatiques | ~30 km | Open | Entraînement sur feux historiques |

### 7.4 Données d'incendie historiques

| Source | Type | Couverture | Licence | Usage |
|---|---|---|---|---|
| **BDIFF** (bdiff.agriculture.gouv.fr) | Base officielle feux France | Depuis 1973 (saisies), 2006 (numérique) | Open | Colonne vertébrale feux historiques + causes (D-08) |
| **Prométhée** | Base méditerranéenne historique | Méditerranée (fusionnée dans BDIFF en 2023) | Open | Historique |
| **feuxdeforet.fr** | Événements validés géolocalisés | France, saison | À qualifier | Étiquettes + signalements citoyens (D-07) |
| **WildfireSpreadTS** | Séries temporelles propagation | International | Open | Simulation / apprentissage |

### 7.5 Données DFCI et infrastructure

| Source | Type | Licence | Usage |
|---|---|---|---|
| **GIP ATGeRi / PIGMA** | Données DFCI Aquitaine (pistes, points d'eau, massifs) | Partenariat | Partenaire données régional (D-09) |
| **Réseaux RTE / Enedis** | Lignes électriques | Open data | Cause d'ignition + enjeu à protéger (D-16) |
| **ANFR Cartoradio** | Positions émetteurs radio | Open data | Couverture radio / déconfliction (G-12) |

### 7.6 Données capteurs sol et citoyennes

| Source | Type | Licence | Usage |
|---|---|---|---|
| **Stations Meshtastic solaires** (C-04) | Capteurs sol LoRa | Propriétaire | Maillage territorial low-cost |
| **sensor.community** | Capteurs citoyens particules/T° | Open data | Préfiguration du maillage (D-18) |
| **Météorage / Blitzortung** | Détections de foudre | Payant / communautaire | Cause d'ignition, surveillance post-orage (D-13) |
| **CAMS** (Copernicus Atmosphère) | Modélisation panaches/qualité air | Open | Validation panache + impact sanitaire (D-14) |

### 7.7 Datasets d'entraînement (détection / caractérisation)

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

### 7.8 Données synthétiques (génération)

| Source | Méthode | Usage |
|---|---|---|
| **GCS-Cinéma (Unreal/Niagara)** | Rendu photoréaliste géoréférencé de feux | Images aériennes annotées, vérité terrain automatique (D-05) |
| **Gazebo** | Rendu physique (fumée lointaine) | Détections simulées bruitées (banc) |
| **Isaac Sim** (NVIDIA, veille) | Synthèse photoréaliste massive | Synergie Jetson, phase 4+ |

---

## 8. Architecture offline-first — implications sur les flux

### 8.1 Synchronisation edge → serveur

```
Edge (drone + GCS terrain)
  ├── File d'attente locale (observations horodatées)
  ├── Cache tuiles (préchargé avant déploiement)
  └── Vol autonome (mission en cours)
      ↓ (connexion intermittente)
  Synchronisation différée
      ↓
Serveur (jumeau numérique)
  ├── Réception des observations en retard
  ├── Rejeu de l'assimilation sur les données manquantes
  └── Mise à jour de la prédiction
```

**Principe** : aucune donnée n'est perdue. Les observations edge sont
horodatées et stockées localement ; le serveur les ingère dès que la
connexion rétablit, recale rétroactivement, et met à jour la prédiction.

### 8.2 Priorité des flux en mode dégradé

| Priorité | Flux | Comportement offline |
|---|---|---|
| 1 (critique) | Détections → GCS | LoRa maillé, passe toujours |
| 2 (standard) | Télémétrie → GCS | 4G/5G si disponible, sinon stocké |
| 3 (enrichissement) | GCS → serveur | Suspendu, file d'attente |
| 4 (large bande) | Imagerie → GCS/serveur | Stocké à bord, différé |

---

## 9. Sécurité et intégrité des données (S-11)

| Mesure | Périmètre | Statut |
|---|---|---|
| Chiffrement liaisons MAVLink 2 signé | Drone ↔ GCS | ✅ Prévu |
| Authentification nœuds mesh | Réseau LoRa | ✅ Prévu |
| Détection anomalies sur messages | Tous flux | ✅ Prévu |
| Résilience brouillage GPS | Navigation drone | ✅ Prévu |
| Chiffrement au repos | Archives serveur | ✅ Prévu |
| Purge automatique données personnes | RGPD (P-09) | ✅ Prévu |
| Qualification SecNumCloud/ANSSI | Hébergement sécurité civile | 🔍 Anticipation |

---

## 10. Assimilation probabiliste multi-observateurs (DIR-0006)

### 10.1 Principe

Aucune source du catalogue (§7) n'est considérée comme une vérité
absolue. Chaque source est conceptualisée comme un **observateur** du
terrain, doté de caractéristiques propres : précision, latence, fiabilité
et incertitude. Le moteur cognitif fusionne l'ensemble des observations
et construit un **consensus probabiliste** — il ne sélectionne jamais une
source unique.

> **Cadrage constitutionnel** : toute affirmation doit être traçable et
> son incertitude explicitée (GSIE-CON-004, GSIE-CON-005). Le consensus
> probabiliste n'est jamais présenté comme une vérité, toujours comme un
> raisonnement justifiable.

### 10.2 Caractérisation des observateurs

Le tableau ci-dessous caractérise les principaux observateurs du pipeline
selon les quatre dimensions définies par DIR-0006. Les valeurs sont
indicatives (Phase 2 — architecture) et seront affinées par qualification
en Phase 3.

| Observateur | Précision spatiale | Latence typique | Fiabilité | Incertitude dominante |
|---|---|---|---|---|
| Drone RGB (détection YOLO + VLM) | Métrique (projection au sol) | < 30 s (LoRa) / < 5 s (4G) | Élevée | Score de confiance [0, 1] ; faux positifs en zone urbaine |
| Drone thermique LWIR (radiométrique) | Métrique | < 30 s (LoRa) / < 5 s (4G) | Élevée (mesure physique) | Covariance par pixel ; atténuation atmosphérique |
| Capteurs atmosphériques drone (CO/CO₂, particules) | Métrique (position drone) | < 30 s | Moyenne | Dérive capteur ; représentativité ponctuelle |
| Satellite Sentinel-2 (optique) | 10 m | 2–5 jours | Élevée | Masquage par nuages / fumée |
| Satellite Sentinel-1 SAR (radar) | 10 m | 6 jours | Élevée | Sensibilité à l'humidité sol |
| NASA FIRMS / MTG-FCI (thermique large échelle) | 375 m – 2 km | 10 min – 3 h | Moyenne | Fausses détections (soleil, industrie) ; résolution grossière |
| Google FireSat / EFA (constellation dédiée) | 5 m | ≤ 20 min | À qualifier (pilote 2026) | Calibrage en cours |
| AROME (modèle météo) | 1–2 km | Horaire | Élevée (modèle opérationnel) | Erreur de prévision ; descente d'échelle requise |
| CorrDiff / Earth-2 (météo IA, descente d'échelle) | ~100 m | Horaire (lié AROME) | En recherche (M-09, M-12) | Erreur de super-résolution |
| Stations Meshtastic solaires (LoRa sol) | Variable (position fixe) | Minutes | Moyenne (capteurs bas coût) | Dérive ; représentativité ponctuelle |
| Capteurs citoyens (sensor.community) | Variable | Minutes | Faible à moyenne | Position approximative ; non étalonné |
| Détections de foudre (Météorage / Blitzortung) | ~1 km | Minutes | Moyenne à élevée | Foudre sans ignition ; latence variable |
| Rapports SDIS / CODIS | Variable (géolocalisation manuelle) | Minutes – heures | Très élevée (humain opérationnel) | Subjectivité ; délai de saisie |
| Signalements citoyens (feuxdeforet.fr) | Variable | Minutes | Faible à moyenne | Non vérifié ; position approximative |
| BDIFF (base historique officielle) | Communale | Jours – mois | Élevée (officiel) | Saisie rétroactive ; exhaustivité variable |
| Copernicus EMS (contours validés) | Variable (post-événement) | 1–5 jours | Très élevée (officiel) | Post-événement ; résolution variable |

### 10.3 Mécanisme de consensus

La fusion des observations suit le principe d'assimilation permanente
(DIR-0006) :

1. **Pondération par incertitude** : chaque observation est pondérée par
   sa covariance (cf. §3.3.4, champ `incertitude`). Les sources à faible
   incertitude et faible latence (drone thermique) prédominent dans la
   boucle temps réel ; les sources officielles différées (Copernicus EMS)
   prédominent dans la validation post-feu.
2. **Filtre d'ensemble** : le recalage ForeFire (§4.1) intègre
   simultanément les observations disponibles, qu'elles proviennent du
   drone, du satellite ou du sol. Le filtre propage l'incertitude de
   chaque source dans l'état recalé du jumeau.
3. **Détection de divergence** : lorsque les estimateurs divergent
   significativement (§4.2, vecteur de feu multi-estimateurs), le système
   **signale l'incertitude au COS** — jamais de fausse certitude.
4. **Traçabilité** : chaque observation conserve son `source` et son
   `niveau_preuve` (§3.3.4), attribué par l'Evidence Engine. Le
   raisonnement qui a conduit au consensus est explicable et auditable
   (GSIE-CON-004).

> Les garde-fous RFC-0004 §8 (autonomie limitée au vol, alerte et
> commandement humains) s'appliquent à l'ensemble du mécanisme. Ils ne
> sont pas reproduits ici — voir RFC-0004 §8.3 et §8.4.

---

## 11. Raisonnement multi-échelle (DIR-0006)

### 11.1 Principe

Le moteur cognitif raisonne simultanément à plusieurs échelles
spatiales. Chaque niveau échange avec les niveaux adjacentes : les
observations locales alimentent l'analyse régionale, et le contexte
régional contraint l'interprétation locale.

### 11.2 Échelles du pipeline

| Échelle | Résolution typique | Données impliquées | Rôle dans le pipeline |
|---|---|---|---|
| **Pixel** | 1 m (LiDAR) – 10 m (Sentinel-2) | Capteurs drone, imagerie satellite | Détection brute (fumée, flamme, anomalie thermique) ; entrée de l'Evidence Engine |
| **Arbre** | Individuel | LiDAR HD, RGB drone | Identification d'ignition ponctuelle ; structure de peuplement |
| **Parcelle** | 25 m (BD Forêt) | BD Forêt v2, classification combustible | Unité de combustible pour ForeFire ; caractérisation du couvert |
| **Massif** | Hectares – km² | Atlas DFCI, MNT LiDAR HD | Unité tactique de propagation ; accès piste / points d'eau |
| **Département** | Échelle SDIS | BDIFF, BD TOPO, AROME | Carte de risque dynamique (J-09) ; pré-positionnement des moyens |
| **Région** | Échelle climatique | AROME, ERA5, Méso-NH | Contexte météo régional ; feux historiques (J-08) ; couplage feu→atmosphère |
| **Pays** | Échelle nationale | BDIFF, Copernicus, EFFIS/GWIS | Tendances saisonnières ; apprentissage sur feux historiques ; benchmark européen |

### 11.3 Flux d'information entre échelles

```
Pixel (drone / satellite)
    ↓ détection + score de confiance
Arbre (LiDAR HD / RGB)
    ↓ ignition ponctuelle + structure
Parcelle (BD Forêt)
    ↓ combustible + couvert
Massif (DFCI / MNT)
    ↓ propagation ForeFire + enjeux
Département (carte de risque)
    ↓ pré-positionnement SDIS
Région (AROME / ERA5)
    ↓ contexte météo + feux historiques
Pays (BDIFF / Copernicus)
    ↓ tendances + apprentissage
```

L'information **remonte** (du pixel vers le pays) pour alimenter
l'apprentissage et la validation. Elle **descend** (du pays vers le
pixel) pour contraindre l'interprétation locale par le contexte. La
boucle d'assimilation (§4.1) opère principalement aux échelles
parcelle → massif, où la propagation physique est calculée. Les
échelles supérieures fournissent le cadre (météo, historique) et les
échelles inférieures fournissent les observations (détections,
mesures).

> **Cadrage constitutionnel** : chaque niveau doit pouvoir être expliqué
> indépendamment (GSIE-CON-004). Le passage d'une échelle à l'autre est
> tracé et justifié, jamais implicite.

---

## 12. Auto-évaluation et curiosité artificielle (DIR-0006)

### 12.1 Auto-évaluation continue

Le moteur cognitif calcule en permanence son propre état de connaissance.
Le pipeline fournit les signaux suivants pour cette auto-évaluation :

| Signal | Source dans le pipeline | Expression |
|---|---|---|
| **Divergence des estimateurs** | Vecteur de feu multi-estimateurs (§4.2) | Écart entre géométrie front, panache/vent et prédiction ForeFire |
| **Densité d'observation** | Catalogue d'observateurs (§10.2) | Nombre d'observateurs actifs sur la zone, fraîcheur de la dernière observation |
| **Incertitude propagée** | Filtre d'ensemble (§4.1) | Covariance de l'état recalé ; divergence des ensembles |
| **Couverture spatiale** | Position des drones / satellites | Zones sans observation récente (trous de couverture) |
| **Cohérence inter-sources** | Consensus probabiliste (§10.3) | Confrontation des observateurs ; détection d'incohérences |

Le système identifie ainsi :

- **les zones d'incertitude** : régions où la divergence des estimateurs
  ou la covariance du filtre d'ensemble dépasse un seuil ;
- **les informations manquantes** : paramètres ForeFire non contraints
  (vent local, ROS, humidité combustible), zones sans observation
  récente, sources attendues mais absentes (satellite masqué, drone hors
  portée) ;
- **les observations à demander** : actions d'observation susceptibles de
  réduire l'incertitude (envoi de drone, mesure thermique, repositionnement
  de capteur, interrogation d'une nouvelle source).

### 12.2 Curiosité artificielle — propositions sous supervision humaine

Lorsque l'incertitude devient trop importante, le moteur cognitif
propose spontanément des actions d'observation. Ces propositions sont
présentées au COS / CODIS et au télépilote comme des **suggestions**,
jamais comme des ordres ou des déclenchements automatiques.

| Type de proposition | Déclencheur | Destinataire |
|---|---|---|
| Envoyer un drone observer une zone | Trou de couverture + divergence d'estimateurs | Télépilote / COS |
| Demander une mesure thermique ciblée | Incertitude sur l'intensité du front | Télépilote |
| Repositionner un capteur sol | Zone aveugle persistante | COS / opérateur terrain |
| Recalculer une simulation avec paramètres alternatifs | Divergence des ensembles > seuil | Système (automatique, sans action sur le terrain) |
| Interroger une nouvelle source (satellite, station) | Information manquante identifiée | Système (automatique, sans action sur le terrain) |

> **Garde-fous RFC-0004 §8.3 / §8.4 (prioritaires — non reproduits
> ici)** : la curiosité artificielle produit des **propositions**
> d'observation. Elle ne déclenche **jamais** automatiquement une mission
> opérationnelle, une alerte ou une intervention. La décision de
> missionner un moyen reste humaine (télépilote, COS / CODIS). La reprise
> manuelle reste toujours possible et prioritaire. Ignis est un
> outil d'aide à la décision, pas un système de commandement.

---

## 13. Présentation immersive du jumeau numérique (DIR-0005)

### 13.1 Principe

Le pipeline ne se termine pas par un tableau de bord. Il se termine par
une **projection sur le terrain**. Le terrain devient l'interface unique
de compréhension : toutes les données — observations, prédictions,
enjeux, moyens, incertitudes — viennent s'y superposer dans leur
contexte géographique.

L'objectif est de réduire la charge cognitive du décideur. Les
informations ne sont jamais dispersées entre plusieurs fenêtres ou
vues. L'utilisateur navigue dans le monde réel, pas dans un logiciel.

### 13.2 Zoom progressif

L'expérience est progressive. L'utilisateur part de la Terre et zoome
progressivement vers le théâtre d'opération. Chaque niveau de zoom
révèle des couches d'information supplémentaires :

```
Terre → France → Régions → Massifs forestiers → Relief
→ Orthophotographies → Forêts → Routes → Pistes DFCI
→ Points d'eau → Bâtiments → Réseaux → Capteurs
→ Drones → Véhicules → Vents → Fumée → Feu
```

Le monde devient progressivement vivant. Toutes les informations sont
superposées au même espace géographique.

### 13.3 Rôle du moteur 3D

Le moteur de rendu 3D (Unreal Engine ou successeur) est la
représentation graphique du jumeau numérique. Il **ne contient aucune
logique métier**. Il reçoit les résultats calculés par le serveur
Ignis (prédictions, observations, enjeux, incertitudes) et les
projette sur le terrain.

| Responsabilité | Acteur |
|---|---|
| Simulations, assimilation, IA, prévisions, calculs géospatiaux | Serveur Ignis (moteur cognitif, §10–§12) |
| Représentation du monde, effets physiques, interaction, immersion | Moteur 3D (client) |

Le moteur 3D est **interchangeable** (GSIE-CON-007). L'intelligence
reste dans GSIE ; le rendu n'est qu'une fenêtre sur cette intelligence.
Aucune logique métier ne vit dans le client 3D.

### 13.4 Interaction contextuelle

Chaque élément de la scène est interactif et révèle son contexte
opérationnel sans quitter la vue principale :

- **Clic sur un camion** : indicatif, équipage, niveau d'eau, autonomie,
  vitesse, destination, mission, ETA.
- **Clic sur un drone** : flux vidéo, caméra thermique, batterie,
  capteurs, mission, possibilité de reprise de contrôle.
- **Clic sur le front de feu** : intensité, vitesse, direction,
  incertitudes, scénarios de propagation, enjeux menacés.

### 13.5 Immersion comme outil de compréhension

Le rendu 3D n'est pas un effet visuel. Chaque élément a une
signification opérationnelle : la fumée indique un comportement, le vent
montre une direction, les flammes représentent une intensité, les
véhicules évoluent en temps réel. Le terrain devient un tableau de bord
vivant.

> **Articulation DIR-0005 / DIR-0006** : le moteur cognitif (DIR-0006,
> §10–§12) comprend le monde ; le moteur 3D (DIR-0005, présente section)
> le montre. Les deux sont indissociables : l'un fournit l'intelligence,
> l'autre la fenêtre.

---

## 14. Sources et références

### 14.1 Sources scientifiques

- Allaire, Filippi & Mallet (2020), *Int. J. Wildland Fire* — ensembles
  de simulations ForeFire
- Kim, Pais & González (2025), *Sci. Rep.* — optimisation contre
  contours réels (F1 0,74 → 0,83)
- Filippi et al. (2014/2018), ForeFire, RSFF — méthode front-tracking

### 14.2 Sources de données

- Copernicus EMS : `emergency.copernicus.eu`
- NASA FIRMS : `firms.modaps.eosdis.nasa.gov` (API FIRMS)
- Sentinel-2/3 : `scihub.copernicus.eu`
- BDIFF : `bdiff.agriculture.gouv.fr`
- AROME : Météo-France (portail open data)
- IGN LiDAR HD : `ign.fr` (portail téléchargement)
- BD Forêt v2 : `ign.fr`
- EFFIS : `effis.jrc.ec.europa.eu`
- EUMETSAT MTG : `eumetsat.int`
- Google FireSat / EFA : `earthfirealliance.org`

### 14.3 Documents de gouvernance

- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0005.md` — Directive fondatrice Ignis
  (GCS / jumeau numérique vivant) — vision côté rendu, terrain comme
  interface, moteur 3D interchangeable, immersion
- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0006.md` — Directive fondatrice Ignis
  (moteur cognitif) — assimilation probabiliste, observateurs, graphe
  vivant, raisonnement multi-échelle, curiosité artificielle sous
  supervision humaine
- `02_RFC/RFC-0004.md` — RFC Ignis (ADOPTÉ) — §8 garde-fous
  (autonomie limitée au vol, alerte et commandement humains)
- `03_DECISIONS/DEC-000003.md` — Adoption RFC-0004 + garde-fous
- `apps/Ignis/REGISTRE.md` — Registre d'idées (sections 1, 2, 6)
- `apps/Ignis/Phase0_comparatif_moteurs_simulation.md`
  — Comparatif moteurs et simulation

---

> **Rappel** : le pipeline sert la boucle d'assimilation (J-03), qui est
> la brique différenciante de Ignis. Toutes les données convergent
> vers le recalage du jumeau numérique et la présentation immersive au
> COS — jamais vers une action automatique. Le moteur cognitif
> (DIR-0006) comprend le monde ; le moteur 3D (DIR-0005) le montre.

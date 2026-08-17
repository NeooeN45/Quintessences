# Catalogue exhaustif des ressources GSIE — Audit croisé 2026-08-13

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-DATA-AUDIT-EDOCUMENTS-002 |
| **Statut** | Draft — relecture du Fondateur requise |
| **Version** | 1.0.0 |
| **Date** | 2026-08-13 |
| **Auteur** | Codex, sous autorité du Fondateur |
| **Périmètre** | Catalogue GSIE, dossiers de recherche, connecteurs QGISIA et `E:\Documents` |
| **Règle** | Inventorier n'est pas ingérer : aucune ressource n'est promue par ce document |

## 1. Résumé

La synthèse précédente était trop courte. La documentation du projet et
l'inventaire local décrivent en réalité quatre périmètres distincts :

1. **Le catalogue GSIE canonique** : 34 familles de datasets et référentiels,
   avec des sous-familles pour le diagnostic stationnel et le marché du bois.
2. **Les dossiers scientifiques de recherche** : 113 fiches source réparties
   dans huit domaines (botanique, dendrométrie, pédologie, climat, hydrologie,
   faune, entomologie/mycologie/microbiologie et pathologie).
3. **Les connecteurs cartographiques QGISIA** : 12 sources officielles,
   61 entrées de connecteurs supplémentaires et 83 entrées de catalogue
   cartographique. Ces listes se recouvrent volontairement et ne constituent
   pas 156 datasets indépendants.
4. **Le fonds local `E:\Documents`** : 41 215 fichiers parcourus,
   15 014 fichiers conservés après exclusions techniques, puis 3 077
   ressources logiques après regroupement des sidecars géospatiaux.

Le nombre important ne signifie pas que tout est exploitable. Les droits,
la sensibilité, la provenance, le millésime, le grain natif et la qualité sont
à qualifier séparément par le Data Registry.

## 2. Résultats consolidés

| Périmètre | Entrées | Interprétation |
|---|---:|---|
| Fiches canoniques `SOURCES_DONNEES_EXHAUSTIVES.md` | 34 familles (`DS-001` à `DS-034f`, avec `DS-022b`) | Sources structurantes du métamodèle GSIE |
| Fiches `GSIE/RESEARCH/SOURCES` | 113 | Référentiels et APIs étudiés, avec licences et priorités à vérifier |
| Registre QGISIA officiel | 12 | Services réellement câblés dans le module de recherche |
| Catalogue QGISIA additionnel | 61 | Fonds, WMS/WMTS/WFS, risques, hydrographie et biodiversité |
| Catalogue JSON QGISIA | 83 | Catalogue cartographique mondial et français, dont plusieurs doublons |
| Ressources locales logiques | 3 077 | Fichiers, rasters, vecteurs, documents et tableurs inventoriés |
| Groupes de doublons exacts locaux | 143 | 414 ressources concernées ; aucun effacement automatique |

### 2.1 Inventaire local exhaustif

| Catégorie logique | Nombre |
|---|---:|
| Documents PDF/DOCX/ODT/PPTX et formats historiques | 359 |
| Tableurs et textes structurés | 256 |
| Textes et JSON non géospatiaux | 460 |
| GeoPackage/GeoJSON/KML | 85 |
| Shapefiles (sidecars regroupés) | 46 |
| Rasters géospatiaux | 195 |
| Images ordinaires | 1 676 |

| Indicateur de qualification locale | Nombre |
|---|---:|
| Pertinence heuristique élevée | 146 |
| Pertinence heuristique moyenne | 247 |
| Sensibilité/restriction à confirmer | 489 |
| Droits inconnus ou ingestion interdite par défaut | 2 350 |
| Routage GSIE-Bench / FieldIntake | 203 |
| Routage Data Registry `metadata_only` | 317 |
| Routage Research puis Knowledge après validation | 756 |
| Routage archive/hors périmètre probable | 1 801 |
| OCR probablement requis | 23 |
| GeoPackage techniquement illisible | 1 |

La preuve machine-readable complète est conservée localement dans :

```text
GSIE/DATASETS/inventory_edocuments/manifest.csv
GSIE/DATASETS/inventory_edocuments/manifest.json
GSIE/DATASETS/inventory_edocuments/summary.json
```

## 3. Catalogue canonique GSIE

Les identifiants ci-dessous viennent de `DATASET_CATALOG.md` et
`SOURCES_DONNEES_EXHAUSTIVES.md`. Ils sont les identifiants à réconcilier avec
le Data Registry ; les noms d'API et les URLs ne doivent jamais les remplacer.

### 3.1 Forestier, climat, sols et biodiversité

| ID | Ressource | Producteur | Usage principal |
|---|---|---|---|
| DS-001 | BD Forêt v2 | IGN | Couverture forestière, formations et essences |
| DS-002 | LiDAR HD (MNT/MNS/MNH, nuages classés) | IGN | Relief, hauteur, structure et combustible |
| DS-003 | Inventaire Forestier National / DataIFN | IGN | Placettes, dendrométrie, calibration |
| DS-004 | BD Ortho | IGN | Orthophotographie et validation visuelle |
| DS-005 | RPF — Référentiel pédologique forestier | ONF/INRAE | Stations et sols forestiers, accord à formaliser |
| DS-006 | SOERE F-ORE-T | INRAE | Observatoires expérimentaux long terme |
| DS-007 | Safran | Météo-France | Climat spatialisé historique |
| DS-008 | DRIAS | Météo-France | Projections climatiques régionalisées |
| DS-009 | ARPEGE / AROME | Météo-France | Prévision et simulation atmosphérique |
| DS-010 | Observations au sol | Météo-France | Stations et observations climatiques |
| DS-011 | BDAT | GIS Sol/INRAE | Analyses de terre |
| DS-012 | RPFR | ONF/INRAE | Référentiel pédologique régional |
| DS-013 | SoilGrids | ISRIC | Sols mondiaux à 250 m ; FETCH actuellement fermé hors micro-extrait autorisé |
| DS-014 | GBIF | GBIF | Occurrences taxonomiques |
| DS-015 | Tela Botanica / BDTFX | Tela Botanica | Flore et observations |
| DS-016 | BDNFF / ISFF | Tela Botanica/SBF | Nomenclature de la flore française |
| DS-017 | INPN / TAXREF / SINP | PatriNat/MNHN/OFB | Espèces, zonages et statuts |

### 3.2 Télédétection, incendie et biomasse

| ID | Ressource | Producteur | Usage principal |
|---|---|---|---|
| DS-018 | Sentinel-2 | ESA/Copernicus | Indices spectraux, stress, brûlis |
| DS-019 | Sentinel-1 | ESA/Copernicus | Radar, humidité et surfaces brûlées |
| DS-020 | Landsat 8/9 | USGS/NASA | Séries multispectrales longues |
| DS-021 | MODIS | NASA | NDVI/EVI et séries globales |
| DS-022 | Prométhée | Entente forêt méditerranéenne | **Obsolète**, fusionné dans BDIFF |
| DS-022b | BDIFF | MTE/MFB | Historique officiel des incendies français |
| DS-023 | EFFIS/GWIS | JRC | Feux européens et surfaces brûlées |
| DS-024 | FIRMS | NASA | Détection active quasi temps réel |
| DS-025 | GEDI L4A/L4B | NASA/UMD | Biomasse aérienne par empreinte et grille |
| DS-026 | ESA Biomass CCI v7 | ESA | Biomasse globale annuelle |
| DS-027 | CoSIA | IGN | Occupation du sol issue d'IA |
| DS-028 | OCS GE | IGN | Occupation du sol à grande échelle |
| DS-029 | Datasets d'apprentissage LiDAR HD | IGN | Apprentissage et classification de nuages |

### 3.3 Sylviculture, économie et diagnostic stationnel

| ID | Ressource | Producteur | Usage principal |
|---|---|---|---|
| DS-030 | Memento FCBA et éditions archivées | FCBA/CIBE | Caractéristiques, cubage, sylviculture, filière |
| DS-031 | Prix des bois sur pied et déclinaisons régionales | France Bois Forêt/FIBOIS | Marché privé, prix par essence et région |
| DS-032 | Mercuriales des bois publics | ONF | Marché public ; disponibilité/licence à confirmer |
| DS-033 | Corpus BTS Gestion Forestière | Fondateur | Méthodes, cas de terrain, exercices et productions personnelles |
| DS-034a | Catalogues des types de stations forestières | IGN/CNPF/CRPF | Typologies et gradients stationnels |
| DS-034b | Guides simplifiés des stations | CNPF/CRPF | Diagnostic terrain et choix d'essences |
| DS-034c | Guides de choix des essences | CNPF/CRPF | Recommandations sylvicoles contextualisées |
| DS-034d | Cahiers d'habitats Natura 2000 | MNHN/ONF | Habitats forestiers et conservation |
| DS-034e | Évaluation de l'état de conservation | MNHN/ONF | Méthodes d'évaluation des habitats |
| DS-034f | Habitats forestiers de France tempérée | INRAE/MNHN/IGN | Typologie phytoécologique quantitative |

## 4. Dossiers scientifiques : 113 fiches source

Les huit dossiers doivent être lus comme des fiches de qualification, pas
comme une autorisation d'ingestion. Les éléments ci-dessous reprennent toutes
les fiches numérotées actuellement présentes.

### D1 — Taxonomie et botanique (12)

TAXREF ; GBIF ; INPN ; Tela Botanica/BDTFX ; BDNFF/ISFF ; Catalogue of Life ;
ITIS ; WoRMS ; BD Forêt/essences IGN ; IPNI ; WCVP ; World Flora Online.

### D2 — Dendrométrie et écologie forestière (11)

BD Forêt v2 ; DataIFN ; indices écologiques IFN ; clés d'habitats par GRECO ;
ICP Forests niveau I ; ICP Forests niveau II ; RENECOFOR ; guides et catalogues
de stations CNPF/CRPF ; Flore forestière française de Rameau ; portail
cartographique IGN ; outil inventIF.

### D3 — Pédologie et géologie (10)

RPF ; WRB ; SoilGrids 2.0 ; WoSIS ; InfoTerre/OGC BRGM ; ESDAC ; GIS Sol,
BDGSF et IGCS ; GéoNormandie/DataNormandie ; LUCAS Soil ; BDAT.

### D4 — Climatologie (10)

DRIAS ; données publiques Météo-France (Safran/ARPEGE) ; Copernicus Climate
Data Store ; CMIP6/ESGF ; DRIAS-Eau ; ClimEssences ; BioClimSol/FORECCAsT ;
Fire Weather Index/CEMS Fire Historical ; Climadiag Agriculture et Forêt ;
EFFIS.

### D5 — Hydrologie (16)

Hub'Eau Hydrométrie ; Hub'Eau Qualité des cours d'eau ; Hub'Eau Écoulement
(ONDE) ; Hub'Eau Piézométrie ; Hub'Eau Température ; Vigicrues ; SIMVIGI ;
SANDRE ; ADES ; BD Carthage ; BD Topage ; BD Hydro ; Banque Hydro/
HydroPortail ; BDLISA ; BSS-Eau/BRGM ; RPDZH et cartographie nationale des
zones humides.

### D6 — Faune et vertébrés (16)

INPN/OpenObs ; INPN/BDC-Statuts ; espèces protégées/réglementées ; TAXREF ;
GBIF ; GBIF France/IPT ; LPO Faune-France ; Atlas des Oiseaux de France ;
SHF reptiles/amphibiens ; POPAmphibien/POPReptile ; SFEPM/Observatoire
National des Mammifères ; Atlas des mammifères sauvages ; Liste rouge UICN
France/PatriNat ; STOC CRBPO/MNHN ; guide de sensibilité SINP ; cadre de
confidentialité des données sensibles.

### D7 — Entomologie, mycologie et microbiologie (17)

INPN insectes ; GBIF arthropodes ; BDM Biodiversity Monitoring Switzerland ;
DSF ; Ephytia ; EPPO Global Database ; EPPO Q-Bank ; FongiBase/FongiFrance ;
MycoDB ; MycoBank ; SwissFungi ; GlobalFungi ; FungalTraits ; RMQS/GIS Sol ;
Earth Microbiome Project ; Global Soil Biodiversity Atlas ; références
bibliographiques associées.

### D8 — Pathologie forestière (21)

EPPO Global Database ; EPPO Data Portal/API ; EPPO Q-Bank ; DSF ; DEPERIS ;
Observatoire des forêts françaises ; inventIF Santé ; RENECOFOR ; ONF Open
Data ; Ephytia ; ICP Forests ; ForDead ; THEIA/Sentinel-2 ; FCBA ; Atlas of
Forest Pests ; Forest Research UK ; EUROPHYT ; EFSA Pest Survey Cards ;
Euphresco ; BDIFF ; synthèse des priorités et lacunes.

### Ressource oubliée à rattacher — Treekipedia / Silvi

Treekipedia n'était pas absente du projet : elle se trouve déjà dans
`21_EXPERIMENTS/_treekipedia_inspection/`, mais elle n'avait pas été remontée
dans le catalogue consolidé. Elle doit être ajoutée comme ressource externe
candidate, distincte des sources françaises officielles.

| Élément | État constaté |
|---|---|
| Site | [treekipedia.silvi.earth](https://treekipedia.silvi.earth) |
| Fonction visible | Authentification et création de zones sur une carte |
| Projet inspecté localement | `21_EXPERIMENTS/_treekipedia_inspection/` — dépôt Silvi cloné pour analyse |
| Nature | Base de connaissances arboricoles, ontologie RDF et application MRV de plantations |
| Données locales repérées | 67 928 espèces ; 3 487 lignes d'insights RDF ; 1 928 lignes GRIIS ; 828 lignes de statut invasif USDA ; 26 tables SQL ; 11 archives GBIF |
| Données non récupérées | 121 champs écologiques complets, 5,7 M tuiles geohash, 31 796 images Wikimedia et 847 polygones d'écorégions nécessitent un accès DB/API Silvi |
| Usages GSIE possibles | Botanical Engine, Knowledge Engine, choix d'essences, provenance taxonomique, suivi de plantations et comparaison internationale |
| Statut GSIE | `RESEARCH` / `metadata_only` — aucune ingestion ou copie autorisée à ce stade |

Treekipedia peut enrichir GSIE, mais ne doit pas être traité comme une vérité
Gold automatique. Il faudra réconcilier ses taxons avec TAXREF/BDNFF/GBIF,
conserver la provenance de chaque assertion, vérifier les licences des données
agrégées et obtenir un accès API ou un export autorisé avant tout FETCH.

## 5. Ressources Ignis et données transverses supplémentaires

`SOURCES_DONNEES_EXHAUSTIVES.md` ajoute des ressources qui ne sont pas toutes
des `DS-*`, mais qui sont nécessaires au jumeau numérique incendie et aux
applications futures :

| Famille | Ressources recensées |
|---|---|
| Topographie et géospatial | BD TOPO/BD TOPO Express, Atlas DFCI, OpenStreetMap, BAN, OSO/CESBIO, API Géoplateforme IGN, API Carto Cadastre, API Calcul altimétrique, BD ALTI, BD Carthage |
| Météorologie et réanalyse | ERA5, Méso-NH, CorrDiff, FourCastNet 3, AIFS, GenCast, Aurora |
| Observation satellite | Copernicus EMS, Sentinel-3, Météosat MTG-FCI, Google FireSat/EFA, EFFIS/GWIS |
| Historique des feux | BDIFF, feuxdeforet.fr, WildfireSpreadTS |
| DFCI et infrastructures | GIP ATGeRi/PIGMA, RTE, Enedis, ANFR Cartoradio |
| Capteurs et citoyen | stations Meshtastic, sensor.community, Météorage, Blitzortung, CAMS |
| Jeux d'apprentissage incendie | Pyro-SDIS, FLAME/FLAME2, D-Fire, FASDD, FIgLib, jeux links-ads, Google FireBench |
| Données synthétiques | GCS-Cinéma Unreal/Niagara, Gazebo, Isaac Sim |
| Capteurs drone | RGB, LWIR radiométrique, CO/CO₂/particules, température/hygrométrie, GPS/IMU |
| Modèles physiques | ForeFire, FARSITE, Rothermel, Balbi, Dupuy |

Ces éléments sont des candidats de recherche ou de raccordement. Leur licence,
les conditions d'API, les quotas et la possibilité d'entraînement doivent être
qualifiés source par source.

## 6. Catalogue QGISIA : ressources cartographiques effectivement référencées

### 6.1 Registre officiel câblé (12)

Plan IGN V2 ; orthophotos nationales ; API Carto Cadastre ; API Carto Limites
administratives ; API Carto WFS Géoplateforme ; geo.api.gouv.fr Communes ;
Overpass API ; NASA GIBS True Color ; NASA GIBS WMTS ; Copernicus Data Space
OData ; Copernicus STAC ; NASA CMR STAC.

### 6.2 Connecteurs additionnels (61)

Fonds OSM/CARTO/Esri/USGS ; Plan IGN, SCAN 25, SCAN Express, Cassini et
État-Major ; orthophotos IGN et orthophotos historiques ; LiDAR HD MNT/MNS ;
RGE ALTI et ombrage ; communes, départements, régions, EPCI, bâtiments,
adresses, routes et voies ferrées ; BD Forêt formations/essences ; zones de
végétation BD TOPO ; Géorisques (PPR, argiles, radon, cavités, mouvements,
ICPE) ; INPN (ZNIEFF, Natura 2000, parcs, réserves) ; GPU (PLU, prescriptions,
servitudes) ; cadastre ; hydrographie IGN ; masses d'eau et bassins SANDRE ;
Corine Land Cover 2012/2018 ; OCS GE ; villes mondiales Natural Earth.

### 6.3 Catalogue JSON (83)

Le catalogue `apps/QGISIA/QGISIA2/config/data_sources.json` ajoute, entre
autres, OpenTopoMap, EOX Sentinel-2 cloudless, ESA WorldCover, couches IGN de
pentes/courbes/admin/parcellaire/RPG, Copernicus DEM, OpenAerialMap, GEBCO,
Natural Earth, Sentinel-2 L2A, Copernicus Land Cover, OpenWeatherMap, réseaux
de randonnée et de transport, catalogues nationaux étrangers, SoilGrids,
Global Forest Watch, NASA FIRMS, OSM/Overpass, HydroSHEDS, GHSL, écorégions
WWF, geoBoundaries et lacs/rivières Natural Earth.

Ces 83 entrées sont un **catalogue d'affichage ou d'interrogation**. Elles ne
doivent pas être comptées comme 83 datasets GSIE indépendants : plusieurs
pointent vers la même famille IGN, OSM, NASA ou Copernicus, et certaines sont
des fonds de carte soumis à attribution.

## 7. Ressources locales prioritaires réellement retrouvées

### 7.1 Diagnostic stationnel et FieldIntake

- `E:\Documents\bts\FICHE DE DIAGNOSTIC STATIONNEL camille (Version Intégrée et Approfon.pdf`
- `E:\Documents\bts\Fiche Diagnostic Forestier Plus fiche térrain vierge.docx`
- `E:\Documents\bts\bio\Diagnostic stationnel Camille Perraudeau.docx`
- `E:\Documents\bts\EIL Carto\Diagnostic_stationnel_Longeyroux_Placette_EIL.docx`
- `E:\Documents\bts\Référentiel Par Défaut + Fiche Terrain A4 — Gradients Autoécologiques.docx`
- rapports CCF martelage et épreuves de terrain ; relevés ODT de parcelles et
  fiches horodatées du PSG tutoré ; rapports DEPERIS Longeyroux.

### 7.2 Inventaire, dendrométrie et sylviculture

- tableur comparatif de placettes ; `Données inv 489 points2.xlsx` ;
  `Description_pplmnts2026.xlsx` ; `données terrain.xlsx` ;
- analyses de parcelles de la forêt domaniale de la Vergne ; dossiers
  d'amélioration des peuplements et du Douglas ; conseils sylvicoles pour
  propriétaires ; peuplements à bois moyens ;
- guides ONF de hêtraie nord-atlantique, hêtraies continentales, sapinières
  du Morvan, chênaie atlantique ; fiches chêne sessile/pédonculé, pin
  sylvestre, pin maritime, autres essences ; guides CNPF/CRPF et SRGS Limousin ;
- Memento FCBA, documents de classement du hêtre et rapports de prix des
  bois sur pied.

### 7.3 Santé, biodiversité, forêt-gibier et climat

- fiches Bombyx disparate, pathogènes, bilans phytosanitaires et DEPERIS ;
- guides équilibre forêt-gibier, ONCFS, EFESE, dégâts de grand gibier,
  perturbations trophiques et IBP ;
- rapports et cartes DFCI, PPFCI/PDPFCI, guides opérationnels feux de forêt ;
- documents de climat, événements extrêmes, changement climatique et
  questionnaires de terrain.

### 7.4 Données géospatiales et projet

- `CCF Celles sur Plaine.gpkg`, `Placette.gpkg`, couches Longeyroux et PSG ;
- rasters MNT/MNS/MNH, LiDAR HD, cartes pH/RUM, orthophotos et cartes par
  essence ;
- `E:\Documents\chantier_ecole_osm.geojson` ; projets DFCI avec GeoPackages
  multi-couches ;
- documentation locale GeoSylva, QGISIA, QField, audits QGIS, schémas de
  base locale et fichiers de build.

## 8. Règles de qualification et de routage

| Ressource | Routage autorisé maintenant | Interdiction |
|---|---|---|
| Source publique/API non qualifiée | fiche Data Registry `DISCOVERED` ou `metadata_only` | copie ou conclusion citable sans licence/checksum |
| Document institutionnel | fiche bibliographique `citation_only` | redistribution, extraction de règles non relue, entraînement |
| Production personnelle BTS | FieldIntake/quarantaine avec consentement et contrôle des tiers | promotion Gold directe |
| Donnée de propriété, PSG ou coordonnées sensibles | registre restreint, floutage éventuel | exposition client, cloud ou benchmark ouvert |
| Fonds de carte WMTS/WMS/XYZ | proxy pour visualisation | l'utiliser comme preuve historique sans archive |
| Raster/vecteur destiné à un calcul | FETCH borné puis RAW/SILVER après qualification | téléchargement implicite ou promotion automatique |
| Image ou scan | quarantaine, OCR contrôlé si nécessaire | réutilisation iconographique ou vérité terrain automatique |

Le catalogue ne modifie pas la décision actuelle : FETCH canonique reste
fermé, à l'exception du micro-extrait SoilGrids explicitement autorisé par
`DEC-000061`. Aucune ressource locale n'est ingérée par ce rapport.

## 9. Lacunes et corrections à apporter à la documentation

1. `DATASET_CATALOG.md` s'arrête aux familles `DS-*` et ne référence pas
   explicitement les 113 fiches spécialisées ; il faut ajouter des liens vers
   les huit dossiers D1–D8.
2. Les connecteurs QGISIA mélangent parfois dataset, service, couche et fond
   de carte. Ils doivent être enregistrés comme `Distribution` ou `Proxy`,
   pas comme nouveaux `Dataset`.
3. Les noms d'API hérités (INPN, Prométhée, certains endpoints Copernicus)
   doivent conserver un statut de santé et un millésime ; une URL morte ne
   doit jamais être considérée comme une source disponible.
4. Les droits d'entraînement IA, les droits d'annotation dérivée et la
   sensibilité spatiale doivent être des champs explicites du Data Registry.
5. Les fichiers locaux contenant des données personnelles, de propriété ou
   des coordonnées précises restent hors benchmark ouvert tant que le
   consentement et le floutage ne sont pas documentés.

## 10. Prochaine tranche recommandée

1. Valider ce catalogue comme inventaire documentaire, sans promotion de
   données.
2. Réconcilier les 34 familles canoniques et les 113 fiches spécialisées en
   identifiants `Dataset`/`Distribution`/`Source`.
3. Dédupliquer les 3 077 ressources locales par checksum, provenance et
   contexte, sans supprimer les copies.
4. Choisir un seul lot public et un seul lot personnel pour FieldIntake et
   GSIE-Bench ; garder tous les autres en quarantaine.
5. Qualifier légalement et techniquement les sources prioritaires avant toute
   ouverture FETCH.

## 11. Sources et preuves

- `GSIE/DATASETS/DATASET_CATALOG.md`
- `GSIE/DATASETS/SOURCES_DONNEES_EXHAUSTIVES.md`
- `GSIE/DATASETS/NOMENCLATURE_SOURCES.md`
- `GSIE/DATASETS/CANDIDATES_RESSOURCES_EDOCUMENTS.md`
- `GSIE/DATASETS/inventory_edocuments/manifest.csv` et `summary.json` (local,
  ignoré par Git)
- `GSIE/RESEARCH/SOURCES/sources_d1_taxonomie_botanique.md`
  à `sources_d8_pathologie_forestiere.md`
- `apps/QGISIA/src/lib/official-sources.ts`
- `apps/QGISIA/src/lib/additional-sources.ts`
- `apps/QGISIA/QGISIA2/config/data_sources.json`
- `02_RFC/RFC-0038-data-registry-gsie.md`
- `02_RFC/RFC-0039-gsie-bench-v0.1.md` (si présent)

## 12. Historique

| Version | Date | Modification |
|---|---|---|
| 1.0.0 | 2026-08-13 | Consolidation exhaustive du catalogue GSIE, des huit dossiers scientifiques, des connecteurs QGISIA et de l'inventaire local 3 077 ressources. |

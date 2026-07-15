# Sources de données — Climatologie

| Champ | Valeur |
|---|---|
| **Domaine** | Climatologie |
| **Livrable** | D4 — Recensement des sources climatologiques |
| **Phase** | 3 — Connaissance |
| **Statut** | Draft |
| **Date de révision** | 2026-07-15 |
| **Lois fondatrices** | GSIE-CON-002, GSIE-CON-003, GSIE-CON-005 |
| **Documents connexes** | 307 (Sourcing Plan), 305 (Dataset Catalog), 204 (Engine Development Order) |
| **Moteurs concernés** | Climate Engine, Forest Dynamics Engine, Simulation Engine |

---

## 1. Objet

Recenser l'ensemble des sources de données climatiques pertinentes pour
le projet GSIE, en couvrant les projections climatiques régionalisées,
les réanalyses, les modèles globaux, les indices bioclimatiques et les
outils d'aide à la décision climatique pour la forêt. Chaque source est
documentée selon une grille standard : accès, licence, volume,
variables, résolution, couverture et priorité GSIE.

Les priorités (P0/P1/P2) correspondent à l'alignement sur l'ordre de
développement des moteurs (livrable 204) :

- **P0** — source bloquante pour le Climate Engine ou le Forest Dynamics
  Engine ;
- **P1** — source importante, ingestion recommandée dans la vague 1-2 ;
- **P2** — source complémentaire, ingestion opportuniste.

---

## 2. Tableau synthétique

| # | Source | Organisme | Type d'accès | Couverture | Priorité |
|---|---|---|---|---|---|
| S-CLIM-01 | DRIAS — Les futurs du climat | Météo-France | file_download | France | P0 |
| S-CLIM-02 | Données publiques Météo-France (Safran, ARPEGE) | Météo-France | file_download | France | P0 |
| S-CLIM-03 | Copernicus Climate Data Store (CDS) | Copernicus / ECMWF | api_rest | Mondial | P0 |
| S-CLIM-04 | CMIP6 — Earth System Grid Federation | WCRP / ESGF | file_download | Mondial | P1 |
| S-CLIM-05 | DRIAS-Eau | Météo-France | file_download | France | P1 |
| S-CLIM-06 | ClimEssences | ONF / CNPF | knowledge_extraction | France | P1 |
| S-CLIM-07 | BioClimSol / FORECCAsT | CNPF / INRAE / ONF | knowledge_extraction | France | P1 |
| S-CLIM-08 | Fire Weather Index (CEMS Fire Historical) | Copernicus / ECMWF | api_rest | Mondial | P0 |
| S-CLIM-09 | Climadiag Agriculture et Forêt | Météo-France / Solagro | knowledge_extraction | France | P2 |
| S-CLIM-10 | EFFIS — European Forest Fire Information System | Copernicus / JRC | file_download | Europe | P1 |

---

## 3. Fiches détaillées par source

### S-CLIM-01 — DRIAS, Les futurs du climat

| Champ | Valeur |
|---|---|
| **Nom officiel** | DRIAS — Les futurs du climat |
| **Organisme** | Météo-France (avec IPSL, CERFACS, CNRM) |
| **URL d'accès** | https://www.drias-climat.fr/ |
| **URL espace données** | https://www.drias-climat.fr/acces_aux_donnnees |
| **URL data.gouv.fr** | https://www.data.gouv.fr/datasets/drias-projections-climatiques-pour-ladaptation-de-nos-societes |
| **Type d'accès** | `file_download` (NetCDF, CSV) |
| **Licence** | Licence Ouverte / Open Licence (données sur data.gouv.fr). **Inscription gratuite requise** sur le portail DRIAS pour télécharger les données : création de compte + acceptation des conditions d'utilisation. Les données sont gratuites mais l'accès est conditionné à l'inscription. |
| **Volume estimé** | Plusieurs To (17 couples de modèles régionaux Euro-Cordex, 3 scénarios RCP, période 1976-2100, résolution 8 km) |
| **Variables** | Température (moyenne, min, max), précipitations, vent, humidité, rayonnement, ETP (Penman-Monteith FAO), SWI (Soil Wetness Index), indices bioclimatiques (jours de risque feu élevé, jours de sols secs, déficit hydrique) |
| **Résolution spatiale** | 8 km × 8 km (grille Safran) |
| **Résolution temporelle** | Journalière à annuelle selon le produit |
| **Couverture** | France métropolitaine, Corse, Outre-mer |
| **Priorité GSIE** | **P0** — source primaire de projections climatiques régionalisées pour le Climate Engine |
| **Jeux de données** | DRIAS-2020 (Euro-Cordex, RCP 2.6/4.5/8.5), Explore2 (17 couples, correction de biais Adamont et CDF-t), TRACC-2023 (trajectoire de réchauffement de référence) |
| **Format** | NetCDF, CSV |
| **Notes** | Le jeu Explore2 complète DRIAS-2020 avec 7 nouvelles simulations. Les données intègrent la TRACC (+2 °C en 2030, +2,7 °C en 2050, +4 °C en 2100). L'espace « Accompagnement » fournit un guide d'utilisation et de bonnes pratiques. |

---

### S-CLIM-02 — Données publiques Météo-France (Safran, ARPEGE)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Données publiques de Météo-France — Safran-SIM2, ARPEGE |
| **Organisme** | Météo-France |
| **URL portail actuel** | https://donneespubliques.meteofrance.fr/ |
| **URL open data** | https://meteo.data.gouv.fr/ (migration en cours) |
| **URL data.gouv.fr** | https://www.data.gouv.fr/organizations/meteo-france/datasets |
| **URL ARPEGE** | https://donneespubliques.meteofrance.fr/?fond=produit&id_produit=130&id_rubrique=51 |
| **Type d'accès** | `file_download` (GRIB, NetCDF, CSV) |
| **Licence** | Licence Ouverte / Open Licence (depuis le 1er janvier 2024, toutes les données publiques Météo-France sont en accès libre) |
| **Volume estimé** | Plusieurs To (Safran-SIM2 : grille 8 km sur toute la France, 1958-présent, journalier) |
| **Variables** | **Safran-SIM2** : température (min, max, moyenne), précipitations, vent, humidité, rayonnement, ETP, bilan hydrique du sol, neige. **ARPEGE** : champs atmosphériques 3D (pression, température, vent, humidité, géopotentiel), prévisions globales |
| **Résolution spatiale** | Safran : 8 km × 8 km (grille France). ARPEGE : ~7,5 km sur France (résolution horizontale variable selon le domaine) |
| **Résolution temporelle** | Safran : journalière (1958-présent). ARPEGE : horaire à 6h selon le produit (prévision) |
| **Couverture** | France métropolitaine (Safran), mondiale (ARPEGE) |
| **Priorité GSIE** | **P0** — Safran est la référence de réanalyse spatialisée pour la France, base de correction des projections DRIAS |
| **Format** | GRIB, NetCDF, CSV |
| **Notes** | Depuis novembre 2023, toutes les données publiques Météo-France sont libérées en open data. Le portail `donneespubliques.meteofrance.fr` est en cours de migration vers `meteo.data.gouv.fr`. Safran-SIM2 est la réanalyse de référence utilisée par DRIAS pour la correction de biais. |

---

### S-CLIM-03 — Copernicus Climate Data Store (CDS)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Copernicus Climate Data Store (CDS) |
| **Organisme** | Copernicus Climate Change Service (C3S) / ECMWF |
| **URL d'accès** | https://cds.climate.copernicus.eu/ |
| **URL API** | https://cds.climate.copernicus.eu/api |
| **URL documentation API** | https://cds.climate.copernicus.eu/how-to-api |
| **URL catalogue** | https://cds.climate.copernicus.eu/datasets |
| **Type d'accès** | `api_rest` (Python `cdsapi`) + `file_download` (interface web) |
| **Licence** | Accès ouvert, gratuit et non restreint. **Inscription requise** (Personal Access Token). Acceptation des Terms of Use de chaque dataset requise avant téléchargement. Licence Copernicus standard (compatible réutilisation commerciale). |
| **Volume estimé** | 3,8 Petabytes (140+ datasets) |
| **Variables** | Température, précipitations, vent, humidité, rayonnement, pression, ETP, indices bioclimatiques (FWI), réanalyses (ERA5), prévisions saisonnières, projections climatiques (CMIP5/CMIP6 via ESGF), variables ECV (Essential Climate Variables) |
| **Résolution spatiale** | Variable selon le dataset : ERA5 (0,25° ≈ 31 km), CORDEX (0,11° ≈ 12,5 km / 0,44° ≈ 50 km), FWI (~10 km) |
| **Résolution temporelle** | Variable : horaire (ERA5), journalière, mensuelle, saisonnière, décennale |
| **Couverture** | Mondiale |
| **Priorité GSIE** | **P0** — source pivot pour les réanalyses ERA5, les projections CORDEX et les indices FWI |
| **Datasets clés pour GSIE** | `reanalysis-era5-single-levels`, `reanalysis-era5-land`, `cems-fire-historical-v1` (FWI), `projections-cmip6`, `satellite-soil-moisture` |
| **Format** | GRIB (recommandé), NetCDF (expérimental) |
| **Notes** | Le client Python `cdsapi` s'installe via `pip install cdsapi`. Configuration via `~/.cdsapirc` avec l'URL et le Personal Access Token. Un nouveau client `ecmwf-datastores-client` est disponible avec des fonctionnalités avancées (REST API synchrone/asynchrone). |

---

### S-CLIM-04 — CMIP6 — Earth System Grid Federation

| Champ | Valeur |
|---|---|
| **Nom officiel** | Coupled Model Intercomparison Project Phase 6 (CMIP6) |
| **Organisme** | World Climate Research Programme (WCRP) / Earth System Grid Federation (ESGF) |
| **URL portail** | https://wcrp-cmip.org/cmip-data-access/ |
| **URL nœud IPSL** | https://esgf-node.ipsl.upmc.fr/projects/cmip6-ipsl/ |
| **URL nœud LLNL** | https://pcmdi.llnl.gov/CMIP6/ArchiveStatistics/esgf_data_holdings/ |
| **URL nœud DKRZ** | https://esgf-data.dkrz.de/search/cmip6-dkrz/ |
| **Type d'accès** | `file_download` (ESGF nodes, OpenDAP, Globus, Wget) |
| **Licence** | Accès ouvert et gratuit. Licence Creative Commons ou équivalent selon les modèles (varie par institution). Inscription recommandée sur un nœud ESGF pour le téléchargement. |
| **Volume estimé** | Plusieurs Po (Petaoctets) — CMIP6 est l'archive climatique mondiale la plus volumineuse |
| **Variables** | Température (surface, atmosphère, océan), précipitations, vent, humidité, rayonnement, pression, nébulosité, variables terrestres (ruissellement, humidité du sol, neige), variables océaniques, cycles biogéochimiques |
| **Résolution spatiale** | Variable selon le modèle : ~100 km à ~25 km (typiquement 1° à 0,25°) |
| **Résolution temporelle** | 3h, 6h, journalière, mensuelle, annuelle selon l'expérience et la variable |
| **Couverture** | Mondiale |
| **Priorité GSIE** | **P1** — source de référence pour les scénarios GIEC (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5). Les projections régionalisées DRIAS sont issues de CMIP6 via Euro-Cordex. |
| **Scénarios** | SSP1-2.6, SSP1-1.9, SSP2-4.5, SSP3-7.0, SSP4-3.4, SSP4-6.0, SSP5-3.4, SSP5-8.5 |
| **Format** | NetCDF (CMIP6 standard), DRS (Data Reference Syntax) |
| **Notes** | Les données CMIP6 sont distribuées via un réseau fédéré de nœuds ESGF. Pour la France, le nœud IPSL (`esgf-node.ipsl.upmc.fr`) est le point d'entrée privilégié. Les identifiants de variables suivent la nomenclature CMIP6 (ex. `tas` pour température surface, `pr` pour précipitations, `tasmin`, `tasmax`, `sfcWind`, `hurs`, `rsds`). |

---

### S-CLIM-05 — DRIAS-Eau

| Champ | Valeur |
|---|---|
| **Nom officiel** | DRIAS-Eau — Portail de données hydrologiques |
| **Organisme** | Météo-France (projet LIFE Eau&Climat / Explore2) |
| **URL d'accès** | https://www.drias-climat.fr/eau |
| **URL présentation** | https://meteofrance.com/le-changement-climatique/drias-eau-quel-futur-pour-leau-en-france |
| **Type d'accès** | `file_download` (NetCDF, CSV) |
| **Licence** | Licence Ouverte / Open Licence. **Inscription gratuite requise** (même compte que DRIAS climat). |
| **Volume estimé** | Plusieurs centaines de Go (projections hydrologiques sur la France, multiples scénarios) |
| **Variables** | Débit des cours d'eau, recharge des nappes, humidité du sol, SWI (Soil Wetness Index), évapotranspiration, précipitations efficaces, bilan hydrique |
| **Résolution spatiale** | Grille 8 km (Safran) pour les variables atmosphériques ; réseau hydrographique pour les débits |
| **Résolution temporelle** | Journalière à mensuelle |
| **Couverture** | France hexagonale et Corse |
| **Priorité GSIE** | **P1** — source pour le couplage climat-hydrologie, pertinente pour le moteur Hydro et Forest Dynamics (stress hydrique) |
| **Notes** | DRIAS-Eau a été ouvert en 2023 dans le cadre du projet LIFE Eau&Climat. Les projections hydrologiques sont produites avec les modèles SIM2 et les forçages Explore2. |

---

### S-CLIM-06 — ClimEssences

| Champ | Valeur |
|---|---|
| **Nom officiel** | ClimEssences |
| **Organisme** | Office National des Forêts (ONF) / Centre National de la Propriété Forestière (CNPF) — réseau AFORCE |
| **URL d'accès** | https://climessences.fr/ |
| **URL documentation** | https://climessences.fr/documentation |
| **URL page ONF** | https://www.onf.fr/onf/+/c41::adaptation-des-forets-au-changement-climatique-les-outils-pour-agir-climessences.html |
| **Type d'accès** | `knowledge_extraction` (interface web cartographique, pas de téléchargement de données brutes) |
| **Licence** | Accès libre et gratuit. Données issues de modèles climatiques DRIAS/GIEC. Pas de licence ouverte explicite sur les données dérivées. |
| **Volume estimé** | N/A (outil web interactif, pas de téléchargement massif) |
| **Variables** | Compatibilité climatique des essences (modèle IKS) : déficit hydrique, température minimale annuelle (froid hivernal), cumul annuel de température (manque de chaleur). Cartes d'analogie climatique. |
| **Résolution spatiale** | 1 km² (données climatiques modélisées) |
| **Résolution temporelle** | Référence « actuelle » + horizons 2050 et 2070 |
| **Couverture** | France (régions forestières françaises) |
| **Priorité GSIE** | **P1** — source de connaissance pour le Forest Dynamics Engine (compatibilité essence × climat) |
| **Scénarios** | RCP 4.5 et RCP 8.5, 3 modélisations (optimiste, intermédiaire, pessimiste), 2 horizons (2050, 2070) |
| **Essences** | 60 essences forestières européennes modélisées via IKS |
| **Notes** | ClimEssences fusionne deux projets AFORCE : Caravane (base de données espèces, 37 critères) et IKSMAP (modèle de compatibilité climatique IKS). Le modèle IKS utilise trois indicateurs limitants : sécheresse (déficit hydrique), froid hivernal, manque de chaleur. Pas d'API ni de téléchargement de données brutes — extraction de connaissance via l'interface web. |

---

### S-CLIM-07 — BioClimSol / FORECCAsT

| Champ | Valeur |
|---|---|
| **Nom officiel** | BioClimSol — Outil de diagnostic sylvo-climatique / FORECCAsT by BioClimSol |
| **Organisme** | CNPF-IDF (pilote), avec INRAE, Météo-France, IGN, ONF, AgroParisTech, DSF |
| **URL CNPF** | https://www.cnpf.fr/decouvrez-bioclimsol |
| **URL AFORCE** | https://reseau-aforce.fr/bioclimsol-0 |
| **URL Zenodo** | https://doi.org/10.5281/zenodo.15303104 |
| **Type d'accès** | `knowledge_extraction` (application Android, version RStudio, version QGIS) |
| **Licence** | Accès libre. Outil collaboratif. Pas de licence ouverte explicite sur les données sous-jacentes. |
| **Volume estimé** | N/A (outil de diagnostic à l'échelle parcelle, base de données de 5000+ placettes) |
| **Variables** | Risque de dépérissement (indice synthétique), compatibilité climatique et pédologique de 48 essences, facteurs biotiques (agents pathogènes), données climatiques historiques et projetées (température, précipitations, déficit hydrique), caractéristiques stationnelles (sol, topographie, réserve utile en eau) |
| **Résolution spatiale** | Échelle parcelle (saisie terrain) à échelle massif (QGIS/RStudio) |
| **Résolution temporelle** | Climat actuel + scénarios futurs (horizons multiples) |
| **Couverture** | France |
| **Priorité GSIE** | **P1** — source de connaissance pour le Forest Dynamics Engine et le Diagnostic Engine (risque de dépérissement) |
| **Formats** | Application Android (FORECCAsT), RStudio (recherche), QGIS (cartographique) |
| **Notes** | BioClimSol combine trois dimensions : BIO (agents biotiques), CLIM (données climatiques et extrêmes), SOL (facteurs compensateurs ou aggravants). La base de données nationale compte plus de 5000 placettes. Les recommandations croisent l'autécologie des essences avec les données climatiques DRIAS/Météo-France. Contact : bioclimsol@cnpf.fr |

---

### S-CLIM-08 — Fire Weather Index (CEMS Fire Historical)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Fire danger indices historical data from the Copernicus Emergency Management Service |
| **Organisme** | Copernicus Emergency Management Service (CEMS) / ECMWF |
| **URL dataset** | https://ewds.climate.copernicus.eu/datasets/cems-fire-historical-v1 |
| **URL documentation** | https://confluence.ecmwf.int/display/CEMS/User+Guide+for++Fire+danger+indices+historical+data+from+the+Copernicus+Emergency+Management+Service |
| **URL STAC** | https://ewds.climate.copernicus.eu/stac-browser/collections/cems-fire-historical-v1 |
| **URL Copernicus FWI** | https://climate.copernicus.eu/fire-weather-index |
| **Type d'accès** | `api_rest` (Python `cdsapi`) + `file_download` + `stac_api` |
| **Licence** | Accès ouvert et gratuit. **Inscription requise** (compte Copernicus). Acceptation des Terms of Use du dataset. |
| **Volume estimé** | Plusieurs To (données quotidiennes 1940-présent, grille mondiale ~10 km) |
| **Variables** | Fire Weather Index (FWI), Fine Fuel Moisture Code (FFMC), Duff Moisture Code (DMC), Drought Code (DC), Initial Spread Index (ISI), Buildup Index (BUI), Daily Severity Rating (DSR) |
| **Résolution spatiale** | ~10 km (0,1°) |
| **Résolution temporelle** | Journalière (depuis 1940 pour l'historique, jusqu'à 2098 pour les projections) |
| **Couverture** | Mondiale |
| **Priorité GSIE** | **P0** — source primaire d'indices bioclimatiques feu pour le moteur Ignis et le Climate Engine |
| **DOI** | 10.24381/cds.0e89c522 |
| **Format** | NetCDF, GRIB |
| **Notes** | Le FWI est basé sur le système canadien Forest Fire Weather Index, adopté par EFFIS en 2007 comme méthode harmonisée pour l'Europe. Les données historiques sont calculées à partir des réanalyses ERA5 d'ECMWF. Les projections futures utilisent les scénarios RCP 2.6, 4.5 et 8.5. Version 2.0 corrigée recommandée. Le dataset inclut aussi les systèmes américain (NFDRS) et australien (Mark 5). |

---

### S-CLIM-09 — Climadiag Agriculture et Forêt

| Champ | Valeur |
|---|---|
| **Nom officiel** | Climadiag Agriculture et Forêt (anciennement Climadiag Agriculture / CANARI) |
| **Organisme** | Météo-France / Solagro |
| **URL d'accès** | https://climadiag-agriculture.fr/ |
| **URL Météo-France** | https://meteofrance.com/le-changement-climatique/climadiag-agriculture-un-service-pour-sadapter-au-rechauffement-climatique |
| **Type d'accès** | `knowledge_extraction` (interface web, calcul d'indicateurs en ligne) |
| **Licence** | Accès libre et gratuit. Service public Météo-France. |
| **Volume estimé** | N/A (service web de calcul d'indicateurs, pas de téléchargement massif) |
| **Variables** | ~300 indicateurs : température (moyenne, min, max, somme, jours chauds/froids), précipitations, ETP (Penman-Monteith FAO), déficit hydrique cumulé, rayonnement, vent, SWI (Soil Wetness Index), indicateurs agro-climatiques par culture, premiers indicateurs forestiers |
| **Résolution spatiale** | 8 km (grille Safran) |
| **Résolution temporelle** | Indicateurs annuels calculés sur les horizons TRACC (+2 °C / +2,7 °C / +4 °C) |
| **Couverture** | France métropolitaine |
| **Priorité GSIE** | **P2** — source complémentaire pour les indicateurs agro-climatiques et forestiers. Les données brutes sous-jacentes sont accessibles via DRIAS (S-CLIM-01). |
| **Notes** | Climadiag utilise une approche multi-modèles (17 couples GCM×RCM) pour prendre en compte les incertitudes. Les indicateurs sont construits selon la TRACC. L'outil CANARI permet de calculer en ligne des indicateurs agro-climatiques locaux à partir de projections climatiques. |

---

### S-CLIM-10 — EFFIS — European Forest Fire Information System

| Champ | Valeur |
|---|---|
| **Nom officiel** | European Forest Fire Information System (EFFIS) |
| **Organisme** | Copernicus Emergency Management Service / Joint Research Centre (JRC) — Commission européenne |
| **URL d'accès** | https://forest-fire.emergency.copernicus.eu/ |
| **URL données** | https://forest-fire.emergency.copernicus.eu/applications/data-and-services |
| **URL FWI technique** | https://forest-fire.emergency.copernicus.eu/about-effis/technical-background/fire-danger-forecast |
| **Type d'accès** | `file_download` (Web services, export cartographique) |
| **Licence** | Accès ouvert et gratuit. Données Copernicus. |
| **Volume estimé** | Plusieurs Go (cartes de surfaces brûlées, statistiques nationales, FWI journalier) |
| **Variables** | Surfaces brûlées (modulation spatiale), nombre de feux de forêt, Fire Weather Index (FWI), niveau de danger feu, cartes de danger journalières |
| **Résolution spatiale** | ~10 km (FWI), modulation spatiale des surfaces brûlées (résolution Landsat/Sentinel) |
| **Résolution temporelle** | Journalière (FWI), annuelle (statistiques de surfaces brûlées) |
| **Couverture** | Europe, Moyen-Orient, Afrique du Nord |
| **Priorité GSIE** | **P1** — source pour le moteur Ignis (validation historique des feux, statistiques nationales) |
| **Format** | Shapefile, GeoTIFF, CSV, XLS |
| **Notes** | EFFIS adopte le système canadien FWI depuis 2007 comme méthode harmonisée pour l'Europe. Les données FWI d'EFFIS sont accessibles via le CDS (S-CLIM-08). EFFIS fournit aussi des statistiques annuelles par pays (surfaces brûlées, nombre de feux) téléchargeables en format XLS. |

---

## 4. Synthèse des variables par source

| Variable | S-CLIM-01 (DRIAS) | S-CLIM-02 (Safran/ARPEGE) | S-CLIM-03 (CDS) | S-CLIM-04 (CMIP6) | S-CLIM-05 (DRIAS-Eau) | S-CLIM-06 (ClimEssences) | S-CLIM-07 (BioClimSol) | S-CLIM-08 (FWI) | S-CLIM-09 (Climadiag) | S-CLIM-10 (EFFIS) |
|---|---|---|---|---|---|---|---|---|---|---|
| Température | ✅ | ✅ | ✅ | ✅ | — | ✅ (dérivée) | ✅ | — | ✅ | — |
| Précipitations | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (dérivée) | ✅ | — | ✅ | — |
| Vent | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ (composante FWI) | ✅ | — |
| Humidité | ✅ | ✅ | ✅ | ✅ | ✅ (SWI) | — | ✅ (sol) | ✅ (FFMC/DMC/DC) | ✅ (SWI) | — |
| ETP | ✅ | ✅ | ✅ | — | ✅ | — | — | — | ✅ | — |
| Rayonnement | ✅ (5 simul.) | ✅ | ✅ | ✅ | — | — | — | — | ✅ | — |
| Déficit hydrique | ✅ | ✅ (bilan) | — | — | ✅ | ✅ (indicateur IKS) | ✅ | — | ✅ | — |
| FWI / indices feu | ✅ (jours risque) | — | ✅ | — | — | — | — | ✅ | — | ✅ |
| Humidité du sol | ✅ (SWI) | ✅ (SIM2) | ✅ | ✅ | ✅ | — | ✅ (RUF) | ✅ (DC) | ✅ (SWI) | — |
| Indices bioclimatiques | ✅ | — | ✅ | — | — | ✅ (IKS) | ✅ (dépérissement) | ✅ | ✅ | ✅ |

---

## 5. Synthèse des conditions d'accès

| Source | Inscription requise | Coût | Conditions spéciales |
|---|---|---|---|
| DRIAS (S-CLIM-01) | **Oui** — compte gratuit sur drias-climat.fr | Gratuit | Acceptation des conditions d'utilisation lors de l'inscription |
| Météo-France (S-CLIM-02) | Non (depuis 2024) | Gratuit | Licence Ouverte / Open Licence |
| Copernicus CDS (S-CLIM-03) | **Oui** — compte Copernicus + Personal Access Token | Gratuit | Acceptation des Terms of Use par dataset |
| CMIP6 / ESGF (S-CLIM-04) | Recommandée (nœud ESGF) | Gratuit | Licence variable par institution |
| DRIAS-Eau (S-CLIM-05) | **Oui** — même compte que DRIAS | Gratuit | Conditions identiques à DRIAS |
| ClimEssences (S-CLIM-06) | Non | Gratuit | Pas d'API ni de téléchargement de données brutes |
| BioClimSol (S-CLIM-07) | Non | Gratuit | Application Android, pas d'accès programmatique |
| FWI / CEMS (S-CLIM-08) | **Oui** — compte Copernicus | Gratuit | Acceptation des Terms of Use du dataset |
| Climadiag (S-CLIM-09) | Non | Gratuit | Service web, pas de téléchargement massif |
| EFFIS (S-CLIM-10) | Non | Gratuit | Web services, export manuel |

---

## 6. Recommandations d'ingestion pour GSIE

### 6.1 Vague 1 — Climate Engine (P0)

Priorité d'ingestion pour le moteur Climate :

1. **DRIAS (S-CLIM-01)** — projections régionalisées France 8 km, source
   primaire pour le Climate Engine. Inscription requise.
2. **Safran-SIM2 (S-CLIM-02)** — réanalyse de référence pour la France,
   base de correction de biais des projections. Accès direct open data.
3. **Copernicus CDS (S-CLIM-03)** — ERA5 pour le contexte européen et
   mondial, FWI historique. API `cdsapi` pour ingestion automatisée.
4. **FWI / CEMS (S-CLIM-08)** — indices bioclimatiques feu, critique
   pour le moteur Ignis en parallèle (vague I).

### 6.2 Vague 2 — Forest Dynamics Engine (P1)

5. **CMIP6 / ESGF (S-CLIM-04)** — scénarios GIEC mondiaux pour le
   contexte et la validation des projections régionalisées.
6. **ClimEssences (S-CLIM-06)** — extraction de connaissance sur la
   compatibilité essence × climat (modèle IKS).
7. **BioClimSol (S-CLIM-07)** — extraction de connaissance sur le
   risque de dépérissement (approche BIO + CLIM + SOL).
8. **EFFIS (S-CLIM-10)** — validation historique des feux en Europe.
9. **DRIAS-Eau (S-CLIM-05)** — projections hydrologiques pour le
   couplage climat-hydrologie.

### 6.3 Vague 3 — Compléments (P2)

10. **Climadiag (S-CLIM-09)** — indicateurs agro-climatiques et
    forestiers pré-calculés. Les données brutes sont déjà accessibles
    via DRIAS, Climadiag apporte une valeur ajoutée de calcul
    d'indicateurs.

---

## 7. Notes méthodologiques

### 7.1 Vérification des URLs

Toutes les URLs de ce document ont été vérifiées le 2026-07-15 via
recherche web. Les URLs principales sont :

- DRIAS : https://www.drias-climat.fr/ (confirmé par Météo-France)
- data.gouv.fr DRIAS :
  https://www.data.gouv.fr/datasets/drias-projections-climatiques-pour-ladaptation-de-nos-societes
- Météo-France données publiques : https://donneespubliques.meteofrance.fr/
- Copernicus CDS : https://cds.climate.copernicus.eu/
- Copernicus CDS API : https://cds.climate.copernicus.eu/how-to-api
- CMIP6 WCRP : https://wcrp-cmip.org/cmip-data-access/
- CMIP6 ESGF IPSL : https://esgf-node.ipsl.upmc.fr/projects/cmip6-ipsl/
- DRIAS-Eau : https://www.drias-climat.fr/eau
- ClimEssences : https://climessences.fr/
- BioClimSol (CNPF) : https://www.cnpf.fr/decouvrez-bioclimsol
- FWI CEMS : https://ewds.climate.copernicus.eu/datasets/cems-fire-historical-v1
- Copernicus FWI : https://climate.copernicus.eu/fire-weather-index
- EFFIS : https://forest-fire.emergency.copernicus.eu/
- Climadiag : https://climadiag-agriculture.fr/

### 7.2 Conditions d'accès DRIAS — détail

DRIAS est **gratuit mais conditionné à une inscription** :

1. Créer un compte sur https://www.drias-climat.fr/ (inscription
   gratuite).
2. Accepter les conditions d'utilisation lors de l'inscription.
3. L'espace « Données et Produits » permet le téléchargement en format
   NetCDF ou CSV.
4. Les données sont aussi référencées sur data.gouv.fr sous Licence
   Ouverte / Open Licence, mais le téléchargement des fichiers complets
   passe par le portail DRIAS avec authentification.
5. Aucune API REST documentée — l'accès se fait via l'interface web de
   téléchargement.

### 7.3 Compatibilité des licences

| Source | Licence | Réutilisation commerciale |
|---|---|---|
| DRIAS | Licence Ouverte / Open Licence | Oui |
| Météo-France open data | Licence Ouverte / Open Licence | Oui |
| Copernicus CDS | Licence Copernicus | Oui |
| CMIP6 / ESGF | Variable par institution | À vérifier par modèle |
| ClimEssences | Non explicitement ouverte | Extraction de connaissance uniquement |
| BioClimSol | Non explicitement ouverte | Extraction de connaissance uniquement |
| EFFIS | Licence Copernicus | Oui |

---

## 8. Références

1. Météo-France, « DRIAS, les futurs du climat »,
   https://meteofrance.com/le-changement-climatique/drias-les-futurs-du-climat-des-projections-climatiques-pour-adapter-nos
2. Copernicus, « The Climate Data Store »,
   https://climate.copernicus.eu/climate-data-store
3. ECMWF, « CDSAPI setup », https://cds.climate.copernicus.eu/how-to-api
4. WCRP, « CMIP Data Access », https://wcrp-cmip.org/cmip-data-access/
5. Copernicus, « Fire Weather Index »,
   https://climate.copernicus.eu/fire-weather-index
6. ECMWF, « Fire danger indices historical data »,
   https://ewds.climate.copernicus.eu/datasets/cems-fire-historical-v1
7. ONF/CNPF, « ClimEssences », https://climessences.fr/
8. CNPF, « Découvrez BioClimSol », https://www.cnpf.fr/decouvrez-bioclimsol
9. Météo-France, « DRIAS-Eau »,
   https://meteofrance.com/le-changement-climatique/drias-eau-quel-futur-pour-leau-en-france
10. Météo-France/Solagro, « Climadiag Agriculture et Forêt »,
    https://meteofrance.com/le-changement-climatique/climadiag-agriculture-un-service-pour-sadapter-au-rechauffement-climatique
11. Copernicus/JRC, « EFFIS Data and services »,
    https://forest-fire.emergency.copernicus.eu/applications/data-and-services
12. data.gouv.fr, « DRIAS - projections climatiques »,
    https://www.data.gouv.fr/datasets/drias-projections-climatiques-pour-ladaptation-de-nos-societes
13. GeoSAS, « Les données Météo France libérées »,
    https://geosas.fr/web/?p=6306

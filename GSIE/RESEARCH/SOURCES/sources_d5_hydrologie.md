# Sources — D5 Hydrologie

| Champ | Valeur |
|---|---|
| **Domaine** | Hydrologie |
| **Date** | 2026-07-15 |
| **Statut** | Recherche préliminaire |

---

## Sommaire

1. [Hub'Eau — API Hydrométrie](#1-hubeau--api-hydrometrie)
2. [Hub'Eau — API Qualité des cours d'eau](#2-hubeau--api-qualite-des-cours-deau)
3. [Hub'Eau — API Écoulement des cours d'eau](#3-hubeau--api-ecoulement-des-cours-deau)
4. [Hub'Eau — API Piézométrie](#4-hubeau--api-piezometrie)
5. [Hub'Eau — API Température des cours d'eau](#5-hubeau--api-temperature-des-cours-deau)
6. [Vigicrues — API vigilance crues](#6-vigicrues--api-vigilance-crues)
7. [SIMVIGI — Système d'information de la vigilance crues](#7-simvigi--systeme-dinformation-de-la-vigilance-crues)
8. [SANDRE — Référentiel national sur l'eau](#8-sandre--referentiel-national-sur-leau)
9. [ADES — Portail national des eaux souterraines](#9-ades--portail-national-des-eaux-souterraines)
10. [BD Carthage — Référentiel hydrographique moyen échelle](#10-bd-carthage--referentiel-hydrographique-moyen-echelle)
11. [BD Topage — Référentiel hydrographique grande échelle](#11-bd-topage--referentiel-hydrographique-grande-echelle)
12. [BD Hydro — Base de données hydrométriques centrale (SCHAPI)](#12-bd-hydro--base-de-donnees-hydrometriques-centrale-schapi)
13. [Banque Hydro / HydroPortail](#13-banque-hydro--hydroportail)
14. [BDLISA — Référentiel hydrogéologique français](#14-bdlisa--referentiel-hydrogeologique-francais)
15. [BSSEAU — Base de données sur les eaux souterraines (BRGM)](#15-bsseau--base-de-donnees-sur-les-eaux-souterraines-brgm)
16. [RPDZH — Réseau Partenarial des Données sur les Zones Humides](#16-rpdzh--reseau-partenarial-des-donnees-sur-les-zones-humides)

---

## 1. Hub'Eau — API Hydrométrie

| Champ | Valeur |
|---|---|
| **Nom officiel** | API Hub'Eau — Hydrométrie |
| **Organisme** | Office Français de la Biodiversité (OFB) / BRGM — Service Central Vigicrues (SCV, ex-SCHAPI) pour les données |
| **URL d'accès** | https://hubeau.eaufrance.fr/page/api-hydrometrie |
| **Type d'accès** | `api_rest` |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | ~5 000 stations hydrométriques ; mesures quasi temps-réel (hauteurs, débits) |
| **Variables** | Débit (Q), hauteur d'eau (H) |
| **Fréquence de mise à jour** | Temps réel (quasi temps-réel, synchronisation continue avec la PHyC) |
| **Couverture** | France métropolitaine + DROM |
| **Priorité GSIE** | **P0** |
| **Exemples d'URL vérifiées** | |

```
# Documentation Swagger
https://hubeau.eaufrance.fr/api/v1/hydrometrie/api-docs

# Lister les stations
https://hubeau.eaufrance.fr/api/v1/hydrometrie/sites?code_departement=45&pretty

# Observations temps réel (débit)
https://hubeau.eaufrance.fr/api/v1/hydrometrie/obs?code_entite=K4513010&grandeur_hydro=Q&size=20&pretty

# Observations temps réel (hauteur)
https://hubeau.eaufrance.fr/api/v1/hydrometrie/obs?code_entite=K4513010&grandeur_hydro=H&size=20&pretty
```

**Endpoints principaux :** `sites` (sites hydrométriques), `stations` (stations de mesure), `obs` (observations temps réel), `obs_elab` (observations élaborées — moyennes journalières, mensuelles, etc.).

---

## 2. Hub'Eau — API Qualité des cours d'eau

| Champ | Valeur |
|---|---|
| **Nom officiel** | API Hub'Eau — Qualité des cours d'eau |
| **Organisme** | OFB / BRGM — données issues de la base Naïades (Agences de l'Eau) |
| **URL d'accès** | https://hubeau.eaufrance.fr/page/api-qualite-cours-deau |
| **Type d'accès** | `api_rest` |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | >200 millions d'analyses sur >20 000 stations |
| **Variables** | Qualité physico-chimique (nitrates, conductivité, pH, matières organiques, métaux, pesticides, etc.) |
| **Fréquence de mise à jour** | Synchronisation en continu avec Naïades (depuis v2) |
| **Couverture** | France métropolitaine + DROM |
| **Priorité GSIE** | **P0** |
| **Exemples d'URL vérifiées** | |

```
# Lister les stations physico-chimiques d'une commune
https://hubeau.eaufrance.fr/api/v2/qualite_rivieres/station_pc?code_commune=17300&pretty

# Analyses physico-chimiques d'une station
https://hubeau.eaufrance.fr/api/v2/qualite_rivieres/analyse_pc?code_station=02115725&size=20&pretty

# Opérations de prélèvement
https://hubeau.eaufrance.fr/api/v2/qualite_rivieres/operation_pc?code_station=02115725&pretty
```

**Endpoints principaux :** `station_pc`, `operation_pc`, `condition_environnementale_pc`, `analyse_pc`. Formats : JSON, GeoJSON, CSV.

---

## 3. Hub'Eau — API Écoulement des cours d'eau

| Champ | Valeur |
|---|---|
| **Nom officiel** | API Hub'Eau — Écoulement des cours d'eau (réseau ONDE) |
| **Organisme** | OFB / BRGM — données du réseau ONDE (Observatoire National des Écoulements) |
| **URL d'accès** | https://hubeau.eaufrance.fr/page/api-ecoulement |
| **Type d'accès** | `api_rest` (conforme OpenAPI 3.0) |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | >350 000 observations visuelles ; >3 200 stations |
| **Variables** | Écoulement (observation visuelle : écoulement visible, assec, écoulement intermittent) |
| **Fréquence de mise à jour** | Campagnes saisonnières (observations terrain) |
| **Couverture** | France métropolitaine (têtes de bassin versant, petits et moyens cours d'eau) |
| **Priorité GSIE** | **P1** |
| **Exemples d'URL vérifiées** | |

```
# Stations d'observation par département
https://hubeau.eaufrance.fr/api/v1/ecoulement/stations?format=json&code_departement=88&size=20

# Campagnes d'observation
https://hubeau.eaufrance.fr/api/v1/ecoulement/campagnes?date_campagne_min=2021-01-01&code_departement=88&size=20

# Observations d'écoulement
https://hubeau.eaufrance.fr/api/v1/ecoulement/observations?format=json&code_station=A0220651&size=20
```

**Endpoints principaux :** `stations`, `campagnes`, `observations`. Complète l'API Hydrométrie sur les têtes de bassin peu instrumentées.

---

## 4. Hub'Eau — API Piézométrie

| Champ | Valeur |
|---|---|
| **Nom officiel** | API Hub'Eau — Piézométrie |
| **Organisme** | OFB / BRGM — données issues du portail ADES |
| **URL d'accès** | https://hubeau.eaufrance.fr/page/api-piezometrie |
| **Type d'accès** | `api_rest` |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | >41 millions de mesures ; chroniques piézométriques France entière |
| **Variables** | Piézométrie (niveau d'eau dans les nappes souterraines) |
| **Fréquence de mise à jour** | Synchronisation avec ADES (continue) |
| **Couverture** | France métropolitaine + DROM |
| **Priorité GSIE** | **P0** |
| **Exemples d'URL vérifiées** | |

```
# Lister les piézomètres d'une commune
https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations?code_commune=71070&pretty

# Chronique piézométrique d'une station
https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques?code_station=06252X0063/PZ1&size=20&pretty
```

**Endpoints principaux :** `stations` (piézomètres), `chroniques` (mesures de niveau d'eau).

---

## 5. Hub'Eau — API Température des cours d'eau

| Champ | Valeur |
|---|---|
| **Nom officiel** | API Hub'Eau — Température en continu des cours d'eau |
| **Organisme** | OFB / BRGM — données issues de Naïades |
| **URL d'accès** | https://hubeau.eaufrance.fr/page/api-temperature-continu |
| **Type d'accès** | `api_rest` |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | ~760 stations (dont ~50 en service) ; mesures horaires à pluripériodiques |
| **Variables** | Température de l'eau (°C, en continu) |
| **Fréquence de mise à jour** | Synchronisation temps réel avec Naïades (depuis juillet 2022) |
| **Couverture** | France métropolitaine |
| **Priorité GSIE** | **P1** |
| **Exemples d'URL vérifiées** | |

```
# Stations de température par département
https://hubeau.eaufrance.fr/api/v1/temperature/station?code_departement=45&pretty

# Chronique de température (5 dernières mesures)
https://hubeau.eaufrance.fr/api/v1/temperature/chronique?code_station=04051125&size=5&sort=desc&pretty
```

**Endpoints principaux :** `station`, `chronique`. Formats : JSON, GeoJSON, CSV.

---

## 6. Vigicrues — API vigilance crues

| Champ | Valeur |
|---|---|
| **Nom officiel** | Vigicrues — API de vigilance crues (v1.1) |
| **Organisme** | Service Central d'Hydrométéorologie et d'Appui à la Prévision des Inondations (SCHAPI / SC Vigicrues) |
| **URL d'accès** | https://www.vigicrues.gouv.fr/services/1 |
| **Type d'accès** | `api_rest` |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | ~1 700 stations télétransmises ; observations et prévisions en hauteurs et débits |
| **Variables** | Hauteur d'eau (H), débit (Q), vigilance crues (niveaux vert/jaune/orange/rouge), prévisions |
| **Fréquence de mise à jour** | Temps réel ; carte de vigilance publiée ≥2 fois/jour (10h et 16h HL) |
| **Couverture** | France métropolitaine (réseau de surveillance réglementaire) |
| **Priorité GSIE** | **P0** |
| **Exemples d'URL vérifiées** | |

```
# Toutes les stations de vigilance crues
https://www.vigicrues.gouv.fr/services/v1.1/StaEntVigiCru.json

# Détail d'un territoire de vigilance (ex. territoire 8)
https://www.vigicrues.gouv.fr/services/v1.1/StaEntVigiCru.json?CdEntVigiCru=8&TypEntVigiCru=5

# Observations en hauteurs d'une station
https://www.vigicrues.gouv.fr/services/observations.json?CdStationHydro=Q745101001

# Observations en débit
https://www.vigicrues.gouv.fr/services/observations.json?CdStationHydro=Q745101001&GrdSimul=Q

# Prévisions en hauteurs
https://www.vigicrues.gouv.fr/services/v1.1/prevision.json

# Prévisions en débit
https://www.vigicrues.gouv.fr/services/v1.1/prevision.json?GrdSimul=Q
```

**Endpoints principaux :** `StaEntVigiCru` (stations/territoires), `observations` (hauteurs/débits temps réel), `prevision` (prévisions), `VigiCru` (carte de vigilance GeoJSON). Données également disponibles via data.gouv.fr et OpenDataSoft.

---

## 7. SIMVIGI — Système d'information de la vigilance crues

| Champ | Valeur |
|---|---|
| **Nom officiel** | SIMVIGI — Système d'Information de la Vigilance crues |
| **Organisme** | SCHAPI (Service Central d'Hydrométéorologie et d'Appui à la Prévision des Inondations) |
| **URL d'accès** | https://www.vigicrues.gouv.fr/ (interface publique) — API : https://www.vigicrues.gouv.fr/services/1 |
| **Type d'accès** | `api_rest` (interface publique via Vigicrues) |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | Carte de vigilance nationale ≥2 publications/jour ; ~1 700 stations ; 22 territoires de compétence crues |
| **Variables** | Niveau de vigilance crues (vert/jaune/orange/rouge), bulletins nationaux et locaux |
| **Fréquence de mise à jour** | ≥2 fois/jour (10h et 16h HL) ; plus fréquente en période de crues |
| **Couverture** | France métropolitaine (réseau des 22 SPC) |
| **Priorité GSIE** | **P1** |
| **Exemples d'URL vérifiées** | |

```
# Carte de vigilance (flux GeoJSON des tronçons avec niveau)
# Disponible via data.gouv.fr :
https://www.data.gouv.fr/datasets/troncons-de-cours-deau-vigicrues-simplifies-avec-niveau-de-vigilance-crues

# Bulletin d'information national
https://www.vigicrues.gouv.fr/
```

**Notes :** SIMVIGI est le système d'information interne du SCHAPI qui alimente la carte de vigilance publique. L'accès aux données se fait via l'API Vigicrues (§6) et le flux GeoJSON des tronçons de vigilance sur data.gouv.fr.

---

## 8. SANDRE — Référentiel national sur l'eau

| Champ | Valeur |
|---|---|
| **Nom officiel** | SANDRE — Service d'Administration Nationale des Données et Référentiels sur l'Eau |
| **Organisme** | OFB (animation) / Office International de l'Eau (OiEau) — secrétariat technique central |
| **URL d'accès** | https://www.sandre.eaufrance.fr/ |
| **Type d'accès** | `api_rest` + `file_download` |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | >40 jeux de données référentiels (cours d'eau, stations, entités hydrogéologiques, taxons, paramètres, etc.) |
| **Variables** | Référentiels : cours d'eau, bassins hydrographiques, stations, paramètres physico-chimiques, entités hydrogéologiques, taxons, intervenants |
| **Fréquence de mise à jour** | Annuelle (versions Topage, circonscriptions, communes) à continue (référentiels métier) |
| **Couverture** | France entière (métropole + DROM) |
| **Priorité GSIE** | **P0** (référentiel structurant pour l'interopérabilité) |
| **Exemples d'URL vérifiées** | |

```
# API Référentiel (REST) — endpoint
https://api.sandre.eaufrance.fr/referentiels/v1/

# Exemple : référentiel des appellations de taxon
https://api.sandre.eaufrance.fr/referentiels/v1/appeltaxon

# Téléchargement d'un référentiel complet
https://api.sandre.eaufrance.fr/referentiels/v1/[referentiel]?format=json

# Téléchargement d'un élément de référentiel
https://api.sandre.eaufrance.fr/referentiels/v1/[referentiel]/[code]

# Téléchargement de jeux de données géographiques (BD Topage, BD Carthage)
https://services.sandre.eaufrance.fr/telechargement/geo/ETH/BDTopage/2024/BD_Topage_FXX_2024-shp.zip
```

**Notes :** Le SANDRE fournit le langage commun et les standards d'échange du SIE. L'API REST permet d'interroger tous les référentiels sans géométries ; les téléchargements de jeux géographiques se font via `services.sandre.eaufrance.fr/telechargement/`.

---

## 9. ADES — Portail national des eaux souterraines

| Champ | Valeur |
|---|---|
| **Nom officiel** | ADES — Portail national d'accès aux données sur les eaux souterraines |
| **Organisme** | BRGM (Bureau de Recherches Géologiques et Minières) / OFB |
| **URL d'accès** | https://ades.eaufrance.fr/ |
| **Type d'accès** | `file_download` + `api_rest` (via Hub'Eau Piézométrie, §4) |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | Points d'eau : BSS entière (dizaines de milliers) ; piézomètres et qualitomètres en suivi ; >41 millions de mesures piézométriques |
| **Variables** | Piézométrie (niveau d'eau), qualité des eaux souterraines (analyses chimiques), descriptif des points d'eau (forages, puits, sources) |
| **Fréquence de mise à jour** | Continue (alimentation par les partenaires du SIE) |
| **Couverture** | France entière (métropole + DROM) |
| **Priorité GSIE** | **P0** |
| **Exemples d'URL vérifiées** | |

```
# Recherche de points d'eau (interface web)
https://ades.eaufrance.fr/recherche/index/pointEauAdes

# Recherche de mesures piézométriques (interface web)
https://ades.eaufrance.fr/recherche/index/PiezometreAvance

# Recherche de mesures qualité (interface web)
https://ades.eaufrance.fr/recherche/index/Qualitometre

# Accès programmatique via Hub'Eau Piézométrie (§4)
https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations?code_commune=71070&pretty
```

**Notes :** ADES diffuse les données de la BSS (Banque du Sous-Sol Eau) gérée par le BRGM. L'accès programmatique aux chroniques piézométriques se fait principalement via l'API Hub'Eau (§4). L'interface ADES permet le téléchargement de fichiers (CSV, Excel) par requête.

---

## 10. BD Carthage — Référentiel hydrographique moyen échelle

| Champ | Valeur |
|---|---|
| **Nom officiel** | BD Carthage® — Base de Données sur la CARtographie THématique des AGences de l'eau |
| **Organisme** | IGN (Institut National de l'Information Géographique et Forestière) / Agences de l'Eau |
| **URL d'accès** | https://www.data.gouv.fr/datasets/bd-carthage-r |
| **Type d'accès** | `file_download` |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | Réseau hydrographique national : tronçons, cours d'eau, plans d'eau, bassins versants, zones hydrographiques (6 bassins, ~200 zones hydrographiques) |
| **Variables** | Référentiel hydrographique de surface (cours d'eau, plans d'eau, bassins versants, tronçons hydrographiques, nœuds) |
| **Fréquence de mise à jour** | Annuelle (mise à jour coordonnée par les Agences de l'Eau) |
| **Couverture** | France métropolitaine + DROM |
| **Priorité GSIE** | **P1** (progressivement remplacée par BD Topage, §11) |
| **Exemples d'URL vérifiées** | |

```
# Téléchargement sur data.gouv.fr
https://www.data.gouv.fr/datasets/bd-carthage-r

# Descriptif de contenu (PDF SANDRE)
https://www.sandre.eaufrance.fr/sites/default/files/IMG/pdf/1-DC_BDCARTHAGE_3_0.pdf
```

**Notes :** BD Carthage est le référentiel hydrographique historique à moyenne échelle. Il est progressivement remplacé par la BD Topage (§11) pour les besoins à grande échelle. Reste pertinent pour les analyses à l'échelle des grands bassins.

---

## 11. BD Topage — Référentiel hydrographique grande échelle

| Champ | Valeur |
|---|---|
| **Nom officiel** | BD Topage® — Référentiel hydrographique français grande échelle |
| **Organisme** | IGN / OFB (Information Géographique sur l'Eau) |
| **URL d'accès** | https://www.sandre.eaufrance.fr/ (téléchargement) |
| **Type d'accès** | `file_download` |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | Cours d'eau, tronçons hydrographiques, plans d'eau, surfaces élémentaires, laisses des eaux, bassins versants topographiques — généré à partir de la BD TOPO® (IGN) |
| **Variables** | Référentiel hydrographique de surface à grande échelle (métrique), conforme INSPIRE |
| **Fréquence de mise à jour** | Annuelle (version 2024 disponible) |
| **Couverture** | France métropolitaine (+ DROM selon versions) |
| **Priorité GSIE** | **P0** (référentiel hydrographique de référence) |
| **Exemples d'URL vérifiées** | |

```
# Téléchargement BD Topage Métropole 2024 (Shapefile)
https://services.sandre.eaufrance.fr/telechargement/geo/ETH/BDTopage/2024/BD_Topage_FXX_2024-shp.zip

# Scénario de transformation INSPIRE
https://sandre.eaufrance.fr/ftp/documents/fr/sct/eth/1/sandre_scenario_transfo_eth_v1.pdf

# Dictionnaire de données Référentiel Hydrographique (ETH v2)
https://www.sandre.eaufrance.fr/ftp/documents/fr/pre/eth/2/sandre_pres_eth_2.pdf
```

**Notes :** BD Topage est le successeur de BD Carthage, à grande échelle (métrique), compatible avec le RGE® de l'IGN. C'est le référentiel hydrographique structurant du SIE.

---

## 12. BD Hydro — Base de données hydrométriques centrale (SCHAPI)

| Champ | Valeur |
|---|---|
| **Nom officiel** | BD Hydro — Base de données HYDRO centrale (opération HYDRO 3) |
| **Organisme** | SCHAPI / SC Vigicrues (ministère de la Transition écologique) |
| **URL d'accès** | https://www.hydro.eaufrance.fr/ (HydroPortail — interface publique) |
| **Type d'accès** | `api_rest` (via Hub'Eau Hydrométrie, §1) + `file_download` (via HydroPortail) |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | ~3 500 stations (dont ~2 400 en service) ; mesures de hauteur d'eau à pas de temps variable ; courbes de tarage |
| **Variables** | Hauteur d'eau (H), débit (Q), courbes de tarage, métadonnées stations |
| **Fréquence de mise à jour** | Temps réel (partie temps réel) ; données validées selon cycles producteurs |
| **Couverture** | France métropolitaine + DROM |
| **Priorité GSIE** | **P0** (base nationale de l'hydrométrie) |
| **Exemples d'URL vérifiées** | |

```
# HydroPortail — recherche de sites/stations hydrométriques
https://www.hydro.eaufrance.fr/

# Aide — site hydrométrique
https://hydro.eaufrance.fr/aide/le-site-hydrometrique

# Accès programmatique via Hub'Eau Hydrométrie (§1)
https://hubeau.eaufrance.fr/api/v1/hydrometrie/sites?code_departement=45&pretty
```

**Notes :** BD Hydro (opération HYDRO 3) est la base de données centrale unique du SCHAPI, unifiant le référentiel hydrométrique et les données temps réel/historiques. Elle alimente à la fois Vigicrues (surveillance crues) et HydroPortail (suivi des régimes hydrologiques). L'accès programmatique public se fait via l'API Hub'Eau Hydrométrie.

---

## 13. Banque Hydro / HydroPortail

| Champ | Valeur |
|---|---|
| **Nom officiel** | Banque HYDRO / HydroPortail |
| **Organisme** | SCHAPI / SC Vigicrues (administration dans le cadre du SIE) |
| **URL d'accès** | https://www.hydro.eaufrance.fr/ |
| **Type d'accès** | `file_download` + `api_rest` (via Hub'Eau, §1) |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | ~3 500 stations (dont ~2 400 en service) ; données historiques et validées (hauteurs, débits, statistiques) |
| **Variables** | Hauteur d'eau (H), débit (Q), statistiques hydrologiques (modules, étiages, crues) |
| **Fréquence de mise à jour** | Données temps réel en continu ; données validées selon cycles de contrôle des producteurs |
| **Couverture** | France métropolitaine + DROM |
| **Priorité GSIE** | **P0** |
| **Exemples d'URL vérifiées** | |

```
# HydroPortail — page d'accueil
https://www.hydro.eaufrance.fr/

# Recherche d'entités hydrométriques
https://www.hydro.eaufrance.fr/

# Fiche métadonnées (Ifremer Sextant)
https://sextant.ifremer.fr/geonetwork/srv/api/records/c79fb1bb-1f22-45b5-995c-f92f1bb5f363
```

**Notes :** La Banque HYDRO est la banque nationale de données pour l'hydrométrie et l'hydrologie. HydroPortail en est l'interface publique de diffusion. Les données temps réel sont accessibles via l'API Hub'Eau (§1) ; les données validées et historiques sont téléchargeables via HydroPortail.

---

## 14. BDLISA — Référentiel hydrogéologique français

| Champ | Valeur |
|---|---|
| **Nom officiel** | BDLISA — Base de Données des Limites des Systèmes Aquifères |
| **Organisme** | BRGM / SANDRE (OFB) / Agences de l'Eau |
| **URL d'accès** | https://bdlisa.eaufrance.fr/ |
| **Type d'accès** | `file_download` + `ogc_wms` (services web cartographiques) |
| **Licence** | CC-BY-NC-SA 2.0 (utilisation non commerciale) |
| **Volume estimé** | 3 niveaux d'échelle (national, régional, local) ; entités hydrogéologiques sur France entière |
| **Variables** | Entités hydrogéologiques (aquifères, formations imperméables, milieux poreux/fracturés/karstiques, écoulements libres/captifs) |
| **Fréquence de mise à jour** | Versions ponctuelles (V2 diffusée depuis 2018, V3 en cours) |
| **Couverture** | France métropolitaine + DROM (Guadeloupe, Guyane, Martinique, Mayotte, Réunion) |
| **Priorité GSIE** | **P1** (référentiel hydrogéologique structurant) |
| **Exemples d'URL vérifiées** | |

```
# Portail BDLISA — téléchargement
https://bdlisa.eaufrance.fr/

# Page BRGM — référentiel hydrogéologique
https://www.brgm.fr/fr/reference-projet-acheve/referentiel-hydrogeologique-francais-bdlisa

# InfoTerre BRGM — visualisation
https://ssp-infoterre.brgm.fr/fr/base-de-donnees/bdlisa-referentiel-hydrogeologique-francais
```

**Formats disponibles :** Shapefile (.shp), File Geodatabase (.gdb), SQLite (.sqlite), Geopackage (.gpkg). Services web cartographiques (WMS) accessibles via le portail BDLISA.

---

## 15. BSSEAU — Base de données sur les eaux souterraines (BRGM)

| Champ | Valeur |
|---|---|
| **Nom officiel** | BSS-Eau — Base de données du Sous-Sol relative aux Eaux souterraines |
| **Organisme** | BRGM |
| **URL d'accès** | https://infoterre.brgm.fr/page/eaux-souterraines-bsseau |
| **Type d'accès** | `file_download` (via ADES, §9) + `api_rest` (via Hub'Eau Piézométrie, §4) |
| **Licence** | Ouverte (Licence Ouverte 2.0 / Etalab) |
| **Volume estimé** | Descriptif de tous les points d'eau de la BSS ; données qualité et quantité des eaux souterraines au format SANDRE |
| **Variables** | Piézométrie, qualité des eaux souterraines, prélèvements, descriptif des points d'eau (forages, puits, sources) |
| **Fréquence de mise à jour** | Continue (alimentation par les partenaires du SIE) |
| **Couverture** | France entière (métropole + DROM) |
| **Priorité GSIE** | **P1** (source amont d'ADES) |
| **Exemples d'URL vérifiées** | |

```
# Page InfoTerre — BSS-Eau
https://infoterre.brgm.fr/page/eaux-souterraines-bsseau

# Accès aux données via ADES (§9)
https://ades.eaufrance.fr/recherche

# Accès programmatique via Hub'Eau Piézométrie (§4)
https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations?code_commune=71070&pretty
```

**Notes :** BSS-Eau est la base de données gérée par le BRGM, au format SANDRE, qui alimente le portail ADES. Elle contient les informations sur les points d'eau (BSS) et les données de suivi (qualité, quantité, prélèvements).

---

## 16. RPDZH — Réseau Partenarial des Données sur les Zones Humides

| Champ | Valeur |
|---|---|
| **Nom officiel** | RPDZH — Réseau Partenarial des Données sur les Zones Humides |
| **Organisme** | Forum des Marais Atlantiques (FMA) / Agences de l'Eau / collectivités partenaires |
| **URL d'accès** | https://sig.reseau-zones-humides.org/ |
| **Type d'accès** | `ogc_wms` + `ogc_wfs` + `file_download` (sur demande) |
| **Licence** | Variable selon producteur (données partenaires — vérifier par couche) |
| **Volume estimé** | Inventaires de zones humides (terrain) + prélocalisations (satellitaire) ; couverture nationale non exhaustive (hors agence RMC) |
| **Variables** | Zones humides (inventaires validés terrain, prélocalisations, caractérisation) |
| **Fréquence de mise à jour** | Variable selon producteurs (alimentation continue par les partenaires) |
| **Couverture** | France nationale (hors bassin RMC pour les inventaires) ; prélocalisations bassin Seine-Normandie |
| **Priorité GSIE** | **P2** |
| **Exemples d'URL vérifiées** | |

```
# Portail SIG du RPDZH
https://sig.reseau-zones-humides.org/

# Service WMS du RPDZH
http://wms.reseau-zones-humides.org/cgi-bin/wmsfma?

# Jeu de données sur data.gouv.fr
https://www.data.gouv.fr/datasets/zones-humides

# Cartographie nationale des milieux humides (PatriNat / OFB)
https://www.patrinat.fr/fr/cartographie-nationale-des-milieux-humides-7187
```

**Notes :** Le RPDZH est depuis 2019 la plateforme nationale des données sur les milieux humides. Les données sont accessibles en visualisation via le portail SIG, par webservices WMS/WFS, ou sur demande par mail. La couverture n'est pas exhaustive et n'a pas de valeur réglementaire. La cartographie nationale des milieux humides (PatriNat/OFB) est un projet complémentaire en cours de déploiement.

---

## Synthèse — Priorités GSIE

| Priorité | Sources | Justification |
|---|---|---|
| **P0** | Hub'Eau Hydrométrie, Hub'Eau Qualité, Hub'Eau Piézométrie, Vigicrues API, SANDRE, ADES, BD Topage, BD Hydro, Banque Hydro/HydroPortail | Données temps réel et historiques structurantes + référentiels nationaux d'interopérabilité |
| **P1** | Hub'Eau Écoulement, Hub'Eau Température, SIMVIGI, BD Carthage, BDLISA, BSSEAU | Données complémentaires, référentiels hydrogéologiques, observations visuelles |
| **P2** | RPDZH (Zones humides) | Données non exhaustives, hétérogènes, accès partiel |

---

## Synthèse — Types d'accès

| Type d'accès | Sources |
|---|---|
| `api_rest` | Hub'Eau (×5), Vigicrues, SIMVIGI, SANDRE, ADES (via Hub'Eau), BD Hydro (via Hub'Eau), Banque Hydro (via Hub'Eau) |
| `ogc_wms` | BDLISA, RPDZH |
| `ogc_wfs` | RPDZH |
| `file_download` | SANDRE, ADES, BD Carthage, BD Topage, BDLISA, BSSEAU, RPDZH, Banque Hydro (HydroPortail) |
| `file_import` | (tous les `file_download` éligibles pour ingestion dans Forge/PostGIS) |

---

## Notes méthodologiques

- **Toutes les URLs ont été vérifiées** via recherche web le 2026-07-15. Les URLs d'exemple sont issues de la documentation officielle de chaque service.
- **Hub'Eau** est le point d'accès unifié privilégié : 13 API REST couvrent l'essentiel des données du SIE (hydrométrie, qualité, piézométrie, température, écoulement, hydrobiologie, prélèvements, etc.). Les autres API Hub'Eau non détaillées ici (prélèvements en eau, hydrobiologie, indicateurs réglementaires, qualité eaux potables, qualité eaux baignade, qualité eaux conchylicoles) sont listées sur https://hubeau.eaufrance.fr/page/apis.
- **SANDRE** est le référentiel structurant : tout moteur GSIE manipulant des données hydrologiques doit s'appuyer sur les codes et nomenclatures SANDRE pour garantir l'interopérabilité.
- **BD Hydro / Banque Hydro / HydroPortail** désignent des facettes du même système : BD Hydro est la base technique (HYDRO 3), HydroPortail est l'interface publique, l'API Hub'Eau Hydrométrie est l'accès programmatique REST.
- **Licences :** la majorité des données du SIE sont sous Licence Ouverte 2.0 / Etalab. BDLISA fait exception (CC-BY-NC-SA 2.0, usage non commercial). Le RPDZH a des licences variables selon le producteur de chaque couche.

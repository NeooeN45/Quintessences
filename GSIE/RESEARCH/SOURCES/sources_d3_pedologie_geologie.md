# Sources — D3 Pédologie + Géologie

| Champ | Valeur |
|---|---|
| **Domaine** | Pédologie + Géologie |
| **Date** | 2026-07-15 |
| **Statut** | Recherche préliminaire |

---

## 1. Référentiel Pédologique Français (RPF)

| Champ | Valeur |
|---|---|
| **Nom officiel** | Référentiel Pédologique Français (RPF) |
| **Organisme** | AFES (Association Française pour l'Étude du Sol) / INRAE |
| **URL d'accès** | https://www.afes.fr/les-sols/referentiel-pedologique/ |
| **Type d'accès** | `publication_text`, `knowledge_extraction` |
| **Licence** | Copyright AFES / INRAE (ouvrage de référence, pas de licence ouverte explicite) |
| **Volume estimé** | Référentiel textuel — classification hiérarchique des sols de France (sols de référence, horizons de référence, attributs). Document de référence (~300 pages) |
| **Variables** | Horizons pédologiques, types de sols (Rédoxisol, Brunisol, Luviosol, etc.), attributs morphologiques, drainage, nature de l'enroûtement, profondeur |
| **Fréquence de mise à jour** | Révisions ponctuelles (éditions 1995, 2008, 2009). Pas de mise à jour régulière programmée |
| **Couverture** | France métropolitaine et DOM |
| **Priorité GSIE** | **P0** — référentiel sémantique de base pour la classification des sols français |
| **Exemples d'URL vérifiées** | https://www.afes.fr/les-sols/referentiel-pedologique/ — https://hal.inrae.fr/hal-02797907/document — https://belinrae.inrae.fr/index.php?lvl=notice_display&id=210173 |

---

## 2. World Reference Base for Soil Resources (WRB)

| Champ | Valeur |
|---|---|
| **Nom officiel** | World Reference Base for Soil Resources (WRB) — 4ᵉ édition 2022 |
| **Organisme** | IUSS (International Union of Soil Sciences) Working Group WRB / FAO / ISRIC |
| **URL d'accès** | https://wrb.isric.org/ |
| **Type d'accès** | `publication_text`, `file_download` |
| **Licence** | CC-BY (document FAO/IUSS — usage libre avec attribution) |
| **Volume estimé** | Document de référence ~250 pages (4ᵉ édition 2022). 32 Reference Soil Groups (RSG), ~200 qualifiers |
| **Variables** | Reference Soil Groups (RSG), qualifiers (qualificatifs), horizons diagnostiques, propriétés diagnostiques, matériaux diagnostiques |
| **Fréquence de mise à jour** | Éditions : 1998, 2006, 2015, 2022. Cycle ~7 ans |
| **Couverture** | Mondiale |
| **Priorité GSIE** | **P0** — standard international de classification des sols, pivot de correspondance RPF ↔ WRB ↔ SoilTaxonomy |
| **Exemples d'URL vérifiées** | https://wrb.isric.org/ — https://isric.org/explore/wrb — https://www.fao.org/soils-portal/data-hub/soil-classification/world-reference-base/en/ — https://files.isric.org/public/documents/WRB_fourth_edition_2022-12-18.pdf |

---

## 3. SoilGrids 2.0 (ISRIC)

| Champ | Valeur |
|---|---|
| **Nom officiel** | SoilGrids 2.0 — Global gridded soil information |
| **Organisme** | ISRIC — World Soil Information |
| **URL d'accès** | https://soilgrids.org/ |
| **Type d'accès** | `file_download` (WebDAV VRT), `api_rest` (GraphQL), `ogc_wms` (visualisation) |
| **Licence** | CC-BY 4.0 |
| **Volume estimé** | Raster global à 250 m de résolution. 8 profondeurs standard (0-5, 5-15, 15-30, 30-60, 60-100, 100-200 cm). ~7 variables principales × 8 profondeurs × 3 statistiques (mean, median, quantile) ≈ plusieurs centaines de couches GeoTIFF. Disponible aussi sur Google Earth Engine |
| **Variables** | pH (eau), texture (sable, limon, argile), carbone organique du sol (SOC), densité apparente (bulk density), CEC (capacité d'échange cationique), profondeur du sol (soil depth), classification WRB (probabilités par RSG) |
| **Fréquence de mise à jour** | Version 2.0 publiée 2021. Pas de cycle régulier annoncé — mises à jour liées aux nouvelles versions de WoSIS |
| **Couverture** | Mondiale (résolution 250 m) |
| **Priorité GSIE** | **P0** — couverture mondiale des propriétés du sol, source primaire pour les couches raster pédologiques |
| **Exemples d'URL vérifiées** | https://soilgrids.org/ — https://isric.org/explore/soilgrids — https://docs.isric.org/globaldata/soilgrids/ — https://github.com/gantian127/soilgrids (librairie Python) |

---

## 4. WoSIS — World Soil Information Service (ISRIC)

| Champ | Valeur |
|---|---|
| **Nom officiel** | WoSIS (World Soil Information Service) — Standardised soil profile database |
| **Organisme** | ISRIC — World Soil Information (WDC-Soils) |
| **URL d'accès** | https://docs.isric.org/globaldata/wosis/ |
| **Type d'accès** | `ogc_wfs` (WoSIS_latest dynamique), `file_download` (snapshots TSV avec DOI) |
| **Licence** | Variable selon data provider — principalement CC-BY et CC-BY-NC |
| **Volume estimé** | Snapshot décembre 2023 : 228 000 profils, 217 000 sites, 174 pays, 900 000 couches/horizons, 6 millions d'enregistrements |
| **Variables** | pH, carbone organique, azote total, densité apparente, texture (sable/limon/argile), CEC, bases échangeables, conductivité électrique, profondeur, description d'horizons |
| **Fréquence de mise à jour** | WoSIS_latest = dynamique (continu). Snapshots statiques avec DOI (~annuel) |
| **Couverture** | Mondiale (174 pays) |
| **Priorité GSIE** | **P0** — base de données de profils de sol la plus complète au monde, source d'observations pour calibration/validation |
| **Exemples d'URL vérifiées** | https://docs.isric.org/globaldata/wosis/ — http://maps.isric.org/mapserv?map=/map/wosis_latest.map (WFS) — https://files.isric.org/public/wosis_snapshot/WoSIS_2023_December.zip — https://doi.org/10.17027/isric-wdcsoils-20231130 |

---

## 5. InfoTerre / Géoservices OGC (BRGM)

| Champ | Valeur |
|---|---|
| **Nom officiel** | InfoTerre — portail d'accès aux données géoscientifiques du BRGM |
| **Organisme** | BRGM (Bureau de Recherches Géologiques et Minières) |
| **URL d'accès** | https://infoterre.brgm.fr/ |
| **Type d'accès** | `file_download` (cartes géologiques shapefile), `ogc_wms` (visualisation), `ogc_wfs` (téléchargement GML) |
| **Licence** | Open data — conditions d'utilisation BRGM (réutilisation libre avec attribution, dans le cadre du Plan national pour la science ouverte) |
| **Volume estimé** | Cartes géologiques à 1/50 000 (Bd Charm-50) : 1063 feuilles vectorisées et harmonisées, 6 couches d'information par feuille. Carte à 1/1 000 000 (Bd Million-Géol) : 6 couches France entière. Banque du Sous-Sol (BSS) : ~700 000 ouvrages, logs géologiques. Cavités souterraines, eaux souterraines, risques naturels |
| **Variables** | Formations géologiques (lithologie, âge, stratigraphie), failles, points remarquables, isobathes, structures magmatiques/métamorphiques, ensembles lithologiques, forages BSS (logs, coupures), nappes souterraines |
| **Fréquence de mise à jour** | Continue — harmonisation des cartes 1/50 000 en cours. Bd Charm-50 enrichie régulièrement |
| **Couverture** | France métropolitaine + DROM |
| **Priorité GSIE** | **P0** — source nationale de référence pour le substrat géologique, indispensable au moteur Pedology (sol = géologie + pédogenèse) |
| **Exemples d'URL vérifiées** | https://infoterre.brgm.fr/ — https://infoterre.brgm.fr/page/telechargement-cartes-geologiques — https://infoterre.brgm.fr/formulaire/telechargement-cartes-geologiques-departementales-150-000-bd-charm-50 — https://infoterre.brgm.fr/formulaire/telechargement-carte-geologique-metropolitaine-11-000-000 — http://geoservices.brgm.fr/geologie (WMS/WFS) |

---

## 6. ESDAC — European Soil Data Centre (JRC)

| Champ | Valeur |
|---|---|
| **Nom officiel** | European Soil Data Centre (ESDAC) |
| **Organisme** | Joint Research Centre (JRC) — Commission Européenne |
| **URL d'accès** | https://esdac.jrc.ec.europa.eu/ |
| **Type d'accès** | `file_download` (raster, vecteur, tabulaire), `publication_text` (rapports) |
| **Licence** | CC-BY 4.0 (la majorité des datasets) |
| **Volume estimé** | ~80+ datasets publics. European Soil Database (ESDB) v2.0 : vecteur + attributes à 1/1 000 000 (Europe). Données d'érosion (PESERA, RUSLE), teneur en carbone organique, propriétés du sol, menaces sur les sols. Plusieurs TB au total |
| **Variables** | Texture, profondeur, pH, MOC (carbone organique), CEC, densité apparente, érosion (t/ha/an), couverture du sol, réserve utile en eau, classification WRB, fonctions du sol, menaces (érosion, salinisation, compaction, perte de MOC) |
| **Fréquence de mise à jour** | Irrégulière — mises à jour liées aux projets JRC (LUCAS Soil, EUSO). European Soil Database : mise à jour majeure rare |
| **Couverture** | Europe (UE-27 + pays voisins), certains datasets mondiaux |
| **Priorité GSIE** | **P0** — centre de référence européen, indispensable pour le contexte européen et la cohérence avec la BDGSF française |
| **Exemples d'URL vérifiées** | https://esdac.jrc.ec.europa.eu/ — https://esdac.jrc.ec.europa.eu/resource-type/datasets — https://esdac.jrc.ec.europa.eu/resource-type/european-soil-database-soil-properties — https://esdac.jrc.ec.europa.eu/content/european-soil-database-v20-vector-and-attribute-data — https://data.jrc.ec.europa.eu/collection/esdac |

---

## 7. GIS Sol / BDGSF / IGCS — INRAE

| Champ | Valeur |
|---|---|
| **Nom officiel** | GIS Sol — Groupement d'Intérêt Scientifique Sol (BDGSF, IGCS, RMQS, BDETM, DoneSol) |
| **Organisme** | INRAE / GIS Sol (INRAE, ADEME, IRSTEA, MNHN, Ministère de l'Agriculture, Ministère de l'Écologie) |
| **URL d'accès** | https://gissol.hub.inrae.fr/donnees-et-outils |
| **Type d'accès** | `file_download` (GeoTIFF, tabulaire via Dataverse), `ogc_wms` (infrastructure de données géographiques), `file_import` (DoneSolWeb — accès restreint) |
| **Licence** | Open data — licences variables par dataset (CC-BY, Etalab Licence Ouverte 2.0) |
| **Volume estimé** | BDGSF (Base de Données Géographique des Sols de France) à 1/1 000 000 : vecteur France entière + attributs. IGCS (Inventaire Gestion et Conservation des Sols) : Référentiels Régionaux Pédologiques (RRP) à 1/250 000 — couverture partielle France. RMQS (Réseau de Mesure de la Qualité des Sols) : ~2 200 sites de monitoring. BDETM : éléments traces métalliques. Dataverse : ~20+ jeux de données |
| **Variables** | Types de sols (RPF), profondeur, texture, pH, MOC, CEC, réserve utile en eau, éléments traces métalliques (BDETM), horizons (DoneSol), propriétés physico-chimiques (RMQS : 30+ paramètres analytiques) |
| **Fréquence de mise à jour** | BDGSF : versions ponctuelles (v3.2.8.0). RMQS : campagne d'échantillonnage ~10 ans. RRP/IGCS : progression régionale continue |
| **Couverture** | France métropolitaine + DOM (RMQS), Europe (BDGSF intégrée à l'ESDB) |
| **Priorité GSIE** | **P0** — source nationale de référence pour les sols de France, pivot entre RPF et cartographie opérationnelle |
| **Exemples d'URL vérifiées** | https://gissol.hub.inrae.fr/donnees-et-outils — https://gissol.hub.inrae.fr/donnees-et-outils/donnees/bdgsf — https://gissol.hub.inrae.fr/programmes/igcs/donnees-igcs — https://entrepot.recherche.data.gouv.fr/dataverse/bdgsf — https://doi.org/10.15454/BPN57S (BDGSF v3.2.8.0) — https://doi.org/10.15454/7ZDND6 (carte profondeur) — https://doi.org/10.15454/JPB9RB (carte réserve utile) — https://geodata.inrae.fr/geonetwork/srv/api/records/15eac194-2fc4-5e35-9b8b-550da5b3f738 (RRP Île-de-France) |

---

## 8. GéoNormandie / DataNormandie

| Champ | Valeur |
|---|---|
| **Nom officiel** | GéoNormandie — Plateforme normande d'échange de données géographiques / DataNormandie (open data) |
| **Organisme** | CRIGE Normandie / DREAL Normandie / DRAAF Normandie / Région Normandie (plateforme État-Région, outil PRODIGE) |
| **URL d'accès** | https://www.geonormandie.fr / https://www.datanormandie.fr/ |
| **Type d'accès** | `ogc_wms`, `ogc_wfs`, `file_download` (catalogue INSPIRE) |
| **Licence** | Open data — Licence Ouverte Etalab 2.0 (la majorité) |
| **Volume estimé** | Catalogue régional INSPIRE — données géographiques mutualisées de 80+ structures publiques normandes. Inclut couches pédologiques régionales (RRP Normandie si disponible), géologie, occupation des sols, hydrographie. Volume variable selon producteurs |
| **Variables** | Variables géographiques régionales — sols (si RRP Normandie publié), géologie (couches BRGM moissonnées), occupation des sols, hydrographie, topographie. Pas de base pédologique dédiée propre — sert de portail d'accès aux données des producteurs régionaux |
| **Fréquence de mise à jour** | Continue (moissonnage des producteurs) — fréquence par dataset selon le producteur |
| **Couverture** | Normandie (Manche, Calvados, Orne, Eure, Seine-Maritime) |
| **Priorité GSIE** | **P1** — portail régional d'accès, utile pour les données pédologiques locales normandes et la cohérence avec le périmètre opérationnel GeoSylva |
| **Exemples d'URL vérifiées** | https://www.datanormandie.fr/explorer — https://www.observatoire-des-territoires.gouv.fr/partenaires/geonormandie — https://draaf.normandie.agriculture.gouv.fr/plateforme-normande-d-echange-de-donnees-geographiques-geonormandie-a2054.html |

---

## 9. LUCAS Soil (Commission Européenne — JRC/Eurostat)

| Champ | Valeur |
|---|---|
| **Nom officiel** | LUCAS Soil — Land Use/Cover Area frame Statistical Survey (module Soil) |
| **Organisme** | Eurostat / JRC — Commission Européenne |
| **URL d'accès** | https://esdac.jrc.ec.europa.eu/content/lucas-soil |
| **Type d'accès** | `file_download` (CSV, shapefile) |
| **Licence** | CC-BY 4.0 |
| **Volume estimé** | ~45 000 points d'échantillonnage top-soil (0-20 cm) sur l'UE. Campagnes 2009, 2012, 2015, 2018, 2022. ~200+ paramètres analytiques par point |
| **Variables** | pH, carbone organique, azote total, carbonate de calcium, texture (sable/limon/argile), densité apparente, CEC, éléments nutritifs (P, K), métaux traces, biodiversité du sol (depuis 2018), érosion |
| **Fréquence de mise à jour** | Tous les 3 ans (2009, 2012, 2015, 2018, 2022) |
| **Couverture** | Europe (UE-27) — inclut points en France |
| **Priorité GSIE** | **P1** — échantillonnage in-situ le plus systématique en Europe, complémentaire de SoilGrids et ESDAC pour validation |
| **Exemples d'URL vérifiées** | https://esdac.jrc.ec.europa.eu/content/lucas-soil — https://esdac.jrc.ec.europa.eu/resource-type/datasets (filtrer "LUCAS") |

---

## 10. Base de Données d'Analyses de Terre (BDAT) — GIS Sol

| Champ | Valeur |
|---|---|
| **Nom officiel** | Base de Données d'Analyses de Terre (BDAT) |
| **Organisme** | GIS Sol / INRAE (gestion), laboratoires d'analyse agronomique (producteurs) |
| **URL d'accès** | https://gissol.hub.inrae.fr/donnees-et-outils/donnees/bdat |
| **Type d'accès** | `file_download` (données agrégées), `publication_text` (rapports) |
| **Licence** | Accès restreint aux données brutes (données laboratoires). Données agrégées en open data (Licence Ouverte Etalab 2.0) |
| **Volume estimé** | ~2,5 millions d'analyses de terre cumulées depuis 1990. Données agrégées par canton/commune. Périodes 1990-1994, 1995-1999, 2000-2004, 2005-2009, 2010-2014, 2015-2019 |
| **Variables** | pH, carbone organique, azote total, P₂O₅, K₂O, MgO, CaO, Na₂O, CEC, texture (sable/limon/argile), conductivité électrique |
| **Fréquence de mise à jour** | Quinquennale (périodes de 5 ans) |
| **Couverture** | France métropolitaine (maille cantonale/communale pour données agrégées) |
| **Priorité GSIE** | **P1** — source unique pour le suivi temporel de la qualité des sols agricoles français, complémentaire du RMQS |
| **Exemples d'URL vérifiées** | https://gissol.hub.inrae.fr/donnees-et-outils/donnees/bdat — https://entrepot.recherche.data.gouv.fr/dataverse/bdgsf (dataverse GIS Sol) |

---

## Synthèse — matrice de priorité GSIE

| Source | Type principal | Couverture | Priorité | Rôle dans GSIE |
|---|---|---|---|---|
| RPF (AFES/INRAE) | `knowledge_extraction` | France | **P0** | Ontologie de classification des sols français |
| WRB (IUSS/FAO) | `publication_text` | Mondiale | **P0** | Standard international de classification — pivot de correspondance |
| SoilGrids 2.0 (ISRIC) | `file_download` / `api_rest` | Mondiale | **P0** | Couches raster globales des propriétés du sol |
| WoSIS (ISRIC) | `ogc_wfs` / `file_download` | Mondiale | **P0** | Profils de sol observés — calibration/validation |
| InfoTerre / BRGM | `ogc_wms` / `ogc_wfs` / `file_download` | France | **P0** | Substrat géologique national |
| ESDAC (JRC) | `file_download` | Europe | **P0** | Centre de référence européen — cohérence BDGSF |
| GIS Sol / BDGSF / IGCS (INRAE) | `file_download` / `ogc_wms` | France | **P0** | Cartographie pédologique nationale de référence |
| GéoNormandie / DataNormandie | `ogc_wms` / `ogc_wfs` | Normandie | **P1** | Portail régional — données locales normandes |
| LUCAS Soil (Eurostat/JRC) | `file_download` | Europe | **P1** | Échantillonnage in-situ européen — validation |
| BDAT (GIS Sol) | `file_download` | France | **P1** | Suivi temporel qualité sols agricoles |

---

## Notes méthodologiques

- **Aucune URL inventée.** Toutes les URLs ci-dessus ont été vérifiées via `web_search` le 2026-07-15.
- **Correspondances RPF ↔ WRB** : un travail de mapping sémantique est nécessaire pour le moteur Pedology. Le RPF est plus détaillé pour la France mais non aligné par défaut avec le WRB. Voir publication INRAE sur les correspondances (https://hal.inrae.fr/hal-02797907).
- **SoilGrids + WoSIS** : SoilGrids 2.0 est entraîné sur les profils WoSIS. Les deux sources sont donc corrélées — ne pas les traiter comme indépendantes pour la validation.
- **BRGM + GIS Sol** : le substrat géologique (BRGM) et la couverture pédologique (GIS Sol) sont complémentaires. Le moteur Pedology doit consommer les deux pour reconstruire la séquence sol → substrat.
- **Accès restreint** : DoneSolWeb (interface de saisie GIS Sol) et les données brutes BDAT nécessitent des accès négociés. Prévoir une démarche d'accord-cadre pour GSIE.
- **Google Earth Engine** : SoilGrids est disponible comme dataset communautaire sur GEE — alternative au téléchargement WebDAV pour les pipelines de traitement cloud.

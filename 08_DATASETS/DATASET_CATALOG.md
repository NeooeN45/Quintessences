# GSIE Dataset Catalog — Catalogue des jeux de données

| Champ | Valeur |
|---|---|
| **Livrable** | 305 — Dataset Catalog |
| **Phase** | 3 — Connaissance |
| **Statut** | Draft |
| **Date de révision** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-002, GSIE-CON-005 |
| **Constitutions liées** | Scientifique (S-1) |
| **Directive d'ouverture** | GSIE-DIR-0007 (DEC-000011) |

---

## 1. Objet

Le présent livrable catalogue les jeux de données (datasets) qui
alimentent la base de connaissances GSIE (`07_KNOWLEDGE/`) et les
14 moteurs spécialisés (`09_ENGINES/`). Il opérationnalise deux
exigences constitutionnelles :

- **GSIE-CON-002** (La science avant tout) : aucune donnée n'est
  intégrée sans une source scientifique identifiable et vérifiable.
- **GSIE-CON-005** (Toute connaissance doit être traçable) : chaque
  dataset possède une origine, un organisme producteur, une version,
  une licence et un contact.

Ce catalogue couvre les dix domaines scientifiques de l'article S-6
(écologie forestière, pédologie, dendrométrie, climatologie,
botanique, pathologie, entomologie, sylviculture, biodiversité,
dynamique des peuplements) ainsi que les besoins spécifiques du
jumeau numérique Ignis (météo, satellite, terrain incendie).

Aucune donnée n'est inventée : chaque fiche renvoie à un organisme
producteur réel et à une licence effectivement appliquée par cet
organisme. Les licences sont détaillées au §5 et référencées dans
`19_LEGAL/`.

---

## 2. Structure d'une fiche de métadonnées

Chaque dataset du catalogue (§3) est décrit selon une fiche
normalisée dont les champs sont définis ci-dessous. Cette structure
garantit que toute donnée entrant dans GSIE est sourcée, traçable et
conforme aux contraintes de licence.

| Champ | Définition | Exigence |
|---|---|---|
| **Identifiant GSIE** | Code stable `DS-XXX` attribué par GSIE | Obligatoire, unique |
| **Nom du dataset** | Nom officiel utilisé par le producteur | Obligatoire |
| **Organisme producteur** | Institution qui produit et maintient la donnée | Obligatoire (S-1 : référentiel officiel) |
| **Catégorie** | Catégorie du catalogue (A à F, voir §3) | Obligatoire |
| **Domaines S-6 couverts** | Domaines scientifiques alimentés (S-6) | Obligatoire |
| **Moteurs consommateurs** | Moteurs GSIE qui ingèrent la donnée | Obligatoire |
| **Source / URL** | Adresse officielle d'accès (portail, API, flux) | Obligatoire |
| **Licence** | Licence effective appliquée par le producteur | Obligatoire (voir §5) |
| **Couverture spatiale** | Périmètre géographique (France métropole, monde, etc.) | Obligatoire |
| **Couverture temporelle** | Plage de dates couverte par la donnée | Obligatoire |
| **Résolution spatiale** | Taille de la maille ou de la cellule (m, km, degrés) | Si applicable |
| **Résolution temporelle** | Pas de temps (quotidien, décennal, etc.) | Si applicable |
| **Format** | Format de distribution (GeoTIFF, NetCDF, CSV, Shapefile, API) | Obligatoire |
| **Version référencée** | Version ou édition exacte utilisisée par GSIE | Obligatoire (CON-005) |
| **Qualité / précision** | Indicateurs de qualité (précision géométrique, attributaire) | Recommandé |
| **Contact** | Organisme ou service à contacter pour l'accès | Obligatoire |
| **Statut d'ingestion** | État dans GSIE (Planifié / En cours / Ingesté / En quarantaine) | Obligatoire |
| **Notes** | Restrictions, particularités, dépendances | Optionnel |

> **Règle de quarantaine (CON-005) :** tout dataset dont les
> métadonnées sont incomplètes est mis en quarantaine jusqu'à
> sourçage complet. Aucune donnée anonyme n'est acceptée.

---

## 3. Catalogue par catégorie

Le catalogue est organisé en six catégories (A à F) correspondant
aux grandes familles de données consommées par GSIE et Ignis.

### 3.A — Datasets forestiers (IGN, ONF, INRAE)

#### DS-001 — BD Forêt v2 (IGN)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-001 |
| **Nom du dataset** | BD Forêt version 2 |
| **Organisme producteur** | IGN (Institut national de l'information géographique et forestière) |
| **Catégorie** | A — Forestier |
| **Domaines S-6 couverts** | Écologie forestière, sylviculture, dynamique des peuplements |
| **Moteurs consommateurs** | GIS Engine, Forest Dynamics Engine, Diagnostic Engine |
| **Source / URL** | https://ignfr.maps.arcgis.com / portail data.gouv.fr (IGN) |
| **Licence** | Licence Ouverte 2.0 (etalab-2.0) |
| **Couverture spatiale** | France métropolitaine et Corse |
| **Couverture temporelle** | 2007-présent (campagnes départementales, mise à jour continue) |
| **Résolution spatiale** | Polygones forestiers (surface minimum 500 m²) |
| **Résolution temporelle** | Mise à jour par département (cycle ~5 ans) |
| **Format** | Shapefile, GeoPackage, WFS |
| **Version référencée** | BD Forêt v2 (édition courante) |
| **Qualité / précision** | Précision géométrique 1 m (BD Parcellaire sous-jacente) ; nomenclature essences IGN |
| **Contact** | IGN — Service de la cartographie forestière |
| **Statut d'ingestion** | Planifié |
| **Notes** | Couverture forestière française de référence ; segmentation par essence dominante et type de peuplement |

#### DS-002 — IGN LiDAR HD

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-002 |
| **Nom du dataset** | LiDAR HD (Modèle Numérique de Terrain et canopée) |
| **Organisme producteur** | IGN |
| **Catégorie** | A — Forestier |
| **Domaines S-6 couverts** | Dendrométrie, dynamique des peuplements, écologie forestière |
| **Moteurs consommateurs** | GIS Engine, Forest Dynamics Engine, Simulation Engine |
| **Source / URL** | https://geoservices.ign.fr/lidarhd (portail IGN) |
| **Licence** | Licence Ouverte 2.0 (etalab-2.0) |
| **Couverture spatiale** | France métropolitaine (couverture programmée 2021-2026) |
| **Couverture temporelle** | 2021-2026 (acquisition progressive) |
| **Résolution spatiale** | MNT à 1 m ; nuages de points classés (densité ~10 pts/m²) |
| **Résolution temporelle** | Acquisition unique (pas de répétition planifiée à ce jour) |
| **Format** | LAZ/LAS, GeoTIFF (MNT raster) |
| **Version référencée** | LiDAR HD (édition 2024+) |
| **Qualité / précision** | Précision altimétrique verticale ~10 cm (MNT) ; classification sol/canopée |
| **Contact** | IGN — Programme LiDAR HD |
| **Statut d'ingestion** | Planifié |
| **Notes** | Permet le calcul de hauteur de canopée, volume sur pied et biomasse ; donnée structurante pour Ignis (combustible) |

#### DS-003 — Inventaire Forestier National (IGN)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-003 |
| **Nom du dataset** | Inventaire Forestier National — placettes permanentes |
| **Organisme producteur** | IGN — Département Inventaire Forestier |
| **Catégorie** | A — Forestier |
| **Domaines S-6 couverts** | Dendrométrie, écologie forestière, dynamique des peuplements |
| **Moteurs consommateurs** | Forest Dynamics Engine, Correlation Engine, Learning Engine |
| **Source / URL** | https://inventaire-forestier.ign.fr |
| **Licence** | Licence Ouverte 2.0 (etalab-2.0) |
| **Couverture spatiale** | France métropolitaine et Corse |
| **Couverture temporelle** | 1958-présent (réseau permanent depuis 2005) |
| **Résolution spatiale** | Placettes de 20 m de rayon (maille systématique ~1 placette / 2 km) |
| **Résolution temporelle** | Relevé tous les 5 ans (cycle IFN) |
| **Format** | CSV, données tabulaires (catalogue IGN) |
| **Version référencée** | Campagnes 2015-2023 (données accessibles) |
| **Qualité / précision** | Protocole dendrométrique normalisé ; mesure de circonférence, hauteur, essence, état sanitaire |
| **Contact** | IGN — Département Inventaire Forestier |
| **Statut d'ingestion** | Planifié |
| **Notes** | Source de vérité dendrométrique nationale ; alimente les modèles de croissance et la calibration Forest Dynamics |

#### DS-004 — BD Ortho

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-004 |
| **Nom du dataset** | BD Ortho — imagerie aérienne |
| **Organisme producteur** | IGN |
| **Catégorie** | A — Forestier |
| **Domaines S-6 couverts** | Écologie forestière, sylviculture |
| **Moteurs consommateurs** | GIS Engine, Diagnostic Engine |
| **Source / URL** | https://geoservices.ign.fr/bdortho |
| **Licence** | Licence Ouverte 2.0 (etalab-2.0) |
| **Couverture spatiale** | France métropolitaine, Corse, DROM-COM |
| **Couverture temporelle** | 2000-présent (renouvellement par département) |
| **Résolution spatiale** | 20 cm (BD Ortho HR) ou 50 cm |
| **Résolution temporelle** | Renouvellement ~3-5 ans selon département |
| **Format** | GeoTIFF, WMS, WMTS |
| **Version référencée** | BD Ortho édition courante |
| **Qualité / précision** | Précision géométrique < 1 m ; orthorectifiée |
| **Contact** | IGN — Service imagerie |
| **Statut d'ingestion** | Planifié |
| **Notes** | Imagerie de référence pour la photo-interprétation forestière et la validation télédétection |

#### DS-005 — ONF RPF (Référentiel Pédologique Forestier)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-005 |
| **Nom du dataset** | Référentiel Pédologique Forestier (RPF) |
| **Organisme producteur** | ONF (Office National des Forêts) — en collaboration INRAE |
| **Catégorie** | A — Forestier / C — Pédologique |
| **Domaines S-6 couverts** | Pédologie, écologie forestière stationnelle |
| **Moteurs consommateurs** | Pedology Engine, Diagnostic Engine, Recommendation Engine |
| **Source / URL** | Documentation ONF (référentiel interne, diffusion limitée) |
| **Licence** | Accord ONF (à formaliser — voir `19_LEGAL/` et `20_PARTNERSHIPS/`) |
| **Couverture spatiale** | Forêts relevant du régime forestier français (domaniales, communales) |
| **Couverture temporelle** | Édition 2008 (référentiel), mises à jour ponctuelles |
| **Résolution spatiale** | Unités stationnelles (échelle parcelle / station) |
| **Résolution temporeelle** | Référentiel (pas de répétition systématique) |
| **Format** | Document technique + couches géographiques (Shapefile) |
| **Version référencée** | RPF édition 2008 |
| **Qualité / précision** | Référentiel expert validé par comité ONF/INRAE |
| **Contact** | ONF — Département Recherche Développement Innovation (RDI) |
| **Statut d'ingestion** | En quarantaine (accord de licence à formaliser) |
| **Notes** | Référentiel fondamental pour les seuils pédologiques (pH, texture, drainage) cités en CON-002 |

#### DS-006 — INRAE — données expérimentales (SOERE F-ORE-T)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-006 |
| **Nom du dataset** | SOERE F-ORE-T — sites expérimentaux forestiers long terme |
| **Organisme producteur** | INRAE (UMR BEF, ISPA, EEF) — réseau SOERE F-ORE-T |
| **Catégorie** | A — Forestier |
| **Domaines S-6 couverts** | Écologie forestière, dendrométrie, dynamique des peuplements, pathologie |
| **Moteurs consommateurs** | Forest Dynamics Engine, Correlation Engine, Learning Engine |
| **Source / URL** | https://www.gip-ecofor.org/soere/f-ore-t |
| **Licence** | Accès sous accord (data policy SOERE) — CC-BY sur publications associées |
| **Couverture spatiale** | Sites expérimentaux français (ex. Hesse, Fougères, Montiers, Breuil-Chenue) |
| **Couverture temporelle** | 1980-présent (selon site, certaines séries > 40 ans) |
| **Résolution spatiale** | Échelle placette / arbre (suivi individuel) |
| **Résolution temporelle** | Annuel à pluriannuel (mesures dendrométriques, flux) |
| **Format** | CSV, bases de données INRAE (accès sur demande) |
| **Version référencée** | Données 2010-2023 (séries longues) |
| **Qualité / précision** | Protocoles INRAE normalisés ; contrôle qualité interne |
| **Contact** | INRAE — coordination SOERE F-ORE-T (GIP Ecofor) |
| **Statut d'ingestion** | Planifié (accord d'accès requis) |
| **Notes** | Données expérimentales de référence pour la calibration des modèles de croissance et flux carbone |

---

### 3.B — Datasets climatiques (Météo-France)

#### DS-007 — Safran (Météo-France)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-007 |
| **Nom du dataset** | Safran — analyse spatialisée quotidienne |
| **Organisme producteur** | Météo-France — Direction de la Climatologie |
| **Catégorie** | B — Climatique |
| **Domaines S-6 couverts** | Climatologie, bioclimatologie |
| **Moteurs consommateurs** | Climate Engine, Simulation Engine, Forest Dynamics Engine |
| **Source / URL** | https://www.meteofrance.fr (portail climatique — accès Météo-France) |
| **Licence** | Conditions Météo-France (Licence Ouverte sur produits dérivés ; données brutes sous accord) |
| **Couverture spatiale** | France métropolitaine (grille 8 km) |
| **Couverture temporelle** | 1958-présent (série continue réanalysée) |
| **Résolution spatiale** | Maille 8 km |
| **Résolution temporelle** | Quotidienne |
| **Format** | NetCDF, GRIB |
| **Version référencée** | Safran (réanalyse courante) |
| **Qualité / précision** | Réanalyse par analyse-objet (précipitations, température, rayonnement, ETP) |
| **Contact** | Météo-France — Direction de la Climatologie et des Services Climatiques |
| **Statut d'ingestion** | Planifié (accord d'accès à formaliser) |
| **Notes** | Source climatique quotidienne de référence pour la France ; indispensable aux modèles bioclimatiques et à Ignis (sécheresse) |

#### DS-008 — DRIAS — projections climatiques régionalisées

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-008 |
| **Nom du dataset** | DRIAS — Les futurs du climat |
| **Organisme producteur** | Météo-France (en partenariat IPSL, CERFACS, CNRM-GAME) |
| **Catégorie** | B — Climatique |
| **Domaines S-6 couverts** | Climatologie, bioclimatologie |
| **Moteurs consommateurs** | Climate Engine, Simulation Engine |
| **Source / URL** | http://www.drias-climat.fr |
| **Licence** | Licence Ouverte 2.0 (etalab-2.0) sur les produits DRIAS |
| **Couverture spatiale** | France métropolitaine (grilles régionalisées 8-12 km) |
| **Couverture temporelle** | 1950-2100 (scénarios RCP/SSP, CMIP5/CMIP6) |
| **Résolution spatiale** | 8 km (Safran downscaled) à 12 km selon produit |
| **Résolution temporelle** | Quotidienne (variables climatiques) |
| **Format** | NetCDF |
| **Version référencée** | DRIAS 2020 (CMIP6, scénarios SSP) |
| **Qualité / précision** | Régionalisation par désagrégation statistique/dynamique (ALADIN, TREND) |
| **Contact** | Météo-France — portail DRIAS |
| **Statut d'ingestion** | Planifié |
| **Notes** | Alimente les projections long terme de Simulation Engine (impact climatique sur peuplements 2100) |

#### DS-009 — ARPEGE / AROME (modèles météo)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-009 |
| **Nom du dataset** | ARPEGE / AROME — sorties de modèles atmosphériques |
| **Organisme producteur** | Météo-France — Direction de la Prévision |
| **Catégorie** | B — Climatique / météorologique |
| **Domaines S-6 couverts** | Climatologie, bioclimatologie |
| **Moteurs consommateurs** | Climate Engine, Simulation Engine, Ignis (météo temps réel) |
| **Source / URL** | https://donneespubliques.meteofrance.fr |
| **Licence** | Conditions Météo-France (Licence Ouverte sur produits ouverts ; archivage sous accord) |
| **Couverture spatiale** | ARPEGE : France + global ; AROME : France métropolitaine (domaine 1.3 km) |
| **Couverture temporelle** | Prévisions opérationnelles continues ; archivage historique |
| **Résolution spatiale** | AROME 1.3 km ; ARPEGE ~5-7 km (France) |
| **Résolution temporelle** | Horaire (prévisions) ; archivage horaire/journalier |
| **Format** | GRIB, NetCDF |
| **Version référencée** | Cycle opérationnel courant (ARPEGE 6, AROME 1.3 km) |
| **Qualité / précision** | Modèle de prévision numérique opérationnel (Météo-France) |
| **Contact** | Météo-France — Direction de la Production |
| **Statut d'ingestion** | Planifié (prioritaire pour Ignis) |
| **Notes** | Vent, température, humidité — entrées critiques pour la propagation incendie (Ignis) |

#### DS-010 — Météo-France — observations sol

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-010 |
| **Nom du dataset** | Postes climatiques au sol (réseau d'observation) |
| **Organisme producteur** | Météo-France — Direction de l'Observation |
| **Catégorie** | B — Climatique |
| **Domaines S-6 couverts** | Climatologie, bioclimatologie |
| **Moteurs consommateurs** | Climate Engine, Correlation Engine |
| **Source / URL** | https://donneespubliques.meteofrance.fr |
| **Licence** | Licence Ouverte 2.0 (etalab-2.0) sur données publiques ; stations privées sous accord |
| **Couverture spatiale** | France métropolitaine et DROM-COM (~3000 postes) |
| **Couverture temporelle** | 1900-présent (selon station) |
| **Résolution spatiale** | Ponctuelle (stations) |
| **Résolution temporelle** | Horaire à quotidienne |
| **Format** | CSV, API Météo-France |
| **Version référencée** | Réseau courant (postes principaux et auxiliaires) |
| **Qualité / précision** | Mesures instrumentales contrôlées (température, précipitations, vent, humidité) |
| **Contact** | Météo-France — Direction de l'Observation |
| **Statut d'ingestion** | Planifié |
| **Notes** | Observations terrain de référence pour la validation Safran et la calibration Climate Engine |

---

### 3.C — Datasets pédologiques

#### DS-011 — BDAT (Base de Données des Analyses de Terre)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-011 |
| **Nom du dataset** | BDAT — Base de Données des Analyses de Terre |
| **Organisme producteur** | INRAE (US INFOSOL) — GIS Sol |
| **Catégorie** | C — Pédologique |
| **Domaines S-6 couverts** | Pédologie, écologie forestière |
| **Moteurs consommateurs** | Pedology Engine, Correlation Engine, Diagnostic Engine |
| **Source / URL** | http://www.gissol.fr/programme/bdat/bdat.php |
| **Licence** | Licence Ouverte 2.0 (etalab-2.0) via GIS Sol |
| **Couverture spatiale** | France métropolitaine (cantons agricoles) |
| **Couverture temporelle** | 1990-présent (campagnes décennales 1990-1994, 1995-1999, 2000-2004, 2005-2009, 2010-2014) |
| **Résolution spatiale** | Agrégation cantonale (statistiques) ; analyses ponctuelles |
| **Résolution temporelle** | Décennale |
| **Format** | CSV, tableurs |
| **Version référencée** | BDAT campagne 2010-2014 |
| **Qualité / précision** | Analyses de laboratoire normalisées (pH, C, N, P, K, Mg, Ca) |
| **Contact** | INRAE US INFOSOL — GIS Sol |
| **Statut d'ingestion** | Planifié |
| **Notes** | Source pédologique agricole de référence ; complémentaire du RPF pour les contextes forestiers |

#### DS-012 — RPFR (Référentiel Pédologique Forestier Régional)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-012 |
| **Nom du dataset** | RPFR — Référentiel Pédologique Forestier Régional |
| **Organisme producteur** | ONF / INRAE (déclinaisons régionales) |
| **Catégorie** | C — Pédologique |
| **Domaines S-6 couverts** | Pédologie, écologie forestière stationnelle |
| **Moteurs consommateurs** | Pedology Engine, Diagnostic Engine |
| **Source / URL** | Documentation ONF régionale (diffusion interne) |
| **Licence** | Accord ONF (à formaliser) |
| **Couverture spatiale** | Régions forestières françaises (selon déclinaison disponible) |
| **Couverture temporelle** | Éditions régionales variables (2000-2020) |
| **Résolution spatiale** | Station / unité de sol |
| **Résolution temporelle** | Référentiel (mise à jour ponctuelle) |
| **Format** | Document technique + SIG |
| **Version référencée** | Éditions régionales courantes |
| **Qualité / précision** | Référentiel expert validé |
| **Contact** | ONF — pôles régionaux RDI |
| **Statut d'ingestion** | En quarantaine (licence à formaliser) |
| **Notes** | Déclinaison régionale du RPF (DS-005) ; précise les types de sols par région forestière |

#### DS-013 — SoilGrids (ISRIC)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-013 |
| **Nom du dataset** | SoilGrids — cartographie mondiale des sols |
| **Organisme producteur** | ISRIC — World Soil Information (Pays-Bas) |
| **Catégorie** | C — Pédologique |
| **Domaines S-6 couverts** | Pédologie |
| **Moteurs consommateurs** | Pedology Engine, GIS Engine |
| **Source / URL** | https://soilgrids.org |
| **Licence** | CC-BY 4.0 (ISRIC) |
| **Couverture spatiale** | Mondiale |
| **Couverture temporelle** | Édition 2017, SoilGrids 2.0 (2020) |
| **Résolution spatiale** | 250 m |
| **Résolution temporelle** | Édition statique (mise à jour ponctuelle) |
| **Format** | GeoTIFF (rasters), services WMS/WCS |
| **Version référencée** | SoilGrids 2.0 (2020) |
| **Qualité / précision** | Modèle prédictif (machine learning) sur profils WOSIS ; incertitude fournie par pixel |
| **Contact** | ISRIC — World Soil Information |
| **Statut d'ingestion** | Planifié |
| **Notes** | Couverture mondiale utile pour les comparaisons et contextes hors France ; compléter par BDAT/RPF sur le territoire national |

---

### 3.D — Datasets taxonomiques et biodiversité

#### DS-014 — GBIF (occurrences taxonomiques)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-014 |
| **Nom du dataset** | GBIF — Global Biodiversity Information Facility |
| **Organisme producteur** | GBIF (secrétariat international, membres nationaux) |
| **Catégorie** | D — Taxonomique / biodiversité |
| **Domaines S-6 couverts** | Botanique, taxonomie, biodiversité, entomologie, pathologie |
| **Moteurs consommateurs** | Botanical Engine, Correlation Engine, Diagnostic Engine |
| **Source / URL** | https://www.gbif.org |
| **Licence** | Variable par occurrence (CC-BY 4.0, CC0, CC-BY-NC) — à vérifier par enregistrement |
| **Couverture spatiale** | Mondiale |
| **Couverture temporelle** | 1700-présent |
| **Résolution spatiale** | Ponctuelle (occurrences géoréférencées) |
| **Résolution temporelle** | Événementielle (occurrences) |
| **Format** | Darwin Core, CSV, API REST |
| **Version référencée** | Snapshot GBIF (téléchargement daté) |
| **Qualité / précision** | Hétérogène (à filtrer par qualité de géoréférencement) |
| **Contact** | GBIF — portail national France (GBIF France / MNHN) |
| **Statut d'ingestion** | Planifié |
| **Notes** | Source d'occurrences pour la cartographie de répartition des essences et pathogènes ; licence à contrôler par occurrence |

#### DS-015 — Tela Botanica (flore française)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-015 |
| **Nom du dataset** | Tela Botanica — réseau botanique et observations flore |
| **Organisme producteur** | Association Tela Botanica (France) |
| **Catégorie** | D — Taxonomique / biodiversité |
| **Domaines S-6 couverts** | Botanique, taxonomie, biodiversité |
| **Moteurs consommateurs** | Botanical Engine, Correlation Engine |
| **Source / URL** | https://www.tela-botanica.org |
| **Licence** | CC-BY-SA (observations) — à vérifier par jeu |
| **Couverture spatiale** | France et régions limitrophes |
| **Couverture temporelle** | 2000-présent |
| **Résolution spatiale** | Ponctuelle (observations citoyennes et expertes) |
| **Résolution temporelle** | Événementielle |
| **Format** | CSV, API Tela Botanica |
| **Version référencée** | Export daté (observations validées) |
| **Qualité / précision** | Validation collaborative ; à filtrer par niveau de validation |
| **Contact** | Association Tela Botanica |
| **Statut d'ingestion** | Planifié |
| **Notes** | Complémentaire de l'INPN pour la flore ; riche en observations citoyennes sur espèces forestières |

#### DS-016 — BDNFF (Base de Données Nomenclaturale de la Flore de France)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-016 |
| **Nom du dataset** | BDNFF — Base de Données Nomenclaturale de la Flore de France |
| **Organisme producteur** | Tela Botanica / Société Botanique de France (référentiel nomenclatural) |
| **Catégorie** | D — Taxonomique / biodiversité |
| **Domaines S-6 couverts** | Botanique, taxonomie |
| **Moteurs consommateurs** | Botanical Engine, Knowledge Engine (ontologie taxonomique) |
| **Source / URL** | https://www.tela-botanica.org/bdnff/ |
| **Licence** | CC-BY (référentiel nomenclatural) |
| **Couverture spatiale** | France métropolitaine et Corse |
| **Couverture temporelle** | Référentiel vivant (mise à jour continue) |
| **Résolution spatiale** | N/A (référentiel taxonomique) |
| **Résolution temporelle** | Continue |
| **Format** | CSV, API |
| **Version référencée** | Version courante (snapshot daté) |
| **Qualité / précision** | Référentiel nomenclatural expert (synonymies, acceptations) |
| **Contact** | Tela Botanica — Société Botanique de France |
| **Statut d'ingestion** | Planifié |
| **Notes** | Référentiel nomenclatural de la flore française ; backbone taxonomique pour l'ontologie forestière (livrable 303) |

#### DS-017 — INPN (Inventaire National du Patrimoine Naturel)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-017 |
| **Nom du dataset** | INPN — Inventaire National du Patrimoine Naturel |
| **Organisme producteur** | MNHN (Muséum national d'Histoire naturelle) — UMS PatriNat |
| **Catégorie** | D — Taxonomique / biodiversité |
| **Domaines S-6 couverts** | Biodiversité, botanique, entomologie, pathologie, conservation |
| **Moteurs consommateurs** | Botanical Engine, Diagnostic Engine, Correlation Engine |
| **Source / URL** | https://inpn.mnhn.fr |
| **Licence** | Licence Ouverte 2.0 (etalab-2.0) / CC-BY selon jeu |
| **Couverture spatiale** | France métropolitaine, DROM-COM, eaux marines |
| **Couverture temporelle** | 1700-présent |
| **Résolution spatiale** | Ponctuelle et zonages (aires de répartition, ZNIEFF) |
| **Résolution temporelle** | Événementielle et statique (zonages) |
| **Format** | CSV, Shapefile, API REST (INPN) |
| **Version référencée** | Snapshot INPN (téléchargement daté) |
| **Qualité / précision** | Validation MNHN ; taxonomie TAXREF de référence |
| **Contact** | MNHN — UMS PatriNat |
| **Statut d'ingestion** | Planifié |
| **Notes** | Source nationale de référence pour la biodiversité ; intègre le référentiel taxonomique TAXREF (backbone complémentaire de BDNFF) |

---

### 3.E — Datasets satellite et télédétection

#### DS-018 — Copernicus Sentinel-2

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-018 |
| **Nom du dataset** | Sentinel-2 — imagerie multispectrale |
| **Organisme producteur** | ESA / Commission européenne (programme Copernicus) |
| **Catégorie** | E — Satellite / télédétection |
| **Domaines S-6 couverts** | Écologie forestière, dynamique des peuplements, pathologie |
| **Moteurs consommateurs** | GIS Engine, Forest Dynamics Engine, Diagnostic Engine, Ignis |
| **Source / URL** | https://scihub.copernicus.eu (Copernicus Open Access Hub) |
| **Licence** | Libre et gratuite (Copernicus data policy — CC-BY 4.0) |
| **Couverture spatiale** | Mondiale (terres émergées) |
| **Couverture temporelle** | 2015-présent (Sentinel-2A), 2017-présent (Sentinel-2B) |
| **Résolution spatiale** | 10 m (bandes visibles, NIR), 20 m (RE, SWIR), 60 m (bandes atmosphériques) |
| **Résolution temporelle** | 5 jours (constellation 2A+2B) |
| **Format** | SAFE (JP2), GeoTIFF (niveaux 1C/2A) |
| **Version référencée** | Niveau 2A (correction atmosphérique) |
| **Qualité / précision** | Calibration ESA ; produits L2A traités |
| **Contact** | ESA — Copernicus Data Access |
| **Statut d'ingestion** | Planifié |
| **Notes** | Imagerie de référence pour les indices de végétation (NDVI), détection dépérissement, cartographie combustible (Ignis) |

#### DS-019 — Copernicus Sentinel-1

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-019 |
| **Nom du dataset** | Sentinel-1 — imagerie radar C-SAR |
| **Organisme producteur** | ESA / Commission européenne (programme Copernicus) |
| **Catégorie** | E — Satellite / télédétection |
| **Domaines S-6 couverts** | Écologie forestière, dynamique des peuplements |
| **Moteurs consommateurs** | GIS Engine, Forest Dynamics Engine |
| **Source / URL** | https://scihub.copernicus.eu |
| **Licence** | Libre et gratuite (Copernicus data policy — CC-BY 4.0) |
| **Couverture spatiale** | Mondiale |
| **Couverture temporelle** | 2014-présent (Sentinel-1A), 2016-présent (Sentinel-1B, puis 1C) |
| **Résolution spatiale** | 10 m (mode IW, GRD) |
| **Résolution temporelle** | 6 jours (constellation) |
| **Format** | SAFE (TIFF), GeoTIFF (GRD) |
| **Version référencée** | Niveau GRD (IW) |
| **Qualité / précision** | Calibration ESA ; traitement GRD |
| **Contact** | ESA — Copernicus Data Access |
| **Statut d'ingestion** | Planifié |
| **Notes** | Radar toutes conditions météo ; utile pour la biomasse forestière et le suivi indépendant de la nébulosité |

#### DS-020 — Landsat 8 / 9

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-020 |
| **Nom du dataset** | Landsat 8 / 9 — imagerie multispectrale |
| **Organisme producteur** | USGS / NASA (États-Unis) |
| **Catégorie** | E — Satellite / télédétection |
| **Domaines S-6 couverts** | Écologie forestière, dynamique des peuplements |
| **Moteurs consommateurs** | GIS Engine, Forest Dynamics Engine |
| **Source / URL** | https://earthexplorer.usgs.gov |
| **Licence** | Domaine public (USGS — pas de restriction) |
| **Couverture spatiale** | Mondiale |
| **Couverture temporelle** | Landsat 8 : 2013-présent ; Landsat 9 : 2021-présent |
| **Résolution spatiale** | 30 m (multispectral), 15 m (panchromatique) |
| **Résolution temporelle** | 8 jours (constellation 8+9) |
| **Format** | GeoTIFF (Niveau 2 — réflectance surface) |
| **Version référencée** | Collection 2, Niveau 2 |
| **Qualité / précision** | Calibration USGS ; archive longue série |
| **Contact** | USGS — Earth Resources Observation and Science (EROS) |
| **Statut d'ingestion** | Planifié |
| **Notes** | Série longue (Landsat continu depuis 1972) ; utile pour les analyses de tendance et l'historique forestier |

#### DS-021 — MODIS (végétation globale)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-021 |
| **Nom du dataset** | MODIS — produits végétation (MOD13 NDVI/EVI, MCD43) |
| **Organisme producteur** | NASA (Terra/Aqua) — LP DAAC |
| **Catégorie** | E — Satellite / télédétection |
| **Domaines S-6 couverts** | Écologie forestière, dynamique des peuplements, climatologie |
| **Moteurs consommateurs** | GIS Engine, Climate Engine, Forest Dynamics Engine |
| **Source / URL** | https://lpdaac.usgs.gov |
| **Licence** | Domaine public (NASA data policy) |
| **Couverture spatiale** | Mondiale |
| **Couverture temporelle** | 2000-présent (Terra), 2002-présent (Aqua) |
| **Résolution spatiale** | 250 m (NDVI), 500 m (BRDF), 1 km (certains produits) |
| **Résolution temporelle** | 16 jours (NDVI), quotidien (BRDF) |
| **Format** | HDF, GeoTIFF |
| **Version référencée** | Collection 6.1 |
| **Qualité / précision** | Calibration NASA ; produits validés |
| **Contact** | NASA LP DAAC |
| **Statut d'ingestion** | Planifié |
| **Notes** | Série temporelle globale pour la phénologie et la productivité primaire ; complémentaire de Sentinel-2 (résolution plus grossière mais fréquence élevée) |

---

### 3.F — Datasets incendie (Ignis)

#### DS-022 — Prométhée (base incendies France méditerranéenne)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-022 |
| **Nom du dataset** | Base Prométhée — base de données sur les incendies de forêt |
| **Organisme producteur** | Entente pour la Forêt Méditerranéenne (EEIFM) — base Prométhée |
| **Catégorie** | F — Incendie |
| **Domaines S-6 couverts** | Écologie forestière, sylviculture (post-incendie) |
| **Moteurs consommateurs** | Ignis, Simulation Engine, Diagnostic Engine |
| **Source / URL** | http://www.promethee.com |
| **Licence** | Accès sous accord (Entente Forêt Méditerranéenne) — données publiques agrégées |
| **Couverture spatiale** | France méditerranéenne (15 départements du Sud-Est) |
| **Couverture temporelle** | 1973-présent |
| **Résolution spatiale** | Polygone d'incendie (surface brûlée) |
| **Résolution temporelle** | Événementielle (chaque incendie) |
| **Format** | CSV, Shapefile |
| **Version référencée** | Base Prométhée (extraction datée) |
| **Qualité / précision** | Saisie opérationnelle (services départementaux incendie) |
| **Contact** | Entente pour la Forêt Méditerranéenne — base Prométhée |
| **Statut d'ingestion** | Planifié (accord d'accès à formaliser) |
| **Notes** | Source historique de référence pour l'analyse de la fréquence et de la surface des incendies en zone méditerranéenne française |

#### DS-023 — EFFIS (European Forest Fire Information System)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-023 |
| **Nom du dataset** | EFFIS — European Forest Fire Information System |
| **Organisme producteur** | Commission européenne — Joint Research Centre (JRC) |
| **Catégorie** | F — Incendie |
| **Domaines S-6 couverts** | Écologie forestière (incendie) |
| **Moteurs consommateurs** | Ignis, Simulation Engine |
| **Source / URL** | https://effis.jrc.ec.europa.eu |
| **Licence** | Licence Ouverte EU (CC-BY 4.0 — Commission européenne) |
| **Couverture spatiale** | Europe (Espace économique européen + pays méditerranéens) |
| **Couverture temporelle** | 2000-présent |
| **Résolution spatiale** | Module rapide : 250 m (MODIS) ; cartographie brûlé : 20 m (Sentinel-2) |
| **Résolution temporelle** | Quotidienne (détection) ; saisonnière (cartographie brûlé) |
| **Format** | Shapefile, GeoTIFF, API EFFIS |
| **Version référencée** | EFFIS courant (extraction datée) |
| **Qualité / précision** | Validation JRC ; croisement satellite et données nationales |
| **Contact** | JRC — unité Forest Fires |
| **Statut d'ingestion** | Planifié |
| **Notes** | Cadre européen de référence ; permet la comparaison France / pays méditerranéens voisins |

#### DS-024 — MODIS / FIRMS (détection active fire)

| Champ | Valeur |
|---|---|
| **Identifiant GSIE** | DS-024 |
| **Nom du dataset** | FIRMS — Fire Information for Resource Management System |
| **Organisme producteur** | NASA (MODIS, VIIRS) — FIRMS (University of Maryland / NASA) |
| **Catégorie** | F — Incendie |
| **Domaines S-6 couverts** | Écologie forestière (incendie) |
| **Moteurs consommateurs** | Ignis, Simulation Engine |
| **Source / URL** | https://firms.modaps.eosdis.nasa.gov |
| **Licence** | Domaine public (NASA data policy) |
| **Couverture spatiale** | Mondiale |
| **Couverture temporelle** | 2000-présent (MODIS), 2012-présent (VIIRS) |
| **Résolution spatiale** | MODIS : 1 km ; VIIRS : 375 m |
| **Résolution temporelle** | Quasi temps réel (plusieurs passages par jour) |
| **Format** | CSV, Shapefile, GeoJSON, flux temps réel |
| **Version référencée** | Collection 6 (MODIS), VIIRS courant |
| **Qualité / précision** | Détection active (faux positifs possibles — à filtrer) |
| **Contact** | NASA FIRMS |
| **Statut d'ingestion** | Planifié (prioritaire Ignis) |
| **Notes** | Détection d'incendies actifs en quasi temps réel ; entrée critique pour le suivi opérationnel Ignis |

---

## 4. Priorité d'ingestion

La priorité d'ingestion des datasets est alignée sur l'ordre de
développement des moteurs (livrable 204 — `ENGINE_DEVELOPMENT_ORDER.md`)
et sur le plan de sourcing (livrable 307 — `SOURCING_PLAN.md`). Les
datasets sont ingérés par vagues, en cohérence avec les vagues de
moteurs qui les consomment.

### 4.1 Vague 0 — Fondations (préalables)

| Priorité | Dataset | Justification |
|---|---|---|
| P0 | DS-016 BDNFF | Backbone taxonomique de l'ontologie forestière (livrable 303) — requis avant tout moteur |
| P0 | DS-017 INPN / TAXREF | Référentiel taxonomique national — complément du BDNFF pour l'ontologie |

### 4.2 Vague 1 — Evidence & Knowledge

| Priorité | Dataset | Justification |
|---|---|---|
| P1 | DS-006 INRAE SOERE F-ORE-T | Données expérimentales peer-reviewed — alimentent directement Knowledge avec niveau de preuve A/B |
| P1 | DS-003 IGN IFN | Données dendrométriques nationales — base de calibration des modèles |

### 4.3 Vague 2 — Moteurs domaine (GIS, Botanical, Pedology, Climate)

| Priorité | Dataset | Moteur cible | Justification |
|---|---|---|---|
| P2 | DS-001 BD Forêt v2 | GIS Engine | Couverture forestière de référence — socle géospatial |
| P2 | DS-002 IGN LiDAR HD | GIS Engine | MNT et canopée — données structurantes pour GIS et Forest Dynamics |
| P2 | DS-004 BD Ortho | GIS Engine | Imagerie de validation |
| P2 | DS-014 GBIF | Botanical Engine | Occurrences taxonomiques |
| P2 | DS-015 Tela Botanica | Botanical Engine | Observations flore française |
| P2 | DS-005 ONF RPF | Pedology Engine | Référentiel pédologique forestier (en quarantaine — licence à formaliser) |
| P2 | DS-011 BDAT | Pedology Engine | Analyses de terre nationales |
| P2 | DS-013 SoilGrids | Pedology Engine | Couverture mondiale complémentaire |
| P2 | DS-007 Safran | Climate Engine | Réanalyse quotidienne française |
| P2 | DS-010 Météo-France obs | Climate Engine | Observations sol de validation |

### 4.4 Vague 3 — Correlation & Reasoning

| Priorité | Dataset | Justification |
|---|---|---|
| P3 | DS-012 RPFR | Affine les croisements pédologie / station (en quarantaine) |
| P3 | DS-018 Sentinel-2 | Télédétection pour les corrélations multi-domaines |

### 4.5 Vague 4 — Diagnostic & Forest Dynamics

| Priorité | Dataset | Moteur cible | Justification |
|---|---|---|---|
| P4 | DS-019 Sentinel-1 | Forest Dynamics Engine | Biomasse radar |
| P4 | DS-020 Landsat 8/9 | Forest Dynamics Engine | Série longue |
| P4 | DS-021 MODIS | Forest Dynamics Engine | Phénologie globale |

### 4.6 Vague 5 — Simulation (projections long terme)

| Priorité | Dataset | Moteur cible | Justification |
|---|---|---|---|
| P5 | DS-008 DRIAS | Simulation Engine | Projections climatiques 2100 |
| P5 | DS-009 ARPEGE/AROME | Simulation Engine / Ignis | Météo opérationnelle |

### 4.7 Ignis (transverse, priorité haute sur le périmètre incendie)

| Priorité | Dataset | Justification |
|---|---|---|
| PI | DS-022 Prométhée | Historique incendies méditerranéens |
| PI | DS-023 EFFIS | Cadre européen incendie |
| PI | DS-024 MODIS/FIRMS | Détection temps réel |

> **Note :** la priorité PI (Ignis) est traitée en parallèle des
> vagues principales car Ignis est un jumeau numérique à
> pipeline partiellement autonome (voir `04_ARCHITECTURE/GSIE_IGNIS_*`).

---

## 5. Notes sur les licences

Le respect des licences est un garde-fou constitutionnel (CON-005)
et juridique (`19_LEGAL/`). Le tableau ci-dessous récapitule les
licences effectivement appliquées par les producteurs des datasets
catalogués.

### 5.1 Licence Ouverte 2.0 (etalab-2.0)

| Dataset | Producteur |
|---|---|
| DS-001 BD Forêt v2 | IGN |
| DS-002 IGN LiDAR HD | IGN |
| DS-003 IGN IFN | IGN |
| DS-004 BD Ortho | IGN |
| DS-008 DRIAS | Météo-France |
| DS-011 BDAT | INRAE / GIS Sol |
| DS-017 INPN | MNHN |

**Conditions :** réutilisation libre, y compris commerciale, avec
mention de la source. Pas de restriction de modification. Exigence
de paternité.

### 5.2 ODbL (Open Database License)

Aucun dataset du catalogue courant n'est sous ODbL strict. Cette
licence reste néanmoins référencée car certains jeux dérivés (ex.
OpenStreetMap) pourraient être intégrés ultérieurement. L'ODbL
impose le partage à l'identique des bases dérivées.

### 5.3 CC-BY 4.0

| Dataset | Producteur |
|---|---|
| DS-013 SoilGrids | ISRIC |
| DS-018 Sentinel-2 | ESA / Copernicus |
| DS-019 Sentinel-1 | ESA / Copernicus |
| DS-023 EFFIS | Commission européenne (JRC) |

**Conditions :** réutilisation avec paternité. Pas de restriction
commerciale pour CC-BY 4.0. Modifications autorisées sous même
licence (CC-BY-SA pour Tela Botanica, DS-015).

### 5.4 Domaine public

| Dataset | Producteur |
|---|---|
| DS-020 Landsat 8/9 | USGS / NASA |
| DS-021 MODIS | NASA |
| DS-024 MODIS/FIRMS | NASA |

**Conditions :** aucune restriction. Mention de source recommandée
mais non exigée.

### 5.5 Accords spécifiques / restrictions

| Dataset | Producteur | Restriction |
|---|---|---|
| DS-005 ONF RPF | ONF / INRAE | Accord ONF à formaliser — diffusion interne |
| DS-006 INRAE SOERE F-ORE-T | INRAE | Data policy SOERE — accès sur demande |
| DS-007 Safran | Météo-France | Données brutes sous accord ; produits dérivés en Licence Ouverte |
| DS-009 ARPEGE/AROME | Météo-France | Archivage sous accord |
| DS-012 RPFR | ONF / INRAE | Accord ONF à formaliser |
| DS-014 GBIF | GBIF | Licence variable par occurrence (CC-BY, CC0, CC-BY-NC) |
| DS-015 Tela Botanica | Tela Botanica | CC-BY-SA (partage à l'identique) |
| DS-022 Prométhée | Entente Forêt Méditerranéenne | Accès sous accord |

> **Règle de conformité :** tout dataset sous accord spécifique
> (DS-005, DS-006, DS-007, DS-009, DS-012, DS-022) est mis en
> quarantaine jusqu'à formalisation du partenariat (`20_PARTNERSHIPS/`)
> et validation juridique (`19_LEGAL/`). Aucune ingestion n'a lieu
> avant l'accord écrit.

### 5.6 Vérification par occurrence

Pour les datasets agrégeant des contributions multiples (GBIF, Tela
Botanica), la licence doit être vérifiée **par enregistrement**.
GSIE filtre les occurrences selon leur licence et exclut les
contributions sous licence restrictive (CC-BY-NC) pour les usages
qui l'exigent.

---

## 6. Historique

| Date | Événement |
|---|---|
| 2026-07-13 | Création du livrable 305 — Dataset Catalog (Draft). Catalogage de 24 datasets répartis en 6 catégories (A-F), alignés sur les 14 moteurs et Ignis. Métadonnées complètes conformes à CON-002 et CON-005. Priorité d'ingestion alignée sur l'ordre de développement des moteurs (livrable 204). Notes de licences détaillées (Licence Ouverte, CC-BY, domaine public, accords spécifiques). |

---

## Références

- `00_CONSTITUTION/GSIE-CON-002.md` — La science avant tout
- `00_CONSTITUTION/GSIE-CON-005.md` — Toute connaissance doit être traçable
- `00_CONSTITUTION/SCIENTIFIC_CONSTITUTION.md` — Articles S-1 (Sources acceptées) à S-7 (Patrimoine scientifique)
- `01_DIRECTIVES/ACTIVE/GSIE-DIR-0007.md` — Lancement officiel de la Phase 3
- `04_ARCHITECTURE/ENGINE_DEVELOPMENT_ORDER.md` — Ordre de développement des moteurs (livrable 204)
- `06_RESEARCH/RESEARCH_METHOD.md` — Méthode de recherche (livrable 301)
- `07_KNOWLEDGE/KNOWLEDGE_METHOD.md` — Méthode de connaissance (livrable 302)
- `07_KNOWLEDGE/FOREST_ONTOLOGY.md` — Ontologie forestière (livrable 303)
- `19_LEGAL/` — Conformité des licences
- `20_PARTNERSHIPS/` — Formalisation des accords producteurs

---

> **Statut : Draft** — Ce livrable est en cours de rédaction. Il ne
> passe en Review qu'après validation interne et conformément à
> l'ordre des livrables défini par `GSIE-DIR-0007`.

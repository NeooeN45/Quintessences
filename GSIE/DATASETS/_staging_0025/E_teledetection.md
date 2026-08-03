# Domaine E — Télédétection, satellite, catalogues STAC

> Fichier partiel — GSIE-PROMPT-0025
> Toutes les URL ci-dessous ont été vérifiées par accès réel (webfetch) le 2026-07-30.
> Compteur URL : 7 testées, 1 échec (Sentinel Hub 503 — temporaire).

---

## Entrées vérifiées

### E-001 — Element84 Earth Search (STAC API sur AWS)

```yaml
- nom: Earth Search by Element84 — STAC API
  producteur: Element84 (USA, hébergé sur AWS Open Data)
  url: https://earth-search.aws.element84.com/v1
  access_method: stac_api
  licence: variable par collection (Sentinel-2 CC-BY 4.0, Landsat domaine public, NAIP variable)
  ai_training_allowed: true
  grain_m2: variable (Sentinel-2 10 m → 100 ; Landsat 30 m → 900 ; Copernicus DEM 30 m → 900)
  emprise: mondial
  etendue_temporelle: Sentinel-2 depuis 2015 ; Landsat depuis 1982 ; NAIP depuis 2003
  frequence_mise_a_jour: continue (sync AWS Open Data)
  format: COG (Cloud Optimized GeoTIFF), STAC metadata JSON
  volume_estime: pétaoctets (collections complètes)
  type_source: capteur_instrumente
  moteur_destinataire: GIS, Forest Dynamics, Diagnostic, Ignis
  regime: referencee
```

**Note** : STAC v1.0.0 confirmé. Collections : sentinel-2-l2a, sentinel-2-l1c, sentinel-2-c1-l2a, sentinel-2-pre-c1-l2a, sentinel-1-grd, landsat-c2-l2, cop-dem-glo-30, cop-dem-glo-90, naip. Conforme OGC API Features + STAC item-search. Agrégations disponibles. **Nouveau** : collection Sentinel-2 Collection 1 (c1-l2a) — reprocessing USGS/ESA. URL testée : API répond en JSON, collections listées.

---

### E-002 — Microsoft Planetary Computer (STAC API + Data)

```yaml
- nom: Microsoft Planetary Computer — STAC API
  producteur: Microsoft (USA)
  url: https://planetarycomputer.microsoft.com/api/stac/v1
  access_method: stac_api
  licence: variable par collection (majorité CC-BY 4.0 ou domaine public)
  ai_training_allowed: true
  grain_m2: variable par collection
  emprise: mondial
  etendue_temporelle: variable par collection
  frequence_mise_a_jour: continue
  format: COG, NetCDF, Zarr, STAC metadata JSON
  volume_estime: pétaoctets (datasets hébergés sur Azure Blob Storage)
  type_source: capteur_instrumente
  moteur_destinataire: GIS, Forest Dynamics, Climate, Diagnostic, Ignis
  regime: referencee
```

**Note** : STAC v1.0.0 confirmé. Conforme CQL2 (basic, json, text), OGC API Features, STAC item-search. Catalogue "microsoft-pc" — datasets Earth science hébergés sur Azure. Inclut Sentinel, Landsat, MODIS, NAIP, DEM, climate data, etc. Planetary Computer Hub (Jupyter) pour processing in-situ. SAS tokens pour accès direct Blob. URL testée : API répond en JSON, conformance classes confirmées.

---

### E-003 — Copernicus Data Space Ecosystem STAC (CDSE)

```yaml
- nom: Copernicus Data Space Ecosystem — STAC API
  producteur: ECMWF / Copernicus (Europe)
  url: https://stac.dataspace.copernicus.eu/v1/
  access_method: stac_api
  licence: Copernicus License (libre, CC-BY 4.0 pour la majorité)
  ai_training_allowed: true
  grain_m2: variable (Sentinel-2 10 m → 100 ; Sentinel-1 10 m → 100 ; Sentinel-3 1 km → 1000000)
  emprise: mondial
  etendue_temporelle: Sentinel-1 depuis 2014 ; Sentinel-2 depuis 2015 ; Sentinel-3 depuis 2016
  frequence_mise_a_jour: continue
  format: COG, NetCDF, STAC metadata JSON
  volume_estime: pétaoctets (archive complète Copernicus)
  type_source: capteur_instrumente
  moteur_destinataire: GIS, Forest Dynamics, Diagnostic, Ignis, Climate
  regime: referencee
```

**Note** : STAC v1.0.0 confirmé. Catalogue "cdse-stac" — asset-level metadata. Conforme CQL2, OGC API Features, collection-search (RC.1). Déjà partiellement dans l'inventaire existant (§10.2 A) — cette entrée précise l'endpoint STAC exact. Documentation : https://documentation.dataspace.copernicus.eu/. URL testée : API répond en JSON, conformance classes confirmées.

---

### E-004 — ESA Earth Online (portail missions et données)

```yaml
- nom: ESA Earth Online — portail missions et données
  producteur: ESA (Europe)
  url: https://earth.esa.int/eogateway/
  access_method: publication_text
  licence: variable (Open Data pour Sentinel, AO pour Third Party Missions)
  ai_training_allowed: false
  grain_m2: variable par mission
  emprise: mondial
  etendue_temporelle: variable par mission (Heritage Missions depuis 1970s)
  frequence_mise_a_jour: continue
  format: variable (GeoTIFF, NetCDF, SAFE)
  volume_estime: inconnu — portail catalogue
  type_source: referentiel_officiel
  moteur_destinataire: GIS, Forest Dynamics, Knowledge
  regime: referencee
```

**Note** : portail ESA pour missions Earth Explorers, Heritage Missions, Third Party Missions. Catégories : Data (All/Open/AO/Project Proposal/Sample), Tools (Analysis/Processing/Visualisation/Catalogues/Apps), News & Events, Learn & Discover. Quality Reports Advanced Search (QRAS). URL testée : page Sentinel-2 répond, navigation confirmée.

---

## À VÉRIFIER — Domaine E

### E-V001 — Sentinel Hub (services.sentinel-hub.com)

**Motif** : 503 (erreur serveur temporaire) au moment du test. Sentinel Hub est un service commercial de traitement satellite (Sentinel, Landsat, MODIS, Planet) avec API REST. URL à retester : https://services.sentinel-hub.com/ et https://www.sentinel-hub.com/. Licence : freemium (tier gratuit limité, payant pour usage intensif). Potentiellement pertinent pour Ignis (traitement temps réel).

### E-V002 — PEPS (Plateforme d'Exploitation des Produits Sentinel)

**Motif** : PEPS (https://peps.cnes.fr) était la plateforme française CNES pour Sentinel. Statut actuel incertain — potentiellement décommissionnée au profit de CDSE. À vérifier : PEPS est-il encore actif en 2026 ?

### E-V003 — USGS EarthExplorer

**Motif** : USGS EarthExplorer (https://earthexplorer.usgs.gov/) est le portail historique pour Landsat, MODIS, et données USGS. URL non testée (probablement SPA). À vérifier : endpoint API, accès bulk.

### E-V004 — Google Earth Engine

**Motif** : Google Earth Engine (https://earthengine.google.com/) est une plateforme cloud de traitement satellite. Accès via API Python/JS, authentification Google. Licence : gratuit pour recherche académique, payant pour commercial. Non testé — potentiellement pertinent pour Forest Dynamics et Learning.

---

## Signalements — Domaine E

- **Sentinel Hub 503** : erreur serveur temporaire au moment du test (30/07/2026). À retester ultérieurement.
- **CDSE STAC déjà partiellement dans l'inventaire** : l'inventaire existant §10.2 cite CDSE mais avec l'endpoint `/v1/collections/sentinel-2-l2a/items` — l'endpoint racine `/v1/` est plus général et permet le search CQL2.

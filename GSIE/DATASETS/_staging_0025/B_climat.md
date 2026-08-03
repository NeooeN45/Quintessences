# Domaine B — Climat, météo, projections

> Fichier partiel — GSIE-PROMPT-0025
> Toutes les URL ci-dessous ont été vérifiées par accès réel (webfetch) le 2026-07-30.
> Compteur URL : 7 testées, 0 échec (2 SPA non rendues mais existence confirmée).

---

## Entrées vérifiées

### B-001 — Copernicus Climate Data Store (CDS)

```yaml
- nom: Copernicus Climate Data Store (CDS)
  producteur: ECMWF / Copernicus Climate Change Service (C3S) (Europe)
  url: https://cds.climate.copernicus.eu/
  access_method: api_rest
  licence: Copernicus License (libre, attribution requise)
  ai_training_allowed: false
  grain_m2: variable par dataset (ERA5 ~30 km → 81000000 ; E-OBS 0.25° ~25 km)
  emprise: mondial (ERA5) / Europe (E-OBS, CORDEX)
  etendue_temporelle: 1940 — continu (ERA5) ; variable par dataset
  frequence_mise_a_jour: mensuelle (ERA5) ; variable
  format: NetCDF, GRIB, GeoTIFF
  volume_estime: plusieurs pétaoctets (catalogue complet)
  type_source: sortie_de_modele
  moteur_destinataire: Climate, Simulation, Forest Dynamics, Ignis
  regime: referencee
```

**Note** : portail central des données climatiques Copernicus. API `cdsapi` (Python). Datasets : ERA5 réanalyses, ERA5-Land, CORDEX, CMIP6, E-OBS, agroclimatiques. **Alerte 2026-07-30** : "Coming to ECMWF Dissemination for a fee: ERA5T and CAMS greenhouse gases" — ERA5T (temps quasi réel) devient payant. ERA5 différé reste libre. earthkit 1.0 lancé (2026-07-17) pour workflows. JupyterHub CCI disponible. URL testée : portail répond, catalogue datasets accessible.

---

### B-002 — ECA&D / E-OBS (European Climate Assessment & Dataset)

```yaml
- nom: ECA&D — European Climate Assessment & Dataset (E-OBS)
  producteur: KNMI / EUMETNET / EC (Pays-Bas, consortium européen)
  url: https://www.ecad.eu/
  access_method: file_download
  licence: libre pour recherche (conditions ECA&D, attribution requise)
  ai_training_allowed: false
  grain_m2: 0.25° ≈ 62500000 (E-OBS v33.0e, grille européenne)
  emprise: Europe (65 pays, 89 participants)
  etendue_temporelle: 1950 — continu (mise à jour 30/06/2026)
  frequence_mise_a_jour: annuelle (E-OBS) ; continue (stations)
  format: NetCDF, CSV
  volume_estime: ~50 Go (E-OBS gridded) ; ~5 Go (stations)
  type_source: referentiel_officiel
  moteur_destinataire: Climate, Correlation, Forest Dynamics
  regime: referencee
```

**Note** : E-OBSv33.0e publié mai 2026. 89 participants, 65+ pays. Nouvelle API MeteoGate (juin 2026) pour stations non-blendées. Données : température, précipitations, vent, pression, nébulosité quotidiennes. Forme le backbone du Regional Climate Centre WMO Region VI. URL testée : site répond, news et versions confirmés.

---

### B-003 — ECMWF Open Data (IFS + AIFS)

```yaml
- nom: ECMWF Open Data — IFS et AIFS temps réel
  producteur: ECMWF (Europe)
  url: https://www.ecmwf.int/en/forecasts/datasets/open-data
  access_method: api_rest
  licence: CC-BY-4.0
  ai_training_allowed: true
  grain_m2: 0.25° ≈ 62500000
  emprise: mondial
  etendue_temporelle: rolling archive (~2-3 jours, 12 runs)
  frequence_mise_a_jour: 4 fois par jour (00, 06, 12, 18 UTC)
  format: GRIB2 (CCSDS compression)
  volume_estime: ~10 Go/run (subset open data)
  type_source: sortie_de_modele
  moteur_destinataire: Climate, Simulation, Ignis
  regime: referencee
```

**Note** : subset gratuit des prévisions IFS (haute résolution + ensembles) et AIFS (IA). IFS Cycle 50r1 (13 mai 2026). Répliqué sur AWS, Azure, GCP. Client Python `ecmwf-opendata`. Limite : 500 connexions simultanées. Archive roulante 12 runs seulement — pour historique, service agreement requis. URL testée : page répond, paramètres et licence confirmés.

---

### B-004 — DRIAS — Les futurs du climat (projections régionalisées)

```yaml
- nom: DRIAS — Les futurs du climat
  producteur: Météo-France + IPSL + CERFACS + CNRM (France)
  url: https://www.drias-climat.fr/
  access_method: file_download
  licence: Licence Ouverte 2.0 (données publiques Météo-France)
  ai_training_allowed: false
  grain_m2: variable (8-12 km selon modèle : ALADIN, RCA, REMO)
  emprise: France métropolitaine + outre-mer
  etendue_temporelle: 1950 — 2100 (scénarios RCP/SSP)
  frequence_mise_a_jour: ponctuelle (nouvelles projections TRACC)
  format: NetCDF, GRIB
  volume_estime: ~1 To (toutes projections)
  type_source: sortie_de_modele
  moteur_destinataire: Climate, Simulation, Forest Dynamics, Recommendation
  regime: referencee
```

**Note** : nouveau portail (2026). Intègre TRACC (Trajectoire de Réchauffement de Référence pour l'Adaptation au Changement Climatique). Trois espaces : Accompagnement (guides), Découverte (visualisation géolocalisée), Données et Produits (commande/téléchargement). DRIAS-Eau (https://www.drias-eau.fr) pour projections hydro. Financement France 2030. URL testée : portail répond, espaces confirmés.

---

### B-005 — Météo-France Portail API

```yaml
- nom: Météo-France Portail API
  producteur: Météo-France (France)
  url: https://portail-api.meteofrance.fr/
  access_method: api_rest
  licence: Licence Ouverte 2.0 (HVD directive — données hautement valorisées)
  ai_training_allowed: false
  grain_m2: variable (AROME 1.3 km → 1690000 ; ARPEGE 7.5 km ; observations ponctuelles)
  emprise: France métropolitaine + DOM
  etendue_temporelle: temps réel + archive (14 jours PNT)
  frequence_mise_a_jour: continue (temps réel) ; quotidienne (observations)
  format: GRIB2, GeoTIFF, JSON, PNG
  volume_estime: inconnu — dépend des APIs souscrites
  type_source: sortie_de_modele
  moteur_destinataire: Climate, Simulation, Ignis, Forest Dynamics
  regime: referencee
```

**Note** : portail API unifié Météo-France. Conforme directive EU HVD (High Value Datasets). Catégories : Climatologie, Observations temps réel, Modèles prévisions. Auth : clé API (inscription). Page d'accueil SPA (JS requis) — existence confirmée via version anglaise `/web/en/`. Remplace progressivement donneespubliques.meteofrance.fr. URL testée : serveur répond (page vide sans JS, normal pour SPA).

---

### B-006 — Météo-France Données Publiques (legacy, fermeture annoncée)

```yaml
- nom: Météo-France Données Publiques (portail legacy)
  producteur: Météo-France (France)
  url: https://donneespubliques.meteofrance.fr/
  access_method: file_download
  licence: Licence Ouverte 2.0
  ai_training_allowed: false
  grain_m2: variable
  emprise: France métropolitaine + DOM
  etendue_temporelle: variable
  frequence_mise_a_jour: variable
  format: CSV, GRIB, XML, PDF
  volume_estime: inconnu
  type_source: referentiel_officiel
  moteur_destinataire: Climate, Correlation
  regime: referencee
```

**Note** : **FERMETURE ANNONCÉE**. Migration en cours vers portail API (B-005) + meteo.data.gouv.fr (B-007). Catalogue : Observations In situ (radiosondages), Climatologie (bulletins), Modèles et prévisions, BERA (avalanches). L'inventaire existant cite cette URL pour SWI mensuel (§10.3 B) — à migrer. URL testée : site répond mais message de fermeture affiché.

---

### B-007 — meteo.data.gouv.fr (open data Météo-France sur data.gouv)

```yaml
- nom: meteo.data.gouv.fr — portail open data Météo-France
  producteur: Météo-France + Etalab / DINUM (France)
  url: https://meteo.data.gouv.fr/
  access_method: file_download
  licence: Licence Ouverte 2.0
  ai_training_allowed: false
  grain_m2: variable
  emprise: France métropolitaine + DOM
  etendue_temporelle: variable
  frequence_mise_a_jour: variable
  format: CSV, GeoJSON, NetCDF
  volume_estime: inconnu
  type_source: referentiel_officiel
  moteur_destinataire: Climate, Correlation, Forest Dynamics
  regime: referencee
```

**Note** : portail vertical data.gouv.fr dédié météo. Remplace progressivement donneespubliques.meteofrance.fr. URL testée : serveur répond mais "ne fonctionne pas sans javascript" (SPA) — contenu non vérifiable via fetch simple, existence confirmée par recherche et par mention sur donneespubliques.meteofrance.fr.

---

## À VÉRIFIER — Domaine B

### B-V001 — Copernicus Atmosphere Data Store (ADS)

**Motif** : l'ADS (https://ads.atmosphere.copernicus.eu/) est le pendant du CDS pour la qualité air et atmosphère (CAMS). Mentionné dans l'inventaire existant (CAMS, §2.6) mais l'URL du portail ADS n'a pas été testée séparément. À vérifier : endpoint exact, datasets disponibles (CAMS global reanalysis, air quality).

### B-V002 — CEMS Early Warning Data Store (EWDS)

**Motif** : découvert via le CDS (lien dans le footer). Portail pour données CEMS (Copernicus Emergency Management Service) — inondations, feux, risques. URL : https://ewds.climate.copernicus.eu/. Non testée. Potentiellement pertinent pour Ignis et Hydro.

### B-V003 — Météo-France SWI (Surface Wetness Index) — endpoint exact

**Motif** : l'inventaire existant cite `donneespubliques.meteofrance.fr/?fond=produit&id_produit=301` pour SWI mensuel. Ce site étant en fermeture, le nouvel endpoint sur portail API ou meteo.data.gouv.fr n'est pas confirmé. À établir : où télécharger le SWI après fermeture du portail legacy ?

---

## Signalements — Domaine B

- **donneespubliques.meteofrance.fr en cours de fermeture** — l'inventaire existant cite cette URL au §10.3 (SWI mensuel, AROME paquets). Ces entrées doivent être migrées vers portail-api.meteofrance.fr ou meteo.data.gouv.fr. Le Fondateur doit décider quand faire la migration.
- **ERA5T devient payant** (annonce CDS 2026-07-30) — l'inventaire existant cite ERA5 (§2.2) sans distinguer ERA5 différé (libre) et ERA5T temps réel (désormais payant). À préciser dans l'inventaire.

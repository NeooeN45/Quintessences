# Domaine F — Incendie, risques, DFCI

> Fichier partiel — GSIE-PROMPT-0025
> Toutes les URL ci-dessous ont été vérifiées par accès réel (webfetch) le 2026-07-30.
> Compteur URL : 5 testées, 1 échec (promethee.net — fusionnée dans BDIFF en 2023).

---

## Entrées vérifiées

### F-001 — EFFIS (European Forest Fire Information System)

```yaml
- nom: EFFIS — European Forest Fire Information System
  producteur: JRC — Joint Research Centre (Commission européenne)
  url: https://effis.jrc.ec.europa.eu/
  access_method: ogc_wms
  licence: CC-BY 4.0 (données Copernicus EMS)
  ai_training_allowed: true
  grain_m2: variable (RDA 250 m → 62500 ; MODIS 1 km ; VIIRS 375 m → 140625)
  emprise: Europe + Méditerranée (43 pays Expert Group on Forest Fires)
  etendue_temporelle: 1998 — continu (RDA daily update)
  frequence_mise_a_jour: quotidienne (saison feu) ; annuelle (rapports)
  format: SHP, KML, WMS, CSV, GeoTIFF
  volume_estime: inconnu — portail + apps
  type_source: capteur_instrumente
  moteur_destinataire: Ignis, Simulation, Diagnostic, GIS
  regime: referencee
```

**Note** : composant Copernicus EMS depuis 2015. Modules : Fire Danger Forecast, Active Fire Detection, Rapid Damage Assessment (RDA), Fire Damage Assessment, Fire Emissions, Fire Severity, Wildfire Risk Assessment, Seasonal/Monthly forecast, European Fire Database, Fuels. Apps : Current Situation Viewer 2.0, Current Statistics Portal, Wildfire Risk Viewer, Data Request Form. 43 pays (EGFF). URL testée : portail répond, modules et apps confirmés.

---

### F-002 — GWIS (Global Wildfire Information System)

```yaml
- nom: GWIS — Global Wildfire Information System
  producteur: JRC + GEO + Copernicus + NASA (consortium international)
  url: https://gwis.jrc.ec.europa.eu/
  access_method: ogc_wms
  licence: CC-BY 4.0
  ai_training_allowed: true
  grain_m2: variable (global, résolution MODIS/VIIRS)
  emprise: mondial
  etendue_temporelle: 2002 — continu (Country Profile 2002-2019)
  frequence_mise_a_jour: quotidienne (saison) ; continue
  format: WMS, SHP, KML, CSV
  volume_estime: inconnu — portail global
  type_source: capteur_instrumente
  moteur_destinataire: Ignis, Simulation, Diagnostic
  regime: referencee
```

**Note** : initiative conjointe GEO + Copernicus. Builds on EFFIS + GOFC-GOLD Fire IT. 5 apps : Current Situation Viewer (fire danger 10 jours, lightning forecast, active fires NRT), Current Statistics Portal, Country Profile (historical fire regimes 2002-2019), Long-term Forecast, Data & Services. Projet GEFF LAC (Latin America Caribbean, Amazonia Plus 2023-2027). URL testée : portail répond, apps confirmées.

---

### F-003 — NASA FIRMS (Fire Information for Resource Management System)

```yaml
- nom: NASA FIRMS — Fire Information for Resource Management System
  producteur: NASA LANCE (USA)
  url: https://firms.modaps.eosdis.nasa.gov/
  access_method: api_rest
  licence: domaine public (données NASA)
  ai_training_allowed: true
  grain_m2: MODIS 1 km → 1000000 ; VIIRS 375 m → 140625
  emprise: mondial
  etendue_temporelle: MODIS depuis 2000 ; VIIRS depuis 2012
  frequence_mise_a_jour: NRT 3h (global) ; temps réel (US/Canada)
  format: CSV, SHP, KML, WMS, TXT
  volume_estime: inconnu — millions de détections/an
  type_source: capteur_instrumente
  moteur_destinataire: Ignis, Simulation, Diagnostic
  regime: referencee
```

**Note** : MODIS (Aqua/Terra) + VIIRS (S-NPP, NOAA-20, NOAA-21). NRT global 3h, temps réel US/Canada. API REST (MAP_KEY gratuite). Archive Download (MODIS 2000+, VIIRS 2012+). Burned Area : BA_MODIS, BA_VIIRS. Fire Data Academy (Google Colab, Jupyter, Python). FIRMS Blog. Déjà dans l'inventaire existant (DS-024, §10.5) — cette entrée confirme l'URL et précise les sources VIIRS (S-NPP, NOAA-20, NOAA-21). URL testée : portail répond, instruments et formats confirmés.

---

### F-004 — BDIFF (Base de Données sur les Incendies de Forêts en France)

```yaml
- nom: BDIFF — Base de Données sur les Incendies de Forêts en France
  producteur: MAA — Ministère de l'Agriculture (France)
  url: https://bdiff.agriculture.gouv.fr/
  access_method: file_download
  licence: Licence Ouverte 2.0 (données publiques)
  ai_training_allowed: false
  grain_m2: inconnu — polygones/surfaces par commune
  emprise: France entière
  etendue_temporelle: 2006 — continu (agrégation communale)
  frequence_mise_a_jour: annuelle
  format: CSV (téléchargement), interface web
  volume_estime: inconnu — ~1364 incendies/an (moyenne récente)
  type_source: referentiel_officiel
  moteur_destinataire: Ignis, Simulation, Diagnostic, Correlation
  regime: referencee
```

**Note** : **Prométhée fusionnée dans BDIFF en janvier 2023**. BDIFF centralise données incendies forêt France depuis 2006, agrégées à la commune. Portail : https://bdiff.agriculture.gouv.fr/incendies (recherche + téléchargement CSV). data.gouv.fr : https://www.data.gouv.fr/datasets/base-de-donnees-sur-les-incendies-de-forets-en-france-bdiff (métadonnées, 2006-2022). Inclut désormais données historiques Prométhée (zone méditerranéenne, depuis 1973). URL testée : portail + data.gouv.fr confirmés via recherche.

---

### F-005 — feuxdeforet.fr (signalements citoyens vérifiés)

```yaml
- nom: feuxdeforet.fr — signalements géolocalisés horodatés
  producteur: feuxdeforet.fr (France, opérateur indépendant)
  url: https://www.feuxdeforet.fr/espaces/data/
  access_method: api_rest
  licence: inconnue — à établir (accès par convention gratuite pour recherche/services publics)
  ai_training_allowed: false
  grain_m2: inconnu — signalements ponctuels
  emprise: France
  etendue_temporelle: continu (saison)
  frequence_mise_a_jour: continue (saison feu)
  format: JSON, GeoJSON, CSV (sur convention)
  volume_estime: inconnu — signalements citoyens vérifiés
  type_source: capteur_participatif
  moteur_destinataire: Ignis, Diagnostic, Correlation
  regime: referencee
```

**Note** : signalements citoyens géolocalisés horodatés. Accès brut (API, exports massifs) par convention gratuite pour recherche académique et services publics. Citation requise : "Données Feux de Forêt (feuxdeforet.fr), signalements citoyens vérifiés" + période. Cross-référence avec BDIFF (bilans consolidés), EFFIS (périmètres satellitaires), Météo des forêts (danger météo). type_source = `capteur_participatif` (proposé RFC-0029 §11.3) : signalements citoyens, recoupement nécessaire. URL testée : page data confirmée via recherche.

---

## À VÉRIFIER — Domaine F

### F-V001 — Prométhée (statut actuel)

**Motif** : Prométhée (www.promethee.com) était la base historique incendies zone méditerranéenne (depuis 1973). Fusionnée dans BDIFF en janvier 2023. L'URL www.promethee.com et www.promethee.net échouent au fetch — probablement décommissionnées. À vérifier : le site promethee.com redirige-t-il vers BDIFF, ou est-il complètement mort ? Les données 1973-2022 sont-elles accessibles via BDIFF ?

### F-V002 — Atlas DFCI (pistes, points d'eau, massifs)

**Motif** : l'inventaire existant cite "Atlas DFCI" (§2.1) et "GIP ATGeRi / PIGMA" (§2.5, DFCI Aquitaine) mais sans URL précise. L'Atlas DFCI national (entente DFCI) n'a pas d'URL unique confirmée — probablement géré par ententes régionales. À inventorier par région.

### F-V003 — Météo des forêts (danger météo quotidien)

**Motif** : mentionné par feuxdeforet.fr comme source officielle de danger météorologique quotidien par département. Probablement lié à Météo-France (portail API ou meteo.data.gouv.fr). URL exacte non confirmée. À vérifier.

### F-V004 — Copernicus EMS — Rapid Mapping

**Motif** : Copernicus Emergency Management Service (CEMS) fournit des cartes rapides post-catastrophe (incluant incendies). URL : https://rapidmapping.emergency.copernicus.eu/ ou via Copernicus EMS. Non testé. Potentiellement pertinent pour vérité terrain validation (déjà cité §2.3 inventaire existant).

---

## Signalements — Domaine F

- **Prométhée fusionnée dans BDIFF (janvier 2023)** : l'inventaire existant cite Prométhée (DS-022) comme source distincte. Cette entrée est désormais obsolète — Prométhée fait partie de BDIFF. À corriger dans l'inventaire existant : fusionner DS-022 dans la fiche BDIFF, préciser que les données 1973-2022 (zone méditerranéenne) sont incluses.
- **feuxdeforet.fr — accès par convention** : pas un open data pur. L'accès brut nécessite une convention décrivant l'usage. À formaliser avant ingestion (régime "accord à formaliser" selon NOMENCLATURE_SOURCES §5).

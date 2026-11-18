# Horizon technologique scientifique de Quintessences

| Champ | Valeur |
|---|---|
| **Statut** | Registre R&D — Draft |
| **Méthode** | Faits vérifiés, puis inférences et propositions d'intégration |
| **Date** | 2026-08-18 |

## 1. Règles de classement

Une technologie est classée selon :

- potentiel de rupture : 25 % ;
- adéquation Quintessences : 20 % ;
- R&D économisée : 15 % ;
- maturité : 10 % ;
- intégrabilité : 10 % ;
- qualité scientifique : 10 % ;
- licence/coût/souveraineté : 10 %.

Le score est un outil de priorisation, jamais une preuve scientifique.

```text
ADOPT      intégration directe après validation locale
ADAPT      wrapper, fork ou calibration nécessaires
LEARN      architecture réutilisable conceptuellement
WATCH      prometteur mais verrou important
REJECT     contradiction dure, licence ou absence de valeur
```

## 2. Synthèse par domaine

| Domaine | Candidat pivot | Action initiale | Pourquoi | Verrou |
|---|---|---|---|---|
| Atmos | WeatherNext 2 | ADOPT comme flux provider | prévision globale probabiliste, flux GCS/BigQuery/Earth Engine | accès, termes temps réel, résolution globale |
| Atmos régional | ECMWF HRES/ENS + Météo-France | ADOPT comme références | source opérationnelle et comparaison française | contrats et harmonisation |
| Incendie | ForeFire / ELMFIRE | ADAPT/BENCHMARKER | moteurs physiques/modulaires existants | licences, calibration française |
| Feu GPU | PyTorchFire | LEARN/BENCHMARKER | accélération et différentiabilité | validation scientifique et domaine |
| Hydrologie | airGR | ADAPT | expertise INRAE et adéquation France | wrapper R, GPL-2 |
| Hydrologie ML | NeuralHydrology | ADAPT | model zoo et architecture modulaire | calibration bassins français |
| Hydrologie opérationnelle | LISFLOOD/GloFAS | ADAPT | chaîne Copernicus distribuée | intégration et domaine |
| EO | Prithvi-EO-2.0 | ADOPT après benchmark | institutionnel, multi-temporel, modèles ouverts | shift territorial |
| EO multimodal | AnySat | BENCHMARKER | résolution/modalité adaptatives | datasets et base model |
| EO embeddings | TESSERA | ADOPT après benchmark | temporel S1/S2, embeddings permissifs | validation forêt française |
| EO produits | SatlasPretrain | ADAPT | labels et backbone multi-capteurs | biais géographiques et ODC-BY |
| Forêt RGB | DeepForest | ADAPT | package mature pour houppiers | corpus français |
| Forêt LiDAR | TreeLearn | BENCHMARKER | segmentation individuelle | coût RAM/VRAM, domaine Wytham |
| Biomasse | GEDI | ADOPT comme dataset | LiDAR spatial et incertitude | couverture 51.6°N/S |
| Botanique | BioCLIP | ADAPT | représentation taxonomique | biais citizen science, validation locale |
| Faune caméra | SpeciesNet/PyTorch-Wildlife | ADAPT | pipeline de détection/classification | licences checkpoint et biais |
| Bioacoustique | BirdNET | ADOPT après contrôle | edge CPU, outil mature | couverture acoustique française |
| Sols | SoilGrids/OpenLandMap | ADOPT comme a priori | cartes et incertitudes | résolution/biais, jamais vérité parcelle |
| Sols profils | WoSIS/LUCAS | ADOPT comme corpus | validation et calibration | droits par provider |
| Drones | SLAM/TreeLearn/EO | WATCH/BENCHMARKER | perception et reconstruction | hardware, codes fragmentés |
| Simulation | WildFireGS | WATCH | lien scène 3D et feu | pas de code/licence stable |
| R&D transverse | GSIE-Bench | ADOPT | conditionne les choix de modèles | corpus expert à construire |

## 3. Technologies pivots

### Pivot 1 — Scientific Model Registry + GSIE-Bench

La valeur ne vient pas d'un modèle isolé, mais de la capacité à comparer,
versionner et révoquer des modèles avec leurs données et domaines de validité.
GSIE-Bench est prioritaire avant le choix d'un LLM, d'un downscaler ou d'un
foundation model local.

### Pivot 2 — xarray/Zarr + provenance

Les cubes météo, EO, hydrologiques et climatiques partagent une structure
multidimensionnelle. La combinaison xarray/Zarr/object storage + métadonnées
PostgreSQL est un socle réutilisable, mais les unités, CRS, chunks et licences
restent propres à chaque dataset.

### Pivot 3 — Earth Observation foundation models

Prithvi, AnySat, TESSERA et Satlas peuvent alimenter GeoSylva, Terra, Flora,
Artemis et IGNIS. Aucun ne doit être adopté sans benchmark régional et contrôle
des licences des poids, datasets et sorties.

### Pivot 4 — moteurs physiques composables

Atmos fournit des forcings ; IGNIS, Hydro et Terra conservent leurs états
physiques. Un modèle ML ne doit pas absorber les responsabilités des moteurs
métiers sans protocole de validation.

## 4. R&D multipliers

- GSIE-Bench et scénarios Gold ;
- génération de données synthétiques Unreal, toujours comparée au réel ;
- wrappers neutres provider/model ;
- schéma de provenance et d'incertitude commun ;
- workers GPU bornés et reproductibles ;
- conversion Zarr/NetCDF/GeoParquet contrôlée ;
- benchmark de downscaling français ;
- interfaces `ForecastProvider`, `ObservationProvider`, `ModelRunner`.

## 5. Ce qui est explicitement rejeté

- LLM calculant des valeurs météo ou dendrométriques ;
- modèle global présenté comme prévision locale ;
- fournisseur unique directement appelé par IGNIS/Hydro ;
- modèle avec licence des poids inconnue ;
- dataset global utilisé comme vérité de parcelle ;
- fine-tuning avant split territorial/temporel et benchmark ;
- probabilité sans nombre de membres ni calibration.

## 6. Sources principales

- WeatherNext : https://github.com/google-deepmind/weathernext
- WeatherNext models : https://developers.google.com/weathernext/guides/models
- WeatherNext feeds : https://developers.google.com/weathernext/guides/access-forecast
- GSIE-Bench : `02_RFC/RFC-0039-gsie-bench-v0-1.md`
- Model Fabric : `02_RFC/RFC-0015-environmental-model-fabric.md`
- Prithvi : https://github.com/NASA-IMPACT/Prithvi-EO-2.0
- AnySat : https://github.com/gastruc/AnySat
- TESSERA : https://github.com/ucam-eo/tessera
- Satlas : https://github.com/allenai/satlas
- NeuralHydrology : https://github.com/neuralhydrology/neuralhydrology
- airGR : https://hydrogr.github.io/airGR/
- SoilGrids : https://soilgrids.org/
- BioCLIP : https://github.com/Imageomics/BioCLIP
- SpeciesNet : https://github.com/google/cameratrapai
- BirdNET : https://github.com/birdnet-team/birdnet

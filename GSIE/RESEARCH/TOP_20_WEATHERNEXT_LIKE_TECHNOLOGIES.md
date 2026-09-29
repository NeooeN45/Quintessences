# Top 20 technologies « WeatherNext-like » pour Quintessences

> Classement R&D initial au 2026-08-18. Un score ne vaut ni validation
> scientifique ni autorisation d'intégration. Les licences de poids/datasets
> doivent toujours être vérifiées séparément du code.

| Rang | Technologie | Domaine | Type | Maturité | Licence indicative | Action | Score |
|---:|---|---|---|---|---|---|---:|
| 1 | WeatherNext 2 | Atmos | modèle global probabiliste | Production data / code Alpha | code Apache-2.0, autres matériaux CC BY 4.0 selon README | ADOPT flux | 9.2 |
| 2 | Prithvi-EO-2.0 | EO | foundation model multi-temporel | Production candidate | MIT/Apache selon artefact | ADOPT benchmark | 9.0 |
| 3 | BioCLIP | biodiversité | foundation vision taxonomique | Production candidate | MIT selon dépôt | ADAPT validation FR | 8.8 |
| 4 | BirdNET | faune acoustique | modèle edge | Mature | MIT/Apache selon version | ADOPT benchmark | 8.8 |
| 5 | NeuralHydrology | Hydro | framework/model zoo séquentiel | Mature | BSD-3-Clause | ADAPT bassin FR | 8.6 |
| 6 | TESSERA | EO/forêt | embeddings temporels S1/S2 | Research candidate | code MIT, embeddings à vérifier | ADAPT | 8.5 |
| 7 | AnySat | EO | JEPA multi-modalités/résolutions | Research candidate | MIT selon dépôt | BENCHMARKER | 8.4 |
| 8 | SatlasPretrain | EO | backbone multi-capteurs | Mature research | Apache/ODC-BY selon artefact | ADAPT | 8.3 |
| 9 | SpeciesNet | faune | camera trap classification | Production candidate | Apache-2.0 selon dépôt | ADAPT | 8.2 |
| 10 | PyTorch-Wildlife/MegaDetector | faune/EO | détection collaborative | Mature | dépend du checkpoint | ADAPT whitelist | 8.2 |
| 11 | airGR | Hydro | modèles conceptuels INRAE | Mature opérationnel | GPL-2 | ADAPT wrapper | 8.1 |
| 12 | SoilGrids | sols | cartographie DSM globale | Mature data product | CC BY 4.0 données | ADOPT comme a priori | 8.0 |
| 13 | OpenLandMap/soildb | sols | cartes DSM et quantiles | Mature data product | CC BY 4.0 selon produit | ADAPT | 7.9 |
| 14 | DeepForest | forêt | détection de houppiers RGB | Mature research | MIT selon dépôt | ADAPT corpus FR | 7.8 |
| 15 | TreeLearn | forêt/LiDAR | segmentation individuelle 3D | Research candidate | MIT selon dépôt | BENCHMARKER | 7.6 |
| 16 | ForeFire | incendie | propagation physique modulaire | Mature research/ops | GPL-3 | ADAPT licence/calibration | 7.6 |
| 17 | ELMFIRE | incendie | level-set propagation | Mature research/ops | EPL-2.0 selon dépôt | ADAPT | 7.5 |
| 18 | LISFLOOD | Hydro | modèle distribué Copernicus | Operational research | EUPL-1.2 selon JRC | ADAPT | 7.5 |
| 19 | PyTorchFire | incendie | simulateur GPU différentiable | Research candidate | MIT selon publication/dépôt | BENCHMARKER | 7.3 |
| 20 | WindNinja | vent local | solver terrain/vent | Mature operational tool | domaine public US selon projet | ADAPT | 7.3 |

## Fiches prioritaires

### WeatherNext 2

- **Pourquoi** : flux opérationnels et historiques accessibles sur Google Cloud,
  BigQuery, Earth Engine et GCS Zarr ; ensemble probabiliste ; architecture
  compatible avec un provider Atmos.
- **Risque** : accès et termes de données, résolution globale, code Alpha,
  dépendance Google si l'on ne garde pas de providers alternatifs.
- **POC** : sous-ensemble France/Nouvelle-Aquitaine, vent/température/précipitation,
  comparaison ECMWF/Météo-France.

### Prithvi-EO-2.0

- **Pourquoi** : fondation EO multi-temporelle institutionnelle avec code et
  artefacts documentés.
- **Risque** : HLS et domaine de calibration, shift territorial, coût du
  fine-tuning.
- **POC** : embeddings Sentinel/HLS sur parcelles GeoSylva avec split spatial.

### BioCLIP + BirdNET

- **Pourquoi** : deux briques perception distinctes et utiles pour Flora/Artemis,
  avec validation humaine obligatoire.
- **Risque** : biais taxonomiques et géographiques ; ne jamais convertir un top-1
  en observation canonique sans confirmation.

### NeuralHydrology + airGR

- **Pourquoi** : couple ML + modèle conceptuel pour comparer une approche apprise
  à un modèle hydrologique français éprouvé.
- **POC** : un ou deux bassins français documentés, mesures de débit, CRPS et
  hydrogrammes, validation temporelle hors échantillon.

### ForeFire/ELMFIRE + WindNinja

- **Pourquoi** : séparer propagation, vent local et météo synoptique est plus
  sain qu'un modèle « feu end-to-end » non explicable.
- **Risque** : licences GPL/EPL, calibration territoriale, vent et combustibles.

## Top 5 à tester

### 1. WeatherNext 2 — score 9,2

- **Modules** : Atmos, IGNIS, Hydro, GeoSylva, Terra.
- **Pourquoi maintenant** : flux officiels accessibles sans GPU Quintessences.
- **POC** : France/Nouvelle-Aquitaine, comparaison ECMWF/Météo-France.
- **Effort** : M, sous réserve d'accès aux flux.

### 2. Prithvi-EO-2.0 — score 9,0

- **Modules** : EO, GeoSylva, Terra, Flora, IGNIS.
- **Pourquoi maintenant** : foundation model multi-temporel avec artefacts
  institutionnels.
- **POC** : embeddings sur parcelles et validation par split spatial.
- **Effort** : M/L, GPU 16–24 Go pour adaptation.

### 3. NeuralHydrology + airGR — score combiné 8,6

- **Modules** : Hydro, Atmos forcings, Terra.
- **Pourquoi maintenant** : comparaison ML/processus sur bassins français.
- **POC** : un bassin instrumenté, métriques déterministes et probabilistes.
- **Effort** : M pour airGR, L pour calibration NeuralHydrology.

### 4. TESSERA/AnySat — score 8,5/8,4

- **Modules** : EO, GeoSylva, Flora, Terra.
- **Pourquoi maintenant** : temporalité et multi-modalité utiles pour le suivi.
- **POC** : Sentinel-1/2 et inventaires sur un territoire français.
- **Effort** : M/L, corpus et licences à qualifier.

### 5. ForeFire/ELMFIRE + WindNinja — score 7,6

- **Modules** : IGNIS, Atmos local, Hub.
- **Pourquoi maintenant** : architecture composable plutôt qu'un modèle feu
  opaque de bout en bout.
- **POC** : propagation contrôlée avec météo et topographie d'une zone pilote.
- **Effort** : L/XL, licences et validation française obligatoires.

## Méthode de sélection

Chaque candidat doit recevoir une fiche Model Fabric :

```yaml
model_id:
version:
code_license:
weights_license:
data_license:
inputs:
outputs:
spatial_domain:
temporal_domain:
uncertainty:
hardware:
validation:
territorial_calibration:
status:
```

## Sources primaires

- WeatherNext : https://github.com/google-deepmind/weathernext
- WeatherNext guide : https://developers.google.com/weathernext/guides/models
- Prithvi : https://github.com/NASA-IMPACT/Prithvi-EO-2.0
- AnySat : https://github.com/gastruc/AnySat
- Satlas : https://github.com/allenai/satlas
- BioCLIP : https://github.com/Imageomics/BioCLIP
- SpeciesNet : https://github.com/google/cameratrapai
- BirdNET : https://github.com/birdnet-team/birdnet
- PyTorch-Wildlife : https://github.com/microsoft/Pytorch-Wildlife
- NeuralHydrology : https://github.com/neuralhydrology/neuralhydrology
- airGR : https://hydrogr.github.io/airGR/
- SoilGrids : https://soilgrids.org/
- ForeFire : https://github.com/forefireAPI/forefire/
- ELMFIRE : https://github.com/lautenberger/elmfire/
- WindNinja : https://github.com/firelab/windninja

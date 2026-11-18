# POC WeatherNext → Atmos → GSIE

| Champ | Valeur |
|---|---|
| **Statut** | Plan expérimental — Draft |
| **Territoire** | sous-zone forestière française, pilote à choisir dans GSIE TEST |
| **Provider initial** | WeatherNext 2 data feed, sans auto-hébergement |
| **Baseline** | ECMWF HRES/ENS et source Météo-France disponible légalement |
| **Objectif** | Mesurer la valeur d'un flux probabiliste global avant tout worker GPU |

## 1. P0 — Accès aux données

### Objectif

Obtenir un run WeatherNext 2 autorisé et documenter les termes d'utilisation.

### Entrées

- demande d'accès WeatherNext ;
- flux GCS Zarr, BigQuery ou Earth Engine ;
- variables minimales vent U/V 10 m, température 2 m, précipitation, humidité si
  disponible/calculable ;
- période historique et un run récent.

### Critères de sortie

- accès reproductible ;
- licence et attribution consignées ;
- `provider_id`, `model_id`, run et checksum enregistrés ;
- aucune clé Google dans Git ou mobile.

## 2. P1 — Ingestion bornée

### Objectif

Lire un petit bbox et une fenêtre temporelle sans télécharger un dataset global.

### Technologies

- xarray ;
- Zarr ;
- Dask ;
- object storage GSIE ;
- manifest JSON ;
- validation Pydantic du schéma Atmos.

### Mesures

- volume transféré ;
- temps d'ouverture ;
- temps de lecture ;
- chunks ;
- RAM ;
- variables réellement disponibles.

## 3. P2 — Normalisation Atmos

### Objectif

Convertir le feed provider vers un contrat canonique sans masquer les
transformations.

### Sortie

```text
ForecastCube
- run_initialization
- valid_time
- member
- variable
- unit
- CRS/grid
- model/version
- source/checksum
- uncertainty
```

### Critères

- unités et conventions vérifiées ;
- U/V conservés, vitesse/direction calculées séparément ;
- accumulation de précipitation distinguée du taux ;
- conversion 10 m/100 m jamais implicite ;
- tests de valeurs plausibles et de dimensions.

## 4. P3 — Stockage

### Objectif

Persister un produit reconstituable.

### Architecture

```text
PostgreSQL/PostGIS : manifestes, runs, index, provenance
Object storage      : Zarr borné et checksum
DuckDB/xarray       : exploration locale
```

### Critères

- relecture exacte par `forecast_id` ;
- checksum stable ;
- expiration/cache documentés ;
- aucun cube non borné retourné par l'API.

## 5. P4 — API GSIE

### Endpoints proposés

```text
GET  /api/v1/atmos/forecast
POST /api/v1/atmos/forecast-cube
GET  /api/v1/atmos/runs/{forecast_id}
```

### Critères

- bbox, variables, période et nombre de membres obligatoires/bornés ;
- `trace_id`, `forecast_id`, modèle et version dans la réponse ;
- erreurs explicites si variable absente ;
- rate limiting et auth ;
- aucune dépendance directe des moteurs au provider.

## 6. P5 — Visualisation

### Objectif

Valider la compréhension humaine, pas seulement le rendu.

Afficher :

- vent U/V et vitesse ;
- température ;
- pluie ;
- membres ou quantiles ;
- médiane/spread ;
- date d'initialisation ;
- horizon ;
- source et version ;
- avertissement « résolution globale, pas micro-météo ».

## 7. P6 — Downscaling expérimental

Comparer sur la zone pilote :

1. correction quantile simple ;
2. analogues ou régression avec MNT ;
3. WindNinja pour le vent ;
4. modèle ML seulement si les baselines sont insuffisantes.

### Critères

- validation par stations non utilisées dans l'ajustement ;
- split spatial et temporel ;
- métriques par variable et horizon ;
- extrêmes séparés des moyennes ;
- domaine de validité et incertitude publiés.

## 8. P7 — IGNIS probabiliste

### Objectif

Tester la propagation de l'incertitude météo avec un simulateur IGNIS simplifié.

```text
8–16 membres météo
        ↓
champ local borné
        ↓
simulateur feu baseline
        ↓
probabilité d'arrivée et enveloppes
```

### Critères

- convergence des probabilités en augmentant le nombre de membres ;
- comparaison avec un run déterministe ;
- temps total et coût par membre ;
- aucune sortie présentée comme alerte officielle.

## 9. Matrice de mesures

| Mesure | P1 | P2 | P3 | P4 | P6 | P7 |
|---|---:|---:|---:|---:|---:|---:|
| volume réseau | ✓ | ✓ | ✓ |  |  |  |
| RAM/CPU | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| latence | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| erreur météo |  | ✓ |  |  | ✓ | ✓ |
| calibration ensemble |  |  |  |  | ✓ | ✓ |
| coût cloud | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| traçabilité | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## 10. Stop conditions

Le POC s'arrête ou revient à une baseline si :

- licence/terms non qualifiés ;
- données inaccessibles de façon reproductible ;
- gain inférieur à une baseline simple ;
- biais critique sur le territoire pilote ;
- coût disproportionné sans valeur opérationnelle ;
- résolution affichée interprétée comme précision locale ;
- incertitude mal calibrée ou impossible à propager.

## 11. Roadmap conditionnelle

### 0–7 jours

- qualifier l'accès WeatherNext et les termes de données ;
- figer `ForecastCube.v0.1` ;
- choisir le bbox et les stations de référence ;
- préparer le manifest et le premier lecteur Zarr.

### 1 mois

- ingestion P1–P3 reproductible ;
- comparaison de volume, latence et RAM ;
- première API Atmos en environnement test ;
- baseline ECMWF/Météo-France documentée.

### 3 mois

- benchmark régional par variable/horizon ;
- calibration de l'ensemble ;
- première correction de biais ;
- décision sur l'intérêt d'un downscaler local.

### 6 mois

- Atmos Registry et cache robustes ;
- intégration contrôlée Hydro et IGNIS ;
- POC vent local et propagation probabiliste ;
- validation scientifique externe du territoire pilote.

### 12 mois

- Scientific Model Fabric multi-domaines si le POC le justifie ;
- providers alternatifs opérationnels ;
- workers GPU autonomes uniquement si le coût/latence le justifie ;
- extension EO/forêt/sols avec GSIE-Bench et licences qualifiées.

Chaque échéance est conditionnée par les preuves de la précédente ; elle ne
constitue pas une promesse de délai de production.

## 12. Périmètre explicitement exclu du POC

- fine-tuning WeatherNext ;
- redistribution de poids ;
- modèle Atmos autonome ;
- production IGNIS ;
- alerte réglementaire ;
- intégration mobile GeoSylva ;
- downscaling à quelques centaines de mètres présenté comme démontré.

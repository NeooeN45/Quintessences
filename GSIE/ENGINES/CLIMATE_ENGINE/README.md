# Climate Engine

Moteur de **données climatiques et bioclimatiques**.

## Périmètre

- Gérer les données climatiques historiques et actuelles
- Calculer les variables bioclimatiques (températures, précipitations,
  déficit hydrique, durée de végétation)
- Fournir les projections climatiques pour les simulations long terme
- Intégrer les données Météo-France et autres sources officielles

## Principe fondamental

**Les données climatiques sont datées et qualifiées.** Les projections
sont affichées avec leur scénario (RCP/SSP) et leur incertitude.

## Frontières

- Consomme les données du `Climate Repository`
- Fournit des données climatiques à `DIAGNOSTIC_ENGINE`,
  `CORRELATION_ENGINE` et `SIMULATION_ENGINE`
- Mode hors-ligne : cache local des données historiques (article T-8)
- Mode dégradé documenté pour les projections temps réel

> Statut : *implémentation en cours (Phase 4)* — code livré, voir CLIMATE_ENGINE.md et PROJECT_MEMORY.md

## Contrat d'interface

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/climate/router.py`. Périmètre v1 :
observations réelles (SYNOP, DPClim, AROME, Vigilance, Package
Observations, Météo des forêts) — aucune projection climatique
(DRIAS/RCP), en attente de la clé du portail API Météo-France.

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/climate/status` | aucune | — | Statut du moteur (`router.py:36`) |
| GET | `/climate/version` | aucune | — | Version et backend (`router.py:47`) |
| POST | `/climate/query` | `engine:read` | `20/minute` | Dernière observation réelle d'une station SYNOP (`router.py:60`) |
| GET | `/climate/danger-feux` | `engine:read` | `20/minute` | Niveau de danger de feux de forêt, tous départements, J+1/J+2 (`router.py:90`) |
| GET | `/climate/climatologie-stations` | `engine:read` | `20/minute` | Liste des stations DPClim d'un département (`router.py:118`) |
| POST | `/climate/climatologie-quotidienne` | `engine:read` | `5/minute` | Données climatologiques quotidiennes DPClim (flux asynchrone, polling) (`router.py:153`) |
| GET | `/climate/vigilance` | `engine:read` | `20/minute` | Carte de vigilance en cours, J et J+1 (`router.py:187`) |
| GET | `/climate/observations-horaires` | `engine:read` | `20/minute` | Observations horaires des 24h, toutes stations d'un département (`router.py:215`) |
| POST | `/climate/arome-temperature` | `engine:read` | — | Température 2 m du modèle AROME (décodage GRIB2) (`router.py:250`) |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/climate/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `ClimateQuery` | Entrée de `/climate/query` | `station_id` (OMM 5 chiffres) |
| `ObservationClimatique` | Sortie de `/climate/query` | `temperature_c` (borné au zéro absolu), `humidite_pct`, `pression_hpa`, `vent_vitesse_ms` |
| `ClimatologieQuotidienneQuery` | Entrée DPClim | `id_station`, période |
| `AromeTemperatureQuery`/`AromeTemperatureResult` | Entrée/sortie AROME | point WGS 84, échéance, `temperature_c` |
| `VigilanceBulletin`, `DangerFeuxDepartement`, `ObservationHoraireDepartement` | Sorties spécialisées | niveau, domaine, échéance |

Valeur SYNOP absente → champ omis, jamais de valeur par défaut (ADR-009).

### 3. Exceptions

Source : `GSIE/API/src/gsie_api/engines/climate/engine.py`

| Exception | Condition de levée | Traduction HTTP |
|---|---|---|
| `ClimateEngineError` | API externe (SYNOP/DPClim/AROME/Vigilance/Météo des forêts) indisponible ou clé absente | 502 |

### 4. Dépendances

- **Amont** : `Climate Repository`.
- **Aval (chaîne principale)** : `DIAGNOSTIC_ENGINE`, `CORRELATION_ENGINE`,
  `SIMULATION_ENGINE`.
- **Clients API externes** : Météo-France — SYNOP (`synop_client.py`,
  licence ouverte, sans clé), DPClim (`dpclim_client.py`), AROME
  (`arome_client.py` + `arome_grib_decoder.py`), Vigilance
  (`vigilance_client.py`), Package Observations
  (`paquet_observation_client.py`), portail générique
  (`meteofrance_client.py`).
- **Persistance** : aucune (moteur sans état, requêtes en direct).

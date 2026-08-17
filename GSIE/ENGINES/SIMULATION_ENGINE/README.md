# Simulation Engine

Moteur de **simulation de scénarios**.

## Périmètre

- Simulation de scénarios sylvicoles sur le long terme
- Projection des effets d'interventions (plantation, éclaircie,
  coupe rase)
- Comparaison de stratégies de gestion
- Évaluation des risques (climatiques, sanitaires, économiques)

## Frontières

- Consomme `FOREST_DYNAMICS_ENGINE`, `CLIMATE_ENGINE` et
  `RECOMMENDATION_ENGINE`
- Fournit des projections au forestier pour l'aide à la décision
- Les résultats sont des **scénarios**, pas des décisions (CON-001)
- Chaque scénario est explicable (CON-004)

> État d’implémentation : une API v1 est présente dans
> `GSIE/API/src/gsie_api/engines/simulation/`. Elle exécute le modèle
> simplifié décrit ci-dessous ; les modèles scientifiques complets et
> leur calibration restent hors de ce périmètre.

## Contrat d'interface

> Cette section documente le contrat effectif du code présent.

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/simulation/router.py`

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/simulation/status` | aucune | — | Statut du moteur |
| GET | `/simulation/version` | aucune | — | Version et backend |
| POST | `/simulation/run` | `engine:write` | `10/minute` | Simule un scénario d'intervention sur un horizon donné |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/simulation/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `ScenarioSimulation` | Entrée de `/simulation/run` | `source_diagnostic`, `intervention` (`InterventionSpec`), `horizon` (ex. 5y/10y/30y), `climate_scenario` (AROME/ERA5/RCP) |
| `InterventionSpec` | Sous-objet | `type_intervention` (eclaircie/plantation/coupe_rase/protection), `parametres` |
| `TimedProjection` | Élément de projection temporelle | état du système à un instant donné |
| `SimulationResult` | Sortie de `/simulation/run` | `sources` (non vide — CON-005), `assumptions` (non vide — CON-004), `alternatives` (comparaison — CON-001), `confidence_level` (`ConfidenceLevel`, qualitatif en v1) |

### 3. Exceptions

Source : `GSIE/API/src/gsie_api/engines/simulation/engine.py`

| Exception | Condition de levée | Traduction HTTP |
|---|---|---|
| `SimulationEngineError` | Horizon ou intervention invalide | 400 |

### 4. Dépendances

- **Amont (chaîne principale)** : `FOREST_DYNAMICS_ENGINE`,
  `CLIMATE_ENGINE`, `RECOMMENDATION_ENGINE`.
- **Aval** : le forestier/COS (aide à la décision) — les résultats sont
  des scénarios, jamais des décisions (CON-001).
- **Clients API externes** : aucun direct (référence à un scénario
  climatique externe via `climate_scenario`, non résolu par le moteur).
- **Persistance** : PostgreSQL.
- **Évolution prévue** : quantification de `ConfidenceLevel` via
  analyse de sensibilité (SALib — Sobol/Morris, §8).

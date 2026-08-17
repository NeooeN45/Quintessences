# Learning Engine

Moteur d'**apprentissage**.

## Périmètre

- Apprentissage à partir des données terrain et des retours
  d'expérience
- Amélioration continue des modèles à partir des observations
  validées
- Détection de patterns émergents dans les corrélations
- Assistance à la calibration des seuils et règles

## Frontières

- Subordonné aux règles expertes et à l'explicabilité (CON-004)
- Ne remplace jamais `RULE_ENGINE` ni `KNOWLEDGE_ENGINE`
- Toute sortie doit être explicable et traçable
- L'IA assiste, elle ne décide pas (CON-001)

> État d’implémentation : une API v1 est présente dans
> `GSIE/API/src/gsie_api/engines/learning/`. Elle traite les signaux
> décrits ci-dessous et ne valide ni n’applique automatiquement ses
> propositions.

## Contrat d'interface

> Cette section documente le contrat effectif du code présent.

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/learning/router.py`

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/learning/status` | aucune | — | Statut du moteur |
| GET | `/learning/version` | aucune | — | Version et backend |
| POST | `/learning/process` | `engine:write` | `30/minute` | Traite un signal d'apprentissage et retourne éventuellement une proposition de révision |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/learning/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `LearningSignal` | Entrée de `/learning/process` | `type` (`LearningSignalType` : retour_forestier/sortie_bloquee/pattern_emergent/observation_terrain), contenu spécifique (`RetourForestier`, `PatternEmergent`) |
| `RetourForestier` | Sous-objet | `recommandation_id`, `decision`, `contexte_station` |
| `PatternEmergent` | Sous-objet | `description`, `correlations`, `confiance` |
| `LearningOutput` | Sortie de `/learning/process` | `type` (`LearningOutputType`), `statut` (`propose`/`en_validation` uniquement — jamais `valide`/`rejete` produits par le moteur), `justification`, `confiance` |

### 3. Exceptions

Source : `GSIE/API/src/gsie_api/engines/learning/engine.py`

| Exception | Condition de levée | Traduction HTTP |
|---|---|---|
| `LearningEngineError` | Type de signal non géré en v1 ou contenu invalide | 400 |

Un signal accumulé sans déclencher de proposition retourne HTTP 204
(`router.py:89`) plutôt qu'une exception.

### 4. Dépendances

- **Amont** : `RECOMMENDATION_ENGINE` (décisions du forestier),
  `VALIDATION_ENGINE` (sorties bloquées, `ValidationResultModel`),
  `CORRELATION_ENGINE` (patterns émergents).
- **Aval** : `KNOWLEDGE_ENGINE` — toute proposition doit y être validée
  avant application (CON-001), jamais appliquée automatiquement.
- **Clients API externes** : aucun.
- **Persistance** : PostgreSQL.

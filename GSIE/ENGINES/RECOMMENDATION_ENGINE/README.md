# Recommendation Engine

Moteur de **recommandations sylvicoles**.

## Périmètre

- Produire des recommandations d'action à partir des diagnostics
- Proposer des alternatives (pas une seule option)
- Justifier chaque recommandation par le diagnostic et les
  connaissances sous-jacentes
- Indiquer le niveau de confiance et les incertitudes

## Principe fondamental

**Toute recommandation est contournable.** Le forestier peut refuser,
modifier ou demander une alternative. Aucune recommandation n'est
exécutoire (CON-001).

## Frontières

- Consomme `DIAGNOSTIC_ENGINE` et `SIMULATION_ENGINE`
- Fournit des recommandations au forestier via l'interface utilisateur
- Ne décide pas — recommande
- Documente les refus et les écarts

## Position dans la chaîne

```
Diagnostic Engine → Recommendation Engine → Validation Engine → Utilisateur
```

> Statut : *implémentation partielle (Phase 4)* — stub/skeleton, voir RECOMMENDATION_ENGINE.md

## Contrat d'interface

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/recommendation/router.py`

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/recommendation/status` | aucune | — | Statut du moteur (`router.py:41`) |
| GET | `/recommendation/version` | aucune | — | Version et backend (`router.py:52`) |
| POST | `/recommendation/recommend` | `engine:write` | `20/minute` | Génère un ensemble de recommandations avec alternatives justifiées à partir d'un diagnostic (`router.py:65`) |
| POST | `/recommendation/decision` | `engine:write` | `30/minute` | Enregistre la décision du forestier (accepte/refuse/modifie/demande_alternative), attribuée à son auteur (`router.py:98`) |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/recommendation/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `RecommendationRequest` | Entrée de `/recommendation/recommend` | `diagnostic_ref`, `objectif_forestier` (production/protection/biodiversite/mixte/reboisement), `alternatives_demandees` |
| `Recommendation` | Une action proposée | `type_action` (dont `ATTENTE_SURVEILLANCE`), `justification` (`JustificationRecommandation`, sources et facteurs limitants obligatoires), `contournable` (propriété calculée, toujours vraie — CON-001) |
| `RecommendationSet` | Sortie de `/recommendation/recommend` | liste de `Recommendation` (avec alternatives) |
| `ForestierDecision` | Entrée de `/recommendation/decision` | `recommandation_id`, `decision` (`DecisionForestier`), `forestier_id` |

### 3. Exceptions

Source : `GSIE/API/src/gsie_api/engines/recommendation/engine.py`

| Exception | Condition de levée | Traduction HTTP |
|---|---|---|
| `RecommendationEngineError` | Requête invalide | 400 |
| `RecommandationIntrouvableError` (hérite de `RecommendationEngineError`) | Recommandation référencée introuvable lors de l'enregistrement d'une décision | 400 |
| `DiagnosticIntrouvableError` (hérite de `RecommendationEngineError`) | Diagnostic référencé introuvable | 400 |

### 4. Dépendances

- **Amont (chaîne principale)** : `DIAGNOSTIC_ENGINE`, `SIMULATION_ENGINE`.
- **Aval** : `VALIDATION_ENGINE`, puis l'utilisateur (forestier) ;
  `LEARNING_ENGINE` (alimenté par les décisions du forestier).
- **Clients API externes** : aucun.
- **Persistance** : PostgreSQL.

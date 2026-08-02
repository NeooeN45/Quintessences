# Reasoning Engine

Moteur de **raisonnement** sur les connaissances.

## Périmètre

- Raisonner sur les connaissances qualifiées par l'Evidence Engine
- Appliquer des règles d'inférence explicites et auditable
- Produire des conclusions expliquées et traçables
- Détecter les contradictions dans le raisonnement

## Principe fondamental

**Aucun raisonnement n'est produit sans chaîne d'inférence
documentée.**

## Frontières

- Consomme `KNOWLEDGE_ENGINE` et `CORRELATION_ENGINE`
- Fournit des conclusions à `DIAGNOSTIC_ENGINE` et
  `RECOMMENDATION_ENGINE`
- Ne produit pas de diagnostic ni de recommandation directe
- N'invente pas de règle — applique uniquement les règles
  scientifiquement validées

## Position dans la chaîne

```
Knowledge Engine → Correlation Engine → Reasoning Engine → Diagnostic Engine
```

> Statut : *implémentation en cours (Phase 4)* — code livré, voir REASONING_ENGINE.md et PROJECT_MEMORY.md

## Contrat d'interface

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/reasoning/router.py`

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/reasoning/status` | aucune | — | Statut du moteur (`router.py:118`) |
| GET | `/reasoning/version` | aucune | — | Version et backend (`router.py:139`) |
| POST | `/reasoning/infer` | `engine:write` | `30/minute` | Applique les règles d'inférence sur un contexte stationnel et produit des conclusions expliquées (`router.py:156`) |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/reasoning/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `ReasoningRequest` | Entrée de `/reasoning/infer` | `contexte` (`StationContexte`), `question`, `profondeur_max`, `date_inference` (fournie par l'appelant, jamais lue en interne — déterminisme) |
| `StationContexte` | Contexte stationnel (au moins un bloc requis) | `geographie`, `climat`, `pedologie`, `botanique`, `peuplement`, `correlations` (`BlocContexte`) |
| `BlocContexte` | Bloc de contexte avec provenance obligatoire | `source_moteur`, `source`, `evidence_level`, `valeurs` |
| `RegleInference` | Règle d'inférence (extension v1, fournie par l'appelant) | `identifiant`, `condition` (expression restreinte, jamais `eval`), `niveau_confiance` (fourni par la règle, jamais calculé) |
| `InferenceResult` | Sortie de `/reasoning/infer` | `resultat_id` (dérivé par `uuid5`, déterministe), `conclusions` (avec `chaine_inference`), `contradictions` (signalées, jamais résolues) |

### 3. Exceptions

Source : `GSIE/API/src/gsie_api/engines/reasoning/engine.py`

| Exception | Condition de levée | Traduction HTTP |
|---|---|---|
| `ReasoningEngineError` | Règle mal formée ou non applicable au contexte fourni | 400 |

Erreurs de validation Pydantic (contexte stationnel vide, champ
manquant) → 422 (`StationContexte._au_moins_un_bloc`).

### 4. Dépendances

- **Amont (chaîne principale)** : `KNOWLEDGE_ENGINE`, `CORRELATION_ENGINE`.
  Réduction de périmètre v1 assumée : les règles d'inférence et le
  contexte stationnel sont fournis directement dans la requête, en
  attendant le branchement direct sur les sept moteurs domaine prévus
  par le contrat (`GIS`, `CLIMATE`, `PEDOLOGY`, `BOTANICAL`,
  `FOREST_DYNAMICS`, `CORRELATION`, `TERRAIN`).
- **Aval** : `DIAGNOSTIC_ENGINE`, `RECOMMENDATION_ENGINE`.
- **Clients API externes** : aucun.
- **Persistance** : PostgreSQL.

# Diagnostic Engine

Moteur de **diagnostic stationnel et sylvicole**.

## Périmètre

- Produire des diagnostics sur l'état d'une station ou d'un peuplement
- Identifier les contraintes, les atouts et les risques
- Synthétiser les données multi-domaines (pédologie, climat, botanique,
  dynamique) en un diagnostic cohérent
- Documenter la confiance et les incertitudes du diagnostic

## Principe fondamental

**Un diagnostic est une analyse, pas une décision.** Il décrit l'état
et les risques, il ne prescrit pas l'action.

## Frontières

- Consomme `REASONING_ENGINE` et les moteurs spécialisés (GIS, Climate,
  Pedology, Botanical, Forest Dynamics)
- Fournit des diagnostics à `RECOMMENDATION_ENGINE`
- Ne produit pas de recommandation d'action
- Le forestier reste le décideur (CON-001)

## Position dans la chaîne

```
Reasoning Engine → Diagnostic Engine → Recommendation Engine
```

> État d’implémentation : une API v1 est présente dans
> `GSIE/API/src/gsie_api/engines/diagnostic/`. Elle couvre le périmètre
> effectif décrit ci-dessous ; son existence ne vaut pas achèvement du
> périmètre fonctionnel complet.

## Contrat d'interface

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/diagnostic/router.py`

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/diagnostic/status` | aucune | — | Statut du moteur |
| GET | `/diagnostic/version` | aucune | — | Version et backend |
| POST | `/diagnostic/diagnostiquer` | `engine:write` | `30/minute` | Assemble les conclusions du Reasoning Engine en un diagnostic stationnel structuré |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/diagnostic/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `DiagnosticRequest` | Entrée de `/diagnostic/diagnostiquer` | `station_id`, `type_diagnostic`, `conclusions` (issues du Reasoning Engine), `qualifications` (rôle/domaine déclarés), `etat_global` |
| `Diagnostic` | Sortie principale | `statut_validation` (`brouillon` par défaut — CON-001), contraintes/atouts/risques, `contradictions`, `confiance` (reprise des conclusions, jamais calculée) |
| `ValidationHumaine` | Sous-objet obligatoire pour passer au statut `valide` | identité de la personne, date de validation |

### 3. Exceptions

Source : `GSIE/API/src/gsie_api/engines/diagnostic/engine.py`

| Exception | Condition de levée | Traduction HTTP |
|---|---|---|
| `DiagnosticEngineError` | Requête indiagnosticable : chaîne d'inférence vide, aucun élément produit | 400 |
| `DiagnosticConflitError` (hérite de `DiagnosticEngineError`) | Contradiction inconstructible (domaines identiques ou non comparables) | 400 |

### 4. Dépendances

- **Amont (chaîne principale)** : `REASONING_ENGINE` (conclusions
  qualifiées), moteurs domaine `GIS`, `CLIMATE`, `PEDOLOGY`, `BOTANICAL`,
  `FOREST_DYNAMICS` (contexte).
- **Aval** : `RECOMMENDATION_ENGINE`.
- **Clients API externes** : aucun.
- **Persistance** : PostgreSQL. Le diagnostic sort toujours à l'état
  `brouillon` — seul un humain le valide (CON-001).

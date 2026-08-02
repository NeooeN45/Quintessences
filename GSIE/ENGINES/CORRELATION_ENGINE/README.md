# Correlation Engine

Moteur de **corrélations multiparamètres**.

## Périmètre

- Croiser automatiquement les données issues de sources hétérogènes
- Détecter les relations statistiques significatives
- Produire une matrice de corrélations justifiées

## Sources prévues

- MNT, RUM, cartes pédologiques, cartes climatiques
- IGN, données météo
- Diagnostic terrain, données utilisateur
- Publications scientifiques

## Sorties

Matrice de corrélations justifiées et sourcées.

## Frontières

- Ne produit pas de recommandation directe
- Alimente les moteurs de raisonnement (`REASONING_ENGINE`,
  `DIAGNOSTIC_ENGINE`)

> Statut : *implémentation en cours (Phase 4)* — code livré, voir CORRELATION_ENGINE.md et PROJECT_MEMORY.md

## Contrat d'interface

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/correlation/router.py`

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/correlation/status` | aucune | — | Statut du moteur (`router.py:32`) |
| GET | `/correlation/version` | aucune | — | Version et backend (`router.py:43`) |
| POST | `/correlation/compute` | `engine:write` | `30/minute` | Calcule et persiste une corrélation entre deux variables (`router.py:56`) |
| GET | `/correlation/stats` | `engine:read` | — | Statistiques des corrélations persistées, par méthode (`router.py:87`) |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/correlation/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `CorrelationComputeRequest` | Entrée de `/correlation/compute` | `variable_a`/`variable_b` (`ParametreCorrelation`, valeurs appariées ≥3 points), `methode` (pearson/spearman/kendall), `seuil_significativite`, `avec_refutation` |
| `ParametreCorrelation` | Sous-objet variable | `source_moteur` (provenance), `variable`, `valeurs` (liste de floats appariés) |
| `CorrelationResult` | Sortie de `/correlation/compute` | `correlation_id`, `coefficient`, `p_valeur`, `type_relation` (positive/negative/non_significative), `strength`, `refutation` (optionnel) |
| `RefutationResult` | Test de réfutation par permutation (RFC-0015 §3.5) | `n_permutations`, `p_valeur_permutation`, `robuste`, `interpretation` (vocabulaire imposé, jamais « cause ») |

### 3. Exceptions

Source : `GSIE/API/src/gsie_api/engines/correlation/engine.py`

| Exception | Condition de levée | Traduction HTTP |
|---|---|---|
| `CorrelationEngineError` | Méthode de corrélation non calculable, données insuffisantes ou invalides pour le calcul demandé | 400 |

### 4. Dépendances

- **Amont** : réduction de périmètre v1 assumée (voir en-tête de
  `schemas.py`) — les valeurs numériques sont fournies directement dans
  la requête plutôt que récupérées auprès des moteurs domaine (`GIS`,
  `CLIMATE`, `PEDOLOGY`, `BOTANICAL`, `FOREST_DYNAMICS`), qui n'exposent
  pas encore tous une API de contexte. Le champ `source_moteur` porte la
  provenance en attendant ce branchement.
- **Aval (chaîne principale)** : `REASONING_ENGINE`, `DIAGNOSTIC_ENGINE`
  — consomment les corrélations comme éléments de contexte.
- **Clients API externes** : aucun.
- **Persistance** : PostgreSQL (ressource « correlation » du graphe v6.2).

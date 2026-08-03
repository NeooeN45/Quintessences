# Validation Engine

Moteur de **validation des résultats**.

## Périmètre

- Vérifier la cohérence des diagnostics et recommandations avant
  présentation à l'utilisateur
- Contrôler que les connaissances utilisées sont valides et à jour
- Détecter les incohérences, les contradictions internes et les
  sorties hors domaine de validité
- Garantir que toute sortie respecte la Constitution (explicabilité,
  traçabilité, niveaux de preuve affichés)

## Principe fondamental

**Aucune sortie n'atteint l'utilisateur sans validation.** La
validation est le dernier rempart avant présentation.

## Frontières

- Consomme les sorties de `RECOMMENDATION_ENGINE` et
  `DIAGNOSTIC_ENGINE`
- Bloque les sorties non conformes (non expliquées, sans niveau de
  preuve, hors domaine)
- Ne produit pas de contenu — valide et filtre
- Journalise toute sortie bloquée avec la cause

## Position dans la chaîne

```
Recommendation Engine → Validation Engine → Utilisateur
```

> Statut : *implémentation livrée (Phase 4)* — code actif dans `GSIE/API/src/gsie_api/engines/validation/`

## Contrat d'interface

> Le code source (`GSIE/API/src/gsie_api/engines/validation/`) est livré
> et actif (`PROJECT_MEMORY.md`, DEC-000021 et suivants). Cette section
> documente le contrat effectif.

### 1. Endpoints API

Source : `GSIE/API/src/gsie_api/engines/validation/router.py`

| Méthode | Route | Auth | Rate limiting | Description |
|---|---|---|---|---|
| GET | `/validation/status` | aucune | — | Statut du moteur (`router.py:32`) |
| GET | `/validation/version` | aucune | — | Version et backend (`router.py:43`) |
| POST | `/validation/validate` | `engine:write` | `60/minute` | Valide une sortie (diagnostic, recommandation ou ensemble complet) et bloque toute sortie non conforme (`router.py:56`) |

### 2. Schémas d'entrée/sortie

Source : `GSIE/API/src/gsie_api/engines/validation/schemas.py`

| Schéma | Rôle | Champs clés |
|---|---|---|
| `ValidationRequest` | Entrée de `/validation/validate` | `type_sortie` (diagnostic/recommandation/ensemble_complet), `contenu` (structure libre typée), `chaines_inference`, `connaissances_utilisees` |
| `ControleResultat` | Résultat d'un contrôle individuel | `nom_controle`, `resultat` (conforme/non_conforme/non_applicable), `details` |
| `CauseBlocage` | Cause de blocage tracée | `type_cause` (8 causes, chacune liée à un article constitutionnel), `element_concerne`, `description` |
| `ValidationResult` | Sortie de `/validation/validate` | `statut` (valide/bloque/partiellement_valide), liste de `ControleResultat`, liste de `CauseBlocage` |

### 3. Exceptions

Source : `GSIE/API/src/gsie_api/engines/validation/engine.py`

| Exception | Condition de levée | Traduction HTTP |
|---|---|---|
| `ValidationEngineError` | Requête malformée au-delà du schéma Pydantic (incohérence interne) | 400 |

Un blocage de sortie n'est **pas** une exception : `statut=bloque` est
retourné en HTTP 200 avec les causes de blocage tracées
(`router.py:69`).

### 4. Dépendances

- **Amont (chaîne principale)** : `RECOMMENDATION_ENGINE`,
  `DIAGNOSTIC_ENGINE`.
- **Aval** : l'utilisateur (forestier) — dernier rempart avant
  présentation ; `LEARNING_ENGINE` (persistance de `ValidationResultModel`
  pour les sorties `bloque`/`partiellement_valide`, RFC-0028).
- **Clients API externes** : aucun.
- **Persistance** : PostgreSQL (`validation_result`, migration
  `20260801_0028_validation_result_table.py`).

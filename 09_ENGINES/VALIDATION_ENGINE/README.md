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

> Statut : *fondation — documentation uniquement (Phase 1)*

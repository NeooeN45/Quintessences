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

> Statut : *fondation — documentation uniquement (Phase 1)*

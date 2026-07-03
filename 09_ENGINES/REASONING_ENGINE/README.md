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

> Statut : *fondation — documentation uniquement (Phase 1)*

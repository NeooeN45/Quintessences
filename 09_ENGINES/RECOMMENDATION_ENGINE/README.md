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

> Statut : *fondation — documentation uniquement (Phase 1)*

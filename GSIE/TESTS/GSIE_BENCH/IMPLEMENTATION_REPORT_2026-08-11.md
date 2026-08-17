# Rapport d'implémentation — GSIE-Bench v0.1, tranche 1

## Périmètre réalisé

La tranche autorisée par DEC-000067 est implémentée sans ingestion et sans
appel fournisseur :

- sélection de trois diagnostics candidats issus de Parelle 2007 ;
- génération déterministe de dix variations par diagnostic ;
- contrat immuable `ScenarioSpec`, `ReferenceRef` et `CandidatePrediction` ;
- runner Closed avec ordre stable, checksum, garde de qualification et porte
  `GO` / `NO-GO` / `INCONCLUSIVE` ;
- baseline naïve par abstention ;
- baseline déterministe pédologique explicable ;
- quatre tests contractuels ciblés.

## Preuves locales

| Contrôle | Résultat |
|---|---|
| Catalogue | 30 scénarios, 3 parents, 10 variations par parent |
| Garde Closed | scénario `pending_expert_review` refusé avant appel candidat |
| Baseline déterministe | cas complet qualifié : `GO`, F1 = 1,0 |
| Baseline naïve | cas complet qualifié : `INCONCLUSIVE`, sans promotion |
| Tests pytest ciblés | 4 passants |
| Ruff | aucune erreur sur le package et le test |
| Mypy strict | aucune erreur sur 5 fichiers source |
| Compilation Python | réussie |
| Tentative Closed officielle | Bloquée avant appel candidat par `QualificationRequiredError` |

## Limites explicites

Les trois scénarios restent `pending_expert_review`. La référence est qualifiée
pour citation et annotation dérivée, mais pas pour la copie ou la redistribution
d'un jeu brut. Les seuils statistiques finaux, les réponses alternatives et la
relecture experte doivent être enregistrés avant une première exécution Closed
complète.

La tranche ne fournit donc pas encore une mesure scientifique de performance
d'un moteur. Elle fournit le contrat et les garde-fous nécessaires pour que
cette mesure soit valide.

## Prochaine action autorisée

Obtenir la relecture experte indépendante, compléter la qualification juridique
des annotations dérivées, puis figer le manifeste Closed. Toute ouverture de
FETCH, intégration IA ou promotion reste hors autorisation.

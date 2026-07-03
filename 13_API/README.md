# 13 — API

## Objectif

Exposer les capacités de GSIE à des clients tiers via des contrats
d'interface formels.

## Responsabilités

- Définir les contrats (REST, gRPC, GraphQL selon RFC)
- Garantir le versionnage et la rétro-compatibilité
- Produire la documentation OpenAPI

## Ce qui peut y être ajouté

- Schémas de requêtes et réponses
- Politique de versionnage
- Documentation de contrats

## Ce qui est interdit

- Implémenter des endpoints (Phase 1)
- Exposer des données sans contrôle d'accès

## Liens

- **14_SDK** : enveloppe l'API
- **12_APPLICATIONS** : consomme l'API
- **09_ENGINES** : l'API expose les moteurs

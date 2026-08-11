# Modèles RFC et ADR

## Modèle RFC

```markdown
# RFC-XXXX - Titre

## Statut
Draft / Review / Accepted / Implemented / Deprecated

## Contexte

## Problème

## Objectifs

## Non-objectifs

## Contraintes métier

## Données concernées

## Architecture proposée

## API et contrats

## Modèle de données

## Fonctionnement hors ligne

## Synchronisation GSIE

## Sécurité et droits

## Provenance scientifique

## Gestion des erreurs

## Migration

## Compatibilité

## Tests

## Observabilité

## Alternatives

## Risques

## Plan de livraison

## Critères d'acceptation
```

## Modèle ADR

```markdown
# ADR-XXXX - Décision

## Statut

## Date

## Contexte

## Décision

## Alternatives considérées

## Conséquences positives

## Conséquences négatives

## Impacts sur GeoSylva

## Impacts sur GSIE

## Migration

## Réversibilité
```

## RFC prioritaires

- RFC-0001 Forestry Scientific Core
- RFC-0002 Global Identity and Workspaces
- RFC-0003 Event Sync Protocol
- RFC-0004 QPIS Pack Format
- RFC-0005 Protocol and Form Engine
- RFC-0006 Geo Engine and QField Interoperability
- RFC-0007 TreeVision Measurement Pipeline
- RFC-0008 Subscription and Entitlements
- RFC-0009 Scientific Method Registry
- RFC-0010 Data Provenance and Evidence

## ADR prioritaires

- Keycloak comme broker d'identité ;
- UUID global ;
- Room/SQLCipher conservé comme base locale métier ;
- GeoPackage comme format d'échange ;
- PMTiles comme format principal de consultation ;
- règles déclaratives hors UI ;
- packs signés ;
- calculs hybrides avec parité ;
- event journal léger ;
- aucune suppression automatique de données non synchronisées.

# GIS Engine

Moteur de **données géospatiales**.

## Périmètre

- Gérer les données géospatiales (parcelles, stations, relief,
  hydrographie)
- Fournir des services de cartographie et d'analyse spatiale
- Calculer les caractéristiques stationnelles liées à la géographie
  (pente, exposition, altitude, distance)
- Intégrer les données IGN et autres sources géographiques officielles

## Principe fondamental

**Toute donnée géospatiale est sourcée et datée.** Les couches
cartographiques portent leur origine et leur date de mise à jour.

## Frontières

- Consomme les données de la `Spatial Database`
- Fournit des données géospatiales à `DIAGNOSTIC_ENGINE` et
  `CORRELATION_ENGINE`
- Mode hors-ligne : cache local des données de référence (article T-8)
- Ne produit pas de diagnostic — fournit des données

> Statut : *fondation — documentation uniquement (Phase 1)*

# Climate Engine

Moteur de **données climatiques et bioclimatiques**.

## Périmètre

- Gérer les données climatiques historiques et actuelles
- Calculer les variables bioclimatiques (températures, précipitations,
  déficit hydrique, durée de végétation)
- Fournir les projections climatiques pour les simulations long terme
- Intégrer les données Météo-France et autres sources officielles

## Principe fondamental

**Les données climatiques sont datées et qualifiées.** Les projections
sont affichées avec leur scénario (RCP/SSP) et leur incertitude.

## Frontières

- Consomme les données du `Climate Repository`
- Fournit des données climatiques à `DIAGNOSTIC_ENGINE`,
  `CORRELATION_ENGINE` et `SIMULATION_ENGINE`
- Mode hors-ligne : cache local des données historiques (article T-8)
- Mode dégradé documenté pour les projections temps réel

> Statut : *fondation — documentation uniquement (Phase 1)*

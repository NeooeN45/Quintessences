# Botanical Engine

Moteur de **flore, taxonomie et autécologie des espèces**.

## Périmètre

- Gérer la taxonomie et la nomenclature botanique (référentiels
  officiels : Tela Botanica, GBIF, BDNFF)
- Stocker les caractéristiques autécologiques de chaque essence
  (optimum, amplitude, exigences)
- Fournir les données d'identification et de classification
- Gérer les synonymes et les évolutions taxonomiques

## Principe fondamental

**Toute donnée botanique est sourcée et versionnée.** Les évolutions
taxonomiques sont tracées — un taxon peut changer de nom, mais
l'historique est conservé (CON-010).

## Frontières

- Consomme les données du `Species Repository` et de l'`Ontology`
- Fournit des données botaniques à `DIAGNOSTIC_ENGINE`,
  `CORRELATION_ENGINE` et `RECOMMENDATION_ENGINE`
- Ne produit pas de diagnostic — fournit des données taxonomiques et
  autécologiques

> Statut : *fondation — documentation uniquement (Phase 1)*

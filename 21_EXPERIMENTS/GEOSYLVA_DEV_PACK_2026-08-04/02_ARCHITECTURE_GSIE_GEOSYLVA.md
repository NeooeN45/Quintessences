# Architecture GSIE - GeoSylva - Quintessences

## Vue générale

```text
Compte unique Quintessences
          |
          v
Identité, organisations et droits
          |
          v
Serveur GSIE
  - API métier
  - synchronisation
  - Quintessences DB
  - registre scientifique
  - usine de packs
  - moteurs lourds
  - cartographie
  - stockage objet
  - audit
          |
  +-------+--------+---------+
  |                |         |
GeoSylva          Ignis    Artemis
Forêt             Feu      Cynégétique
  |                |         |
Flora / Terra / Hydro / Atmos / futurs modules
```

## Responsabilités de GeoSylva

- collecte terrain ;
- base locale chiffrée ;
- exécution des calculs essentiels ;
- fonctionnement hors connexion ;
- cartes locales ;
- capteurs et instruments ;
- génération immédiate de rapports ;
- file d'événements à synchroniser ;
- validation humaine ;
- cache des droits et packs.

## Responsabilités du serveur GSIE

- identité fédérée ;
- organisations et abonnements ;
- synchronisation ;
- stockage partagé ;
- détection des conflits ;
- préparation des packs ;
- collecte des API externes ;
- calculs lourds ;
- télédétection ;
- LiDAR ;
- agrégations multi-territoires ;
- moteur IA serveur ;
- publication de référentiels ;
- journal d'audit central.

## Objets communs Quintessences

Les applications ne doivent pas dupliquer les objets fondamentaux.

Entités communes recommandées :

- Identity
- Organization
- Workspace
- Team
- Project
- Mission
- Location
- Geometry
- Territory
- Property
- ManagementUnit
- Taxon
- Habitat
- Observation
- Measurement
- Evidence
- Protocol
- Method
- Calculation
- Document
- Asset
- Event

Les extensions spécialisées sont rattachées à ces objets communs.

## Unité territoriale partagée

Une même unité de gestion peut être enrichie par plusieurs modules :

- GeoSylva : peuplements, inventaires, martelages, travaux ;
- Ignis : combustibilité, accès DFCI, points d'eau, scénarios ;
- Artemis : dégâts de gibier, passages, pression ;
- Flora : taxons, habitats, espèces protégées ;
- Terra : sol, réserve utile, hydromorphie ;
- Atmos : climat, sécheresse, prévisions ;
- Hydro : ruissellement, cours d'eau, zones humides.

## Moteurs locaux, serveurs et hybrides

### Locaux

- surface terrière ;
- statistiques dendrométriques ;
- cubage courant ;
- contrôles de cohérence ;
- valorisation simple ;
- simulation de prélèvement ;
- règles indispensables ;
- rapport de terrain.

### Serveur

- télédétection ;
- LiDAR ;
- analyse nationale ;
- comparaison de grands volumes ;
- modèles climatiques ;
- IA lourde ;
- génération massive de tuiles ;
- agrégations organisationnelles.

### Hybrides

Les moteurs hybrides partagent les mêmes définitions, paramètres et jeux de tests :

- volume ;
- biomasse ;
- carbone ;
- valorisation ;
- règles de qualité ;
- scénarios sylvicoles.

## Règle de parité

Un calcul effectué localement et le même calcul exécuté sur le serveur avec la même méthode et les mêmes entrées doivent produire le même résultat dans la tolérance définie.

## Deep links interapplications

Exemples :

- `quintessences://geosylva/management-unit/{uuid}`
- `quintessences://flora/taxon/{uuid}`
- `quintessences://ignis/risk-zone/{uuid}`
- `quintessences://artemis/observation/{uuid}`

## Architecture modulaire recommandée

```text
platform/
  identity/
  authorization/
  subscription/
  packs/
  sync/
  audit/

forest-core/
  taxonomy/
  measurement/
  dendrometry/
  volume/
  assortment/
  valuation/
  silviculture/
  health/
  biodiversity/

mission-engine/
  professions/
  capabilities/
  protocols/
  workflows/
  forms/

geo-engine/
  rendering/
  geometry/
  offline/
  geopackage/
  pmtiles/
  qgis-interop/

treevision/
  capture/
  detection/
  geometry/
  positioning/
  uncertainty/
```

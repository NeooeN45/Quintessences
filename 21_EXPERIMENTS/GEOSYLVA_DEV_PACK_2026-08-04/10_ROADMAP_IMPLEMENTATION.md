# Feuille de route d'implémentation

## Phase 0 - Audit du dépôt

Objectifs :

- cartographier modules, tables, migrations et dépendances ;
- inventorier les méthodes de cubage ;
- inspecter Essence, ForestryCalculator, prix, Room, SQLCipher ;
- établir la couverture de tests ;
- identifier les dettes et duplications ;
- geler les contrats actuels par tests.

Livrables :

- architecture actuelle ;
- diagramme des données ;
- inventaire des calculs ;
- risques ;
- plan de migration.

## Phase 1 - Fondations communes

- UUID globaux ;
- distinction entité/observation/mesure/résultat ;
- unités typées ;
- provenance ;
- registre de méthodes ;
- CalculationRun ;
- nouveaux tests de référence ;
- compatibilité ascendante.

## Phase 2 - Refonte du moteur forestier

- VolumeEquationDefinition ;
- MethodResolver ;
- calcul indépendant par essence ;
- agrégations ;
- comparaison ;
- avertissements ;
- incertitude ;
- classification produits ;
- valorisation transparente.

## Phase 3 - Mission et Protocol Engine

- métiers ;
- capacités ;
- missions ;
- protocoles déclaratifs ;
- formulaires contextuels ;
- workflows de validation ;
- mode étudiant/formateur.

## Phase 4 - Identité et organisations

- Keycloak ;
- Google ;
- passkeys ;
- OIDC PKCE ;
- workspaces ;
- invitations ;
- droits ;
- cache hors ligne ;
- révocation appareils.

## Phase 5 - Synchronisation GSIE

- event journal ;
- file locale ;
- API idempotente ;
- résolution de conflits ;
- audit ;
- stockage objet ;
- parité des calculs.

## Phase 6 - QPIS

- format de manifeste ;
- catalogue ;
- téléchargement ;
- stockage ;
- signatures ;
- delta ;
- rollback ;
- packs départementaux ;
- packs scientifiques ;
- packs organisationnels.

## Phase 7 - Geo Engine

- PMTiles ;
- GeoPackage ;
- import/export ;
- édition ;
- R-Tree ;
- QGIS/QField ;
- PostGIS ;
- Martin ;
- packs cartographiques.

## Phase 8 - TreeVision prototype

1. diamètre semi-automatique ;
2. ligne 1,30 m ;
3. scan multi-angle ;
4. compas comme référence ;
5. visée base/cime ;
6. GNSS stabilisé ;
7. triangulation ;
8. banc de validation ;
9. pack de modèle.

## Phase 9 - Moteurs serveur

- télédétection ;
- STAC ;
- Orfeo ToolBox ;
- LiDAR ;
- analyses régionales ;
- modèle IA ;
- rapports avancés.

## Stratégie de livraison

Chaque phase :

1. RFC ;
2. ADR ;
3. tests de contrat ;
4. implémentation par petits lots ;
5. migration ;
6. instrumentation ;
7. documentation ;
8. validation terrain ;
9. rollback possible.

## Définition de terminé

- code ;
- tests ;
- documentation ;
- migration ;
- télémétrie ;
- sécurité ;
- compatibilité hors ligne ;
- export ;
- validation terrain ;
- absence de régression.

## Priorité immédiate

Commencer par l'audit du dépôt et le RFC du moteur de cubage et de valorisation. Ne pas lancer simultanément l'identité, les packs, le SIG et TreeVision sans fondations partagées.

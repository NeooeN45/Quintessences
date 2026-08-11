# Moteur géospatial et intégrations open source

## Positionnement

GeoSylva doit posséder un SIG mobile forestier, sans devenir un clone complet de QField. Il combine un moteur de rendu rapide, des opérations géométriques et une forte interopérabilité QGIS/QField.

## Architecture cible

- MapLibre Native : rendu ;
- GeoPackage : échange et données géographiques ;
- PMTiles : couches de consultation hors ligne ;
- Room/SQLCipher : base métier locale ;
- index R-Tree : requêtes spatiales ;
- PostGIS : base collaborative serveur ;
- Martin : tuiles vectorielles ;
- OGC API Features : objets géographiques ;
- QGIS/QField : préparation et interopérabilité.

## Trois niveaux

### Carte opérationnelle

- position ;
- arbres ;
- parcelles ;
- points ;
- lignes ;
- polygones ;
- mesures ;
- filtres ;
- couches hors ligne.

### SIG mobile

- édition de sommets ;
- snapping ;
- fusion ;
- découpage ;
- buffer ;
- intersection ;
- sélection spatiale ;
- profil altimétrique ;
- topologie ;
- reprojection.

### Interopérabilité

- import/export GeoPackage ;
- UUID stables ;
- relations ;
- styles partiels ;
- projets QGIS ;
- synchronisation ;
- PostGIS.

## Règle de stockage

La base métier interne ne doit pas être remplacée automatiquement par GeoPackage.

- Room/SQLCipher : métier et sécurité ;
- GeoPackage : échange ;
- PMTiles : consultation ;
- PostGIS : collaboration.

## QField

Stratégie recommandée :

- compatibilité par formats ;
- inspiration des workflows ;
- éventuelle contribution ;
- réutilisation de code seulement après audit de licence et faisabilité ;
- pas d'intégration brute de toute l'application.

## Autres briques à étudier

- ODK Collect : formulaires ;
- Open Foris Collect/Arena : inventaires, validation, campagnes ;
- DuckDB Spatial : analyse lourde locale ou desktop ;
- Orfeo ToolBox : télédétection serveur ;
- STAC : catalogue d'images ;
- Martin : tuiles ;
- pg_featureserv ou équivalent : OGC API Features ;
- moteur de règles déclaratif inspiré de JSON Logic ou ZEN.

## Distance de débardage

Calcul sur graphe de desserte, pas seulement distance euclidienne.

Entrées :

- réseau ;
- portance ;
- pente ;
- obstacles ;
- périodes ;
- sens de circulation ;
- place de dépôt.

Sorties :

- itinéraire ;
- distance ;
- difficulté ;
- coût estimé ;
- incertitude.

## Packs géographiques

Les couches sont préparées côté serveur par département, région, forêt ou mission. L'application ne contacte pas directement toutes les sources.

## Licences

Créer un registre interne :

- permissif ;
- copyleft compatible ;
- interopérabilité seulement ;
- réimplémentation ;
- usage interdit dans le produit commercial.

Chaque dépendance doit avoir :

- licence ;
- version ;
- usage ;
- obligations ;
- auteur ;
- URL ;
- décision.

# Quintessences Pack Intelligence System - QPIS

## Finalité

GeoSylva ne doit pas appeler directement des dizaines d'API publiques. Le serveur GSIE collecte, normalise, contrôle, découpe, compresse, signe et distribue les données sous forme de packs.

Le gestionnaire local choisit les packs selon :

- compte ;
- abonnement ;
- workspace ;
- métier ;
- mission ;
- territoire ;
- appareil ;
- connexion ;
- batterie ;
- stockage ;
- fraîcheur des données.

## Types de packs

### Système

- taxonomie ;
- unités ;
- méthodes ;
- équations ;
- règles ;
- classifications ;
- protocoles de base ;
- traductions ;
- documentation.

### Fonctionnels

- inventaire avancé ;
- martelage pro ;
- valorisation ;
- santé ;
- travaux ;
- DFCI ;
- SIG avancé ;
- IA locale ;
- collaboration.

Les nouvelles fonctions exécutables passent par une mise à jour signée ou un module dynamique officiel. Les packs GSIE contiennent surtout données, modèles, règles, protocoles et configuration.

### Géographiques

Hiérarchie :

France -> région -> département -> territoire -> forêt -> mission.

### Cartographiques

- PMTiles ;
- MBTiles si nécessaire ;
- orthophotos ;
- fond topographique ;
- cadastre autorisé ;
- DFCI ;
- relief ;
- couches forestières ;
- modèles numériques.

### Scientifiques

- tarifs de cubage ;
- équations ;
- allométrie ;
- biomasse ;
- carbone ;
- station ;
- santé ;
- sylviculture ;
- produits.

### Organisationnels

- protocoles privés ;
- tarifs internes ;
- couches privées ;
- nomenclatures ;
- modèles de rapports ;
- paramètres ;
- missions.

### IA

- reconnaissance d'essences ;
- TreeVision ;
- voix ;
- OCR ;
- assistant local ;
- modèle sanitaire.

## Manifestes

Chaque pack doit inclure :

- ID ;
- version sémantique ;
- type ;
- taille compressée ;
- espace installé ;
- dépendances ;
- compatibilité application ;
- niveau d'abonnement ;
- territoire ;
- date de publication ;
- expiration ;
- source ;
- licence ;
- hash ;
- signature ;
- stratégie de mise à jour ;
- criticité ;
- politiques de suppression.

## Etats

- REQUIRED
- RECOMMENDED
- OPTIONAL
- DEPRECATED
- REVOKED
- ARCHIVED

## Téléchargement intelligent

Politique proposée :

- petits correctifs : mobile autorisé ;
- packs moyens : confirmation ;
- gros packs : Wi-Fi recommandé ;
- LiDAR/orthophoto : Wi-Fi par défaut ;
- téléchargement différé si batterie faible ;
- préchargement avant mission ;
- reprise sur coupure ;
- vérification par blocs.

## Storage Budget Manager

Priorité de conservation :

1. données non synchronisées ;
2. mission active ;
3. référentiels essentiels ;
4. cartes de mission ;
5. packs favoris ;
6. archives synchronisées ;
7. orthophotos ;
8. caches reproductibles.

Calcul avant installation :

espace du pack + espace temporaire + espace rollback + marge - espace libéré.

## Mise à jour différentielle

- découpage en blocs adressés par hash ;
- réutilisation des blocs identiques ;
- téléchargement uniquement des différences ;
- installation atomique ;
- retour arrière ;
- collecte des anciennes versions après validation.

## Abonnements

Le serveur calcule les droits de packs. Une expiration :

- ne supprime pas les données ;
- conserve l'export ;
- autorise la lecture ;
- bloque éventuellement les nouveaux traitements premium ;
- respecte un délai de grâce hors ligne.

## Usine de packs serveur

Pipeline :

ingestion -> validation -> normalisation -> reprojection -> déduplication -> enrichissement -> découpage territorial -> génération des index -> compression -> signature -> publication -> surveillance.

## API de packs

Services logiques :

- PackCatalogService
- EntitlementResolver
- RegionalPackBuilder
- DependencyResolver
- NetworkPolicyManager
- StorageBudgetManager
- DeltaUpdateEngine
- IntegrityVerifier
- AtomicInstaller
- RollbackManager
- GarbageCollector

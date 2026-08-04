# Vision produit et principes fondateurs

## Vision

Quintessences est un écosystème scientifique, professionnel et territorial unifié. Il réunit plusieurs applications spécialisées autour d'une identité commune, d'un modèle de données partagé, de moteurs scientifiques versionnés et d'un serveur central GSIE.

GeoSylva est le client forestier mobile de cet écosystème. Il doit devenir le poste de travail numérique du technicien forestier : préparation des missions, collecte, inventaire, martelage, diagnostic, cubage, valorisation, suivi des travaux, cartographie, restitution, synchronisation et analyse.

## Finalité métier

GeoSylva doit réduire :

- la double saisie ;
- les erreurs de transcription ;
- les calculs manuels répétitifs ;
- la dispersion des documents ;
- la perte de contexte entre terrain et bureau ;
- les incohérences entre méthodes ;
- les difficultés de restitution ;
- la dépendance au réseau ;
- les oublis de contrôle et de suivi.

GeoSylva ne remplace pas le technicien. Il réunit son expertise, les instruments de terrain, les capteurs du téléphone, les référentiels scientifiques et les capacités du serveur.

## Cycle métier couvert

Comprendre -> préparer -> observer -> mesurer -> diagnostiquer -> décider -> planifier -> prescrire -> exécuter -> contrôler -> communiquer -> archiver -> apprendre.

## Positionnement différenciant

GeoSylva n'est ni un simple carnet de terrain, ni un QGIS mobile, ni un calculateur de cubage. Il doit combiner :

- moteur forestier scientifique ;
- moteur de protocoles ;
- moteur de règles et de scénarios ;
- SIG mobile professionnel ;
- collecte multimodale ;
- cartographie hors ligne ;
- synchronisation multi-utilisateur ;
- analyse locale et serveur ;
- explication des résultats ;
- intégration aux autres applications Quintessences.

## Principes de conception

### Architecture-first

Toute fonctionnalité doit être précédée d'une définition claire des données, des moteurs, des interfaces, des dépendances et des tests.

### Offline-first

Les fonctions essentielles du terrain doivent rester disponibles sans connexion : inventaire, martelage, calculs, cartes téléchargées, formulaires, rapports et historique local.

### Scientific-by-design

Les équations, seuils, facteurs, coefficients et règles sont des ressources versionnées. Leur provenance et leur domaine d'emploi sont enregistrés.

### Human-in-the-loop

Une mesure automatique peut être confirmée, corrigée ou remplacée par une mesure instrumentale. La correction ne supprime jamais la mesure initiale ; elle enrichit la traçabilité.

### Adaptation contextuelle

L'interface dépend du métier, de la mission, du protocole, de l'organisation, du territoire, du matériel, de l'abonnement, de la connexion et du stockage disponible.

### Interopérabilité

QGIS, QField, GeoPackage, PostGIS, OGC API Features, PMTiles, formats tabulaires et API documentées doivent être traités comme des interfaces natives de l'écosystème.

## Critères de réussite

- Utilisation d'une seule main en conditions de terrain.
- Aucune perte de données en cas de panne ou d'absence de réseau.
- Résultats reproductibles et explicables.
- Temps de saisie inférieur ou égal au papier pour les opérations courantes.
- Adaptation aux organismes sans fork spécifique de l'application.
- Migrations sûres et testées.
- Données exportables à tout moment.
- Possibilité d'audit complet des calculs et modifications.

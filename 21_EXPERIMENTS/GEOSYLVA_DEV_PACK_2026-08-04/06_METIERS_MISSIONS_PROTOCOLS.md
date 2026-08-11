# Métiers, missions, protocoles et adaptation de l'interface

## Trois dimensions

Ne pas confondre :

- métier : fonction habituelle ;
- mission : tâche actuelle ;
- contexte : organisme, territoire, protocole, contraintes.

## Métiers initiaux

- technicien forestier territorial ;
- gestionnaire privé ;
- expert forestier ;
- technicien travaux ;
- technicien exploitation ;
- technicien SIG ;
- technicien DFCI ;
- chargé biodiversité ;
- propriétaire ;
- étudiant ;
- formateur ;
- administrateur.

## Capabilities

Les droits et l'interface sont basés sur des capacités précises :

- forest.inventory.read
- forest.inventory.create
- forest.inventory.validate
- forest.marking.execute
- forest.valuation.read
- forest.valuation.modify
- forest.protocol.manage
- geo.layer.publish
- geo.export.sensitive
- organization.members.manage

## Mission Engine

Une mission contient :

- type ;
- objectif ;
- responsable ;
- participants ;
- territoire ;
- parcelles ;
- protocole ;
- date ;
- couches ;
- matériel ;
- formulaires ;
- règles ;
- livrables ;
- politique de synchronisation ;
- packs nécessaires.

## Protocol Engine

Inspirations : ODK et Open Foris.

Le protocole décrit :

- sections ;
- champs ;
- types ;
- unités ;
- valeurs ;
- obligations ;
- conditions ;
- répétitions ;
- calculs ;
- contrôles ;
- pièces jointes ;
- géométrie ;
- règles de validation ;
- rapport attendu.

Le protocole est versionné, signé et distribué par pack.

## Formulaires contextuels

Exemple :

si état sanitaire = dépérissant, afficher :

- déficit foliaire ;
- branches mortes ;
- symptômes ;
- cause suspectée ;
- photo ;
- confiance.

Le technicien ne voit que les champs nécessaires au moment utile.

## Workflows de validation

Brouillon -> terminé -> contrôlé automatiquement -> à corriger -> validé -> contrôlé par responsable -> verrouillé.

## Tableaux de bord par métier

### Technicien territorial

- tournée ;
- martelage ;
- travaux ;
- échéances ;
- santé ;
- documents ;
- alertes.

### Travaux

- prescription ;
- entreprise ;
- quantités ;
- risques ;
- avancement ;
- non-conformités ;
- réception ;
- réserves.

### Exploitation

- lot ;
- produits ;
- qualité ;
- accès ;
- débardage ;
- dépôt ;
- transport ;
- estimation ;
- réception réelle.

### SIG

- projections ;
- géométries ;
- topologie ;
- couches ;
- relations ;
- import ;
- synchronisation ;
- métadonnées.

### Étudiant

- explications ;
- protocoles guidés ;
- exercices ;
- comparaison manuel/automatique ;
- contrôle pédagogique.

### Formateur

- distribution de missions ;
- récupération ;
- correction ;
- annotation ;
- comparaison de groupes ;
- export.

## Catalogue de protocoles

- officiels ;
- organisationnels ;
- pédagogiques ;
- communautaires validés.

Métadonnées :

- auteur ;
- organisme ;
- version ;
- licence ;
- territoire ;
- date ;
- compatibilité ;
- champs ;
- règles ;
- tests ;
- livrables.

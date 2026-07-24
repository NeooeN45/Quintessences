# Proposition de plan de réalisation — Quintessences

| Champ | Valeur |
|---|---|
| Statut | Proposed — validation fondateur requise |
| Date | 2026-07-24 |
| Nature | Document de travail, non normatif |
| Portée | Quintessences, GSIE, Forge, GeoSylva, Hub et Ignis |

> Ce document consolide les réponses données pendant l'entretien fondateur.
> Il ne remplace pas la Constitution, les décisions, les RFC, les
> spécifications ou les roadmaps officielles. Ces sources ne seront modifiées
> qu'après validation complète de la proposition et enregistrement formel des
> arbitrages.

## 1. Vision consolidée

Quintessences est un programme de recherche et développement, une marque, un
écosystème technologique et une plateforme commune reliant données, moteurs
scientifiques, intelligences artificielles spécialisées et applications.

Sa mission est de combler le retard technologique des métiers
environnementaux, d'améliorer la coordination entre organismes et de permettre
des décisions plus rapides, mieux documentées et plus faciles à comprendre.

Les trois priorités non négociables sont :

1. interface et expérience utilisateur ;
2. qualité scientifique ;
3. intelligence artificielle spécialisée.

Les valeurs de réalisation sont la sécurité humaine, la qualité avant la
vitesse et l'accessibilité des outils.

## 2. Rôle des composants

### 2.1 GSIE

GSIE est le noyau scientifique commun de Quintessences. Il reste principalement
invisible derrière les applications, mais possède une interface experte
d'administration, d'exploration et de contrôle.

Il fournit :

- données fiables et documentées ;
- connaissances scientifiques ;
- corrélations avancées ;
- diagnostics et recommandations ;
- simulations ;
- services d'IA spécialisés ;
- API commune.

### 2.2 GeoSylva

GeoSylva désigne toute la verticale forestière de Quintessences, comprenant
l'application Android existante, les services forestiers GSIE, la
synchronisation et les visualisations associées.

L'utilisateur principal est un professionnel forestier de terrain. Le profil
de référence est le technicien réalisant inventaires, martelage,
géolocalisation et suivi de parcelles, souvent hors ligne.

### 2.3 Forge

Forge est d'abord une infrastructure interne stratégique. Il sera renforcé
avant toute ouverture à des partenaires. Une ouverture contrôlée, puis un
produit autonome, ne seront envisagés qu'après validation de sa qualité et de
son utilité réelles.

### 2.4 Hub

Le Hub est le jumeau numérique immersif de Quintessences. Il combine :

1. simulation ;
2. exploration interactive ;
3. centre de commandement ;
4. formation.

Le premier Hub est conçu pour un gestionnaire forestier et synchronise quatre
représentations principales : vue 3D, carte 2D, schémas/graphiques et
comparaison de scénarios.

### 2.5 Ignis

Ignis avance en parallèle de GeoSylva/Hub après consolidation du socle GSIE
commun. Sa première validation repose sur la reproduction d'un incendie
historique documenté. Les drones sont différés ; seules les études et
expérimentations de communication pourront commencer après stabilisation du
cœur logiciel.

## 3. Principes d'architecture produit

### 3.1 Architecture générale, première implémentation locale

Quintessences est conçu dès le départ comme un système générique,
multi-territoires et multi-domaines. Chizé-Aulnay est la première
implémentation et la première preuve, pas la frontière du produit.

Règles :

- aucun élément propre à Chizé n'est codé en dur ;
- les capsules Forge suivent un contrat territorial générique ;
- GSIE charge des profils territoriaux interchangeables ;
- les modèles sont configurables et versionnés ;
- le Hub peut charger plusieurs jumeaux numériques ;
- les connecteurs de données sont réutilisables ;
- un territoire indépendant vérifie ensuite la portabilité.

### 3.2 Domaine avant application

L'eau, la flore, la faune et les autres domaines sont d'abord intégrés comme
données, moteurs, corrélations et couches GSIE. Une application autonome n'est
créée que si un utilisateur, un problème, un parcours et un modèle d'usage
autonomes sont validés.

### 3.3 Autonomie fondée sur le risque

- Les opérations de données peuvent devenir automatiques après validation.
- Les simulations peuvent être automatiques, journalisées et annulables.
- Les diagnostics et recommandations sont explicables et corrigeables.
- Les décisions critiques exigent une validation humaine préalable.
- Les systèmes liés à la sécurité vitale exigent une autorisation humaine et
  un arrêt d'urgence.

### 3.4 Réalité, simulation et historique

Toutes les interfaces distinguent strictement :

- l'état observé et horodaté ;
- l'état simulé et incertain ;
- le rejeu historique.

Chaque couche indique son origine, sa fraîcheur et sa fiabilité.

## 4. Portefeuille proposé

| Statut | Chantiers |
|---|---|
| P0 actif | Socle GSIE commun, qualité GeoSylva, Forge territorial, Hub de simulation |
| P1 parallèle | Ignis par simulation historique et validation SDIS |
| Étude | Drones, communications alternatives, calcul GPU cloud, futur matériel |
| Différé | Forge partenaires, internationalisation, formation immersive complète |
| En attente | Applications Hydro, Flora, Artemis et QGISIA |

Les domaines eau, flore et faune restent actifs dans GSIE lorsqu'ils sont
nécessaires aux simulations, sans imposer la création immédiate des
applications correspondantes.

## 5. Première implémentation de référence

### 5.1 Territoires

1. RBI de Chizé ;
2. forêt de Chizé ;
3. forêt d'Aulnay.

La première étude observe et simule la dynamique naturelle des trois
territoires. Les scénarios d'intervention sylvicole sont différés jusqu'à
validation de cette dynamique.

### 5.2 Sorties scientifiques minimales

- état écologique initial ;
- trajectoire probable avec intervalle d'incertitude ;
- évolution des essences, de la structure et de la régénération ;
- mortalité et recrutement ;
- risques biotiques et abiotiques dominants ;
- facteurs expliquant les différences entre territoires ;
- seuils ou points de bascule possibles ;
- coefficient de fiabilité décomposé ;
- sources et données manquantes.

### 5.3 Données P0

1. état initial arbre/placette daté et géoréférencé ;
2. remesures historiques ;
3. sols fonctionnels locaux ;
4. microclimat et eau sous couvert ;
5. historique de gestion et de perturbations ;
6. pression des ongulés ;
7. jeu indépendant de calibration et validation.

La première phase n'installe pas de nouveaux capteurs. Elle utilise les données
existantes et réduit explicitement la fiabilité lorsque les données P0
manquent.

Les données personnelles issues du stage restent en quarantaine privée jusqu'à
vérification formelle de leurs droits.

## 6. Livrables ordonnés

### L0 — Alignement et contrats

- corriger les statuts et sources périmés ;
- enregistrer le nouvel ordre produit ;
- définir les contrats génériques de capsule, territoire, simulation et couche ;
- définir les barrières de qualité communes.

Critère de sortie : une seule trajectoire cohérente entre vision, décisions,
spécifications et roadmaps.

### L1 — GeoSylva Terrain Quality

- gel des nouvelles fonctions majeures ;
- petites fonctions de qualité autorisées ;
- mode Martelage terrain ;
- mode pluie et protection contre les retours accidentels ;
- écran maintenu allumé ;
- retours haptiques différenciés ;
- sauvegarde et reprise sans perte ;
- historique et provenance des mesures ;
- contrôle qualité actif ;
- tests sur plusieurs niveaux de téléphone.

Critère de sortie : une mission réelle est réalisable sans fiche papier et sans
perte de données.

### L2 — Forge Capsule territoriale

- séparation données publiques, autorisées et privées ;
- conservation des fichiers bruts ;
- licences, empreintes, versions et provenance ;
- extraction et normalisation reproductibles ;
- détection des doublons, contradictions et péremptions ;
- rapport de couverture des sept familles P0 ;
- validation humaine avant publication.

Critère de sortie : une capsule territoriale versionnée est reproductible et
consommable par GSIE sans dépendance au code propre à Chizé.

### L3 — GSIE vertical forestier

Implémenter les capacités minimales nécessaires dans Evidence, Knowledge, GIS,
Climate, Botanical, Pedology, Correlation, Diagnostic, Forest Dynamics et
Simulation, sans attendre la complétude horizontale des quatorze moteurs.

Critère de sortie : une capsule réelle produit une trajectoire, ses preuves,
son incertitude et ses facteurs explicatifs via une API stable.

### L4 — Hub multi-vues

- jumeau numérique chargeable par profil territorial ;
- vue 3D immersive ;
- carte 2D ;
- schémas et graphiques ;
- comparaison de scénarios ;
- ligne temporelle ;
- interrogation des zones et objets ;
- séparation observé/simulé/historique.

Critère de sortie : un gestionnaire peut comprendre et comparer les trajectoires
des trois territoires sans assistance technique.

### L5 — Ignis historique

- sélectionner un feu documenté ;
- produire sa capsule de données ;
- simuler la propagation ;
- comparer prédiction et observation ;
- mesurer les erreurs spatiales et temporelles ;
- afficher le rejeu et la simulation dans le Hub ;
- faire relire le résultat par un professionnel SDIS.

Critère de sortie : un prototype préopérationnel mesuré, sans revendication
d'usage réel en intervention.

### L6 — Validation et démonstration

- benchmark GSIE contre plusieurs experts en aveugle ;
- tests terrain GeoSylva ;
- mesures de temps, erreurs et coordination ;
- tests de sécurité, restauration et performance ;
- démonstrations GeoSylva–GSIE–Hub et Ignis ;
- dossier scientifique et captation professionnelle.

Critère de sortie : une démonstration visuellement forte, utile et accompagnée
de preuves vérifiables.

## 7. Capacité et mode d'exécution

- Fondateur : 35 heures par semaine.
- Budget personnel : 1 000 euros sur six mois.
- Poste actuel : i5-11300H, 32 Go RAM, RTX 3050 Laptop 4 Go.
- Téléphone principal : Samsung Galaxy S25 Ultra.
- Tests futurs : téléphone Android milieu de gamme et appareil limité ou
  renforcé.
- Testeur métier quotidien : BTS Gestion forestière et pompier volontaire.
- Partenaire potentiel : technicien chargé de la gestion de la RBI.
- Contact SDIS possible pour la validation des besoins Ignis.

Le calcul intensif est hybride : local par défaut et ressources GPU louées
ponctuellement, avec quotas, arrêt automatique et coût par exécution.

## 8. Rythme et barrières de livraison

Rythme :

- retours terrain quotidiens ;
- revue qualité hebdomadaire ;
- incrément intégré mensuel.

Une version importante exige :

- compilation, lint, typage et tests verts ;
- migration sans perte de données ;
- parcours hors ligne vérifié ;
- test réel des fonctions terrain modifiées ;
- contrôle visuel et test utilisateur ;
- comparaison scientifique aux références disponibles ;
- provenance et incertitude correctes ;
- sécurité et confidentialité vérifiées ;
- documentation et démonstration mises à jour ;
- test final du fondateur concluant.

## 9. Mesures de succès

Premiers indicateurs :

1. temps économisé ;
2. diminution des erreurs ;
3. amélioration de la coordination.

Objectifs de qualité :

- GeoSylva devient indispensable au professionnel de terrain ;
- GSIE atteint une qualité comparable aux experts sur un benchmark
  indépendant ;
- le Hub devient remarquable, utile et compréhensible ;
- Ignis reproduit un événement historique avec des erreurs mesurées.

## 10. Éléments explicitement non décidés

- dates contractuelles des livrables ;
- seuils numériques de fiabilité ;
- modèle ou fournisseur IA définitif ;
- matériel à acheter dans deux mois ;
- licence finale de chaque dépôt ;
- prix et modèle d'abonnement détaillés ;
- choix du feu historique Ignis ;
- date d'ouverture de Forge aux partenaires ;
- ordre des futures applications autonomes.

Ces points seront décidés à partir de mesures, de tests ou d'entretiens, pas
par hypothèse documentaire.

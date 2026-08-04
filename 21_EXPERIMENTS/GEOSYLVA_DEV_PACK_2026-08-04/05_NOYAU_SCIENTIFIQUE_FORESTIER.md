# Noyau scientifique forestier

## Règle fondamentale

Les données observées, les données de référence, les méthodes de calcul, les règles métier et les décisions sont séparées.

```text
Observation
  -> normalisation
  -> sélection de méthode
  -> calcul
  -> contrôle
  -> agrégation
  -> décision
  -> explication
```

## Modèle minimal d'une mesure

- valeur ;
- unité ;
- source ;
- méthode de capture ;
- incertitude ;
- date ;
- auteur ;
- appareil ;
- statut ;
- preuve ;
- correction éventuelle.

## Moteurs

### Measurement Engine

- unités ;
- normalisation ;
- validation ;
- conversions ;
- gestion des valeurs manquantes.

### Dendrometry Engine

- N ;
- N/ha ;
- G ;
- G/ha ;
- Dm ;
- Dg ;
- Hm ;
- Hg/Lorey ;
- distributions ;
- statistiques d'échantillonnage ;
- intervalles de confiance ;
- représentativité.

### Volume Engine

Distinctions obligatoires :

- `VolumeEquation`
- `VolumeTariff`
- `CommercialPrice`

Chaque méthode contient :

- identifiant ;
- version ;
- famille d'équation ;
- variables requises ;
- essences compatibles ;
- groupes compatibles ;
- territoire ;
- plage de diamètre ;
- plage de hauteur ;
- type de volume ;
- écorce ;
- unité ;
- coefficients ;
- source ;
- métriques de validation.

### Method Resolver

Sélection automatique selon :

- essence ;
- groupe ;
- région ;
- peuplement ;
- diamètre ;
- hauteur disponible ;
- type de volume ;
- précision ;
- protocole de l'organisation.

Le résultat doit expliquer le choix et signaler toute extrapolation.

### Calcul par essence

Toujours calculer au niveau le plus fin possible puis agréger :

arbre -> essence -> placette -> strate -> peuplement -> parcelle.

Ne pas appliquer un tarif feuillu moyen à un mélange si des méthodes spécifiques existent.

### Assortment Engine

- découpe théorique ;
- longueur marchande ;
- diamètre fin bout ;
- produits ;
- pertes ;
- rendement ;
- qualité ;
- défauts.

### Valuation Engine

Chaîne :

volume brut -> pertes -> volume commercialisable -> produits -> prix -> qualité -> coûts -> valeur nette -> fourchette -> facteurs explicatifs.

Facteurs :

- essence ;
- dimensions ;
- qualité ;
- défauts ;
- homogénéité du lot ;
- accessibilité ;
- pente ;
- portance ;
- distance de débardage ;
- dépôt ;
- transport ;
- saison ;
- mode de vente ;
- certification ;
- risques.

### Rule Engine

Règles déclaratives, versionnées et testables. Pas de logique forestière dispersée dans les ViewModels.

### Scenario Engine

- aucune intervention ;
- éclaircie ;
- conversion ;
- renouvellement ;
- diversification ;
- enrichissement ;
- libre évolution ;
- comparaison économique, sylvicole et écologique.

### Provenance Engine

Chaque résultat conserve :

- entrées ;
- méthode ;
- version ;
- paramètres ;
- source ;
- date ;
- avertissements ;
- domaine de validité ;
- incertitude ;
- moteur exécutant ;
- hash de la définition.

## Registre central

Exemples d'identifiants :

- METHOD-FR-VOLUME-OAK-002@1.2.0
- PRICE-NA-OAK-BO-2026-Q3@1.0.0
- RULE-THINNING-IRREGULAR-004@2.1.0

## Mode comparaison de méthodes

Pour une même entrée :

- calculer plusieurs méthodes compatibles ;
- afficher médiane, écart, domaine ;
- expliquer les différences ;
- ne pas choisir silencieusement en cas de divergence forte.

## Calibration locale

Possibilité future de calibrer une équation avec des données réelles :

- séparation entraînement/validation ;
- statistiques d'erreur ;
- biais ;
- RMSE ;
- domaine ;
- publication interne versionnée ;
- validation humaine obligatoire.

## Tests exigés

- tests unitaires par méthode ;
- jeux de référence ;
- tests aux limites ;
- tests d'unités ;
- tests d'extrapolation ;
- tests de parité mobile/serveur ;
- tests de migration ;
- tests de non-régression.

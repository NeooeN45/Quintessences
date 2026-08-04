# TreeVision - mesure multimodale des arbres

## Vision

TreeVision combine caméra, profondeur, AR, IMU, GNSS, visées humaines et instruments forestiers afin de produire une observation complète, traçable et assortie d'une incertitude.

## Données estimées

- diamètre à 1,30 m ;
- hauteur totale ;
- hauteur marchande ;
- inclinaison ;
- rectitude ;
- diamètre à plusieurs hauteurs ;
- défauts visibles ;
- position ;
- volume ;
- qualité de mesure.

## Sources possibles

### Diamètre

- caméra ;
- AR Depth ;
- scan multi-angle ;
- compas ;
- ruban ;
- pied à coulisse Bluetooth ;
- saisie manuelle.

### Hauteur

- visée base/cime ;
- clinomètre ;
- reconstruction ;
- télémètre ;
- saisie ;
- modèle.

### Position

- GNSS ;
- constellations multiples ;
- immobilisation ;
- SLAM ;
- azimut/distance ;
- triangulation ;
- RTK externe ;
- points de contrôle ;
- orthophoto ou LiDAR comme contexte de recalage.

## Hiérarchie des sources

Mesure instrumentale directe validée > instrument connecté > vision multi-angle fiable > vision simple > estimation algorithmique > valeur par défaut.

Le moteur ne fait pas une moyenne naïve. Il fusionne selon l'incertitude et conserve les valeurs sources.

## Workflow un arbre

1. vérification du matériel ;
2. viser la base ;
3. estimation du sol ;
4. placement du plan 1,30 m ;
5. scan en arc ;
6. segmentation ;
7. ajustement cercle/ellipse/cylindre ;
8. visée de la cime ;
9. zoom optique si nécessaire ;
10. position ;
11. cohérence ;
12. incertitude ;
13. confirmation ;
14. création de l'observation ;
15. cubage ;
16. synchronisation.

## Viseur

- réticule central ;
- loupe ;
- verrouillage à l'immobilité ;
- capture moyenne ;
- retour haptique ;
- changement d'objectif contrôlé ;
- paramètres intrinsèques recalculés.

## Correction humaine

Le technicien peut :

- modifier le diamètre ;
- déplacer la ligne 1,30 m ;
- corriger les bords ;
- sélectionner la bonne cime ;
- saisir le compas ;
- indiquer un obstacle ;
- refaire le scan.

La valeur automatique est conservée avec la correction et le motif.

## Position améliorée

Lorsque l'utilisateur est immobile :

- accumulation GNSS ;
- moyenne pondérée ;
- rejet d'outliers ;
- filtre de Kalman ;
- stabilité IMU ;
- estimation de dispersion.

La position de l'arbre est dérivée de la position du téléphone, de l'azimut et de la distance. Deux points d'observation permettent une triangulation relative.

## Précision absolue et relative

Toujours distinguer :

- précision nationale/absolue ;
- précision locale/relative dans la placette.

## Indice de confiance

Facteurs :

- distance ;
- visibilité ;
- lumière ;
- mouvement ;
- couverture angulaire ;
- profondeur ;
- cohérence ;
- GNSS ;
- nombre de visées ;
- présence d'obstacles ;
- mesure de référence.

## Modes

- rapide ;
- précis ;
- calibration ;
- placette semi-automatique.

## Banc de validation

Pour chaque arbre :

- diamètre réel ;
- circonférence ;
- hauteur de référence ;
- position de référence ;
- essence ;
- écorce ;
- pente ;
- lumière ;
- distance ;
- téléphone ;
- vidéo ;
- profondeur ;
- résultat ;
- correction.

## Boucle GSIE

Mesure automatique -> correction instrumentale -> synchronisation consentie -> analyse -> amélioration -> nouveau pack TreeVision.

Les données client restent privées sauf consentement explicite et cadre défini.

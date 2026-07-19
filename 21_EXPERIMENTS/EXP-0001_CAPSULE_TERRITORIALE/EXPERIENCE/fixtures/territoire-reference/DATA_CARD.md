# Data Card — territoire de référence EXP-0001

| Champ | Valeur |
|---|---|
| **Identifiant** | `gsie-demo-territoire-001` |
| **Nature** | entièrement synthétique |
| **Finalité** | test logiciel et démonstration |
| **Usage opérationnel** | interdit |
| **Données personnelles** | aucune |
| **Droits tiers** | aucun contenu tiers redistribué |
| **Licence de la fixture** | CC0-1.0 |
| **Revue scientifique** | non réalisée |

## Contenu

La fixture décrit un petit polygone fictif en EPSG:4326, trois observations
d'arbres inventées et une fiche de formule. Les coordonnées ne représentent
pas une parcelle cadastrale, un peuplement réel ou un diagnostic de terrain.

## Risques d'usage abusif

- interpréter les observations comme un inventaire réel ;
- présenter les valeurs comme représentatives d'un climat ou d'une station ;
- prendre une décision sylvicole à partir de la capsule ;
- confondre le statut « calcul reproductible » avec une validation par un
  organisme scientifique.

Ces usages sont interdits. La mention `operational_use: forbidden` est
transportée dans le manifeste signé.

## Remplacement futur

Une fixture pilote réelle devra posséder une data card distincte indiquant au
minimum producteur, millésime, emprise, résolution, méthode, licence,
redistribution, qualité, lacunes, données personnelles, durée de conservation
et validation métier.


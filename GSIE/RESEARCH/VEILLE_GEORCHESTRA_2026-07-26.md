# Veille technologique GSIE — geoOrchestra — 2026-07-26

## Objet

Évaluer geoOrchestra comme source géospatiale externe potentielle pour
Quintessences, sans l'adopter comme composant du socle GSIE.

## Évaluation

| Trouvaille | Source | Pertinence | Maturité | Moteur concerné | Action |
|---|---|---|---|---|---|
| geoOrchestra, infrastructure de données spatiales libre et modulaire | [Site officiel](https://www.georchestra.org/fr/) | Haute | Élevée : projet créé en 2009, communauté et gouvernance établies | GIS Engine | Veille |
| Catalogue GeoNetwork et services GeoServer/GeoWebCache | [Composants officiels](https://www.georchestra.org/fr/logiciel.html) | Haute pour la découverte, l'affichage et l'ingestion de données externes | Élevée, composants géospatiaux largement établis | GIS Engine, GSIE API | Évaluer un connecteur |
| Data API et standards OGC | [Documentation officielle](https://www.georchestra.org/fr/documentation.html) | Haute pour l'interopérabilité | Moyenne à élevée selon la version et l'instance exposée | GIS Engine | Tester OGC API Features puis WFS |
| Version 26.0.0 | [Versions GitHub](https://github.com/georchestra/georchestra/releases) | Moyenne pour GSIE à court terme | Récente ; Gateway 3 et plusieurs transitions de composants | Déploiement, GIS Engine | Ne pas intégrer immédiatement |

## Position pour Quintessences

geoOrchestra est retenu comme **source externe potentielle future** et non
comme source de vérité ou dépendance du cœur GSIE. Une instance geoOrchestra
peut fédérer et publier des jeux issus de producteurs différents ; elle
n'est donc pas, à elle seule, le producteur ni le garant juridique des
données diffusées.

Une intégration éventuelle devra suivre ce flux :

```text
Instance geoOrchestra
        ↓
Connecteur OGC/API GSIE
        ↓
Validation des métadonnées et de la licence
        ↓
Normalisation et stockage GSIE
        ↓
GIS Engine et applications
```

## Conditions avant ingestion

- identifier l'instance, le producteur réel et l'URL de service ;
- relever la licence au niveau du jeu de données, sans la déduire de la
  licence logicielle de geoOrchestra ;
- enregistrer la provenance, la date de collecte, la date des données, le
  système de coordonnées et la résolution ;
- préférer OGC API Features ou WFS pour les objets vectoriels ;
- réserver WMS/WMTS à la visualisation lorsque les objets sources ne sont
  pas téléchargeables ;
- normaliser et mettre en cache les données dans le stockage GSIE ;
- prévoir les limites de disponibilité, quotas, pagination, reprise et
  détection des changements ;
- interdire toute dépendance directe des applications à l'instance externe.

## Risques

- qualité, fraîcheur et licence variables entre jeux et instances ;
- services OGC parfois limités ou configurés différemment ;
- cycle de support majeur annoncé de douze mois pour geoOrchestra ;
- documentation technique inégale sur certains modules ;
- confusion possible entre licence du logiciel et licence des données.

## Recommandation

Conserver geoOrchestra en **priorité 3 — veille / inspiration à moyen
terme**. Lorsqu'une instance concrète apportera un jeu utile au territoire
pilote, réaliser un test de connecteur borné avec métadonnées, licence,
pagination, reprise sur erreur et import PostGIS. Cette inscription
n'autorise ni déploiement de la suite, ni modification du contrat actuel du
GIS Engine.

## Sources à référencer

- [geoOrchestra — site officiel](https://www.georchestra.org/fr/)
- [geoOrchestra — logiciel et services](https://www.georchestra.org/fr/logiciel.html)
- [geoOrchestra — documentation](https://www.georchestra.org/fr/documentation.html)
- [geoOrchestra — documentation principale](https://docs.georchestra.org/georchestra/)
- [geoOrchestra — versions GitHub](https://github.com/georchestra/georchestra/releases)
- [geoOrchestra — dépôt GitHub](https://github.com/georchestra/georchestra)

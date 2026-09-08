# Quintessences — Resource Integration Radar

> Registre vivant des technologies, modèles, datasets, API, standards, bibliothèques et idées d'intégration candidates pour l'écosystème Quintessences.

## Objectif

Ce document évite d'accumuler des notes de veille dispersées. Chaque ressource candidate est évaluée, reliée à l'architecture GSIE et suivie jusqu'à une décision explicite : **ADOPTER**, **POC**, **SURVEILLER**, **REJETER** ou **INTÉGRÉ**.

Une idée n'est jamais considérée comme validée uniquement parce qu'elle est récente ou impressionnante. Elle doit être sourcée, testable et comparée à la stack existante.

## États

- **CANDIDATE** : ressource identifiée, validation initiale en cours.
- **À ÉVALUER** : intéressante mais informations ou preuves insuffisantes.
- **POC** : expérimentation concrète justifiée.
- **ADOPTER** : intégration recommandée.
- **INTÉGRÉ** : intégré et suivi par les tests/benchmarks.
- **SURVEILLER** : prometteur mais trop immature, coûteux ou prématuré.
- **REJETÉ** : ne justifie pas l'intégration ou la migration.
- **REMPLACÉ** : supersédé par une meilleure ressource.

## Score /100

| Critère | Poids |
|---|---:|
| Impact produit / scientifique | 20 |
| Adéquation architecture Quintessences | 20 |
| Gain de temps ou R&D | 15 |
| Qualité scientifique / technique | 10 |
| Maturité / maintenabilité | 10 |
| Facilité d'intégration | 10 |
| Licence / coût / souveraineté | 10 |
| Testabilité / observabilité | 5 |

## Fiche standard d'une ressource

Chaque entrée doit contenir au minimum :

- **Nom**
- **Type** : modèle / bibliothèque / dataset / API / standard / architecture / outil / matériel
- **Date de vérification**
- **Source primaire**
- **Version / commit / release étudié**
- **Licence et compatibilité commerciale**
- **Modules Quintessences concernés**
- **Problème résolu**
- **Ce que cela remplace ou complète**
- **Intégration proposée dans GSIE**
- **Dépendances**
- **Matériel / infrastructure requis**
- **Coût estimé**
- **Risques / limites**
- **Effort** : S (<1 jour), M (1–5 jours), L (1–4 semaines), XL (>1 mois)
- **Score /100**
- **Décision**
- **POC minimal**
- **Critères de réussite**
- **Critères d'abandon**
- **Tests de non-régression à ajouter si intégré**

## Règles d'enrichissement quotidien

1. Lire d'abord ce registre et les documents spécialisés existants afin d'éviter les doublons.
2. Vérifier la source officielle, la date réelle, la licence et l'état du projet.
3. Comparer explicitement la ressource à la stack actuelle.
4. Ne pas créer une nouvelle entrée pour une simple mise à jour mineure : enrichir l'entrée existante.
5. Ne jamais présenter un paper sans code comme une brique prête à intégrer.
6. Ne jamais présenter une API propriétaire comme équivalente à une technologie auto-hébergeable sans préciser la dépendance fournisseur.
7. Une ressource à fort impact doit proposer un POC mesurable.
8. Toute adoption doit conduire à un benchmark ou à un test reproductible.
9. Les changements qui affectent la Constitution, une RFC, un ADR, le métamodèle ou une interface publique doivent passer par une décision d'architecture, pas par une simple modification de ce registre.
10. Si aucune nouveauté n'apporte de valeur réelle, ne rien ajouter.

## Axes permanents de recherche

### QMF — Quintessences Model Factory
- modèles spécialisés environnementaux ;
- DAPT / SFT / DPO / GRPO ;
- distillation et quantification ;
- génération de données synthétiques ;
- évaluation automatique et QEB ;
- serving local / edge / GPU ;
- routage et orchestration de petits modèles.

### GSIE Data Ecosystem
- catalogues de sources ;
- acquisition incrémentale ;
- normalisation ;
- qualité et provenance ;
- data lake Bronze / Silver / Gold ;
- GeoParquet / Zarr / xarray ;
- feature stores géospatiaux ;
- détection de lacunes dans les datasets.

### GeoSylva
- LiDAR et nuages de points ;
- inventaire forestier ;
- dendrométrie ;
- segmentation individuelle des arbres ;
- télédétection ;
- santé / dépérissement ;
- biomasse / carbone ;
- SIG mobile offline-first.

### IGNIS / Atmos
- prévision météo IA ;
- downscaling ;
- vent local ;
- propagation feu / fumée ;
- détection satellite / caméra ;
- simulation et assimilation de données.

### Hydro / Terra / Flora / Artemis
- hydrologie et crues ;
- sols et géologie ;
- botanique / habitats / phénologie ;
- faune / bioacoustique / camera traps / tracking.

### GSIE Server / Hub Unreal / Edge
- bases spatio-temporelles ;
- event streaming ;
- CRDT et synchronisation offline-first ;
- jumeaux numériques ;
- server meshing ;
- calcul distribué ;
- LoRa / Meshtastic ;
- edge AI / TinyML ;
- drones / ROS 2 / PX4 / ArduPilot.

## Backlog initial à réévaluer

Les pistes déjà identifiées dans les travaux précédents doivent être réévaluées selon la grille ci-dessus avant adoption :

- WeatherNext / WeatherNext 2 / WeatherNext 3 pour Atmos ;
- NVIDIA Earth-2 / CorrDiff pour downscaling et météo scientifique ;
- projets open source de prédiction incendie et CFFDRS/FBP ;
- modèles de fondation Earth Observation ;
- frameworks agents géospatiaux et outils EO ;
- bibliothèques de traitement LiDAR / raster / vectoriel accéléré ;
- technologies de synchronisation et réplication offline-first.

---

Dernière règle : **une découverte rare à très fort impact vaut davantage que vingt ajouts moyens**.

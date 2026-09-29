# ADR — Utilisation de WeatherNext dans Atmos

| Champ | Valeur |
|---|---|
| **Identifiant** | ADR-WEATHERNEXT-ATMOS-001 |
| **Statut** | Proposition — Draft |
| **Date** | 2026-08-18 |
| **Périmètre** | Atmos et consommateurs GSIE |
| **Décisionnaire** | Fondateur, après POC et revue scientifique |

## 1. Contexte

WeatherNext 2 est un modèle global probabiliste de moyen terme. Le dépôt
public v0.3.0 expose un code de recherche Alpha, des checkpoints et des
utilities JAX/xarray, tandis que Google publie aussi des flux opérationnels et
historiques via BigQuery, Earth Engine et Google Cloud Storage.

Quintessences a besoin de forcings météo pour Atmos, IGNIS, Hydro, GeoSylva et
Terra, mais doit éviter :

- dépendance à un fournisseur unique ;
- confusion entre résolution globale et prévision locale ;
- perte de l'incertitude ;
- licence non qualifiée des poids ou données ;
- auto-hébergement GPU prématuré.

## 2. Options

### Option A — API/data only

Atmos consomme les flux WeatherNext autorisés sans faire tourner les poids.

**Avantages** : délai et coût d'intégration faibles, pas de GPU, maintenance
limitée.

**Risques** : dépendance au fournisseur, disponibilité et conditions de flux,
moins de contrôle sur l'inférence.

### Option B — Inference self-hosted

Quintessences télécharge les poids et exécute WN2 dans un worker GPU/TPU.

**Avantages** : contrôle, reproductibilité du runtime, possibilité d'inférence
privée.

**Risques** : H100/TPU, VRAM, stockage, JAX/Haiku, licences, API Alpha,
maintenance et coût opérationnel.

### Option C — Hybrid provider abstraction

Atmos définit un contrat `AtmosProvider`, consomme WeatherNext/ECMWF/Météo-France
et peut déléguer ponctuellement une inférence autonome à un worker qualifié.

**Avantages** : indépendance, comparaison scientifique, remplacement fournisseur,
POC sans GPU puis extension progressive.

**Risques** : plus de conception de registre et de normalisation.

### Option D — Fine-tuned Atmos custom

Quintessences fine-tune WN2 ou construit un modèle régional spécialisé.

**Avantages** : adaptation au territoire et aux variables propres.

**Risques** : corpus français, séparation spatio-temporelle, calibration,
licences, coût, responsabilité scientifique et risque de sur-ajustement.

## 3. Décision proposée

**Retenir l'Option C, commencer opérationnellement par l'Option A, et réserver B/D
à des tranches conditionnelles.**

```text
AtmosProvider
 ├── WeatherNextFeedProvider
 ├── ECMWFProvider
 ├── MeteoFranceProvider
 ├── ObservationProvider
 └── OptionalSelfHostedModelProvider
```

WeatherNext 2 est le premier provider à benchmarker, pas le seul provider à
faire confiance. L'auto-hébergement ne sera autorisé qu'après :

1. benchmark français montrant un gain utile ;
2. budget matériel et coût total connus ;
3. licences code/poids/données/flux qualifiées ;
4. artefacts inscrits au Model Registry ;
5. validation des extrêmes et incertitudes ;
6. worker reproductible et observable.

## 4. Conséquences

### Positives

- le POC peut démarrer sans GPU dédié ;
- IGNIS et Hydro consomment un contrat Atmos neutre ;
- WeatherNext peut être comparé à ECMWF et Météo-France ;
- les sorties gardent membres, quantiles, spread et provenance ;
- un provider peut être retiré sans réécrire les moteurs.

### Négatives

- il faut construire un registre de schéma et de provenance ;
- la valeur ne sera pas démontrée avant le benchmark local ;
- le downscaling reste un composant distinct ;
- la consommation des flux dépend d'autorisations et de termes externes.

## 5. Garde-fous scientifiques

- `native_grid_resolution` n'est jamais présenté comme une précision locale ;
- toutes les transformations sont versionnées ;
- les modèles et datasets ont des domaines de validité ;
- une moyenne n'efface jamais l'ensemble ;
- les probabilités affichent le nombre de membres ;
- aucune sortie ne remplace une alerte officielle ;
- les extrêmes sont évalués séparément ;
- les observations terrain et sources officielles gardent leur statut propre.

## 6. Critères de révision

L'ADR sera révisée après le POC selon :

- score WN2 contre baselines par variable/horizon ;
- coût par run et par zone ;
- latence ingestion → API ;
- disponibilité des flux ;
- calibration de l'ensemble ;
- utilité IGNIS/Hydro ;
- licences et possibilité de redistribution ;
- charge opérationnelle.

## 7. Sources

- WeatherNext repository v0.3.0 : https://github.com/google-deepmind/weathernext/tree/v0.3.0
- WeatherNext models : https://developers.google.com/weathernext/guides/models
- WeatherNext data access : https://developers.google.com/weathernext/guides/access-forecast
- FGN : https://arxiv.org/abs/2506.10772
- Model Fabric Quintessences : `02_RFC/RFC-0015-environmental-model-fabric.md`
- GSIE-Bench : `02_RFC/RFC-0039-gsie-bench-v0-1.md`

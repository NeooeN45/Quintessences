# WeatherNext 2 — Deep Dive pour Quintessences

| Champ | Valeur |
|---|---|
| **Statut** | Analyse R&D — Draft |
| **Version de référence** | WeatherNext repository `v0.3.0` |
| **Commit de référence** | `89c4b2a77a1c57b328b909c575550fd2e5aadc9c` |
| **Dépôt** | https://github.com/google-deepmind/weathernext |
| **Dernier commit observé sur `main`** | `9c034db1ff41`, 2026-08-11 |
| **Licence code** | Apache-2.0 |
| **Licence autres matériaux / poids** | CC BY 4.0 selon le README v0.3.0 ; les conditions de données temps réel sont séparées |
| **Maturité déclarée** | Code de recherche Alpha, API susceptible de changer |
| **Date d'analyse** | 2026-08-18 |

## 1. Résumé exécutif

### Faits vérifiés

WeatherNext 2 (WN2) est un modèle atmosphérique global de moyen terme,
présenté par Google DeepMind et Google Research. Le dépôt v0.3.0 contient le
code WN2, WeatherNext Cyclones, WeatherNext Graph/GraphCast et WeatherNext
Gen/GenCast.

WN2 est un modèle probabiliste fondé sur une **Functional Generative Network
(FGN)**. Le code public expose une architecture de type encodeur points/grille →
maillage icosaédrique → processeur graph-transformer → décodage vers grille,
avec des wrappers xarray/JAX, normalisation, rollouts autorégressifs,
sharding et ensembles.

La documentation officielle indique pour WN2 :

- résolution spatiale globale de 0,25° (~30 km à l'équateur) ;
- prévisions de 6 heures ;
- initialisations toutes les 6 heures ;
- horizon jusqu'à 15 jours ;
- variables de surface et variables sur niveaux de pression ;
- prédiction expérimentale horaire accessible dans certaines offres ;
- vent à 100 m disponible pour WN2 ;
- code optimisé prioritairement pour TPU ;
- modèles complets nécessitant typiquement un H100 pour l'inférence GPU ;
- modèle Cyclones Mini destiné aux environnements plus contraints, à 1°.

### Conclusion Quintessences

La meilleure trajectoire est hybride :

```text
Phase 1 : consommer les flux WeatherNext 2
Phase 2 : normaliser dans Atmos et stocker les sous-ensembles utiles
Phase 3 : comparer WeatherNext à ECMWF/Météo-France sur la France
Phase 4 : downscaling et correction de biais régionaux
Phase 5 : auto-hébergement uniquement si un benchmark et un besoin opérationnel le justifient
```

WN2 ne doit pas devenir directement la source d'IGNIS ou d'Hydro. Il doit être
un fournisseur interchangeable derrière Atmos.

## 2. Architecture réelle du dépôt

### Arborescence utile

```text
weathernext/
├── cyclones/                 # pipeline, tracker direct, IBTrACS
├── utils/
│   ├── autoregressive.py     # feedback des prédictions dans les entrées
│   ├── checkpoint.py         # chargement/sérialisation des poids
│   ├── data_modalities.py    # grille, points, données globales, mesh
│   ├── ensemble.py           # dimension sample pour les ensembles
│   ├── icosahedral_mesh.py   # maillage icosaédrique
│   ├── losses.py             # pertes pondérées et diagnostics
│   ├── normalization.py      # normalisation, résidus et dénormalisation
│   ├── rollout.py            # exécution multi-échantillons et sharding
│   ├── sharding.py           # axes et placement JAX
│   ├── typed_graph_net.py    # briques GNN typées
│   ├── update_blocks.py      # encodeur/processeur/décodeur
│   └── xarray_tree.py        # PyTree xarray
├── weathernext1_graph/       # GraphCast, legacy déterministe
├── weathernext1_gen/         # GenCast, diffusion probabiliste
└── weathernext2/
    ├── architecture.py       # ForwardPass FGN
    ├── architecture_utils.py # classification grille/global
    ├── configs/               # configurations Fiddle sérialisées
    └── fgn.py                 # Predictor FGN, bruit et CRPS
```

### Versions et activité

Le dépôt compte 54 commits au moment de l'analyse. Le tag `v0.3.0` a été publié
le 2026-08-06. Le commit suivant ajoute WN2, puis les commits suivants mettent à
jour la documentation et les citations. Le dépôt est donc actif, mais sa propre
documentation le qualifie de code de recherche fourni « as-is » et recommande
de pinner une release.

## 3. Chaîne données → modèle → produit

```text
ERA5 / HRES / état initial opérationnel
              ↓
      xarray.Dataset + coordonnées
              ↓
   normalisation par niveau et variable
              ↓
  classification grille / global / forcings
              ↓
   points latitude-longitude → mesh icosaédrique
              ↓
      encodeur de points et features spatiales
              ↓
    graph-transformer sur maillage latent
              ↓
      mesh → grille latitude-longitude
              ↓
     sortie un pas de temps (FGN)
              ↓
        wrapper autorégressif
              ↓
    horizon 6 h…15 jours selon cible
              ↓
  plusieurs samples/bruits et plusieurs seeds
              ↓
 xarray de prévision + statistiques d'ensemble
              ↓
    stockage/produits/trackers aval
```

## 4. Représentation des données

### Entrées

La configuration `WeatherNext2.json` définit notamment des champs d'entrée :

- température et géopotentiel sur niveaux de pression ;
- composantes U/V du vent ;
- vitesse verticale ;
- humidité spécifique ;
- température à 2 m ;
- pression moyenne au niveau de la mer ;
- vent à 10 m ;
- température de surface de la mer ;
- vent à 100 m ;
- géopotentiel de surface ;
- masque terre/mer ;
- variables cycliques saisonnières et diurnes.

La configuration liste 13 niveaux de pression :

```text
50, 100, 150, 200, 250, 300, 400,
500, 600, 700, 850, 925, 1000 hPa
```

Les données sont des `xarray.Dataset`, les dimensions et les noms de variables
portant une partie importante du contrat. `xarray_jax` enregistre ces structures
comme PyTrees JAX afin de conserver coordonnées et métadonnées autour des
arrays compilés.

### Sorties

WN2 prédit des variables atmosphériques de surface et de pression. Dans la
configuration publique, on trouve notamment :

- température ;
- géopotentiel ;
- U/V du vent ;
- vitesse verticale ;
- humidité spécifique ;
- température à 2 m ;
- pression au niveau de la mer ;
- vent à 10 m ;
- température de surface de la mer ;
- vent à 100 m ;
- précipitation totale sur 6 h ;
- variables de cyclones pour les modèles concernés.

La disponibilité exacte d'une variable dépend du modèle, du checkpoint et du
flux consommé. Atmos doit donc utiliser un catalogue de schéma par provider,
et non supposer que tous les modèles exposent le même tenseur.

## 5. Architecture spatiale

`architecture.py` construit un maillage triangulaire icosaédrique avec
`mesh_num_splits=6` pour la configuration WN2 publique. Le chemin de calcul est
conceptuellement :

```text
LatLonGridData / LatLonPointsData
        ↓ points_to_mesh_model_ctor
TriangularMeshData
        ↓ mesh_model_ctor
maillage latent graph-transformer
        ↓ mesh_to_grid_model_ctor
LatLonGridData
```

Le maillage n'est pas une grille locale uniforme et ne donne pas une précision
locale gratuite. La résolution affichée de 0,25° décrit le produit global ; la
résolution prédictive effective reste celle validée par les métriques et le
domaine de calibration.

### Abstractions réutilisables

Les parties conceptuellement réutilisables par Quintessences sont :

- conteneurs de données spatiales génériques ;
- conversion points/grille/mesh ;
- features géométriques et topologiques ;
- GNN sur graphe irrégulier ;
- interfaces prédicteur et wrappers ;
- normalisation explicite ;
- rollout autorégressif ;
- sharding par axes nommés ;
- ensembles et calcul de métriques probabilistes.

Le code WN2 lui-même ne doit pas être transformé en moteur incendie ou hydro
par simple changement de noms de variables : les opérateurs physiques, les
observations et les domaines de validité diffèrent.

## 6. Rollout autorégressif

`utils/autoregressive.py` enveloppe un prédicteur un pas :

1. prend une fenêtre d'états initiaux ;
2. prédit le prochain état ;
3. réinjecte les variables cibles dans la fenêtre ;
4. injecte les forcings de l'échéance suivante ;
5. répète jusqu'à la longueur demandée.

Les variables statiques restent des entrées constantes. Les variables temporelles
doivent être des cibles ou des forcings pour pouvoir être traitées correctement.
Un `hk.scan` limite la matérialisation naïve de toute la séquence et un mode de
rematerialisation peut réduire la mémoire au prix de calcul supplémentaire.

### Risque important

L'erreur de modèle et la dérive autorégressive peuvent s'accumuler avec
l'horizon. Atmos doit conserver le champ `forecast_horizon`, la version du
modèle et les métriques par échéance ; une moyenne sur 15 jours ne suffit pas.

## 7. Génération probabiliste

FGN injecte un bruit dans le prédicteur et expose une dimension `sample`. Le
code `fgn.py` :

- empile batch et sample pour exécuter le réseau ;
- désempile les sorties ;
- calcule une perte CRPS à partir des erreurs absolues et des différences
  entre membres ;
- masque les valeurs non valides avant le terme de spread ;
- permet un estimateur unbiased pour l'ensemble.

Le papier FGN décrit une approche entraînée directement avec une perte CRPS sur
des marginales par localisation et variable, tout en cherchant à préserver la
structure spatiale jointe.

Pour Quintessences, cela signifie que l'ensemble doit être conservé comme
information, et non réduit immédiatement à une moyenne.

```text
ensemble brut
 ├── moyenne / médiane
 ├── quantiles
 ├── spread / variance
 ├── probabilités de dépassement
 ├── membres extrêmes
 └── provenance de chaque membre
```

## 8. Prétraitements et normalisation

`normalization.py` sépare :

- `mean_by_level` et `stddev_by_level` pour les valeurs ;
- `diffs_stddev_by_level` pour les résidus ;
- ajout du dernier état d'entrée après dénormalisation des résidus.

Cette distinction est critique : une normalisation de modèle n'est pas une
correction de biais physique. Atmos doit conserver séparément :

```text
normalisation modèle
correction statistique
assimilation d'observations
downscaling
reprojection
```

Aucune de ces opérations ne doit être invisible dans la provenance.

## 9. Variantes

| Variante | Nature | Résolution / horizon | Utilité Quintessences | Choix |
|---|---|---|---|---|
| WeatherNext 2 | FGN probabiliste | 0,25°, 6 h, jusqu'à 15 jours | fournisseur global principal | **POC flux** |
| WeatherNext Cyclones | FGN avec poids cyclone indépendants | 0,25°, jusqu'à 15 jours | trajectoires et scénarios cycloniques ; intérêt faible pour le pilote forestier métropolitain | **WATCH** |
| Cyclones Mini | version plus légère | 1° | test local, CI scientifique, démonstrateur | **BENCHMARKER** |
| WeatherNext Graph / GraphCast | GNN déterministe | 0,25°, 6 h, 10 jours selon variante | baseline déterministe et référence architecturale | **LEARN** |
| WeatherNext Gen / GenCast | diffusion probabiliste | 0,25° ou 1°, 12 h, 15 jours selon variante | comparaison probabiliste et étude diffusion | **LEARN** |

La documentation officielle signale que Graph et Gen sont désormais des modèles
legacy pour les nouveaux projets et que les workflows actifs doivent migrer vers
WN2. Cela n'interdit pas de les garder comme baselines historiques.

## 10. Notebook et chemin d'exécution réel

Le notebook `docs/weathernext2/wn2_demo.ipynb` est une preuve utile du chemin
opérationnel, mais pas un contrat de production :

1. il installe le dépôt et reconfigure JAX/TPU dans Colab ;
2. il charge un dataset HRES initialisé depuis le bucket `dm_graphcast` ;
3. il charge la configuration Fiddle et le checkpoint ;
4. il construit le prédicteur ;
5. il exécute un rollout autorégressif ;
6. il pmape les membres sur les devices ;
7. il visualise les variables et peut exécuter le tracker cyclone ;
8. il expose aussi une loss et un gradient step.

Le notebook utilise par défaut `WeatherNextCyclones_Mini`, résolution 1°, 20
étapes, précisément pour rester démontrable. Il indique qu'un backend GPU doit
remplacer l'attention `splash_mha` par une implémentation GPU alternative,
plus lente et plus consommatrice de mémoire. Il indique également que le
calcul de gradient du modèle Mini peut dépasser la mémoire d'un P100.

Cette distinction est importante pour le POC Atmos : le notebook prouve la
chaîne logicielle, pas la capacité d'un VPS GSIE à exécuter WN2 complet.

## 11. Entraînement et fine-tuning

Le dépôt fournit des interfaces de loss et permet un gradient step dans le
notebook. Il ne fournit pas une plateforme de production prête à entraîner un
modèle Quintessences.

Données citées :

- ERA5 via ECMWF/WeatherBench2 pour le pré-entraînement ;
- HRES opérationnel pour l'initialisation et le fine-tuning opérationnel ;
- données spécifiques cyclones pour WeatherNext Cyclones.

Un fine-tuning Quintessences nécessiterait au minimum :

- un corpus français juridiquement utilisable ;
- une séparation temporelle et spatiale ;
- des observations de stations/radar correctement alignées ;
- un benchmark WeatherBench2 localisé ;
- une validation des extrêmes ;
- une procédure de registre de modèle RFC-0015.

Il ne faut pas fine-tuner WN2 sur une petite zone française avant d'avoir
mesuré le gain par rapport à une correction de biais ou à un downscaler plus
simple.

## 12. Matériel et coûts

### Faits officiels

- TPU recommandé par le dépôt pour les modèles complets ;
- WN2 complet demande typiquement un H100 sur GPU selon le guide ;
- Cyclones Mini est destiné aux machines plus contraintes ;
- poids et données sont téléchargés séparément depuis un bucket Google ;
- l'inférence complète implique JAX, Haiku, xarray-jax, Dask et les outils
  de graphes.

### Estimation d'architecture

| Mode | Matériel | Décision |
|---|---|---|
| Flux Google | aucun GPU Quintessences | **priorité POC** |
| Mini local | GPU/TPU contraint | benchmark uniquement |
| WN2 complet | H100 80 Go ou TPU adapté | cloud burst / benchmark ponctuel |
| Fine-tuning | plusieurs GPU/TPU + stockage massif | pas avant preuve de valeur |
| Production self-hosted | worker GPU dédié + cache objet | seulement après benchmark coût/latence |

Les coûts cloud et les volumes exacts doivent être mesurés dans le POC, pas
inventés à partir du nombre de paramètres.

## 13. Licences et responsabilité

Le README v0.3.0 distingue :

- code et notebooks sous Apache-2.0 ;
- autres matériaux, dont les poids selon les termes décrits, sous CC BY 4.0 ;
- flux temps réel sous des conditions expérimentales spécifiques ;
- datasets ECMWF/Copernicus sous leurs propres conditions.

Le registre Quintessences doit donc avoir un enregistrement séparé pour :

```text
code_license
weights_license
training_data_license
forecast_feed_terms
output_terms
attribution_required
commercial_use_verified
redistribution_allowed
```

Le modèle ne remplace pas les alertes, vigilances ou notices des agences
météorologiques officielles. Pour IGNIS, il reste une source d'aide à la
décision et de scénarios, jamais une autorité opérationnelle.

## 14. Limites scientifiques

1. 0,25° ne fournit pas un champ de vent forestier à l'échelle de la cellule
   d'incendie.
2. Les extrêmes, rafales, convection et relief complexe exigent des validations
   spécifiques.
3. Un ensemble ML peut être bien calibré globalement et mal calibré sur la
   Nouvelle-Aquitaine ou les Cévennes.
4. Le downscaling ne crée pas l'information absente ; il ajoute une hypothèse
   conditionnelle et doit porter son propre niveau de preuve.
5. Une sortie moyenne peut masquer un membre rare mais opérationnellement
   important.
6. Les conditions initiales, versions de données et transformations doivent
   être conservées pour rendre un résultat rejouable.

## 15. Décision R&D recommandée

### À faire maintenant

- consommer les flux WN2 historiques et temps réel autorisés ;
- construire le contrat `AtmosForecast` et son registre de provenance ;
- comparer WN2, ECMWF HRES/ENS et Météo-France sur un territoire pilote ;
- stocker un sous-ensemble Zarr dans le Data Registry ;
- produire des statistiques par variable, horizon et région.

### À ne pas faire maintenant

- embarquer WN2 dans GeoSylva ;
- auto-héberger les poids sur le VPS GSIE sans GPU qualifié ;
- appeler WN2 directement depuis IGNIS ou Hydro ;
- présenter la maille globale comme une prévision locale ;
- fine-tuner avant d'avoir un benchmark français et des droits qualifiés.

## 16. Sources primaires

- Dépôt : https://github.com/google-deepmind/weathernext/tree/v0.3.0
- Commit : https://github.com/google-deepmind/weathernext/commit/89c4b2a77a1c57b328b909c575550fd2e5aadc9c
- README v0.3.0 : https://raw.githubusercontent.com/google-deepmind/weathernext/v0.3.0/README.md
- Code WN2 : https://github.com/google-deepmind/weathernext/tree/v0.3.0/weathernext/weathernext2
- FGN : https://arxiv.org/abs/2506.10772
- Guide modèles : https://developers.google.com/weathernext/guides/models
- Accès aux flux : https://developers.google.com/weathernext/guides/access-forecast
- WeatherNext Cyclones : https://www.nature.com/articles/s41586-026-10953-2
- WeatherBench2 : https://weatherbench2.readthedocs.io/en/latest/data-guide.html
- ERA5 : https://www.ecmwf.int/en/forecasts/datasets/reanalysis-datasets/era5

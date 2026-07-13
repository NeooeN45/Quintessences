# Correlation Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Correlation Engine |
| **Catégorie** | Chaîne d'intelligence (détection de relations) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-002, GSIE-CON-005 |
| **Ordre de développement** | 5 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Détecter et quantifier les corrélations statistiques significatives
entre données issues de sources hétérogènes (géospatiales, climatiques,
pédologiques, botaniques, terrain) pour alimenter le raisonnement.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| `KNOWLEDGE_ENGINE` | Connaissances normalisées | Règles, seuils et relations connues servant de référence |
| `GIS_ENGINE` | Données géospatiales | MNT, pente, exposition, hydrographie, limites parcellaires |
| `CLIMATE_ENGINE` | Données climatiques | Températures, précipitations, déficit hydrique, bioclimat |
| `PEDOLOGY_ENGINE` | Données pédologiques | Texture, pH, profondeur, drainage, réserve utile |
| `BOTANICAL_ENGINE` | Données botaniques | Présence/absence d'essences, autécologie |
| `FOREST_DYNAMICS_ENGINE` | Données de peuplement | Croissance, régénération, perturbations |
| Observations terrain | Données utilisateur | Relevés, inventaires, diagnostics terrain |
| `GSIE/DATASETS/` | Jeux de données | Séries temporelles et spatiales référencées |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `REASONING_ENGINE` | Matrice de corrélations | Relations statistiques justifiées et sourcées |
| `DIAGNOSTIC_ENGINE` | Matrice de corrélations | Relations utiles au diagnostic stationnel |
| `FOREST_DYNAMICS_ENGINE` | Corrélations | Relations alimentant les modèles de dynamique |
| `LEARNING_ENGINE` | Patterns émergents | Corrélations nouvelles détectées, à valider |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Moteur | `KNOWLEDGE_ENGINE` | Référentiel de règles et relations connues |
| Moteur | `GIS_ENGINE` | Données géospatiales |
| Moteur | `CLIMATE_ENGINE` | Données climatiques |
| Moteur | `PEDOLOGY_ENGINE` | Données pédologiques |
| Moteur | `BOTANICAL_ENGINE` | Données botaniques |
| Moteur | `FOREST_DYNAMICS_ENGINE` | Données de peuplement |
| Base | `GSIE/DATASETS/` | Jeux de données référencés |

## 5. Contrat d'interface

### Entrée — `CorrelationRequest`

```
CorrelationRequest = {
  requete_id    : UUID
  domaine       : enum { stationnel, climatique, sylvicole, sanitaire, global }
  parametres    : liste de ParametreCorrelation
  zone_etude    : EmpriseGeographique (optionnel)
  periode       : PeriodeTemporelle (optionnel)
  seuil_significativite : décimal (optionnel, défaut 0,05)
}

ParametreCorrelation = {
  source_moteur : enum { GIS, CLIMATE, PEDOLOGY, BOTANICAL, FOREST_DYNAMICS, TERRAIN }
  variable      : texte (ex. « pH », « precipitations_estivales », « altitude » )
  unite         : texte
}

EmpriseGeographique = {
  type     : enum { point, polygone, parcelle }
  geometrie : structure GeoJSON (optionnel)
  parcelle_id : texte (optionnel)
}
```

### Sortie — `CorrelationMatrix`

```
CorrelationMatrix = {
  matrice_id    : UUID
  requete_origine : UUID
  correlations  : liste de Correlation
  date_calcul   : ISO 8601
  sources_utilisees : liste de SourceReference
}

Correlation = {
  variable_a    : ParametreCorrelation
  variable_b    : ParametreCorrelation
  coefficient   : décimal (-1,0 à 1,0)
  p_valeur      : décimal
  type_relation : enum { positive, negative, non_significative }
  n_observations: entier
  domaine_validite : texte (ex. « France méditerranéenne, sols acides »)
  source        : SourceReference
  evidence_level: enum { A, B, C, D, E, F }
  confidence    : décimal (0,0 à 1,0)
}
```

## 6. Garanties

- Toute corrélation produite est **sourcée** et **statistiquement
  justifiée** (coefficient, p-valeur, taille d'échantillon) (`GSIE-CON-002`).
- Aucune corrélation n'est présentée comme relation de causalité sans
  justification scientifique explicite.
- Le domaine de validité de chaque corrélation est explicité (zone,
  période, conditions).
- Le moteur ne produit **pas de recommandation** — il alimente le
  raisonnement (séparation des responsabilités).
- Les corrélations non significatives sont conservées dans la matrice
  pour éviter les inférences abusives.
- Fonctionnement hors-ligne sur données en cache local (article T-8).

## 7. Cas d'usage

### Cas 1 — Corrélation entre déficit hydrique estival et dépérissement du hêtre

Le Correlation Engine croise les données climatiques du Climate Engine
(déficit hydrique estival 2003–2023) avec les observations de
dépérissement du hêtre issues du terrain. Il détecte une corrélation
négative significative (r = -0,72, p < 0,01) entre les précipitations
estivales et la vitalité du hêtre en dessous de 800 m. Cette corrélation
est transmise au Reasoning Engine et au Diagnostic Engine avec son
domaine de validité (« France atlantique, altitude < 800 m, période
2003–2023 »).

### Cas 2 — Corrélation entre pH sol et présence du chêne sessile

Croisement des données pédologiques (pH mesuré sur 150 stations) et des
relevés botaniques (présence/absence du chêne sessile). Corrélation
positive significative (r = 0,58, p < 0,05) entre pH 4,5–6,0 et la
présence de l'essence. La corrélation est sourcée (observations terrain
+ référentiel Rameau et al., 2018) et transmise au Reasoning Engine.

## 8. État de l'art et pistes de recherche sourcées

Cette section recense, à titre de piste de recherche pour la Phase 4
(implémentation), des méthodes et bibliothèques reconnues de l'état de
l'art en statistique spatiale, en inférence causale et en gestion de la
significativité statistique — directement pertinentes pour la
responsabilité du Correlation Engine : détecter et quantifier des
corrélations statistiquement significatives entre données hétérogènes
(géospatiales, climatiques, pédologiques, botaniques, terrain). Aucune
prescription de code ni de détail d'implémentation n'est faite ici ;
il s'agit d'orienter les choix d'architecture technique à venir.

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| **PySAL** (écosystème Python de statistique spatiale, notamment le sous-module `esda` pour l'autocorrélation spatiale — I de Moran globale et locale/LISA) | Détecter si une variable géospatiale (ex. dépérissement, présence d'essence) présente un regroupement ou une dispersion spatiale significative avant/au-delà de toute corrélation avec une autre variable de source différente | Le moteur croise des données à référence spatiale (`GIS_ENGINE`, observations terrain géolocalisées) ; ignorer l'autocorrélation spatiale expose à des corrélations spécieuses (pseudo-réplication spatiale). PySAL est la bibliothèque de référence de la communauté de géo-analyse computationnelle pour ce diagnostic (Rey & Anselin, 2010 ; module `esda`, pysal.org) |
| **R `spdep`** (schémas de pondération spatiale, tests d'autocorrélation — Moran, Geary) et **`GWmodel`** (régression géographiquement pondérée, GWR) | Vérifier la stationnarité spatiale d'une relation avant de la généraliser (une corrélation pH–essence peut différer entre deux régions pédoclimatiques) ; produire des coefficients locaux plutôt qu'un coefficient global unique | Répond directement à la garantie du moteur « le domaine de validité de chaque corrélation est explicité (zone, période, conditions) » : la GWR quantifie explicitement l'hétérogénéité spatiale d'une relation plutôt que de l'écraser en un coefficient global (Gollini et al., 2015) |
| **Bibliothèques de découverte causale par graphes orientés acycliques — DAG** (écosystème `py-why` : `causal-learn`, `DoWhy`) | Distinguer, parmi les corrélations détectées, celles compatibles avec une structure causale plausible de celles relevant d'un facteur de confusion commun | Répond directement à la garantie « aucune corrélation n'est présentée comme relation de causalité sans justification scientifique explicite » : ces outils formalisent la distinction corrélation/causalité plutôt que de la laisser implicite (Zheng et al., 2024 ; DoWhy, projet py-why) |
| **Analyse de causalité de Granger (multivariée)** | Établir, pour des séries temporelles (ex. précipitations estivales vs. vitalité du hêtre sur plusieurs années), si une variable précède statistiquement les variations d'une autre, en complément du coefficient de corrélation | Le Cas d'usage 1 documenté au §7 (déficit hydrique 2003–2023 / dépérissement du hêtre) est une série temporelle ; la causalité de Granger est une approche établie pour qualifier la direction temporelle d'une relation en écologie, sans prétendre à une preuve causale mécaniste (Damos, 2016, BMC Ecology) |
| **Apprentissage automatique par ensembles d'arbres (forêts aléatoires) et mesures d'importance de variables** | Détecter des relations non linéaires ou des interactions entre variables de sources hétérogènes (GIS, climat, pédologie, botanique) que le seul coefficient de corrélation linéaire ne capture pas, en amont d'une quantification statistique classique | Les sources d'entrée du moteur sont explicitement hétérogènes ; les forêts aléatoires et mesures d'importance associées sont une approche courante pour ce type de fusion multi-sources en écologie, avant de re-exprimer les relations détectées sous forme de corrélations sourcées et testées (Allen Akselrud, 2024, Fisheries Research) |
| **Correction pour comparaisons multiples — Bonferroni / taux de fausses découvertes (FDR, procédure de Benjamini-Hochberg)** | Ajuster le seuil de significativité (`seuil_significativite`, `p_valeur`) lorsque de nombreuses paires de variables sont testées simultanément entre plusieurs moteurs domaine | Le contrat d'interface autorise des requêtes multi-paramètres ; tester de nombreuses paires sans correction gonfle le taux de faux positifs. La FDR (moins conservatrice que Bonferroni) est la pratique de référence en écologie pour ce cas (Pike et al., 2011, Methods in Ecology and Evolution) |

Ces pistes ne remettent pas en cause le contrat d'interface déjà
spécifié (§5) : elles relèvent de choix d'implémentation interne au
Correlation Engine, à trancher en Phase 4 en fonction des contraintes
de performance, de la disponibilité hors-ligne (article T-8) et des
compétences de l'équipe. La distinction corrélation/causalité, déjà
posée comme garantie du moteur (§6), trouve dans la littérature de
découverte causale (DAG, Granger) un cadre méthodologique établi
plutôt qu'une simple précaution rédactionnelle.

À noter : le `DIAGNOSTIC_ENGINE` propose également les forêts
aléatoires, mais pour un rôle distinct (classification supervisée de
l'état sanitaire, plutôt que fusion exploratoire multi-sources) ; les
deux usages sont complémentaires et ne doivent pas conduire à deux
implémentations redondantes en Phase 4.

### Sources

- Rey, S. J., & Anselin, L. (2010). *PySAL: A Python Library of Spatial Analytical Methods.* Geographical Analysis. Projet : [pysal.org](https://pysal.org)
- Bivand, R. et al. *spdep: Spatial Dependence: Weighting Schemes, Statistics.* Package R, CRAN. https://cran.r-project.org/package=spdep
- Gollini, I., Lu, B., Charlton, M., Brunsdon, C., & Harris, P. (2015). *GWmodel: An R Package for Exploring Spatial Heterogeneity Using Geographically Weighted Models.* Journal of Statistical Software, 63(17), 1–50. DOI : 10.18637/jss.v063.i17
- Zheng, Y., Huang, B., Chen, W. et al. (2024). *Causal-learn: Causal Discovery in Python.* Journal of Machine Learning Research, 25(60), 1–8. arXiv:2307.16405
- Projet DoWhy (py-why). *DoWhy: A Python library for causal inference.* https://www.pywhy.org/dowhy/ — https://github.com/py-why/dowhy
- Damos, P. (2016). *Using multivariate cross correlations, Granger causality and graphical models to quantify spatiotemporal synchronization and causality between pest populations.* BMC Ecology, 16, 33. DOI : 10.1186/s12898-016-0087-7
- Correia, H. E., Dee, L. E., Byrnes, J. E. K. et al. (2026). *Best practices for moving from correlation to causation in ecological research.* Nature Communications. https://www.nature.com/articles/s41467-026-69878-z
- Allen Akselrud, C. I. (2024). *Random forest regression models in ecology: Accounting for messy biological data and producing predictions with uncertainty.* Fisheries Research. https://www.sciencedirect.com/science/article/abs/pii/S016578362400225X
- Pike, N., Verhoeven, K., McIntyre, L. et al. (2011). *Using false discovery rates for multiple comparisons in ecology and evolution.* Methods in Ecology and Evolution. DOI : 10.1111/j.2041-210X.2010.00061.x

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*

# Climate Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Climate Engine |
| **Catégorie** | Moteur domaine (climat) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-002, GSIE-CON-005 |
| **Ordre de développement** | 7 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Gérer les données climatiques historiques et actuelles, calculer les
variables bioclimatiques stationnelles et fournir les projections
climatiques avec leur scénario et leur incertitude.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| Climate Repository | Base de données | Données climatiques historiques stockées |
| Météo-France | Source externe | Données historiques, safran, projections DRIAS |
| DRIAS / IPSL | Source externe | Projections climatiques régionalisées (RCP/SSP) |
| Bundle de mission | Cache local | Données climatiques préchargées (RFC-0003) |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `DIAGNOSTIC_ENGINE` | Variables bioclimatiques | Températures, précipitations, déficit hydrique, durée de végétation |
| `CORRELATION_ENGINE` | Données climatiques | Séries pour croisement statistique |
| `SIMULATION_ENGINE` | Projections climatiques | Scénarios long terme pour les projections de peuplement |
| `REASONING_ENGINE` | Variables bioclimatiques | Données pour l'inférence d'adaptation |
| `FOREST_DYNAMICS_ENGINE` | Variables climatiques | Données pour les modèles de croissance |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Base externe | Climate Repository | Stockage des données climatiques |
| Source externe | Météo-France | Données historiques et safran |
| Source externe | DRIAS / IPSL | Projections climatiques régionalisées |
| Aucun moteur | — | Le Climate Engine ne dépend d'aucun autre moteur (source domaine) |

## 5. Contrat d'interface

### Entrée — `ClimateQuery`

```
ClimateQuery = {
  requete_id : UUID
  emprise    : EmpriseGeographique
  periode    : PeriodeTemporelle
  variables  : liste de enum {
    temperature_moyenne, temperature_min, temperature_max,
    precipitations_totales, precipitations_estivales,
    deficit_hydrique, duree_vegetation, gel_jours,
    vent_moyen, vent_max, humidite
  }
  type_donnees : enum { historique, actuelle, projection }
  scenario    : enum { RCP26, RCP45, RCP85, SSP126, SSP245, SSP585 } (si projection)
}

PeriodeTemporelle = {
  debut : ISO 8601 (année)
  fin   : ISO 8601 (année)
}
```

### Sortie — `ClimateData`

```
ClimateData = {
  requete_id  : UUID
  variables   : liste de ClimateVariable
  source      : SourceReference
  date_donnees: ISO 8601
  mode        : enum { en_ligne, hors_ligne, degrade }
}

ClimateVariable = {
  nom         : texte (ex. « deficit_hydrique_estival »)
  valeur      : décimal
  unite       : texte (ex. « mm », « °C », « jours »)
  periode     : PeriodeTemporelle
  scenario    : enum { RCP26, RCP45, RCP85, SSP126, SSP245, SSP585, historique } (optionnel)
  incertitude : IntervalleConfiance (optionnel — obligatoire pour projections)
  source      : SourceReference
}

IntervalleConfiance = {
  minimum : décimal
  maximum : décimal
  niveau  : enum { 80pct, 90pct, 95pct }
}
```

## 6. Garanties

- **Les données climatiques sont datées et qualifiées** — chaque
  variable porte sa source et sa période (principe fondateur).
- **Les projections sont affichées avec leur scénario (RCP/SSP) et leur
  incertitude** — jamais présentées comme certitudes (principe
  fondateur).
- Mode hors-ligne : cache local des données historiques (article T-8).
- Mode dégradé documenté pour les projections temps réel.
- Le moteur ne produit **pas de diagnostic** — il fournit des données
  climatiques (séparation des responsabilités).
- Aucune donnée climatique n'est extrapolée sans justification
  scientifique (`GSIE-CON-002`).

## 7. Cas d'usage

### Cas 1 — Calcul du déficit hydrique estival pour diagnostic de dépérissement

Le Diagnostic Engine demande le déficit hydrique estival pour la
parcelle 27 sur la période 2003–2023. Le Climate Engine retourne :
déficit moyen 180 mm (source : Météo-France Safran, evidence B), avec
une tendance à la hausse sur les 10 dernières années. Ces données
alimentent le diagnostic de dépérissement de la hêtraie.

### Cas 2 — Projection climatique 2050 pour choix d'essence

Le Simulation Engine demande les projections 2041–2070 pour la
parcelle 27 sous scénario RCP 8.5. Le Climate Engine retourne :
température moyenne +2,3 °C (intervalle [+1,8 ; +2,9] à 90 %),
précipitations estivales -15 % (intervalle [-25 % ; -5 %]). Source :
DRIAS 2024. Ces projections permettent d'évaluer l'adaptation future
du hêtre et du chêne sessile à cette station.

## 8. État de l'art et pistes de recherche sourcées

Cette section recense, pour la Phase 4, des pistes techniques et scientifiques
identifiées par recherche documentaire ciblée sur les quatre axes propres à la
responsabilité du Climate Engine : données de réanalyse (historique/actuelle),
projections régionalisées avec scénario et incertitude, microclimat forestier
stationnel, et calcul des variables bioclimatiques (dont l'évapotranspiration).
Elle reste au niveau piste de recherche — aucune implémentation n'est
prescrite ici.

### 8.1 Données historiques et actuelles

Le contrat d'interface distingue trois types de données (`historique`,
`actuelle`, `projection`, cf. §5). Deux familles de sources concrètes
couvrent ce besoin :

- La réanalyse **ERA5-Land** (Copernicus Climate Change Service / ECMWF)
  fournit un historique climatique global continu depuis 1950, à résolution
  spatiale de 9 km et temporelle horaire, avec mise à jour continue
  (Muñoz-Sabater et al., 2021). Elle peut servir de source de repli hors du
  territoire français ou en cas d'indisponibilité d'une source nationale,
  cohérente avec le mode dégradé déjà documenté (§6).
- La chaîne opérationnelle **Météo-France** couvre le territoire national :
  la réanalyse **SAFRAN** (grille ~8 km, réanalyse quotidienne/mensuelle) est
  la référence pour les données `historique`, tandis que les modèles
  **ARPEGE** (global) et **AROME** (haute résolution) fournissent les
  données `actuelle`/court terme. Ces jeux sont accessibles via
  `meteo.data.gouv.fr` sous licence ouverte.

### 8.2 Projections climatiques régionalisées (DRIAS, SSP/RCP)

Le portail **DRIAS — Les futurs du climat** (Météo-France, avec le soutien
scientifique du CNRM, du Cerfacs et de l'IPSL) est la source de référence
pour les projections régionalisées françaises exigées par le contrat de
sortie. Le jeu **DRIAS-2020** repose sur l'ensemble Euro-CORDEX (une
trentaine de simulations régionalisées, scénarios RCP2.6/4.5/8.5) ; depuis
fin 2023, DRIAS propose également la **TRACC** (Trajectoire de
Réchauffement de Référence pour l'Adaptation au Changement Climatique).
Ces jeux fournissent nativement des ensembles multi-modèles permettant de
dériver l'`IntervalleConfiance` attendu en sortie, sans qu'aucune
extrapolation ne soit nécessaire au-delà de ce que l'ensemble fournit —
condition posée par la garantie de non-extrapolation (§6, `GSIE-CON-002`).

### 8.3 Microclimat forestier (sous couvert vs plein découvert)

Le moteur doit calculer des variables bioclimatiques **stationnelles**,
c'est-à-dire à l'échelle de la parcelle, et non la seule macroclimatologie
régionale. Une analyse globale de 714 paires de mesures (Zellweger et al.,
2020, *Science*) montre que les températures moyennes et maximales sous
couvert sont respectivement inférieures de 1,7 °C et 4,1 °C à celles du
plein découvert, tandis que les minimales y sont supérieures de 1,1 °C.
Des modèles mécanistiques dédiés, tels que **microclimc** et sa version
spatialisée **microclimf** (Maclean et al., 2021), permettent de dériver des
estimations de microclimat au-dessus, dans et sous couvert à partir de
variables macroclimatiques standards et de la structure du peuplement.
Une piste pour la Phase 4 consiste à évaluer si un module de correction
stationnelle de ce type doit s'intercaler entre les données macroclimatiques
brutes (SAFRAN/ERA5-Land/DRIAS) et les `ClimateVariable` retournées. Cette
correction stationnelle recoupe directement les données de pente/exposition
déjà calculées par le `GIS_ENGINE` (§8.1 de ce dernier) — les deux moteurs
gagneraient à partager la même donnée d'entrée topographique plutôt qu'à la
recalculer séparément.

### 8.4 Évapotranspiration et variables bioclimatiques dérivées

Le calcul du **déficit hydrique** suppose une estimation de
l'évapotranspiration. La méthode **FAO-56 Penman-Monteith** (Allen, Pereira,
Raes & Smith, 1998) est le standard international pour l'évapotranspiration
de référence (ET0), calculée à partir du rayonnement net, de la
température, de l'humidité et du vent. Pour la nomenclature et la
définition des variables bioclimatiques dérivées, les référentiels
**WorldClim** et **CHELSA** (Karger et al., 2017 ; CHELSA v2.1 à ~1 km de
résolution) constituent des standards méthodologiques établis, transposables
en tant que méthode de définition plutôt qu'utilisables tels quels comme
source directe à l'échelle stationnelle visée par ce moteur.

### Tableau de synthèse

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| ERA5-Land (Copernicus C3S / ECMWF) | Source de repli pour données historiques/actuelles hors couverture SAFRAN, ou en mode dégradé | Réanalyse globale continue depuis 1950, résolution 9 km / horaire (Muñoz-Sabater et al., 2021) |
| SAFRAN / ARPEGE / AROME (Météo-France) | Source de référence France pour `type_donnees = historique` (SAFRAN) et `actuelle` (ARPEGE/AROME) | Réanalyse nationale ~8 km qualifiée et modèles opérationnels ouverts (`meteo.data.gouv.fr`) |
| Portail DRIAS (DRIAS-2020, TRACC — Météo-France/CNRM/Cerfacs/IPSL) | Source de projections régionalisées pour `type_donnees = projection` | Ensemble Euro-CORDEX multi-modèles fournissant nativement une dispersion exploitable comme intervalle de confiance |
| Modèles mécanistiques de microclimat forestier (microclimc/microclimf, Maclean et al., 2021) | Piste pour dériver des variables réellement « stationnelles » sous couvert à partir du macroclimat | Le couvert forestier modifie significativement température et humidité au sol (Zellweger et al., 2020, *Science*) |
| FAO-56 Penman-Monteith (Allen et al., 1998) | Méthode de référence pour le calcul de l'évapotranspiration entrant dans le `deficit_hydrique` | Standard international FAO pour l'ET0 |
| Référentiels de variables bioclimatiques type WorldClim/CHELSA (Karger et al., 2017) | Cadre méthodologique pour la nomenclature des variables bioclimatiques dérivées | Jeux de référence internationalement reconnus, transposables en méthode plutôt qu'en source directe à l'échelle stationnelle |

### Sources

- Muñoz-Sabater, J. et al. (2021). *ERA5-Land: a state-of-the-art global reanalysis dataset for land applications*. Earth System Science Data, 13, 4349–4383. https://essd.copernicus.org/articles/13/4349/2021/
- Copernicus Climate Change Service (C3S) / ECMWF. *Climate reanalysis*. https://climate.copernicus.eu/climate-reanalysis
- INRAE AgroClim. *SAFRAN — Centre d'aide de l'application SICLIMA*. https://agroclim.inrae.fr/siclima/help/references/bases/safran.html
- Météo-France. *Données publiques — modèle ARPEGE*. https://donneespubliques.meteofrance.fr/?fond=produit&id_produit=130&id_rubrique=51
- Météo-France. *Données publiques — modèle AROME*. https://donneespubliques.meteofrance.fr/?fond=produit&id_produit=131&id_rubrique=51
- DRIAS — Les futurs du climat (Météo-France, CNRM, Cerfacs, IPSL). https://www.drias-climat.fr
- Centre de ressources pour l'adaptation au changement climatique. *Les nouvelles projections climatiques de référence DRIAS-2020*. https://www.adaptation-changement-climatique.gouv.fr/actualites/veille/les-nouvelles-projections-climatiques-reference-drias-2020
- Zellweger, F., De Frenne, P., Lenoir, J. et al. (2020). *Forest microclimate dynamics drive plant responses to warming*. Science, 368(6492), 772–775. https://www.science.org/doi/10.1126/science.aba6880
- Maclean, I.M.D. et al. (2021). *Microclimc: A mechanistic model of above, below and within-canopy microclimate*. Ecological Modelling, 451, 109567. https://www.sciencedirect.com/science/article/abs/pii/S0304380021001265 (dépôt du code : https://github.com/ilyamaclean/microclimc)
- Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). *Crop Evapotranspiration — Guidelines for Computing Crop Water Requirements*. FAO Irrigation and Drainage Paper n°56, FAO, Rome. https://openknowledge.fao.org/handle/20.500.14283/cd6621en (une édition révisée a été publiée par la FAO en 2025, sans remettre en cause la méthode Penman-Monteith utilisée ici)
- Karger, D.N. et al. (2017). *Climatologies at high resolution for the earth's land surface areas*. Scientific Data, 4, 170122. https://www.nature.com/articles/sdata2017122 (voir aussi https://chelsa-climate.org)

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*

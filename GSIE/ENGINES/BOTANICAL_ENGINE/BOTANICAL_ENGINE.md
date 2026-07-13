# Botanical Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Botanical Engine |
| **Catégorie** | Moteur domaine (botanique) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-005, GSIE-CON-010 |
| **Ordre de développement** | 9 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Gérer la taxonomie, la nomenclature et l'autécologie des espèces
forestières, en assurant le versionnement des évolutions taxonomiques et
la fourniture des données d'identification et d'exigences écologiques.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| Species Repository | Base de données | Données d'espèces stockées (taxonomie, autécologie) |
| Ontology | Base de données | Ontologie taxonomique et relations nomenclaturales |
| Tela Botanica | Source externe | Référentiel nomenclatural français |
| GBIF | Source externe | Global Biodiversity Information Facility |
| BDNFF | Source externe | Base de Données Nomenclaturale de la Flore de France |
| Observations terrain | Données utilisateur | Relevés floristiques, identifications |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `DIAGNOSTIC_ENGINE` | Données botaniques | Autécologie des essences présentes et candidates |
| `CORRELATION_ENGINE` | Données botaniques | Présence/absence d'essences pour croisement |
| `RECOMMENDATION_ENGINE` | Données botaniques | Exigences et optimums d'essences candidates |
| `REASONING_ENGINE` | Données botaniques | Autécologie pour l'inférence d'adaptation |
| Utilisateur (via interface) | Identification | Aide à la détermination, clés d'identification |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Base externe | Species Repository | Stockage des données d'espèces |
| Base externe | Ontology (via `KNOWLEDGE_ENGINE`) | Structure taxonomique |
| Source externe | Tela Botanica, GBIF, BDNFF | Référentiels nomenclaturaux officiels |
| Aucun moteur | — | Le Botanical Engine ne dépend d'aucun autre moteur (source domaine) |

## 5. Contrat d'interface

### Entrée — `BotanicalQuery`

```
BotanicalQuery = {
  requete_id : UUID
  type       : enum { par_essence, par_taxon, par_station, identification }
  essence    : texte (nom scientifique ou vernaculaire, optionnel)
  station_id : UUID (optionnel)
  parametres : liste de enum {
    taxonomie, nomenclature, autecologie, synonymes, exigences, optimum, amplitude
  }
}
```

### Sortie — `BotanicalData`

```
BotanicalData = {
  requete_id : UUID
  especes    : liste de EspeceData
  source     : SourceReference
  date_donnees : ISO 8601
}

EspeceData = {
  taxon_id        : UUID
  nom_scientifique : texte
  nom_vernaculaire : texte
  synonymes       : liste de texte
  famille         : texte
  autecologie     : Autecologie (optionnel)
  taxonomie_version : texte (version du référentiel)
  source          : SourceReference
}

Autecologie = {
  optimum_ph       : IntervalleValeur (optionnel)
  optimum_altitude : IntervalleValeur (optionnel)
  optimum_precipitations : IntervalleValeur (optionnel)
  tolerance_gel    : décimal (°C, optionnel)
  tolerance_ombre  : enum { tres_forte, forte, moderee, faible, tres_faible }
  exigence_eau     : enum { hygrophyte, mesophyte, xerophyte }
  exigence_sol     : texte (optionnel)
  source           : SourceReference
  evidence_level   : enum { A, B, C, D, E, F }
}

IntervalleValeur = {
  minimum : décimal
  maximum : décimal
  unite   : texte
}
```

## 6. Garanties

- **Toute donnée botanique est sourcée et versionnée** — chaque taxon
  porte son référentiel d'origine (Tela Botanica, GBIF, BDNFF) et la
  version du référentiel (principe fondateur).
- **Les évolutions taxonomiques sont tracées** — un taxon peut changer
  de nom, mais l'historique est conservé (`GSIE-CON-010`).
- Les synonymes sont gérés — une recherche par ancien nom renvoie le
  taxon courant.
- Le moteur ne produit **pas de diagnostic** — il fournit des données
  taxonomiques et autécologiques (séparation des responsabilités).
- Fonctionnement hors-ligne sur données en cache local (article T-8).
- Les données autécologiques portent leur niveau de preuve
  (`GSIE-CON-005`).

## 7. Cas d'usage

### Cas 1 — Fourniture de l'autécologie du chêne sessile pour recommandation

Le Recommendation Engine demande l'autécologie du chêne sessile
(*Quercus petraea*). Le Botanical Engine retourne : optimum pH 4,5–6,0
(evidence B, source : Rameau et al., 2018), optimum altitude 0–1400 m
(evidence B), tolérance gel -22 °C (evidence C), exigence eau :
mésophyte (evidence B). Le synonyme *Quercus sessiliflora* est
référencé. Ces données alimentent la recommandation de reboisement.

### Cas 2 — Évolution taxonomique d'une espèce

En 2028, le GBIF révise la classification d'une espèce : *Sorbus aria*
devient *Aria edulis*. Le Botanical Engine archive l'ancienne
classification (version 1, *Sorbus aria*, source GBIF 2024) et crée la
nouvelle (version 2, *Aria edulis*, source GBIF 2028). Les recherches
par *Sorbus aria* continuent de fonctionner via le système de
synonymes. Les recommandations passées restent explicables avec le
nom utilisé à l'époque (`GSIE-CON-010`).

## 8. État de l'art et pistes de recherche sourcées

Cette section recense, à titre de veille scientifique et technique, des
référentiels, bibliothèques et méthodes actuels pertinents pour une
implémentation future (Phase 4) du Botanical Engine. Elle reste au
niveau de la piste de recherche : aucun choix d'implémentation n'est
arrêté à ce stade, et aucune de ces briques ne remplace la
responsabilité du moteur (gestion de la taxonomie, de la nomenclature
et de l'autécologie, avec versionnement des évolutions taxonomiques).

### 8.1 Référentiels taxonomiques et nomenclaturaux

**TAXREF (MNHN/INPN)** est le référentiel taxonomique national officiel
pour la faune, la flore et la fonge de France (cadre du Système
d'Information sur la Nature et les Paysages, SINP). La version en
vigueur, TAXREF v18.0, a été publiée le 9 janvier 2025 par le Muséum
national d'Histoire naturelle. Il liste les noms scientifiques valides
ainsi que leurs synonymes, et un accès en web service est disponible
depuis la version 2 du référentiel (`taxref.mnhn.fr`, `inpn.mnhn.fr`).
Ce référentiel correspond directement à l'entrée déjà prévue dans le
moteur et au besoin de « fourniture des données d'identification » et
de gestion des synonymes documenté en §6.

**GBIF Taxonomic Backbone / API `species/match`** assure la mise en
correspondance internationale des noms scientifiques au-delà du
périmètre strict de la flore française. Le backbone du GBIF est
alimenté par le Catalogue of Life. GBIF figure déjà comme source
d'entrée du moteur ; son API de correspondance de noms est une piste
concrète pour fiabiliser la résolution de synonymes à l'échelle
internationale.

**Catalogue of Life (CoL)** constitue un modèle structurel de
référence pour la gestion de la synonymie qui sert de brique amont à
la fois à TAXREF et au GBIF Backbone. Il illustre exactement le type
d'événement décrit dans le cas d'usage 2 du présent document (*Sorbus
aria* devenant *Aria edulis*), et peut servir de référence conceptuelle
pour concevoir le mécanisme interne de versionnement taxonomique du
moteur.

### 8.2 Modèles de distribution d'espèces pour l'autécologie

**MaxEnt** (Phillips, Anderson et Schapire, 2006) est la méthode de
référence pour estimer la distribution potentielle d'une espèce à
partir de données de présence seule et de variables environnementales
(climat, altitude, sol). Elle constitue une piste pour compléter, à
titre indicatif et avec un `evidence_level` explicitement abaissé par
rapport à une observation empirique documentée (type Rameau et al.),
des champs de la structure `Autecologie` peu couverts par la
littérature de terrain.

**biomod2** (package R, CRAN) est une plateforme d'ensemble de
modélisation de la distribution d'espèces qui combine jusqu'à une
dizaine d'algorithmes (GLM, MARS, arbres de classification, boosted
regression trees, random forest, réseau de neurones via `cito`) en un
modèle d'ensemble avec score de confiance agrégé — une piste pour
croiser plusieurs approches de modélisation et documenter un niveau de
preuve consolidé, cohérent avec l'échelle `evidence_level` (A à F)
déjà prévue dans le contrat de sortie du moteur.

### 8.3 Identification automatique par vision

**Pl@ntNet** est un service opérationnel d'identification visuelle de
plantes développé par un consortium associant Cirad, Inria, INRAE, IRD
et le réseau Tela Botanica. Sa documentation d'API indique une
couverture d'environ 78 800 espèces, un moteur initialement fondé sur
des réseaux de neurones convolutifs (CNN) puis migré vers des
architectures Vision Transformer (ViT). Deux publications documentent
son fonctionnement : Joly et al. (2016) pour l'architecture générale de
la plateforme, et Lefort et al. (préprint 2024, publication *Methods in
Ecology and Evolution*) pour le mécanisme d'apprentissage coopératif du
modèle. Pl@ntNet constitue une piste directe pour le type de requête
`identification` du contrat d'entrée — en tant que service externe
consommé via API, sans réentraînement interne, ce qui est cohérent avec
la garantie de fonctionnement hors-ligne sur cache local : un tel appel
serait une capacité en ligne complémentaire, non substituable au cache.

### Synthèse

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| TAXREF (MNHN/INPN) | Référentiel taxonomique et nomenclatural pivot pour la flore française, socle du versionnement | Référentiel national officiel (SINP), v18.0 publiée le 2025-01-09, web service disponible depuis la v2 |
| GBIF Taxonomic Backbone (API `species/match`) | Résolution de synonymes et mise en correspondance de noms à l'échelle internationale | Backbone alimenté par le Catalogue of Life ; GBIF est déjà cité comme source d'entrée du moteur |
| Catalogue of Life (CoL) | Modèle conceptuel pour la structure interne de gestion de synonymie et de versionnement taxonomique | Structure de référence utilisée par GBIF et par de nombreux référentiels nationaux |
| MaxEnt (Phillips et al., 2006) | Estimation d'optimums/niches écologiques à partir de données de présence et de variables environnementales | Méthode de référence en modélisation de distribution à données de présence seule |
| biomod2 (R, CRAN) | Agrégation de plusieurs modèles de distribution (dont MaxEnt) en un ensemble avec score de confiance | Plateforme d'ensemble consolidée permettant de documenter un niveau de preuve agrégé |
| Pl@ntNet (API) | Identification automatique par image pour le type `identification` du contrat d'entrée | Service opérationnel (Cirad/Inria/INRAE/IRD/Tela Botanica), ~78 800 espèces, documenté scientifiquement |

Le catalogue des données forestières et de l'inventaire forestier
national de l'IGN (`ign.fr/offre`) recoupe par ailleurs les catalogues
de stations forestières du CNPF cités dans la section équivalente du
`PEDOLOGY_ENGINE` — un lien à formaliser entre les deux moteurs pour la
correspondance sol/cortège floristique.

### Sources

- TAXREF v18.0, référentiel taxonomique pour la France. Muséum national d'Histoire naturelle (MNHN) / INPN, publié le 09/01/2025. https://inpn.mnhn.fr/
- TaxRef — Muséum national d'Histoire naturelle. https://taxref.mnhn.fr/taxref-web/
- GBIF Secretariat. « Taxonomy interpretation », documentation technique GBIF. https://techdocs.gbif.org/en/data-processing/taxonomy-interpretation
- GBIF Backbone Taxonomy (jeu de données). https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c
- Catalogue of Life. https://www.catalogueoflife.org/
- Phillips, S.J., Anderson, R.P., Schapire, R.E. (2006). « Maximum entropy modeling of species geographic distributions ». Ecological Modelling, 190(3-4), 231-259.
- biomod2: Ensemble Platform for Species Distribution Modeling (package R). CRAN. https://cran.r-project.org/package=biomod2 — https://biomodhub.github.io/biomod2/
- Pl@ntNet API — documentation développeur. https://docs.plantnet.org/en/reference/api-plantnet/ et https://my.plantnet.org/
- Joly, A., Bonnet, P., Goëau, H. et al. (2016). « A look inside the Pl@ntNet experience ». Multimedia Systems, 22(6), 751-766.
- Lefort, V. et al. (préprint 2024, arXiv:2406.03356 ; publication Methods in Ecology and Evolution). « Cooperative learning of Pl@ntNet's Artificial Intelligence algorithm ». https://arxiv.org/pdf/2406.03356
- IGN — Catalogue des offres (données forestières, inventaire forestier). https://www.ign.fr/offre

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*

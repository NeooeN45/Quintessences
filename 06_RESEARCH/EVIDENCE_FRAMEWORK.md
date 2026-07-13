# GSIE Evidence Framework — Cadre d'assignation des niveaux de preuve

| Champ | Valeur |
|---|---|
| **Livrable** | 306 — Evidence Framework |
| **Phase** | 3 — Connaissance |
| **Statut** | Draft |
| **Date de révision** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-002, GSIE-CON-005 |
| **Constitutions liées** | Scientifique (S-2, S-3, S-5) |
| **Directive d'ouverture** | GSIE-DIR-0007 (DEC-000011) |

---

## 1. Objet

Définir le cadre opérationnel d'assignation des six niveaux de preuve
(A à F) utilisés par l'Evidence Engine (livrable 206) pour qualifier chaque
connaissance intégrée à GSIE. Ce framework opérationnalise l'article S-2 de
la Constitution Scientifique en fournissant :

- des **critères opérationnels précis** pour chaque niveau (section 2) ;
- une **matrice de décision** déterminant comment l'Evidence Engine assigne
  un niveau à partir de la catégorie de source (S-1), de la convergence des
  sources et de la taille de l'échantillon (section 3) ;
- des **exemples concrets par domaine scientifique** (section 4) couvrant
  les 10 domaines définis par S-6 ;
- des **règles de résolution des cas limites** (section 5) ;
- un **tableau formel des règles d'upgrade et de downgrade** (section 6) ;
- un **modèle de quantification de l'incertitude** (section 7) conforme à
  l'article S-5.

Ce document complète le livrable 301 (Research Method), qui décrit le
pipeline de recherche en 10 étapes. L'étape 4 du pipeline (« Attribution
d'un niveau de preuve ») renvoie explicitement au présent framework pour
les critères détaillés.

---

## 2. Définition des 6 niveaux de preuve

La Constitution Scientifique (S-2) définit six niveaux de preuve, de A
(prouvé) à F (observation). Le tableau ci-dessous reprend ces définitions et
ajoute les **critères opérationnels** qui permettent à l'Evidence Engine
d'attribuer un niveau de manière reproductible et auditable.

### 2.1 Tableau des niveaux

| Niveau | Label | Définition (S-2) | Critères opérationnels |
|---|---|---|---|
| **A** | Prouvé | Consensus scientifique large, multiples études peer-reviewed convergentes | (1) ≥ 3 sources indépendantes de catégorie peer-reviewed ou référentiel officiel ; (2) convergence des conclusions (pas de contradiction majeure non résolue) ; (3) recul temporel suffisant (≥ 5 ans de littérature convergente) ; (4) idéalement méta-analyse ou synthèse institutionnelle |
| **B** | Établi | Études peer-reviewed convergentes, consensus partiel | (1) 1 à 2 sources peer-reviewed ou référentiel officiel ; (2) reproductibilité du protocole ; (3) aucune contradiction d'égale qualité ; (4) domaine de validité explicitement délimité par la source |
| **C** | Probable | Études limitées ou contradictoires, tendance dominante | (1) source peer-reviewed unique avec échantillon limité, OU (2) plusieurs sources avec contradiction non résolue mais tendance dominante, OU (3) document technique validé de qualité ; (4) domaine de validité partiel ou extrapolé |
| **D** | Hypothèse | Publication unique ou études préliminaires | (1) publication unique (peer-reviewed ou préprint), OU (2) étude préliminaire, thèse, communication de conférence sans actes ; (3) échantillon restreint ou protocole non reproduit ; (4) aucune source convergente indépendante |
| **E** | Expert | Connaissance experte non publiée, témoignage d'expert reconnu | (1) expert identifié, daté, signé (nom, fonction, organisme) ; (2) expertise reconnue dans le domaine (publications antérieures ou mandat institutionnel) ; (3) pas de publication directe pour cette connaissance ; (4) cohérence interne vérifiable |
| **F** | Observation | Observation terrain isolée, sans recoupement | (1) observation directe avec date et localisation ; (2) protocole de mesure décrit ; (3) aucune source convergente ; (4) aucune publication ni expertise reconnue associée ; (5) non recoupée par une seconde observation indépendante |

### 2.2 Principes transverses

Les principes suivants s'appliquent à tous les niveaux :

1. **Le niveau est attribué par l'Evidence Engine**, pas par le chercheur
   humain directement (S-2). Le chercheur soumet une
   `RawKnowledgeSubmission` (livrable 206) ; le moteur évalue et attribue.
2. **Le niveau est affiché à l'utilisateur** à chaque recommandation (S-2).
   Il n'est jamais masqué, jamais omis.
3. **Le niveau est conservé dans la traçabilité** de la connaissance
   (CON-005). Toute réévaluation crée une nouvelle version (CON-010).
4. **Un niveau ne peut jamais être supérieur au plafond imposé par la
   catégorie de source** (voir section 3, matrice de décision).
5. **L'incertitude associée au niveau est quantifiée si possible et
   affichée** (S-5, voir section 7).

---

## 3. Matrice de décision

L'Evidence Engine assigne un niveau de preuve selon trois axes :

- **Axe 1 — Catégorie de source** (S-1) : détermine le niveau maximum
  atteignable (plafond).
- **Axe 2 — Convergence des sources** : nombre de sources indépendantes
  convergentes pour la même connaissance.
- **Axe 3 — Taille de l'échantillon et robustesse** : effectif, durée
  d'observation, reproductibilité.

### 3.1 Plafond par catégorie de source

La catégorie de source (S-1) impose un plafond. Aucune règle d'upgrade ne
peut franchir ce plafond sans changement de catégorie.

| Catégorie de source (S-1) | Niveau maximum atteignable | Rationale |
|---|---|---|
| Peer-reviewed (revue indexée, comité de lecture) | **B** (source unique) → A (si convergence) | Source de plus haute qualité ; le niveau A exige la convergence multi-sources |
| Référentiel officiel (INRAE, IGN, ONF, Météo-France) | **B** | Validation institutionnelle, procédure formelle, mais ne remplace pas le consensus peer-reviewed multi-sources |
| Document technique validé (guide ONF, document CRPF) | **C** | Comité de validation professionnel, mais pas de comité de lecture scientifique |
| Connaissance experte (expert identifié, daté, signé) | **D** | Expertise reconnue mais non publiée ; ne peut pas dépasser le niveau d'une publication unique |
| Observation terrain (mesure directe, protocole décrit) | **F** | Observation isolée, non recoupée |

### 3.2 Règle de calcul du niveau initial

```
niveau_initial = min(
    plafond_categorie_source,
    niveau_convergence,
    niveau_robustesse
)
```

Où :

- `plafond_categorie_source` : voir tableau 3.1.
- `niveau_convergence` : fonction du nombre de sources indépendantes
  convergentes (voir 3.3).
- `niveau_robustesse` : fonction de la taille de l'échantillon et de la
  reproductibilité (voir 3.4).

### 3.3 Niveau selon la convergence des sources

| Nombre de sources indépendantes convergentes | Niveau de convergence |
|---|---|
| ≥ 3 sources peer-reviewed ou référentiel convergentes, sans contradiction majeure | A |
| 2 sources peer-reviewed ou référentiel convergentes | B |
| 1 source peer-reviewed ou référentiel | B (plafonné par la catégorie) |
| 1 source avec tendance convergentes mais contradictions mineures | C |
| 1 source unique, aucune convergence | D (plafonné par la catégorie) |
| 0 source publiée, expertise uniquement | E |
| 0 source publiée, observation uniquement | F |

### 3.4 Niveau selon la robustesse de l'échantillon

| Robustesse | Critères | Ajustement |
|---|---|---|
| Élevée | Échantillon ≥ 100 individus/placettes OU ≥ 10 ans de suivi OU méta-analyse | Aucun downgrade |
| Moyenne | Échantillon 30–99 OU 3–10 ans de suivi | Downgrade d'un niveau si la source est unique |
| Faible | Échantillon < 30 OU < 3 ans OU protocole non reproduit | Downgrade d'un niveau systématique |

### 3.5 Exemple de calcul

Une publication peer-reviewed (Rameau et al., 2018) décrit l'optimum
écologique du chêne sessile sur sols acides à pH 4,5–6,0, avec un
échantillon de 250 placettes sur 15 ans.

- `plafond_categorie_source` = B (peer-reviewed unique).
- `niveau_convergence` = B (1 source).
- `niveau_robustesse` = élevée (250 placettes, 15 ans) → aucun downgrade.
- `niveau_initial` = min(B, B, B) = **B**.

Si deux autres publications indépendantes (Dobremez, 2019 ; ONF, 2020)
convergent vers la même gamme de pH, la règle d'upgrade (section 6) s'applique
et le niveau passe à **A**.

---

## 4. Exemples concrets par domaine scientifique

Les 10 domaines scientifiques définis par S-6 sont illustrés ci-dessous par
au moins un exemple concret, avec le raisonnement complet d'assignation du
niveau de preuve.

### 4.1 Écologie forestière — Autécologie du chêne sessile

| Élément | Valeur |
|---|---|
| **Connaissance** | Optimum écologique du chêne sessile (*Quercus petraea*) sur sols acides à pH 4,5–6,0, altitude < 800 m |
| **Sources** | Rameau et al. (2018) — *Annals of Forest Science* ; Dobremez (2019) — *Revue forestière française* ; Guide ONF sylviculture chênes (2020) |
| **Catégorie de source** | Peer-reviewed (×2) + référentiel officiel (×1) |
| **Convergence** | 3 sources indépendantes convergentes, aucune contradiction |
| **Robustesse** | Élevée (250+ placettes, 15 ans de suivi) |
| **Niveau assigné** | **A — Prouvé** |
| **Justification** | 3 sources indépendantes de haute qualité convergentes, recul temporel suffisant, aucune contradiction |

### 4.2 Pédologie — Seuil de pH pour alocrisol

| Élément | Valeur |
|---|---|
| **Connaissance** | L'alocrisol (Référentiel Pédologique Français) présente un pH eau compris entre 3,5 et 5,5 avec saturation en aluminium > 50 % |
| **Sources** | Référentiel Pédologique Français (INRAE, édition 2008) ; Baize & Jabiol (2011) — *Étude et gestion des sols* |
| **Catégorie de source** | Référentiel officiel (×1) + peer-reviewed (×1) |
| **Convergence** | 2 sources convergentes |
| **Robustesse** | Élevée (référentiel national, protocole standardisé) |
| **Niveau assigné** | **B — Établi** |
| **Justification** | Référentiel INRAE + publication convergente ; plafond B pour référentiel, 2 sources convergentes → B confirmé |

### 4.3 Dendrométrie — Modèle de croissance ONF-FFN

| Élément | Valeur |
|---|---|
| **Connaissance** | Modèle de croissance en hauteur dominante pour le chêne sessile (équation de Hossfeld IV modifiée), âge < 120 ans, productivité modérée |
| **Sources** | ONF — Fichier Forestier National (FFN), modèle de production 2017 ; Dupouey et al. (2020) — validation indépendante |
| **Catégorie de source** | Référentiel officiel (×1) + peer-reviewed (×1) |
| **Convergence** | 2 sources convergentes (modèle + validation) |
| **Robustesse** | Élevée (≥ 3 000 placettes IFN, calibration nationale) |
| **Niveau assigné** | **B — Établi** |
| **Justification** | Référentiel national + validation peer-reviewed ; 2 sources convergentes → B ; pas de 3e source indépendante → pas d'upgrade vers A |

### 4.4 Climatologie — Projections DRIAS

| Élément | Valeur |
|---|---|
| **Connaissance** | Projection climatique régionalisée pour la France métropolitaine à horizon 2050 (scénario RCP 4.5), résolution 8 km, modèle ALADIN63 |
| **Sources** | DRIAS 2020 — Météo-France (jeu de données régionalisé) ; IPCC AR6 (2021) — cadre global |
| **Catégorie de source** | Référentiel officiel (×1) + peer-reviewed (×1, IPCC) |
| **Convergence** | 2 sources convergentes (cadre global + régionalisation) |
| **Robustesse** | Élevée (multi-modèles, 12 simulations GCM/RCM) |
| **Niveau assigné** | **B — Établi** |
| **Justification** | Référentiel Météo-France + IPCC AR6 ; plafond B pour référentiel. L'incertitude inter-modèles est quantifiée (section 7) et affichée |

### 4.5 Botanique — Taxonomie *Quercus petraea*

| Élément | Valeur |
|---|---|
| **Connaissance** | *Quercus petraea* (Matt.) Liebl. — chêne sessile, famille Fagaceae, synonyme *Quercus sessiliflora* Salisb. |
| **Sources** | GBIF (2024) — Backbone Taxonomy ; Tela Botanica (2024) — eFlore ; BDNFF (Base de Données Nomenclaturale de la Flore de France, 2023) |
| **Catégorie de source** | Référentiel officiel (×3) |
| **Convergence** | 3 sources indépendantes convergentes (même nom accepté, mêmes synonymes) |
| **Robustesse** | Élevée (référentiels taxonomiques nationaux et internationaux) |
| **Niveau assigné** | **A — Prouvé** |
| **Justification** | 3 référentiels indépendants convergents ; consensus taxonomique international stable. La taxonomie est un domaine où le consensus est par nature large |

### 4.6 Pathologie — Seuil de dégât pour la chalarose du frêne

| Élément | Valeur |
|---|---|
| **Connaissance** | Seuil de dépérissement > 50 % de couronnes atteintes déclenche la recommandation de ne pas régénérer par plantation de frêne (*Fraxinus excelsior*) sur la zone |
| **Sources** | Husson et al. (2019) — *Forest Pathology* ; DSF (Département Santé des Forêts) — bulletin 2022 ; Gross et al. (2014) — étude préliminaire |
| **Catégorie de source** | Peer-reviewed (×2) + référentiel officiel (×1) |
| **Convergence** | Tendance dominante mais divergences sur le seuil exact (40 % vs 50 % vs 60 % selon les études) |
| **Robustesse** | Moyenne (échantillons variables, pas de protocole harmonisé national) |
| **Niveau assigné** | **C — Probable** |
| **Justification** | Sources convergentes sur la tendance (dépérissement → éviter régénération) mais contradiction sur le seuil exact. Tendance dominante à 50 %, mais non consensuelle → C |

### 4.7 Entomologie — Seuil de population pour scolyte

| Élément | Valeur |
|---|---|
| **Connaissance** | Seuil de 2 000 attaques de *Ips typographus* par hectare et par an déclenchant l'alerte de risque d'infestation épidémique sur épicéa commun (*Picea abies*) |
| **Sources** | Communication préliminaire INRAE (2023) — Journées Forestières de Santé ; observation DSF 2022 (non publiée) |
| **Catégorie de source** | Préprint / communication (×1) + observation terrain (×1) |
| **Convergence** | 1 source préliminaire + 1 observation non recoupée |
| **Robustesse** | Faible (échantillon limité à 2 massifs, protocole non reproduit) |
| **Niveau assigné** | **D — Hypothèse** |
| **Justification** | Publication unique préliminaire, échantillon restreint, pas de source convergente indépendante peer-reviewed. Le seuil est une hypothèse de travail, à confirmer |

### 4.8 Sylviculture — Densité de plantation recommandée

| Élément | Valeur |
|---|---|
| **Connaissance** | Densité de plantation recommandée pour le chêne sessile en futaie régulière : 1 100 à 1 400 plants/ha (objectif bois d'œuvre, densité finale 120–180 tiges/ha à 60 ans) |
| **Sources** | Guide ONF sylviculture du chêne (2018) ; Guide CRPF Centre-Val de Loire (2020) ; Jarret & Jappiot (2017) — *Revue forestière française* |
| **Catégorie de source** | Document technique validé (×2) + peer-reviewed (×1) |
| **Convergence** | 3 sources convergentes sur la fourchette 1 100–1 400 |
| **Robustesse** | Élevée (recommandations issues de > 30 ans d'expérimentation) |
| **Niveau assigné** | **B — Établi** |
| **Justification** | Plafond C pour documents techniques, mais présence d'1 source peer-reviewed → plafond B. 3 sources convergentes → B confirmé. L'upgrade vers A nécessiterait 3 sources peer-reviewed indépendantes (ici 1 seule) |

### 4.9 Biodiversité — Indicateur de diversité

| Élément | Valeur |
|---|---|
| **Connaissance** | Indice de Shannon (H') calculé sur la flore vasculaire d'une placette : H' > 2,5 indique une diversité élevée pour une forêt tempérée française à l'échelle de la placette (400 m²) |
| **Sources** | Gosselin & Pargada (2019) — *Forest Ecology and Management* ; Inventaire forestier national IGN — protocole de biodiversité 2021 ; MNHN — référentiel d'évaluation |
| **Catégorie de source** | Peer-reviewed (×1) + référentiel officiel (×2) |
| **Convergence** | 3 sources convergentes sur le seuil H' > 2,5 |
| **Robustesse** | Élevée (protocole standardisé, > 5 000 placettes IGN) |
| **Niveau assigné** | **B — Établi** |
| **Justification** | 1 source peer-reviewed + 2 référentiels convergents. Plafond B (référentiel majoritaire). L'absence de 3 sources peer-reviewed indépendantes empêche l'upgrade vers A. Le seuil est contextuel (forêt tempérée française) et affiché comme tel |

### 4.10 Dynamique des peuplements — Modèle de succession

| Élément | Valeur |
|---|---|
| **Connaissance** | Modèle de succession secondaire en forêt tempérée : peuplier tremble → bouleau → chêne sessile → hêtre sur sols acides à mull oligotrophe, cycle 150–200 ans sans perturbation majeure |
| **Sources** | Rameau (2016) — *Phytosociologie forestière* ; Barbier et al. (2018) — *Annals of Forest Science* (validation partielle sur 3 massifs) |
| **Catégorie de source** | Peer-reviewed (×2) |
| **Convergence** | 2 sources convergentes sur la séquence générale, mais divergence sur la durée du stade chêne (80 ans vs 120 ans) |
| **Robustesse** | Moyenne (3 massifs, suivi < 30 ans pour validation, cycle extrapolé) |
| **Niveau assigné** | **C — Probable** |
| **Justification** | Sources convergentes sur la séquence mais contradictoires sur la durée des stades. Tendance dominante identifiée, mais consensus partiel → C. L'extrapolation temporelle (cycle 150–200 ans non observé en continu) introduit une incertitude affichée |

### 4.11 Tableau récapitulatif des exemples

| Domaine (S-6) | Connaissance | Niveau | Source principale |
|---|---|---|---|
| Écologie forestière | Autécologie chêne sessile (pH 4,5–6,0) | A | Rameau et al. (2018) + 2 sources |
| Pédologie | Seuil pH alocrisol (3,5–5,5) | B | RPF INRAE (2008) |
| Dendrométrie | Modèle croissance ONF-FFN | B | ONF FFN (2017) |
| Climatologie | Projections DRIAS 2050 | B | Météo-France DRIAS (2020) |
| Botanique | Taxonomie *Quercus petraea* | A | GBIF + Tela Botanica + BDNFF |
| Pathologie | Seuil chalarose du frêne (50 %) | C | Husson et al. (2019) |
| Entomologie | Seuil scolyte *Ips typographus* | D | Communication INRAE (2023) |
| Sylviculture | Densité plantation chêne (1 100–1 400/ha) | B | Guide ONF (2018) |
| Biodiversité | Indice Shannon H' > 2,5 | B | Gosselin & Pargada (2019) |
| Dynamique | Succession peuplier → hêtre | C | Rameau (2016) + Barbier (2018) |

---

## 5. Cas limites et règles de résolution

Les cas suivants ne sont pas triviaux et nécessitent des règles explicites.
Toutes ces règles sont implémentées par l'Evidence Engine et tracées dans le
journal d'audit.

### 5.1 Conflit entre deux sources de même niveau (S-3)

**Situation** : deux sources de catégorie et niveau identiques donnent des
valeurs contradictoires pour un même paramètre.

**Exemple** : deux publications peer-reviewed donnent des seuils de
vulnérabilité au gel du sapin pectiné : -20 °C (source A, 2015) et -15 °C
(source B, 2023, provenances du Sud).

**Règle** :
1. **Aucune source n'est supprimée** (S-3) — les deux sont conservées.
2. Un `ConflitBibliographique` est créé, référençant les deux sources avec
   dates et contextes.
3. **Aucune moyenne arbitraire** n'est calculée (S-3).
4. Le niveau de preuve de chaque connaissance est **maintenu** (B dans cet
   exemple) — le conflit ne déclenche pas un downgrade automatique.
5. Le conflit est **signalé à l'utilisateur** : GSIE présente les deux
   positions avec leurs contextes.
6. Si une résolution est nécessaire, elle passe par une **RFC et un comité
   scientifique** (S-3), jamais par une décision automatique.

### 5.2 Conflit entre sources de niveau différent

**Situation** : une source de niveau élevé contredit une source de niveau
inférieur.

**Exemple** : une publication peer-reviewed (niveau B) indique un optimum
de pH 4,5–6,0 pour le chêne sessile ; un guide technique (niveau C) indique
pH 5,0–7,0.

**Règle** :
1. Les deux connaissances sont conservées avec leurs niveaux respectifs (B
   et C).
2. Un `ConflitBibliographique` est créé.
3. La source de niveau supérieur (B) est **présentée en premier** à
   l'utilisateur, la source de niveau inférieur (C) est présentée comme
   alternative avec son niveau affiché.
4. Aucune fusion n'est effectuée.
5. Le niveau de la connaissance de niveau inférieur n'est pas downgradé
   automatiquement — le conflit est documenté, pas résolu.

### 5.3 Connaissance experte confirmée par publication (upgrade E → B)

**Situation** : une connaissance de niveau E (expert) est confirmée par une
publication peer-reviewed ultérieure.

**Exemple** : un expert forestier signale en 2022 que le hêtre présente une
sensibilité accrue à la sécheresse sur sols superficiels calcaires
(niveau E). En 2024, une publication de Lebourgeois et al. confirme ce
pattern sur 15 placettes (niveau B).

**Règle** :
1. La connaissance experte (E) est **conservée** dans l'historique
   (CON-010).
2. Une **nouvelle version** de la connaissance est créée avec la source
   peer-reviewed.
3. Le niveau est **réévalué** : E → B (upgrade, voir section 6).
4. La traçabilité conserve le lien entre la version E (origine experte) et
   la version B (confirmation publiée).

### 5.4 Observation terrain recoupée (upgrade F → D)

**Situation** : une observation terrain isolée (niveau F) est recoupée par
une seconde observation indépendante.

**Exemple** : un forestier observe en 2023 une mortalité anormale de
charmes sur une placette en Bourgogne (niveau F). En 2024, un technicien
ONF observe le même phénomène sur un massif voisin, avec protocole décrit.

**Règle** :
1. La première observation (F) est conservée dans l'historique.
2. Une **nouvelle version** est créée intégrant les deux observations.
3. Le niveau passe de F à **D** (deux observations indépendantes
   convergentes, sans publication — équivalent à une étude préliminaire).
4. Si une publication peer-reviewed confirme ultérieurement, le niveau peut
   monter jusqu'à B (upgrade D → B).

### 5.5 Source ancienne vs source récente

**Situation** : une source ancienne et une source récente donnent des
valeurs différentes pour un même paramètre.

**Exemple** : le Référentiel Pédologique Français (édition 1995) définit
les alocrisols avec un pH 4,0–5,5 ; l'édition 2008 révisée élargit à
pH 3,5–5,5.

**Règle** :
1. **Aucune source n'est supprimée** — l'édition 1995 est conservée dans
   l'historique (CON-010, S-7).
2. L'édition la plus récente (2008) est **présentée en priorité** comme
   version courante.
3. Le niveau de preuve de la version courante est celui de la source la
   plus récente (B pour référentiel INRAE).
4. Si l'ancienne édition contient des connaissances non reprises dans la
   nouvelle, elles sont conservées avec leur niveau original et un
   avertissement de périmence.
5. Une RFC de révision (S-4) est créée si la modification est majeure.

### 5.6 Source locale vs source nationale

**Situation** : une source locale (monographie régionale) et une source
nationale (référentiel) donnent des valeurs différentes.

**Exemple** : une étude locale sur les Vosges indique un optimum altitudinal
du sapin pectiné à 900–1 200 m ; le référentiel national IGN indique
600–1 500 m.

**Règle** :
1. Les deux connaissances sont conservées avec leurs niveaux respectifs.
2. La source locale est **affinée géographiquement** : son domaine de
   validité est restreint au massif vosgien.
3. La source nationale a un domaine de validité plus large mais moins
   précis.
4. Le moteur de raisonnement utilise la source locale si la localisation de
   l'utilisateur est dans le périmètre local, et la source nationale sinon.
5. Les deux sont présentées à l'utilisateur avec leurs domaines de validité
   respectifs.

---

## 6. Règles d'upgrade et de downgrade

### 6.1 Tableau formel des règles

| Règle | Condition | Effet | Justification |
|---|---|---|---|
| **Upgrade B → A** | ≥ 3 sources indépendantes de catégorie peer-reviewed ou référentiel officiel, convergentes, sans contradiction majeure non résolue | B → A | Consensus multi-sources = critère S-2 du niveau A |
| **Upgrade C → B** | 2 sources indépendantes convergentes de catégorie peer-reviewed ou référentiel, résolvant la contradiction initiale | C → B | La résolution de la contradiction élève le niveau |
| **Upgrade D → B** | 1 source peer-reviewed indépendante confirme l'hypothèse initiale | D → B | Confirmation par publication = passage d'hypothèse à établi |
| **Upgrade E → B** | 1 source peer-reviewed confirme la connaissance experte | E → B | La publication transforme l'expertise en connaissance établie |
| **Upgrade E → D** | 2 observations indépendantes recoupent l'expertise, sans publication | E → D | Recoupement d'observations = équivalent étude préliminaire |
| **Upgrade F → D** | 1 seconde observation indépendante recoupe la première | F → D | Deux observations indépendantes = équivalent étude préliminaire |
| **Downgrade B → C** | 1 source contradictoire de même niveau (peer-reviewed) apparaît | B → C | La contradiction non résolue fait passer d'établi à probable |
| **Downgrade C → D** | La source unique est invalidée partiellement (retrait, erratum) | C → D | Perte de la tendance dominante = retour à hypothèse |
| **Downgrade D → E** | La publication unique est rétractée (retraction) | D → E | Perte de la publication = retour à expertise si l'auteur reste crédible |
| **Downgrade tout niveau → F** | La source est invalidée et aucune source alternative n'est disponible | → F | Sans source, seule l'observation terrain subsiste |

### 6.2 Conditions d'application

1. **Toute upgrade ou downgrade crée une nouvelle version** de la
   connaissance (CON-010). L'ancien niveau est conservé dans l'historique.
2. **Toute upgrade ou downgrade est tracée** dans le journal d'audit de
   l'Evidence Engine avec : la connaissance concernée, l'ancien niveau, le
   nouveau niveau, la règle appliquée, les sources impliquées, la date.
3. **Aucune upgrade ne peut franchir le plafond de catégorie de source**
   (section 3.1). Une observation terrain (plafond F) ne peut pas être
   upgradée au-delà de D sans publication confirmante.
4. **Les downgrades sont réversibles** : si la source contradictoire est
   elle-même invalidée, la connaissance peut être ré-upgradée via une
   nouvelle version.
5. **Les upgrades vers A exigent obligatoirement** un comité scientifique
   ou une RFC (S-4) — l'Evidence Engine propose, le comité valide.

### 6.3 Schéma de transition

```
F ──(recoupement)──> D ──(publication)──> B ──(≥3 sources)──> A
│                      │                     │
│                      └──(expertise)──> E   └──(contradiction)──> C
│                                              │
└──(recoupement expert)──> E                   └──(invalidation)──> D
                                               └──(retraction)──> E
```

---

## 7. Quantification de l'incertitude (S-5)

L'article S-5 impose que toute incertitude scientifique soit identifiée,
quantifiée si possible, affichée et jamais masquée. Cette section définit
le modèle opérationnel de quantification.

### 7.1 Sources d'incertitude

| Source | Description | Exemple forestier |
|---|---|---|
| **Incertitude de mesure** | Erreur instrumentale ou protocole de mesure | Erreur sur mesure de pH (± 0,2 unité) ; erreur dendrométrique sur circonférence (± 1 cm) |
| **Variabilité naturelle** | Hétérogénéité spatiale ou temporelle du phénomène | Variabilité du pH dans un même horizon (± 0,5) ; variabilité inter-annuelle de croissance |
| **Incertitude d'échantillonnage** | Taille d'échantillon limitée, biais de sélection | Estimation de la hauteur dominante sur 30 placettes (intervalle de confiance à 95 %) |
| **Incertitude de modèle** | Choix du modèle, paramètres calibrés, extrapolation | Écart-type des projections DRIAS inter-modèles (12 simulations RCM) |
| **Incertitude de classification** | Ambiguïté taxonomique ou pédologique | Confusion *Quercus petraea* / *Quercus robur* sur caractères intermédiaires |
| **Incertitude de niveau de preuve** | Le niveau lui-même reflète une incertitude | Niveau C = incertitude modérée ; niveau D = incertitude élevée |

### 7.2 Outils de quantification

| Outil | Définition | Quand l'utiliser |
|---|---|---|
| **Intervalle de confiance (IC)** | Plage de valeurs dans laquelle le paramètre réel se trouve avec une probabilité donnée (généralement 95 %) | Quand la source fournit un estimateur statistique et un échantillon |
| **Marge d'erreur** | Demi-largeur de l'intervalle de confiance, exprimée en ± unités | Quand l'utilisateur a besoin d'une valeur unique avec sa précision |
| **Écart-type (σ)** | Mesure de la dispersion des valeurs autour de la moyenne | Quand la source fournit une distribution (variabilité naturelle) |
| **Coefficient de variation (CV)** | Écart-type rapporté à la moyenne (σ / μ), exprimé en % | Pour comparer la variabilité entre paramètres d'échelles différentes |
| **Plage de projection** | Étendue des valeurs prédites par un ensemble de modèles | Pour les projections climatiques (DRIAS) ou les modèles de croissance |
| **Indice de confiance** | Score qualitatif dérivé du niveau de preuve (A=5, B=4, C=3, D=2, E=1, F=1) | Quand aucune quantification statistique n'est disponible |

### 7.3 Affichage à l'utilisateur

L'incertitude est affichée à l'utilisateur **en même temps que la
connaissance et le niveau de preuve**. Le format d'affichage comprend :

1. **La valeur centrale** (ou la fourchette) de la connaissance.
2. **Le niveau de preuve** (A–F) avec son label textuel.
3. **L'incertitude quantifiée** si disponible (IC, marge d'erreur, écart-type).
4. **L'incertitude qualitative** si non quantifiable (ex. « incertitude
   élevée — étude préliminaire »).
5. **Les conflits bibliographiques** le cas échéant (S-3).

### 7.4 Exemples d'affichage

**Exemple 1 — pH optimum du chêne sessile (niveau A)** :

> Optimum de pH pour le chêne sessile : **4,5 – 6,0** (sol acide à
> modérément acide).
> Niveau de preuve : **A — Prouvé** (3 sources convergentes).
> Incertitude : faible (consensus multi-sources, variabilité naturelle
> ± 0,3 unité pH).

**Exemple 2 — Projection climatique DRIAS 2050 (niveau B)** :

> Augmentation de température moyenne annuelle à horizon 2050 (RCP 4.5) :
> **+1,8 °C** (moyenne multi-modèles).
> Niveau de preuve : **B — Établi** (référentiel Météo-France + IPCC AR6).
> Incertitude : **± 0,6 °C** (intervalle de confiance 95 %, plage
> inter-modèles : +1,2 à +2,4 °C).

**Exemple 3 — Seuil de scolyte (niveau D)** :

> Seuil d'alerte *Ips typographus* : **2 000 attaques/ha/an**.
> Niveau de preuve : **D — Hypothèse** (publication préliminaire unique).
> Incertitude : **élevée** — échantillon limité à 2 massifs, protocole non
> reproduit. Valeur à confirmer.

**Exemple 4 — Conflit sur le seuil de gel du sapin (niveau B + conflit)** :

> Seuil de vulnérabilité au gel du sapin pectiné :
> - Source A (2015) : **-20 °C** — niveau B.
> - Source B (2023, provenances du Sud) : **-15 °C** — niveau B.
> Conflit bibliographique signalé : les deux sources sont présentées.
> Aucune moyenne calculée. Le choix dépend de la provenance du peuplement.

### 7.5 Règle de non-masquage

Présenter un résultat certain quand la source est incertaine est une
**violation de la Constitution** (S-5). L'Evidence Engine refuse
l'intégration d'une connaissance si :

- la source indique une incertitude qui n'est pas retransmise dans la
  connaissance ;
- le niveau de preuve est D, E ou F et aucune mention d'incertitude n'est
  associée ;
- un conflit bibliographique existe et n'est pas signalé.

---

## 8. Articulation avec les autres livrables

| Livrable | Relation |
|---|---|
| 301 — Research Method | Le présent framework est référencé à l'étape 4 du pipeline de recherche (attribution du niveau de preuve) |
| 206 — Contrats d'interface | Définit les types `EvidenceLevel`, `QualifiedKnowledge`, `ConflitBibliographique` que ce framework opérationnalise |
| 302 — Knowledge Method | Le cycle de vie d'un `KnowledgeObject` intègre les règles d'upgrade/downgrade définies en section 6 |
| 303 — Forest Ontology | Les concepts par domaine (S-6) sont les supports des exemples de la section 4 |
| 307 — Sourcing Plan | Le plan d'ingestion priorise les sources permettant d'atteindre les niveaux A et B |
| 308 — Knowledge Base Seed | Les premières connaissances concrètes sont qualifiées selon ce framework |

---

## 9. Historique

| Date | Événement |
|---|---|
| 2026-07-13 | Création — Livrable 306, Phase 3 (Draft initial) |

---

> Statut : *Draft — Phase 3 (Connaissance). Documentation uniquement, aucune
> implémentation (Phase 4).*

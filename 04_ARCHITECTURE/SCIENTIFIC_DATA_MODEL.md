# SCIENTIFIC_DATA_MODEL — Modèle de données scientifique de GSIE

| Champ | Valeur |
|---|---|
| **Livrable** | 205 — Modèle de données scientifique |
| **Phase** | 2 — Architecture |
| **Statut** | Draft |
| **Date de révision** | 2026-07-12 |
| **Lois fondatrices** | GSIE-CON-002, GSIE-CON-005, GSIE-CON-010 |
| **Constitutions liées** | Scientifique (S-1 à S-7), Technique (T-6, T-8) |
| **RFC de référence** | RFC-0003 (GSIE-Net — synchronisation orientée données) |
| **Décision d'ouverture** | DEC-000004 |

---

## 1. Objet

Définir le modèle de données scientifique de GSIE : les entités
principales, leurs relations, les sources de données référencées et
le versioning des données scientifiques.

Ce modèle est la **structure** qui circule dans le pipeline des
moteurs (voir `GSIE_MASTER_ARCHITECTURE.md` §5). Il est conforme à
la Constitution Scientifique (S-1 à S-7) : toute donnée est sourcée,
versionnée, traçable et porte son niveau de preuve.

> **Note :** ce document décrit le modèle **logique** des données,
> pas le schéma physique de base (SQLite/PostgreSQL — à définir en
> Phase 3/4). Les structures ci-dessous sont des descriptions
> conceptuelles, pas du code métier.

---

## 2. Principes du modèle

### 2.1 Toute donnée est sourcée (S-1)

Aucune entité n'existe sans source. Chaque entité porte au minimum
une `SourceRef` (voir `ENGINE_COMMUNICATION_PROTOCOL.md` §3.4). Les
sources sont classées par catégorie (S-1) :

1. Publication peer-reviewed
2. Référentiel officiel (INRAE, IGN, ONF, Météo-France…)
3. Document technique validé
4. Connaissance experte (identifiée, datée, signée)
5. Observation terrain (datée, localisée, protocole décrit)

### 2.2 Toute donnée porte son niveau de preuve (S-2)

Chaque entité scientifique porte un `evidence_level` (A à F) attribué
par l'Evidence Engine. Ce niveau est **affiché à l'utilisateur** et
jamais masqué.

### 2.3 Toute donnée est versionnée (CON-010, S-7, T-6)

Chaque entité a un identifiant stable et un historique de versions.
L'ancienne version est conservée lors d'une révision (S-4). Le
versioning suit le modèle « commit » (RFC-0003 §4) : chaque
modification est un commit sur l'entité identifiée.

### 2.4 Toute incertitude est explicite (S-5)

Chaque donnée quantitative porte son incertitude (intervalle de
confiance, marge d'erreur, variabilité) si applicable. L'incertitude
est affichée à l'utilisateur, jamais masquée.

### 2.5 Conflits conservés (S-3)

Lorsque deux sources se contredisent, les deux sont conservées. Le
conflit est documenté et signalé. Aucune fusion arbitraire.

---

## 3. Entités principales

### 3.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    MODÈLE DE DONNÉES GSIE                    │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Station  │───▶│ Sol      │    │ Climat   │              │
│  │          │    │ (Pedology)│   │ (Climate)│              │
│  └────┬─────┘    └──────────┘    └──────────┘              │
│       │                                                      │
│  ┌────▼─────┐    ┌──────────┐    ┌──────────┐              │
│  │ Parcelle │    │ Essence  │    │ Source   │              │
│  │ (GIS)    │    │(Botanical)│   │ (SourceRef)│             │
│  └────┬─────┘    └────┬─────┘    └──────────┘              │
│       │               │                                      │
│  ┌────▼─────┐    ┌────▼─────┐    ┌──────────┐              │
│  │ Arbre    │───▶│ Obs.     │    │ Evidence │              │
│  │ (Tree)   │    │ Terrain  │    │ (Proof)  │              │
│  └────┬─────┘    └────┬─────┘    └──────────┘              │
│       │               │                                      │
│  ┌────▼─────┐         │                                      │
│  │ Peuplement│        │                                      │
│  │ (Stand)  │         │                                      │
│  └────┬─────┘         │                                      │
│       │               │                                      │
│  ┌────▼─────┐    ┌────▼─────┐    ┌──────────┐              │
│  │ Forest   │    │ Diagnostic│───▶│Recommand.│              │
│  │ Dynamics │    │          │    │          │              │
│  └──────────┘    └────┬─────┘    └──────────┘              │
│                       │                                      │
│                ┌──────▼─────┐    ┌──────────┐              │
│                │ Simulation │───▶│ Entités  │              │
│                │ Scenario   │    │ de sortie│              │
│                └────────────┘    └──────────┘              │
│                                                              │
│  Transverses :                                               │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Knowledge│    │ Corrélation│   │ Simulation│             │
│  │ Item     │    │          │    │ Scenario │              │
│  └──────────┘    └──────────┘    └──────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Entités géospatiales et stationnelles

#### Station

L'entité **Station** est l'unité écologique de base. Elle décrit un
milieu stationnel homogène (sol, climat, topographie, végétation).

```
Station {
  station_id      : string        // identifiant stable (UUID v7)
  label           : string        // nom lisible (ex: "Station 27 - versant nord")
  geometry        : GeoJSON       // polygone ou point (WGS84 / Lambert-93)

  // --- Caractéristiques stationnelles ---
  altitude_m      : Range         // altitude (min-max, en mètres)
  slope_deg       : Range         // pente (min-max, en degrés)
  aspect          : enum          // N | NE | E | SE | S | SW | W | NW | plat
  drainage        : enum          // bon | modéré | imparfait | mauvais | nul

  // --- Relations ---
  soil_id         : string?       // référence vers Sol (Pedology)
  climate_id      : string?       // référence vers Climat (Climate)
  parcelle_ids    : string[]      // références vers Parcelles (GIS)

  // --- Traçabilité ---
  sources         : SourceRef[]   // sources des caractéristiques (S-1)
  evidence_level  : enum          // niveau de preuve (A-F) (S-2)
  version         : int           // numéro de version (CON-010)
  created_at      : ISO 8601
  updated_at      : ISO 8601
  history         : Commit[]      // historique des révisions (RFC-0003 §4)
}
```

#### Parcelle

L'entité **Parcelle** est l'unité administrative/gestionnelle
(cadastrale ou forestière).

```
Parcelle {
  parcelle_id     : string        // identifiant stable
  label           : string        // référence cadastrale ou forestière
  geometry        : GeoJSON       // polygone (Lambert-93)
  area_ha         : float         // surface en hectares
  owner           : string?       // propriétaire (si disponible)
  management_plan : string?       // référence du plan de gestion
  station_id      : string?       // station rattachée

  sources         : SourceRef[]   // source cadastrale (IGN, cadastre)
  version         : int
  history         : Commit[]
}
```

#### Arbre (Tree)

L'entité **Arbre** est l'individu forestier mesuré sur le terrain.

```
Tree {
  tree_id         : string        // identifiant stable
  station_id      : string        // station de rattachement
  parcelle_id     : string?       // parcelle de rattachement
  species_id      : string        // référence vers Essence (Botanical)

  // --- Mesures dendrométriques ---
  dbh_cm          : Range         // diamètre à hauteur de poitrine (cm)
  height_m        : Range         // hauteur totale (m)
  crown_height_m  : Range?        // hauteur de cime (m)
  crown_diameter_m: Range?        // diamètre de cime (m)
  vitality        : enum?         // 0-5 (échelle sanitaire, sourcée)
  sanitary_status : enum?         // sain | dépérissant | mort | malade

  // --- Localisation ---
  position        : GeoJSON Point // GPS (WGS84)
  gps_precision   : float?        // HDOP ou précision en mètres

  // --- Métadonnées de terrain ---
  measured_at     : ISO 8601      // date de mesure
  measured_by     : string        // identifiant de l'observateur
  protocol        : string        // protocole de mesure (référence)
  photo_ids       : string[]?     // références vers photos

  // --- Traçabilité ---
  sources         : SourceRef[]   // observation terrain (S-1, catégorie 5)
  evidence_level  : enum          // niveau de preuve (F par défaut pour observation)
  version         : int
  history         : Commit[]      // historique des modifications (RFC-0003 §4)
}
```

#### Peuplement (Stand)

L'entité **Peuplement** représente un ensemble d'arbres constituant
une unité forestière cohérente sur une station ou une parcelle. Elle
caractérise la structure, la composition et la dynamique du couvert.
Elle est l'unité de raisonnement sylvicole et de projection (Forest
Dynamics).

```
Stand {
  stand_id         : string        // identifiant stable (UUID v7)
  station_id       : string        // station de rattachement
  parcelle_id      : string?       // parcelle de rattachement
  label            : string        // nom lisible (ex: "Peuplement 12 - futaie régulière de chêne")

  // --- Structure ---
  structure_type   : enum          // futaie_reguliere | futaie_irreguliere | melange_futaie_taillis | taillis | plantation | parc
  density          : float         // densité (tiges/ha)
  density_range    : Range?        // intervalle de densité si variable (S-5)
  age_mean         : Range         // âge moyen du peuplement (années)
  age_structure    : enum?         // regulier | irregulier | jumele | multistrate

  // --- Composition ---
  composition      : SpeciesShare[]  // composition en essences (parts surfaciques ou en nombre)
  dominant_species : string        // species_id de l'essence dominante
  richness         : int?          // nombre d'essences présentes

  // --- Dendrométrie de peuplement ---
  basal_area_m2    : float         // surface terrière (m²/ha)
  basal_area_range : Range?        // intervalle de surface terrière (S-5)
  mean_dbh_cm      : Range?        // diamètre moyen à hauteur de poitrine
  mean_height_m    : Range?        // hauteur moyenne de Lorey (m)
  volume_m3_ha     : Range?        // volume sur pied (m³/ha)

  // --- Relations ---
  tree_ids         : string[]      // arbres inventoriés rattachés
  growth_model_id  : string?       // référence vers GrowthModel (Forest Dynamics)

  // --- Traçabilité ---
  sources          : SourceRef[]   // IGN BD Forêt, inventaire terrain (S-1)
  evidence_level   : enum          // niveau de preuve (A-F) (S-2)
  version          : int           // numéro de version (CON-010)
  created_at       : ISO 8601
  updated_at       : ISO 8601
  history          : Commit[]      // historique des révisions (RFC-0003 §4)
}

SpeciesShare {
  species_id       : string        // référence vers Essence (Botanical)
  share            : float         // part (0.0-1.0) ou % surfacique
  share_type       : enum          // surfacique | nombre | volume
  source           : SourceRef     // source de la part (S-1)
}
```

### 3.3 Entités domaine

#### Sol (Pedology)

```
Soil {
  soil_id         : string
  station_id      : string

  // --- Caractéristiques pédologiques ---
  soil_type       : string        // classification (RPF ou WRB) — sourcée
  texture         : enum          // sableux | limoneux | argileux | mixte
  ph              : Range         // pH (min-max)
  depth_cm        : Range         // profondeur (cm)
  drainage        : enum          // bon | modéré | imparfait | mauvais | nul
  water_reserve_mm: Range         // réserve utile en eau (mm)

  // --- Traçabilité ---
  sources         : SourceRef[]   // BD Sols, référentiel RPF/WRB (S-1)
  evidence_level  : enum
  version         : int
  history         : Commit[]
}
```

#### Climat (Climate)

```
Climate {
  climate_id      : string
  station_id      : string

  // --- Variables climatiques (historiques) ---
  temp_mean_c     : Range         // température moyenne annuelle (°C)
  temp_min_c      : Range         // température minimale (°C)
  temp_max_c      : Range         // température maximale (°C)
  precip_mm       : Range         // précipitations annuelles (mm)
  drought_index   : Range?        // indice de déficit hydrique
  veg_days        : Range?        // durée de végétation (jours)

  // --- Projections (si applicable) ---
  projections     : ClimateProjection[]?  // projections climatiques

  // --- Traçabilité ---
  sources         : SourceRef[]   // Météo-France, DRIAS (S-1)
  evidence_level  : enum
  scenario        : string?       // RCP 4.5 / RCP 8.5 / SSP 2-4.5 / SSP 5-8.5 (S-5)
  uncertainty     : Range?        // incertitude de projection (S-5)
  period          : string        // période de référence (ex: "1991-2020")
  version         : int
  history         : Commit[]
}

ClimateProjection {
  scenario        : string        // RCP/SSP
  horizon         : string        // ex: "2050", "2100"
  temp_delta_c    : Range         // variation de température (°C)
  precip_delta_pct: Range         // variation des précipitations (%)
  uncertainty     : Range         // incertitude (S-5)
  source          : SourceRef     // DRIAS, GIEC (S-1)
}
```

#### Essence (Botanical)

```
Species {
  species_id      : string        // identifiant stable (taxon)
  scientific_name : string        // nom scientifique (référentiel BDNFF)
  common_name_fr  : string        // nom vernaculaire français
  synonyms        : string[]      // synonymes taxonomiques (CON-010)

  // --- Autécologie ---
  temp_optimum    : Range         // optimum thermique (°C)
  temp_amplitude  : Range         // amplitude thermique tolérée
  precip_optimum  : Range         // optimum pluviométrique (mm)
  precip_amplitude: Range         // amplitude pluviométrique
  soil_ph_range   : Range         // amplitude de pH
  soil_drainage   : enum[]        // drainages tolérés
  light_requirement: enum         // héliophile | demi-ombre | ombrophile

  // --- Traçabilité ---
  sources         : SourceRef[]   // Tela Botanica, GBIF, BDNFF, autécologie INRAE (S-1)
  evidence_level  : enum
  taxonomy_version: string        // version du référentiel taxonomique (CON-010)
  version         : int
  history         : Commit[]
}
```

#### Dynamique forestière (Forest Dynamics)

L'entité **GrowthModel** représente un modèle de croissance et de
production forestière mobilisé par le moteur Forest Dynamics pour
projeter l'évolution d'un peuplement. L'entité **ForestProjection**
matérialise une projection produite par un tel modèle sur un
peuplement donné.

```
GrowthModel {
  model_id          : string        // identifiant stable (UUID v7)
  label             : string        // nom lisible (ex: "Modèle croissance chêne sessile - INRAE")
  model_type        : enum          // diametre | hauteur | volume | biomasse | surface_terriere | complet
  species_ids       : string[]      // essences couvertes (références Species)

  // --- Paramètres du modèle ---
  formulation       : string        // formulation mathématique (équation, référence)
  parameters        : dict          // paramètres calibrés (nom → valeur)
  calibration       : SourceRef     // jeu de calibration (S-1)
  validation        : SourceRef?    // jeu de validation indépendant (S-1)
  applicability     : string        // domaine de validité (plage de diamètre, station, âge)

  // --- Projection ---
  time_step_years   : int           // pas de temps (années)
  max_horizon_years : int           // horizon maximal de projection
  outputs           : string[]      // variables de sortie projetées (ex: ["dbh", "height", "volume"])

  // --- Incertitude (S-5) ---
  uncertainty       : Range?        // incertitude de projection moyenne
  scenario          : string?       // scénario climatique associé si dépendant (RCP/SSP)

  // --- Traçabilité ---
  sources           : SourceRef[]   // publications, référentiels (S-1)
  evidence_level    : enum          // niveau de preuve (A-F) (S-2)
  version           : int           // numéro de version (CON-010)
  created_at        : ISO 8601
  updated_at        : ISO 8601
  history           : Commit[]      // historique des révisions (RFC-0003 §4)
}

ForestProjection {
  projection_id     : string        // identifiant stable (UUID v7)
  stand_id          : string        // peuplement projeté (référence Stand)
  model_id          : string        // modèle mobilisé (référence GrowthModel)

  // --- Paramètres de projection ---
  start_year        : int           // année de départ
  horizon_years     : int           // horizon de projection (années)
  intervention      : enum?         // plantation | eclaircie | coupe_rase | regeneration | none
  intensity         : string?       // intensité de l'intervention (ex: "20% prélèvement")
  climate_scenario  : string?       // scénario climatique (RCP/SSP) (S-5)

  // --- Résultats projetés ---
  time_series       : ProjectionPoint[]  // série temporelle projetée
  outputs           : string[]      // variables projetées (ex: ["dbh", "height", "volume", "basal_area"])

  // --- Incertitude (S-5) ---
  uncertainty       : Range?        // incertitude globale de projection
  confidence        : float         // 0.0-1.0

  // --- Traçabilité ---
  sources           : SourceRef[]   // modèle + données d'entrée (S-1)
  evidence_level    : enum          // niveau de preuve (A-F) (S-2)
  produced_at       : ISO 8601
  trace_id          : UUID v7       // chaîne de trace (CON-004)
  version           : int           // numéro de version (CON-010)
  history           : Commit[]      // historique des révisions (RFC-0003 §4)
}

ProjectionPoint {
  year              : int           // année projetée
  values            : dict          // variables projetées (nom → valeur ou Range)
  uncertainty       : Range?        // incertitude à ce pas (S-5)
}
```

### 3.4 Entités de raisonnement

#### Observation terrain

```
Observation {
  observation_id  : string        // identifiant stable
  station_id      : string?       // station concernée
  tree_id         : string?       // arbre concerné (si applicable)
  observer_id     : string        // identifiant de l'observateur
  observed_at     : ISO 8601      // date et heure
  location        : GeoJSON Point // localisation GPS

  // --- Contenu ---
  observation_type: enum          // dendrometrie | sanitaire | floristique | pedologique | phénologique
  values          : dict          // valeurs mesurées (typées par observation_type)
  protocol        : string        // protocole de référence (ONF, IGN)
  photos          : string[]?     // identifiants de photos

  // --- Traçabilité ---
  sources         : SourceRef[]   // observation terrain (S-1, catégorie 5)
  evidence_level  : enum          // F par défaut (observation isolée)
  device_id       : string?       // nœud émetteur (RFC-0003)
  offline         : boolean       // produit hors-ligne ?
  version         : int
  history         : Commit[]
}
```

#### Evidence (preuve)

```
Evidence {
  evidence_id     : string        // identifiant stable
  knowledge_id    : string        // connaissance concernée

  // --- Évaluation ---
  evidence_level  : enum          // A=Prouvé → F=Observation (S-2)
  confidence      : float         // 0.0 à 1.0
  conflicts       : Conflict[]?   // conflits bibliographiques détectés (S-3)

  // --- Décision ---
  evaluated_by    : string        // Evidence Engine (trace)
  evaluated_at    : ISO 8601
  decision_trace  : TraceEntry[]  // chaîne de décision (CON-004)

  // --- Traçabilité ---
  version         : int
  history         : Commit[]
}

Conflict {
  source_a        : SourceRef     // source A
  source_b        : SourceRef     // source B
  description     : string        // description du conflit
  resolution      : enum          // none | manual | rfc (S-3)
}
```

#### KnowledgeItem (connaissance qualifiée)

```
KnowledgeItem {
  knowledge_id    : string        // identifiant stable et citable (S-7)
  concept         : string        // concept ontologique (ex: "autécologie.chene_sessile")
  domain          : enum          // ecologie | pedologie | climatologie | botanique | sylviculture | …

  // --- Contenu ---
  statement       : string        // énoncé de la connaissance
  values          : dict          // valeurs structurées (typées par concept)
  unit            : string?       // unité si applicable

  // --- Relations ---
  relations       : Relation[]    // relations vers d'autres KnowledgeItems

  // --- Traçabilité ---
  sources         : SourceRef[]   // sources (S-1)
  evidence_id     : string        // référence vers Evidence (preuve)
  evidence_level  : enum          // niveau de preuve (S-2) — redondé pour accès rapide
  uncertainty     : Range?        // incertitude (S-5)

  // --- Versioning ---
  version         : int           // numéro de version (CON-010, S-7)
  status          : enum          // active | superseded | disputed
  superseded_by   : string?       // identifiant de la version de remplacement
  created_at      : ISO 8601
  updated_at      : ISO 8601
  history         : Commit[]      // historique complet des révisions (S-4)
}

Relation {
  relation_type   : string        // est_adapté_à | influence | dépend_de | est_validé_par | contredit
  target_id       : string        // identifiant du KnowledgeItem cible
  strength        : float?        // force de la relation (0.0-1.0) si quantifiable
  source          : SourceRef     // source de la relation (S-1)
}
```

#### Correlation

```
Correlation {
  correlation_id  : string
  source_entities : string[]      // entités corrélées (station_ids, tree_ids, etc.)
  correlation_type: string        // ex: "station_sol_essence"
  matrix          : dict          // matrice de corrélations justifiées

  // --- Traçabilité ---
  sources         : SourceRef[]   // sources des données croisées (S-1)
  evidence_level  : enum
  computed_at     : ISO 8601
  trace_id        : UUID v7       // chaîne de trace
  version         : int
  history         : Commit[]
}
```

#### Diagnostic

```
Diagnostic {
  diagnostic_id   : string
  station_id      : string        // station diagnostiquée
  diagnostic_type : enum          // stationnel | sylvicole | sanitaire

  // --- Contenu ---
  constraints     : DiagnosticItem[]  // contraintes identifiées
  assets          : DiagnosticItem[]  // atouts identifiés
  risks           : DiagnosticItem[]  // risques identifiés
  summary         : string            // synthèse (français)

  // --- Confiance ---
  confidence      : float             // 0.0-1.0
  uncertainties   : Uncertainty[]     // incertitudes documentées (S-5)

  // --- Traçabilité ---
  sources         : SourceRef[]       // sources mobilisées (S-1)
  evidence_level  : enum              // niveau de preuve global
  reasoning_trace : TraceEntry[]      // chaîne de raisonnement (CON-004)
  produced_at     : ISO 8601
  trace_id        : UUID v7
  version         : int
  history         : Commit[]
}

DiagnosticItem {
  label           : string
  description     : string
  severity        : enum          // info | minor | moderate | major | critical
  source_refs     : SourceRef[]   // sources justifiant l'item
  evidence_level  : enum
}

Uncertainty {
  description     : string        // source d'incertitude (S-5)
  quantified      : Range?        // quantification si possible
  impact          : string        // impact sur le diagnostic
}
```

#### Recommendation

```
Recommendation {
  recommendation_id: string
  diagnostic_id    : string       // diagnostic source

  // --- Contenu ---
  action          : string        // action recommandée (ex: "éclaircie mixte")
  rationale       : string        // justification (CON-004)
  alternatives    : Alternative[] // alternatives proposées (pas une seule option)
  expected_outcome: string        // résultat attendu

  // --- Confiance ---
  confidence      : float
  evidence_level  : enum          // niveau de preuve (S-2)
  uncertainties   : Uncertainty[]

  // --- Contournabilité (CON-001) ---
  status          : enum          // proposed | accepted | refused | modified
  user_feedback   : string?       // retour du forestier
  refused_reason  : string?       // motif de refus si applicable

  // --- Traçabilité ---
  sources         : SourceRef[]
  simulation_ids  : string[]?     // simulations mobilisées
  produced_at     : ISO 8601
  trace_id        : UUID v7
  version         : int
  history         : Commit[]
}

Alternative {
  action          : string
  rationale       : string
  tradeoffs       : string        // compromis vs recommandation principale
  evidence_level  : enum
}
```

#### SimulationScenario

```
SimulationScenario {
  scenario_id     : string
  station_id      : string
  recommendation_id: string?      // recommandation associée (si applicable)

  // --- Paramètres ---
  intervention    : enum          // plantation | eclaircie | coupe_rase | regeneration | none
  intensity       : string?       // intensité (ex: "20% prélèvement")
  horizon_years   : int           // horizon de projection (années)
  climate_scenario: string?       // scénario climatique (RCP/SSP) (S-5)

  // --- Résultats ---
  projections     : dict          // projections (biomasse, croissance, risque)
  risks           : RiskAssessment[]  // évaluation des risques

  // --- Traçabilité ---
  sources         : SourceRef[]   // modèles mobilisés (Forest Dynamics, Climate)
  evidence_level  : enum
  uncertainty     : Range?        // incertitude de projection (S-5)
  produced_at     : ISO 8601
  trace_id        : UUID v7
  version         : int
  history         : Commit[]
}

RiskAssessment {
  risk_type       : enum          // climatique | sanitaire | economique | écologique
  probability     : float         // 0.0-1.0
  impact          : enum          // faible | modéré | élevé | critique
  description     : string
  source          : SourceRef
}
```

### 3.5 Entités de sortie

Les entités de sortie sont les produits structurés destinés à
l'utilisateur et aux clients du moteur. Elles agrègent et formalisent
les résultats du pipeline (diagnostic, recommandation, simulation) en
gardant une traçabilité complète (S-1 à S-7, CON-004, CON-010).

#### DiagnosticReport

L'entité **DiagnosticReport** est le rapport de diagnostic final
remis au client. Elle agrège un ou plusieurs `Diagnostic` et présente
les conclusions de manière lisible et citable.

```
DiagnosticReport {
  report_id         : string          // identifiant stable (UUID v7)
  station_id        : string          // station concernée
  diagnostic_ids    : string[]        // diagnostics agrégés (références Diagnostic)

  // --- Contenu ---
  title             : string          // titre du rapport (français)
  summary           : string          // synthèse exécutive (français)
  constraints       : DiagnosticItem[]  // contraintes identifiées
  assets            : DiagnosticItem[]  // atouts identifiés
  risks             : DiagnosticItem[]  // risques identifiés
  findings          : Finding[]       // conclusions structurées

  // --- Confiance ---
  confidence        : float           // 0.0-1.0
  evidence_level    : enum            // niveau de preuve global (S-2)
  uncertainties     : Uncertainty[]   // incertitudes documentées (S-5)

  // --- Traçabilité ---
  sources           : SourceRef[]     // sources mobilisées (S-1)
  reasoning_trace   : TraceEntry[]    // chaîne de raisonnement (CON-004)
  produced_at       : ISO 8601
  produced_by       : string          // moteur ou utilisateur émetteur
  trace_id          : UUID v7
  version           : int             // numéro de version (CON-010)
  history           : Commit[]        // historique des révisions (RFC-0003 §4)
}

Finding {
  label             : string          // intitulé de la conclusion
  description       : string          // description (français)
  severity          : enum            // info | minor | moderate | major | critical
  source_refs       : SourceRef[]     // sources justifiant (S-1)
  evidence_level    : enum            // niveau de preuve (S-2)
}
```

#### RecommendationSet

L'entité **RecommendationSet** est l'ensemble structuré de
recommandations remis au décideur (forestier). Elle agrège un ou
plusieurs `Recommendation` et explicite les alternatives et la
contournabilité (CON-001).

```
RecommendationSet {
  set_id            : string          // identifiant stable (UUID v7)
  report_id         : string?         // rapport de diagnostic associé
  recommendation_ids: string[]        // recommandations agrégées (références Recommendation)

  // --- Contenu ---
  title             : string          // titre (français)
  summary           : string          // synthèse (français)
  primary           : Recommendation  // recommandation principale
  alternatives      : Alternative[]   // alternatives proposées (pas une seule option)
  expected_outcomes : string[]        // résultats attendus par recommandation

  // --- Confiance ---
  confidence        : float           // 0.0-1.0
  evidence_level    : enum            // niveau de preuve global (S-2)
  uncertainties     : Uncertainty[]   // incertitudes documentées (S-5)

  // --- Contournabilité (CON-001) ---
  status            : enum            // proposed | accepted | refused | modified
  user_feedback     : string?         // retour du forestier
  refused_reason    : string?         // motif de refus si applicable

  // --- Traçabilité ---
  sources           : SourceRef[]     // sources mobilisées (S-1)
  simulation_ids    : string[]?       // simulations mobilisées
  produced_at       : ISO 8601
  produced_by       : string
  trace_id          : UUID v7
  version           : int             // numéro de version (CON-010)
  history           : Commit[]        // historique des révisions (RFC-0003 §4)
}
```

#### SimulationResult

L'entité **SimulationResult** est le résultat structuré d'une
simulation remis au client. Elle formalise les projections d'un
`SimulationScenario` (et/ou `ForestProjection`) avec leurs
incertitudes.

```
SimulationResult {
  result_id         : string          // identifiant stable (UUID v7)
  scenario_id       : string          // scénario source (référence SimulationScenario)
  projection_ids    : string[]?       // projections Forest Dynamics mobilisées

  // --- Contenu ---
  title             : string          // titre (français)
  summary           : string          // synthèse (français)
  projections       : ProjectionPoint[]  // série temporelle projetée
  outputs           : string[]        // variables projetées
  risks             : RiskAssessment[]   // évaluation des risques

  // --- Confiance ---
  confidence        : float           // 0.0-1.0
  evidence_level    : enum            // niveau de preuve global (S-2)
  uncertainty       : Range?          // incertitude globale de projection (S-5)

  // --- Traçabilité ---
  sources           : SourceRef[]     // modèles et données mobilisés (S-1)
  produced_at       : ISO 8601
  produced_by       : string
  trace_id          : UUID v7
  version           : int             // numéro de version (CON-010)
  history           : Commit[]        // historique des révisions (RFC-0003 §4)
}
```

---

## 4. Relations entre entités

### 4.1 Graphe des relations

```
Parcelle ──contient──▶ Station ──a_pour_sol──▶ Sol
    │                     │
    │                     ├──a_pour_climat──▶ Climat
    │                     │
    ├──contient──▶ Arbre ──est_de_l_essence──▶ Essence
    │                     │
    │                     ├──fait_objet_de──▶ Observation
    │                     │
    ├──compose──▶ Peuplement ──est_projete_par──▶ ForestProjection
    │                  │                              │
    │                  └──utilise──▶ GrowthModel ─────┘
    │
    └──fait_objet_de──▶ Diagnostic ──produit──▶ Recommendation
                                              │
                                    ──évaluée_par──▶ SimulationScenario
                                    │
                          Validation Engine (validation, pas entité)

Diagnostic ──agrégé_dans──▶ DiagnosticReport
Recommendation ──agrégé_dans──▶ RecommendationSet
SimulationScenario ──formalisé_dans──▶ SimulationResult

KnowledgeItem ──est_preuvé_par──▶ Evidence
     │
     ├──est_en_relation_avec──▶ KnowledgeItem (Relation)
     │
     ──mobilisé_par──▶ Correlation ──alimente──▶ Reasoning ──▶ Diagnostic
```

### 4.2 Cardinalités

| Relation | Source | Cible | Cardinalité |
|---|---|---|---|
| Station → Sol | Station | Sol | 1 → 1 (ou 0..n pour sols complexes) |
| Station → Climat | Station | Climat | 1 → 1 |
| Station → Parcelle | Station | Parcelle | 1 → 0..n |
| Parcelle → Arbre | Parcelle | Arbre | 1 → 0..n |
| Arbre → Essence | Arbre | Essence | n → 1 |
| Arbre → Observation | Arbre | Observation | 1 → 0..n |
| Station → Peuplement | Station | Peuplement | 1 → 0..n |
| Parcelle → Peuplement | Parcelle | Peuplement | 1 → 0..n |
| Peuplement → Arbre | Peuplement | Arbre | 1 → 0..n |
| Peuplement → GrowthModel | Peuplement | GrowthModel | n → 0..1 |
| GrowthModel → ForestProjection | GrowthModel | ForestProjection | 1 → 0..n |
| Peuplement → ForestProjection | Peuplement | ForestProjection | 1 → 0..n |
| Station → Diagnostic | Station | Diagnostic | 1 → 0..n |
| Diagnostic → Recommendation | Diagnostic | Recommendation | 1 → 0..n |
| Recommendation → SimulationScenario | Recommendation | SimulationScenario | 1 → 0..n |
| Diagnostic → DiagnosticReport | Diagnostic | DiagnosticReport | n → 1 |
| Recommendation → RecommendationSet | Recommendation | RecommendationSet | n → 1 |
| SimulationScenario → SimulationResult | SimulationScenario | SimulationResult | 1 → 0..n |
| KnowledgeItem → Evidence | KnowledgeItem | Evidence | 1 → 1 |
| KnowledgeItem → KnowledgeItem (Relation) | KnowledgeItem | KnowledgeItem | n → n |

---

## 5. Sources de données

Chaque source est citée et catégorisée selon S-1. Aucune donnée
n'entre dans le système sans source identifiée.

### 5.1 Sources géospatiales (GIS Engine)

| Source | Type (S-1) | Données fournies | Référence |
|---|---|---|---|
| **IGN — Géoportail / BD Ortho** | Référentiel officiel | Orthophotos, MNT, limites parcellaires | `https://www.ign.fr/` |
| **IGN — BD Forêt** | Référentiel officiel | Types de peuplement, essences dominantes | `https://www.ign.fr/institut/bd-foret` |
| **Cadastre — data.gouv.fr** | Référentiel officiel | Parcelles cadastrales, propriétaires | `https://www.data.gouv.fr/` |
| **LiDAR HD (IGN)** | Référentiel officiel | Modèles numériques de terrain haute résolution | `https://geoservices.ign.fr/lidarhd` |

### 5.2 Sources climatiques (Climate Engine)

| Source | Type (S-1) | Données fournies | Référence |
|---|---|---|---|
| **Météo-France** | Référentiel officiel | Données climatiques historiques (températures, précipitations) | `https://meteofrance.com/` |
| **DRIAS — Météo-France / IPSL** | Référentiel officiel | Projections climatiques régionalisées (RCP/SSP) | `https://www.drias-climat.fr/` |
| **GIEC / IPCC** | Publication peer-reviewed | Scénarios climatiques (RCP, SSP), incertitudes | `https://www.ipcc.ch/` |

### 5.3 Sources pédologiques (Pedology Engine)

| Source | Type (S-1) | Données fournies | Référence |
|---|---|---|---|
| **Référentiel Pédologique Français (RPF)** | Référentiel officiel | Classification des sols, seuils (pH, texture, drainage) | INRAE — Éditions Quae |
| **WRB — World Reference Base** | Référentiel officiel | Classification internationale des sols | FAO / IUSS |
| **Base de Données des Sols (BDETM)** | Référentiel officiel | Données pédologiques spatialisées | INRAE / GIS Sol |

### 5.4 Sources botaniques (Botanical Engine)

| Source | Type (S-1) | Données fournies | Référence |
|---|---|---|---|
| **BDNFF — Base de Données Nomenclaturale de la Flore de France** | Référentiel officiel | Nomenclature, synonymes, taxonomie | Tela Botanica / INRAE |
| **Tela Botanica** | Référentiel officiel | Flore, autécologie, clés de détermination | `https://www.tela-botanica.org/` |
| **GBIF — Global Biodiversity Information Facility** | Référentiel officiel | Occurrences, taxonomie mondiale | `https://www.gbif.org/` |
| **INRAE — autécologie des essences** | Publication peer-reviewed / Référentiel | Autécologie (optimum, amplitude, exigences) | INRAE — publications |

### 5.5 Sources sylvicoles et forestières

| Source | Type (S-1) | Données fournies | Référence |
|---|---|---|---|
| **ONF — Guides sylvicoles** | Document technique validé | Protocoles, recommandations sylvicoles, guides de gestion | `https://www.onf.fr/` |
| **IGN — Inventaire forestier national** | Référentiel officiel | Inventaires, volumes, accroissements | `https://www.ign.fr/institut/inventaire-forestier-national` |
| **INRAE — modèles de croissance** | Publication peer-reviewed | Modèles de croissance et de production | INRAE — publications |

### 5.6 Sources scientifiques (Evidence Engine)

| Source | Type (S-1) | Données fournies | Référence |
|---|---|---|---|
| **Publications peer-reviewed** | Publication peer-reviewed | Connaissances scientifiques (écologie, pédologie, climatologie) | DOI, revues indexées |
| **Observations terrain (GSIE)** | Observation terrain | Mesures, observations directes, datées, localisées | Protocoles GSIE/ONF/IGN |

> **Règle (S-1) :** toute source non listée dans l'une de ces
> catégories est exclue. Les sources sont référencées dans
> `06_RESEARCH/` et les jeux de données dans `08_DATASETS/`.

---

## 6. Versioning des données scientifiques

### 6.1 Modèle de versioning (CON-010, S-7, T-6)

Chaque entité scientifique est versionnée selon le modèle « commit »
(RFC-0003 §4). Une modification produit un **commit** sur l'entité
identifiée, pas un écrasement.

```
Entité (identifiant stable)
  ├── Version 1 (création)     — commit #1
  ├── Version 2 (révision)     — commit #2 (référence commit #1)
  ├── Version 3 (révision)     — commit #3 (référence commit #2)
  └── ...
```

### 6.2 Structure d'un Commit

```
Commit {
  commit_id       : UUID v7       // identifiant unique du commit
  entity_id       : string        // entité modifiée
  entity_type     : enum          // station | parcelle | tree | stand | soil | climate | species | growth_model | forest_projection | diagnostic | recommendation | simulation_scenario | diagnostic_report | recommendation_set | simulation_result | ...
  parent_commit   : UUID v7?      // commit parent (null si création)
  author          : string        // auteur (utilisateur ou moteur)
  timestamp       : ISO 8601      // horodatage
  changes         : FieldChange[] // champs modifiés
  reason          : string        // motif de la modification (CON-004)
  source          : SourceRef?    // source justifiant la modification (S-1)
  device_id       : string?       // nœud émetteur (RFC-0003)
  offline         : boolean       // produit hors-ligne ?
  sync_status     : enum          // local | synced | conflict
}

FieldChange {
  field           : string        // nom du champ modifié
  old_value       : any?          // ancienne valeur (null si création)
  new_value       : any           // nouvelle valeur
}
```

### 6.3 Propriétés du versioning

| Propriété | Garantie | Référence |
|---|---|---|
| **Immuabilité** | Un commit n'est jamais modifié ni supprimé | CON-010 |
| **Réversibilité** | On peut revenir à toute version antérieure | S-7, CON-010 |
| **Citabilité** | Chaque entité a un identifiant stable et citable | S-7 |
| **Traçabilité** | Chaque modification a un auteur, un motif et une source | CON-005, S-1 |
| **Synchronisation** | Les commits se synchronisent inter-nœuds (RFC-0003 §4) | T-8 |

### 6.4 Révision des connaissances (S-4)

Une connaissance (KnowledgeItem) peut être révisée lorsque :

- sa source est invalidée par la communauté scientifique ;
- une nouvelle publication contredit significativement la
  connaissance existante ;
- le consensus scientifique évolue.

La procédure de révision (S-4) :

1. **Identification** du besoin de révision ;
2. **Création d'une RFC** de révision ;
3. **Évaluation** par l'Evidence Engine de la nouvelle source ;
4. **Mise à jour versionnée** — l'ancienne version est conservée
   avec `status = superseded`, la nouvelle avec
   `superseded_by = null` ;
5. **Mise à jour de la traçabilité** — le commit de révision
   référence le motif et la source.

L'ancienne version n'est **jamais supprimée** (CON-010). Elle reste
consultable et citable.

### 6.5 Conflits de versions (synchronisation)

Lorsqu'un même entité est modifiée sur deux nœuds hors-ligne
(RFC-0003 §4), la synchronisation peut produire un conflit. La
résolution suit les règles définies dans
`ENGINE_COMMUNICATION_PROTOCOL.md` §6.4 :

- champs différents → merge automatique ;
- même champ, valeurs différentes → conflit documenté, résolution
  manuelle ou par règle métier (S-3 : pas de fusion arbitraire) ;
- suppression vs modification → préservation de la modification
  (CON-010).

---

## 7. Types de données communs

### 7.1 Range (intervalle)

De nombreuses données scientifiques sont des intervalles (min-max)
pour exprimer la variabilité naturelle ou l'incertitude (S-5).

```
Range {
  min             : float         // borne inférieure
  max             : float         // borne supérieure
  unit            : string        // unité (ex: "°C", "mm", "cm")
  confidence      : float?        // niveau de confiance (0.0-1.0) si applicable
}
```

### 7.2 SourceRef (référence de source)

Défini dans `ENGINE_COMMUNICATION_PROTOCOL.md` §3.4. Rappel :

```
SourceRef {
  source_id       : string
  source_type     : enum          // publication | referentiel | technique | expert | observation
  citation        : string        // citation bibliographique complète
  url             : string?
  accessed_at     : ISO 8601
  version         : string?       // version du référentiel
}
```

### 7.3 TraceEntry (entrée de trace)

```
TraceEntry {
  step            : string        // étape du pipeline (ex: "evidence.qualify")
  engine          : string        // moteur responsable
  timestamp       : ISO 8601
  description     : string        // description de l'étape (français)
  inputs          : string[]?     // identifiants des entrées
  outputs         : string[]?     // identifiants des sorties
  evidence_level  : enum?         // niveau de preuve à cette étape
}
```

---

## 8. Contraintes d'intégrité

Les contraintes ci-dessous sont des règles de validation applicables
au moment de l'ingestion et de la révision des entités. Elles
complètent les principes de traçabilité (S-1 à S-7) et garantissent la
cohérence scientifique des données. Une entité non conforme est rejetée
ou marquée comme `disputed` (S-3) selon la gravité.

### 8.1 Contraintes géospatiales et stationnelles

| Entité | Champ | Règle | Référence |
|---|---|---|---|
| Station | `altitude_m` | `min > 0` et `max >= min` (sauf altitude négative sous niveau marin, documentée) | S-5 |
| Station | `slope_deg` | `min >= 0` et `max <= 90` et `max >= min` | — |
| Station | `aspect` | valeur parmi `N, NE, E, SE, S, SW, W, NW, plat` | — |
| Station | `drainage` | valeur parmi `bon, modéré, imparfait, mauvais, nul` | — |
| Station | `geometry` | SRU WGS84 ou Lambert-93, polygone ou point valide | RFC-0003 |
| Station | `sources` | au moins une `SourceRef` (S-1) | S-1 |
| Parcelle | `area_ha` | `> 0` | — |
| Parcelle | `geometry` | polygone fermé, Lambert-93 | — |
| Parcelle | `station_id` | référence existante ou `null` | — |
| Arbre | `dbh_cm` | `min > 0` et `max >= min` | — |
| Arbre | `height_m` | `min > 0` et `max >= min` | — |
| Arbre | `vitality` | entier `0` à `5` si renseigné | — |
| Arbre | `sanitary_status` | valeur parmi `sain, dépérissant, mort, malade` si renseigné | — |
| Arbre | `species_id` | référence vers `Species` existante | — |
| Arbre | `measured_at` | date <= date courante | — |

### 8.2 Contraintes domaine

| Entité | Champ | Règle | Référence |
|---|---|---|---|
| Sol | `ph` | `min >= 0` et `max <= 14` et `max >= min` | — |
| Sol | `depth_cm` | `min >= 0` et `max >= min` | — |
| Sol | `water_reserve_mm` | `min >= 0` et `max >= min` | — |
| Sol | `texture` | valeur parmi `sableux, limoneux, argileux, mixte` | — |
| Sol | `drainage` | valeur parmi `bon, modéré, imparfait, mauvais, nul` | — |
| Climat | `temp_mean_c` | `max >= min` (pas de borne absolue, projection possible) | S-5 |
| Climat | `precip_mm` | `min >= 0` et `max >= min` | — |
| Climat | `period` | format `"AAAA-AAAA"` avec `fin >= début` | — |
| ClimateProjection | `horizon` | année entière >= année courante | — |
| ClimateProjection | `uncertainty` | `min <= max` (S-5) | S-5 |
| Species | `scientific_name` | non vide, référentiel BDNFF | — |
| Species | `soil_ph_range` | `min >= 0` et `max <= 14` | — |
| Species | `light_requirement` | valeur parmi `héliophile, demi-ombre, ombrophile` | — |
| Stand | `density` | `>= 0` | — |
| Stand | `basal_area_m2` | `>= 0` | — |
| Stand | `age_mean` | `min >= 0` et `max >= min` | — |
| Stand | `composition` | somme des `share` <= 1.0 (ou 100 %) selon `share_type` | — |
| Stand | `dominant_species` | présente dans `composition` | — |
| GrowthModel | `time_step_years` | `> 0` | — |
| GrowthModel | `max_horizon_years` | `>= time_step_years` | — |
| GrowthModel | `species_ids` | au moins une essence couverte | — |
| ForestProjection | `horizon_years` | `> 0` et `<= model.max_horizon_years` | — |
| ForestProjection | `start_year` | année entière | — |

### 8.3 Contraintes de raisonnement et de sortie

| Entité | Champ | Règle | Référence |
|---|---|---|---|
| Observation | `observed_at` | date <= date courante | — |
| Observation | `location` | point GeoJSON valide | — |
| Evidence | `evidence_level` | valeur parmi `A, B, C, D, E, F` (S-2) | S-2 |
| Evidence | `confidence` | `0.0 <= x <= 1.0` | — |
| KnowledgeItem | `concept` | non vide, ontologie référencée | S-7 |
| KnowledgeItem | `sources` | au moins une `SourceRef` (S-1) | S-1 |
| KnowledgeItem | `status` | valeur parmi `active, superseded, disputed` | S-4 |
| Correlation | `source_entities` | au moins deux entités | — |
| Diagnostic | `confidence` | `0.0 <= x <= 1.0` | — |
| Diagnostic | `station_id` | référence existante | — |
| Recommendation | `confidence` | `0.0 <= x <= 1.0` | — |
| Recommendation | `diagnostic_id` | référence existante | — |
| Recommendation | `alternatives` | au moins une alternative proposée (pas une seule option) | CON-001 |
| SimulationScenario | `horizon_years` | `> 0` | — |
| SimulationScenario | `intensity` | non vide si `intervention != none` | — |
| DiagnosticReport | `diagnostic_ids` | au moins un diagnostic agrégé | — |
| DiagnosticReport | `evidence_level` | valeur parmi `A` à `F` (S-2) | S-2 |
| RecommendationSet | `recommendation_ids` | au moins une recommandation agrégée | — |
| RecommendationSet | `primary` | présente parmi les recommandations agrégées | — |
| SimulationResult | `scenario_id` | référence existante | — |
| SimulationResult | `projections` | au moins un `ProjectionPoint` | — |

### 8.4 Contraintes transverses (traçabilité et versioning)

| Règle | Portée | Référence |
|---|---|---|
| Toute entité scientifique porte au moins une `SourceRef` | toutes | S-1 |
| Toute entité scientifique porte un `evidence_level` (A-F) | toutes | S-2 |
| Toute entité a un identifiant stable et un `version` >= 1 | toutes | CON-010, S-7 |
| Toute entité a un `history` de `Commit` non vide après création | toutes | RFC-0003 §4 |
| Toute donnée quantitative porte son incertitude si applicable | toutes (champs `Range`) | S-5 |
| Aucune fusion arbitraire en cas de conflit de sources | toutes | S-3 |
| Un `Commit` n'est jamais modifié ni supprimé | versioning | CON-010 |

---

## 9. Ce que ce document ne fait PAS

- Il n'implémente aucun code (Phase 2 — interdit, DEC-000004).
- Il ne définit pas le schéma physique de base de données (SQLite /
  PostgreSQL — Phase 3/4).
- Il ne liste pas exhaustivement toutes les sources scientifiques
  (voir `06_RESEARCH/` et `08_DATASETS/`).
- Il ne définit pas les contrats d'interface détaillés par moteur
  (livrable 206).
- Il ne contredit aucun article constitutionnel.

---

## 10. Historique

| Date | Événement |
|---|---|
| 2026-07-01 | Création — version squelette (Phase 1, 7 champs génériques) |
| 2026-07-12 | Enrichissement Phase 2 — entités, relations, sources citées, versioning par commits |
| 2026-07-12 | Correction audit — ajout Peuplement (Stand), Forest Dynamics (GrowthModel, ForestProjection), entités de sortie (DiagnosticReport, RecommendationSet, SimulationResult), contraintes d'intégrité |

---

## 11. Validation

Document en statut **Draft**. Passage en `Review` soumis à
validation du Fondateur. Aucune modification destructive sans
versionnement préalable (CON-010, T-6).

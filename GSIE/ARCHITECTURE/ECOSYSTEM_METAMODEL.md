# ECOSYSTEM_METAMODEL — Métamodèle de l'Encyclopédie de l'Écosystème GSIE

| Champ | Valeur |
|---|---|
| **Livrable** | 213 — Métamodèle de l'Écosystème (v6.2) |
| **Phase** | 4 — Implémentation |
| **Statut** | Proposé (soumis à RFC-0011) |
| **Date de révision** | 2026-07-15 |
| **Lois fondatrices** | GSIE-CON-002, GSIE-CON-003, GSIE-CON-005, GSIE-CON-010 |
| **Constitutions liées** | Scientifique (S-1 à S-7), Technique (T-1, T-2) |
| **Directive d'ouverture** | GSIE-DIR-0008 (amendée par DEC-000022) |
| **RFC liée** | RFC-0011 (en cours d'adoption) |
| **Décision liée** | DEC-000022 (Proposé) |
| **Documents supersédés** | 302 (Knowledge Method), 304 (Knowledge Graph Spec), 309 (Encyclopedia DB Schema), 310 (Engine Data Socle) — voir RFC-0011 annexes |
| **Documents connexes** | 205 (Scientific Data Model, Draft), 206 (Engine Interface Contracts, Draft), 305 (Dataset Catalog, Validated), 306 (Evidence Framework, Validated), 308 (Knowledge Base Seed, Validated) |
| **Version précédente** | v6.1 (42 types, intégrée dans v6.2) → v5 (archivée dans `22_PROJECT_MEMORY/SUPERSEDED_DRAFTS/`, non adoptée) |

> **⚠️ Avertissement de gouvernance — document en cours de rédaction, rien n'est adopté.**
> À la date de cette révision, **`RFC-0011.md` n'existe pas** dans `02_RFC/` et **`DEC-000022.md`
> n'existe pas** dans `03_DECISIONS/`. Les mentions ci-dessus (« amendée par DEC-000022 »,
> « RFC-0011 en cours d'adoption », « DEC-000022 (Proposé) », « Documents supersédés : 302,
> 304, 309, 310 ») décrivent l'**intention du paquet en préparation** (RFC-0011 + DEC-000022 +
> ADRs, rédigés ensemble), pas un fait acquis. Les livrables 302, 304, 309 et 310 restent
> `Validated` et inchangés tant que RFC-0011 n'est pas déposée et DEC-000022 non adopté par le
> Fondateur. Ne pas citer ce document comme source d'une décision déjà prise.

---

## 1. Objet

Définir le métamodèle de l'Encyclopédie de l'Écosystème GSIE : la
structure conceptuelle universelle qui permet de représenter flore,
faune, sols, climat, hydrologie, pathologies, interactions écologiques,
modèles, simulations, décisions et observations de terrain — le tout
sourcé, versionné et traçable.

Ce métamodèle remplace la structure `KnowledgeObject` à 6 types
(livrable 302) par un noyau universel de **73 types** organisés en cinq
niveaux. Il corrige les contradictions identifiées par l'audit v6.1
(voir RFC-0011), intègre les arbitrages du Fondateur, et enrichit la
v6.1 (42 types) avec 18 types supplémentaires issus de la passe
écologique du Fondateur (v6.2) + 1 type pour le Temporal Engine
(ResourceDiff, type 61) + 4 types pour l'audit FAIR/RGPD/SOSA (types
62-65 : Sample, Consent, DataSubject, PersistentIdentifier) + 8 types
pour la passe dynamiques écologiques (types 66-73 : Flow,
ConfidenceGraph, Goal, Constraint, KnowledgeLineage, Experiment,
TerrainSession, EcologicalState).
écologique du Fondateur (v6.2) : ScaleContext, Phenomenon,
EcologicalProcess, RelationType, SamplingEvent, TraitDefinition,
TraitValue, Feature, FeatureSet, Inference, Question, Hypothesis,
Decision, Recommendation, Scenario, Correlation, EcosystemService,
Capability.

### 1.1 Principes directeurs

| Principe | Source | Traduction |
|---|---|---|
| Tout objet avec identité, histoire ou relations propres peut devenir une entité | Arbitrage Fondateur | `Entity` comme racine conceptuelle |
| Toute information sur un objet devient observation, assertion, événement, processus, mesure ou propriété contextualisée | Arbitrage Fondateur | Types `Observation`, `Assertion`, `Activity`, `Result` |
| Aucune FK polymorphe `target_type/target_id` | Audit F-P1-03 | Racine `Resource` unique, FK fortes vers `resource.id` |
| Bitemporalité complète (valid_time + transaction_time) | Audit F-P1-02 | `TemporalContext` + **GSIE Temporal & Provenance Engine** (Revision + Snapshot + ResourceDiff + PROV-O, ADR-002) |
| Absence observée distincte d'absence de donnée | Audit F-P0-05 | `Result.value_type='absence'` + `sampling_effort` |
| Distinction épistémologique des claims | Audit F-P1-01 | `claim_kind` séparé de `lifecycle_status` |
| Indépendance vis-à-vis des API (archivage local) | Arbitrage Fondateur | `DataAsset.archived_from` + `Distribution.access_method` |
| Confidentialité et souveraineté des données sensibles | Audit F-P1-05 | 4 types : `RightsStatement`, `AccessPolicy`, `SensitivityClassification`, `SpatialDisclosurePolicy` |
| PostgreSQL 16 + PostGIS comme vérité canonique | Arbitrage Fondateur | AGE/Neo4j/Jena/ES = projections différées (benchmark Vague 1) |
| Toute corrélation écologique dépend de l'échelle | Passe écologique Fondateur v6.2 | `ScaleContext` comme contexte de premier ordre (comme Place et TemporalContext) |
| Les phénomènes écologiques ne sont ni entités, ni observations, ni activités PROV | Passe écologique Fondateur v6.2 | Type `Phenomenon` (sécheresse, scolytes, succession) distinct d'Entity, Observation et Activity |
| Les processus écologiques sont distincts des activités de provenance | Passe écologique Fondateur v6.2 | Type `EcologicalProcess` (photosynthèse, croissance) distinct de PROV `Activity` |
| GSIE est un moteur de raisonnement, pas seulement un stockage | Passe écologique Fondateur v6.2 | Couche raisonnement : `Question`, `Hypothesis`, `Decision`, `Recommendation`, `Scenario` |
| Les corrélations sont des objets de connaissance versionnés et évaluables | Passe écologique Fondateur v6.2 | Type `Correlation` avec method, confidence, strength, evidence |
| Les traits fonctionnels sont transversaux et comparables cross-species | Passe écologique Fondateur v6.2 | Types `TraitDefinition` + `TraitValue` distincts des Observations génériques |
| L'IA est un citoyen de premier ordre dans GSIE | Passe écologique Fondateur v6.2 | Types `Feature`, `FeatureSet`, `Inference` au noyau |
| Conformité FAIR (Findable, Accessible, Interoperable, Reusable) | Audit comparatif v6.2 | `PersistentIdentifier` (65) pour F1 ; plan FAIR §15.1 |
| Conformité RGPD (données personnelles) | Audit comparatif v6.2 | Types `Consent` (63) + `DataSubject` (64) ; plan RGPD §15.2 |
| Interopérabilité SOSA/SSN (W3C/OGC observations) | Audit comparatif v6.2 | Type `Sample` (62) + mapping SOSA/SSN §15.3 |
| Les écosystèmes fonctionnent par flux, pas seulement par relations | Passe dynamiques Fondateur v6.2 | Type `Flow` (66) — carbone, eau, nutriments, énergie, graines, gènes, pathogènes |
| L'incertitude scientifique est globale, pas par assertion isolée | Passe dynamiques Fondateur v6.2 | Type `ConfidenceGraph` (67) — propagation de confiance à travers les dépendances |
| Toute décision dépend d'objectifs et est limitée par des contraintes | Passe dynamiques Fondateur v6.2 | Types `Goal` (68) + `Constraint` (69) — orientent et limitent les recommandations |
| Le lignage de connaissance est un DAG explicite, pas seulement des citations | Passe dynamiques Fondateur v6.2 | Type `KnowledgeLineage` (70) — chaîne A → B → Recommendation → Decision |
| Un scientifique fait des séries de simulations, pas une simulation | Passe dynamiques Fondateur v6.2 | Type `Experiment` (71) — groupe de ModelRuns avec cadre de comparaison |
| Une mission terrain GeoSylva est plus large qu'un échantillonnage | Passe dynamiques Fondateur v6.2 | Type `TerrainSession` (72) — météo, GPS, matériel, martelage, inventaire, sync |
| L'état de santé d'un écosystème mérite une représentation synthétique | Passe dynamiques Fondateur v6.2 | Type `EcologicalState` (73) — santé, vitalité, risque, résilience, biodiversité |
| GSIE est un Knowledge Operating System, pas une base de données | Passe dynamiques Fondateur v6.2 | Document d'orchestration séparé (§9.4) — orchestration moteurs IA, physiques, statistiques, SIG |

### 1.2 Ce que ce document n'est pas

- Ce n'est pas un schéma physique SQL (voir ADR-001 à ADR-006)
- Ce n'est pas une spécification d'API (voir livrable 206, à amender)
- Ce n'est pas un profil métier (voir §7, profils différés en Vague 2+)
- Ce n'est pas une adoption définitive — statut **Proposé**, soumis à
  RFC-0011 puis vote Fondateur via DEC-000022

---

## 2. Architecture en cinq niveaux

Le métamodèle sépare explicitement cinq niveaux de préoccupation pour
éviter le mélange qui caractérisait la proposition v5 (110 classes).

```
Niveau A — Noyau universel (73 types)
    Types conceptuels indépendants du domaine forestier.
    Tout domaine (forêt, faune, eau, incendie) les réutilise.

Niveau B — Profils métier (différés Vague 2+)
    Spécialisations du noyau pour un domaine : Tree, Placette,
    SoilProfile, FireFront, CameraTrap, Martelage…
    Un profil ajoute des champs typés, pas de nouveaux types noyau.

Niveau C — Projections standards (différées)
    Mappings vers standards externes : STAC, OGC O&M, SensorThings,
    Darwin Core, PROV-O, DCAT/GeoDCAT-AP, ISO 19115.
    Ce sont des vues, pas des types fondamentaux.

Niveau D — Infrastructure (spécifiée, implémentation différée)
    ConnectorRegistry, OutboxEvent, ConsumerInbox, object storage.
    Spécifiés dans le métamodèle mais implémentés au fil du besoin.

Niveau E — Vision long terme (différée)
    Jumeaux numériques territoriaux, plugins dynamiques.
    Non spécifiés ici. (Les services écosystémiques sont désormais
    au noyau A via EcosystemService, type 59.)
```

### 2.1 Règle de séparation

Un type du noyau (A) ne peut pas référencer un type de profil (B). Un
profil (B) référence le noyau (A) et ajoute des champs spécifiques. Une
projection (C) est une vue en lecture sur le noyau. L'infrastructure (D)
manipule le noyau mais n'ajoute pas de types métier.

### 2.2 Stratification méta-architecturale (niveau 0)

GSIE n'est pas un projet classique — c'est une plateforme scientifique
ouverte destinée à intégrer de nouveaux domaines (forêt, hydrologie,
agriculture, biodiversité, climat, incendies) sans remettre en cause
les fondations. Cette ambition justifie une stratification
méta-architecturale explicite :

```
Niveau 0 — Universe (méta-méta)
    Cadre philosophique : ce qui existe, ce qui est connaissable.
    Non implémenté — c'est le cadre de pensée.

Niveau 1 — MetaOntology
    Comment on construit les concepts : règles de définition,
    de nommage, de versionnement. C'est ce que font les types
    Vocabulary, Concept, ConceptVersion, ControlledTerm du noyau.

Niveau 2 — Ontology
    Les concepts eux-mêmes : Quercus_robur, Alocrisol, sécheresse.
    Instances de la méta-ontologie. C'est ce que font les types
    Concept, ControlledTerm, TraitDefinition, RelationType.

Niveau 3 — MetaModel (ce document)
    Les types du noyau (73 types) qui structurent la connaissance.
    Définit comment on représente entités, observations, assertions,
    phénomènes, processus, corrélations, raisonnement.

Niveau 4 — Profiles (niveau B)
    Spécialisations par domaine : Tree, Placette, FireFront…

Niveau 5 — Applications
    GeoSylva, Ignis, Artemis, Hydro, Flora, QGISIA.
    Consomment le noyau + profils via l'API.
```

Cette stratification est **conceptuelle** — elle n'ajoute pas de tables
SQL. Elle guide la conception : les types du noyau (niveau 3) sont des
instances de la méta-ontologie (niveau 1), et les concepts du domaine
(niveau 2) sont des instances des types du noyau. Un nouveau domaine
(agriculture) ajoute des concepts (niveau 2) et un profil (niveau 4),
mais ne modifie pas le métamodèle (niveau 3).
```

### 2.1 Règle de séparation

Un type du noyau (A) ne peut pas référencer un type de profil (B). Un
profil (B) référence le noyau (A) et ajoute des champs spécifiques. Une
projection (C) est une vue en lecture sur le noyau. L'infrastructure (D)
manipule le noyau mais n'ajoute pas de types métier.

---

## 3. Niveau A — Noyau universel (73 types)

### 3.1 Racine relationnelle : `Resource`

Toute entité du noyau hérite de `Resource` — une table racine unique
avec `id` (UUID v4 via `gen_random_uuid()`, ou UUID v7 via fonction
custom en Vague 1 si le tri chronologique s'avère nécessaire), `type`
(discriminant), `created_at` (immuable). Cela garantit l'intégrité
référentielle SQL : toutes les FK pointent vers `resource.id`, pas vers
des tables polymorphes `target_type/target_id`.

**Stratégie physique** : class-table inheritance (voir ADR-001). Chaque
type a sa propre table, avec FK vers `resource(id)`. Pas de single-table
inheritance (colonnes sparse massives), pas de tables polymorphes.

### 3.2 Les 73 types du noyau

#### Identité et référentiels (types 1-8)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 1 | **Entity** | Racine conceptuelle. Tout objet avec identité, histoire ou relations propres. Sous-type `feature_of_interest` pour les choses observées distinctes de l'entité-support (audit F-P0-04). | `id`, `type`, `created_at`, `gsie_id` |
| 2 | **EntityAlias** | Alias d'entité vers un référentiel externe (GBIF, INPN, TaxRef). Résolution d'identité cross-source. | `entity_id` → Entity, `namespace` (ex. "GBIF"), `external_id`, `external_url` |
| 3 | **Concept** | Concept stable et citable (ex. `Quercus_robur`). L'identité ne change pas entre versions. | `id`, `preferred_label`, `description`, `vocabulary_id` → Vocabulary |
| 4 | **ConceptVersion** | Version d'un concept par release de vocabulaire. Porte les fusions taxonomiques (ex. TAXREF 15→16). | `concept_id` → Concept, `release_id` → VocabularyRelease, `label`, `fusions` (liste FusionEntry) |
| 5 | **Vocabulary** | Vocabulaire contrôlé (ex. TAXREF, WRB, EUR28). | `id`, `name`, `namespace`, `description` |
| 6 | **VocabularyRelease** | Release versionnée d'un vocabulaire (ex. TAXREF 16.0). | `vocabulary_id` → Vocabulary, `version`, `release_date` |
| 7 | **ControlledTerm** | Terme dans un vocabulaire, avec position hiérarchique optionnelle. | `vocabulary_id`, `code`, `label`, `parent_id` → ControlledTerm (optionnel) |
| 8 | **Instance** | Occurrence individuelle d'un Concept (ex. arbre n°458, placette A12). Sous-type d'Entity. | `concept_id` → Concept, `entity_id` → Entity, `spatial_scope` → Place |

#### Assertions et connaissances (types 9-13)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 9 | **Assertion** | Assertion scientifique unifiée. Remplace `KnowledgeObject` (livrable 302). `claim_kind` distinct de `lifecycle_status` (audit F-P1-01). Quand `claim_kind=rule`, `rule_subtype` précise la nature (inference, scientific, business, regulatory — enum §3.14). `scale_context_id` précise l'échelle de validité (v6.2). | `id`, `claim_kind` (enum §3.3), `lifecycle_status` (enum §3.4), `rule_subtype` (enum §3.14, optionnel, seulement si claim_kind=rule), `predicate_id` → Predicate, `spatial_scope_id` → Place, `temporal_context_id` → TemporalContext, `scale_context_id` → ScaleContext (optionnel), `version` (entier) |
| 10 | **AssertionParticipant** | Participant typé à une assertion (sujet, objet, contexte). Remplace les FK directes sujet/objet. Pointe vers `resource.id` (pas Entity) car un participant peut être un Concept (ex. *Quercus_robur*), une Instance, un Place, un Model, etc. — correction cohérence P0. | `assertion_id` → Assertion, `role` (enum : subject, object, context), `participant_id` → resource.id |
| 11 | **AssertionQualifier** | Qualificateur d'une assertion (région, période, métrique, protocole). Domaine de validité explicite (S-5). | `assertion_id` → Assertion, `key` (ex. "pH"), `value` (ex. "4.5-6.0"), `unit_id` → Unit (optionnel) |
| 12 | **Predicate** | Prédicat typé (ex. `est_adapte_a`, `influence`, `contredit`). Référence un ControlledTerm ou est libre. Référence un RelationType qui classifie la nature de la relation (causal, spatial, trophic, etc. — v6.2). | `id`, `label`, `inverse_label` (optionnel), `controlled_term_id` → ControlledTerm (optionnel), `relation_type_id` → RelationType (optionnel) |
| 13 | **EvidenceAssessment** | Évaluation de preuve sur une assertion. Multiples évaluations possibles (pas de `evidence_level` direct sur Assertion — audit F-P0-03). | `assertion_id` → Assertion, `level` (A-F, livrable 306), `evaluator_id` → Agent, `method`, `evaluated_at`, `scope` (texte) |

#### Observations et mesures (types 14-19)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 14 | **Observation** | Acte d'observer. Porte `sampling_effort` et `detection_probability` (audit F-P1-04). Le `subject` pointe vers `resource.id` (pas Entity) car on peut observer un Concept (ex. présence d'espèce), une Instance (ex. arbre 458), un Place, etc. — correction cohérence P0. Le `feature_of_interest_id` peut référencer un `FeatureOfInterest` (sous-type d'Entity, audit F-P0-04). | `id`, `subject_id` → resource.id, `feature_of_interest_id` → Entity (optionnel), `method_id` → Method, `instrument_id` → Instrument (optionnel), `temporal_context_id` → TemporalContext, `sampling_effort` (JSONB : durée, surface, visites), `detection_probability` (decimal, optionnel) |
| 15 | **Result** | Résultat d'une observation. `value_type='absence'` pour les absences observées (audit F-P0-05). `detection_limit` pour les limites de détection. | `observation_id` → Observation, `value_type` (enum §3.5), `value_numeric` (optionnel), `value_term_id` → ControlledTerm (optionnel), `value_text` (optionnel), `unit_id` → Unit (optionnel), `uncertainty_id` → Uncertainty (optionnel), `detection_limit` (optionnel) |
| 16 | **Method** | Méthode ou protocole d'observation/acquisition. | `id`, `name`, `description`, `protocol_url` (optionnel) |
| 17 | **Instrument** | Instrument ou capteur utilisé. | `id`, `name`, `type` (ex. "laser_dendrometre", "camera_trap"), `calibration_date` (optionnel) |
| 18 | **Uncertainty** | Incertitude quantifiée sur un Result ou une Assertion (S-5). | `id`, `type` (enum : confidence_interval, standard_error, range, qualitative), `lower` (optionnel), `upper` (optionnel), `confidence_level` (optionnel), `description` |
| 19 | **QualityAssessment** | Évaluation de qualité d'une donnée. FK vers `resource.id` (pas de FK polymorphe — audit F-P1-03). | `id`, `target_id` → resource.id, `dimension` (enum : completeness, positional_accuracy, temporal_accuracy, thematic_accuracy, logical_consistency), `score` (decimal 0-1), `method`, `assessed_at` |

#### Provenance et activités (types 20-24)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 20 | **Activity** | Activité PROV (transformation, extraction, ingestion, validation). Les extracteurs (PDF, NetCDF, GeoTIFF) sont des Activity avec `type='extraction'` ou `type='transformation'`. | `id`, `type` (enum : extraction, transformation, ingestion, validation, revision, simulation), `started_at`, `ended_at`, `agent_id` → Agent (optionnel), `method_id` → Method (optionnel) |
| 21 | **ProvEntity** | Entité PROV (artefact produit ou consommé par une Activity). Porte checksums pour la reproductibilité. | `id`, `checksum` (optionnel), `checksum_algorithm` (optionnel), `was_derived_from` → ProvEntity (optionnel), `was_generated_by` → Activity (optionnel) |
| 22 | **Agent** | Agent PROV (personne, organisation, logiciel). | `id`, `name`, `type` (enum : person, organisation, software), `orcid` (optionnel), `ror` (optionnel) |
| 23 | **Source** | Source d'information. Porte `source_nature` (audit F-P1-10) pour distinguer fournisseur de données vs fournisseur de connaissance. | `id`, `title`, `subtype` (enum : publication, dataset, api, person, organisation, regulatory_text, expert_statement), `source_nature` (enum §3.6), `url` (optionnel), `doi` (optionnel), `licence` (optionnel) |
| 24 | **Citation** | Citation d'une Source par une Assertion ou Observation. FK vers `resource.id` (audit F-P1-03). `locator` précis (page, figure, timestamp). | `id`, `source_id` → Source, `target_id` → resource.id, `citation_role` (enum : primary, supporting, contradicting, cited), `locator` (ex. "p.142", "fig.3", "00:14:32") |

#### Contextes (types 25-28)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 25 | **Unit** | Unité de mesure (UCUM/QUDT). | `id`, `symbol` (ex. "m", "°C", "mm"), `name`, `ucum_code` (optionnel) |
| 26 | **Place** | Entité spatiale. PostGIS pour la géométrie. | `id`, `geometry` (PostGIS), `srid` (ex. 2154), `label` (optionnel), `area_m2` (optionnel) |
| 27 | **TemporalContext** | Contexte temporel bitemporel (audit F-P1-02). Implémenté via le **GSIE Temporal & Provenance Engine** (Revision bitemporelle + Snapshot, ADR-002) — pas d'extension externe. | `id`, `valid_time_start`, `valid_time_end` (optionnel), `transaction_time_start` (immuable), `transaction_time_end` (null si courant), `granularity` (enum : instant, day, month, year, period, range) |
| 28 | **Media** | Média associé (photo, audio, vidéo, document). | `id`, `type` (enum : image, audio, video, document), `url`, `mime_type`, `checksum` (optionnel) |

#### Versionnement et snapshots (types 29-30)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 29 | **Revision** | Révision universelle d'une ressource. **Toute** ressource (Observation, Concept, Assertion, Dataset, Model, Instance, Correlation, Recommendation…) possède des révisions explicites. Append-only (CON-010 — jamais UPDATE ni DELETE). Bitemporelle : `valid_time_start/end` (quand c'est vrai dans le monde) + `transaction_time` (immuable, quand le système l'a enregistré). Liée à une Activity PROV (qui, comment) et optionnellement à un ResourceDiff (ce qui a changé). C'est le cœur du **GSIE Temporal & Provenance Engine** (ADR-002). | `id`, `target_id` → resource.id, `version` (entier), `author_id` → Agent, `justification` (texte obligatoire), `parent_id` → Revision (optionnel, chaîne), `valid_time_start`, `valid_time_end` (optionnel), `transaction_time` (immuable), `activity_id` → Activity (optionnel, PROV-O), `diff_id` → ResourceDiff (optionnel), `created_at` |
| 30 | **Snapshot** | Instantané immuable d'un état complet pour reproductibilité. Sérialise l'état de la ressource + ses relations + ses qualifiers + son evidence en JSONB. Utilisé pour : reproducibilité d'un ModelRun (input = Snapshot), reconstruction d'un état pour une Decision (« sur quelle version de la connaissance cette décision s'est-elle basée ? »), audit scientifique (« que savait-on au 2024-06-15 ? »). | `id`, `target_id` → resource.id, `revision_id` → Revision (capturée), `captured_at`, `serialized_state` (JSONB : champs + relations + qualifiers + evidence), `checksum` |

#### Modèles et simulations (types 31-32, 41)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 31 | **Model** | Modèle scientifique ou IA (croissance, dynamique, propagation). | `id`, `name`, `type` (enum : growth, dynamics, propagation, climate, ml), `description` |
| 32 | **ModelRun** | Exécution d'un ModelVersion avec des inputs, paramètres et outputs. Inputs et outputs sont des relations n:m via tables de jonction (`model_run_input`, `model_run_output`) — pas des listes JSONB. | `id`, `model_version_id` → ModelVersion, `parameters` (JSONB), `activity_id` → Activity, `scenario` (texte, optionnel) |

Tables de jonction associées (définies en Vague 1) :
```sql
CREATE TABLE model_run_input (
    model_run_id  UUID REFERENCES resource(id),
    input_id      UUID REFERENCES resource(id),  -- Snapshot ou ProvEntity
    role          VARCHAR(64),  -- ex. "initial_state", "forcing_data"
    PRIMARY KEY (model_run_id, input_id)
);
CREATE TABLE model_run_output (
    model_run_id  UUID REFERENCES resource(id),
    output_id     UUID REFERENCES resource(id),  -- Result ou ProvEntity
    role          VARCHAR(64),  -- ex. "projection", "metric"
    PRIMARY KEY (model_run_id, output_id)
);
```
| 41 | **ModelVersion** | Version versionnée d'un Model (ex. LANDIS-II v6.0 → v7.0). Entité traçable, pas un simple champ string (audit F-P1-07). | `id`, `model_id` → Model, `version` (string), `release_date`, `checksum` (optionnel), `inputs_schema` (JSONB), `outputs_schema` (JSONB) |

#### Datasets et distribution (types 33-36)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 33 | **Dataset** | Jeu de données référencé (livrable 305 catalogue 29 datasets). `purpose` précise l'usage : production, training, evaluation, reference (v6.2 — remplace les types TrainingDataset/EvaluationDataset par un champ, plus DRY). | `id`, `title`, `description`, `publisher_id` → Agent, `spatial_resolution` (optionnel), `temporal_resolution` (optionnel), `topic` (optionnel), `purpose` (enum §3.15, défaut : production) |
| 34 | **DatasetVersion** | Version d'un dataset (ex. BD Forêt v2.0 → v2.1). | `id`, `dataset_id` → Dataset, `version`, `release_date`, `changes` (texte) |
| 35 | **DataAsset** | Actif physique (fichier archivé localement). Porte `archived_from` + `checksum` + `original_uri` pour l'indépendance API (audit F-P2-08). | `id`, `dataset_version_id` → DatasetVersion, `format` (ex. "NetCDF", "GeoTIFF", "Parquet", "LAZ"), `size_bytes`, `checksum`, `archived_from` → Source (optionnel), `original_uri` (optionnel), `archived_at` |
| 36 | **Distribution** | Distribution d'un DatasetVersion avec canal d'accès typé (audit F-P1-09, 6 niveaux d'ingestion). | `id`, `dataset_version_id` → DatasetVersion, `access_method` (enum §3.7), `access_url` (optionnel), `licence`, `rights_statement_id` → RightsStatement (optionnel) |

#### Confidentialité et souveraineté (types 37-40)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 37 | **RightsStatement** | Déclaration de droits (licence, usage, restrictions). | `id`, `licence` (ex. "CC-BY-4.0", "LO-2.0", "ODbL"), `usage_rights` (enum : open, restricted, private), `attribution_required` (bool), `ai_training_allowed` (bool) |
| 38 | **AccessPolicy** | Politique d'accès (qui peut lire, écrire, exporter). | `id`, `target_id` → resource.id, `principal` (ex. "role:gestionnaire", "public"), `permission` (enum : read, write, export, delete), `condition` (optionnel) |
| 39 | **SensitivityClassification** | Classification de sensibilité d'une donnée (ex. espèce protégée). | `id`, `target_id` → resource.id, `level` (enum : public, restricted, sensitive, critical), `reason` (ex. "espèce_protégée_L214"), `classified_by` → Agent |
| 40 | **SpatialDisclosurePolicy** | Politique de dégradation spatiale (ex. maille 10km pour public, point exact pour gestionnaire). | `id`, `target_id` → resource.id, `public_precision` (ex. "10km"), `restricted_precision` (ex. "exact"), `authority` (ex. "INPN", "MNHN") |

#### Conflits (type 42)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 42 | **ConflictCluster** | Groupe d'Assertions contradictoires (audit F-P2-05, scénario B). Remplace le prédicat `contredit` isolé par une entité traçable qui groupe les assertions en conflit et documente la résolution (ou l'absence de résolution). | `id`, `description`, `status` (enum : open, resolved_by_consensus, resolved_by_arbitrage, unresolved), `resolution_note` (optionnel), `assertion_ids` (liste → Assertion via table de jonction) |

#### Échelle (type 43)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 43 | **ScaleContext** | Contexte d'échelle écologique. Toute corrélation écologique dépend de l'échelle : une assertion vraie au niveau peuplement peut être fausse au niveau paysage. ScaleContext définit le niveau granularity auquel une Assertion, Observation, Correlation ou EcologicalProcess est valide. Hiérarchie : leaf → tree → plot → stand → forest → massif → landscape → region → country → biome → earth. | `id`, `level` (enum §3.8), `parent_scale_id` → ScaleContext (optionnel, pour la hiérarchie), `extent_m2` (optionnel), `grain_m2` (optionnel), `description` (optionnel) |

#### Phénomènes et processus écologiques (types 44-45)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 44 | **Phenomenon** | Phénomène écologique (sécheresse, tempête, attaque de scolytes, succession écologique, migration, compétition, stress hydrique). Ni une entité, ni une observation, ni une activité PROV. A une durée, une étendue spatiale, une intensité. Est observé (via Observations), affecte des entités (via AssertionParticipants), et déclenche des EcologicalProcess. Essentiel pour Ignis. | `id`, `phenomenon_type` (enum §3.9), `name`, `intensity` (optionnel, decimal), `intensity_unit_id` → Unit (optionnel), `spatial_scope_id` → Place, `temporal_context_id` → TemporalContext, `scale_context_id` → ScaleContext, `affected_entities` (via AssertionParticipants sur des assertions claim_kind=relation) |
| 45 | **EcologicalProcess** | Processus écologique (photosynthèse, transpiration, croissance, décomposition, mycorhization, pollinisation, succession, compétition). Distinct de PROV Activity (qui est import/validation/simulation). Un EcologicalProcess a des inputs/outputs écologiques (CO2, H2O, biomass), pas des artefacts PROV. Peut être observé, modélisé, et il drive des Phenomena. | `id`, `process_type` (enum §3.10), `name`, `spatial_scope_id` → Place, `temporal_context_id` → TemporalContext, `scale_context_id` → ScaleContext, `rate` (optionnel, decimal), `rate_unit_id` → Unit (optionnel), `driver_phenomenon_id` → Phenomenon (optionnel) |

#### Typologie des relations (type 46)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 46 | **RelationType** | Méta-classification des prédicats. Un Predicate référence un RelationType qui catégorise la nature de la relation : causal, spatial, temporal, ecological, taxonomic, hydrological, genetic, trophic, competition, facilitation, host-pathogen, predator-prey. Permet au Reasoning Engine de filtrer les inférences par type de relation. | `id`, `category` (enum §3.11), `label`, `description`, `parent_id` → RelationType (optionnel, pour sous-typage) |

#### Échantillonnage (type 47)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 47 | **SamplingEvent** | Événement d'échantillonnage (campagne de terrain). Hiérarchie : campagne → placettes → observations → résultats. Un SamplingEvent groupe des Observations avec un protocole partagé, une fenêtre temporelle et un design spatial. Essentiel pour la validité statistique (détection de pseudo-réplication, calcul d'effort d'échantillonnage agrégé). | `id`, `name`, `protocol_id` → Method, `spatial_design` (texte, ex. "grille 100m × 100m"), `temporal_context_id` → TemporalContext, `scale_context_id` → ScaleContext, `parent_event_id` → SamplingEvent (optionnel, pour la hiérarchie campagne → placette), `principal_investigator_id` → Agent |

#### Traits fonctionnels (types 48-49)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 48 | **TraitDefinition** | Définition d'un trait fonctionnel (Leaf Area, SLA, Wood Density, Root Depth, Shade Tolerance, Fire Resistance, Drought Resistance, Longevity). Transversal — comparable cross-species. Référence des standards (TRY, LEDA). | `id`, `name`, `abbreviation` (ex. "SLA"), `description`, `unit_id` → Unit, `standard_reference` (optionnel, ex. "TRY-db"), `value_range` (optionnel, texte) |
| 49 | **TraitValue** | Valeur d'un trait pour une entité, avec incertitude et contexte. Distinct d'une Observation générique car les traits ont une sémantique spécifique (comparabilité cross-species, protocoles standardisés). | `id`, `trait_definition_id` → TraitDefinition, `entity_id` → resource.id, `value_numeric` (optionnel), `value_term_id` → ControlledTerm (optionnel, pour traits catégoriels comme shade_tolerance), `unit_id` → Unit, `uncertainty_id` → Uncertainty (optionnel), `observation_id` → Observation (optionnel, source de la mesure), `scale_context_id` → ScaleContext (optionnel) |

#### IA et machine learning (types 50-52)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 50 | **Feature** | Caractéristique calculée utilisée par les modèles IA (ex. "ndvi_moyen_2024", "dbh_moyen_placette", "ph_moyen_sol"). Une Feature est dérivée d'Observations, de Traits, ou d'autres Features. | `id`, `name`, `description`, `source_type` (enum : observation, trait, computed, external), `computation_method` (optionnel, texte), `unit_id` → Unit (optionnel) |
| 51 | **FeatureSet** | Collection structurée de Features utilisée pour entraîner ou évaluer un modèle IA. Définit le schéma d'entrée d'un ModelVersion. | `id`, `name`, `description`, `feature_ids` (liste → Feature via table de jonction), `model_version_id` → ModelVersion (optionnel) |
| 52 | **Inference** | Inférence produite par un modèle IA appliqué à de nouvelles données. Distinct de ModelRun (qui est l'exécution complète) : une Inference est le résultat d'une application ponctuelle (prédiction, classification, détection). | `id`, `model_version_id` → ModelVersion, `feature_set_id` → FeatureSet, `input_snapshot_id` → Snapshot, `output_assertion_id` → Assertion (optionnel, si l'inférence produit une assertion), `confidence` (decimal 0-1), `inferred_at` |

#### Raisonnement (types 53-57)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 53 | **Question** | Question scientifique ou opérationnelle (ex. « Quelle essence planter sur cette parcelle ? », « Le hêtre est-il en stress hydrique sur ce site ? »). Point d'entrée du moteur de raisonnement. | `id`, `text`, `question_type` (enum : scientific, operational, diagnostic, predictive), `asked_by` → Agent, `asked_at`, `scale_context_id` → ScaleContext (optionnel), `spatial_scope_id` → Place (optionnel), `temporal_context_id` → TemporalContext (optionnel) |
| 54 | **Hypothesis** | Hypothèse testable liée à une Question. Référence des Assertions qui la supportent ou la contredisent. | `id`, `question_id` → Question, `text`, `status` (enum : proposed, testing, supported, refuted, inconclusive), `supporting_assertions` (via table de jonction), `contradicting_assertions` (via table de jonction) |
| 55 | **Decision** | Décision prise par un humain (CON-001 : l'IA assiste, ne décide jamais). Référence les Recommendations considérées et les Evidence qui ont motivé le choix. | `id`, `question_id` → Question (optionnel), `decided_by` → Agent, `decision_text`, `rationale` (texte obligatoire), `recommendations_considered` (liste → Recommendation via table de jonction), `evidence_refs` (liste → Citation via table de jonction), `decided_at`, `scale_context_id` → ScaleContext (optionnel) |
| 56 | **Recommendation** | Recommandation produite par un moteur GSIE. Référence les Assertions et Scenarios qui la justifient. Est contournable par le forestier (CON-001). | `id`, `question_id` → Question (optionnel), `recommended_by` → Agent (le moteur), `recommendation_text`, `confidence` (decimal 0-1), `supporting_assertions` (via table de jonction), `scenarios_evaluated` (liste → Scenario via table de jonction), `scale_context_id` → ScaleContext, `spatial_scope_id` → Place (optionnel), `temporal_context_id` → TemporalContext (optionnel) |
| 57 | **Scenario** | Scénario (sylvicole, climatique, de gestion) qui alimente des ModelRuns et des Recommendations. Un Scenario définit des hypothèses sur le futur (ex. "RCP 4.5 2050", "sylviculture dynamique rapprochée"). `scenario_subtype` spécialise les scénarios climatiques (RCP, SSP, DRIAS) qui reviennent partout dans GSIE (v6.2 enrichissement). | `id`, `name`, `scenario_type` (enum : sylvicultural, climatic, management, disturbance, baseline), `scenario_subtype` (enum §3.22, optionnel), `description`, `parameters` (JSONB), `scale_context_id` → ScaleContext, `temporal_context_id` → TemporalContext |

#### Corrélations (type 58)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 58 | **Correlation** | Corrélation entre deux ou plusieurs entités/variables. Objet de connaissance versionné et évaluable. Le Correlation Engine les produit et les réévalue. Porte la méthode, la confiance, la force et l'évidence. | `id`, `method` (enum §3.12), `variables` (liste → resource.id via table de jonction, avec role), `coefficient` (decimal, optionnel), `strength` (enum : negligible, weak, moderate, strong, very_strong), `confidence` (decimal 0-1), `p_value` (optionnel), `evidence_assessment_id` → EvidenceAssessment (optionnel), `scale_context_id` → ScaleContext, `spatial_scope_id` → Place (optionnel), `temporal_context_id` → TemporalContext (optionnel), `lifecycle_status` (enum §3.4, réutilisé) |

#### Services écosystémiques (type 59)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 59 | **EcosystemService** | Service écosystémique (régulation, support, production, culture). Type défini mais vide — implémentation différée (niveau E). Le type existe au noyau pour éviter un changement de schéma futur. Classification CICES ou Millennium Ecosystem Assessment. | `id`, `name`, `category` (enum : regulation, support, provisioning, cultural), `description`, `scale_context_id` → ScaleContext (optionnel) |

#### Orchestration (type 60)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 60 | **Capability** | Capacité d'un moteur ou d'une application (observer, predict, inventory, diagnose, simulate, recommend). Utilisé par l'orchestrateur pour router les requêtes vers le bon moteur/app. Un moteur déclare ses Capabilities ; l'orchestrateur les lit pour composer des pipelines. | `id`, `name`, `capability_type` (enum §3.13), `provider_type` (enum : engine, application), `provider_id` → Agent, `input_schema` (JSONB, optionnel), `output_schema` (JSONB, optionnel) |

#### Diff de révision (type 61)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 61 | **ResourceDiff** | Différence explicite entre deux Revisions. Documente **ce qui a changé** (champs ajoutés, modifiés, supprimés, relations ajoutées/retirées). Permet à un humain ou un moteur de comprendre l'évolution sans comparer deux snapshots complets. C'est le 5e concept du GSIE Temporal & Provenance Engine (ADR-002). | `id`, `from_revision_id` → Revision, `to_revision_id` → Revision, `changes` (JSONB : `{added: {...}, modified: {field: {from, to}}, removed: {...}}`), `summary` (texte, description humaine du changement), `created_at` |

#### Échantillon physique (type 62) — SOSA/SSN

| # | Type | Description | Champs clés |
|---|---|---|---|
| 62 | **Sample** | Échantillon physique prélevé sur le terrain (échantillon de sol, carotte, feuille, écorce, prélèvement d'eau). Distinct d'une Observation (l'échantillon est un artefact matériel, pas une mesure) et d'une Instance (l'Instance est l'organisme vivant, l'échantillon est un fragment prélevé). Mapping SOSA/SSN : `sosa:Sample`. Un Sample est produit par un SamplingEvent (type 47) et peut générer plusieurs Observations (type 14). | `id`, `sample_type` (enum §3.16), `sampling_event_id` → SamplingEvent, `subject_id` → resource.id (entité échantillonnée : Instance, Place, etc.), `material` (ex. "sol", "écorce", "feuille", "eau"), `storage_location` (optionnel), `storage_conditions` (optionnel, ex. "-20°C"), `collected_at` → TemporalContext, `mass_g` (optionnel), `volume_ml` (optionnel) |

#### RGPD / Confidentialité des personnes (types 63-64)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 63 | **Consent** | Consentement explicite RGPD d'une personne (DataSubject) pour le traitement de ses données. Obligatoire pour tout traitement de données personnelles (Agent type=person, Decision.decided_by, observations par un forestier identifié). Porte la finalité, la durée, le droit de retrait. | `id`, `data_subject_id` → DataSubject, `purpose` (texte, ex. "recherche forestière", "publication scientifique"), `scope` (enum : full, anonymized_only, aggregated_only), `granted_at`, `expires_at` (optionnel), `withdrawn_at` (optionnel), `legal_basis` (enum §3.17), `document_ref` (optionnel, URL ou chemin du document signé) |
| 64 | **DataSubject** | Personne physique concernée par des données personnelles (RGPD art. 4). Distinct d'Agent : un Agent peut être une organisation ou un logiciel (pas un DataSubject). Un DataSubject a des droits (accès, rectification, oubli, portabilité). Lié à Agent (quand type=person) via `agent_id`. | `id`, `agent_id` → Agent (lien vers la personne), `email` (chiffré, optionnel), `anonymized` (bool, défaut false), `rights_exercised` (JSONB, optionnel : historique des droits exercés), `consent_ids` (liste → Consent via table de jonction) |

#### Identifiants persistants (type 65)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 65 | **PersistentIdentifier** | Identifiant persistant externe pour une ressource GSIE. Permet la citation académique (DOI), la découverte (PURL/w3id), l'interopérabilité (ORCID, ROR, GBIF taxonKey, Wikidata QID). Un objet GSIE peut avoir plusieurs PersistentIdentifiers (ex. un Dataset a un DOI DataCite + un URI PURL). Répond au principe FAIR F1 (identifiant persistant global). | `id`, `target_id` → resource.id, `pid_type` (enum §3.18), `value` (ex. "10.5281/zenodo.1234567", "https://w3id.org/gsie/assertion/1234", "0000-0002-1825-0097"), `authority` (ex. "DataCite", "Wikidata", "ORCID", "GBIF"), `registered_at`, `active` (bool, défaut true) |

#### Flux écologiques (type 66)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 66 | **Flow** | Flux écologique entre compartiments de l'écosystème (carbone, eau, nutriments, énergie, graines, gènes, maladies, champignons, pollens). Un flux a une source, une destination, une magnitude, une direction, une unité et une dynamique temporelle. Distinct d'une relation (Assertion) car un flux est une **quantité qui se déplace**, pas juste un lien. Exemple : carbone → atmosphère → photosynthèse → bois → mort → décomposition → sol → atmosphère. Essentiel pour les bilans (carbone, hydrique, azote). | `id`, `flow_type` (enum §3.19), `source_id` → resource.id (compartiment source : Place, Instance, Phenomenon), `sink_id` → resource.id (compartiment destination), `magnitude` (decimal), `magnitude_unit_id` → Unit, `direction` (enum : source_to_sink, bidirectional), `temporal_context_id` → TemporalContext, `scale_context_id` → ScaleContext, `driver_process_id` → EcologicalProcess (optionnel), `uncertainty_id` → Uncertainty (optionnel) |

#### Graphe de confiance (type 67)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 67 | **ConfidenceGraph** | Graphe de confiance calculé qui propage l'incertitude à travers les dépendances de connaissance. Une recommandation peut dépendre de 14 publications, 6 observations, 2 modèles, 1 IA, 3 experts — le ConfidenceGraph agrège ces sources en un score de confiance global avec propagation. Distinct d'EvidenceAssessment (qui évalue une assertion individuelle) : ConfidenceGraph évalue la **chaîne complète** et propage l'incertitude amont→aval. Calculé par le Reasoning Engine ou un moteur dédié. | `id`, `target_id` → resource.id (ressource évaluée : Assertion, Recommendation, Decision), `confidence_score` (decimal 0-1, score global propagé), `propagation_method` (enum : bayesian, weighted_average, dempster_shafer, fuzzy), `source_nodes` (JSONB : liste de `{resource_id, individual_confidence, weight, evidence_level}`), `propagation_tree` (JSONB : arbre de propagation avec nœuds et arêtes), `computed_at`, `computed_by` → Agent (moteur), `valid_for_revision_id` → Revision (état de la connaissance au moment du calcul) |

#### Objectifs et contraintes (types 68-69)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 68 | **Goal** | Objectif de gestion ou scientifique qui oriente les décisions. Exemples : « favoriser la biodiversité », « maximiser la production », « limiter les risques incendies », « restaurer la continuité écologique ». Toute Recommendation et Decision référence un ou plusieurs Goals. Un Goal peut être hiérarchique (objectif national → régional → local) et peut entrer en conflit avec d'autres Goals (production vs biodiversité). | `id`, `goal_type` (enum §3.20), `name`, `description`, `priority` (enum : primary, secondary, tertiary), `parent_goal_id` → Goal (optionnel, hiérarchie), `spatial_scope_id` → Place (optionnel), `temporal_context_id` → TemporalContext (optionnel), `scale_context_id` → ScaleContext (optionnel), `success_criteria` (texte, optionnel — comment mesurer l'atteinte) |
| 69 | **Constraint** | Contrainte qui limite la faisabilité d'une Recommendation. Peut être réglementaire (Natura 2000, arrêté préfectoral), opérationnelle (budget, accessibilité, météo, machine indisponible), écologique (pente, sensibilité du sol), ou temporelle (fenêtre de travail). Le moteur doit savoir **pourquoi** une recommandation n'est pas réalisable. Une Constraint peut bloquer, limiter, ou conditionner une Recommendation. | `id`, `constraint_type` (enum §3.21), `name`, `description`, `severity` (enum : blocking, limiting, conditional), `source_id` → Source (optionnel, ex. texte réglementaire), `spatial_scope_id` → Place (optionnel), `temporal_context_id` → TemporalContext (optionnel), `affected_recommendation_id` → Recommendation (optionnel), `mitigation` (texte, optionnel — comment contourner) |

#### Lignage de connaissance (type 70)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 70 | **KnowledgeLineage** | Nœud explicite du DAG de lignage de connaissance. Pas seulement Source → Citation, mais la chaîne complète : Connaissance A → a servi à produire → Connaissance B → qui produit → Recommendation → Decision. Chaque nœud documente quelle ressource a été dérivée de quelles autres, par quel processus, avec quelle confiance. Complète PROV-O (qui est générique) avec la sémantique de **production de connaissance scientifique**. Permet de répondre : « si je invalide l'assertion X, quelles recommandations et décisions sont affectées ? » | `id`, `resource_id` → resource.id (ressource produite), `derived_from` (liste → resource.id via table de jonction, avec role : primary_input, supporting_input, method), `produced_by` → Activity (processus PROV), `production_method` (enum : inference, correlation, synthesis, expert_judgment, model_output, extraction, validation), `confidence_graph_id` → ConfidenceGraph (optionnel), `lineage_depth` (entier, profondeur dans le DAG) |

#### Expériences scientifiques (type 71)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 71 | **Experiment** | Série d'expérimentations scientifiques groupant plusieurs ModelRuns avec un cadre de comparaison. Un scientifique ne fait pas 1 simulation — il fait 500 simulations, compare, publie. Un Experiment définit l'hypothèse testée, les scénarios comparés, les métriques d'évaluation, et référence les ModelRuns. Peut produire une Assertion (claim_kind=model) si les résultats sont concluants, ou une Publication (via Source). | `id`, `name`, `hypothesis_id` → Hypothesis (optionnel), `scenario_ids` (liste → Scenario via table de jonction), `model_run_ids` (liste → ModelRun via table de jonction), `comparison_metrics` (JSONB : métriques d'évaluation), `conclusion` (texte, optionnel), `resulting_assertion_id` → Assertion (optionnel), `resulting_source_id` → Source (optionnel, publication), `conducted_by` → Agent, `scale_context_id` → ScaleContext |

#### Missions terrain (type 72)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 72 | **TerrainSession** | Mission terrain GeoSylva — plus large qu'un SamplingEvent. Une sortie terrain contient : météo, GPS, opérateur, matériel, précision GPS, photos, LiDAR, remarques, martelage, inventaire, arbres, placettes, protocole, erreurs, synchronisation. Une TerrainSession peut contenir plusieurs SamplingEvents (placettes), des Observations, des Samples, des Media (photos), et produire des Assertions (inventaire, martelage). C'est l'unité de **production de connaissance terrain** pour GeoSylva. | `id`, `name`, `operator_id` → Agent (forestier/opérateur), `session_type` (enum : inventory, martelage, monitoring, diagnosis, research, calibration), `started_at`, `ended_at`, `weather` (JSONB : température, humidité, vent, précipitations), `gps_precision_m` (decimal, optionnel), `equipment` (JSONB : liste du matériel utilisé), `spatial_scope_id` → Place, `scale_context_id` → ScaleContext, `protocol_id` → Method (optionnel), `sampling_event_ids` (liste → SamplingEvent via table de jonction), `media_ids` (liste → Media via table de jonction), `sync_status` (enum : synced, partial, pending, failed), `notes` (texte, optionnel) |

#### État écologique synthétique (type 73)

| # | Type | Description | Champs clés |
|---|---|---|---|
| 73 | **EcologicalState** | État écologique synthétique d'un écosystème à un endroit et un instant donnés. Répond à « quel est l'état de santé de cet écosystème ? » plutôt qu'à « quel est le pH ? ». Agrège des Observations, Traits, Correlations et Assertions en un état synthétique avec des indicateurs (biodiversité, vitalité, risque, résilience). Peut être calculé par le Diagnostic Engine ou le Forest Dynamics Engine. Versionné via Revision (l'état évolue dans le temps). | `id`, `spatial_scope_id` → Place, `temporal_context_id` → TemporalContext, `scale_context_id` → ScaleContext, `state_type` (enum : health, vitality, risk, resilience, biodiversity, productivity, integrity), `indicators` (JSONB : `{indicator_name: {value, unit, confidence, trend}}`), `overall_score` (decimal 0-1, optionnel), `overall_grade` (enum : excellent, good, moderate, poor, critical, optionnel), `based_on` (liste → resource.id via table de jonction : observations, traits, correlations, assertions), `computed_by` → Agent (moteur), `trend` (enum : improving, stable, declining, unknown, optionnel) |

### 3.3 Enum `claim_kind` (Assertion)

Distinction épistémologique (audit F-P1-01). Séparé de `lifecycle_status`.

| Valeur | Description | Exemple |
|---|---|---|
| `observation` | Issue d'une mesure directe | « dbh de l'arbre 458 = 32 cm » |
| `relation` | Relation typée entre entités | « chêne sessile est_adapte_a sol acide » |
| `rule` | Règle d'inférence | « SI pH ∈ [4,5;6,0] ET altitude <1400 m ALORS chêne sessile adapté » |
| `threshold` | Valeur seuil scientifique | « RUM minimale pour le hêtre = 80 mm » |
| `model` | Référence à un modèle scientifique | « ONF-FFN pour le douglas » |
| `classification` | Classification référentielle | « Alocrisol (RPF, INRAE 2008) » |
| `absence` | Absence observée (audit F-P0-05) | « espèce X non détectée avec effort Y » |

**Mapping depuis KnowledgeObject 6 types** (livrable 302 → v6.1) :
`concept` → non applicable (devenu `Concept` type 3) ; `relation` →
`claim_kind=relation` ; `regle` → `claim_kind=rule` ; `seuil` →
`claim_kind=threshold` ; `modele` → `claim_kind=model` ; `classification`
→ `claim_kind=classification`. Ajouts : `observation` et `absence`.

### 3.4 Enum `lifecycle_status` (Assertion)

Statut de cycle de vie, distinct de la nature épistémologique.

| Valeur | Description |
|---|---|
| `draft` | Brouillon, non soumis |
| `proposed` | Soumis, en attente de qualification |
| `accepted` | Qualifié par Evidence Engine, ingéré |
| `superseded` | Remplacé par une nouvelle version (CON-010) |
| `rejected` | Refusé par Evidence Engine |
| `deprecated` | Obsolète mais conservé |

### 3.5 Enum `value_type` (Result)

| Valeur | Description |
|---|---|
| `numeric` | Valeur numérique avec unité |
| `term` | Référence à un ControlledTerm |
| `media_ref` | Référence à un Media |
| `entity_ref` | Référence à une Entity |
| `computed` | Valeur calculée (dérivée d'autres Results) |
| `absence` | Absence observée (audit F-P0-05) — accompagné de `sampling_effort` sur l'Observation parent |

### 3.6 Enum `source_nature` (Source)

Distinction épistémologique entre fournisseurs de données et
fournisseurs de connaissance (audit F-P1-10).

| Valeur | Description | Exemple |
|---|---|---|
| `data_provider` | Fournit des observations/mesures brutes | IGN BD Forêt, Météo-France, SoilGrids |
| `knowledge_provider` | Fournit des assertions/recommandations déjà interprétées | ClimEssences, BioClimSol, guides sylvicoles |
| `reference` | Publication citée (article, thèse, rapport) | Rameau et al. 2018 |
| `expert_statement` | Déclaration d'expert identifié | Forestier X, communication personnelle |
| `regulatory` | Texte réglementaire ou norme | Code forestier, directive Natura 2000 |
| `model_output` | Sortie d'un modèle scientifique | Projection DRIAS, ModelRun |

### 3.7 Enum `access_method` (Distribution)

Les 6 niveaux d'ingestion (arbitrage Fondateur + audit F-P1-09).

| Valeur | Niveau | Description | Exemples |
|---|---|---|---|
| `api_rest` | 1 | API REST officielle | Hub'Eau, INPN API, GBIF API |
| `api_graphql` | 1 | API GraphQL officielle | (réservé, non utilisé en Vague 1) |
| `ogc_wms` | 3 | Service OGC WMS | IGN Géoplateforme (cartes) |
| `ogc_wfs` | 3 | Service OGC WFS | IGN Géoplateforme (vecteur) |
| `ogc_wmts` | 3 | Service OGC WMTS | IGN Géoplateforme (tuiles raster) |
| `ogc_wcs` | 3 | Service OGC WCS | IGN Géoplateforme (raster continu) |
| `stac_api` | 4 | API STAC | Copernicus, Earth Search, Sentinel Hub |
| `file_download` | 2 | Téléchargement officiel (avec conditions) | DRIAS (NetCDF), SoilGrids (dump) |
| `file_import` | 5 | Import de fichier local | GeoTIFF, LAZ, CSV, GeoPackage utilisateur |
| `publication_text` | 6 | Publication scientifique (texte) | DOI, Crossref, HAL, OpenAlex |
| `knowledge_extraction` | 6 | Extraction de connaissance depuis ressource non structurée | ClimEssences (site web), PDF, tableau |

### 3.8 Enum `scale_level` (ScaleContext)

Hiérarchie d'échelles écologiques. Toute assertion, observation,
corrélation ou processus est valide à une échelle donnée.

| Valeur | Description | Ordre de grandeur |
|---|---|---|
| `leaf` | Feuille | mm² - cm² |
| `tree` | Arbre individuel | m² |
| `plot` | Placette | 100 m² - 1 ha |
| `stand` | Peuplement | 1 - 100 ha |
| `forest` | Forêt | 100 ha - 10 000 ha |
| `massif` | Massif | 10 000 ha - 1 Mha |
| `landscape` | Paysage | 1 Mha - 10 Mha |
| `region` | Région | 10 Mha - 100 Mha |
| `country` | Pays | 100 Mha - 1 Gha |
| `biome` | Biome | > 1 Gha |
| `earth` | Planète | 51 Gha |

### 3.9 Enum `phenomenon_type` (Phenomenon)

| Valeur | Description | Exemple |
|---|---|---|
| `drought` | Sécheresse | Stress hydrique 2003 |
| `storm` | Tempête | Tempête Lothar 1999 |
| `pest_outbreak` | Épidémie de ravageurs | Scolytes 2018-2023 |
| `pathogen_outbreak` | Épidémie de pathogène | Chalarose du frêne |
| `wildfire` | Incendie | Landes 2022 |
| `flood` | Inondation | Crue centennale |
| `succession` | Succession écologique | Colonisation post-coupe |
| `migration` | Migration d'espèces | Migration altitudinale du hêtre |
| `competition` | Compétition interspécifique | Hêtre vs chêne |
| `invasion` | Invasion biologique | Renouée du Japon |
| `decline` | Dépérissement | Dépérissement du sapin pectiné |
| `regeneration` | Régénération naturelle | Semis post-tempête |
| `phenology_shift` | Décalage phénologique | Floraison avancée |
| `other` | Autre phénomène | (à préciser dans `name`) |

### 3.10 Enum `ecological_process_type` (EcologicalProcess)

| Valeur | Description |
|---|---|
| `photosynthesis` | Photosynthèse |
| `transpiration` | Transpiration |
| `respiration` | Respiration (plante, sol, écosystème) |
| `growth` | Croissance (individu, peuplement) |
| `decomposition` | Décomposition de la litière / matière organique |
| `nutrient_cycling` | Cycle des nutriments (N, P, K, C) |
| `mycorrhization` | Mycorhization |
| `nitrogen_fixation` | Fixation d'azote |
| `pollination` | Pollinisation |
| `seed_dispersal` | Dissémination des graines |
| `herbivory` | Herbivorie |
| `predation` | Prédation |
| `competition` | Compétition (intra/inter-spécifique) |
| `facilitation` | Facilitation |
| `succession` | Succession primaire/secondaire |
| `carbon_sequestration` | Séquestration carbone |
| `water_cycling` | Cycle de l'eau |
| `other` | Autre processus |

### 3.11 Enum `relation_category` (RelationType)

| Valeur | Description | Exemples de prédicats |
|---|---|---|
| `causal` | Relation causale | influence, provoque, empêche |
| `spatial` | Relation spatiale | adjacent_a, inclus_dans, chevauche |
| `temporal` | Relation temporelle | precede, succede_a, contemporain_de |
| `ecological` | Relation écologique générale | est_adapte_a, croit_mieux_sur |
| `taxonomic` | Relation taxonomique | est_espèce_de, est_synonyme_de |
| `hydrological` | Relation hydrologique | draine_vers, alimente, inonde |
| `genetic` | Relation génétique | est_parent_de, est_hybride_de |
| `trophic` | Relation trophique | mange, est_mangé_par, décompose |
| `competition` | Relation de compétition | compétition_avec, exclut |
| `facilitation` | Relation de facilitation | facilite, protège |
| `host_pathogen` | Relation hôte-pathogène | infecte, est_hôte_de |
| `predator_prey` | Relation prédateur-proie | prédation_sur, est_proie_de |
| `other` | Autre | (à préciser dans `label`) |

### 3.12 Enum `correlation_method` (Correlation)

| Valeur | Description |
|---|---|
| `pearson` | Corrélation de Pearson (linéaire) |
| `spearman` | Corrélation de Spearman (monotone) |
| `kendall` | Tau de Kendall |
| `bayesian` | Inférence bayésienne |
| `mutual_information` | Information mutuelle (non-linéaire) |
| `ai` | Corrélation détectée par modèle IA |
| `expert` | Corrélation affirmée par expert |
| `literature` | Corrélation documentée dans la littérature |
| `meta_analysis` | Méta-analyse |

### 3.13 Enum `capability_type` (Capability)

| Valeur | Description | Moteur/app typique |
|---|---|---|
| `observe` | Collecter des observations | GIS Engine, Botanical Engine |
| `predict` | Prédire un état futur | Simulation Engine, Climate Engine |
| `inventory` | Inventorier des ressources | Forest Dynamics Engine |
| `diagnose` | Diagnostiquer un état/pathologie | Diagnostic Engine |
| `simulate` | Simuler un scénario | Simulation Engine |
| `recommend` | Recommander une action | Recommendation Engine |
| `correlate` | Détecter des corrélations | Correlation Engine |
| `reason` | Inférer des conclusions | Reasoning Engine |
| `validate` | Valider des assertions | Validation Engine |
| `learn` | Apprendre des patterns | Learning Engine |
| `extract` | Extraire de la connaissance | Knowledge Engine |
| `assess_evidence` | Évaluer le niveau de preuve | Evidence Engine |

### 3.14 Enum `rule_subtype` (Assertion quand claim_kind=rule)

Typologie des règles (adaptation de la proposition Fondateur — pas 4
types séparés, mais un champ sur Assertion pour préserver l'unification).

| Valeur | Description | Exemple |
|---|---|---|
| `inference` | Règle d'inférence logique | « SI pH ∈ [4.5;6.0] ET altitude <1400 m ALORS chêne sessile adapté » |
| `scientific` | Règle scientifique établie | « RUM minimale pour le hêtre = 80 mm » |
| `business` | Règle métier (sylviculture, gestion) | « Pas de coupe rase sur pente > 30% » |
| `regulatory` | Règle réglementaire | « Distance minimale 50m entre coupes > 2ha » (Code forestier) |

### 3.15 Enum `dataset_purpose` (Dataset)

| Valeur | Description |
|---|---|
| `production` | Dataset opérationnel (référence, catalogue) |
| `training` | Dataset d'entraînement pour modèles IA |
| `evaluation` | Dataset d'évaluation pour modèles IA |
| `reference` | Dataset de référence (ground truth, benchmark) |

### 3.16 Enum `sample_type` (Sample)

Typologie des échantillons physiques (mapping SOSA/SSN `sosa:Sample`).

| Valeur | Description | Exemple |
|---|---|---|
| `soil` | Échantillon de sol | Horizon A, 0-30cm |
| `leaf` | Échantillon de feuille | Feuille de chêne, nécrose |
| `bark` | Échantillon d'écorce | Écorce avec fructification de pathogène |
| `wood_core` | Carotte de bois | Dendrochronologie |
| `water` | Prélèvement d'eau | Eau de surface, nappe |
| `root` | Échantillon de racine | Mycorhization |
| `seed` | Graine | Banque de semences |
| `tissue` | Tissu végétal/animal | ADN, génétique |
| `soil_water` | Solution du sol | Lysimètre |
| `litter` | Litière | Décomposition |
| `other` | Autre | (à préciser dans `material`) |

### 3.17 Enum `legal_basis` (Consent — RGPD art. 6)

Base légale du traitement des données personnelles.

| Valeur | Description | Article RGPD |
|---|---|---|
| `consent` | Consentement de la personne | Art. 6.1.a |
| `contract` | Exécution d'un contrat | Art. 6.1.b |
| `legal_obligation` | Obligation légale | Art. 6.1.c |
| `vital_interest` | Intérêt vital | Art. 6.1.d |
| `public_interest` | Mission d'intérêt public | Art. 6.1.e |
| `legitimate_interest` | Intérêt légitime | Art. 6.1.f |
| `research` | Recherche scientifique (art. 9.2.j) | Art. 9.2.j + dérogation |

### 3.18 Enum `pid_type` (PersistentIdentifier)

Typologie des identifiants persistants (FAIR F1).

| Valeur | Description | Autorité | Exemple |
|---|---|---|---|
| `doi` | Digital Object Identifier | DataCite, Crossref | `10.5281/zenodo.1234567` |
| `purl` | Persistent URL | w3id.org, purl.org | `https://w3id.org/gsie/assertion/1234` |
| `orcid` | Open Researcher and Contributor ID | ORCID | `0000-0002-1825-0097` |
| `ror` | Research Organization Registry | ROR | `042nb2s42` |
| `gbif_taxonkey` | GBIF Taxon Key | GBIF | `2878688` (Quercus robur) |
| `wikidata_qid` | Wikidata Q ID | Wikidata | `Q165145` |
| `inpn_taxref` | TaxRef INPN | MNHN | `97849` |
| `issn` | International Standard Serial Number | ISSN | `2024-0089` |
| `handle` | Handle System | CNRI | `20.500.12123/456` |
| `ark` | Archival Resource Key | CDL | `ark:/12148/cb11936373k` |
| `urn` | Uniform Resource Name | IETF | `urn:isbn:978-2-86...` |
| `gsie_uri` | URI GSIE persistante | GSIE | `https://gsie.quintessences.fr/r/1234` |

---

### 3.19 Enum `flow_type` (Flow)

Typologie des flux écologiques entre compartiments de l'écosystème.

| Valeur | Description | Exemple |
|---|---|---|
| `carbon` | Flux de carbone | Photosynthèse, respiration, décomposition |
| `water` | Flux d'eau | Transpiration, ruissellement, infiltration |
| `nitrogen` | Flux d'azote | Fixation, minéralisation, lessivage |
| `phosphorus` | Flux de phosphore | Absorption, retour au sol |
| `nutrient` | Flux de nutriments (générique) | Cycle NPK |
| `energy` | Flux d'énergie | Rayonnement, biomasse, trophique |
| `seed` | Dissémination de graines | Vent, zoochorie, barochorie |
| `pollen` | Flux de pollen | Anémophilie, entomophilie |
| `gene` | Flux génétique | Pollinisation croisée, dispersion |
| `pathogen` | Propagation de pathogènes | Spores, vecteurs, contact |
| `spore` | Dispersion de spores (champignons) | Mycorhization, pathogènes |
| `biomass` | Transfert de biomasse | Litière, nécromasse, herbivorie |
| `sediment` | Flux de sédiments | Érosion, dépôt |
| `other` | Autre flux | (à préciser dans `name`) |

### 3.20 Enum `goal_type` (Goal)

| Valeur | Description | Exemple |
|---|---|---|
| `biodiversity` | Favoriser la biodiversité | Continuité écologique, mixité d'essences |
| `production` | Maximiser la production | Volume bois, croissance |
| `risk_reduction` | Limiter les risques | Incendie, tempête, ravageurs |
| `conservation` | Conserver un état / une espèce | Natura 2000, espèce protégée |
| `restoration` | Restaurer un écosystème dégradé | Reconstitution post-tempête |
| `carbon_sequestration` | Séquestrer du carbone | Plantation, gestion carbone |
| `water_protection` | Protéger la ressource en eau | Zones humides, ripisylves |
| `soil_protection` | Protéger les sols | Anti-érosion, fertilité |
| `recreation` | Fonction récréative / sociale | Accueil du public, paysage |
| `research` | Objectif scientifique | Suivi long terme, expérimentation |
| `regulatory` | Conformité réglementaire | Code forestier, Natura 2000 |
| `other` | Autre objectif | (à préciser dans `name`) |

### 3.21 Enum `constraint_type` (Constraint)

| Valeur | Description | Exemple |
|---|---|---|
| `regulatory` | Contrainte réglementaire | Natura 2000, arrêté préfectoral, Code forestier |
| `budget` | Contrainte budgétaire | Coût d'intervention, budget annuel |
| `accessibility` | Accessibilité du site | Pente, distance, route, saison |
| `weather` | Contrainte météorologique | Pluie, vent, gel, fenêtre de travail |
| `equipment` | Matériel indisponible ou inadapté | Débardage, scie, LiDAR |
| `ecological` | Contrainte écologique | Sensibilité du sol, période de reproduction |
| `temporal` | Contrainte temporelle | Délai, saisonnalité, urgence |
| `social` | Contrainte sociale / acceptabilité | Opposition locale, usage traditionnel |
| `technical` | Contrainte technique | Précision GPS, résolution satellite |
| `other` | Autre contrainte | (à préciser dans `name`) |

### 3.22 Enum `scenario_subtype` (Scenario — enrichissement)

Enrichissement du type Scenario (57) pour spécialiser les scénarios
climatiques qui reviennent partout dans GSIE (RCP, SSP, DRIAS).

| Valeur de `scenario_type` | `scenario_subtype` | Description |
|---|---|---|
| `climatic` | `rcp_2.6` | RCP 2.6 — réchauffement limité (+1.5-2°C) |
| `climatic` | `rcp_4.5` | RCP 4.5 — réchauffement modéré (+2-3°C) |
| `climatic` | `rcp_8.5` | RCP 8.5 — réchauffement sévère (+4-5°C) |
| `climatic` | `ssp1_2.6` | SSP1-2.6 — développement durable |
| `climatic` | `ssp3_7.0` | SSP3-7.0 — rivalité régionale |
| `climatic` | `ssp5_8.5` | SSP5-8.5 — développement basé sur énergies fossiles |
| `climatic` | `drias_2020` | DRIAS 2020 — downscaled France |
| `sylvicultural` | `clear_cut` | Coupe rase |
| `sylvicultural` | `selective_thinning` | Éclaircie sélective |
| `sylvicultural` | `shelterwood` | Coupe d'abri |
| `sylvicultural` | `coppice` | Taillis |
| `management` | `no_intervention` | Non-intervention (libre évolution) |
| `management` | `adaptive` | Gestion adaptative |
| `disturbance` | `wildfire` | Incendie |
| `disturbance` | `storm` | Tempête |
| `disturbance` | `pest_outbreak` | Épidémie de ravageurs |
| `baseline` | `current_conditions` | Conditions actuelles (référence) |

> Le champ `scenario_subtype` est ajouté au type Scenario (57). C'est un
> champ optionnel qui spécialise `scenario_type`. Pas un nouveau type.

---

## 3.23 Relation Observation ↔ Assertion

Une confusion potentielle existe entre `Observation` (type 14, acte
d'observer qui produit des `Result`) et `Assertion` avec
`claim_kind=observation` (type 9, affirmation issue d'une mesure). La
distinction est la suivante :

| Aspect | Observation (type 14) | Assertion claim_kind=observation (type 9) |
|---|---|---|
| Nature | Événement empirique — « j'ai mesuré X avec l'instrument Y » | Affirmation scientifique — « X = 32 cm (source: ma mesure) » |
| Porte | `sampling_effort`, `method`, `instrument`, `temporal_context` | `claim_kind`, `lifecycle_status`, `evidence_assessment`, `citations` |
| Produit | `Result` (valeur brute + incertitude) | Rien (c'est un nœud terminal du graphe de connaissances) |
| Versionnée | Non (l'acte est immuable) | Oui (via `Revision`) |

**Règle de passage** : une `Observation` dont le `Result` est validé
génère une `Assertion` avec `claim_kind=observation` qui référence
l'`Observation` via un `AssertionParticipant` (role=context). Cette
assertion entre dans le graphe de connaissances, est évaluée par
l'Evidence Engine, et peut être citée par d'autres assertions.

```
[Observation] --produit--> [Result]
      |
      | (validation Evidence Engine)
      v
[Assertion claim_kind=observation]
      |-- participant (role=context) --> [Observation]
      |-- participant (role=subject)  --> [Resource mesuré]
      |-- evidence_assessment         --> [EvidenceAssessment level=B]
      |-- citation                    --> [Source + locator]
```

**Cas particulier `claim_kind=absence`** : une `Observation` avec
`Result.value_type='absence'` génère une `Assertion` avec
`claim_kind=absence`. L'effort d'échantillonnage (`sampling_effort`)
est porté par l'`Observation` et référencé par l'`Assertion` via le
participant context.

---

## 4. Graphe logique des relations

Les relations entre entités du noyau ne sont pas des arêtes Neo4j mais
des **Assertions** (`claim_kind=relation`) avec des
**AssertionParticipant** (sujet, objet, contexte). Cela unifie le graphe
de connaissances et le graphe ontologique : une relation EST une
assertion, avec son niveau de preuve, ses citations et son historique.

### 4.1 Quatre graphes logiques

| Graphe | Contenu | Support |
|---|---|---|
| Ontologique | Concepts, vocabulaires, hiérarchies | Tables `concept`, `controlled_term` |
| Des assertions | Assertions + participants + qualificateurs + citations + evidence | Tables `assertion`, `assertion_participant`, `assertion_qualifier`, `citation`, `evidence_assessment` |
| Des observations | Observations + results + incertitudes + méthodes | Tables `observation`, `result`, `uncertainty`, `method` |
| De provenance | Activities + ProvEntities + Agents + lineage | Tables `activity`, `prov_entity`, `agent` |

### 4.2 Traversée et requêtes

Les requêtes de traversée (toutes les assertions liées à `Quercus
robur`) se font en SQL sur les tables `assertion` + `assertion_participant`
+ `entity`. Pour les traversées profondes (multi-sauts), Apache AGE
(extension PostgreSQL) est évalué par benchmark dès la Vague 1 (ADR-003).
Neo4j est différé et sera adopté uniquement si AGE ne passe pas le
seuil mesuré.

---

## 5. Knowledge Evolution — GSIE Temporal & Provenance Engine

GSIE ne versionne pas des lignes SQL — il fait **évoluer des
connaissances scientifiques**. Le versioning est implémenté par un
**moteur métier intégré** (le GSIE Temporal & Provenance Engine), pas
par une extension PostgreSQL. C'est un changement philosophique
fondamental par rapport à la v6.1 qui utilisait `temporal_tables`.

### 5.1 Les cinq concepts

| Concept | Type | Rôle |
|---|---|---|
| **Revision** | 29 (enrichi) | Chaque ressource a des révisions explicites, append-only, justifiées, chaînées, bitemporelles, liées à PROV-O |
| **Validity** | (champs sur Revision) | Bitemporel métier : `valid_time` (quand c'est vrai dans le monde) + `transaction_time` (immuable, quand le système l'a enregistré) |
| **Snapshot** | 30 (enrichi) | Reconstruction de l'état complet d'une ressource à une date donnée (champs + relations + qualifiers + evidence en JSONB) |
| **ResourceDiff** | 61 (nouveau) | Différence explicite entre deux Revisions — ce qui a changé, champ par champ |
| **Provenance** | 20 (Activity) | Chaque Revision est liée à une Activity PROV-O (qui, quand, comment, à partir de quelles preuves) |

### 5.2 Cycle de vie d'une connaissance

```
Concept / Assertion / Observation / Dataset / Model…
  ↓
Revision 1 (création)
  ↓
Revision 2 (correction — justifiée, diff explicite)
  ↓
Revision 3 (validation — Evidence Engine évalue, level=B)
  ↓
Revision 4 (publication — lifecycle_status=accepted)
  ↓
Revision 5 (superseded — nouvelle revision plus précise)
  ↓
(l'ancienne reste conservée — CON-010, jamais supprimée)
```

Chaque transition est un événement traçable. Une EvidenceAssessment
peut évaluer une revision spécifique. Une Decision référence les
revisions qu'elle utilisait au moment du choix.

### 5.3 Bitemporalité métier

- **valid_time** : période où l'information est scientifiquement
  valable (ex. « cette observation a été faite le 2024-06-15 »)
- **transaction_time** : quand le système l'a enregistré (immuable,
  ex. « GSIE a enregistré cette observation le 2024-06-16 14:32:00 »)

Implémenté en **SQL métier** (colonnes sur Revision), pas par
extension. Le MVCC PostgreSQL garantit l'immutabilité du
transaction_time (une Revision est insert-only, jamais UPDATEd).
Enforce par trigger BEFORE UPDATE/DELETE qui lève une exception.

### 5.4 Reconstruction historique

```sql
-- Que savait-on sur le chêne sessile au 2024-06-15 ?
SELECT * FROM revision
WHERE target_id = ?  -- UUID du concept Quercus_petraea
  AND transaction_time <= '2024-06-15'
ORDER BY version DESC
LIMIT 1;
-- → retourne la dernière revision connue à cette date
```

Pour reconstruire l'état complet (champs + relations + qualifiers) :
utiliser le Snapshot associé, ou reconstruire depuis la Revision +
ses AssertionParticipants + AssertionQualifiers.

### 5.5 Pourquoi pas temporal_tables ?

`temporal_tables` (ou pgMemento) résout le versioning générique, mais :

| Besoin GSIE | temporal_tables | Temporal Engine |
|---|---|---|
| Bitemporel (valid + transaction) | Oui | Oui |
| Revision justifiée (pourquoi on révise) | Non | **Oui** |
| Lien Revision ↔ EvidenceAssessment | Non | **Oui** |
| Lien Revision ↔ Decision | Non | **Oui** |
| Diff explicite entre revisions | Non (diff JSONB implicite) | **Oui** (ResourceDiff) |
| Snapshot reproductible (ModelRun) | Non | **Oui** |
| Intégration PROV-O native | Non | **Oui** (Activity) |
| Cycle de vie scientifique (draft→accepted→superseded) | Non | **Oui** (lifecycle_status) |

Le Temporal Engine demande plus de code, mais il **comprend la
sémantique scientifique** — c'est la différence entre historiser une
ligne et représenter l'évolution d'une connaissance.

### 5.6 Implémentation

Voir ADR-002 (GSIE Temporal & Provenance Engine). Le moteur est
implémenté en Python (`TemporalEngine` class) + SQL (triggers
append-only, index) en Vague 1. Il a ses propres tests, comme
l'Evidence Engine et le Knowledge Engine.

---

## 6. Schéma conceptuel des tables principales

### 6.1 Table racine `resource`

```sql
CREATE TABLE resource (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type         VARCHAR(64) NOT NULL,  -- discriminant (entity, assertion, observation...)
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    gsie_id      VARCHAR(32) UNIQUE  -- identifiant citable GSIE-XXX-XXXXXXXX
);
```

### 6.2 Tables des 73 types (class-table inheritance)

Chaque type a sa propre table avec `id` comme PK ET FK vers
`resource(id)`. Exemple pour `assertion` :

```sql
CREATE TABLE assertion (
    id                   UUID PRIMARY KEY REFERENCES resource(id),
    claim_kind           VARCHAR(32) NOT NULL,  -- enum §3.3
    lifecycle_status     VARCHAR(32) NOT NULL DEFAULT 'draft',  -- enum §3.4
    predicate_id         UUID REFERENCES resource(id),  -- → Predicate
    spatial_scope_id     UUID REFERENCES resource(id),  -- → Place
    temporal_context_id  UUID REFERENCES resource(id),  -- → TemporalContext
    version              INTEGER NOT NULL DEFAULT 1
);
```

### 6.3 Tables de jonction

Les relations n:m utilisent des tables de jonction explicites, pas des
tableaux de FK (audit v5, point 7).

```sql
-- Participants d'une assertion (participant = n'importe quel Resource :
-- Concept, Instance, Place, Model, etc. — pas seulement Entity)
CREATE TABLE assertion_participant (
    assertion_id   UUID REFERENCES resource(id),
    participant_id UUID REFERENCES resource(id),
    role           VARCHAR(32) NOT NULL,  -- subject, object, context
    PRIMARY KEY (assertion_id, participant_id, role)
);

-- Citations d'une assertion
CREATE TABLE citation (
    id            UUID PRIMARY KEY REFERENCES resource(id),
    source_id     UUID REFERENCES resource(id),  -- → Source
    target_id     UUID REFERENCES resource(id),  -- → resource (assertion, observation...)
    citation_role VARCHAR(32) NOT NULL,
    locator       TEXT
);

-- Membres d'un ConflictCluster
CREATE TABLE conflict_cluster_member (
    cluster_id    UUID REFERENCES resource(id),
    assertion_id  UUID REFERENCES resource(id),
    PRIMARY KEY (cluster_id, assertion_id)
);
```

### 6.4 Index stratégiques

| Index | Table | Colonnes | Type |
|---|---|---|---|
| `idx_assertion_claim_kind` | assertion | claim_kind | B-tree |
| `idx_assertion_lifecycle` | assertion | lifecycle_status | B-tree |
| `idx_assertion_temporal` | assertion | temporal_context_id | B-tree |
| `idx_participant_entity` | assertion_participant | participant_id | B-tree |
| `idx_observation_subject` | observation | subject_id | B-tree |
| `idx_place_geometry` | place | geometry | GIST |
| `idx_temporal_valid` | temporal_context | valid_time_start, valid_time_end | B-tree |
| `idx_resource_type` | resource | type | B-tree |
| `idx_resource_gsie_id` | resource | gsie_id | B-tree (UNIQUE) |

---

## 7. Niveau B — Profils métier (différés Vague 2+)

Les profils spécialisent le noyau pour un domaine sans ajouter de types
noyau. Un profil ajoute des champs typés via une table de profil liée à
`resource(id)`.

| Profil | Domaine | Types de profil | Vague |
|---|---|---|---|
| Forestier | Sylviculture, dendrométrie | `Tree`, `Placette`, `Peuplement`, `TreeMeasurement`, `Martelage`, `ForestOperation` | 2 |
| Botanique | Flore | `PlantOccurrence`, `PhenologyRecord` | 2 |
| Pédologie | Sols | `SoilProfile`, `SoilHorizon` | 2 |
| Climat | Météo, climat | `WeatherSnapshot`, `ClimateProjection` | 2 |
| Hydrologie | Eau | `Watershed`, `HydroStation` | 3 |
| Faune | Vertébrés | `Animal`, `CameraTrap`, `TelemetryRecord` | 3 |
| Entomologie | Insectes | `Insect`, `Trap` | 3 |
| Mycologie | Champignons | `Fungus`, `Mycorrhiza` | 3 |
| Pathologie | Maladies | `Pathogen`, `Disease` | 3 |
| Incendies | Feu | `FireFront`, `FuelModel`, `IgnitionPoint` | 4 |
| Télédétection | Satellite, LiDAR | `STACItem` (projection C), `LiDARCloud` | 4 |

**Règle** : un profil ne peut pas être référencé par le noyau. Un profil
référence le noyau. Les profils sont définis dans leur moteur de domaine
respectif (`GSIE/ENGINES/<NOM>_ENGINE/`).

---

## 8. Niveau C — Projections standards (différées)

| Standard | Source | Type de projection | Quand |
|---|---|---|---|
| STAC | `Distribution` + `DataAsset` | Vue lecture | Vague 2 |
| OGC O&M / SOSA | `Observation` + `Result` + `FeatureOfInterest` | Vue lecture | Vague 2 |
| SensorThings | `Instrument` + `Observation` | Vue lecture | Vague 3 |
| Darwin Core | `Instance` (taxon) + `Observation` (occurrence) | Vue lecture | Vague 2 |
| PROV-O | `Activity` + `ProvEntity` + `Agent` | Vue lecture | Vague 1 |
| DCAT / GeoDCAT-AP | `Dataset` + `Distribution` | Vue lecture | Vague 2 |
| ISO 19115 | `Dataset` + `Place` | Vue lecture | Vague 2 |
| SKOS / OWL | `Concept` + `ControlledTerm` | Vue lecture | Vague 2 |

Les projections sont régénérables à partir du noyau (A). Elles ne sont
pas une source de vérité.

---

## 9. Niveau D — Infrastructure (spécifiée, implémentation différée)

### 9.1 ConnectorRegistry

Registre des connecteurs d'ingestion. Chaque connecteur a un manifest
avec `type` correspondant à `Distribution.access_method` (enum §3.7).

**Types de connecteurs** (audit F-P2-07) :
`rest_api`, `graphql_api`, `ogc_wms`, `ogc_wfs`, `ogc_wmts`, `ogc_wcs`,
`stac_api`, `file_downloader`, `file_importer`, `knowledge_extractor`.

Le type `knowledge_extractor` couvre l'extraction de connaissances depuis
des ressources non structurées (PDF, sites web, tableaux — ex.
ClimEssences, BioClimSol). Ces extracteurs sont des `Activity` PROV avec
`type='extraction'`.

### 9.2 OutboxEvent / ConsumerInbox

Spécifiés pour la cohérence transactionnelle (audit v5 point 3 :
`LISTEN/NOTIFY` seul n'est pas un bus durable). Implémentation différée
(ADR-005). Pattern : transactional outbox — les événements sont écrits
dans la même transaction que la donnée, puis relayés par un worker.

```sql
CREATE TABLE outbox_event (
    id           UUID PRIMARY KEY,
    aggregate_id UUID REFERENCES resource(id),
    event_type   VARCHAR(64) NOT NULL,
    payload      JSONB NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ  -- null si non traité
);
```

### 9.3 Object storage

Interface `put/get/delete` pour les `DataAsset` volumineux (rasters,
LAZ, NetCDF). MinIO en développement, S3 en production. Différé (ADR-006).

### 9.4 Knowledge Operating System — Orchestration

GSIE n'est pas une base de données — c'est un **Knowledge Operating
System** qui orchestre des moteurs hétérogènes (IA, physiques,
statistiques, SIG, métiers, climatiques, incendies, forestiers) pour
produire, évaluer et faire évoluer de la connaissance environnementale.

Le type `Capability` (60) permet aux moteurs de déclarer leurs capacités
(observe, predict, inventory, diagnose, simulate, recommend, correlate,
reason, validate, learn, extract, assess_evidence). L'orchestrateur lit
les Capabilities pour composer des pipelines.

**Document dédié** : l'orchestration complète (routing, pipelines,
séquenceurs, parallélisation, dépendances, failover, observabilité) est
spécifiée dans un document séparé — `GSIE/ARCHITECTURE/KNOWLEDGE_ORCHESTRATION.md`
(à rédiger en Vague 0). Ce document couvrira :

- Architecture de l'orchestrateur (réactif, event-driven)
- Déclaration de Capabilities par moteur (manifest)
- Composition de pipelines (DAG d'exécution)
- Séquençage et parallélisation des moteurs
- Gestion des dépendances (KnowledgeLineage → ordre d'exécution)
- Failover et résilience (moteur indisponible → repli)
- Observabilité (traces, métriques, SLO par moteur)
- Priorité et arbitrage (conflits entre moteurs)
- Scaling (horizontal, vertical, cloud burst)

---

## 10. Niveau E — Vision long terme (différée)

Non spécifiée dans cette version. Inclut :
- Jumeaux numériques territoriaux (alimentation Centre de Commandement UE5.8)
- Plugins dynamiques (exigent allowlist, signature, isolation)

> Note : les services écosystémiques sont désormais au noyau A via
> `EcosystemService` (type 59). Le Feature Store est partiellement couvert
> par `Feature` + `FeatureSet` (types 50-51) au noyau.

---

## 11. Sécurité et confidentialité

### 11.1 Row Level Security (RLS)

PostgreSQL RLS obligatoire sur les tables contenant des données
sensibles (observations d'espèces protégées, données privées). Les
politiques RLS référencent `SpatialDisclosurePolicy` et `AccessPolicy`.

### 11.2 Propagation des restrictions (audit F-P2-06)

Tout `Result` computed ou output de `ModelRun` hérite des restrictions
de ses inputs (via `ProvEntity.was_derived_from`). Règle : si un input
est `sensitive`, le dérivé est `sensitive` sauf documentation explicite
d'agrégation suffisante (ex. maille 10km).

### 11.3 Droit d'entraînement IA

`RightsStatement.ai_training_allowed` (bool) porte le droit
d'utiliser une source pour l'entraînement de modèles IA. Sans ce champ
à `true`, la source ne peut pas alimenter un pipeline d'entraînement.

---

## 12. Mapping depuis l'existant (migration)

### 12.1 KnowledgeObject 6 types → Assertion

| KnowledgeObject (livrable 302) | v6.1 |
|---|---|
| `type=concept` | `Concept` (type 3) — n'est plus une assertion |
| `type=relation` | `Assertion` avec `claim_kind=relation` |
| `type=regle` | `Assertion` avec `claim_kind=rule` |
| `type=seuil` | `Assertion` avec `claim_kind=threshold` |
| `type=modele` | `Assertion` avec `claim_kind=model` + `Model` (type 31) |
| `type=classification` | `Assertion` avec `claim_kind=classification` |
| `evidence_level` (champ direct) | `EvidenceAssessment` (type 13, multiple) |
| `source` (champ direct) | `Citation` (type 24) → `Source` (type 23) |
| `contenu` (dict libre) | `AssertionParticipant` + `AssertionQualifier` |
| `historique` (liste) | `Revision` (type 29) |
| `domaines_validite` (liste) | `AssertionQualifier` (key=domaine) |
| `conflits` (liste ConflitBibliographique) | `ConflictCluster` (type 42) |

### 12.2 Schéma PostgreSQL existant

Le schéma actuel (`knowledge_models.py` + migration 0001) définit des
tables `knowledge_objects`, `knowledge_history` et l'extension AGE. La
migration (ADR-004) transforme ces tables en `resource` + `assertion` +
`assertion_participant` + `assertion_qualifier` + `evidence_assessment` +
`citation`. Les 25 connaissances seed (livrable 308) sont migrées.

### 12.3 Code existant (engine.py in-memory)

Le `Knowledge Engine` actuel utilise `self._store: dict[UUID,
KnowledgeObject]`. La migration (Vague 0) remplace le store in-memory par
un repository PostgreSQL sur le schéma v6.2. Les 67 tests Rust de
l'Evidence Engine sont préservés (adaptateur Rust évalue + Python
enrichit — arbitrage T4).

---

## 13. Vagues d'implémentation

### Vague 0 — Gouvernance + RFC + ADR + audit migration (~2 semaines)

- RFC-0011 adoptée + DEC-000022 validée
- 6 ADR rédigés et validés
- Tests contractuels Evidence Engine (Rust → EvidenceAssessment)
- Contrats d'interface noyau ↔ profils ↔ API
- Audit de migration (écart engine.py ↔ knowledge_models.py ↔ v6.2)
- Résolution des 5 actions qualité Q1-Q5 (§17)

### Vague 1 — Noyau complet + Essence 360° (~4 semaines)

- **73 types implémentés dès le départ** (arbitrage T3 — pas de
  migration de schéma entre vagues)
- Schéma PostgreSQL + PostGIS + **GSIE Temporal & Provenance Engine** (Revision + Snapshot + ResourceDiff, ADR-002)
- Migration depuis le schéma actuel (ADR-004)
- Benchmark AGE (ADR-003) sur données réelles
- Tranche verticale : Fiche Essence 360° (chêne sessile, hêtre, pin
  maritime, douglas, sapin pectiné) — sur noyau seul (Concept +
  Assertion + Observation + Citation + EvidenceAssessment + ScaleContext
  + TraitDefinition + TraitValue + Correlation)
- Adaptateur Evidence Rust → EvidenceAssessment
- Types raisonnement (Question, Hypothesis, Recommendation, Decision,
  Scenario) : structures créées, alimentation différée Vague 2+
- Types IA (Feature, FeatureSet, Inference) : structures créées,
  alimentation différée Vague 2+
- EcosystemService : structure créée, vide
- **FAIR** : PersistentIdentifier (65) implémenté — DOI DataCite pour
  datasets, URI persistante `https://gsie.quintessences.fr/r/{id}` pour
  toute ressource, tombstone pour A2
- **RGPD** : Consent (63) + DataSubject (64) implémentés — API droit
  d'accès, anonymisation, audit log d'accès, registre de traitement
- **SOSA/SSN** : Sample (62) implémenté — mapping documenté §15.3
- **FAIR F3/F4** : endpoint de découverte (OGC API Records ou CSW)

### Vague 2+ — Profils métier + ingestion massive + raisonnement + interop

- Profils forestier, botanique, pédologie, climat (niveau B)
- Projections STAC, OGC, Darwin Core, EML, SOSA/SSN, ISO 19115 (niveau C)
- ConnectorRegistry + pipelines d'ingestion
- Outbox/Inbox (niveau D) si besoin asynchrone confirmé
- Alimentation des types raisonnement (Question → Hypothesis →
  Recommendation → Decision)
- Alimentation des types IA (Feature, FeatureSet, Inference)
- Phenomenon + EcologicalProcess : alimentation par Ignis, Forest Dynamics
- Capability : déclaration par les moteurs/apps, orchestration

### Vague 2 — Roadmap détaillée (P1 + P2 priorisés)

Issue de l'audit comparatif GSIE vs standards internationaux (FAIR,
CARE, SOSA/SSN, RO-Crate, DataONE, GBIF, Wikidata). Priorisation par
impact et dépendances.

#### P1 — Interopérabilité et robustesse (Vague 2, ~6 semaines)

| # | Action | Standard | Impact | Dépendance |
|---|---|---|---|---|
| V2-1 | **Projections Darwin Core** (occurrences) | GBIF, OBIS, iNaturalist | Interop faune/flore | Vague 1 |
| V2-2 | **Projections EML** (datasets écologiques) | DataONE, LTER, NEON | Métadonnées FAIR F2 | Vague 1 |
| V2-3 | **Projections STAC** (rasters, imagerie) | Element84, Planetary Computer | Interop satellitaire | Vague 1 |
| V2-4 | **Projection SOSA/SSN** (observations sémantiques) | W3C/OGC | Interop observations | Vague 1 (Sample 62) |
| V2-5 | **Projection ISO 19115/19139** (catalogue géo) | INSPIRE | Conformité réglementaire EU | Vague 1 |
| V2-6 | **Projection DCAT/GeoDCAT-AP** (catalogue data.gov.eu) | EU | Conformité EU | Vague 1 |
| V2-7 | **Web sémantique : RDF/JSON-LD** | W3C | FAIR I1, interop sémantique | Vague 1 |
| V2-8 | **SKOS pour vocabulaires contrôlés** | W3C | FAIR I2, mapping ENVO/GBIF/Wikidata | Vague 1 (ControlledTerm) |
| V2-9 | **Liens RDF typés** (owl:sameAs, skos:exactMatch) | W3C | FAIR I3 | V2-7, V2-8 |
| V2-10 | **RO-Crate** (packaging reproductibilité) | ResearchObject | Reproductibilité computationnelle | Vague 1 (Snapshot 30) |
| V2-11 | **Workflow scientifique** (CWL ou WDL) | Common Workflow Language | Reproductibilité ModelRun | Vague 1 (ModelRun 32) |
| V2-12 | **Conteneurs d'exécution** (Docker/Singularity) | OCI | Reproductibilité environnement | V2-11 |
| V2-13 | **SPARQL endpoint** | W3C | Requête fédérée, raisonnement DL | V2-7 |
| V2-14 | **Système d'alertes** (seuils, anomalies, notifications) | - | Critique pour Ignis, Diagnostic | Vague 1 |
| V2-15 | **CloudEvents** (event-driven standard) | CNCF | OutboxEvent standardisé | Vague 1 (OutboxEvent) |
| V2-16 | **Schema registry** (event versioning) | Confluent, Apicurio | Évolutivité événements | V2-15 |

#### P2 — Découverte, collaboration, gouvernance (Vague 3+, différé)

| # | Action | Standard | Impact | Dépendance |
|---|---|---|---|---|
| V3-1 | **Recherche full-text** (PostgreSQL FTS) | - | Découverte assertions | Vague 1 |
| V3-2 | **Recherche sémantique** (embeddings, pgvector) | - | Découverte par similarité | Vague 2 (IA) |
| V3-3 | **Faceted search** (filtres multi-dimensionnels) | - | UX découverte | Vague 1 |
| V3-4 | **Système d'annotation** (commentaires sur assertions) | W3C Web Annotation | Collaboration scientifique | Vague 1 |
| V3-5 | **Peer review interne** (review workflow) | - | Validation scientifique | V3-4 |
| V3-6 | **CARE principles** (données autochtones/patrimoniales) | GIDA | Gouvernance éthique | Vague 1 (Sensitivity 39) |
| V3-7 | **Internationalisation (i18n)** (labels multilingues) | W3C | Interop internationale | Vague 1 |
| V3-8 | **Data lifecycle** (retention, archivage, suppression) | - | Conformité RGPD + storage | Vague 1 (Consent 63) |
| V3-9 | **Backup/restore + disaster recovery** | - | Résilience | Vague 1 |
| V3-10 | **Partitioning temporel** (observations par année) | PostgreSQL | Performance | Vague 1 |
| V3-11 | **Sharding spatial** (observations par région) | PostgreSQL | Performance | Vague 1 |
| V3-12 | **Materialized views** (agrégats pré-calculés) | PostgreSQL | Performance | Vague 1 |
| V3-13 | **Caching Redis** (lectures fréquentes) | Redis | Performance | Vague 1 |
| V3-14 | **Audit log d'accès** (RGPD art. 30+32) | - | Conformité RGPD | Vague 1 |
| V3-15 | **DPIA** (analyse d'impact RGPD art. 35) | - | Conformité RGPD | Vague 0 |
| V3-16 | **Recommandation** (assertions pertinentes pour un contexte) | - | UX raisonnement | Vague 2 (IA) |
| V3-17 | **Dead letter queue** (events échoués) | - | Robustesse event-driven | V2-15 |
| V3-18 | **Event Sourcing** (capteurs temps réel) | - | Haute fréquence | Vague 2+ |
| V3-19 | **Apache Iceberg / Delta Lake** (Data Lake versionné) | - | DataAsset volumineux | Vague 2+ |
| V3-20 | **Notebook reproductible** (Jupyter + Binder) | - | Reproductibilité recherche | V2-10 |

---

## 14. Compteur de types et justification

**73 types au noyau** (v6.2). La v6.1 en comportait 42 ; la passe
écologique du Fondateur en a ajouté 18 (types 43-60), le Temporal Engine
1 (type 61 ResourceDiff), l'audit FAIR/RGPD/SOSA 4 (types 62-65 : Sample,
Consent, DataSubject, PersistentIdentifier), et la passe dynamiques
écologiques 8 (types 66-73 : Flow, ConfidenceGraph, Goal, Constraint,
KnowledgeLineage, Experiment, TerrainSession, EcologicalState). Chaque
type est justifié par :

| Catégorie | Types | Justification |
|---|---|---|
| Identité + référentiels | 8 (1-8) | Backbone taxonomique versionné + résolution d'identité cross-source |
| Assertions + connaissances | 5 (9-13) | Assertion unifiée + participants + qualificateurs + prédicats + évaluation de preuve |
| Observations + mesures | 6 (14-19) | Observation avec effort + Result avec absence + Method + Instrument + Uncertainty + Quality |
| Provenance + activités | 5 (20-24) | Activity PROV + ProvEntity + Agent + Source typée + Citation avec locator |
| Contextes | 4 (25-28) | Unit + Place + TemporalContext bitemporel + Media |
| Versionnement + Temporal Engine | 3 (29-30, 61) | Revision universelle append-only + Snapshot immuable + ResourceDiff explicite — cœur du GSIE Temporal & Provenance Engine (ADR-002) |
| Modèles | 3 (31-32, 41) | Model + ModelRun + ModelVersion (reproductibilité) |
| Datasets | 4 (33-36) | Dataset + DatasetVersion + DataAsset + Distribution (6 niveaux d'ingestion) |
| Confidentialité | 4 (37-40) | Rights + Access + Sensitivity + SpatialDisclosure (scénario D, axe 7) |
| Conflits | 1 (42) | ConflictCluster (scénario B, S-3) |
| **Échelle** | 1 (43) | ScaleContext — toute corrélation écologique dépend de l'échelle (v6.2) |
| **Phénomènes + processus** | 2 (44-45) | Phenomenon (sécheresse, scolytes) + EcologicalProcess (photosynthèse, croissance) — distincts d'Entity, Observation et PROV Activity (v6.2) |
| **Typologie des relations** | 1 (46) | RelationType — méta-classification des prédicats (causal, trophic, etc.) (v6.2) |
| **Échantillonnage** | 1 (47) | SamplingEvent — hiérarchie campagne → placettes → observations (v6.2) |
| **Traits fonctionnels** | 2 (48-49) | TraitDefinition + TraitValue — transversaux, comparables cross-species (v6.2) |
| **IA / ML** | 3 (50-52) | Feature + FeatureSet + Inference — l'IA est un citoyen de premier ordre (v6.2) |
| **Raisonnement** | 5 (53-57) | Question + Hypothesis + Decision + Recommendation + Scenario — GSIE est un moteur de raisonnement (v6.2) |
| **Corrélations** | 1 (58) | Correlation — objet de connaissance versionné et évaluable (v6.2) |
| **Services écosystémiques** | 1 (59) | EcosystemService — type vide, implémentation différée (v6.2) |
| **Orchestration** | 1 (60) | Capability — déclaration des capacités moteurs/apps pour l'orchestrateur (v6.2) |
| **Échantillon physique** | 1 (62) | Sample — échantillon matériel prélevé, mapping SOSA/SSN `sosa:Sample` (v6.2 audit FAIR) |
| **RGPD** | 2 (63-64) | Consent + DataSubject — conformité RGPD art. 6 + 9.2.j (recherche) (v6.2 audit FAIR) |
| **Identifiants persistants** | 1 (65) | PersistentIdentifier — DOI, PURL, ORCID, GBIF, Wikidata (FAIR F1) (v6.2 audit FAIR) |
| **Flux écologiques** | 1 (66) | Flow — carbone, eau, nutriments, énergie, graines, gènes, pathogènes (v6.2 dynamiques) |
| **Graphe de confiance** | 1 (67) | ConfidenceGraph — propagation d'incertitude à travers les dépendances de connaissance (v6.2 dynamiques) |
| **Objectifs + contraintes** | 2 (68-69) | Goal + Constraint — objectifs de gestion + contraintes qui limitent la faisabilité (v6.2 dynamiques) |
| **Lignage de connaissance** | 1 (70) | KnowledgeLineage — DAG explicite de production de connaissance (v6.2 dynamiques) |
| **Expériences scientifiques** | 1 (71) | Experiment — série de ModelRuns avec cadre de comparaison (v6.2 dynamiques) |
| **Missions terrain** | 1 (72) | TerrainSession — mission GeoSylva (météo, GPS, matériel, martelage, inventaire) (v6.2 dynamiques) |
| **État écologique** | 1 (73) | EcologicalState — état synthétique de santé/vitalité/risque/résilience (v6.2 dynamiques) |

**Champs ajoutés (pas de nouveaux types)** :
- `Assertion.rule_subtype` (enum §3.14) — typologie des règles (inference, scientific, business, regulatory)
- `Dataset.purpose` (enum §3.15) — remplace TrainingDataset/EvaluationDataset par un champ (plus DRY)

**Stratégie de réduction si sur-ingénierie confirmée** : RightsStatement
et AccessPolicy pourraient migrer en infrastructure (D) plutôt que noyau
(A) si l'usage montre qu'ils ne sont nécessaires qu'au niveau
infrastructure. SensitivityClassification et SpatialDisclosurePolicy
pourraient migrer en profil faune (B) si les essences forestières n'en
ont pas besoin. EcosystemService (59) pourrait rester vide
indéfiniment. Ces décisions sont différées après la Vague 1.

---

## 15. Conformité constitutionnelle

| Loi | Application dans le métamodèle |
|---|---|
| CON-001 (décideur humain) | `Decision` (type 55) = acte humain, `Recommendation` (type 56) = output moteur contournable |
| CON-002 (science avant tout) | Toute assertion porte un `EvidenceAssessment` (A-F) |
| CON-003 (connaissance avant code) | Le métamodèle précède l'implémentation |
| CON-005 (traçabilité) | `Activity` + `ProvEntity` + `Agent` + `Citation` avec locator |
| CON-010 (historique) | `Revision` append-only + `TemporalContext` bitemporel |
| S-1 (sources catégorisées) | `Source` avec `source_nature` (6 valeurs) |
| S-2 (niveau de preuve) | `EvidenceAssessment` multiples, pas de score global |
| S-3 (conflits documentés) | `ConflictCluster` + `Citation` role=contradicting |
| S-5 (incertitude explicite) | `Uncertainty` + `AssertionQualifier` (domaine de validité) |
| S-7 (patrimoine versionné) | `Concept` stable + `ConceptVersion` par release + `Revision` |
| **v6.2 : multi-échelle** | `ScaleContext` (type 43) — toute assertion/corrélation/processus est valide à une échelle donnée |
| **v6.2 : raisonnement** | `Question` → `Hypothesis` → `Recommendation` → `Decision` — chaîne de raisonnement explicite |
| **v6.2 : IA traçable** | `Feature` + `FeatureSet` + `Inference` — l'IA produit des objets traçables, pas des boîtes noires |
| **v6.2 : phénomènes** | `Phenomenon` + `EcologicalProcess` — représentation explicite du vivant, pas seulement de mesures |
| **v6.2 : Knowledge Evolution** | `Revision` (29) + `Snapshot` (30) + `ResourceDiff` (61) + PROV-O — versionnement métier intégré, pas d'extension externe (ADR-002) |
| **v6.2 : RGPD** | `Consent` (63) + `DataSubject` (64) — conformité art. 6 + art. 9.2.j (recherche) |
| **v6.2 : FAIR F1** | `PersistentIdentifier` (65) — DOI, PURL, ORCID, GBIF, Wikidata |
| **v6.2 : SOSA/SSN** | `Sample` (62) — mapping W3C/OGC `sosa:Sample` |
| **v6.2 : flux écologiques** | `Flow` (66) — carbone, eau, nutriments, énergie, graines, gènes, pathogènes |
| **v6.2 : confiance globale** | `ConfidenceGraph` (67) — propagation d'incertitude à travers les dépendances |
| **v6.2 : objectifs + contraintes** | `Goal` (68) + `Constraint` (69) — orientent et limitent les décisions |
| **v6.2 : lignage DAG** | `KnowledgeLineage` (70) — chaîne explicite A → B → Recommendation → Decision |
| **v6.2 : expériences** | `Experiment` (71) — série de ModelRuns avec comparaison et publication |
| **v6.2 : missions terrain** | `TerrainSession` (72) — mission GeoSylva (météo, GPS, matériel, martelage) |
| **v6.2 : état écologique** | `EcologicalState` (73) — santé, vitalité, risque, résilience synthétiques |
| **v6.2 : Knowledge OS** | `Capability` (60) + document orchestration §9.4 — GSIE est un système d'exploitation de la connaissance |

### 15.1 Conformité FAIR (Findable, Accessible, Interoperable, Reusable)

Les FAIR Guiding Principles (Wilkinson et al. 2016, Scientific Data)
sont le standard international pour les données scientifiques. Horizon
Europe et EOSC l'exigent. Audit des 15 principes :

| Principe | Description | Statut GSIE v6.2 | Action |
|---|---|---|---|
| **F1** | Identifiant persistant global | **Partiel** — `PersistentIdentifier` (65) défini ; `gsie_id` interne existe | Vague 1 : enregistrer DOI pour datasets via DataCite ; URI persistante `https://gsie.quintessences.fr/r/{id}` pour toute ressource |
| **F2** | Métadonnées riches | **Partiel** — Source, Dataset, Citation | Vague 1 : compléter avec EML pour datasets écologiques |
| **F3** | Métadonnées indexées dans ressource searchable | **Manquant** | Vague 1 : endpoint OGC API Records ou CSW pour catalogue |
| **F4** | Ressource searchable | **Manquant** | Vague 1 : API de découverte (full-text + faceted) |
| **A1** | Récupérable par ID via protocole standard | **Partiel** — API REST | Vague 1 : garantir `GET /api/v1/resources/{gsie_id}` retourne toujours la ressource, même si supprimée (tombstone) |
| **A1.1** | Protocole ouvert, gratuit, universel | **OK** — HTTP REST | - |
| **A1.2** | Authentification/autorisation | **OK** — JWT (DIR-0008) | - |
| **A2** | Métadonnées accessibles même si donnée supprimée | **Manquant** | Vague 1 : politique de tombstone (métadonnées conservées, donnée supprimée/anonymisée) |
| **I1** | Langage formel de représentation | **Partiel** — SQL | Vague 2 : exposition RDF/JSON-LD (projection niveau C) |
| **I2** | Vocabulaires FAIR | **Partiel** — ControlledTerm interne | Vague 2 : SKOS pour vocabulaires + mapping vers ENVO, GBIF, Wikidata |
| **I3** | Références qualifiées vers autres (meta)data | **Partiel** — Citation | Vague 2 : liens RDF typés (owl:sameAs, skos:exactMatch) |
| **R1** | Attributs précis et pertinents | **OK** — 73 types avec champs riches | - |
| **R1.1** | Licence claire et accessible | **OK** — RightsStatement | Vague 1 : licence par défaut sur tous les datasets |
| **R1.2** | Provenance | **OK** — PROV-O (Activity, ProvEntity, Agent) + Revision | - |
| **R1.3** | Standards communautaires | **Partiel** — mentionnés, pas implémentés | Vague 2 : Darwin Core (occurrences), EML (datasets), STAC (rasters), SOSA/SSN (observations) |

**Score FAIR v6.2** : 4/15 OK, 7/15 partiel, 4/15 manquant.
**Cible Vague 1** : 10/15 OK, 5/15 partiel, 0/15 manquant.
**Cible Vague 2** : 15/15 OK.

### 15.2 Conformité RGPD (Règlement Général sur la Protection des Données)

GSIE stocke des données personnelles : noms de forestiers (Agent
type=person), géolocalisation d'observations (Place), décisions
(Decision.decided_by). Le RGPD est obligatoire en France.

| Obligation RGPD | Article | Implémentation GSIE v6.2 | Statut |
|---|---|---|---|
| Base légale du traitement | Art. 6 | `Consent.legal_basis` (enum §3.17, 7 valeurs) | **OK** |
| Consentement explicite | Art. 6.1.a + 7 | `Consent` (type 63) avec scope, durée, retrait | **OK** |
| Dérogation recherche | Art. 9.2.j | `legal_basis=research` | **OK** |
| Droit d'accès | Art. 15 | API `GET /api/v1/personal-data/{data_subject_id}` | Vague 1 |
| Droit de rectification | Art. 16 | `Revision` (correction via Temporal Engine) | **OK** |
| Droit à l'oubli | Art. 17 | `DataSubject.anonymized=true` + anonymisation des données liées | Vague 1 |
| Droit à la portabilité | Art. 20 | Export JSON-LD des données personnelles | Vague 2 |
| Minimisation | Art. 5.1.c | `Consent.scope` (full, anonymized_only, aggregated_only) | **OK** |
| Registre de traitement | Art. 30 | Document de registre (à créer en Vague 0) | Vague 0 |
| Notification de violation | Art. 33 | OutboxEvent + alerting | Vague 2 |
| Audit log d'accès | Art. 30 + 32 | Séparé du versioning métier — table `access_log` | Vague 1 |
| DPIA (analyse d'impact) | Art. 35 | Document DPIA (à créer en Vague 0 si risque élevé) | Vague 0 |

### 15.3 Mapping SOSA/SSN (W3C/OGC)

SOSA (Sensor, Observation, Sample, and Actuator) est le standard
W3C/OGC pour les observations sémantiques.

| Concept SOSA/SSN | Type GSIE | Notes |
|---|---|---|
| `sosa:Sensor` | Instrument (16) | - |
| `sosa:Observation` | Observation (14) | - |
| `sosa:Procedure` | Method (16) | - |
| `sosa:Sample` | **Sample (62)** | Nouveau v6.2 |
| `sosa:Sampling` | SamplingEvent (47) | - |
| `sosa:FeatureOfInterest` | Observation.subject_id → resource.id | - |
| `sosa:observedProperty` | Result + TraitValue (49) | Propriété observée = Result ou Trait |
| `sosa:hasResult` | Result (15) | - |
| `sosa:madeBySensor` | Observation.instrument_id → Instrument | - |
| `sosa:usedProcedure` | Observation.method_id → Method | - |
| `sosa:hasSample` | SamplingEvent → Sample | Via `sample.sampling_event_id` |
| `sosa:isSampleOf` | Sample.subject_id → resource.id | - |
| `ssn:Property` | TraitDefinition (48) | - |
| `ssn:hasProperty` | TraitValue → TraitDefinition | - |
| `ssn:observationValue` | TraitValue.value_numeric / value_term | - |

**Projection SOSA/SSN** : Vague 2 (niveau C). Le mapping est
documenté ici pour garantir que les types GSIE sont compatibles.

---

## 16. Documents de référence

| Document | Rôle | Statut |
|---|---|---|
| RFC-0011 | Justification des choix + superseding | Proposé |
| DEC-000022 | Décision d'adoption | Proposé |
| ADR-001 | Racine Resource (class-table inheritance) | Proposé |
| ADR-002 | GSIE Temporal & Provenance Engine (Revision + Snapshot + ResourceDiff + PROV-O) — remplace temporal_tables | Proposé |
| ADR-003 | AGE benchmark (stratégie d'évaluation) | Proposé |
| ADR-004 | Migration schéma (knowledge_objects → v6.1) | Proposé |
| ADR-005 | Outbox/Inbox (transactional outbox) | Proposé |
| ADR-006 | Object storage (MinIO/S3) | Proposé |
| Livrable 306 | Evidence Framework (A-F) | Validated (non supersédé) |
| Livrable 305 | Dataset Catalog (29 datasets) | Validated (non supersédé) |
| Livrable 308 | Knowledge Base Seed (25 connaissances) | Validated (non supersédé, à migrer) |

---

## 17. Actions de suivi Vague 0 (passe qualité)

Les points suivants ont été identifiés lors de la passe qualité du
2026-07-15. Ils ne bloquent pas l'adoption mais doivent être résolus
pendant la Vague 0 (avant implémentation).

| # | Point | Action | Priorité |
|---|---|---|---|
| Q1 | **Exemple end-to-end manquant** | Rédiger un exemple concret complet : « chêne sessile adapté au pH 4.5-6.0, source Rameau 2018, preuve B » avec toutes les tables impliquées et leurs valeurs. Valider la structure par cet exemple. | Haute |
| Q2 | **Essence 360° sans profil forestier** | La tranche verticale Vague 1 prévoit Essence 360° mais les profils forestiers (Tree, Placette, Peuplement) sont différés en Vague 2+. Résoudre : soit définir un profil forestier minimal en Vague 1, soit faire Essence 360° sur le noyau seul (Concept + Assertion + Observation + Citation + EvidenceAssessment, sans Instance d'arbre individuel). | Haute |
| Q3 | **ConceptVersion.fusions (FusionEntry)** | Le champ `fusions` référence un type `FusionEntry` qui n'est pas défini dans les 73 types. Spécifier : soit un type JSONB structuré (liste de `{old_concept_id, new_concept_id, date}`), soit une table de jonction `concept_fusion`. | Moyenne |
| Q4 | **Resource.type vs Entity.type** | Deux champs `type` avec des sémantiques différentes (discriminant de table vs sous-type d'entité). Renommer `Entity.type` en `Entity.subtype` pour lever l'ambiguïté. | Moyenne |
| Q5 | **Temporal Engine : spécification interface + tests** | Spécifier l'interface du `TemporalEngine` Python (create_revision, get_state_as_of, compute_diff) + tests unitaires avant implémentation Vague 1. Valider que le pattern Revision + triggers SQL append-only couvre tous les cas d'usage bitemporel. | Haute |

---

> Ce métamodèle est **Proposé**. Il n'est adopté qu'après validation de
> RFC-0011 et DEC-000022 par le Fondateur. Aucune implémentation ne
> démarre avant le gate documentaire de la Vague 0.

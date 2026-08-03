# RFC-0030 — Mapping Treekipedia → métamodèle v6.2

| Champ | Valeur |
|---|---|
| **Identifiant** | RFC-0030 |
| **Statut** | Draft |
| **Auteur** | GLM 5.2 High (Devin CLI) |
| **Date** | 2026-07-31 |
| **Décision liée** | `DEC-000040` |
| **Motivation** | GSIE dispose de 25 connaissances validées ; Treekipedia (MIT) en a 67 743. L'ingestion nécessite un mapping formel des 121 champs Treekipedia vers les 73 types noyau du métamodèle v6.2. |

## Problème

Treekipedia utilise un schéma relationnel PostgreSQL avec 121 champs par espèce, organisés en paires `_human`/`_ai` pour la plupart des attributs écologiques et morphologiques. GSIE utilise un métamodèle v6.2 avec 73 types noyau (`entity`, `assertion`, `source`, `revision`, etc.) et un système de niveaux de preuve A-F.

Sans mapping formel, l'ingestion produirait des données incohérentes avec la Constitution (GSIE-CON-005 traçabilité, S-3 conflits bibliographiques, RFC-0014 garde-fou anti-invention).

## Solution proposée

### 1. Mapping des champs taxonomiques (12 champs)

| Champ Treekipedia | Type noyau v6.2 | Attributs |
|---|---|---|
| `taxon_id` | `entity` | `kind=species`, `external_ref=treekipedia:taxon_id` |
| `species_scientific_name` | `entity` | `label` (nom scientifique accepté) |
| `subspecies` | `entity` | `rank=subspecies` |
| `specific_epithet` | `entity` | `epithet` |
| `accepted_scientific_name` | `entity` | `accepted_name` |
| `synonyms` | `assertion` | `claim_kind=taxonomic_synonym` |
| `family` | `entity` | `lineage.family` |
| `genus` | `entity` | `lineage.genus` |
| `class` | `entity` | `lineage.class` |
| `taxonomic_order` | `entity` | `lineage.order` |
| `common_name` | `assertion` | `claim_kind=common_name`, `evidence_level=E` |
| `common_countries` | `assertion` | `claim_kind=common_name_locale` |

### 2. Mapping des champs écologiques (dual _human/_ai)

**Règle générale** :
- Champ `_human` présent → `evidence_level = E` (Expert) ou `B` (si source peer-reviewed/référentiel)
- Champ `_ai` uniquement → `evidence_level = D` (Hypothèse), `methodology = "LLM extraction via Treekipedia"`
- Les deux présents → `evidence_level = min(human, ai)`, note dans `provenance`

| Champ Treekipedia | Type noyau v6.2 | `claim_kind` |
|---|---|---|
| `general_description_human`/`_ai` | `assertion` | `description` |
| `ecological_function_human`/`_ai` | `assertion` | `ecological_role` |
| `elevation_ranges_human`/`_ai` | `assertion` | `elevation_range` |
| `compatible_soil_types_human`/`_ai` | `assertion` | `soil_preference` |
| `habitat_human`/`_ai` | `assertion` | `habitat` |
| `native_adapted_habitats_human`/`_ai` | `assertion` | `native_habitat` |
| `agroforestry_use_cases_human`/`_ai` | `assertion` | `agroforestry_use` |
| `growth_form_human`/`_ai` | `assertion` | `morphological_trait.growth_form` |
| `leaf_type_human`/`_ai` | `assertion` | `morphological_trait.leaf_type` |
| `deciduous_evergreen_human`/`_ai` | `assertion` | `morphological_trait.leaf_persistence` |
| `flower_color_human`/`_ai` | `assertion` | `morphological_trait.flower_color` |
| `fruit_type_human`/`_ai` | `assertion` | `morphological_trait.fruit_type` |
| `bark_characteristics_human`/`_ai` | `assertion` | `morphological_trait.bark` |
| `maximum_height_human`/`_ai` | `assertion` | `morphological_trait.max_height` (numeric) |
| `maximum_diameter_human`/`_ai` | `assertion` | `morphological_trait.max_diameter` (numeric) |
| `lifespan_human`/`_ai` | `assertion` | `morphological_trait.lifespan` |
| `maximum_tree_age_human`/`_ai` | `assertion` | `morphological_trait.max_age` (numeric) |
| `conservation_status_human`/`_ai` | `assertion` | `conservation_status` |
| `stewardship_best_practices_human`/`_ai` | `assertion` | `stewardship_practice` |
| `planting_recipes_human`/`_ai` | `assertion` | `planting_recipe` |
| `pruning_maintenance_human`/`_ai` | `assertion` | `pruning_practice` |
| `disease_pest_management_human`/`_ai` | `assertion` | `disease_pest_management` |
| `fire_management_human`/`_ai` | `assertion` | `fire_management` |
| `cultural_significance_human`/`_ai` | `assertion` | `cultural_significance` |
| `climate_tolerance_ai` | `assertion` | `climate_tolerance` |
| `tolerances_ai` | `assertion` | `tolerances` |
| `associated_species_ai` | `assertion` | `associated_species` |
| `propagation_methods_ai` | `assertion` | `propagation_method` |
| `timber_value_ai` | `assertion` | `timber_value` |
| `non_timber_products_ai` | `assertion` | `non_timber_product` |
| `nutritional_caloric_value_ai` | `assertion` | `nutritional_value` |
| `etymology_ai` | `assertion` | `etymology` |
| `identification_features_ai` | `assertion` | `identification_feature` |

### 3. Mapping des champs géospatiaux

| Champ Treekipedia | Type noyau v6.2 | `claim_kind` |
|---|---|---|
| `countries_native` | `assertion` | `distribution.native` |
| `countries_invasive` | `assertion` | `distribution.invasive` |
| `countries_introduced` | `assertion` | `distribution.introduced` |
| `ecoregions` | `assertion` | `ecoregion` |
| `biomes` | `assertion` | `biome` |
| `forest_type` | `assertion` | `forest_type` |
| `wetland_type` | `assertion` | `wetland_type` |
| `urban_setting` | `assertion` | `urban_setting` |
| `successional_stage` | `assertion` | `successional_stage` |
| `forest_layers` | `assertion` | `forest_layer` |
| `Present_Intact_Forest` | `assertion` | `intact_forest_presence` |
| `climate_change_vulnerability` | `assertion` | `climate_vulnerability` |

### 4. Mapping des champs métadonnées

| Champ Treekipedia | Type noyau v6.2 | Usage |
|---|---|---|
| `data_sources` | `source` | Liste des sources d'origine (GBIF, iNaturalist, etc.) |
| `reference_list` | `source` | Références bibliographiques |
| `ipfs_cid` | `entity` | `external_ref.ipfs` (attestation IPFS) |
| `researched` | `entity` | `flags.researched` (booléen) |
| `last_updated_date` | `entity` | `last_modified` |
| `default_image` | `entity` | `media.default_image_url` |
| `associated_media` | `entity` | `media.associated` |
| `allometric_models` | `assertion` | `allometric_model` |
| `allometric_curve` | `assertion` | `allometric_curve` |

### 5. Mapping du modèle Insight (architecture atomique)

Treekipedia introduit la notion d'**Insight** (unité atomique de connaissance avec `claim_type`, `claim_value`, `confidence`, `methodology`, `model_version`, `evidence[]`, `provenance`). Ce modèle est très proche des `SourcedFact` et `Assertion` du métamodèle v6.2.

| Champ Insight Treekipedia | Champ équivalent v6.2 |
|---|---|
| `taxon_id` | `assertion.entity_id` |
| `claim_type` | `assertion.claim_kind` |
| `claim_value` (JSONB) | `assertion.value` |
| `confidence` (0-1) | `assertion.evidence_level` (mapping A-F ci-dessous) |
| `methodology` | `assertion.methodology` |
| `model_version` | `assertion.model_version` |
| `is_current` | `assertion.is_current` |
| `content_hash` | `assertion.content_hash` (SHA-256) |
| `dcterms:source` | `source` (entité liée) |
| `prov:wasGeneratedBy` | `source.agent` |
| `dcterms:created` | `assertion.created_at` |

### 6. Mapping confidence (0-1) → evidence_level (A-F)

| `confidence` Treekipedia | `evidence_level` GSIE | Justification |
|---|---|---|
| ≥ 0.9 + source humaine peer-reviewed | `A` (Preuve formelle) | Consensus scientifique |
| ≥ 0.9 + source humaine non peer-reviewed | `B` (Référentiel) | Référentiel officiel (GBIF, USDA) |
| 0.7-0.9 + source humaine | `C` (Littérature) | Littérature grise ou expert |
| 0.7-0.9 + source AI uniquement | `D` (Hypothèse) | LLM extraction, en quarantine |
| < 0.7 | `E` (Spéculation) | À valider |
| Aucune source | `F` (Non sourcé) | Rejeté par garde-fou |

### 7. Mapping des ontologies RDF

Treekipedia utilise les préfixes suivants, à importer tels quels dans GSIE :

| Préfixe | URI | Usage GSIE |
|---|---|---|
| `dwc:` | `http://rs.tdwg.org/dwc/terms/` | Taxonomie, occurrences |
| `envo:` | `http://purl.obolibrary.org/obo/ENVO_` | Habitats, biomes |
| `pato:` | `http://purl.obolibrary.org/obo/PATO_` | Traits phénotypiques |
| `prov:` | `http://www.w3.org/ns/prov#` | Provenance (déjà aligné CON-005) |
| `dcterms:` | `http://purl.org/dc/terms/` | Sources, dates |
| `schema:` | `https://schema.org/` | URLs, titres |
| `tkp:` | `https://treekipedia.silvi.earth/ontology#` | Propriétés custom Treekipedia |

### 8. Garde-fous GSIE appliqués à l'ingestion

1. **Garde-fou anti-invention (RFC-0014 §3.2)** :
   - Tout fait AI-sourced sans source humaine → `evidence_level = D` + statut `quarantine`.
   - Tout fait sans provenance → statut `rejete`.
   - Citation mot pour mot requise pour les faits human-sourced.

2. **Conflits bibliographiques (S-3)** :
   - Si un fait Treekipedia contredit un fait GSIE → `revision` (CON-010) avec les deux valeurs.
   - `conflict_status = divergent`, jamais de moyenne arbitraire.

3. **Traçabilité (CON-005)** :
   - Chaque fait conserve sa source d'origine (GBIF, iNaturalist, paper, LLM).
   - `provenance` documente la chaîne : source d'origine → Treekipedia → Forge → GSIE.

4. **Le forestier reste le décideur (CON-001)** :
   - Les faits AI-sourced sont affichés avec `evidence_level = D` à l'utilisateur.
   - L'utilisateur peut contester n'importe quel fait.

## Impact

- **Documents modifiés** : `GSIE/KNOWLEDGE/` (ajout ontologies), `GSIE/API/src/gsie_api/ingestion/` (mapper), `Forge/forge/connectors/` (connecteur), `docker-compose.yml` (Jena Fuseki), migration Alembic (pgvector).
- **Contrats d'interface affectés** : Knowledge Engine (nouveau format d'ingestion), Evidence Engine (évaluation des faits Treekipedia).
- **Risques** :
  - Données AI-sourced erronées → mitigé par `evidence_level = D` + quarantine.
  - Conflits avec données GSIE → mitigé par S-3 (conservation des deux positions).
  - Volume trop important pour PostgreSQL → mitigé par multi-tier storage (hot/cold).
  - Mapping incomplet → mitigé par itération (champs critiques d'abord).

## Alternatives considérées

1. **Re-développer une base from scratch** : rejeté — Treekipedia a déjà consolidé 10+ datasets globaux, re-développer prendrait des mois.
2. **Utiliser uniquement GBIF** : rejeté — GBIF ne fournit que les occurrences, pas l'autécologie (habitat, sol, écologie).
3. **Attendre un dump DB complet avant toute ingestion** : rejeté — les 67 928 espèces (taxonomie) + 3 487 insights RDF sont déjà utilisables et permettent de valider le pipeline.
4. **Utiliser l'API Treekipedia en runtime** : rejeté — créerait une dépendance runtime externe. L'ingestion one-shot + versioning (CON-010) est préférable.

## Processus

1. RFC-0030 en statut `Draft` (ce document).
2. DEC-000040 référençant cette RFC (créée en parallèle).
3. Mise à jour `PROJECT_MEMORY.md`.
4. Attente validation du Fondateur.
5. Après validation : pilote 100 espèces → ingestion massive 50 000+.

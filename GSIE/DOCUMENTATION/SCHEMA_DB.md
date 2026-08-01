# Documentation du schéma de base de données GSIE

> Généré automatiquement par `TOOLS/generate_schema_doc.py`.
> 120 tables réparties sur 7 schémas.
> 2122 colonnes documentées.

## Sommaire

- **gsie_botanique** — 6 tables : Domaine botanique : taxons, autecologie, identification. RFC-0029 §4.1.
- **gsie_foret** — 12 tables : Domaine forestier : peuplements, itineraires, regles sylvicoles, dynamique. RFC-0029 §4.1.
- **gsie_gouvernance** — 6 tables : Domaine gouvernance : decisions, recommandations, validations, apprentissage. RFC-0029 §4.1.
- **gsie_knowledge_graph** — 2 tables
- **gsie_rgpd** — 6 tables : Donnees personnelles pseudonymisees. Ne permet pas d identifier.
- **gsie_rgpd_identites** — 1 tables : Mecanisme de reversion du pseudonymat (RGPD art. 32). Acces distinct de gsie_rgpd, jamais accorde a un moteur.
- **public** — 87 tables : standard public schema

## gsie_botanique

### autecology_profile

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `species_entity_id` | `uuid` | ✓ |  |  |
| `variable` | `character varying(200)` | ✓ |  |  |
| `value_numeric` | `double precision` |  |  |  |
| `value_text` | `text` |  |  |  |
| `unit` | `character varying(50)` |  |  |  |
| `life_stage` | `character varying(100)` |  |  |  |
| `season` | `character varying(50)` |  |  |  |
| `territory_description` | `text` |  |  |  |
| `method` | `text` |  |  |  |
| `uncertainty` | `text` |  |  |  |
| `evidence_level` | `evidence_level` | ✓ |  |  |
| `source_id` | `uuid` | ✓ |  |  |
| `status` | `lifecycle_status` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### botanical_identification_decision

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `result_id` | `uuid` | ✓ |  |  |
| `status` | `identification_decision_status` | ✓ |  |  |
| `selected_candidate_index` | `integer` |  |  |  |
| `manual_species_entity_id` | `uuid` |  |  |  |
| `validated_by_id` | `uuid` |  |  |  |
| `decided_at` | `timestamp with time zone` |  |  |  |
| `rejection_reason` | `text` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### botanical_identification_request

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `requested_by_id` | `uuid` | ✓ |  |  |
| `parcel_id` | `uuid` |  |  |  |
| `photos` | `jsonb` | ✓ |  |  |
| `captured_at` | `timestamp with time zone` | ✓ |  |  |
| `sent_at` | `timestamp with time zone` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### botanical_identification_result

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `request_id` | `uuid` | ✓ |  |  |
| `provider` | `character varying(100)` | ✓ |  |  |
| `provider_engine_version` | `character varying(100)` | ✓ |  |  |
| `candidates` | `jsonb` | ✓ |  |  |
| `received_at` | `timestamp with time zone` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 24 kB*

### trait_definition

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(200)` | ✓ |  |  |
| `abbreviation` | `character varying(20)` |  |  |  |
| `description` | `text` | ✓ |  |  |
| `unit_id` | `uuid` |  |  |  |
| `standard_reference` | `character varying(100)` |  |  |  |
| `value_range` | `character varying(100)` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### trait_value

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `trait_definition_id` | `uuid` | ✓ |  |  |
| `entity_id` | `uuid` | ✓ |  |  |
| `value_numeric` | `double precision` |  |  |  |
| `value_term_id` | `uuid` |  |  |  |
| `unit_id` | `uuid` |  |  |  |
| `uncertainty_id` | `uuid` |  |  |  |
| `observation_id` | `uuid` |  |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 64 kB*

## gsie_foret

### diagnostic_protocol

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(200)` | ✓ |  |  |
| `version` | `character varying(100)` | ✓ |  |  |
| `criteria_description` | `text` | ✓ |  |  |
| `thresholds_description` | `text` | ✓ |  |  |
| `limitations` | `text` |  |  |  |
| `source_id` | `uuid` | ✓ |  |  |
| `status` | `lifecycle_status` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### economic_scenario

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `category` | `economic_category` | ✓ |  |  |
| `plan_id` | `uuid` |  |  |  |
| `intervention_id` | `uuid` |  |  |  |
| `amount_eur` | `double precision` | ✓ |  |  |
| `year` | `integer` |  |  |  |
| `unit` | `character varying(50)` |  |  |  |
| `description` | `text` |  |  |  |
| `source_reference` | `character varying(500)` |  |  |  |
| `details` | `jsonb` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### fertility_class

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `species_entity_id` | `uuid` | ✓ |  |  |
| `site_index_model_id` | `uuid` | ✓ |  |  |
| `class_label` | `character varying(100)` | ✓ |  |  |
| `dominant_height_m` | `double precision` |  |  |  |
| `reference_age_years` | `integer` | ✓ |  |  |
| `lower_bound_m` | `double precision` |  |  |  |
| `upper_bound_m` | `double precision` |  |  |  |
| `calibration_region` | `character varying(200)` | ✓ |  |  |
| `source_id` | `uuid` | ✓ |  |  |
| `status` | `lifecycle_status` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### health_risk

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `subject_id` | `uuid` | ✓ |  |  |
| `diagnostic_protocol_id` | `uuid` |  |  |  |
| `symptom_observed` | `text` | ✓ |  |  |
| `suspected_causal_agent` | `character varying(300)` |  |  |  |
| `confirmed_causal_agent` | `character varying(300)` |  |  |  |
| `confirmation_method` | `text` |  |  |  |
| `severity` | `health_risk_severity` |  |  |  |
| `observed_at` | `timestamp with time zone` | ✓ |  |  |
| `source_id` | `uuid` | ✓ |  |  |
| `status` | `lifecycle_status` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### intervention

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `intervention_type` | `intervention_type` | ✓ |  |  |
| `status` | `intervention_status` | ✓ |  |  |
| `plan_id` | `uuid` |  |  |  |
| `spatial_scope_id` | `uuid` | ✓ |  |  |
| `scheduled_date` | `date` |  |  |  |
| `completed_date` | `date` |  |  |  |
| `area_ha` | `double precision` |  |  |  |
| `volume_m3` | `double precision` |  |  |  |
| `target_species` | `jsonb` | ✓ |  |  |
| `operator_id` | `uuid` |  |  |  |
| `notes` | `text` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 56 kB*

### management_plan

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `plan_type` | `management_plan_type` | ✓ |  |  |
| `status` | `plan_status` | ✓ |  |  |
| `spatial_scope_id` | `uuid` | ✓ |  |  |
| `owner_id` | `uuid` |  |  |  |
| `manager_id` | `uuid` |  |  |  |
| `start_date` | `date` | ✓ |  |  |
| `end_date` | `date` | ✓ |  |  |
| `revision_number` | `integer` | ✓ |  |  |
| `approval_date` | `date` |  |  |  |
| `approval_authority` | `character varying(200)` |  |  |  |
| `objectives` | `jsonb` | ✓ |  |  |
| `summary` | `text` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 56 kB*

### provenance_material

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `species_entity_id` | `uuid` | ✓ |  |  |
| `provenance_region` | `character varying(200)` | ✓ |  |  |
| `base_material` | `character varying(300)` | ✓ |  | Identifiant du matériel de base (verger à graines, peuplement classé, etc.) |
| `base_material_category` | `materiel_base_category` | ✓ |  |  |
| `aid_eligible` | `boolean` | ✓ |  |  |
| `decree_version` | `character varying(300)` | ✓ |  | Version de l'arrêté MFR qui fonde l'admissibilité (ex. « arrêté du 6 mars 2026 ») |
| `valid_region_description` | `text` |  |  |  |
| `source_id` | `uuid` | ✓ |  |  |
| `status` | `lifecycle_status` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 48 kB*

### silvicultural_rule

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `silvicultural_system_id` | `uuid` |  |  |  |
| `species_entity_id` | `uuid` |  |  |  |
| `required_context` | `text` | ✓ |  |  |
| `trigger` | `text` | ✓ |  |  |
| `action` | `text` | ✓ |  |  |
| `intensity` | `text` | ✓ |  |  |
| `evidence_level` | `evidence_level` | ✓ |  |  |
| `human_validator` | `character varying(300)` |  |  | Nom/qualité du validateur humain (curateur + forestier compétent) — obligatoire dès que status passe à accepted |
| `source_id` | `uuid` | ✓ |  |  |
| `status` | `lifecycle_status` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |
| `validity_zone_description` | `text` |  |  | Zone geographique de validite declaree par la source (DEC-000038) |

*Taille : 40 kB*

### silvicultural_system

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `category` | `silvicultural_system_category` | ✓ |  |  |
| `description` | `text` |  |  |  |
| `source_id` | `uuid` | ✓ |  |  |
| `status` | `lifecycle_status` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### site_index_model

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `species_entity_id` | `uuid` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `method` | `character varying(200)` | ✓ |  |  |
| `reference_age_years` | `integer` | ✓ |  |  |
| `age_convention` | `character varying(200)` | ✓ |  |  |
| `calibration_region` | `character varying(200)` | ✓ |  |  |
| `valid_age_min_years` | `integer` |  |  |  |
| `valid_age_max_years` | `integer` |  |  |  |
| `source_id` | `uuid` | ✓ |  |  |
| `status` | `lifecycle_status` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### station_observation

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `plot_reference` | `character varying(200)` | ✓ |  |  |
| `station_type_id` | `uuid` |  |  |  |
| `key_path_followed` | `text` |  |  | Réponses saisies et embranchement obtenu dans la clé du guide |
| `topography_observed` | `text` |  |  |  |
| `substrate_observed` | `text` |  |  |  |
| `hydromorphy_observed` | `text` |  |  |  |
| `indicator_flora_observed` | `text` |  |  |  |
| `available_water_capacity_mm` | `double precision` |  |  |  |
| `available_water_capacity_method` | `character varying(300)` |  |  |  |
| `determination_uncertainty` | `text` |  |  |  |
| `observed_at` | `timestamp with time zone` | ✓ |  |  |
| `source_id` | `uuid` | ✓ |  |  |
| `status` | `lifecycle_status` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### station_type

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `guide` | `character varying(300)` | ✓ |  |  |
| `guide_version` | `character varying(100)` | ✓ |  |  |
| `validity_zone_description` | `text` | ✓ |  | Zone de validité du guide en texte libre (pas de géométrie en tranche 2) |
| `ser_greco_code` | `character varying(50)` |  |  |  |
| `topography_description` | `text` |  |  |  |
| `substrate_description` | `text` |  |  |  |
| `hydromorphy_description` | `text` |  |  |  |
| `indicator_flora_description` | `text` |  |  |  |
| `source_id` | `uuid` | ✓ |  |  |
| `status` | `lifecycle_status` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

## gsie_gouvernance

### compliance_check

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `regulation_id` | `uuid` | ✓ |  |  |
| `target_id` | `uuid` | ✓ |  |  |
| `status` | `compliance_status` | ✓ |  |  |
| `checked_by` | `uuid` |  |  |  |
| `checked_at` | `timestamp with time zone` |  |  |  |
| `details` | `text` |  |  |  |
| `waiver_reason` | `text` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 48 kB*

### conflict_cluster

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `description` | `text` | ✓ |  |  |
| `status` | `conflict_status` | ✓ |  |  |
| `resolution_note` | `text` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 24 kB*

### decision

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `question_id` | `uuid` |  |  |  |
| `decided_by` | `uuid` | ✓ |  |  |
| `decision_text` | `text` | ✓ |  |  |
| `rationale` | `text` | ✓ |  |  |
| `decided_at` | `timestamp with time zone` | ✓ |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### outcome_tracking

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `recommendation_id` | `uuid` | ✓ |  |  |
| `decision_id` | `uuid` |  |  |  |
| `status` | `outcome_status` | ✓ |  |  |
| `expected_outcome` | `text` | ✓ |  |  |
| `actual_outcome` | `text` |  |  |  |
| `expected_date` | `date` |  |  |  |
| `actual_date` | `date` |  |  |  |
| `assessment` | `text` |  |  |  |
| `metrics` | `jsonb` | ✓ |  |  |
| `recalibration_notes` | `text` |  |  |  |
| `feedback_score` | `double precision` |  |  |  |
| `lessons_learned` | `text` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### recommendation

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `question_id` | `uuid` |  |  |  |
| `recommended_by` | `uuid` | ✓ |  |  |
| `recommendation_text` | `text` | ✓ |  |  |
| `confidence` | `double precision` | ✓ |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `spatial_scope_id` | `uuid` |  |  |  |
| `temporal_context_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 56 kB*

### regulation

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `domain` | `regulation_domain` | ✓ |  |  |
| `code` | `character varying(100)` | ✓ |  |  |
| `title` | `character varying(500)` | ✓ |  |  |
| `description` | `text` | ✓ |  |  |
| `authority` | `character varying(200)` |  |  |  |
| `effective_date` | `date` |  |  |  |
| `url` | `character varying(500)` |  |  |  |
| `penalties` | `jsonb` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

## gsie_knowledge_graph

### _ag_label_edge

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `graphid` | ✓ | _graphid((_label_id('gsie_knowledge_graph'::name, '_ag_label_edge'::name))::integer, nextval('gsie_knowledge_graph._ag_label_edge_id_seq'::regclass)) |  |
| `start_id` | `graphid` | ✓ |  |  |
| `end_id` | `graphid` | ✓ |  |  |
| `properties` | `agtype` | ✓ | agtype_build_map() |  |

*Taille : 16 kB*

### _ag_label_vertex

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `graphid` | ✓ | _graphid((_label_id('gsie_knowledge_graph'::name, '_ag_label_vertex'::name))::integer, nextval('gsie_knowledge_graph._ag_label_vertex_id_seq'::regclass)) |  |
| `properties` | `agtype` | ✓ | agtype_build_map() |  |

*Taille : 16 kB*

## gsie_rgpd

### access_policy

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `target_id` | `uuid` | ✓ |  |  |
| `principal` | `character varying(200)` | ✓ |  |  |
| `permission` | `permission` | ✓ |  |  |
| `condition` | `text` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### consent

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `data_subject_id` | `uuid` | ✓ |  |  |
| `purpose` | `text` | ✓ |  |  |
| `scope` | `consent_scope` | ✓ |  |  |
| `granted_at` | `timestamp with time zone` | ✓ |  |  |
| `expires_at` | `timestamp with time zone` |  |  |  |
| `withdrawn_at` | `timestamp with time zone` |  |  |  |
| `legal_basis` | `legal_basis` | ✓ |  |  |
| `document_ref` | `character varying(500)` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### data_subject_consent

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('gsie_rgpd.data_subject_consent_id_seq'::regclass) |  |
| `data_subject_id` | `uuid` | ✓ |  |  |
| `consent_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### rights_statement

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `licence` | `character varying(100)` | ✓ |  |  |
| `usage_rights` | `usage_rights` | ✓ |  |  |
| `attribution_required` | `boolean` | ✓ |  |  |
| `ai_training_allowed` | `boolean` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 16 kB*

### sensitivity_classification

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `target_id` | `uuid` | ✓ |  |  |
| `level` | `sensitivity_level` | ✓ |  |  |
| `reason` | `character varying(300)` | ✓ |  |  |
| `classified_by` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### spatial_disclosure_policy

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `target_id` | `uuid` | ✓ |  |  |
| `public_precision` | `character varying(50)` | ✓ |  |  |
| `restricted_precision` | `character varying(50)` | ✓ |  |  |
| `authority` | `character varying(100)` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 16 kB*

## gsie_rgpd_identites

### data_subject

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `agent_id` | `uuid` | ✓ |  |  |
| `pseudonymized_id` | `character varying(200)` | ✓ |  |  |
| `email_encrypted` | `character varying(500)` |  |  |  |
| `anonymized` | `boolean` | ✓ |  |  |
| `rights_exercised` | `jsonb` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

## public

### activity

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `type` | `activity_type` | ✓ |  |  |
| `started_at` | `timestamp with time zone` | ✓ |  |  |
| `ended_at` | `timestamp with time zone` |  |  |  |
| `agent_id` | `uuid` |  |  |  |
| `method_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### administrative_unit

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `level` | `administrative_level` | ✓ |  |  |
| `code` | `character varying(100)` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `parent_id` | `uuid` |  |  |  |
| `spatial_scope_id` | `uuid` |  |  |  |
| `authority` | `character varying(200)` |  |  |  |
| `attributes` | `jsonb` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 48 kB*

### agent

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `type` | `agent_type` | ✓ |  |  |
| `orcid` | `character varying(50)` |  |  |  |
| `ror` | `character varying(50)` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 24 kB*

### alembic_version

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `version_num` | `character varying(32)` | ✓ |  |  |

*Taille : 56 kB*

### assertion

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `claim_kind` | `claim_kind` | ✓ |  |  |
| `lifecycle_status` | `lifecycle_status` | ✓ |  |  |
| `rule_subtype` | `rule_subtype` |  |  |  |
| `predicate_id` | `uuid` |  |  |  |
| `spatial_scope_id` | `uuid` |  |  |  |
| `temporal_context_id` | `uuid` |  |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `version` | `integer` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 56 kB*

### assertion_participant

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('assertion_participant_id_seq'::regclass) |  |
| `assertion_id` | `uuid` | ✓ |  |  |
| `role` | `participant_role` | ✓ |  |  |
| `participant_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### assertion_qualifier

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('assertion_qualifier_id_seq'::regclass) |  |
| `assertion_id` | `uuid` | ✓ |  |  |
| `key` | `character varying(100)` | ✓ |  |  |
| `value` | `text` | ✓ |  |  |
| `unit_id` | `uuid` |  |  |  |

*Taille : 32 kB*

### capability

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(200)` | ✓ |  |  |
| `capability_type` | `capability_type` | ✓ |  |  |
| `provider_type` | `provider_type` | ✓ |  |  |
| `provider_id` | `uuid` | ✓ |  |  |
| `input_schema` | `jsonb` |  |  |  |
| `output_schema` | `jsonb` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### citation

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `source_id` | `uuid` | ✓ |  |  |
| `target_id` | `uuid` | ✓ |  |  |
| `citation_role` | `citation_role` | ✓ |  |  |
| `locator` | `character varying(100)` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 24 kB*

### concept

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `preferred_label` | `character varying(300)` | ✓ |  |  |
| `description` | `text` | ✓ |  |  |
| `vocabulary_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 24 kB*

### concept_version

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `concept_id` | `uuid` | ✓ |  |  |
| `release_id` | `uuid` |  |  |  |
| `label` | `character varying(300)` | ✓ |  |  |
| `fusions` | `jsonb` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### confidence_graph

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `root_resource_id` | `uuid` | ✓ |  |  |
| `confidence_score` | `double precision` |  |  |  |
| `propagation_method` | `propagation_method` | ✓ |  |  |
| `source_nodes` | `jsonb` | ✓ |  |  |
| `propagation_tree` | `jsonb` | ✓ |  |  |
| `computed_at` | `timestamp with time zone` | ✓ |  |  |
| `computed_by` | `uuid` |  |  |  |
| `valid_for_revision_id` | `integer` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### conflict_cluster_assertion

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('conflict_cluster_assertion_id_seq'::regclass) |  |
| `conflict_cluster_id` | `uuid` | ✓ |  |  |
| `assertion_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### constraint

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `constraint_type` | `constraint_type` | ✓ |  |  |
| `description` | `text` | ✓ |  |  |
| `severity` | `constraint_severity` | ✓ |  |  |
| `source_id` | `uuid` |  |  |  |
| `spatial_scope_id` | `uuid` |  |  |  |
| `temporal_context_id` | `uuid` |  |  |  |
| `affected_recommendation_id` | `uuid` |  |  |  |
| `mitigation` | `text` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 64 kB*

### controlled_term

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `vocabulary_id` | `uuid` | ✓ |  |  |
| `code` | `character varying(100)` | ✓ |  |  |
| `label` | `character varying(300)` | ✓ |  |  |
| `parent_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### correlation

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `method` | `correlation_method` | ✓ |  |  |
| `coefficient` | `double precision` |  |  |  |
| `strength` | `correlation_strength` | ✓ |  |  |
| `confidence` | `double precision` | ✓ |  |  |
| `p_value` | `double precision` |  |  |  |
| `evidence_assessment_id` | `uuid` |  |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `spatial_scope_id` | `uuid` |  |  |  |
| `temporal_context_id` | `uuid` |  |  |  |
| `lifecycle_status` | `lifecycle_status` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### correlation_variable

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('correlation_variable_id_seq'::regclass) |  |
| `correlation_id` | `uuid` | ✓ |  |  |
| `variable_id` | `uuid` | ✓ |  |  |
| `role` | `character varying(50)` |  |  |  |

*Taille : 24 kB*

### data_asset

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `dataset_version_id` | `uuid` | ✓ |  |  |
| `format` | `character varying(50)` | ✓ |  |  |
| `size_bytes` | `integer` | ✓ |  |  |
| `checksum` | `character varying(200)` | ✓ |  |  |
| `archived_from` | `uuid` |  |  |  |
| `original_uri` | `character varying(500)` |  |  |  |
| `archived_at` | `timestamp with time zone` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### dataset

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `title` | `character varying(500)` | ✓ |  |  |
| `description` | `text` | ✓ |  |  |
| `publisher_id` | `uuid` |  |  |  |
| `spatial_resolution` | `character varying(100)` |  |  |  |
| `temporal_resolution` | `character varying(100)` |  |  |  |
| `topic` | `character varying(200)` |  |  |  |
| `purpose` | `dataset_purpose` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### dataset_version

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `dataset_id` | `uuid` | ✓ |  |  |
| `version` | `character varying(50)` | ✓ |  |  |
| `release_date` | `timestamp with time zone` |  |  |  |
| `changes` | `text` |  |  |  |
| `stats` | `jsonb` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 24 kB*

### decision_evidence

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('decision_evidence_id_seq'::regclass) |  |
| `decision_id` | `uuid` | ✓ |  |  |
| `citation_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### decision_recommendation

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('decision_recommendation_id_seq'::regclass) |  |
| `decision_id` | `uuid` | ✓ |  |  |
| `recommendation_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### diagnostic

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `requete_origine` | `uuid` | ✓ |  |  |
| `station_id` | `uuid` | ✓ |  |  |
| `type_diagnostic` | `diagnostic_type` | ✓ |  |  |
| `etat_global` | `diagnostic_global_state` | ✓ |  |  |
| `statut_validation` | `diagnostic_validation_status` | ✓ |  |  |
| `confiance` | `double precision` | ✓ |  |  |
| `evidence_level_plancher` | `evidence_level` | ✓ |  |  |
| `date_diagnostic` | `timestamp with time zone` | ✓ |  |  |
| `contenu` | `jsonb` | ✓ |  | Diagnostic sérialisé intégral — seule source de relecture |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 144 kB*

### distribution

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `dataset_version_id` | `uuid` | ✓ |  |  |
| `access_method` | `access_method` | ✓ |  |  |
| `access_url` | `character varying(500)` |  |  |  |
| `licence` | `character varying(100)` | ✓ |  |  |
| `rights_statement_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |
| `scale_context_id` | `uuid` |  |  | Resolution native de la source, via scale_context.grain_m2 |

*Taille : 48 kB*

### ecological_process

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `process_type` | `ecological_process_type` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `spatial_scope_id` | `uuid` |  |  |  |
| `temporal_context_id` | `uuid` |  |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `rate` | `double precision` |  |  |  |
| `rate_unit_id` | `uuid` |  |  |  |
| `driver_phenomenon_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 56 kB*

### ecological_state

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `spatial_scope_id` | `uuid` | ✓ |  |  |
| `temporal_context_id` | `uuid` |  |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `state_type` | `state_type` | ✓ |  |  |
| `indicators` | `jsonb` | ✓ |  |  |
| `overall_score` | `double precision` |  |  |  |
| `overall_grade` | `ecological_grade` |  |  |  |
| `computed_by` | `uuid` |  |  |  |
| `trend` | `trend` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 56 kB*

### ecological_state_basis

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('ecological_state_basis_id_seq'::regclass) |  |
| `ecological_state_id` | `uuid` | ✓ |  |  |
| `basis_id` | `uuid` | ✓ |  |  |
| `basis_type` | `character varying(50)` |  |  |  |

*Taille : 24 kB*

### ecosystem_service

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `category` | `ecosystem_service_category` | ✓ |  |  |
| `description` | `text` | ✓ |  |  |
| `spatial_scope_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### entity

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `entity_subtype` | `character varying(50)` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |
| `embedding` | `vector(1536)` |  |  |  |

*Taille : 1672 kB*

### entity_alias

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `entity_id` | `uuid` | ✓ |  |  |
| `namespace` | `character varying(50)` | ✓ |  |  |
| `external_id` | `character varying(200)` | ✓ |  |  |
| `external_url` | `character varying(500)` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### evidence_assessment

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `assertion_id` | `uuid` | ✓ |  |  |
| `level` | `evidence_level` | ✓ |  |  |
| `evaluator_id` | `uuid` |  |  |  |
| `method` | `character varying(200)` | ✓ |  |  |
| `evaluated_at` | `timestamp with time zone` | ✓ |  |  |
| `scope` | `text` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### experiment

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `hypothesis_id` | `uuid` |  |  |  |
| `comparison_metrics` | `jsonb` | ✓ |  |  |
| `conclusion` | `text` |  |  |  |
| `resulting_assertion_id` | `uuid` |  |  |  |
| `resulting_source_id` | `uuid` |  |  |  |
| `conducted_by` | `uuid` | ✓ |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 64 kB*

### experiment_model_run

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('experiment_model_run_id_seq'::regclass) |  |
| `experiment_id` | `uuid` | ✓ |  |  |
| `model_run_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### experiment_scenario

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('experiment_scenario_id_seq'::regclass) |  |
| `experiment_id` | `uuid` | ✓ |  |  |
| `scenario_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### feature

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(200)` | ✓ |  |  |
| `description` | `text` | ✓ |  |  |
| `source_type` | `feature_source_type` | ✓ |  |  |
| `computation_method` | `text` |  |  |  |
| `unit_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### feature_set

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(200)` | ✓ |  |  |
| `description` | `text` | ✓ |  |  |
| `model_version_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### feature_set_feature

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('feature_set_feature_id_seq'::regclass) |  |
| `feature_set_id` | `uuid` | ✓ |  |  |
| `feature_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### flow

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `flow_type` | `flow_type` | ✓ |  |  |
| `source_id` | `uuid` | ✓ |  |  |
| `sink_id` | `uuid` | ✓ |  |  |
| `magnitude` | `double precision` | ✓ |  |  |
| `magnitude_unit_id` | `uuid` | ✓ |  |  |
| `direction` | `flow_direction` | ✓ |  |  |
| `temporal_context_id` | `uuid` |  |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `driver_process_id` | `uuid` |  |  |  |
| `uncertainty_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 72 kB*

### goal

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `goal_type` | `goal_type` | ✓ |  |  |
| `description` | `text` | ✓ |  |  |
| `priority` | `goal_priority` | ✓ |  |  |
| `target_value` | `double precision` |  |  |  |
| `parent_goal_id` | `uuid` |  |  |  |
| `spatial_scope_id` | `uuid` |  |  |  |
| `temporal_context_id` | `uuid` |  |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `success_criteria` | `text` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 64 kB*

### hypothesis

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `question_id` | `uuid` | ✓ |  |  |
| `text` | `text` | ✓ |  |  |
| `status` | `hypothesis_status` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### hypothesis_contradicting

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('hypothesis_contradicting_id_seq'::regclass) |  |
| `hypothesis_id` | `uuid` | ✓ |  |  |
| `assertion_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### hypothesis_supporting

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('hypothesis_supporting_id_seq'::regclass) |  |
| `hypothesis_id` | `uuid` | ✓ |  |  |
| `assertion_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### inbox_event

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `source` | `character varying(100)` | ✓ |  |  |
| `external_id` | `character varying(200)` | ✓ |  |  |
| `event_type` | `character varying(100)` | ✓ |  |  |
| `payload` | `jsonb` | ✓ |  |  |
| `received_at` | `timestamp with time zone` | ✓ | now() |  |
| `processed_at` | `timestamp with time zone` |  |  |  |
| `status` | `character varying(20)` | ✓ |  |  |

*Taille : 48 kB*

### inference

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `model_version_id` | `uuid` | ✓ |  |  |
| `feature_set_id` | `uuid` | ✓ |  |  |
| `input_snapshot_id` | `uuid` |  |  |  |
| `output_assertion_id` | `uuid` |  |  |  |
| `confidence` | `double precision` | ✓ |  |  |
| `inferred_at` | `timestamp with time zone` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### instance

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `concept_id` | `uuid` | ✓ |  |  |
| `entity_id` | `uuid` |  |  |  |
| `spatial_scope_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### instrument

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(200)` | ✓ |  |  |
| `type` | `character varying(100)` | ✓ |  |  |
| `calibration_date` | `date` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 16 kB*

### knowledge_lineage

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `resource_id` | `uuid` | ✓ |  |  |
| `produced_by` | `uuid` |  |  |  |
| `production_method` | `character varying(50)` |  |  |  |
| `confidence_graph_id` | `uuid` |  |  |  |
| `lineage_depth` | `integer` | ✓ |  |  |
| `computed_at` | `timestamp with time zone` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### knowledge_lineage_derived

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('knowledge_lineage_derived_id_seq'::regclass) |  |
| `knowledge_lineage_id` | `uuid` | ✓ |  |  |
| `derived_from_id` | `uuid` | ✓ |  |  |
| `role` | `character varying(50)` |  |  |  |

*Taille : 24 kB*

### media

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `type` | `media_type` | ✓ |  |  |
| `url` | `character varying(500)` | ✓ |  |  |
| `mime_type` | `character varying(100)` | ✓ |  |  |
| `checksum` | `character varying(200)` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 24 kB*

### method

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `description` | `text` | ✓ |  |  |
| `protocol_url` | `character varying(500)` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 24 kB*

### model

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `type` | `model_type` | ✓ |  |  |
| `description` | `text` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### model_run

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `model_version_id` | `uuid` | ✓ |  |  |
| `scenario_id` | `uuid` |  |  |  |
| `started_at` | `timestamp with time zone` | ✓ |  |  |
| `ended_at` | `timestamp with time zone` |  |  |  |
| `status` | `character varying(20)` | ✓ |  |  |
| `parameters` | `jsonb` | ✓ |  |  |
| `activity_id` | `uuid` |  |  |  |
| `output_assertion_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 56 kB*

### model_run_input

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('model_run_input_id_seq'::regclass) |  |
| `model_run_id` | `uuid` | ✓ |  |  |
| `input_id` | `uuid` | ✓ |  |  |
| `role` | `character varying(50)` |  |  |  |

*Taille : 24 kB*

### model_run_output

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('model_run_output_id_seq'::regclass) |  |
| `model_run_id` | `uuid` | ✓ |  |  |
| `output_id` | `uuid` | ✓ |  |  |
| `role` | `character varying(50)` |  |  |  |

*Taille : 24 kB*

### model_version

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `model_id` | `uuid` | ✓ |  |  |
| `version` | `character varying(50)` | ✓ |  |  |
| `release_date` | `timestamp with time zone` |  |  |  |
| `checksum` | `character varying(200)` |  |  |  |
| `inputs_schema` | `jsonb` |  |  |  |
| `outputs_schema` | `jsonb` |  |  |  |
| `trained_at` | `timestamp with time zone` |  |  |  |
| `metrics` | `jsonb` |  |  |  |
| `feature_set_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### observation

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `subject_id` | `uuid` | ✓ |  |  |
| `feature_of_interest_id` | `uuid` |  |  |  |
| `method_id` | `uuid` |  |  |  |
| `instrument_id` | `uuid` |  |  |  |
| `temporal_context_id` | `uuid` |  |  |  |
| `sampling_effort` | `jsonb` |  |  |  |
| `detection_probability` | `double precision` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 56 kB*

### outbox_event

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `aggregate_id` | `uuid` | ✓ |  |  |
| `aggregate_type` | `character varying(50)` | ✓ |  |  |
| `event_type` | `character varying(100)` | ✓ |  |  |
| `payload` | `jsonb` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `published_at` | `timestamp with time zone` |  |  |  |
| `status` | `character varying(20)` | ✓ |  |  |
| `attempt_count` | `integer` | ✓ | 0 |  |
| `next_attempt_at` | `timestamp with time zone` | ✓ | now() |  |
| `last_error_code` | `character varying(100)` |  |  |  |
| `dead_lettered_at` | `timestamp with time zone` |  |  |  |

*Taille : 128 kB*

### outcome_evidence

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('outcome_evidence_id_seq'::regclass) |  |
| `outcome_id` | `uuid` | ✓ |  |  |
| `evidence_id` | `uuid` | ✓ |  |  |
| `role` | `character varying(50)` | ✓ |  |  |

*Taille : 24 kB*

### persistent_identifier

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `target_id` | `uuid` | ✓ |  |  |
| `pid_type` | `pid_type` | ✓ |  |  |
| `value` | `character varying(500)` | ✓ |  |  |
| `authority` | `character varying(100)` | ✓ |  |  |
| `registered_at` | `timestamp with time zone` | ✓ |  |  |
| `active` | `boolean` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 40 kB*

### phenomenon

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `phenomenon_type` | `phenomenon_type` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `intensity` | `double precision` |  |  |  |
| `intensity_unit_id` | `uuid` |  |  |  |
| `spatial_scope_id` | `uuid` |  |  |  |
| `temporal_context_id` | `uuid` |  |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 48 kB*

### place

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `geometry` | `geometry(Geometry,2154)` |  |  |  |
| `srid` | `integer` | ✓ |  |  |
| `label` | `character varying(300)` |  |  |  |
| `area_m2` | `double precision` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |
| `geom_4326` | `geometry(Geometry,4326)` |  | st_transform(geometry, 4326) |  |

*Taille : 40 kB*

### predicate

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `label` | `character varying(200)` | ✓ |  |  |
| `inverse_label` | `character varying(200)` |  |  |  |
| `controlled_term_id` | `uuid` |  |  |  |
| `relation_type_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### prov_entity

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `checksum` | `character varying(200)` |  |  |  |
| `checksum_algorithm` | `character varying(50)` |  |  |  |
| `was_derived_from` | `uuid` |  |  |  |
| `was_generated_by` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 24 kB*

### quality_assessment

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `target_id` | `uuid` | ✓ |  |  |
| `dimension` | `quality_dimension` | ✓ |  |  |
| `score` | `double precision` | ✓ |  |  |
| `method` | `character varying(200)` | ✓ |  |  |
| `assessed_at` | `timestamp with time zone` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 16 kB*

### question

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `text` | `text` | ✓ |  |  |
| `question_type` | `question_type` | ✓ |  |  |
| `asked_by` | `uuid` |  |  |  |
| `asked_at` | `timestamp with time zone` | ✓ |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `spatial_scope_id` | `uuid` |  |  |  |
| `temporal_context_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 56 kB*

### recommendation_assertion

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('recommendation_assertion_id_seq'::regclass) |  |
| `recommendation_id` | `uuid` | ✓ |  |  |
| `assertion_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### recommendation_scenario

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('recommendation_scenario_id_seq'::regclass) |  |
| `recommendation_id` | `uuid` | ✓ |  |  |
| `scenario_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### relation_type

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `category` | `relation_category` | ✓ |  |  |
| `label` | `character varying(200)` | ✓ |  |  |
| `description` | `text` | ✓ |  |  |
| `parent_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### resource

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `type` | `character varying(50)` | ✓ |  |  |
| `gsie_id` | `character varying(100)` |  |  |  |
| `metadata_json` | `jsonb` | ✓ |  |  |
| `deleted_at` | `timestamp with time zone` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 64 kB*

### resource_diff

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `from_revision_id` | `integer` |  |  |  |
| `to_revision_id` | `integer` |  |  |  |
| `changes` | `jsonb` | ✓ |  | {added: {...}, modified: {field: {from, to}}, removed: {...}} |
| `summary` | `text` |  |  |  |
| `field_changes` | `jsonb` | ✓ |  |  |
| `added_relations` | `jsonb` | ✓ |  |  |
| `removed_relations` | `jsonb` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### result

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `observation_id` | `uuid` | ✓ |  |  |
| `value_type` | `value_type` | ✓ |  |  |
| `value_numeric` | `double precision` |  |  |  |
| `value_term_id` | `uuid` |  |  |  |
| `value_text` | `text` |  |  |  |
| `unit_id` | `uuid` |  |  |  |
| `uncertainty_id` | `uuid` |  |  |  |
| `detection_limit` | `double precision` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 48 kB*

### revision

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('revision_id_seq'::regclass) |  |
| `target_id` | `uuid` | ✓ |  |  |
| `version` | `integer` | ✓ |  |  |
| `author_id` | `uuid` |  |  |  |
| `justification` | `text` | ✓ |  |  |
| `parent_id` | `integer` |  |  |  |
| `valid_time_start` | `timestamp with time zone` | ✓ |  |  |
| `valid_time_end` | `timestamp with time zone` |  |  |  |
| `transaction_time` | `timestamp with time zone` | ✓ |  |  |
| `activity_id` | `uuid` |  |  |  |
| `diff_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 64 kB*

### sample

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `sample_type` | `sample_type` | ✓ |  |  |
| `sampling_event_id` | `uuid` |  |  |  |
| `subject_id` | `uuid` | ✓ |  |  |
| `material` | `character varying(100)` | ✓ |  |  |
| `storage_location` | `character varying(200)` |  |  |  |
| `storage_conditions` | `character varying(200)` |  |  |  |
| `collected_at` | `uuid` |  |  |  |
| `mass_g` | `double precision` |  |  |  |
| `volume_ml` | `double precision` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 48 kB*

### sampling_event

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `protocol_id` | `uuid` |  |  |  |
| `spatial_design` | `text` | ✓ |  |  |
| `temporal_context_id` | `uuid` |  |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `parent_event_id` | `uuid` |  |  |  |
| `principal_investigator_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 64 kB*

### scale_context

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `level` | `scale_level` | ✓ |  |  |
| `parent_scale_id` | `uuid` |  |  |  |
| `extent_m2` | `double precision` |  |  |  |
| `grain_m2` | `double precision` |  |  |  |
| `description` | `text` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 32 kB*

### scenario

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `scenario_type` | `scenario_type` | ✓ |  |  |
| `scenario_subtype` | `scenario_subtype` |  |  |  |
| `description` | `text` | ✓ |  |  |
| `parameters` | `jsonb` | ✓ |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `temporal_context_id` | `uuid` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 48 kB*

### snapshot

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('snapshot_id_seq'::regclass) |  |
| `target_id` | `uuid` | ✓ |  |  |
| `revision_id` | `integer` |  |  |  |
| `captured_at` | `timestamp with time zone` | ✓ |  |  |
| `serialized_state` | `jsonb` | ✓ |  |  |
| `checksum` | `character varying(200)` | ✓ |  |  |

*Taille : 32 kB*

### source

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `title` | `character varying(500)` | ✓ |  |  |
| `subtype` | `source_subtype` | ✓ |  |  |
| `source_nature` | `source_nature` | ✓ |  |  |
| `url` | `character varying(500)` |  |  |  |
| `doi` | `character varying(200)` |  |  |  |
| `licence` | `character varying(100)` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |
| `auteur` | `character varying(500)` |  |  | Auteurs de la source, sous la forme attendue pour une citation |
| `date_publication` | `character varying(50)` |  |  | Date de publication declaree par la source (annee ou date complete) |

*Taille : 40 kB*

### spatial_ref_sys

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `srid` | `integer` | ✓ |  |  |
| `auth_name` | `character varying(256)` |  |  |  |
| `auth_srid` | `integer` |  |  |  |
| `srtext` | `character varying(2048)` |  |  |  |
| `proj4text` | `character varying(2048)` |  |  |  |

*Taille : 7144 kB*

### temporal_context

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `valid_time_start` | `timestamp with time zone` | ✓ |  |  |
| `valid_time_end` | `timestamp with time zone` |  |  |  |
| `transaction_time_start` | `timestamp with time zone` | ✓ |  |  |
| `transaction_time_end` | `timestamp with time zone` |  |  |  |
| `granularity` | `temporal_granularity` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 8192 bytes*

### terrain_session

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(300)` | ✓ |  |  |
| `session_type` | `terrain_session_type` | ✓ |  |  |
| `started_at` | `timestamp with time zone` | ✓ |  |  |
| `ended_at` | `timestamp with time zone` |  |  |  |
| `operator_id` | `uuid` |  |  |  |
| `weather` | `jsonb` |  |  |  |
| `gps_precision_m` | `double precision` |  |  |  |
| `equipment` | `jsonb` | ✓ |  |  |
| `spatial_scope_id` | `uuid` |  |  |  |
| `scale_context_id` | `uuid` |  |  |  |
| `protocol_id` | `uuid` |  |  |  |
| `sync_status` | `sync_status` | ✓ |  |  |
| `notes` | `text` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 64 kB*

### terrain_session_media

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('terrain_session_media_id_seq'::regclass) |  |
| `terrain_session_id` | `uuid` | ✓ |  |  |
| `media_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### terrain_session_sampling

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `integer` | ✓ | nextval('terrain_session_sampling_id_seq'::regclass) |  |
| `terrain_session_id` | `uuid` | ✓ |  |  |
| `sampling_event_id` | `uuid` | ✓ |  |  |

*Taille : 24 kB*

### uncertainty

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `type` | `uncertainty_type` | ✓ |  |  |
| `lower` | `double precision` |  |  |  |
| `upper` | `double precision` |  |  |  |
| `confidence_level` | `double precision` |  |  |  |
| `description` | `text` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 16 kB*

### unit

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `symbol` | `character varying(20)` | ✓ |  |  |
| `name` | `character varying(200)` | ✓ |  |  |
| `ucum_code` | `character varying(50)` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 16 kB*

### vocabulary

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `name` | `character varying(200)` | ✓ |  |  |
| `namespace` | `character varying(100)` | ✓ |  |  |
| `description` | `text` | ✓ |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 24 kB*

### vocabulary_release

| Colonne | Type | Not Null | Défaut | Commentaire |
|---|---|---|---|---|
| `id` | `uuid` | ✓ |  |  |
| `vocabulary_id` | `uuid` | ✓ |  |  |
| `version` | `character varying(50)` | ✓ |  |  |
| `release_date` | `date` |  |  |  |
| `created_at` | `timestamp with time zone` | ✓ | now() |  |
| `updated_at` | `timestamp with time zone` | ✓ | now() |  |

*Taille : 16 kB*

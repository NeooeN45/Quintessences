# Inspection Treekipedia — Findings réels

**Date** : 2026-07-31
**Source** : `github.com/SilviProtocol/silvi` (clone dans `21_EXPERIMENTS/_treekipedia_inspection/`)
**Licence** : **MIT** (confirmée dans `LICENSE.md`) — utilisation, modification, redistribution libres

---

## 1. Volume du repo

| Métrique | Valeur |
|---|---|
| Fichiers (hors venv/node_modules/.git) | **728** |
| Taille totale | **226 MB** |
| Fichiers .md | 157 |
| Fichiers .js | 115 (backend Node/Express) |
| Fichiers .py | 63 (orchestrator + microservice) |
| Fichiers .sql | 46 (migrations + schémas) |
| Fichiers .tsx | 71 (frontend Next.js) |
| Fichiers .json | 106 |

## 2. Stack technique réelle

| Couche | Technologie | Détail |
|---|---|---|
| Backend API | **Node.js + Express** | `treekipedia/backend/` — 12 controllers, JWT, middleware |
| Microservice ontologie | **Python + Flask** | `treekipedia/python-microservice/` — OWL/RDF, sync PostgreSQL→Fuseki |
| Orchestrateur recherche | **Python** | `orchestrator/` — Claude Code CLI + WebSearch (depuis Jan 2026) |
| Base de données | **PostgreSQL 14 + PostGIS** | 26 tables documentées |
| Graphe sémantique | **Apache Jena Fuseki (TDB2)** | `treekipedia/sparql/` — config + données + requêtes |
| Frontend | **Next.js (React/TSX)** | `treekipedia/frontend/` |
| Blockchain | **Celo + Arbitrum + EAS** | Smart contracts, NFT Contreebution, attestations |
| Stockage immutable | **IPFS** | `services/ipfs.js` — pinning recherches |

## 3. Données récupérables immédiatement depuis le repo

### 3.1 CSV d'espèces (taxonomie)

| Fichier | Lignes | Colonnes | Contenu |
|---|---|---|---|
| `species_names_v2.csv` | **67 928** | 4 | taxon_id, species_scientific_name, taxon_full, common_name |
| `treekipedia_griis_full_intersection.csv` | **1 928** | 14 | Invasivité GRIIS (pays natifs/invasifs/aliens, habitats) |
| `Treekipedia_USDA_invasiveFlag_short.csv` | **828** | — | Statut invasif USDA |
| `exports/treekipedia_species_for_silvi.csv` | — | 8 | Export Silvi (taxonomie uniquement) |

### 3.2 Ontologie RDF (Turtle)

| Fichier | Taille | Lignes | Contenu |
|---|---|---|---|
| `sparql/config/treekipedia.ttl` | 1.13 KB | — | Config Fuseki (service + dataset TDB2) |
| `sparql/data/insights.ttl` | **291 KB** | **3 487** | Insights atomiques RDF avec provenance |

**Préfixes ontologiques utilisés** (alignés standards W3C/TDWG) :
- `tkp:` — ontologie Treekipedia (propriétés custom)
- `dwc:` — Darwin Core (taxonomie, occurrences)
- `envo:` — Environment Ontology (habitats, biomes)
- `pato:` — Phenotype And Trait Ontology (traits)
- `dcterms:` — Dublin Core (sources, dates)
- `prov:` — W3C Provenance (génération des insights)
- `schema:` — Schema.org (URLs, titres)

**Structure d'un insight RDF** (exemple réel extrait) :
```turtle
treekipedia:AngMaFaFbCx09076-00 tkp:barkCharacteristics "Smooth bark..." .

<#insight_9c2365af...> a tkp:Insight ;
    tkp:aboutSpecies treekipedia:AngMaFaFbCx09076-00 ;
    tkp:claimType "bark_characteristics" ;
    tkp:confidence "0.85"^^xsd:decimal ;
    prov:wasGeneratedBy "claude-code-cli" ;
    dcterms:created "2026-01-06T14:16:00..."^^xsd:dateTime ;
    dcterms:source <#source_..._0>, <#source_..._1> .

<#source_..._0> a tkp:Source ;
    schema:url "https://apps.lucidcentral.org/wattle/text/entities/acacia_acrionastes.htm" ;
    dcterms:title "Factsheet - Acacia acrionastes - WorldWideWattle" ;
    tkp:sourceType "database" ;
    tkp:credibility "0.9"^^xsd:decimal .
```

### 3.3 Données GBIF (occurrences)

| Dossier | Contenu |
|---|---|
| `orchestrator/gbif_data/` | 11 zips GBIF + `gbif_occurrences.parquet` + `gbif_occurrences_top100.parquet` + `gbif_occurrences_top100_gps.parquet` |

### 3.4 Schéma SQL complet

46 fichiers `.sql` dans `treekipedia/database/` :
- `current-schema.sql` — schéma courant (3 tables : species, users, contreebution_nfts)
- `08_atomic_insights_architecture.sql` — architecture insights atomiques (hash, agrégation, triggers)
- `06_insights_schema.sql` — table `insights`
- `05_ecoregions_integration.sql` — écorégions
- `02_create_geohash_tiles_table.sql` — tuiles geohash
- `12_common_names.sql` — noms communs
- + 40 autres migrations

**26 tables PostgreSQL documentées** (schema_summary.txt) :
species, species_v8, species_research_queue, insights, geohash_species_tiles, geohash_taxon_id_mapping, ecoregions, ecoregion_assignments, countries, images, users, contreebution_nfts, sponsorships, sponsorship_items, taxon_id_mapping (×4), + backups.

### 3.5 Scripts et orchestrateur

| Dossier | Contenu |
|---|---|
| `treekipedia/scripts/` | 60+ scripts JS/Python (import, export, fix, geohash, images, écorégions) |
| `orchestrator/` | Research orchestrator Python (Claude Code CLI + WebSearch), GBIF downloader, GEE sampler, IPFS archiver, location predictor, clustering POC |

## 4. Ce qui n'est PAS dans le repo

| Donnée | Localisation | Comment l'obtenir |
|---|---|---|
| 121 champs écologiques complets par espèce | DB PostgreSQL (non dumpée) | API Treekipedia ou dump DB demandé à Silvi |
| 5.7M tuiles geohash | DB PostgreSQL | Idem |
| 31 796 images Wikimedia | URLs externes (Wikimedia Commons) | Scraping ou API Wikimedia |
| 847 polygones écorégions | Shapefiles WWF (non inclus) | `naturalearthdata.com` + `worldwildlife.org` |
| Insights complets (50k+ espèces) | DB + Fuseki | Le repo n'a que 3 487 lignes RDF (échantillon) |

## 5. Architecture insights — détail technique

### 5.1 35 claim_types documentés (FIELD_TO_CLAIM_TYPE)

Extrait de `backend/controllers/species.js` :
```javascript
const FIELD_TO_CLAIM_TYPE = {
    popular_common_name_ai: 'popular_common_name',
    habitat_ai: 'habitat',
    elevation_ranges_ai: 'elevation_ranges',
    ecological_function_ai: 'ecological_function',
    native_adapted_habitats_ai: 'native_adapted_habitats',
    agroforestry_use_cases_ai: 'agroforestry_use_cases',
    conservation_status_ai: 'conservation_status',
    general_description_ai: 'general_description',
    compatible_soil_types_ai: 'compatible_soil_types',
    growth_form_ai: 'growth_form',
    leaf_type_ai: 'leaf_type',
    deciduous_evergreen_ai: 'deciduous_evergreen',
    flower_color_ai: 'flower_color',
    fruit_type_ai: 'fruit_type',
    bark_characteristics_ai: 'bark_characteristics',
    maximum_height_ai: 'maximum_height',
    maximum_diameter_ai: 'maximum_diameter',
    lifespan_ai: 'lifespan',
    maximum_tree_age_ai: 'maximum_tree_age',
    stewardship_best_practices_ai: 'stewardship_best_practices',
    planting_recipes_ai: 'planting_recipes',
    pruning_maintenance_ai: 'pruning_maintenance',
    disease_pest_management_ai: 'disease_pest_management',
    fire_management_ai: 'fire_management',
    cultural_significance_ai: 'cultural_significance',
    // v2 (10 nouveaux)
    etymology_ai: 'etymology',
    synonyms_ai: 'synonyms',
    identification_features_ai: 'identification_features',
    climate_tolerance_ai: 'climate_tolerance',
    tolerances_ai: 'tolerances',
    associated_species_ai: 'associated_species',
    propagation_methods_ai: 'propagation_methods',
    timber_value_ai: 'timber_value',
    non_timber_products_ai: 'non_timber_products',
    nutritional_caloric_value_ai: 'nutritional_caloric_value'
};
```

### 5.2 Mécanisme d'agrégation (08_atomic_insights_architecture.sql)

- **Hash SHA-256** : `generate_insight_hash(taxon_id, claim_type, claim_value)` → déduplication
- **Index unique** sur `content_hash` où `is_current = TRUE`
- **Trigger** auto-génère le hash avant INSERT/UPDATE
- **4 fonctions d'agrégation** :
  - `aggregate_text_insights` — concatène par confiance décroissante (bullet points)
  - `aggregate_ranked_insights` — liste séparée par `;` ordonnée par rank
  - `aggregate_top_insight` — valeur seule la plus confiante
  - `get_primary_common_name` — nom commun principal (rank 1)
- **Sync** : les insights sont synchronisées vers les colonnes `_ai` de `species`

### 5.3 Research orchestrator (depuis Jan 2026)

**Avant** : Perplexity + OpenAI
**Après** : **Claude Code CLI avec WebSearch auto-approved**

Fichiers clés :
- `orchestrator/research_orchestrator.py` — orchestration
- `orchestrator/research_runner.py` — exécution
- `orchestrator/atomic_research_prompts.py` — prompts structurés
- `orchestrator/unified_research_prompt.py` — prompt unifié
- `orchestrator/confidence_calculator.py` — calcul de confiance
- `orchestrator/sync_insights.py` — sync vers PostgreSQL
- `orchestrator/lean_rdf_exporter.py` — export RDF minimal
- `orchestrator/ipfs_archiver.py` — archivage IPFS

## 6. 15 requêtes SPARQL d'exemple (example_queries.sparql)

1. Lister toutes les espèces avec nom scientifique
2. Tous les insights pour une espèce spécifique
3. Informations habitat haute confiance (>0.8)
4. Espèces avec statut de conservation (endangered/vulnerable/critical)
5. Cas d'usage agroforesterie
6. Compter les insights par claim_type
7. Espèces avec info gestion du feu
8. Provenance — insights par agent de recherche
9. Fonctions écologiques cross-espèces
10. Espèces par forme de croissance
11. Espèces adaptées à types de sol spécifiques
12. Espèces récemment recherchées
13. Requête fédérée (intégration GBIF)
14. Statistiques de confiance (avg/min/max/count)
15. Profil complet d'une espèce

## 7. Mapping Treekipedia → GSIE — findings réels

### 7.1 Compatibilité ontologie

L'ontologie Treekipedia utilise **exactement** les standards que je recommandais :
- Darwin Core (dwc) ✅
- ENVO ✅
- PATO ✅
- PROV (W3C) ✅
- Schema.org ✅

**Action** : importer `sparql/data/insights.ttl` tel quel dans un Jena Fuseki GSIE.

### 7.2 Compatibilité schéma SQL

Le schéma `species` (121 champs, dual `_human`/`_ai`) est documenté dans `current-schema.sql`. Le schéma `insights` (architecture atomique) est dans `06_insights_schema.sql` + `08_atomic_insights_architecture.sql`.

**Action** : adapter ces schémas vers le métamodèle v6.2 de GSIE (73 types noyau).

### 7.3 Récupération immédiate possible

Sans accès à la DB Treekipedia, on peut déjà récupérer depuis le repo :
1. **67 928 espèces** (taxon_id + noms) → `species_names_v2.csv`
2. **3 487 lignes d'insights RDF** avec provenance → `insights.ttl`
3. **1 928 espèces** avec données invasivité GRIIS → `treekipedia_griis_full_intersection.csv`
4. **828 espèces** avec statut USDA → `Treekipedia_USDA_invasiveFlag.csv`
5. **Schéma SQL complet** (46 migrations) → `database/`
6. **Ontologie RDF + config Fuseki** → `sparql/`
7. **11 zips GBIF + parquet occurrences** → `orchestrator/gbif_data/`
8. **60+ scripts d'import/export** → `scripts/`
9. **Orchestrateur de recherche** (Claude Code CLI) → `orchestrator/`

### 7.4 Pour récupérer les 121 champs complets

Deux options :
1. **API Treekipedia** : contacter l'équipe Silvi pour accès API (le backend Express expose des endpoints species/research)
2. **Dump DB** : demander un dump PostgreSQL (le schéma est documenté, un `pg_dump` serait direct)

## 8. Conclusion d'inspection

**Le repo Treekipedia est utilisable immédiatement** sous licence MIT. On peut :
- Ingérer les 67 928 espèces (taxonomie) dès maintenant
- Ingérer les 3 487 lignes d'insights RDF (échantillon avec provenance complète)
- Récupérer le schéma SQL et l'adapter au métamodèle v6.2
- Récupérer l'ontologie RDF et la déployer dans un Jena Fuseki GSIE
- Récupérer les 11 zips GBIF pour les occurrences

**Pour les 121 champs écologiques complets** : il faut soit l'API Treekipedia, soit un dump DB. Le schéma étant documenté, un dump serait l'option la plus simple.

**Recommandation** : contacter l'équipe Silvi (support@silvi.earth, Telegram t.me/SilviProtocol) pour demander un dump PostgreSQL ou un accès API en lecture.

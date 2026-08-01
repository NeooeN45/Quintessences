# Treekipedia — Analyse d'opportunité d'intégration dans GSIE

**Date** : 2026-07-31
**Auteur** : GLM 5.2 High
**Statut** : Draft — en attente de validation du Fondateur
**Décision associée** : à créer (DEC-000040) si validation

---

## 1. Ce qu'est Treekipedia

### 1.1 Identité

**Treekipedia** est une base de données open source de connaissances sur les arbres, développée par **Silvi** (SilviProtocol), un protocole de reforestation basé sur la blockchain. C'est l'une des tentatives les plus complètes d'unifier les connaissances mondiales sur les espèces arborées en une plateforme interrogeable unique.

- **Repo GitHub** : `SilviProtocol/silvi` (public, 4 stars, licence non spécifiée explicitement mais open source)
- **Documentation** : `docs.silvi.earth/treekipedia`
- **Roadmap** : v1.0 lancée Earth Day 2025, phases 2-5 en cours

### 1.2 Échelle actuelle (novembre 2025)

| Métrique | Volume |
|---|---|
| Espèces enregistrées | **67 743** (50 797 espèces uniques + 16 946 sous-espèces) |
| Records bruts agrégés | **25 millions+** (10+ datasets globaux) |
| Observations | **17.6 millions** |
| Tuiles geohash (occurrences) | **5.7 millions** (L7, ~150m × 150m) |
| Images Wikimedia | **31 796** (avec attribution) |
| Polygones écorégions | **847** |
| Limites forêts intactes | **6 819** |
| Champs par espèce | **121** (taxonomie + écologie + morphologie + interactions) |

### 1.3 Sources de données agrégées

Treekipedia consolide des données de :
- **GBIF** (>3.11 milliards d'occurrences)
- **iNaturalist** (citizen science)
- **SiBBr** (Système d'Information sur la Biodiversité du Brésil)
- **SpeciesLink** (Brésil)
- **Wikimedia Commons** (images)
- **OneEarth** (bioregions, écorégions)
- **GloBI** (Global Biotic Interactions — pollinisation, herbivorie, parasitisme, dispersion)
- **10+ autres datasets globaux**

### 1.4 Architecture technique cible

Treekipedia utilise une **architecture hybride multi-tier** documentée dans `TREEKIPEDIA_KNOWLEDGE_ARCHITECTURE.md` (v1.0, novembre 2025) :

| Tier | Technologie | Usage | Taille |
|---|---|---|---|
| **Hot** | PostgreSQL + PostGIS + pgvector | Espèces actives, insights récents, occurrences live | ~10 GB |
| **Graph** | Apache AGE (Cypher dans PostgreSQL) | Traversées de graphe, réseaux d'interactions | ~50 GB |
| **Semantic** | Apache Jena Fuseki (RDF/SPARQL) | Raisonnement sémantique, ontologies, fédération | ~20 GB |
| **Cold** | S3/MinIO (Parquet) | Snapshots historiques, PDFs, images, datasets | ~500 GB |
| **Immutable** | IPFS | Ontologies versionnées, recherches publiées, attestations | ~5 GB |

**Ontologies alignées** :
- **Darwin Core** (DwC) — occurrences et taxonomie
- **Environment Ontology** (ENVO) — habitats
- **Plant Ontology** (PO) — structures morphologiques
- **Flora Phenotype Ontology** (FLOPO) — traits
- **PROV** (W3C) — provenance

### 1.5 Modèle "Insight" — l'innovation conceptuelle

Treekipedia introduit la notion d'**Insight** : une unité atomique de connaissance avec :
- `claim_type` (ex: "maximum_height", "soil_preference")
- `claim_value` (JSON flexible)
- `confidence` (0.0-1.0)
- `methodology` (comment cette connaissance a été produite)
- `model_version` (quel LLM/agent a généré l'insight)
- `evidence[]` (sources supportant l'insight)
- `provenance` (traçabilité complète)

**Catégories d'insights** (10 primaires) :
1. Taxonomic (changements de noms, synonymes, phylogénie)
2. Morphological (caractéristiques physiques, croissance)
3. Physiological (photosynthèse, efficacité eau, nutriments)
4. Ecological (habitat, succession, perturbations)
5. Interactions (pollinisation, herbivorie, symbiose)
6. Biogeochemical (cycle nutriments, séquestration carbone)
7. Phenological (floraison, fructification, chute feuilles)
8. Ethnobotanical (usages traditionnels, noms locaux)
9. Agronomic (pratiques de culture, rendements)
10. Conservation (menaces, tendances, restauration)

---

## 2. Pourquoi c'est exceptionnel pour GSIE

### 2.1 Le gap que Treekipedia comble

GSIE a aujourd'hui **25 connaissances validées** et des pilotes d'extraction pour ~8 essences. L'ambition (DEC-000012) est "le million d'entrées". Treekipedia a déjà **67 743 espèces** avec **121 champs** chacune.

**Gain potentiel** : passer de 25 connaissances à **50 000+ espèces structurées** en une ingestion. C'est un saut de 3 ordres de grandeur.

### 2.2 Compatibilité architecturale

| Dimension | Treekipedia | GSIE | Compatibilité |
|---|---|---|---|
| SGBD | PostgreSQL + PostGIS | PostgreSQL 16 + PostGIS 3.4 | ✅ Identique |
| Graphe | Apache AGE (Cypher) | Apache AGE (Cypher) | ✅ Identique |
| Sémantique | Apache Jena (RDF/SPARQL) | Pas encore | 🟡 À ajouter |
| Vectoriel | pgvector (embeddings) | Pas encore | 🟡 À ajouter |
| Stockage froid | S3/MinIO (Parquet) | Pas encore | 🟡 À ajouter |
| Ontologies | Darwin Core, ENVO, PO, FLOPO, PROV | Métamodèle v6.2 (73 types) | 🟡 Mapping à faire |

**Conclusion** : L'architecture de Treekipedia est **exactement celle que GSIE vise**. Tu peux réutiliser leur schéma et leurs ontologies presque tel quels.

### 2.3 Ce que Treekipedia a que GSIE n'a pas encore

1. **Volume** : 67k espèces vs 25 connaissances
2. **Ontologie formelle** : Darwin Core + ENVO + PO + FLOPO + PROV (standards W3C/TDWG)
3. **Modèle Insight** : unité atomique de connaissance avec confiance + provenance + modèle
4. **Interactions biotiques** : GloBI (pollinisation, herbivorie, parasitisme, dispersion) — 121 champs incluant `Globi_pollinatedBy`, `Globi_eatenBy`, `Globi_hasParasite`, `Globi_hasDispersalVector`, `Globi_preyedUponBy`
5. **Données géospatiales d'occurrence** : 5.7M tuiles geohash, 847 écorégions, 6 819 forêts intactes
6. **Images** : 31 796 images Wikimedia avec attribution
7. **Embeddings** : pgvector pour similarité sémantique entre espèces
8. **Multi-tier storage** : hot/graph/semantic/cold/immutable
9. **SPARQL endpoint** : interrogation sémantique fédérée
10. **Dual human/AI** : champs `_human` et `_ai` pour chaque attribut écologique

### 2.4 Ce que GSIE a que Treekipedia n'a pas

1. **Chaîne de raisonnement déterministe** (Evidence→Knowledge→...→Validation) — Treekipedia n'a pas de raisonnement
2. **Niveaux de preuve A-F** — Treekipedia a `confidence` (0-1) mais pas de matrice type_source × type_contenu
3. **Garde-fou anti-invention** — Treekipedia fait confiance aux LLM pour extraire
4. **Moteurs domaine** (GIS, Climate, Pedology, Botanical, Forest Dynamics) — Treekipedia est taxonomique uniquement
5. **Diagnostic sylvicole** — Treekipedia ne fait pas de diagnostic
6. **Recommandations contournables** — Treekipedia ne recommande pas
7. **Constitution scientifique** — Treekipedia n'a pas de gouvernance scientifique formelle
8. **Apps terrain** (GeoSylva) — Treekipedia est une plateforme web, pas une app terrain
9. **Jumeau numérique 3D** (UE5.8) — Treekipedia n'a pas de visualisation 3D
10. **Multi-domaine** (forêt+feu+faune+eau+végétation) — Treekipedia est arbres uniquement

**Conclusion** : Treekipedia et GSIE sont **complémentaires**. Treekipedia apporte le volume de données et l'ontologie formelle. GSIE apporte le raisonnement, le diagnostic, et les apps terrain. L'intégration crée un système **supérieur à la somme des parties**.

---

## 3. Comment intégrer Treekipedia dans GSIE

### 3.1 Stratégie recommandée — ingestion en 3 phases

#### Phase A — Récupération des données brutes (1-2 jours)

**Objectif** : Cloner le repo SilviProtocol/silvi et extraire les datasets.

```bash
# Cloner le repo
git clone https://github.com/SilviProtocol/silvi.git
cd silvi/treekipedia

# Données disponibles :
# - treekipedia/data/ : CSV/Parquet des 67k espèces
# - treekipedia/sparql/ : Configuration Jena Fuseki
# - treekipedia/docs/ : Documentation ontologie
# - ontology-generator/ : Schémas d'ontologie
```

**Vérifications préalables** :
- Licence : le repo est public mais la licence n'est pas explicitement spécifiée. **Vérifier avant ingestion**. Le lightpaper mentionne "open source" et les données sources (GBIF, iNaturalist) sont sous licences ouvertes (CC-BY, CC0).
- Attribution : les 31 796 images Wikimedia ont leurs attributions — à préserver.
- Provenance : chaque record doit garder sa source d'origine (GBIF, iNaturalist, etc.) pour respecter GSIE-CON-005 (traçabilité).

#### Phase B — Mapping vers le métamodèle v6.2 (3-5 jours)

**Objectif** : Mapper les 121 champs Treekipedia vers les 73 types noyau du métamodèle v6.2.

**Mapping proposé** (première analyse) :

| Champ Treekipedia | Type noyau v6.2 | Notes |
|---|---|---|
| `species_scientific_name` | `entity` (kind=species) | Entité taxonomique |
| `taxon_id` / `taxon_id_new` | `entity` (external_ref) | Double ID à réconcilier |
| `family`, `genus`, `class`, `taxonomic_order` | `entity` (lineage) | Hiérarchie taxonomique |
| `general_description_human` / `_ai` | `assertion` (claim_kind=description) | Dual human/AI → evidence_level |
| `ecological_function_human` / `_ai` | `assertion` (claim_kind=ecological_role) | |
| `elevation_ranges` | `assertion` (claim_kind=elevation_range) | |
| `compatible_soil_types` | `assertion` (claim_kind=soil_preference) | |
| `habitat` | `assertion` (claim_kind=habitat) | |
| `growth_form`, `leaf_type` | `assertion` (claim_kind=morphological_trait) | |
| `countries_native`, `countries_invasive`, `countries_introduced` | `assertion` (claim_kind=distribution) | |
| `Globi_pollinatedBy`, `Globi_eatenBy`, etc. | `assertion` (claim_kind=biotic_interaction) | Relations interspécifiques |
| `ecoregions`, `biomes` | `assertion` (claim_kind=ecoregion) | |
| `Present_Intact_Forest` | `assertion` (claim_kind=intact_forest_presence) | |
| Soil texture/chemistry (all/dominant/preferred/tolerated) | `assertion` (claim_kind=soil_preference_gradient) | Granularité remarquable |

**Règle de mapping pour le dual human/AI** :
- Champ `_human` présent → `evidence_level` = E (Expert) ou B (si source peer-reviewed)
- Champ `_ai` uniquement → `evidence_level` = D (Hypothèse) avec `methodology` = "LLM extraction"
- Les deux présents → `evidence_level` = min(human, ai) + note dans `provenance`

#### Phase C — Ingestion via Forge → Knowledge Engine (5-10 jours)

**Objectif** : Utiliser Forge pour ingérer les données Treekipedia, puis Knowledge Engine pour persister.

**Pipeline** :
```
Treekipedia CSV/Parquet
  ↓ Forge (connecteur custom)
Manifeste QDS-TREEKIPEDIA-v1.0 (provenance, hash, licences)
  ↓ KnowledgeIngestRequest
Evidence Engine (évaluation niveau de preuve par champ)
  ↓ SourcedFact
Knowledge Engine (persistance PostgreSQL + AGE)
  ↓
Graphe de connaissances GSIE (50 000+ espèces)
```

**Étapes détaillées** :

1. **Forge** : créer un connecteur `treekipedia` dans `Forge/forge/connectors/`
   - Lit les CSV/Parquet du repo silvi
   - Produit un manifeste `QDS-TREEKIPEDIA-v1.0` conforme à `08_DATASETS`
   - Garde la provenance (GBIF, iNaturalist, etc.) pour chaque record

2. **Mapping** : créer un mapper `treekipedia_to_v62` dans `GSIE/API/src/gsie_api/ingestion/`
   - Transforme les 121 champs en `SourcedFact` (format d'échange)
   - Applique le mapping de la Phase B
   - Gère le dual human/AI (evidence_level)

3. **Evidence Engine** : évalue chaque fait
   - Fait human-sourced → niveau de preuve E (Expert) ou B (si référentiel)
   - Fait AI-sourced → niveau de preuve D (Hypothèse) avec `methodology` = "LLM"
   - Fait GloBI → niveau de preuve B (référentiel officiel)

4. **Knowledge Engine** : persiste dans PostgreSQL + AGE
   - 50 000+ entités `entity` (kind=species)
   - ~500 000+ assertions (121 champs × 50k espèces, filtré)
   - Graphe d'interactions biotiques (GloBI) dans AGE

5. **Validation** : garde-fou anti-invention (RFC-0014 §3.2)
   - Vérifier que chaque fait a une source traçable
   - Statut `quarantine` pour les faits AI-sourced sans source humaine
   - Statut `rejete` pour les faits sans provenance

### 3.2 Ce qu'il faut ajouter à GSIE pour profiter pleinement

#### pgvector (embeddings sémantiques)

Treekipedia utilise pgvector pour la similarité entre espèces. GSIE ne l'a pas encore.

```sql
-- Migration Alembic
CREATE EXTENSION IF NOT EXISTS vector;

-- Table d'embeddings
ALTER TABLE gsie_botanique.entity_embedding
    ADD COLUMN embedding vector(768);

-- Index pour similarité cosinus
CREATE INDEX idx_entity_embedding
    ON gsie_botanique.entity_embedding
    USING ivfflat (embedding vector_cosine_ops);
```

**Usage** : "trouver les espèces écologiquement similaires au chêne pédonculé" → requête par similarité vectorielle.

#### Apache Jena Fuseki (couche sémantique RDF/SPARQL)

Treekipedia utilise Jena pour SPARQL. GSIE utilise AGE (Cypher). Les deux sont complémentaires.

**Recommandation** : ajouter un service Jena Fuseki dans `docker-compose.yml` pour exposer une couche RDF/SPARQL au-dessus de PostgreSQL. Cela permet :
- Interopérabilité avec l'écosystème scientifique (TDWG, GBIF, OBIS)
- Requêtes fédérées across external SPARQL endpoints
- Raisonnement sémantique (inférence OWL)

```yaml
# docker-compose.yml — ajout
fuseki:
    image: stain/jena-fuseki:latest
    ports:
        - "3030:3030"
    volumes:
        - ./fuseki/data:/fuseki/data
        - ./fuseki/config:/fuseki/config
    environment:
        - ADMIN_PASSWORD=${FUSEKI_ADMIN_PASSWORD}
```

#### Ontologies Darwin Core + ENVO

Importer les ontologies standards dans GSIE :
- **Darwin Core** : `http://rs.tdwg.org/dwc/terms/` — taxonomie et occurrences
- **ENVO** : `http://purl.obolibrary.org/obo/ENVO_` — habitats et biomes
- **PROV** : `http://www.w3.org/ns/prov#` — provenance (déjà aligné avec CON-005)

**Fichier à créer** : `GSIE/KNOWLEDGE/ONTOLOGIES/STANDARDS_ALIGNMENT.md`

### 3.3 Précautions et garde-fous GSIE

#### Garde-fou anti-invention (RFC-0014 §3.2)

Treekipedia utilise des LLM (GPT-4, Claude) pour extraire des insights. GSIE exige la **citation mot pour mot**. Il faut donc :

1. **Séparer les faits human-sourced des faits AI-sourced** lors de l'ingestion
2. **Marquer les faits AI-sourced** avec `evidence_level = D` (Hypothèse) et `methodology = "LLM extraction via Treekipedia"`
3. **Mettre en `quarantine`** les faits AI-sourced qui n'ont pas de source humaine corroborante
4. **Préserver la provenance** : chaque fait doit tracer sa source d'origine (GBIF, iNaturalist, paper, LLM)

#### Conflits bibliographiques (S-3)

Treekipedia peut avoir des valeurs différentes de GSIE pour la même espèce (ex: hauteur max du chêne pédonculé). La Constitution S-3 exige la **conservation des deux positions**.

**Règle** : si un fait Treekipedia entre en conflit avec un fait GSIE existant :
- Créer une `revision` (CON-010) avec les deux valeurs
- Marquer `conflict_status = divergent`
- Ne **jamais** faire une moyenne arbitraire
- Documenter le conflit dans `provenance`

#### Licence et droits d'usage

**À vérifier impérativement avant ingestion** :
- Le repo `SilviProtocol/silvi` est public mais la licence n'est pas explicitement spécifiée dans le README
- Les données sources (GBIF, iNaturalist) sont sous licences ouvertes (CC-BY, CC0)
- Les insights générés par LLM sont probablement sous licence ouverte (à confirmer)
- Les images Wikimedia ont leurs propres licences (CC-BY-SA, CC0, etc.)

**Recommandation** : contacter l'équipe Silvi pour clarifier la licence avant ingestion massive. Pour une ingestion partielle (taxonomie + occurrences GBIF), la licence GBIF (CC-BY) s'applique.

#### Qualité des données AI-sourced

Treekipedia acknowledge que les champs `_ai` sont générés par LLM et peuvent contenir des erreurs. GSIE doit :
- **Ne jamais utiliser un fait AI-sourced sans validation humaine** pour un diagnostic sylvicole
- **Afficher `evidence_level = D`** à l'utilisateur pour les faits AI-sourced
- **Permettre au forestier de contester** (CON-001 — le forestier reste le décideur)

---

## 4. Impact estimé sur GSIE

### 4.1 Volume de connaissances

| Métrique | Avant | Après ingestion Treekipedia | Gain |
|---|---|---|---|
| Espèces structurées | ~8 (pilotes) | **50 000+** | ×6 250 |
| Assertions (faits) | ~25 | **~500 000+** | ×20 000 |
| Interactions biotiques | 0 | **~100 000+** (GloBI) | ∞ |
| Occurrences géospatiales | 0 | **5.7 millions** | ∞ |
| Images | 0 | **31 796** | ∞ |
| Écorégions | 0 | **847** | ∞ |

### 4.2 Déblocage de moteurs

| Moteur | Blocker actuel | Déblocage par Treekipedia |
|---|---|---|
| **Botanical Engine** | Pas d'autécologie | ✅ Champs `ecological_function`, `habitat`, `compatible_soil_types`, `elevation_ranges` |
| **Reasoning Engine** | Pas d'autécologie pour raisonner | ✅ 121 champs d'autécologie par espèce |
| **Diagnostic Engine** | Pas de données stationnelles | ✅ `soil_texture`, `soil_ph`, `elevation`, `precipitation` |
| **Correlation Engine** | Pas de données à corréler | ✅ 500k+ faits à corréler |
| **Simulation Engine** | Pas de modèles de croissance | 🟡 Partiel — `growth_form`, `max_height`, `growth_rate` disponibles |

### 4.3 Position concurrentielle

| Dimension | Avant | Après |
|---|---|---|
| Volume de connaissances | 🔴 25 (vs Treekipedia 67k) | 🟢 50k+ (au niveau de Treekipedia) |
| Ontologie formelle | 🔴 Aucune | 🟢 Darwin Core + ENVO + PO + FLOPO |
| Interactions biotiques | 🔴 Aucune | 🟢 GloBI (pollinisation, herbivorie, etc.) |
| Interopérabilité scientifique | 🔴 Aucune | 🟢 SPARQL + standards W3C/TDWG |
| Reasoning sur données réelles | 🔴 Blocker autécologie | 🟢 Débloqué |

---

## 5. Plan d'action recommandé

### 5.1 Immédiat (cette semaine)

1. **Cloner le repo** `SilviProtocol/silvi` et inspecter les données réelles
2. **Vérifier la licence** (contacter l'équipe Silvi si nécessaire)
3. **Créer la DEC-000040** — "Ingestion Treekipedia dans l'Encyclopédie de l'Écosystème"
4. **Créer la RFC-0030** — "Mapping Treekipedia → métamodèle v6.2"

### 5.2 Court terme (2 prochaines semaines)

5. **Créer le connecteur Forge** `treekipedia` dans `Forge/forge/connectors/`
6. **Créer le mapper** `treekipedia_to_v62` dans `GSIE/API/src/gsie_api/ingestion/`
7. **Ajouter pgvector** à PostgreSQL (migration Alembic)
8. **Ingestion pilote** : 100 espèces forestières françaises (chênes, hêtres, pins, sapins, etc.)
9. **Tests** : vérifier que le garde-fou anti-invention fonctionne sur les données Treekipedia

### 5.3 Moyen terme (mois prochain)

10. **Ingestion massive** : 50 000+ espèces
11. **Ajouter Apache Jena Fuseki** au docker-compose
12. **Importer les ontologies** Darwin Core + ENVO + PROV
13. **Créer le SPARQL endpoint** GSIE
14. **Débloquer Reasoning/Diagnostic** avec l'autécologie Treekipedia

### 5.4 Long terme (3 mois)

15. **Mapping GloBI → graphe AGE** : interactions biotiques dans Apache AGE
16. **Embeddings pgvector** : similarité sémantique entre espèces
17. **Golden Bench** : 50 cas "or" utilisant les données Treekipedia
18. **Publication scientifique** : "GSIE + Treekipedia — un DSS forestier evidence-based à l'échelle mondiale"

---

## 6. Risques et mitigation

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Licence non ouverte | Faible | Élevé | Contacter Silvi avant ingestion ; les données sources (GBIF) sont CC-BY |
| Données AI-sourced erronées | Élevé | Moyen | evidence_level=D + quarantine + garde-fou anti-invention |
| Conflits avec données GSIE | Moyen | Faible | S-3 (conservation des deux positions) + revision CON-010 |
| Volume trop important pour PostgreSQL | Faible | Moyen | Multi-tier storage (hot/cold) + partitionnement |
| Mapping v6.2 incomplet | Moyen | Moyen | Itération : mapper les champs critiques d'abord, étendre ensuite |
| Dépendance à Treekipedia | Faible | Faible | Ingestion one-shot + versioning (CON-010) — pas de dépendance runtime |

---

## 7. Conclusion

**Treekipedia est l'opportunité la plus stratégique pour GSIE en 2026**. L'ingestion de leurs 50 000+ espèces structurées avec 121 champs chacune ferait passer GSIE de 25 connaissances à 500 000+ faits — un saut de 3 ordres de grandeur qui positionnerait GSIE au niveau de Treekipedia sur le volume, tout en conservant la supériorité sur le raisonnement, le diagnostic, et les apps terrain.

L'architecture de Treekipedia est **exactement celle que GSIE vise** (PostgreSQL + PostGIS + AGE + Jena + pgvector). L'intégration est donc naturelle et non une migration.

**Recommandation** : valider la DEC-000040 et lancer l'ingestion pilote (100 espèces) dans les 2 prochaines semaines.

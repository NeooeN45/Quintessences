# ENCYCLOPEDIA_DATABASE_SCHEMA — Schéma de base de données de l'Encyclopédie de l'Écosystème

| Champ | Valeur |
|---|---|
| **Livrable** | 309 — Encyclopédie Database Schema |
| **Phase** | 3 — Connaissance |
| **Statut** | Review |
| **Date de révision** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-002, GSIE-CON-003, GSIE-CON-005, GSIE-CON-010 |
| **Constitutions liées** | Scientifique (S-1 à S-7) |
| **Directive d'ouverture** | GSIE-DIR-0007 (DEC-000011), GSIE-DIR-0008 (DEC-000012) |
| **Documents connexes** | 302 (Knowledge Method), 303 (Forest Ontology), 304 (Knowledge Graph Specification), 305 (Dataset Catalog), 306 (Evidence Framework), 308 (Knowledge Base Seed) |

---

## 1. Objet

Définir le schéma physique de base de données de l'Encyclopédie de
l'Écosystème GSIE (GSIE-DIR-0008, DEC-000012) : la structure des tables
PostgreSQL/PostGIS, le graphe Neo4j, les index Elasticsearch et le
triple store RDF/OWL Apache Jena.

Ce schéma opérationnalise l'ambition de la directive GSIE-DIR-0008 :
construire la plus grande base de données structurée, sourcée et
traçable sur l'écosystème, à l'échelle du million d'entrées minimum. Il
traduit en DDL et en Cypher les structures logiques définies par les
livrables 302 (KnowledgeObject), 304 (graphe de connaissances) et 306
(niveaux de preuve A-F).

Le présent document est un schéma d'architecture (Phase 3). Il ne
contient aucun code métier : les blocs SQL et Cypher sont des
définitions de structure (DDL), pas des fonctions applicatives.
L'implémentation physique et l'optimisation des requêtes relèvent de la
Phase 4.

### 1.1 Principes directeurs

| Principe | Source constitutionnelle | Traduction technique |
|---|---|---|
| Toute donnée est sourcée | S-1, CON-002 | FK obligatoire vers `sources` sur toute table de connaissance |
| Toute donnée porte son niveau de preuve | S-2 | Colonne `evidence_level` avec CHECK A-F |
| Conflits conservés | S-3 | Table `conflits` dédiée, aucune suppression |
| Incertitude explicite | S-5 | Colonnes `incertitude_min` / `incertitude_max` |
| Domaines de validité explicites | S-5 | Table `domaines_validite` liée |
| Versioning obligatoire | CON-010, S-7 | Tables d'historique, jamais de DELETE |
| Traçabilité | CON-005 | Table `ingestion_logs` |
| 10 domaines scientifiques | S-6 | Enum `domaine_scientifique` |
| Identifiants stables et citables | S-7, CON-010 | Colonnes `gsie_id` UNIQUE, séquences dédiées |

---

## 2. Vue d'ensemble de l'architecture

L'Encyclopédie repose sur quatre couches de stockage spécialisées,
chacune ayant une responsabilité unique. Aucune couche ne duplique la
responsabilité d'une autre : le graphe porte la topologie, PostgreSQL
porte les métadonnées et la géo, Elasticsearch porte la recherche
full-text, Jena porte la sémantique et l'alignement Linked Open Data.

```
┌─────────────────────────────────────────────────────────────────────┐
│               ENCYCLOPÉDIE DE L'ÉCOSYSTÈME GSIE                      │
│                  (GSIE-DIR-0008, DEC-000012)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────┐ │
│  │   Neo4j         │  │  PostgreSQL 16   │  │  Elasticsearch 8   │ │
│  │   (graphe)      │  │  + PostGIS 3     │  │  (full-text)       │ │
│  │                 │  │  (métadonnées    │  │                    │ │
│  │  Nœuds :        │  │   + géo)         │  │  Index :           │ │
│  │  - KnowledgeObj │  │                  │  │  - connaissances   │ │
│  │  - Essence      │  │  Tables :        │  │  - sources         │ │
│  │  - Sol          │  │  - sources       │  │  - taxons          │ │
│  │  - Climat       │  │  - datasets      │  │                    │ │
│  │  - Station      │  │  - connaissances │  │  Analyseur         │ │
│  │  - Habitat      │  │  - taxons        │  │  français          │ │
│  │  - Pathologie   │  │  - types_sol     │  │                    │ │
│  │  - Insecte      │  │  - habitats      │  └────────────────────┘ │
│  │  - Modele       │  │  - pathologies   │                         │
│  │                 │  │  - insectes      │  ┌────────────────────┐ │
│  │  Arêtes :       │  │  - modeles       │  │  Apache Jena       │ │
│  │  - est_adapte_a │  │  - conflits      │  │  (triple store     │ │
│  │  - influence    │  │  - domaines      │  │   RDF/OWL)         │ │
│  │  - depend_de    │  │  - versions      │  │                    │ │
│  │  - est_valide_par│ │  - ingestion     │  │  Ontologie :       │ │
│  │  - contredit    │  │  - utilisateurs  │  │  - gsie:KO         │ │
│  │  - croit_mieux  │  │                  │  │  - gsie:Essence    │ │
│  │  - substituable │  │  PostGIS :       │  │  - gsie:Sol        │ │
│  │                 │  │  - géométries    │  │  - owl:sameAs      │ │
│  │  10M nœuds min  │  │  - index GIST    │  │    (GBIF, WRB,     │ │
│  │                 │  │                  │  │     INPN)          │ │
│  └─────────────────┘  └──────────────────┘  └────────────────────┘ │
│         │                     │                     │              │
│         └──────────┬──────────┴─────────────────────┘              │
│                    │                                                │
│              ┌─────▼──────┐                                        │
│              │  API GSIE  │  REST / GraphQL                         │
│              │  (Phase 4) │  gsie://K-XXXXXXXXXX                    │
│              └────────────┘                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1 Responsabilités par couche

| Couche | Technologie | Responsabilité | Volume cible |
|---|---|---|---|
| Graphe | Neo4j 5.x | Topologie des connaissances, traversal, relations versionnées | 10M nœuds, 50M arêtes |
| Relationnel | PostgreSQL 16 + PostGIS 3.4 | Métadonnées structurées, géométries, historique, audit | Millions de lignes |
| Recherche | Elasticsearch 8.x | Recherche full-text française, facettage, auto-complétion | Index sur descriptions |
| Sémantique | Apache Jena (TDB2) | Triple store RDF/OWL, SPARQL, alignement LOD | Millions de triplets |

### 2.2 Flux de données entre couches

```
Ingestion → PostgreSQL (métadonnées + versioning)
         → Neo4j (nœud + arêtes)
         → Elasticsearch (indexation full-text)
         → Jena (publication RDF, alignement ontologies)
```

PostgreSQL est la source de vérité pour les métadonnées et
l'historique. Neo4j est la source de vérité pour la topologie.
Elasticsearch et Jena sont des projections dérivées (index de
recherche et publication sémantique), régénérables à partir de
PostgreSQL et Neo4j.

---

## 3. Schéma PostgreSQL/PostGIS

### 3.1 Tables principales

Le schéma PostgreSQL porte les métadonnées structurées, l'historique
des versions, les conflits, les domaines de validité, les entités
taxonomiques et référentielles, et les logs d'ingestion. Il ne porte
pas la topologie des relations (rôle de Neo4j) ni le contenu full-text
(rôle d'Elasticsearch).

L'extension `pgcrypto` est requise pour le hachage des mots de passe et
`uuid-ossp` (ou `gen_random_uuid`) pour les UUID v4 internes. Les
identifiants métier GSIE (GSIE-K-XXXXXXXXXX, etc.) sont des chaînes
générées par séquence et formatées.

#### 3.1.1 Table `sources`

Sources scientifiques référencées (S-1). Chaque connaissance, chaque
relation et chaque dataset doit pointer vers au moins une source.

```sql
CREATE TABLE sources (
    id                  SERIAL PRIMARY KEY,
    gsie_id             VARCHAR(20) NOT NULL UNIQUE,   -- GSIE-SRC-XXXXXX
    titre               TEXT NOT NULL,
    auteur              TEXT,
    annee               INTEGER,
    type_source         VARCHAR(30) NOT NULL CHECK (
                            type_source IN (
                                'peer_reviewed',
                                'referentiel_officiel',
                                'document_technique',
                                'connaissance_experte',
                                'observation_terrain'
                            )
                        ),
    reference_externe   TEXT,          -- DOI, URL, ISBN
    organisme_producteur TEXT,
    licence             VARCHAR(100),
    resume              TEXT,
    date_integration    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    statut              VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (
                            statut IN ('actif', 'obsolete', 'quarantine')
                        ),
    version_source      VARCHAR(50),
    CONSTRAINT chk_gsie_id_source CHECK (
        gsie_id ~ '^GSIE-SRC-[0-9]{6}$'
    )
);
```

#### 3.1.2 Table `datasets`

Datasets catalogués (livrable 305). Chaque dataset référence un
organisme producteur, une licence et des métadonnées de couverture.

```sql
CREATE TABLE datasets (
    id                  SERIAL PRIMARY KEY,
    gsie_id             VARCHAR(15) NOT NULL UNIQUE,   -- GSIE-DS-XXX
    nom                 TEXT NOT NULL,
    organisme_producteur TEXT NOT NULL,
    categorie           VARCHAR(10) NOT NULL CHECK (
                            categorie IN ('A','B','C','D','E','F')
                        ),
    domaines_s6         TEXT[],        -- tableau des domaines S-6 couverts
    moteurs_consommateurs TEXT[],
    source_url          TEXT NOT NULL,
    licence             VARCHAR(100) NOT NULL,
    couverture_spatiale TEXT NOT NULL,
    couverture_temporelle_de DATE,
    couverture_temporelle_a DATE,
    resolution_spatiale TEXT,
    resolution_temporelle TEXT,
    format_distribution TEXT NOT NULL,
    version_referencee  VARCHAR(100) NOT NULL,
    qualite_precision   TEXT,
    contact             TEXT NOT NULL,
    statut_ingestion    VARCHAR(20) NOT NULL DEFAULT 'planifie' CHECK (
                            statut_ingestion IN (
                                'planifie', 'en_cours', 'ingeste',
                                'quarantine'
                            )
                        ),
    notes               TEXT,
    date_integration    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_id           INTEGER REFERENCES sources(id),
    CONSTRAINT chk_gsie_id_dataset CHECK (
        gsie_id ~ '^GSIE-DS-[0-9]{3}$'
    )
);
```

#### 3.1.3 Table `connaissances_meta`

Métadonnées des KnowledgeObject (livrable 302). Cette table contient la
version courante de chaque connaissance. L'historique complet est dans
`connaissances_versions`.

```sql
CREATE TABLE connaissances_meta (
    id                  SERIAL PRIMARY KEY,
    gsie_id             VARCHAR(25) NOT NULL UNIQUE,   -- GSIE-K-XXXXXXXXXX
    type                VARCHAR(20) NOT NULL CHECK (
                            type IN (
                                'concept', 'relation', 'regle',
                                'seuil', 'modele', 'classification'
                            )
                        ),
    titre               TEXT NOT NULL,
    description         TEXT NOT NULL,
    contenu             JSONB NOT NULL,                -- structure typée selon type
    evidence_level      CHAR(1) NOT NULL CHECK (
                            evidence_level IN ('A','B','C','D','E','F')
                        ),
    domaine_scientifique VARCHAR(60) NOT NULL CHECK (
                            domaine_scientifique IN (
                                'ecologie_forestiere',
                                'pedologie',
                                'dendrometrie',
                                'climatologie',
                                'botanique',
                                'pathologie',
                                'entomologie',
                                'sylviculture',
                                'biodiversite',
                                'dynamique_peuplements'
                            )
                        ),
    version             INTEGER NOT NULL DEFAULT 1,
    statut              VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (
                            statut IN ('actif', 'obsolete', 'quarantine')
                        ),
    source_id           INTEGER NOT NULL REFERENCES sources(id),
    source_secondaire_ids INTEGER[],   -- sources additionnelles (convergence)
    date_integration    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    date_revision       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    mots_cles           TEXT[],
    moteurs_consommateurs TEXT[],
    incertitude_min     DOUBLE PRECISION,
    incertitude_max     DOUBLE PRECISION,
    incertitude_unite   VARCHAR(20),
    confiance           DOUBLE PRECISION CHECK (confiance >= 0.0 AND confiance <= 1.0),
    cree_par            INTEGER REFERENCES utilisateurs(id),
    valide_par          INTEGER REFERENCES utilisateurs(id),
    CONSTRAINT chk_gsie_id_connaissance CHECK (
        gsie_id ~ '^GSIE-K-[0-9]{10}$'
    )
);
```

#### 3.1.4 Table `connaissances_versions`

Historique des versions de chaque connaissance (CON-010, S-7). Une
ligne par version. Jamais de suppression : une version obsolète reste
présente pour audit.

```sql
CREATE TABLE connaissances_versions (
    id                  SERIAL PRIMARY KEY,
    connaissance_id     INTEGER NOT NULL REFERENCES connaissances_meta(id),
    version             INTEGER NOT NULL,
    type                VARCHAR(20) NOT NULL,
    titre               TEXT NOT NULL,
    description         TEXT NOT NULL,
    contenu             JSONB NOT NULL,
    evidence_level      CHAR(1) NOT NULL CHECK (
                            evidence_level IN ('A','B','C','D','E','F')
                        ),
    source_id           INTEGER NOT NULL REFERENCES sources(id),
    statut              VARCHAR(20) NOT NULL CHECK (
                            statut IN ('actif', 'obsolete', 'quarantine')
                        ),
    justification       TEXT NOT NULL,
    rfc_reference       VARCHAR(20),          -- requis pour révisions majeures
    date_version        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cree_par            INTEGER REFERENCES utilisateurs(id),
    UNIQUE (connaissance_id, version)
);
```

#### 3.1.5 Table `conflits`

Conflits bibliographiques (S-3). Lorsque deux connaissances se
contredisent, les deux sont conservées et le conflit est documenté.
Aucune fusion arbitraire.

```sql
CREATE TABLE conflits (
    id                  SERIAL PRIMARY KEY,
    gsie_id             VARCHAR(25) NOT NULL UNIQUE,   -- GSIE-CFL-XXXXXX
    connaissance_a_id   INTEGER NOT NULL REFERENCES connaissances_meta(id),
    connaissance_b_id   INTEGER NOT NULL REFERENCES connaissances_meta(id),
    description         TEXT NOT NULL,
    source_a_id         INTEGER NOT NULL REFERENCES sources(id),
    source_b_id         INTEGER NOT NULL REFERENCES sources(id),
    statut              VARCHAR(20) NOT NULL DEFAULT 'ouvert' CHECK (
                            statut IN ('ouvert', 'documente', 'resolution_partielle')
                        ),
    date_detection      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    date_resolution     TIMESTAMPTZ,
    resolu_par          INTEGER REFERENCES utilisateurs(id),
    notes               TEXT,
    CONSTRAINT chk_conflit_distinct CHECK (
        connaissance_a_id <> connaissance_b_id
    ),
    CONSTRAINT chk_gsie_id_conflit CHECK (
        gsie_id ~ '^GSIE-CFL-[0-9]{6}$'
    )
);
```

#### 3.1.6 Table `domaines_validite`

Domaines de validité des connaissances (S-5). Une connaissance peut
avoir plusieurs domaines de validité (ex : plage de pH, plage
d'altitude, région géographique).

```sql
CREATE TABLE domaines_validite (
    id                  SERIAL PRIMARY KEY,
    connaissance_id     INTEGER NOT NULL REFERENCES connaissances_meta(id),
    parametre           VARCHAR(50) NOT NULL,   -- ex: 'ph', 'altitude', 'region'
    valeur_min          DOUBLE PRECISION,
    valeur_max          DOUBLE PRECISION,
    unite               VARCHAR(20),
    valeur_texte        TEXT,                   -- pour paramètres non numériques (region)
    CONSTRAINT chk_domaine_valeur CHECK (
        valeur_min IS NOT NULL OR valeur_texte IS NOT NULL
    )
);
```

#### 3.1.7 Table `taxons`

Taxons (essences, flore, faune). Identifiant GSIE-TAX-XXXXXXXX. Aligné
avec GBIF et INPN.

```sql
CREATE TABLE taxons (
    id                  SERIAL PRIMARY KEY,
    gsie_id             VARCHAR(20) NOT NULL UNIQUE,   -- GSIE-TAX-XXXXXXXX
    nom_scientifique    TEXT NOT NULL,
    nom_vernaculaire    TEXT,
    famille             VARCHAR(100),
    genre               VARCHAR(100),
    espece              VARCHAR(100),
    synonymes           TEXT[],
    rang_taxonomique    VARCHAR(30) CHECK (
                            rang_taxonomique IN (
                                'regne', 'embranchement', 'classe',
                                'ordre', 'famille', 'genre',
                                'espece', 'sous_espece', 'variete'
                            )
                        ),
    parent_taxon_id     INTEGER REFERENCES taxons(id),
    gbif_id             VARCHAR(20),            -- alignement GBIF
    inpn_id             VARCHAR(20),            -- alignement INPN
    taxonomie_version   VARCHAR(50),
    statut              VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (
                            statut IN ('actif', 'obsolete', 'quarantine')
                        ),
    date_integration    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_id           INTEGER NOT NULL REFERENCES sources(id),
    CONSTRAINT chk_gsie_id_taxon CHECK (
        gsie_id ~ '^GSIE-TAX-[0-9]{8}$'
    )
);
```

#### 3.1.8 Table `types_sol`

Types de sol (GSIE-PED-XXXX). Aligné avec le Référentiel Pédologique
Français (RPF) et WRB.

```sql
CREATE TABLE types_sol (
    id                  SERIAL PRIMARY KEY,
    gsie_id             VARCHAR(15) NOT NULL UNIQUE,   -- GSIE-PED-XXXX
    nom                 TEXT NOT NULL,
    referentiel         VARCHAR(20) NOT NULL CHECK (
                            referentiel IN ('RPF', 'WRB', 'SoilGrids')
                        ),
    version_referentiel VARCHAR(50) NOT NULL,
    categorie           VARCHAR(50),
    ph_min              DOUBLE PRECISION,
    ph_max              DOUBLE PRECISION,
    texture_dominante   VARCHAR(50),
    profondeur_typique_cm INTEGER,
    rum_typique_mm      INTEGER,
    parent_geologique   TEXT,
    description         TEXT,
    statut              VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (
                            statut IN ('actif', 'obsolete', 'quarantine')
                        ),
    date_integration    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_id           INTEGER NOT NULL REFERENCES sources(id),
    CONSTRAINT chk_gsie_id_sol CHECK (
        gsie_id ~ '^GSIE-PED-[0-9]{4}$'
    )
);
```

#### 3.1.9 Table `habitats`

Habitats écologiques (GSIE-HAB-XXXX). Aligné avec EUR28 et les Cahiers
d'habitats.

```sql
CREATE TABLE habitats (
    id                  SERIAL PRIMARY KEY,
    gsie_id             VARCHAR(15) NOT NULL UNIQUE,   -- GSIE-HAB-XXXX
    code_eur28          VARCHAR(20),
    syntaxonomie        TEXT,
    nom                 TEXT NOT NULL,
    description         TEXT,
    essences_typiques   TEXT[],
    region              TEXT,
    statut              VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (
                            statut IN ('actif', 'obsolete', 'quarantine')
                        ),
    date_integration    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_id           INTEGER NOT NULL REFERENCES sources(id),
    CONSTRAINT chk_gsie_id_habitat CHECK (
        gsie_id ~ '^GSIE-HAB-[0-9]{4}$'
    )
);
```

#### 3.1.10 Table `pathologies`

Pathologies forestières (GSIE-PATH-XXXX). Maladies, champignons
pathogènes, bactéries, virus.

```sql
CREATE TABLE pathologies (
    id                  SERIAL PRIMARY KEY,
    gsie_id             VARCHAR(15) NOT NULL UNIQUE,   -- GSIE-PATH-XXXX
    nom                 TEXT NOT NULL,
    agent_pathogene     TEXT,
    type_agent          VARCHAR(30) CHECK (
                            type_agent IN (
                                'champignon', 'bacterie', 'virus',
                                'phytoplasme', 'nematode', 'autre'
                            )
                        ),
    essences_cibles     TEXT[],
    symptomes           TEXT,
    gravite             VARCHAR(20) CHECK (
                            gravite IN ('faible', 'moderee', 'forte', 'mortelle')
                        ),
    saison_risque       VARCHAR(50),
    mesures_prophylaxie TEXT,
    description         TEXT,
    statut              VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (
                            statut IN ('actif', 'obsolete', 'quarantine')
                        ),
    date_integration    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_id           INTEGER NOT NULL REFERENCES sources(id),
    CONSTRAINT chk_gsie_id_pathologie CHECK (
        gsie_id ~ '^GSIE-PATH-[0-9]{4}$'
    )
);
```

#### 3.1.11 Table `insectes`

Insectes forestiers (GSIE-ENT-XXXX). Ravageurs, auxiliaires,
décomposeurs.

```sql
CREATE TABLE insectes (
    id                  SERIAL PRIMARY KEY,
    gsie_id             VARCHAR(15) NOT NULL UNIQUE,   -- GSIE-ENT-XXXX
    nom_scientifique    TEXT NOT NULL,
    nom_vernaculaire    TEXT,
    ordre               VARCHAR(50),
    famille             VARCHAR(100),
    role_ecologique     VARCHAR(30) CHECK (
                            role_ecologique IN (
                                'ravageur', 'auxiliaire', 'decomposeur',
                                'pollinisateur', 'xylophage', 'autre'
                            )
                        ),
    essences_cibles     TEXT[],
    degre_nuisibilite   VARCHAR(20) CHECK (
                            degre_nuisibilite IN (
                                'aucun', 'faible', 'modere', 'fort', 'epidemique'
                            )
                        ),
    cycle_vie           TEXT,
    description         TEXT,
    statut              VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (
                            statut IN ('actif', 'obsolete', 'quarantine')
                        ),
    date_integration    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_id           INTEGER NOT NULL REFERENCES sources(id),
    taxon_id            INTEGER REFERENCES taxons(id),
    CONSTRAINT chk_gsie_id_insecte CHECK (
        gsie_id ~ '^GSIE-ENT-[0-9]{4}$'
    )
);
```

#### 3.1.12 Table `modeles`

Modèles scientifiques (GSIE-MOD-XXXX). Croissance, dynamique,
propagation, climatique.

```sql
CREATE TABLE modeles (
    id                  SERIAL PRIMARY KEY,
    gsie_id             VARCHAR(15) NOT NULL UNIQUE,   -- GSIE-MOD-XXXX
    nom_modele          TEXT NOT NULL,
    type_modele         VARCHAR(30) NOT NULL CHECK (
                            type_modele IN (
                                'croissance', 'dynamique', 'propagation',
                                'climatique', 'hydrique', 'autre'
                            )
                        ),
    variables_entree    TEXT[] NOT NULL,
    variables_sortie    TEXT[] NOT NULL,
    parametres          JSONB,
    domaine_validite    TEXT,
    incertitude_min     DOUBLE PRECISION,
    incertitude_max     DOUBLE PRECISION,
    version_modele      VARCHAR(50) NOT NULL,
    description         TEXT,
    statut              VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (
                            statut IN ('actif', 'obsolete', 'quarantine')
                        ),
    date_integration    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_id           INTEGER NOT NULL REFERENCES sources(id),
    CONSTRAINT chk_gsie_id_modele CHECK (
        gsie_id ~ '^GSIE-MOD-[0-9]{4}$'
    )
);
```

#### 3.1.13 Table `moteurs_consommateurs`

Mapping entre connaissances et moteurs GSIE qui les consomment. Table
de jointure permettant de savoir quel moteur dépend de quelle
connaissance (utile pour la propagation des révisions, livrable 304
§6.5).

```sql
CREATE TABLE moteurs_consommateurs (
    id                  SERIAL PRIMARY KEY,
    connaissance_id     INTEGER NOT NULL REFERENCES connaissances_meta(id),
    moteur              VARCHAR(50) NOT NULL CHECK (
                            moteur IN (
                                'knowledge', 'evidence', 'correlation',
                                'reasoning', 'diagnostic', 'recommendation',
                                'validation', 'utilisateur', 'gis',
                                'climate', 'pedology', 'botanical',
                                'forest_dynamics', 'learning', 'simulation'
                            )
                        ),
    type_consommation   VARCHAR(20) NOT NULL CHECK (
                            type_consommation IN (
                                'lecture', 'requete', 'inférence', 'validation'
                            )
                        ),
    date_association    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (connaissance_id, moteur)
);
```

#### 3.1.14 Table `relations_meta`

Métadonnées des relations du graphe (versioning CON-010). Chaque
relation est elle-même un KnowledgeObject de type `relation` (livrable
304 §6). Cette table stocke le miroir relationnel pour audit et
requêtes SQL, en complément du graphe Neo4j.

```sql
CREATE TABLE relations_meta (
    id                  SERIAL PRIMARY KEY,
    relation_uuid       UUID NOT NULL UNIQUE,          -- stable à travers les versions
    version             INTEGER NOT NULL DEFAULT 1,
    sujet_gsie_id       VARCHAR(25) NOT NULL,          -- nœud source
    predicat            VARCHAR(30) NOT NULL CHECK (
                            predicat IN (
                                'est_adapte_a', 'influence', 'depend_de',
                                'est_valide_par', 'contredit',
                                'croit_mieux_sur', 'est_substituable_par'
                            )
                        ),
    objet_gsie_id       VARCHAR(25) NOT NULL,          -- nœud cible
    force               DOUBLE PRECISION CHECK (force >= 0.0 AND force <= 1.0),
    poids               DOUBLE PRECISION CHECK (poids >= 0.0 AND poids <= 1.0),
    description         TEXT,
    evidence_level      CHAR(1) NOT NULL CHECK (
                            evidence_level IN ('A','B','C','D','E','F')
                        ),
    source_id           INTEGER NOT NULL REFERENCES sources(id),
    conflit_id          INTEGER REFERENCES conflits(id),  -- si predicat = contredit
    contexte_application TEXT,
    statut              VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (
                            statut IN ('actif', 'obsolete', 'quarantine')
                        ),
    date_integration    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    justification       TEXT,
    rfc_reference       VARCHAR(20),
    UNIQUE (relation_uuid, version)
);
```

#### 3.1.15 Table `ingestion_logs`

Logs d'ingestion (CON-005, traçabilité). Chaque entrée ingérée dans
l'Encyclopédie est tracée : source, étape du pipeline, statut,
éventuelles erreurs.

```sql
CREATE TABLE ingestion_logs (
    id                  SERIAL PRIMARY KEY,
    batch_id            UUID NOT NULL,                 -- identifiant de lot d'ingestion
    source_id           INTEGER REFERENCES sources(id),
    dataset_id          INTEGER REFERENCES datasets(id),
    gsie_id_genere      VARCHAR(25),                   -- identifiant GSIE créé
    etape               VARCHAR(40) NOT NULL CHECK (
                            etape IN (
                                'extraction', 'classification',
                                'validation', 'integration_graphe',
                                'versioning', 'indexation',
                                'publication_rdf'
                            )
                        ),
    statut              VARCHAR(20) NOT NULL CHECK (
                            statut IN ('succes', 'echec', 'quarantine', 'rejete')
                        ),
    message             TEXT,
    detail_erreur       TEXT,
    date_log            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    utilisateur_id      INTEGER REFERENCES utilisateurs(id)
);
```

#### 3.1.16 Table `utilisateurs`

Utilisateurs et contributeurs de l'Encyclopédie. Rôles définis au
§10.

```sql
CREATE TABLE utilisateurs (
    id                  SERIAL PRIMARY KEY,
    nom_utilisateur     
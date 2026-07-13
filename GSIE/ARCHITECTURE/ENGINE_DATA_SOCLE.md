# ENGINE_DATA_SOCLE — Socle de données de chaque moteur GSIE et liens vers les apps externes

| Champ | Valeur |
|---|---|
| **Livrable** | 310 — Engine Data Socle |
| **Phase** | 3 — Connaissance |
| **Statut** | Review |
| **Date de révision** | 2026-07-13 |
| **Lois fondatrices** | GSIE-CON-003, GSIE-CON-005, GSIE-CON-007 |
| **Constitutions liées** | Scientifique (S-6), Technique (T-1, T-2) |
| **Directive d'ouverture** | GSIE-DIR-0007 + GSIE-DIR-0008 |
| **Documents connexes** | 204 (ordre développement), 206 (contrats interface), 302 (méthode connaissance), 303 (ontologie forêt), 304 (spec graphe), 305 (catalogue datasets), 309 (encyclopédie) |

---

## 1. Objet

Le présent livrable définit, pour chacun des 14 moteurs GSIE, le
**socle de données** qu'il consomme depuis l'Encyclopédie de
l'Écosystème (GSIE-DIR-0008) et ce qu'il produit en retour. Il
définit également les liens entre les moteurs et les six
applications externes de l'écosystème Quintessences : GeoSylva,
Ignis, Artemis, Hydro, Flora et QGISIA.

Le socle de données est le **contrat de données** entre
l'Encyclopédie (source centrale) et chaque moteur. Il précise, pour
chaque moteur :

- les types de `KnowledgeObject` consommés (livrable 302) ;
- les domaines scientifiques couverts (article S-6) ;
- les datasets du catalogue (livrable 305) ;
- les entités externes référencées (livrable 304) ;
- les productions du moteur ;
- les dépendances amont et les consommateurs aval ;
- les applications externes servies ;
- les tables PostgreSQL ou nœuds Neo4j spécifiques ;
- l'ordre de grandeur des volumes manipulés.

> **Note de gouvernance :** ce document est un document
> d'architecture de données (Phase 3). Il ne contient aucun code
> métier. L'implémentation des moteurs reste réservée à la Phase 4
> (DEC-000004). Les schémas de tables et de nœuds décrits ici sont
> des descriptions logiques, pas des schémas physiques.

---

## 2. Principe du socle de données

### 2.1 Définition

Le **socle** d'un moteur est l'ensemble des données qu'il **consomme**
depuis l'Encyclopédie et qu'il **produit** en sortie. Le socle définit
le contrat de données entre l'Encyclopédie et le moteur : ce que le
moteur a le droit de lire, ce qu'il a l'obligation de produire, et
sous quelles garanties (sourçage S-1, niveau de preuve S-2,
traçabilité CON-005, versioning CON-010).

### 2.2 Trois couches de données

Chaque socle se décompose en trois couches :

| Couche | Origine | Description |
|---|---|---|
| **Couche connaissances** | Encyclopédie (Knowledge Graph) | `KnowledgeObject` des 6 types (concept, relation, regle, seuil, modele, classification) — sourcés, versionnés, niveau de preuve |
| **Couche référentiels** | Datasets externes (livrable 305) | Données brutes IGN, Météo-France, INRAE, GBIF, Copernicus — ingérées et qualifiées |
| **Couche productions** | Le moteur lui-même | Sorties du moteur (diagnostics, corrélations, simulations, recommandations…) — re-sourcées et re-versionnées |

### 2.3 Règles du socle

1. **Aucune donnée n'entre dans un moteur sans niveau de preuve**
   (S-2). L'Evidence Engine qualifie toute donnée avant son entrée
   dans le Knowledge Graph ; les moteurs ne lisent que des
   connaissances déjà qualifiées.

2. **Aucune sortie de moteur n'est non sourcée** (CON-005). Toute
   production cite les sources et les moteurs qui l'ont générée
   (CON-004 : explicabilité).

3. **Le socle est versionné** (CON-010). Une évolution d'une donnée
   d'entrée entraîne une nouvelle version de la production qui en
   dépend.

4. **Le socle est découplé du moteur** (CON-007, T-2). Le moteur ne
   connaît que le contrat de données, pas le stockage interne de
   l'Encyclopédie. L'accès se fait par requêtes au Knowledge Graph
   (livrable 304) ou par les contrats d'interface (livrable 206).

5. **Le socle est aligné sur l'ordre de développement** (livrable
   204). Un moteur n'est alimenté que lorsque ses dépendances amont
   produisent leurs socles (§8).

---

## 3. Schéma global des flux

Le schéma ci-dessous montre l'Encyclopédie au centre, alimentant les
14 moteurs, qui à leur tour servent les 6 applications externes.

```
                    +-----------------------------------------+
                    |       ENCYCLOPEDIE DE L'ECOSYSTEME      |
                    |          (GSIE-DIR-0008)                |
                    |  Knowledge Graph + 24 datasets (305)    |
                    |  6 types KO x 10 domaines S-6           |
                    +-------------------+---------------------+
                                        |
            +---------------------------+---------------------------+
            |                           |                           |
            v                           v                           v
     +--------------+            +--------------+            +--------------+
     |   EVIDENCE   |  ------>   |  KNOWLEDGE   |  <------   |  LEARNING    |
     |   ENGINE     |            |  ENGINE      |            |  ENGINE      |
     +--------------+            +--------------+            +--------------+
                                        |
          +-------------+-------------+-------------+-------------+
          |             |             |             |             |
          v             v             v             v             v
     +--------+    +--------+    +--------+    +--------+    +--------+
     |  GIS   |    |BOTANIC.|    |PEDOLOGY|    |CLIMATE |    |FOREST  |
     | ENGINE |    | ENGINE |    | ENGINE |    | ENGINE |    | DYN.   |
     +--------+    +--------+    +--------+    +--------+    +--------+
          \             \             |             /             /
           \             \            |            /             /
            v             v           v           v             v
          +-----------------------------------------------+
          |              CORRELATION ENGINE               |
          +-----------------------+-----------------------+
                                  |
                                  v
          +-----------------------------------------------+
          |              REASONING ENGINE                 |
          +-----------------------+-----------------------+
                                  |
                                  v
          +-----------------------------------------------+
          |              DIAGNOSTIC ENGINE                |
          +-----------------------+-----------------------+
                                  |
                                  v
          +-----------------------------------------------+
          |            SIMULATION ENGINE                  |
          +-----------------------+-----------------------+
                                  |
                                  v
          +-----------------------------------------------+
          |           RECOMMENDATION ENGINE               |
          +-----------------------+-----------------------+
                                  |
                                  v
          +-----------------------------------------------+
          |             VALIDATION ENGINE                 |
          +-----------------------+-----------------------+
                                  |
                                  v
                    +---------------------------+
                    |     SORTIES VALIDEES      |
                    |  (ValidatedOutput, 206)   |
                    +-------------+-------------+
                                  |
          +-----------+-----------+-----------+-----------+-----------+-----------+
          |           |           |           |           |           |           |
          v           v           v           v           v           v
     +-----------+ +-----------+ +-----------+ +-----------+ +-----------+ +-----------+
     | GEOSYLVA  | |  IGNIS    | |  ARTEMIS  | |  QGISIA   | |  HYDRO    | |  FLORA    |
     |  (foret)  | | (incendie)| | (faune)   | | (QGIS+IA) | |  (eau)    | | (végétal) |
     +-----------+ +-----------+ +-----------+ +-----------+ +-----------+ +-----------+
```

Légende : les flèches représentent les flux de données principaux.
Les moteurs transverses (Evidence, Knowledge, Learning) encadrent le
pipeline. Les moteurs domaine (GIS, Botanical, Pedology, Climate,
Forest Dynamics) alimentent le cœur d'intelligence (Correlation →
Reasoning → Diagnostic → Simulation → Recommendation → Validation).
Les applications externes consomment les sorties validées via l'API
GSIE (livrable 207).

---

## 4. Socle par moteur

Les 14 moteurs sont décrits ci-dessous dans l'ordre du livrable 204.

### 4.1 — Evidence Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Évalue les sources entrantes, assigne un niveau de preuve A-F (S-2) à chaque connaissance candidate avant son intégration au Knowledge Graph. Filtre amont obligatoire du pipeline. |
| **Consomme (types KnowledgeObject)** | `concept` (définitions de critères d'évaluation), `regle` (règles d'assignation de niveau de preuve), `classification` (typologie des sources S-1) |
| **Consomme (domaines S-6)** | Tous les 10 domaines (l'Evidence Engine est transverse : il qualifie des connaissances de tous les domaines) |
| **Consomme (datasets)** | Aucun dataset brut directement — il consomme les métadonnées de sourçage des datasets (DS-001 à DS-024) pour évaluer la fiabilité des sources |
| **Consomme (entités externes)** | `Publication` (sources scientifiques à évaluer) |
| **Produit** | `QualifiedKnowledge` (connaissance + niveau de preuve + source + version), `ReassessmentSignal` (signaux de réévaluation vers Learning) |
| **Requêtes typiques** | 1. « Quels critères s'appliquent à une source de type peer_reviewed en pédologie ? » 2. « Quel niveau de preuve assigner à une observation terrain non publiée en dendrométrie ? » 3. « Quelles connaissances ont un niveau F contesté ? » |
| **Moteurs amont (dépendances)** | Aucun (filtre amont — première porte d'entrée) |
| **Moteurs aval (consommateurs)** | Knowledge Engine (reçoit les connaissances qualifiées), Learning Engine (reçoit les signaux de réévaluation) |
| **Apps externes servies** | Aucune directement (les apps consomment les sorties validées en aval) |
| **Tables/Nodes spécifiques** | Neo4j : nœuds `EvidenceEvaluation` (liés aux `KnowledgeObject`) ; PostgreSQL : table `evidence_audit` (journal des décisions de qualification) |
| **Volume estimé** | ~100 000 évaluations de sources (une par connaissance candidate), croissance continue avec l'Encyclopédie |

### 4.2 — Knowledge Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Stocke, versionne et requête le Knowledge Graph. Centralise toutes les connaissances qualifiées et expose les API de requête aux autres moteurs. Cœur du système. |
| **Consomme (types KnowledgeObject)** | Les 6 types : `concept`, `relation`, `regle`, `seuil`, `modele`, `classification` (il les stocke tous) |
| **Consomme (domaines S-6)** | Tous les 10 domaines (stockage universel) |
| **Consomme (datasets)** | Aucun dataset brut — il reçoit les connaissances déjà qualifiées par l'Evidence Engine. Référence les datasets comme sources (SourceReference) |
| **Consomme (entités externes)** | `Essence`, `Station`, `Sol`, `Climat`, `Habitat`, `Publication` (toutes les entités externes du graphe, livrable 304) |
| **Produit** | Réponses aux `KnowledgeQuery` (Correlation, Reasoning), `KnowledgeUpdate` (intégration des mises à jour Learning), index de recherche plein texte |
| **Requêtes typiques** | 1. « Toutes les relations `est_adapte_a` liées à `Quercus petraea` » 2. « Tous les `seuil` de RUM pour le hêtre, version courante » 3. « Toutes les `regle` applicables au domaine pédologie avec evidence_level >= C » |
| **Moteurs amont (dépendances)** | Evidence Engine (les connaissances entrent qualifiées) |
| **Moteurs aval (consommateurs)** | Correlation Engine, Reasoning Engine, tous les moteurs domaine (cache/ontologie), Learning Engine (mises à jour) |
| **Apps externes servies** | GeoSylva (recherche connaissances), QGISIA (requêtes graphe), indirectement toutes via l'API |
| **Tables/Nodes spécifiques** | Neo4j : tous les nœuds `KnowledgeObject` + entités externes + arêtes typées (livrable 304) ; PostgreSQL : tables `ko_concept`, `ko_relation`, `ko_regle`, `ko_seuil`, `ko_modele`, `ko_classification`, `ko_version_history` |
| **Volume estimé** | ~1 000 000 KnowledgeObject à terme (ambition Encyclopédie, GSIE-DIR-0008), ~5 000 000 arêtes |

### 4.3 — GIS Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Gère les données géospatiales : parcelles, relief, occupation du sol, imagerie satellite. Fournit le contexte spatial à tous les autres moteurs. |
| **Consomme (types KnowledgeObject)** | `concept` (notions spatiales), `classification` (nomenclatures d'occupation du sol), `modele` (modèles de traitement spatial) |
| **Consomme (domaines S-6)** | Écologie forestière et stationnelle, biodiversité et conservation |
| **Consomme (datasets)** | DS-001 (BD Forêt v2), DS-002 (LiDAR HD), DS-004 (BD Ortho), DS-013 (SoilGrids — couche spatiale), DS-018 (Sentinel-2), DS-019 (Sentinel-1), DS-020 (Landsat 8/9), DS-021 (MODIS) |
| **Consomme (entités externes)** | `Station` (localisation), `Habitat` (cartographie) |
| **Produit** | `DomainData` spatial (parcelles, MNT, indices végétation), couches raster/vectorielles, géocodage d'entités |
| **Requêtes typiques** | 1. « Polygone de la parcelle X avec type de peuplement » 2. « MNT et hauteur de canopée sur un rayon de 500 m autour de la station Y » 3. « Indice NDVI moyen sur la parcelle Z pour l'été 2025 » |
| **Moteurs amont (dépendances)** | Knowledge Engine (cache, ontologie spatiale) |
| **Moteurs aval (consommateurs)** | Diagnostic Engine, Simulation Engine, Forest Dynamics Engine, indirectement Correlation (via Knowledge) |
| **Apps externes servies** | GeoSylva (cartes), Ignis (terrain, combustible spatial), Artemis (cartes habitats), QGISIA (couches QGIS) |
| **Tables/Nodes spécifiques** | PostgreSQL/PostGIS : tables `parcelle`, `mnt_raster`, `canopee_raster`, `occupation_sol`, `sentinel_tile` ; Neo4j : `Station` avec géométrie |
| **Volume estimé** | ~10 To de données raster (LiDAR, satellite), ~500 000 polygones forestiers (BD Forêt) |

### 4.4 — Botanical Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Gère la taxonomie, l'autécologie et la botanique des essences forestières et de la flore associée. Référentiel taxonomique de l'Encyclopédie. |
| **Consomme (types KnowledgeObject)** | `classification` (taxonomie), `concept` (notions botaniques), `relation` (autécologie : `est_adapte_a`, `croit_mieux_sur`), `seuil` (exigences stationnelles des essences) |
| **Consomme (domaines S-6)** | Botanique et taxonomie, écologie forestière et stationnelle, biodiversité et conservation |
| **Consomme (datasets)** | DS-014 (GBIF), DS-015 (Tela Botanica), DS-016 (BDNFF), DS-017 (INPN) |
| **Consomme (entités externes)** | `Essence` (toutes les espèces), `Habitat` (syntaxonomie) |
| **Produit** | `DomainData` botanique (fiches autécologiques, aires de répartition, exigences stationnelles), ontologie taxonomique vers Knowledge Engine |
| **Requêtes typiques** | 1. « Autécologie complète de `Quercus petraea` : pH, altitude, RUM, exposition » 2. « Essences adaptées à un sol de pH 5,0 et altitude 600 m » 3. « Aire de répartition de `Fagus sylvatica` selon GBIF » |
| **Moteurs amont (dépendances)** | Knowledge Engine (ontologie taxonomique) |
| **Moteurs aval (consommateurs)** | Diagnostic Engine, Correlation Engine, Simulation Engine, Recommendation Engine (indirectement) |
| **Apps externes servies** | GeoSylva (fiches essences), Artemis (habitats faune liés à la flore), QGISIA (couches taxonomiques) |
| **Tables/Nodes spécifiques** | Neo4j : nœuds `Essence` (taxonomie hiérarchique), arêtes `est_adapte_a` ; PostgreSQL : tables `essence`, `essence_autecologie`, `taxon_classification`, `aire_repartition` |
| **Volume estimé** | ~50 000 taxons (BDNFF), ~200 000 occurrences (GBIF France), ~5 000 fiches autécologiques |

### 4.5 — Pedology Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Gère les données pédologiques : types de sols, horizons, propriétés physico-chimiques, réserve utile en eau. Référentiel sol de l'Encyclopédie. |
| **Consomme (types KnowledgeObject)** | `classification` (RPF, WRB), `concept` (notions pédologiques : RUM, pH, CEC), `seuil` (seuils pédologiques : RUM minimale par essence), `modele` (modèles de dynamique hydrique) |
| **Consomme (domaines S-6)** | Pédologie, écologie forestière et stationnelle |
| **Consomme (datasets)** | DS-005 (ONF RPF), DS-011 (BDAT), DS-012 (RPFR), DS-013 (SoilGrids) |
| **Consomme (entités externes)** | `Sol` (types et profils), `Station` (caractéristiques stationnelles) |
| **Produit** | `DomainData` pédologique (profils, RUM, pH, texture, CEC), classifications RPF/WRB vers Knowledge Engine |
| **Requêtes typiques** | 1. « RUM et pH du sol à la station X selon SoilGrids » 2. « Tous les sols de type Alocrisol avec leurs propriétés » 3. « Seuil de RUM minimale pour le hêtre, version courante » |
| **Moteurs amont (dépendances)** | Knowledge Engine (cache, classifications) |
| **Moteurs aval (consommateurs)** | Diagnostic Engine, Correlation Engine, Recommendation Engine (adéquation essence-sol) |
| **Apps externes servies** | GeoSylva (cartes sols, fiches stationnelles), QGISIA (couches pédologiques) |
| **Tables/Nodes spécifiques** | Neo4j : nœuds `Sol`, arêtes `depend_de` (sol-essence) ; PostgreSQL : tables `sol_type`, `sol_profil`, `sol_horizon`, `sol_propriete`, `station_sol` |
| **Volume estimé** | ~2 000 types de sols référencés (RPF/WRB), ~100 000 analyses de terre (BDAT), ~1 To raster (SoilGrids) |

### 4.6 — Climate Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Gère les données climatiques et bioclimatiques : observations historiques, projections régionalisées, déficits hydriques, indices bioclimatiques. |
| **Consomme (types KnowledgeObject)** | `concept` (notions climatiques : déficit hydrique, étage bioclimatique), `seuil` (seuils climatiques : déficit maximal toléré par essence), `modele` (modèles climatiques ARPEGE/AROME, DRIAS) |
| **Consomme (domaines S-6)** | Climatologie et bioclimatologie, écologie forestière et stationnelle |
| **Consomme (datasets)** | DS-007 (Safran), DS-008 (DRIAS), DS-009 (ARPEGE/AROME), DS-010 (Météo-France obs sol), DS-021 (MODIS — végétation globale) |
| **Consomme (entités externes)** | `Climat` (contextes climatiques historiques et projetés), `Station` (localisation climatique) |
| **Produit** | `DomainData` climatique (normales, déficits, projections par scénario SSP), indices bioclimatiques, étages bioclimatiques |
| **Requêtes typiques** | 1. « Déficit hydrique cumulé été 2025 à la station X » 2. « Projection de température moyenne 2050 scénario SSP3-7.0 sur la parcelle Y » 3. « Étage bioclimatique de la station Z selon la classification de Rameau » |
| **Moteurs amont (dépendances)** | Knowledge Engine (cache) |
| **Moteurs aval (consommateurs)** | Diagnostic Engine, Simulation Engine, Forest Dynamics Engine, Correlation Engine |
| **Apps externes servies** | GeoSylva (données climatiques station), Ignis (météo temps réel pour propagation feu), Artemis (météo chasse) |
| **Tables/Nodes spécifiques** | Neo4j : nœuds `Climat` (historique/projection), arêtes `influence` (climat-essence) ; PostgreSQL : tables `climat_normale`, `climat_projection`, `climat_observation`, `bioclimat_indice` |
| **Volume estimé** | ~5 To de données climatiques gridded (Safran, DRIAS), ~10 millions d'observations journalières |

### 4.7 — Correlation Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Détecte les corrélations multiparamètres entre connaissances de domaines différents (ex. lien entre pH, climat et croissance d'une essence). Croise les données domaine. |
| **Consomme (types KnowledgeObject)** | `relation` (relations existantes à croiser), `seuil` (seuils de corrélation), `modele` (modèles statistiques de corrélation), `concept` (notions de corrélation) |
| **Consomme (domaines S-6)** | Tous les 10 domaines (croisement inter-domaines) |
| **Consomme (datasets)** | DS-003 (IFN placettes — calibration corrélations), DS-006 (INRAE SOERE F-ORE-T), DS-010 (Météo-France obs sol), DS-011 (BDAT), DS-014 (GBIF), DS-017 (INPN) |
| **Consomme (entités externes)** | `Essence`, `Sol`, `Climat`, `Station`, `Habitat` (croise toutes les entités) |
| **Produit** | `CorrelationSet` (ensemble de corrélations détectées avec force et confiance), `CorrelationFeedback` vers Learning Engine |
| **Requêtes typiques** | 1. « Corrélations entre déficit hydrique et déclin du hêtre sur les 10 dernières années » 2. « Croisement pH sol + altitude + croissance chêne sessile » 3. « Corrélations émergentes non expliquées par les règles existantes » |
| **Moteurs amont (dépendances)** | Knowledge Engine + tous les moteurs domaine (GIS, Botanical, Pedology, Climate, Forest Dynamics) |
| **Moteurs aval (consommateurs)** | Reasoning Engine, Learning Engine |
| **Apps externes servies** | QGISIA (analyses IA, détection de patterns) |
| **Tables/Nodes spécifiques** | Neo4j : nœuds `Correlation` (liés aux `KnowledgeObject` sources) ; PostgreSQL : tables `correlation_set`, `correlation_parametre`, `correlation_statistique` |
| **Volume estimé** | ~100 000 corrélations détectées, ~10 millions de paires testées (croisements inter-domaines) |

### 4.8 — Reasoning Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Applique les règles d'inférence et produit des conclusions raisonnées à partir des connaissances et des corrélations. Moteur d'inférence du système. |
| **Consomme (types KnowledgeObject)** | `regle` (règles d'inférence à appliquer), `seuil` (seuils de déclenchement), `relation` (relations de causalité), `concept` (définitions des variables) |
| **Consomme (domaines S-6)** | Tous les 10 domaines (les règles couvrent tous les domaines) |
| **Consomme (datasets)** | Aucun dataset brut — travaille sur les connaissances et corrélations (indirectement issues des datasets) |
| **Consomme (entités externes)** | `Essence`, `Sol`, `Climat`, `Station` (variables des règles) |
| **Produit** | `ReasoningOutput` (conclusions raisonnées + règles appliquées + chaîne d'inférence), requêtes `KnowledgeQuery` vers Knowledge Engine |
| **Requêtes typiques** | 1. « Appliquer toutes les règles d'adaptation d'essence au contexte station X (pH 5,0, altitude 600 m, déficit 80 mm) » 2. « Quelles conclusions pour le diagnostic sanitaire de la parcelle Y ? » 3. « Chaîne d'inférence complète pour la conclusion "hêtre non adapté" » |
| **Moteurs amont (dépendances)** | Knowledge Engine, Correlation Engine |
| **Moteurs aval (consommateurs)** | Diagnostic Engine |
| **Apps externes servies** | Aucune directement (les conclusions alimentent le Diagnostic Engine) |
| **Tables/Nodes spécifiques** | Neo4j : nœuds `ReasoningTrace` (chaînes d'inférence) ; PostgreSQL : tables `reasoning_session`, `reasoning_rule_applied`, `reasoning_conclusion` |
| **Volume estimé** | ~50 000 règles d'inférence, ~1 million de conclusions par cycle de diagnostic |

### 4.9 — Diagnostic Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Évalue l'état actuel d'un peuplement ou station et identifie les risques (sanitaires, climatiques, sylvicoles). Synthétise les conclusions en un diagnostic exploitable. |
| **Consomme (types KnowledgeObject)** | `regle` (règles de diagnostic), `seuil` (seuils d'alerte : déficit critique, RUM minimale), `modele` (modèles d'évaluation de risque), `classification` (typologies de risque) |
| **Consomme (domaines S-6)** | Écologie forestière et stationnelle, pathologie forestière, entomologie forestière, dendrométrie et croissance, dynamique des peuplements |
| **Consomme (datasets)** | DS-001 (BD Forêt), DS-004 (BD Ortho — état visuel), DS-005 (RPF), DS-011 (BDAT), DS-017 (INPN — biodiversité), DS-018 (Sentinel-2 — indices de stress) |
| **Consomme (entités externes)** | `Essence`, `Sol`, `Climat`, `Station`, `Habitat` |
| **Produit** | `DiagnosticReport` (état diagnostiqué + problèmes identifiés + gravité + confiance), `SystemState` (état courant pour Simulation) |
| **Requêtes typiques** | 1. « Diagnostic sanitaire de la parcelle X : stress hydrique, maladies, ravageurs » 2. « Risque de dépérissement du chêne sur la station Y selon climat 2025 » 3. « État de régénération naturelle de la parcelle Z » |
| **Moteurs amont (dépendances)** | Reasoning Engine + moteurs domaine (GIS, Climate, Pedology, Botanical, Forest Dynamics) |
| **Moteurs aval (consommateurs)** | Recommendation Engine, Simulation Engine |
| **Apps externes servies** | GeoSylva (diagnostic affiché au forestier), Ignis (diagnostic combustible/risque incendie) |
| **Tables/Nodes spécifiques** | Neo4j : nœuds `Diagnostic` (liés aux parcelles) ; PostgreSQL : tables `diagnostic_report`, `diagnostic_probleme`, `diagnostic_risque`, `system_state` |
| **Volume estimé** | ~10 000 diagnostics par an (un par parcelle active), ~50 paramètres par diagnostic |

### 4.10 — Forest Dynamics Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Modélise la croissance, la dynamique et l'évolution des peuplements dans le temps. Calibre les modèles de croissance sur les données dendrométriques. |
| **Consomme (types KnowledgeObject)** | `modele` (modèles de croissance : ONF-FFN, CAPSIS), `seuil` (seuils de croissance, densité), `relation` (relations croissance-facteurs), `regle` (règles de dynamique) |
| **Consomme (domaines S-6)** | Dendrométrie et croissance, dynamique des peuplements, sylviculture et gestion |
| **Consomme (datasets)** | DS-001 (BD Forêt), DS-002 (LiDAR HD — biomasse), DS-003 (IFN placettes — calibration), DS-006 (INRAE SOERE F-ORE-T), DS-018 (Sentinel-2), DS-019 (Sentinel-1), DS-020 (Landsat), DS-021 (MODIS) |
| **Consomme (entités externes)** | `Essence`, `Station`, `Climat` (facteurs de croissance) |
| **Produit** | `DomainData` dynamique (projections de croissance, accroissements, biomasse, volume sur pied), `SystemState` dynamique pour Simulation |
| **Requêtes typiques** | 1. « Projection de croissance du douglas sur la parcelle X à 10 ans selon le modèle ONF-FFN » 2. « Accroissement moyen annuel de la parcelle Y par essence » 3. « Biomasse sur pied estimée par LiDAR sur la parcelle Z » |
| **Moteurs amont (dépendances)** | Knowledge Engine, Correlation Engine |
| **Moteurs aval (consommateurs)** | Diagnostic Engine, Simulation Engine |
| **Apps externes servies** | GeoSylva (projections croissance), Ignis (biomasse = combustible) |
| **Tables/Nodes spécifiques** | Neo4j : nœuds `Peuplement`, `Arbre` ; PostgreSQL : tables `peuplement`, `arbre`, `croissance_projection`, `biomasse_estimation`, `modele_calibration` |
| **Volume estimé** | ~100 000 peuplements suivis, ~10 millions d'arbres (IFN + LiDAR), ~50 modèles de croissance calibrés |

### 4.11 — Simulation Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Projette des scénarios long terme (croissance, climat, intervention sylvicole, incendie) et compare des alternatives. Moteur de projection du système. |
| **Consomme (types KnowledgeObject)** | `modele` (modèles de simulation : croissance, propagation feu), `regle` (règles de scénario), `seuil` (seuils de bascule), `concept` (notions de scénario) |
| **Consomme (domaines S-6)** | Dynamique des peuplements, climatologie et bioclimatologie, sylviculture et gestion, écologie forestière et stationnelle |
| **Consomme (datasets)** | DS-002 (LiDAR HD), DS-007 (Safran), DS-008 (DRIAS — projections climatiques), DS-009 (ARPEGE/AROME), DS-022 (Prométhée — incendie), DS-023 (EFFIS), DS-024 (MODIS/FIRMS) |
| **Consomme (entités externes)** | `Essence`, `Sol`, `Climat`, `Station` (conditions initiales et aux limites) |
| **Produit** | `SimulationResult` (projections temporelles + confiance + sources), `ScenarioComparison` (comparatif de scénarios), `SimulationGap` vers Learning |
| **Requêtes typiques** | 1. « Simulation de la parcelle X sur 50 ans avec scénario SSP3-7.0 et intervention d'éclaircie à 15 ans » 2. « Propagation d'un incendie sur la zone Y avec vent 30 km/h et humidité 20 % » 3. « Comparaison de 3 scénarios sylvicoles pour la parcelle Z » |
| **Moteurs amont (dépendances)** | Forest Dynamics Engine, Climate Engine |
| **Moteurs aval (consommateurs)** | Recommendation Engine, Validation Engine, Learning Engine |
| **Apps externes servies** | GeoSylva (simulations sylvicoles), Ignis (simulation propagation feu, jumeau UE 5.8) |
| **Tables/Nodes spécifiques** | Neo4j : nœuds `Scenario`, `SimulationRun` ; PostgreSQL : tables `simulation_scenario`, `simulation_run`, `simulation_result`, `scenario_comparison` |
| **Volume estimé** | ~1 000 scénarios par an, ~100 000 pas de temps par simulation, ~50 Go de résultats par scénario long |

### 4.12 — Recommendation Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Produit des recommandations sylvicoles contournables à partir du diagnostic et des simulations. Propose des itinéraires et alternatives. |
| **Consomme (types KnowledgeObject)** | `regle` (règles de recommandation sylvicole), `modele` (modèles d'itinéraire), `seuil` (seuils d'intervention : densité, diamètre), `concept` (notions sylvicoles) |
| **Consomme (domaines S-6)** | Sylviculture et gestion, écologie forestière et stationnelle, dynamique des peuplements, biodiversité et conservation |
| **Consomme (datasets)** | Aucun dataset brut — travaille sur les sorties Diagnostic et Simulation (indirectement issues des datasets) |
| **Consomme (entités externes)** | `Essence` (essences à recommander), `Station` (contexte de la recommandation), `Sol`, `Climat` |
| **Produit** | `RecommendationSet` (recommandations contournables + alternatives + justification), `InterventionSpec` (actions à simuler) vers Simulation |
| **Requêtes typiques** | 1. « Recommandations sylvicoles pour la parcelle X compte tenu du diagnostic et du scénario climatique 2050 » 2. « Alternatives à l'enrésinement de la parcelle Y » 3. « Itinéraire sylvicole optimal pour la régénération de la parcelle Z » |
| **Moteurs amont (dépendances)** | Diagnostic Engine, Simulation Engine |
| **Moteurs aval (consommateurs)** | Validation Engine, Simulation Engine (retour d'InterventionSpec) |
| **Apps externes servies** | GeoSylva (recommandations affichées au forestier — produit principal de l'app) |
| **Tables/Nodes spécifiques** | Neo4j : nœuds `Recommendation` (liés aux diagnostics) ; PostgreSQL : tables `recommendation_set`, `recommendation_item`, `intervention_spec`, `recommendation_alternative` |
| **Volume estimé** | ~10 000 recommandations par an, ~5 alternatives par recommandation |

### 4.13 — Validation Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Contrôle la conformité des recommandations et sorties avec la Constitution GSIE (CON-000 à CON-010), les principes scientifiques (S-1 à S-7) et les contraintes techniques (T-1 à T-8). Garde-fou final. |
| **Consomme (types KnowledgeObject)** | `regle` (règles de conformité constitutionnelle), `classification` (typologies de conformité), `concept` (principes constitutionnels) |
| **Consomme (domaines S-6)** | Tous les 10 domaines (la conformité s'applique transversalement) |
| **Consomme (datasets)** | Aucun dataset brut — valide les sorties des moteurs amont |
| **Consomme (entités externes)** | Aucune directement (valide des productions, pas des entités) |
| **Produit** | `ValidatedOutput` (recommandations validées + sources + niveau de confiance), `ValidationGap` vers Learning Engine (écarts détectés) |
| **Requêtes typiques** | 1. « La recommandation X est-elle conforme à CON-001 (le forestier décideur) ? » 2. « Toutes les sources de la recommandation Y sont-elles traçables (CON-005) ? » 3. « Le niveau de preuve de chaque élément de la recommandation Z est-il affiché (S-2) ? » |
| **Moteurs amont (dépendances)** | Recommendation Engine, Diagnostic Engine |
| **Moteurs aval (consommateurs)** | Utilisateur final (via apps externes), Learning Engine (écarts) |
| **Apps externes servies** | GeoSylva (sorties validées affichées), Ignis (validations des simulations incendie), Artemis, QGISIA, Hydro, Flora (toutes les apps consomment les sorties validées) |
| **Tables/Nodes spécifiques** | Neo4j : nœuds `ValidationResult` (liés aux recommandations) ; PostgreSQL : tables `validation_result`, `validation_check`, `validation_gap`, `conformite_constitution` |
| **Volume estimé** | ~10 000 validations par an (une par recommandation), ~20 contrôles par validation |

### 4.14 — Learning Engine

| Aspect | Détail |
|---|---|
| **Rôle** | Détecte les signaux de réévaluation (connaissances dont le niveau de preuve évolue), les patterns émergents et les écarts entre prédictions et réalité. Moteur transverse d'amélioration continue. |
| **Consomme (types KnowledgeObject)** | Tous les 6 types (analyse les évolutions de toutes les connaissances), `relation` (patterns émergents), `modele` (modèles à recalibrer) |
| **Consomme (domaines S-6)** | Tous les 10 domaines (apprentissage transverse) |
| **Consomme (datasets)** | DS-003 (IFN placettes — écarts prédiction/réalité), DS-006 (INRAE SOERE F-ORE-T), DS-018 (Sentinel-2 — détection changements), DS-024 (MODIS/FIRMS — validation incendie) |
| **Consomme (entités externes)** | `Essence`, `Sol`, `Climat`, `Station` (pour recalibration des modèles) |
| **Produit** | `ReassessmentRequest` vers Evidence Engine (réévaluation de niveau de preuve), `KnowledgeUpdate` vers Knowledge Engine (ajustements), `CorrelationFeedback` (corrélations à valider) |
| **Requêtes typiques** | 1. « Quelles connaissances de niveau C pourraient être promues en B suite aux nouvelles observations ? » 2. « Écarts entre projections Forest Dynamics 2020 et croissance réelle observée 2025 » 3. « Patterns émergents de dépérissement non expliqués par les règles actuelles » |
| **Moteurs amont (dépendances)** | Tous les moteurs (transverse — reçoit les écarts et signaux de tous les moteurs) |
| **Moteurs aval (consommateurs)** | Evidence Engine (réévaluations), Knowledge Engine (mises à jour) |
| **Apps externes servies** | Aucune directement (alimente la boucle d'amélioration en amont des apps) |
| **Tables/Nodes spécifiques** | Neo4j : nœuds `LearningSignal`, `Pattern` ; PostgreSQL : tables `learning_signal`, `pattern_emergent`, `model_gap`, `reassessment_request` |
| **Volume estimé** | ~50 000 signaux par an, ~1 000 patterns émergents détectés, ~5 000 recalibrations de modèles |

---

## 5. Liens vers les apps externes

Les six applications externes de l'écosystème Quintessences
consomment les sorties des moteurs GSIE via l'API GSIE (livrable 207).
Aucune app n'accède directement au Knowledge Graph : toutes passent
par les contrats d'interface validés (livrable 206).

### 5.1 GeoSylva (forêt)

GeoSylva est l'application forestière principale et le client
historique de GSIE. Elle couvre toute la chaîne d'intelligence :
diagnostic, recommandations, simulations, cartographie.

| Aspect | Détail |
|---|---|
| **Moteurs consommés** | Tous les 14 moteurs (application principale — chaîne complète Evidence → Validation) |
| **Données affichées** | Diagnostic de peuplement, recommandations sylvicoles contournables, simulations long terme, carte interactive (GIS), fiches essences, données pédologiques et climatiques stationnelles |
| **Flux** | GSIE API → GeoSylva frontend (mobile + web) |
| **Socle spécifique** | Essences (autécologie, aires), stations (caractéristiques stationnelles), sylviculture (itinéraires, densités, rotations), diagnostics, recommandations |
| **Contrats consommés** | `ValidatedOutput` (206), `DiagnosticReport` (206), `RecommendationSet` (206), `SimulationResult` (206), `DomainData` GIS/Botanical/Pedology/Climate (206) |
| **Fréquence d'accès** | Temps réel pour la consultation, asynchrone pour les diagnostics et simulations longs |

### 5.2 Ignis (incendie)

Ignis est l'application de surveillance et d'analyse incendie,
dotée d'un jumeau numérique 3D sous Unreal Engine 5.8. Elle
consomme les moteurs spatiaux, climatiques et de simulation pour
modéliser la propagation du feu.

| Aspect | Détail |
|---|---|
| **Moteurs consommés** | GIS Engine, Climate Engine, Simulation Engine, Knowledge Engine, Reasoning Engine, Forest Dynamics Engine (biomasse = combustible), Diagnostic Engine (risque combustible) |
| **Données affichées** | Propagation du feu (simulation), météo temps réel, terrain (MNT, pente, exposition), combustibles (biomasse, humidité), jumeau 3D UE 5.8 |
| **Flux** | GSIE API → Ignis GCS (ground control station) + Unreal Engine 5.8 (rendu 3D temps réel) |
| **Socle spécifique** | Comportement du feu (modèles FARSITE, Prométhée), combustibles (classification, charge, humidité), météo temps réel (AROME), terrain (LiDAR, pente), historique incendies (Prométhée, EFFIS, FIRMS) |
| **Contrats consommés** | `SimulationResult` (propagation), `DomainData` GIS/Climate, `DiagnosticReport` (risque combustible), `SystemState` (état initial) |
| **Fréquence d'accès** | Temps réel pendant la surveillance active (flux synchrone autorisé, livrable 206 §4) ; asynchrone pour les analyses post-incendie |
| **Datasets spécifiques** | DS-002 (LiDAR — combustible spatial), DS-009 (AROME — météo temps réel), DS-022 (Prométhée), DS-023 (EFFIS), DS-024 (MODIS/FIRMS — détection active) |

### 5.3 Artemis (faune)

Artemis est l'application de suivi de la faune. Elle consomme les moteurs
spatiaux et botaniques pour cartographier les habitats faune et
fournir le contexte météo aux utilisateurs.

| Aspect | Détail |
|---|---|
| **Moteurs consommés** | GIS Engine, Botanical Engine, Knowledge Engine, Climate Engine |
| **Données affichées** | Habitats faune (liés à la flore et aux habitats écologiques), cartes interactives, météo de terrain, observations naturalistes (INPN) |
| **Flux** | GSIE API → Artemis frontend (mobile) |
| **Socle spécifique** | Habitats faune (corrélation flore-faune via INPN), biodiversité, données spatiales (parcelles, relief), météo locale |
| **Contrats consommés** | `DomainData` GIS/Botanical/Climate, `KnowledgeQuery` (recherche habitats) |
| **Fréquence d'accès** | Temps réel pour la consultation terrain (mobile), asynchrone pour les analyses d'habitat |
| **Datasets spécifiques** | DS-014 (GBIF — occurrences), DS-017 (INPN — patrimoine naturel), DS-007 (Safran — météo), DS-001 (BD Forêt — cartes) |

### 5.4 QGISIA (QGIS + IA)

QGISIA est un plugin QGIS augmenté par IA. Il consomme les moteurs
spatiaux et de corrélation pour proposer des analyses intelligentes
directement dans QGIS.

| Aspect | Détail |
|---|---|
| **Moteurs consommés** | GIS Engine, Knowledge Engine, Correlation Engine, Reasoning Engine (analyses IA) |
| **Données affichées** | Couches QGIS (raster, vectoriel), analyses IA (corrélations détectées, patterns), requêtes au graphe de connaissances |
| **Flux** | GSIE API → plugin QGIS (Python) |
| **Socle spécifique** | Données spatiales (toutes couches GIS), analyses de corrélation (détection de patterns inter-domaines), requêtes Knowledge Graph |
| **Contrats consommés** | `DomainData` GIS, `KnowledgeQuery` (requêtes graphe), `CorrelationSet` (patterns détectés) |
| **Fréquence d'accès** | À la demande (l'utilisateur déclenche les analyses depuis QGIS) |
| **Datasets spécifiques** | DS-001 (BD Forêt), DS-002 (LiDAR), DS-018/019/020 (Sentinel/Landsat), DS-013 (SoilGrids) |

### 5.5 Hydro (eau)

Hydro est l'application de gestion et de visualisation de l'eau. Elle
consomme les moteurs spatiaux, climatiques, de connaissances et de
corrélation pour cartographier le réseau hydrographique et analyser
les régimes hydriques.

| Aspect | Détail |
|---|---|
| **Moteurs consommés** | GIS Engine, Climate Engine, Knowledge Engine, Correlation Engine |
| **Données affichées** | Réseau hydrographique, zones humides, régimes hydriques |
| **Flux** | GSIE API → Hydro frontend |
| **Socle spécifique** | BD Carthage (IGN), BD TOPAGE, Sandre |
| **Contrats consommés** | `DomainData` GIS/Climate, `KnowledgeQuery` (requêtes hydriques), `CorrelationSet` (corrélations hydro-climatiques) |
| **Fréquence d'accès** | Temps réel pour la consultation, asynchrone pour les analyses de régime hydrique |

### 5.6 Flora (végétation)

Flora est l'application de cartographie et d'analyse de la végétation.
Elle consomme les moteurs botaniques, de connaissances, spatiaux et
climatiques pour fournir des données floristiques, taxonomiques et
phénologiques.

| Aspect | Détail |
|---|---|
| **Moteurs consommés** | Botanical Engine, Knowledge Engine, GIS Engine, Climate Engine |
| **Données affichées** | Flore, taxonomie, cartographie végétale, phénologie |
| **Flux** | GSIE API → Flora frontend |
| **Socle spécifique** | GBIF, Tela Botanica, BDNFF, INPN |
| **Contrats consommés** | `DomainData` Botanical/GIS/Climate, `KnowledgeQuery` (requêtes taxonomiques) |
| **Fréquence d'accès** | Temps réel pour la consultation terrain, asynchrone pour les analyses phénologiques |

---

## 6. Matrice moteur × app

Lecture : la ligne est un moteur, la colonne est une application. Une
case cochée signifie que l'application consomme les sorties du
moteur (directement ou via les sorties validées).

| Moteur \ App | GeoSylva | Ignis | Artemis | QGISIA | Hydro | Flora |
|---|---|---|---|---|---|---|
| **Evidence Engine** | Oui (indirect) | Oui (indirect) | Oui (indirect) | Oui (indirect) | Oui (indirect) | Oui (indirect) |
| **Knowledge Engine** | Oui | Oui | Oui | Oui | Oui | Oui |
| **GIS Engine** | Oui | Oui | Oui | Oui | Oui | Oui |
| **Botanical Engine** | Oui | Non | Oui | Non | Non | Oui |
| **Pedology Engine** | Oui | Non | Non | Oui | Non | Non |
| **Climate Engine** | Oui | Oui | Oui | Non | Oui | Oui |
| **Correlation Engine** | Oui (indirect) | Non | Non | Oui | Oui | Non |
| **Reasoning Engine** | Oui (indirect) | Oui (indirect) | Non | Oui (indirect) | Non | Non |
| **Diagnostic Engine** | Oui | Oui | Non | Non | Non | Non |
| **Forest Dynamics Engine** | Oui | Oui (combustible) | Non | Non | Non | Non |
| **Simulation Engine** | Oui | Oui | Non | Non | Non | Non |
| **Recommendation Engine** | Oui | Non | Non | Non | Non | Non |
| **Validation Engine** | Oui | Oui | Oui | Oui | Oui | Oui |
| **Learning Engine** | Non (transverse) | Non (transverse) | Non (transverse) | Non (transverse) | Non (transverse) | Non (transverse) |

Légende :
- **Oui** = l'app consomme directement les sorties du moteur.
- **Oui (indirect)** = l'app consomme les sorties via un moteur aval
  (ex. GeoSylva consomme les conclusions de Reasoning via le
  Diagnostic Engine).
- **Non** = l'app ne consomme pas ce moteur.

> GeoSylva consomme la chaîne complète car c'est l'application
> forestière principale. Ignis se concentre sur les moteurs
> spatiaux, climatiques et de simulation. Artemis exploite les
> moteurs spatiaux et botaniques pour les habitats faune. QGISIA
> exploite les moteurs spatiaux et de corrélation pour les analyses
> IA. Hydro exploite les moteurs spatiaux, climatiques et de
> corrélation pour le réseau hydrographique et les régimes hydriques.
> Flora exploite les moteurs botaniques, spatiaux et climatiques pour
> la cartographie végétale et la phénologie. Le Learning Engine est
> transverse et n'est pas consommé directement par les apps : il
> alimente la boucle d'amélioration en amont.

---

## 7. Contrats d'interface (référence livrable 206)

Cette section rappelle les messages clés échangés entre
l'Encyclopédie, les moteurs et les applications externes. Les
schémas formels complets sont définis au livrable 206 (contrats
d'interface) et au livrable 203 (protocole de communication).

### 7.1 Flux Encyclopédie → moteurs

| Message | Émetteur | Destinataire | Description |
|---|---|---|---|
| `KnowledgeQuery` | Tout moteur | Knowledge Engine | Requête de connaissances au graphe (filtres par type, domaine, evidence_level, version) |
| `QualifiedKnowledge` | Evidence Engine | Knowledge Engine | Connaissance candidate qualifiée (niveau de preuve + source + version) prête à intégrer |
| `DomainData` | Moteurs domaine | Diagnostic / Simulation | Données spatiales, climatiques, pédologiques, botaniques, dynamiques |

### 7.2 Flux moteurs → moteurs

| Message | Émetteur | Destinataire | Description |
|---|---|---|---|
| `CorrelationSet` | Correlation Engine | Reasoning Engine | Ensemble de corrélations multiparamètres détectées |
| `ReasoningOutput` | Reasoning Engine | Diagnostic Engine | Conclusions raisonnées + règles appliquées + chaîne d'inférence |
| `DiagnosticReport` | Diagnostic Engine | Recommendation Engine | État diagnostiqué + problèmes identifiés + gravité |
| `SystemState` | Diagnostic Engine | Simulation Engine | État courant du système pour initialiser une simulation |
| `SimulationResult` | Simulation Engine | Recommendation / Validation | Projections temporelles + confiance + sources |
| `RecommendationSet` | Recommendation Engine | Validation Engine | Recommandations contournables + alternatives |
| `InterventionSpec` | Recommendation Engine | Simulation Engine | Actions sylvicoles à simuler (retour) |

### 7.3 Flux moteurs → apps externes

| Message | Émetteur | Destinataire | Description |
|---|---|---|---|
| `ValidatedOutput` | Validation Engine | GeoSylva, Ignis, Artemis, QGISIA, Hydro, Flora | Sorties validées (recommandations + sources + niveau de confiance) — produit principal exposé aux apps |
| `DomainData` (GIS) | GIS Engine | GeoSylva, Ignis, Artemis, QGISIA, Hydro, Flora | Couches spatiales (parcelles, MNT, imagerie) |
| `DomainData` (Climate) | Climate Engine | GeoSylva, Ignis, Artemis, Hydro, Flora | Données climatiques et bioclimatiques |
| `DomainData` (Botanical) | Botanical Engine | GeoSylva, Artemis, Flora | Données botaniques (taxonomie, autécologie) |
| `SimulationResult` | Simulation Engine | GeoSylva, Ignis | Projections et simulations (sylvicoles et incendie) |
| `DiagnosticReport` | Diagnostic Engine | GeoSylva, Ignis | Diagnostic de peuplement / risque combustible |

### 7.4 Flux transverses (Learning)

| Message | Émetteur | Destinataire | Description |
|---|---|---|---|
| `ReassessmentSignal` | Evidence Engine | Learning Engine | Connaissances dont le niveau de preuve peut évoluer |
| `CorrelationFeedback` | Correlation Engine | Learning Engine | Corrélations à valider/ajuster par apprentissage |
| `ValidationGap` | Validation Engine | Learning Engine | Écarts entre attendu et observé |
| `SimulationGap` | Simulation Engine | Learning Engine | Écarts simulation/réalité pour calibration |
| `ReassessmentRequest` | Learning Engine | Evidence Engine | Demande de réévaluation du niveau de preuve |
| `KnowledgeUpdate` | Learning Engine | Knowledge Engine | Connaissances ajustées par apprentissage |

### 7.5 Principes d'interface (rappel)

1. **Aucun moteur ne connaît les détails internes d'un autre**
   (CON-007). Chaque échange passe par un contrat explicite.
2. **Tous les flux sont tracés** (CON-005). Chaque message porte un
   identifiant de source et un horodatage.
3. **Toutes les sorties sont explicables** (CON-004). Chaque
   recommandation cite les moteurs et sources qui l'ont produite.
4. **Communication asynchrone par défaut**. La chaîne d'intelligence
   peut être synchrone pour les flux temps réel (Ignis).
5. **Offline-first**. Les moteurs communiquent par messages persistés
   (T-2).

---

## 8. Priorité d'alimentation du socle

L'alimentation du socle de chaque moteur est alignée sur l'ordre de
développement du livrable 204. Un moteur n'est alimenté que lorsque
ses dépendances amont produisent leurs socles. Les vagues ci-dessous
définissent l'ordre d'ingestion des datasets et de peuplement du
Knowledge Graph.

### Vague 0 — Fondations (préalables aux moteurs)

| Composant | Socle à préparer |
|---|---|
| Modèle de données (205) | Structure des `KnowledgeObject` et entités externes |
| Protocole (203) | Contrats de messages entre moteurs |
| Stack (202) | PostgreSQL/PostGIS, Neo4j, infrastructure |
| Contrats d'interface (206) | Schémas formels de tous les messages |

### Vague 1 — Evidence + Knowledge (socle fondateur)

| Moteur | Socle à ingérer |
|---|---|
| **Evidence Engine** | Critères d'évaluation des sources (S-1), règles d'assignation des niveaux A-F (livrable 306), classification des sources |
| **Knowledge Engine** | Ontologie forestière (livrable 303), structure du graphe (livrable 304), premières connaissances (livrable 308) |

**Justification :** ces deux moteurs sont la porte d'entrée. Sans
Evidence, aucune donnée n'est qualifiée. Sans Knowledge, aucun
moteur ne peut requêter le graphe. Leur socle doit être peuplé en
premier.

### Vague 2 — Moteurs domaine (données de référence)

| Moteur | Socle à ingérer (datasets prioritaires) |
|---|---|
| **GIS Engine** | DS-001 (BD Forêt), DS-002 (LiDAR HD), DS-004 (BD Ortho), DS-018/019/020 (satellite) |
| **Botanical Engine** | DS-014 (GBIF), DS-015 (Tela Botanica), DS-016 (BDNFF), DS-017 (INPN) |
| **Pedology Engine** | DS-005 (RPF), DS-011 (BDAT), DS-012 (RPFR), DS-013 (SoilGrids) |
| **Climate Engine** | DS-007 (Safran), DS-008 (DRIAS), DS-009 (AROME), DS-010 (obs sol) |

**Justification :** les moteurs domaine sont indépendants entre eux
et peuvent être alimentés en parallèle. Ils doivent précéder
Correlation, qui les croise tous. Chaque moteur domaine ingère ses
datasets de référence et publie ses `DomainData` dans le Knowledge
Graph.

### Vague 3 — Correlation + Reasoning (croisement et inférence)

| Moteur | Socle à ingérer |
|---|---|
| **Correlation Engine** | Toutes les `DomainData` des moteurs domaine (vague 2), DS-003 (IFN), DS-006 (INRAE) pour calibration |
| **Reasoning Engine** | Toutes les `regle` du Knowledge Graph, corrélations de Correlation Engine |

**Justification :** Correlation nécessite que tous les moteurs
domaine produisent des données à croiser. Reasoning dépend de
Correlation. Ces deux moteurs sont séquentiels dans la vague.

### Vague 4 — Diagnostic + Forest Dynamics (synthèse et dynamique)

| Moteur | Socle à ingérer |
|---|---|
| **Diagnostic Engine** | Sorties Reasoning + `DomainData` de tous les moteurs domaine, DS-017 (INPN), DS-018 (Sentinel-2 stress) |
| **Forest Dynamics Engine** | DS-003 (IFN placettes), DS-006 (INRAE), modèles de croissance (ONF-FFN, CAPSIS) |

**Justification :** Diagnostic et Forest Dynamics dépendent tous
deux de la vague 3 mais sont indépendants entre eux — ils peuvent
être alimentés en parallèle. Diagnostic synthétise l'état actuel ;
Forest Dynamics projette l'évolution.

### Vague 5 — Simulation + Recommendation (projection et conseil)

| Moteur | Socle à ingérer |
|---|---|
| **Simulation Engine** | Sorties Forest Dynamics + Climate (projections), DS-008 (DRIAS), DS-022/023/024 (incendie) |
| **Recommendation Engine** | Sorties Diagnostic + Simulation, règles sylvicoles du Knowledge Graph |

**Justification :** Simulation dépend de Forest Dynamics (vague 4)
et Climate (vague 2). Recommendation dépend de Diagnostic (vague 4)
et Simulation (vague 5) — strictement après Simulation.

### Vague 6 — Validation + Learning (garde-fou et amélioration)

| Moteur | Socle à ingérer |
|---|---|
| **Validation Engine** | Règles de conformité constitutionnelle (CON-000 à CON-010, S-1 à S-7, T-1 à T-8), sorties Recommendation |
| **Learning Engine** | Écarts de tous les moteurs (ValidationGap, SimulationGap, CorrelationFeedback), DS-003/006/018/024 pour recalibration |

**Justification :** Validation est le garde-fou final — il valide
les recommandations. Learning est transverse et développé en
dernier : il analyse les écarts de tous les moteurs pour alimenter
la boucle d'amélioration continue.

### Synthèse des vagues

```
Vague 0 : Fondations (modèle, protocole, stack, contrats)
Vague 1 : Evidence + Knowledge          (socle fondateur)
Vague 2 : GIS + Botanical + Pedology + Climate  (données de référence)
Vague 3 : Correlation + Reasoning       (croisement et inférence)
Vague 4 : Diagnostic + Forest Dynamics  (synthèse et dynamique)
Vague 5 : Simulation + Recommendation   (projection et conseil)
Vague 6 : Validation + Learning         (garde-fou et amélioration)
```

---

## 10. Volumétrie globale du socle

Le tableau ci-dessous synthétise l'ordre de grandeur des volumes
manipulés par chaque moteur. Ces estimations sont indicatives et
servent à dimensionner l'infrastructure (PostgreSQL/PostGIS, Neo4j,
stockage raster). Elles seront affinées en Phase 4 lors de
l'implémentation.

| Moteur | Volume consommé | Volume produit | Nature dominante |
|---|---|---|---|
| Evidence Engine | ~100 000 évaluations | ~100 000 qualifications | Métadonnées (léger) |
| Knowledge Engine | ~1 000 000 KO + ~5 000 000 arêtes | Index de recherche | Graphe (modéré) |
| GIS Engine | ~10 To raster + ~500 000 polygones | Couches dérivées | Raster/vectoriel (lourd) |
| Botanical Engine | ~50 000 taxons + ~200 000 occurrences | ~5 000 fiches autécologie | Tabulaire + graphe (modéré) |
| Pedology Engine | ~2 000 types + ~100 000 analyses + ~1 To raster | Profils et classifications | Raster + tabulaire (lourd) |
| Climate Engine | ~5 To gridded + ~10 M observations | Normales et projections | Raster temporel (lourd) |
| Correlation Engine | ~10 M paires testées | ~100 000 corrélations | Calcul (modéré) |
| Reasoning Engine | ~50 000 règles | ~1 M conclusions/cycle | Calcul (léger) |
| Diagnostic Engine | ~10 000 diagnostics/an | ~10 000 rapports | Tabulaire (léger) |
| Forest Dynamics Engine | ~100 000 peuplements + ~10 M arbres | Projections et biomasse | Tabulaire + raster (modéré) |
| Simulation Engine | Conditions aux limites | ~50 Go/scénario long | Calcul + raster (lourd) |
| Recommendation Engine | Sorties Diagnostic + Simulation | ~10 000 recommandations/an | Tabulaire (léger) |
| Validation Engine | Sorties Recommendation | ~10 000 validations/an | Tabulaire (léger) |
| Learning Engine | Écarts de tous les moteurs | ~50 000 signaux/an | Tabulaire + calcul (modéré) |

**Total estimé :** ~20 To de données brutes (essentiellement raster
GIS, Pedology, Climate), ~1 000 000 KnowledgeObject dans le graphe,
~5 000 000 arêtes. Le stockage raster est le point de dimensionnement
critique ; le graphe Neo4j reste d'volume modéré.

> **Note :** ces volumes excluent le code métier (Phase 4) et les
> artefacts de build. Ils ne couvrent que les données du socle.

---

## 11. Références

| Référence | Description |
|---|---|
| `GSIE/ARCHITECTURE/ENGINE_DEVELOPMENT_ORDER.md` (204) | Ordre de développement des 14 moteurs et graphe de dépendances |
| `GSIE/ARCHITECTURE/ENGINE_INTERFACE_CONTRACTS.md` (206) | Contrats d'interface et matrice d'interactions entre moteurs |
| `GSIE/ARCHITECTURE/SCIENTIFIC_DATA_MODEL.md` (205) | Modèle de données scientifique (entités, relations, sources) |
| `GSIE/ARCHITECTURE/ENGINE_COMMUNICATION_PROTOCOL.md` (203) | Protocole de communication entre moteurs |
| `GSIE/ARCHITECTURE/TECHNOLOGY_STACK.md` (202) | Stack technologique (PostgreSQL/PostGIS, Neo4j) |
| `GSIE/KNOWLEDGE/KNOWLEDGE_METHOD.md` (302) | Méthode de gestion des connaissances (KnowledgeObject) |
| `GSIE/KNOWLEDGE/FOREST_ONTOLOGY.md` (303) | Ontologie forestière par domaine S-6 |
| `GSIE/KNOWLEDGE/KNOWLEDGE_GRAPH_SPECIFICATION.md` (304) | Spécification du graphe de connaissances (nœuds, arêtes) |
| `GSIE/DATASETS/DATASET_CATALOG.md` (305) | Catalogue des 24 datasets (DS-001 à DS-024) |
| `01_DIRECTIVES/ACTIVE/GSIE-DIR-0007.md` | Lancement de la Phase 3 — Connaissance |
| `01_DIRECTIVES/ACTIVE/GSIE-DIR-0008.md` | L'Encyclopédie de l'Écosystème (base centrale) |
| `00_CONSTITUTION/SCIENTIFIC_CONSTITUTION.md` | Constitution Scientifique (S-1 à S-7, dont S-6 domaines) |
| `00_CONSTITUTION/TECHNICAL_CONSTITUTION.md` | Constitution Technique (T-1, T-2) |

---

## 12. Historique

| Version | Date | Auteur | Modification |
|---|---|---|---|
| 0.1 | 2026-07-13 | Camille Perraudeau | Création du livrable 310 — socle de données des 14 moteurs et liens vers les apps externes (GeoSylva, Ignis, Artemis, QGISIA) |
| 0.2 | 2026-07-13 | Camille Perraudeau | Restructuration GSIE-DIR-0009 / DEC-000013 — ajout Hydro et Flora (sections 5.5, 5.6), renommage Ignis → Ignis, Artemis → Artemis, matrice moteur × app étendue à 6 apps |

---

*Statut : Review — Livrable 310, Phase 3 Connaissance. Document
d'architecture de données, aucun code métier. L'implémentation des
moteurs est réservée à la Phase 4 (DEC-000004).*

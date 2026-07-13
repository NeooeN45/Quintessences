# ============================================================================
# GSIE ECOSYSTEM ENCYCLOPEDIA DIRECTIVE
# Directive ID : GSIE-DIR-0008
# Version : 1.0
# Statut : ACTIVE
# Priorité : CRITIQUE
# Classification : FONDATION
# Auteur : Camille Perraudeau
# Date : 2026-07-13
# ============================================================================

# Titre : L'Encyclopédie de l'Écosystème — la plus grande base de
# connaissances écologiques du marché

## Résumé exécutif

GSIE ne construit pas un fichier markdown de 25 connaissances. GSIE
construit **l'Encyclopédie de l'Écosystème** : la plus grande base de
données structurée, sourcée et traçable sur tout ce qui touche à
l'écosystème — flore, faune, sols, climat, hydrologie, pathologies,
insectes, champignons, interactions trophiques, dynamiques de
peuplements, modèles de croissance, et au-delà.

Cette encyclopédie est **un produit en soi**, pas un sous-produit des
moteurs. Elle peut alimenter GSIE, GeoSylva, GSIE-Ignis, mais aussi
tout autre acteur (recherche, éducation, gestion, politique
environnementale).

L'échelle visée est **million d'entrées**, pas dizaine.

---

## 1. Vision

### 1.1 L'Encyclopédie comme produit principal

La Constitution dit « la connaissance est le véritable produit »
(CON-003). Cette directive l'opérationnalise : la connaissance n'est
pas un livrable markdown, c'est une **base de données vivante,
structurée, interrogeable et exposée**.

### 1.2 Périmètre

L'Encyclopédie couvre **tout l'écosystème**, pas seulement la forêt :

| Domaine | Exemples de contenu |
|---|---|
| Flore | Toutes les essences forestières + flore sous-étage + flore associée |
| Faune | Vertébrés forestiers, insectes, oiseaux, mammifères, reptiles, amphibiens |
| Sols | Tous les types pédologiques (RPF, WRB), propriétés, horizons, dynamiques |
| Climat | Données climatiques, bioclimatiques, projections, scénarios |
| Hydrologie | Bassins versants, zones humides, régimes hydriques |
| Pathologies | Toutes les maladies forestières (champignons, bactéries, virus) |
| Entomologie | Tous les insectes forestiers (ravageurs, auxiliaires, décomposeurs) |
| Mycologie | Champignons symbiotiques, pathogènes, saprophytes |
| Interactions | Relations trophiques, symbioses, compétitions, parasitismes |
| Dynamiques | Successions, cycles, perturbations, régénération |
| Sylviculture | Itinéraires, densités, rotations, modèles de croissance |
| Biodiversité | Indicateurs, habitats, corridors, connectivité |
| Géographie | Répartitions, aires, altitudes, expositions |
| Incendie | Comportement du feu, combustibles, météo, propagation (GSIE-Ignis) |

### 1.3 Ambition de marché

L'Encyclopédie vise à être **la référence la plus complète du marché**
sur l'écosystème, devant :

- les bases existantes (GBIF, INPN, Tela Botanica) qui sont
  taxonomiques mais pas écologiques ;
- les référentiels institutionnels (IGN, INRAE, ONF) qui sont sectoriels
  mais pas interconnectés ;
- les encyclopédies grand public (Wikipédia) qui ne sont pas
  structurées ni sourcées scientifiquement.

**Le positionnement unique de GSIE** : la seule base qui combine
taxonomie + autécologie + pédologie + climat + interactions + modèles +
sylviculture, le tout sourcé, versionné et interrogeable.

---

## 2. Architecture technique cible

### 2.1 Base de données graphe

L'Encyclopédie est implémentée comme un **graphe de connaissances**
(respectant le livrable 304) :

- **Technologie recommandée** : Neo4j (graphe natif, Cypher, scalable,
  écosystème mature) ou alternative équivalente à évaluer en Phase 4.
- **Stockage** : nœuds (connaissances, entités) + arêtes (relations
  versionnées).
- **Requêtes** : Cypher ou GraphQL sur le graphe.
- **Scalabilité** : capacité visée de 10 millions de nœuds minimum.

### 2.2 Identifiants uniques stables

Chaque entrée de l'Encyclopédie possède un **identifiant unique,
stable et citable** (S-7, CON-010) :

| Type d'entité | Format d'identifiant | Exemple |
|---|---|---|
| Connaissance (KnowledgeObject) | `GSIE-K-XXXXXXXXXX` | `GSIE-K-0000000001` |
| Essence / taxon | `GSIE-TAX-XXXXXXXX` | `GSIE-TAX-00000001` |
| Type de sol | `GSIE-PED-XXXX` | `GSIE-PED-0001` |
| Habitat | `GSIE-HAB-XXXX` | `GSIE-HAB-0001` |
| Pathologie | `GSIE-PATH-XXXX` | `GSIE-PATH-0001` |
| Insecte | `GSIE-ENT-XXXX` | `GSIE-ENT-0001` |
| Modèle | `GSIE-MOD-XXXX` | `GSIE-MOD-0001` |
| Source | `GSIE-SRC-XXXXXX` | `GSIE-SRC-000001` |
| Dataset | `GSIE-DS-XXX` | `GSIE-DS-001` |

**Règles** :
- L'identifiant est **attribué à la création** et **jamais réutilisé**
  (même si l'entrée est archivée).
- L'identifiant est **citable** dans toute publication, recommandation
  ou interface.
- L'identifiant est **résolvable** : `gsie://K-0000000001` renvoie la
  connaissance complète.

### 2.3 Triple store sémantique (couche optionnelle)

Au-dessus du graphe, une couche sémantique (RDF/OWL) permet :
- l'interrogation SPARQL ;
- l'alignement avec des ontologies externes (GBIF, ENVO, AGROVOC) ;
- la publication en Linked Open Data.

### 2.4 API et exposition

L'Encyclopédie est exposée via :
- **API REST/GraphQL** : interrogation programmatique par les moteurs
  et les applications clientes.
- **Interface web** : consultation humaine, recherche, navigation
  graphique.
- **Export** : JSON, RDF, CSV pour intégration externe.
- **API publique** : accès en lecture pour la communauté scientifique
  et éducative (avec licence à définir en `19_LEGAL/`).

---

## 3. Collecte massive de données

### 3.1 Stratégie d'ingestion

L'Encyclopédie se construit par **ingestion automatisée à grande
échelle** des sources identifiées (livrable 307) et au-delà :

| Source | Volume estimé | Méthode d'ingestion |
|---|---|---|
| GBIF | ~100 000 occurrences taxonomiques | API REST + dump |
| Tela Botanica / BDNFF | ~10 000 taxons floraux | API eFlore |
| INPN (MNHN) | ~50 000 espèces | API + dumps |
| IGN BD Forêt v2 | ~10 000 entités forestières | Shapefile + API |
| IGN LiDAR HD | Millions de points | Pipeline cloud |
| Météo-France Safran | Grille quotidienne 8 km | Accord + API |
| DRIAS | Projections grille 8 km | Accord + API |
| RPF INRAE | ~50 types de sols | Manuel + OCR |
| ONF guides sylvicoles | ~100 guides | OCR + NLP |
| Publications peer-reviewed | Milliers d'articles | Web scraping + DOI |
| Copernicus Sentinel-2 | Imagerie 10 m | API Sentinel Hub |
| Prométhée (incendies) | ~10 000 événements | Accord + API |
| SoilGrids (ISRIC) | Grille 250 m mondial | API + dump |
| EPPO (pathologies) | ~1 000 pathogènes | API |
| ICP Forests | ~4 000 placettes | Accord + API |

**Total estimé** : plusieurs millions d'entrées après ingestion complète.

### 3.2 Classificateurs automatisés

Pour ingérer à cette échelle, des **classificateurs** sont nécessaires :

| Classificateur | Rôle | Technologie cible |
|---|---|---|
| Classificateur de source | Catégorise la source (S-1) | Règles + NLP |
| Classificateur de preuve | Assigne le niveau A-F (S-2) | Règles + Evidence Engine |
| Classificateur de domaine | Assigne le domaine S-6 | NLP + ontologie (livrable 303) |
| Classificateur de type | Assigne le type KnowledgeObject | NLP + ontologie |
| Extracteur d'entités | Extrait essences, sols, climats du texte | NER + LLM |
| Extracteur de relations | Extrait relations entre entités | NLP + LLM |
| Extracteur de seuils | Extrait valeurs seuils | Regex + NLP |
| Détecteur de conflits | Détecte contradictions (S-3) | Comparaison graphe |
| Détecteur de doublons | Évite les entrées dupliquées | Similarité + graphe |
| Validateur de conformité | Vérifie S-1 à S-7 | Règles + Validation Engine |

### 3.3 Pipeline d'ingestion

```
Source brute → Extraction (NER/NLP) → Classification (type/domaine/preuve)
→ Validation (S-1 à S-7) → Intégration graphe → Versioning (CON-010)
→ Indexation → Exposition API
```

Chaque étape est **tracée** (CON-005). Une entrée rejetée est conservée
en quarantaine pour audit.

---

## 4. Extrême structuration et tri

### 4.1 Taxonomie multi-dimensionnelle

Chaque entrée est classée selon **plusieurs dimensions
orthogonales** :

| Dimension | Valeurs | Exemple |
|---|---|---|
| Domaine scientifique | 10 domaines S-6 | Écologie forestière |
| Type de connaissance | 6 types (livrable 302) | seuil |
| Niveau de preuve | A à F (S-2) | B |
| Échelle | arbre / peuplement / massif / paysage | peuplement |
| Géographie | région / département / commune | Vosges |
| Altitude | plage altitudinale | 400-1400 m |
| Climat | zone bioclimatique | atlantique |
| Substrat | géologique | cristallin |
| Version | numéro de version | 3 |
| Statut | actif / obsolète / quarantine | actif |

### 4.2 Indexation

- Index sur tous les champs filtrables (domaine, type, evidence,
  géographie, altitude).
- Index full-text sur les descriptions et mots-clés.
- Index spatial (PostGIS ou équivalent) pour les requêtes géographiques.
- Index temporel pour l'historique des versions.

### 4.3 Qualité des données

| Exigence | Mécanisme |
|---|---|
| Pas de doublon | Détecteur de doublons + identifiant unique |
| Pas de contradiction non documentée | Détecteur de conflits (S-3) |
| Pas d'entrée sans source | Validateur S-1 |
| Pas d'entrée sans niveau de preuve | Validateur S-2 |
| Pas d'entrée hors domaine de validité | Validateur S-5 |
| Historique complet | Versioning CON-010 |
| Citable | Identifiant stable GSIE-XXX |

---

## 5. Technologies cibles (à finaliser en Phase 4)

| Couche | Technologie candidate | Alternative |
|---|---|---|
| Base graphe | Neo4j | ArangoDB, Amazon Neptune |
| Base relationnelle (métadonnées) | PostgreSQL + PostGIS | MySQL |
| Triple store sémantique | Apache Jena | GraphDB, Virtuoso |
| Recherche full-text | Elasticsearch | OpenSearch, Meilisearch |
| Cache | Redis | Memcached |
| API | GraphQL (Apollo) + REST | Hasura |
| Ingestion NLP | spaCy + transformers | Stanza, Flair |
| Extraction LLM | Modèle local fine-tuné | API externe |
| Pipeline | Apache Airflow | Prefect, Dagster |
| Stockage objets (datasets) | MinIO / S3 | — |
| Interface web | Next.js + D3.js / Cytoscape | React + vis.js |

> Le choix définitif se fait en Phase 4 par ADR dédié. Cette directive
> fixe l'exigence, pas la technologie.

---

## 6. Gouvernance de l'Encyclopédie

### 6.1 Conformité constitutionnelle

L'Encyclopédie respecte **toutes** les lois et articles :

| Loi | Application |
|---|---|
| CON-002 | Chaque entrée est sourcée |
| CON-003 | L'Encyclopédie est le produit, pas le code |
| CON-005 | Chaque entrée est traçable (création, modification, usage) |
| CON-010 | Chaque entrée est versionnée, historique conservé |
| S-1 | Sources catégorisées et vérifiées |
| S-2 | Niveau de preuve affiché |
| S-3 | Conflits documentés, jamais résolus arbitrairement |
| S-4 | Révision par RFC pour changements majeurs |
| S-5 | Incertitude et domaine de validité explicites |
| S-7 | Patrimoine versionné, réversible, citable, ouvert |

### 6.2 Licence d'ouverture

L'Encyclopédie vise une **ouverture maximale** :
- Données sous licence ouverte (Licence Ouverte 2.0 ou CC-BY 4.0) dans
  la mesure des droits des sources.
- API publique en lecture.
- Export en formats ouverts (JSON, RDF, CSV).
- Les restrictions de licences sources (ONF, INRAE, Safran) sont
  respectées et documentées dans `19_LEGAL/`.

### 6.3 Contribution

L'Encyclopédie accepte des contributions externes (chercheurs,
forestiers, naturalistes) selon le pipeline du livrable 301. Chaque
contribution suit le même processus : source → évidence → validation →
intégration.

---

## 7. Impact sur les phases

### 7.1 Phase 3 (courante)

Le livrable 308 (Knowledge Base Seed) reste valable comme **amorce
manuelle** de 25 connaissances. Mais il devient le **point de départ**
d'une ingestion massive, pas le produit final.

Les livrables 301-307 restent valides : ils définissent les méthodes,
l'ontologie, le graphe, les datasets, le framework de preuve et le plan
de sourcing. L'Encyclopédie les implémente à grande échelle.

### 7.2 Phase 4 (à venir)

La Phase 4 implémente :
- La base de données graphe (Neo4j ou équivalent).
- Les pipelines d'ingestion automatisés (Airflow + NLP + LLM).
- Les classificateurs.
- L'API GraphQL/REST.
- L'interface web de consultation.
- L'intégration avec les 14 moteurs.

### 7.3 Phase 5 (future)

L'Encyclopédie devient un **produit public** :
- API ouverte.
- Interface web grand public.
- Partenariats data (INRAE, IGN, MNHN, universités).
- Contribution communautaire.

---

## 8. Décisions validées

1. L'Encyclopédie de l'Écosystème est le **produit principal** de GSIE.
2. L'échelle visée est **million d'entrées minimum**.
3. Le périmètre couvre **tout l'écosystème**, pas seulement la forêt.
4. Chaque entrée possède un **identifiant unique stable et citable**.
5. L'ingestion est **automatisée** via pipelines NLP/LLM + classificateurs.
6. L'Encyclopédie est **exposée** via API + interface web.
7. L'Encyclopédie vise une **licence ouverte** maximale.
8. Le livrable 308 est l'amorce, pas le produit final.
9. L'implémentation technique se fait en **Phase 4**.
10. Le choix des technologies est finalisé par **ADR** en Phase 4.

---

## 9. Garde-fous

- La Constitution Scientifique (S-1 à S-7) prime sur toute
  considération d'échelle ou de vitesse.
- Aucune entrée sans source (S-1), même à l'échelle du million.
- Aucune entrée sans niveau de preuve (S-2).
- Les conflits sont documentés, jamais résolus arbitrairement (S-3).
- L'historique est conservé (CON-010), même pour les entrées obsolètes.
- La qualité prime sur la quantité : mieux vaut 100 000 entrées
  sourcées que 1 000 000 entrées non sourcées.

---

> L'Encyclopédie de l'Écosystème est l'ambition ultime de GSIE. La
> connaissance à l'échelle du marché, au service de la science, de la
> gestion et de l'éducation.

# Knowledge Engine — Architecture détaillée

| Champ | Valeur |
|---|---|
| **Moteur** | Knowledge Engine |
| **Catégorie** | Chaîne d'intelligence (base de connaissances) |
| **Phase** | Phase 2 — Architecture |
| **Statut** | Draft |
| **Articles constitutionnels** | GSIE-CON-003, GSIE-CON-005, GSIE-CON-010 |
| **Ordre de développement** | 1 (voir `ENGINE_DEVELOPMENT_ORDER.md`) |

---

## 1. Responsabilité

Centraliser, structurer et versionner toutes les connaissances
scientifiques qualifiées de GSIE dans un graphe de connaissances
interrogeable, constituant la source unique de vérité pour tous les
moteurs de raisonnement.

## 2. Entrées

| Source | Type | Description |
|---|---|---|
| `EVIDENCE_ENGINE` | Connaissance qualifiée | Connaissances dotées d'un niveau de preuve et d'une source (`QualifiedKnowledge`) |
| `LEARNING_ENGINE` | Proposition de révision | Connaissances dont le niveau de preuve ou le contenu est susceptible d'évolution |
| `GSIE/KNOWLEDGE/` | Ontologies et règles | Ontologies, taxonomies et règles scientifiques structurées |

## 3. Sorties

| Destinataire | Type | Description |
|---|---|---|
| `CORRELATION_ENGINE` | Connaissances normalisées | Règles, seuils et relations pour le croisement de données |
| `REASONING_ENGINE` | Connaissances normalisées | Concepts, relations et règles d'inférence pour le raisonnement |
| `DIAGNOSTIC_ENGINE` | Connaissances normalisées | Référentiels stationnels et sylvicoles |
| `RECOMMENDATION_ENGINE` | Connaissances normalisées | Règles sylvicoles, gammes d'optimum, exigences d'essences |
| `FOREST_DYNAMICS_ENGINE` | Connaissances normalisées | Modèles de croissance, paramètres de production |
| `BOTANICAL_ENGINE` | Ontologie | Structure taxonomique et relations nomenclaturales |
| `VALIDATION_ENGINE` | Vérification de validité | Contrôle que les connaissances utilisées dans une sortie sont à jour et valides |

## 4. Dépendances

| Type | Cible | Nature |
|---|---|---|
| Moteur | `EVIDENCE_ENGINE` | Filtre amont obligatoire — aucune connaissance n'entre sans qualification |
| Moteur | `LEARNING_ENGINE` | Révisions proposées par apprentissage (sous réserve de validation) |
| Base | `GSIE/KNOWLEDGE/` | Ontologies et règles scientifiques sourcées |

## 5. Contrat d'interface

### Entrée — `QualifiedKnowledge` (depuis Evidence Engine)

Voir `EVIDENCE_ENGINE.md` §5. Le Knowledge Engine reçoit les
connaissances au statut `accepte`.

### Sortie — `KnowledgeQueryResult`

```
KnowledgeQueryResult = {
  requete_id      : UUID
  connaissances   : liste de KnowledgeObject
  total           : entier
  version_graph   : texte (version du graphe au moment de la requête)
}

KnowledgeObject = {
  connaissance_id   : UUID
  type              : enum { concept, relation, regle, seuil, modele, classification }
  contenu           : structure typée selon `type`
  evidence_level    : enum { A, B, C, D, E, F }
  source            : SourceReference
  version           : entier
  date_integration  : ISO 8601
  historique        : liste de VersionEntry
  domaines_validite : liste de DomaineValidite (optionnel)
}

VersionEntry = {
  version     : entier
  date        : ISO 8601
  justification : texte
  rfc_reference : texte (optionnel)
}

DomaineValidite = {
  parametre  : texte (ex. « pH », « altitude », « climat »)
  minimum    : valeur (optionnel)
  maximum    : valeur (optionnel)
  unite      : texte (optionnel)
}
```

### Requête — `KnowledgeQuery`

```
KnowledgeQuery = {
  requete_id : UUID
  type       : enum { par_concept, par_relation, par_domaine, par_essence, par_station }
  filtres    : map (clé-valeur selon le type)
  evidence_min : enum { A, B, C, D, E, F } (optionnel — filtre par niveau de preuve minimum)
}
```

## 6. Garanties

- **Source unique de vérité** — aucun autre moteur ne stocke de
  connaissance scientifique ; tous interrogent le Knowledge Engine.
- Toute connaissance est versionnée et son historique est conservé
  (`GSIE-CON-010`).
- Aucune logique d'inférence — le Knowledge Engine stocke et fournit,
  il ne raisonne pas (séparation des responsabilités, `GSIE-CON-007`).
- Toute connaissance est traçable jusqu'à sa source et son niveau de
  preuve (`GSIE-CON-005`).
- Le graphe de connaissances est interrogeable hors-ligne (article T-8).
- Une connaissance dont la source est invalidée est révisée via
  procédure documentée, jamais supprimée silencieusement.

## 7. Cas d'usage

### Cas 1 — Interrogation des exigences autécologiques du hêtre

Le Diagnostic Engine demande au Knowledge Engine toutes les
connaissances relatives aux exigences du hêtre (pH, altitude, climat,
sol). Le Knowledge Engine retourne une `KnowledgeQueryResult`
contenant les objets de connaissance avec leurs niveaux de preuve, leurs
sources (Rameau et al., 2018 ; ONF, 2020) et leurs domaines de validité.
Le Diagnostic Engine sait que le hêtre préfère les pH 5,0–7,0
(evidence B) et les altitudes 0–1400 m (evidence B, domaine France
métropolitaine).

### Cas 2 — Révision d'un seuil de vulnérabilité au gel

Une nouvelle publication (2028) invalide le seuil de -20 °C pour le
sapin pectiné au profit de -15 °C pour les provenances du Sud. Le
Knowledge Engine archive la version 1 (seuil -20 °C, source 2015) dans
l'historique, crée la version 2 (seuil -15 °C, source 2028) avec
justification. Les recommandations émises entre 2015 et 2028 restent
explicables : on sait quel seuil était utilisé (`GSIE-CON-010`).

## 8. État de l'art et pistes de recherche sourcées

Cette section recense, à titre de piste pour la Phase 4
(implémentation), des technologies et méthodes actuelles pertinentes
pour la responsabilité du Knowledge Engine — centraliser, structurer
et versionner les connaissances scientifiques qualifiées dans un
graphe interrogeable. Elle ne prescrit aucun choix définitif ni
détail d'implémentation : elle documente l'état de l'art pour éclairer
une future Architecture (05_SPECIFICATIONS / GSIE/ARCHITECTURE).

| Outil / Méthode | Rôle potentiel pour ce moteur | Justification |
|---|---|---|
| **Neo4j** (base de données de graphe de propriétés) | Support de stockage du graphe de connaissances (`KnowledgeObject` et relations) | Base de graphe de propriétés largement documentée pour la construction de graphes de connaissances de production ; des motifs de versionnement temporel y sont documentés (nœuds/relations horodatés, reconstruction d'état historique par filtrage temporel), ce qui correspond à l'exigence d'historisation (`historique : liste de VersionEntry`, §5). Neo4j Inc. précise cependant que Cypher et le moteur cœur n'offrent pas de versionnement intégré nativement — un schéma de modélisation temporelle explicite resterait à concevoir. |
| **Apache Jena / Fuseki** (triple store RDF + serveur SPARQL) | Représentation formelle RDF/OWL des connaissances et interrogation via SPARQL | Framework Apache établi pour le stockage et l'interrogation RDF, avec TDB2 comme moteur de stockage transactionnel persistant et un serveur SPARQL 1.1 conforme aux standards W3C. Une modélisation RDF/OWL correspondrait naturellement au triplet concept-relation-preuve attendu par `KnowledgeObject`, et la requête `KnowledgeQuery` (§5) se rapproche structurellement d'une requête SPARQL paramétrée. Eclipse RDF4J (ex-Sesame) constitue une alternative Java équivalente. |
| **Protégé** (éditeur d'ontologies, Stanford Center for Biomedical Informatics Research) et **OWL 2** | Modélisation en amont des ontologies et taxonomies avant peuplement du graphe (ex. taxonomie botanique pour `BOTANICAL_ENGINE`, classifications pédologiques) | Outil open source de référence pour la construction d'ontologies formelles, avec support complet d'OWL 2 et connexion à des raisonneurs de logique de description (HermiT, Pellet) permettant de vérifier la cohérence logique d'une taxonomie avant son intégration au graphe — pertinent pour la garantie « aucune logique d'inférence » du Knowledge Engine (§6), qui n'empêche pas une vérification de cohérence structurelle de l'ontologie elle-même. |
| **W3C PROV-O** (ontologie de provenance) | Modélisation normalisée de la traçabilité (`SourceReference`, `VersionEntry`, historique) | Ontologie OWL2 standardisée par le W3C pour représenter la provenance (entités, activités, agents) et leurs relations de génération/attribution. Correspond directement à l'exigence constitutionnelle de traçabilité (`GSIE-CON-005`, `GSIE-CON-010`) : chaque `KnowledgeObject` pourrait être relié à son activité de qualification (Evidence Engine) et à sa source via un vocabulaire interopérable plutôt qu'un schéma propriétaire. PROV-O est également cité dans les sections équivalentes du `RECOMMENDATION_ENGINE` et du `VALIDATION_ENGINE` — une seule modélisation centralisée du vocabulaire de provenance, réutilisée par les trois moteurs, éviterait une triple redondance d'implémentation. |
| **RDF2Vec** (embeddings de graphes RDF) | Recherche de connaissances par similarité sémantique en complément de la recherche exacte par identifiant/relation | Méthode établie (Ristoski & Paulheim, 2016) de projection des entités d'un graphe RDF dans un espace vectoriel continu par extraction de marches aléatoires puis apprentissage de type word2vec ; respecte la typologie des prédicats RDF, contrairement à des méthodes génériques comme node2vec. Pourrait enrichir `KnowledgeQuery` d'un mode de requête approximative, sans réintroduire de logique d'inférence dans le moteur. |
| **GraphRAG** (Microsoft Research, 2024) | Approche hybride graphe + recherche vectorielle pour répondre à des requêtes larges nécessitant une synthèse transversale du graphe | Combine extraction d'entités/relations, détection de communautés (algorithme de Leiden) et résumés hiérarchiques générés par LLM pour répondre à des questions de synthèse qu'une recherche vectorielle seule ne couvre pas efficacement. Piste pertinente uniquement pour la couche de restitution/synthèse en aval (ex. Reasoning Engine), le Knowledge Engine restant responsable du stockage et de la mise à disposition, non de la génération de synthèse. |

### Éléments complémentaires — versionnement temporel

Le besoin d'historisation (`VersionEntry`, garantie « aucune connaissance
supprimée silencieusement », §6) recoupe un axe de recherche actif sur
le **versionnement temporel des graphes RDF** : modélisation de
snapshots successifs, requêtes « voyage dans le temps » sur les
historiques de changements, et représentations condensées pour éviter
la duplication complète du graphe à chaque version. Ces travaux
offrent des précédents scientifiques directement transposables à la
conception du schéma `VersionEntry` et à la stratégie de stockage
historique du Knowledge Engine, sans qu'aucun choix ne soit tranché à
ce stade.

### Sources

- Neo4j Developer Blog — Ljubica Lazarevic, « Keeping track of graph changes using temporal versioning », Neo4j. https://medium.com/neo4j/keeping-track-of-graph-changes-using-temporal-versioning-3b0f854536fa
- Apache Software Foundation, « Apache Jena Fuseki — documentation ». https://jena.apache.org/documentation/fuseki2/
- Eclipse Foundation, « The Eclipse RDF4J Framework ». https://rdf4j.org/about/
- Protégé (Stanford Center for Biomedical Informatics Research), page officielle. https://protege.stanford.edu/
- W3C, « PROV-O: The PROV Ontology », W3C Recommendation, 2013. https://www.w3.org/TR/prov-o/
- Ristoski, P. & Paulheim, H. (2016). « RDF2Vec: RDF Graph Embeddings for Data Mining ». International Semantic Web Conference (ISWC). Voir aussi https://www.rdf2vec.org/
- Edge, D., Trinh, H., Cheng, N. et al. (2024). « From Local to Global: A Graph RAG Approach to Query-Focused Summarization ». Microsoft Research. arXiv:2404.16130. https://arxiv.org/abs/2404.16130
- « Time travel for knowledge graphs: live queries over RDF change histories », arXiv:2210.02534. https://arxiv.org/abs/2210.02534
- « Condensed Representation for Snapshot-Based RDF Graphs », arXiv:2506.21203. https://arxiv.org/html/2506.21203

---

> Statut : *Draft — Phase 2 (Architecture). Documentation uniquement,
> aucune implémentation (Phase 4).*

# Annexe RFC-0011 — Superseding du livrable 304 (Knowledge Graph Specification)

| Champ | Valeur |
|---|---|
| **RFC** | RFC-0011 |
| **Document supersédé** | 304 — Knowledge Graph Specification (`GSIE/KNOWLEDGE/KNOWLEDGE_GRAPH_SPECIFICATION.md`) |
| **Statut du document supersédé** | Validated |
| **Action** | Supersédé par DEC-000022 |
| **Date** | 2026-07-15 |

---

## Ce qui change

Le livrable 304 spécifie un graphe de connaissances avec :
- 6 types de nœuds `KnowledgeObject` (concept, relation, regle, seuil,
  modele, classification)
- 6 types d'entités externes (Essence, Station, Sol, Climat, Habitat,
  Publication)
- 7 types d'arêtes (est_adapte_a, influence, depend_de, est_valide_par,
  contredit, croit_mieux_sur, est_substituable_par)
- Topologie implémentée dans Neo4j (implicite, confirmé par livrable 309)

Le métamodèle v6.1 remplace cette topologie par :

| Élément 304 | Élément v6.1 |
|---|---|
| Nœuds KnowledgeObject (6 types) | `Assertion` avec `claim_kind` (7 valeurs) |
| Entités externes (Essence, Station, Sol, Climat, Habitat, Publication) | `Entity` (type 1) + `Instance` (type 8) + `Concept` (type 3) + `Source` (type 23) |
| Arêtes (7 prédicats) | `Assertion` avec `claim_kind=relation` + `AssertionParticipant` (sujet, objet) + `Predicate` (type 12) |
| `contredit` (arête entre KO) | `ConflictCluster` (type 42) — entité dédiée groupant les assertions contradictoires |
| Topologie Neo4j | Tables PostgreSQL + Apache AGE (benchmark Vague 1, ADR-003) |

## Ce qui est conservé

- Les 7 prédicats (est_adapte_a, influence, depend_de, est_valide_par,
  contredit, croit_mieux_sur, est_substituable_par) deviennent des
  `Predicate` (type 12) — leur sémantique est préservée.
- Le versionnement des relations (CON-010) est préservé : une relation
  EST une Assertion, donc versionnée comme toute assertion.
- Les patterns de requête (§5 du livrable 304) restent valides mais
  s'expriment en SQL sur les tables `assertion` +
  `assertion_participant` au lieu de Cypher sur Neo4j.

## Impact

- Les requêtes de traversée se font en SQL (jointures sur
  `assertion_participant`). Pour les traversées profondes (multi-sauts),
  Apache AGE est évalué (ADR-003).
- Neo4j est différé. Si le benchmark AGE (Vague 1) montre qu'AGE ne
  passe pas le seuil mesuré, Neo4j sera réintroduit. La décision est
  basée sur des données réelles, pas sur des hypothèses.

## Statut du document 304

Le fichier `KNOWLEDGE_GRAPH_SPECIFICATION.md` est **conservé intact**
dans `GSIE/KNOWLEDGE/`. En-tête annoté : supersédé par RFC-0011 /
DEC-000022.

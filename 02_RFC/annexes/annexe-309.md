# Annexe RFC-0011 — Superseding du livrable 309 (Encyclopedia Database Schema)

| Champ | Valeur |
|---|---|
| **RFC** | RFC-0011 |
| **Document supersédé** | 309 — Encyclopedia Database Schema (`GSIE/ARCHITECTURE/ENCYCLOPEDIA_DATABASE_SCHEMA.md`) |
| **Statut du document supersédé** | Validated |
| **Action** | Supersédé par DEC-000022 |
| **Date** | 2026-07-15 |

---

## Ce qui change

Le livrable 309 spécifie **quatre couches de stockage** :

| Couche 309 | Technologie | Volume cible |
|---|---|---|
| Graphe | Neo4j 5.x | 10M nœuds, 50M arêtes |
| Relationnel | PostgreSQL 16 + PostGIS 3.4 | Millions de lignes |
| Recherche | Elasticsearch 8.x | Index full-text |
| Sémantique | Apache Jena (TDB2) | Millions de triplets |

Le métamodèle v6.1 remplace cette architecture par :

| Couche v6.1 | Technologie | Statut |
|---|---|---|
| Relationnel + géo | PostgreSQL 16 + PostGIS 3.4 | **Vérité canonique** (Vague 1) |
| Bitemporalité | **GSIE Temporal & Provenance Engine** (moteur métier) | Vague 1 (ADR-002) |
| Graphe | Apache AGE (extension PG) | Benchmark Vague 1 (ADR-003) |
| Recherche full-text | PG trigram + GIN | Vague 1 (Elasticsearch différé) |
| Sémantique RDF/OWL | Apache Jena | **Différé** — projection régénérable |
| API | REST (FastAPI) | Vague 1 (GraphQL différé) |

## Justification du superseding

1. **YAGNI** : Neo4j, ES et Jena ajoutent 3 services à maintenir, sans
   benchmark prouvant le besoin en Vague 1.
2. **PostgreSQL canonique** : PG 16 + PostGIS + AGE couvrent le besoin
   relationnel, géospatial et de traversée de graphe. ES et Jena sont
   des projections régénérables à partir de PG.
3. **Benchmark avant décision** : AGE est évalué sur données réelles en
   Vague 1 (ADR-003). Si AGE ne passe pas, Neo4j est réintroduit. La
   décision est empirique, pas hypothétique.
4. **Complexité opérationnelle** : 1 service (PG) vs 4 services (PG +
   Neo4j + ES + Jena) en Vague 1. La maintenance, le monitoring et les
   sauvegardes sont simplifiés.

## Ce qui est conservé

- Les principes directeurs (S-1 à S-7, CON-002, CON-005, CON-010) sont
  préservés — ils sont indépendants de la technologie de stockage.
- Les identifiants stables `GSIE-K-XXXXXXXXXX` etc. sont préservés
  (champ `gsie_id` sur `resource`).
- L'indexation (B-tree, GIST, GIN) est spécifiée dans le métamodèle §6.4.
- Le versionnement et l'historique sont préservés via `Revision` +
  le **GSIE Temporal & Provenance Engine** (Revision + Snapshot + ResourceDiff + PROV-O, ADR-002).

## Ce qui est différé (pas supprimé)

| Technologie | Condition de réintroduction |
|---|---|
| Neo4j | Si benchmark AGE < seuil mesuré (ADR-003) |
| Elasticsearch | Si recherche full-text PG insuffisante (volume, analyser français) |
| Apache Jena | Si besoin SPARQL / alignement LOD confirmé |
| GraphQL | Si consommateurs API expriment le besoin |

## Statut du document 309

Le fichier `ENCYCLOPEDIA_DATABASE_SCHEMA.md` est **conservé intact**
dans `GSIE/ARCHITECTURE/`. En-tête annoté : supersédé par RFC-0011 /
DEC-000022.

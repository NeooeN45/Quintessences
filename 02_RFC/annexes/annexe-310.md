# Annexe RFC-0011 — Superseding du livrable 310 (Engine Data Socle)

| Champ | Valeur |
|---|---|
| **RFC** | RFC-0011 |
| **Document supersédé** | 310 — Engine Data Socle (`GSIE/ARCHITECTURE/ENGINE_DATA_SOCLE.md`) |
| **Statut du document supersédé** | Validated |
| **Action** | Supersédé par DEC-000022 |
| **Date** | 2026-07-15 |

---

## Ce qui change

Le livrable 310 définit le socle de données de chacun des 14 moteurs GSIE
autour de `KnowledgeObject` (6 types : concept, relation, regle, seuil,
modele, classification). Les moteurs consomment des `KnowledgeQuery` et
produisent des `ValidatedOutput` basés sur cette structure.

Le métamodèle v6.1 remplace `KnowledgeObject` par `Assertion` avec
`claim_kind` (7 valeurs : observation, relation, rule, threshold, model,
classification, absence).

## Mapping des contrats moteurs

| Élément 310 | Élément v6.1 |
|---|---|
| `KnowledgeObject` 6 types | `Assertion` avec `claim_kind` 7 valeurs |
| `KnowledgeQuery.type` (6 valeurs) | `KnowledgeQuery.claim_kind` (7 valeurs) |
| `evidence_level` sur KO | `EvidenceAssessment` (multiple, sur Assertion) |
| `source` sur KO | `Citation` → `Source` |
| `domaines_validite` sur KO | `AssertionQualifier` |
| Tables PG ou nœuds Neo4j | Tables PG canoniques (+ AGE si benchmark OK) |
| `ValidatedOutput` | `Assertion` produite par le moteur (re-sourcée, CON-005) |

## Mapping claim_kind par moteur

| Moteur | Types KO consommés (310) | claim_kind v6.1 |
|---|---|---|
| Evidence | — (qualifie, ne consomme pas) | Produit `EvidenceAssessment` |
| Knowledge | Tous (stocke) | Stocke toutes `Assertion` |
| Correlation | relation, modele | relation, model |
| Reasoning | regle, seuil, relation | rule, threshold, relation |
| Diagnostic | relation, seuil, modele | relation, threshold, model |
| Simulation | modele | model (+ `ModelRun` type 32) |
| Recommendation | relation, regle | relation, rule |
| Validation | tous (vérifie) | toutes |
| GIS | classification, observation | classification, observation |
| Climate | seuil, modele, observation | threshold, model, observation |
| Pedology | classification, seuil | classification, threshold |
| Botanical | classification, relation | classification, relation |
| Forest Dynamics | modele, relation | model, relation |
| Learning | tous (apprend) | toutes (+ produit `Assertion` candidate) |

## Impact sur les contrats d'interface (livrable 206)

Le livrable 206 (Engine Interface Contracts, Draft) définit
`QualifiedKnowledge` et `KnowledgeQuery` basés sur `KnowledgeObject`.
Ces contrats sont amendés :

- `QualifiedKnowledge` → `Assertion` + `EvidenceAssessment`
- `KnowledgeQuery.type` → `KnowledgeQuery.claim_kind`
- `KnowledgeQuery.evidence_min` → filtre sur `EvidenceAssessment.level`

L'amendement du livrable 206 se fait en Vague 0 (contrats d'interface
noyau ↔ profils ↔ API).

## Ce qui est conservé

- Le principe du socle (3 couches : connaissances, référentiels,
  productions) reste valide.
- Les règles du socle (S-2, CON-005, CON-010, CON-007) sont préservées.
- L'ordre de développement (livrable 204) et les dépendances entre
  moteurs restent valides.
- Les liens avec les 6 applications externes (GeoSylva, Ignis, Artemis,
  Hydro, Flora, QGISIA) sont préservés.

## Statut du document 310

Le fichier `ENGINE_DATA_SOCLE.md` est **conservé intact** dans
`GSIE/ARCHITECTURE/`. En-tête annoté : supersédé par RFC-0011 /
DEC-000022.

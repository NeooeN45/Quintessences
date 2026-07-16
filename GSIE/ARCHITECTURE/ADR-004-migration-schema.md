# ADR-004 — Migration du schéma actuel vers v6.1

| Champ | Valeur |
|---|---|
| **ID** | ADR-004 |
| **Statut** | Validated |
| **Date** | 2026-07-15 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Décision liée** | DEC-000022, RFC-0011 |

## Contexte

Le schéma actuel de la base de connaissances comprend :

1. **`knowledge_models.py`** — modèles SQLAlchemy définissant les tables
   `knowledge_objects`, `knowledge_history` (schéma PG complet mais non
   connecté au moteur).
2. **`engine.py`** — Knowledge Engine utilisant `self._store:
   dict[UUID, KnowledgeObject]` (in-memory, pas de persistance).
3. **Migration 0001** — crée l'extension AGE, le graphe
   `gsie_knowledge_graph`, et les tables PG (mais aucune requête Cypher
   n'existe dans `src/`).
4. **25 connaissances seed** (livrable 308) — structurées en
   `KnowledgeObject` 6 types avec `evidence_level` direct.

L'audit v6.1 (F-P2-02) demande de documenter cet écart et de planifier
la migration vers le schéma v6.1 (`resource` + 42 tables).

## Écart documenté

| Élément | État actuel | État v6.1 |
|---|---|---|
| Store moteur | `dict[UUID, KnowledgeObject]` (in-memory) | Repository PG sur `resource` + `assertion` + tables associées |
| Schéma PG | `knowledge_models.py` (tables `knowledge_objects`, `knowledge_history`) — non connecté | `resource` + 42 tables (ADR-001) |
| Migration | 0001 : tables `knowledge_objects` + AGE inerte | 0002 : transformation vers v6.1 |
| Evidence | `evidence_level` direct sur `KnowledgeObject` | `EvidenceAssessment` (multiple, sur `Assertion`) |
| Source | `source` direct sur `KnowledgeObject` | `Citation` → `Source` |
| Contenu | `contenu` dict libre | `AssertionParticipant` + `AssertionQualifier` |
| Historique | `historique` liste `VersionEntry` | `Revision` (append-only) |
| Conflits | `conflits` liste `ConflitBibliographique` | `ConflictCluster` |
| Tests Rust | 67 tests Evidence Engine (intacts) | Intacts (adaptateur Rust évalue + Python enrichit) |
| Tests Python | 33 tests Knowledge + 11 tests pipeline | Adaptés au schéma v6.1 |

## Options envisagées

1. **Migration big bang** — une migration 0002 qui transforme toutes les
   tables existantes en schéma v6.1 en une seule fois. Avantage : état
   final propre. Inconvénient : risque élevé, pas de rollback facile.

2. **Migration progressive** — migrations 0002 (création tables v6.1),
   0003 (copie données), 0004 (bascule moteur), 0005 (suppression
   anciennes tables). Avantage : rollback possible à chaque étape.
   Inconvénient : plus de migrations à maintenir.

3. **Schéma vert (greenfield)** — créer le schéma v6.1 à côté de
   l'ancien, migrer les données, puis supprimer l'ancien. Avantage :
   zéro risque sur l'existant. Inconvénient : double schéma temporaire.

## Décision

**Option 2 : migration progressive (4 migrations).**

### Plan de migration

| Migration | Action | Rollback |
|---|---|---|
| 0002 | Créer `resource` + 73 tables v6.2 (vides) + index + tables Temporal Engine (revision, snapshot, resource_diff) + tables FAIR/RGPD (sample, consent, data_subject, persistent_identifier) + tables dynamiques (flow, confidence_graph, goal, constraint, knowledge_lineage, experiment, terrain_session, ecological_state) | DROP tables v6.2 |
| 0003 | Copier `knowledge_objects` → `resource` + `assertion` + `assertion_participant` + `assertion_qualifier` + `evidence_assessment` + `citation`. Mapper `evidence_level` → `EvidenceAssessment(level)`. Mapper `source` → `Citation` + `Source`. Mapper `contenu` → participants + qualifiers. | DELETE FROM tables v6.1 (les anciennes tables sont intactes) |
| 0004 | Bascule `engine.py` : repository PG sur schéma v6.1. Tests adaptés. | Repli sur store in-memory (feature flag) |
| 0005 | Supprimer anciennes tables `knowledge_objects`, `knowledge_history` après validation | Restaurer depuis backup (les données sont conservées dans les tables v6.1) |

### Migration des 25 connaissances seed (livrable 308)

Script Python dédié qui :
1. Lit chaque `KnowledgeObject` seed
2. Crée l'`Entity` / `Concept` / `Instance` correspondant
3. Crée l'`Assertion` avec `claim_kind` mappé (§3.3 métamodèle)
4. Crée les `AssertionParticipant` (sujet, objet)
5. Crée les `AssertionQualifier` (domaines_validite → qualifiers)
6. Crée l'`EvidenceAssessment` (evidence_level → level)
7. Crée la `Citation` + `Source` (source → citation + source)
8. Vérifie l'intégrité (count avant/après, tests)

### Adaptateur Evidence Engine (arbitrage T4)

- **Rust** : cœur d'évaluation préservé (matrice A-F, 67 tests intacts).
  Produit un `EvidenceResult` avec `level` (A-F) + `status`
  (accepte/quarantine/refuse).
- **Python** : couche d'enrichissement qui transforme le `EvidenceResult`
  en `EvidenceAssessment` (ajoute `evaluator_id`, `method`,
  `evaluated_at`, `scope`).

```python
# Adaptateur (Python)
def evidence_result_to_assessment(
    result: EvidenceResult, evaluator: Agent, method: str
) -> EvidenceAssessment:
    return EvidenceAssessment(
        assertion_id=result.assertion_id,
        level=result.level,  # A-F depuis Rust
        evaluator_id=evaluator.id,
        method=method,
        evaluated_at=datetime.now(UTC),
        scope=result.scope,
    )
```

## Conséquences

- **Positives** : migration progressive avec rollback, tests à chaque
  étape, adaptateur préserve le cœur Rust.
- **Négatives** : 4 migrations à maintenir, double schéma temporaire
  (0002-0004), effort de test sur les 25 seeds.
- **Impact moteurs** : `engine.py` passe de in-memory à repository PG.
  Les 33 tests Python Knowledge sont adaptés. Les 11 tests pipeline
  sont adaptés. Les 67 tests Rust sont intacts.

## Statut de suivi

- 2026-07-15 : Proposé (RFC-0011 / DEC-000022)
- Vague 0 : audit de migration détaillé (vérifier `knowledge_models.py`
  ↔ migration 0001 ↔ schéma v6.1)
- Vague 1 : exécution des migrations 0002-0005 + tests

## Validation (2026-07-16)

ADR-004 validée par le Fondateur. Le plan en 4 migrations progressives
(0002-0005) est retenu. La migration 0002 actuelle (big bang) sera
réécrite pour suivre ce plan. RFC-0012 est amendée pour s'aligner sur
cette ADR (voir RFC-0012 §6 — amendement de cohérence).
